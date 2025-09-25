import os, json, time, uuid, asyncio
from datetime import datetime, timezone
from typing import AsyncGenerator, List, Dict, Optional
from contextlib import asynccontextmanager

import httpx
import boto3
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, Depends, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import jwt
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import logging

# ----- קונפיג -----
REDIS_URL = os.getenv("REDIS_URL", "redis://:password@redis:6379/0")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "tinyllama")
OLLAMA_FAST_MODEL = os.getenv("OLLAMA_FAST_MODEL", "phi3")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "password")
S3_BUCKET = os.getenv("S3_BUCKET", "chat-archive")
SESSION_TTL = int(os.getenv("SESSION_TTL_SECONDS", "259200"))  # 3 ימים
INSTANCE_ID = os.getenv("INSTANCE_ID", "api-1")
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")

# ----- Prometheus Metrics -----
REQUEST_COUNT = Counter('chat_requests_total', 'Total chat requests', ['instance', 'status'])
REQUEST_DURATION = Histogram('chat_request_duration_seconds', 'Request duration', ['instance'])
ACTIVE_SESSIONS = Counter('active_sessions_total', 'Active sessions', ['instance'])

# ----- Logging -----
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----- Global Variables -----
rds = None
s3 = None
security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global rds, s3
    rds = await redis.from_url(REDIS_URL, decode_responses=True)
    s3 = boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        region_name="us-east-1",
    )
    # ודא שה-bucket קיים
    try:
        s3.head_bucket(Bucket=S3_BUCKET)
    except Exception:
        s3.create_bucket(Bucket=S3_BUCKET)
    
    logger.info(f"🚀 Enterprise Chat API {INSTANCE_ID} started successfully")
    yield
    
    # Shutdown
    await rds.close()
    logger.info(f"🛑 Enterprise Chat API {INSTANCE_ID} shutdown")

app = FastAPI(
    title="Enterprise Org Chat API",
    description="Scalable enterprise chatbot with advanced features",
    version="2.0.0",
    lifespan=lifespan
)

# ----- Middleware -----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

def _ts():
    return datetime.now(timezone.utc).isoformat()

# ----- Authentication -----
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ----- Rate Limiting -----
async def check_rate_limit(user_id: str, request: Request):
    key = f"rate_limit:{user_id}"
    current = await rds.get(key)
    
    if current is None:
        await rds.setex(key, 60, 1)
        return True
    
    if int(current) >= RATE_LIMIT_PER_MINUTE:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    await rds.incr(key)
    return True

# ----- Session Management -----
async def get_ctx(session_id: str) -> List[Dict]:
    data = await rds.get(f"sess:{session_id}")
    return json.loads(data) if data else []

async def set_ctx(session_id: str, messages: List[Dict]):
    await rds.setex(f"sess:{session_id}", SESSION_TTL, json.dumps(messages))

async def get_session_metadata(session_id: str) -> Dict:
    data = await rds.get(f"meta:{session_id}")
    return json.loads(data) if data else {"created_at": _ts(), "message_count": 0}

async def update_session_metadata(session_id: str, metadata: Dict):
    await rds.setex(f"meta:{session_id}", SESSION_TTL, json.dumps(metadata))

# ----- Archive System -----
def archive_message(session_id: str, payload: Dict):
    try:
        key = f"conversations/{session_id}/{int(time.time()*1000)}-{uuid.uuid4().hex}.json"
        s3.put_object(
            Bucket=S3_BUCKET, 
            Key=key, 
            Body=json.dumps(payload).encode("utf-8"),
            Metadata={
                "timestamp": _ts(),
                "session_id": session_id,
                "instance_id": INSTANCE_ID
            }
        )
    except Exception as e:
        logger.error(f"Archive failed: {e}")

# ----- AI Integration -----
async def ollama_stream(messages: List[Dict], model: str = None) -> AsyncGenerator[str, None]:
    model = model or OLLAMA_MODEL
    url = f"{OLLAMA_URL}/api/chat"
    
    async with httpx.AsyncClient(timeout=120) as client:
        req = {
            "model": model, 
            "messages": messages, 
            "stream": True,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "num_predict": 1000
            }
        }
        
        try:
            async with client.stream("POST", url, json=req) as resp:
                if resp.status_code != 200:
                    text = await resp.aread()
                    raise HTTPException(500, f"ollama error: {text.decode('utf-8','ignore')}")
                
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except Exception:
                        continue
                    
                    if "message" in obj and "content" in obj["message"]:
                        yield obj["message"]["content"]
                    if obj.get("done"):
                        break
        except httpx.TimeoutException:
            raise HTTPException(504, "AI service timeout")

