import os, json, time, uuid
from datetime import datetime, timezone
from typing import AsyncGenerator, List, Dict

import httpx
import boto3
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

# ----- קונפיג -----
REDIS_URL = os.getenv("REDIS_URL","redis://:password@redis:6379/0")
OLLAMA_URL = os.getenv("OLLAMA_URL","http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL","tinyllama")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT","http://minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY","admin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY","password")
S3_BUCKET = os.getenv("S3_BUCKET","chat-archive")
SESSION_TTL = int(os.getenv("SESSION_TTL_SECONDS","259200"))  # 3 ימים

app = FastAPI(title="Org Chat POC")
rds = None
s3 = None

def _ts():
    return datetime.now(timezone.utc).isoformat()

@app.on_event("startup")
async def startup():
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

async def get_ctx(session_id: str) -> List[Dict]:
    data = await rds.get(f"sess:{session_id}")
    return json.loads(data) if data else []

async def set_ctx(session_id: str, messages: List[Dict]):
    await rds.set(f"sess:{session_id}", json.dumps(messages), ex=SESSION_TTL)

def archive_message(session_id: str, payload: Dict):
    key = f"conversations/{session_id}/{int(time.time()*1000)}-{uuid.uuid4().hex}.json"
    s3.put_object(Bucket=S3_BUCKET, Key=key, Body=json.dumps(payload).encode("utf-8"))

async def ollama_stream(messages: List[Dict]) -> AsyncGenerator[str, None]:
    url = f"{OLLAMA_URL}/api/chat"
    async with httpx.AsyncClient(timeout=60) as client:
        req = {"model": OLLAMA_MODEL, "messages": messages, "stream": True}
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
                # פורמט הזרם של ollama: {"message":{"role":"assistant","content":"..."},"done":false}
                if "message" in obj and "content" in obj["message"]:
                    yield obj["message"]["content"]
                if obj.get("done"):
                    break

@app.post("/chat")
async def chat(body: Dict):
    session_id = (body.get("session_id") or "").strip()
    prompt = (body.get("prompt") or "").strip()
    if not session_id or not prompt:
        raise HTTPException(400, "session_id ו-prompt חובה")

    ctx = await get_ctx(session_id)
    new_ctx = ctx + [{"role":"system","content":"You are a helpful and concise enterprise assistant."}] if not ctx else ctx
    new_ctx = new_ctx + [ {"role":"user","content":prompt} ]

    # ארכוב הודעת המשתמש
    archive_message(session_id, {"ts":_ts(),"role":"user","content":prompt})

    async def gen():
        assistant_text = ""
        try:
            async for chunk in ollama_stream(new_ctx):
                assistant_text += chunk
                yield chunk
        finally:
            # עדכון זיכרון קצר + ארכוב תשובת העוזר
            ctx2 = ctx + [{"role":"user","content":prompt},{"role":"assistant","content":assistant_text}]
            await set_ctx(session_id, ctx2)
            archive_message(session_id, {"ts":_ts(),"role":"assistant","content":assistant_text})

    return StreamingResponse(gen(), media_type="text/plain")