# ----- Health Check -----
@app.get("/health")
async def health_check():
    try:
        # Check Redis
        await rds.ping()
        # Check MinIO
        s3.head_bucket(Bucket=S3_BUCKET)
        return {
            "status": "healthy",
            "instance": INSTANCE_ID,
            "timestamp": _ts(),
            "services": {
                "redis": "ok",
                "minio": "ok"
            }
        }
    except Exception as e:
        raise HTTPException(503, f"Service unhealthy: {e}")

# ----- Metrics -----
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# ----- Main Chat Endpoint -----
@app.post("/chat")
async def chat(
    body: Dict,
    request: Request,
    background_tasks: BackgroundTasks,
    user: dict = Depends(verify_token)
):
    start_time = time.time()
    session_id = (body.get("session_id") or "").strip()
    prompt = (body.get("prompt") or "").strip()
    model = body.get("model", OLLAMA_MODEL)
    
    if not session_id or not prompt:
        REQUEST_COUNT.labels(instance=INSTANCE_ID, status='bad_request').inc()
        raise HTTPException(400, "session_id ו-prompt חובה")
    
    # Rate limiting
    user_id = user.get("user_id", session_id)
    await check_rate_limit(user_id, request)
    
    # Get session context
    ctx = await get_ctx(session_id)
    metadata = await get_session_metadata(session_id)
    
    # Build context with system message
    if not ctx:
        ctx = [{"role": "system", "content": """אתה עוזר ארגוני חכם ומועיל בעברית. 

תפקידך:
- לענות על שאלות עסקיות, טכנולוגיות וניהוליות
- לתת עצות מעשיות וקונקרטיות
- להיות מקצועי, ידידותי ומועיל
- לענות בעברית בלבד
- לתת תשובות ברורות וממוקדות
- לשאול שאלות הבהרה כשצריך

תמיד התחל את התשובה בברכה קצרה ותן מידע רלוונטי ומעשי."""}]
    
    new_ctx = ctx + [{"role": "user", "content": prompt}]
    
    # Archive user message
    user_message = {"ts": _ts(), "role": "user", "content": prompt, "model": model}
    background_tasks.add_task(archive_message, session_id, user_message)
    
    async def generate_response():
        assistant_text = ""
        try:
            async for chunk in ollama_stream(new_ctx, model):
                assistant_text += chunk
                yield chunk
        finally:
            # Update session context
            ctx2 = ctx + [
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": assistant_text}
            ]
            await set_ctx(session_id, ctx2)
            
            # Update metadata
            metadata["message_count"] = metadata.get("message_count", 0) + 1
            metadata["last_activity"] = _ts()
            await update_session_metadata(session_id, metadata)
            
            # Archive assistant response
            assistant_message = {
                "ts": _ts(), 
                "role": "assistant", 
                "content": assistant_text,
                "model": model,
                "response_time": time.time() - start_time
            }
            background_tasks.add_task(archive_message, session_id, assistant_message)
            
            # Update metrics
            REQUEST_COUNT.labels(instance=INSTANCE_ID, status='success').inc()
            REQUEST_DURATION.labels(instance=INSTANCE_ID).observe(time.time() - start_time)
    
    return StreamingResponse(
        generate_response(), 
        media_type="text/plain; charset=utf-8",
        headers={
            "X-Instance-ID": INSTANCE_ID,
            "X-Response-Time": str(time.time() - start_time)
        }
    )

# ----- Session Management -----
@app.get("/sessions/{session_id}")
async def get_session(session_id: str, user: dict = Depends(verify_token)):
    ctx = await get_ctx(session_id)
    metadata = await get_session_metadata(session_id)
    
    return {
        "session_id": session_id,
        "messages": ctx,
        "metadata": metadata,
        "instance": INSTANCE_ID
    }

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str, user: dict = Depends(verify_token)):
    await rds.delete(f"sess:{session_id}")
    await rds.delete(f"meta:{session_id}")
    
    return {"message": "Session deleted", "session_id": session_id}

# ----- Analytics -----
@app.get("/analytics/sessions")
async def get_session_analytics(user: dict = Depends(verify_token)):
    # Get session statistics from Redis
    keys = await rds.keys("meta:*")
    sessions = []
    
    for key in keys[:100]:  # Limit to 100 sessions
        data = await rds.get(key)
        if data:
            sessions.append(json.loads(data))
    
    return {
        "total_sessions": len(keys),
        "recent_sessions": sessions,
        "instance": INSTANCE_ID
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
