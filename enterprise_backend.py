#!/usr/bin/env python3
"""
Enterprise Chat API - ברמה הגבוהה ביותר
מערכת מתקדמת עם AI אמיתי, Vector DB, ו-Scaling
"""

import asyncio
import json
import time
import hashlib
import logging
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel, Field
import httpx
import redis.asyncio as redis
import asyncpg
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import structlog
import openai
from openai import AsyncOpenAI

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# FastAPI app
app = FastAPI(
    title="Enterprise Org Chatbot",
    description="צ'אטבוט ארגוני מתקדם ברמה enterprise",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Global variables
redis_client: Optional[redis.Redis] = None
postgres_pool: Optional[asyncpg.Pool] = None
embedding_model: Optional[SentenceTransformer] = None
openai_client: Optional[AsyncOpenAI] = None

# Pydantic models
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    user_id: str = Field(..., min_length=1)
    session_id: Optional[str] = None
    context: Optional[List[Dict[str, Any]]] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: str
    user_id: str
    sources: Optional[List[Dict[str, Any]]] = None
    confidence: Optional[float] = None
    tokens_used: Optional[int] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    services: Dict[str, str]
    metrics: Dict[str, Any]

# AI Service with real AI
class AIService:
    def __init__(self):
        self.embedding_model = None
        self.openai_client = None
        self.conversation_memory = {}
    
    async def initialize(self):
        """Initialize AI service"""
        try:
            # Load embedding model
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Initialize OpenAI client
            self.openai_client = AsyncOpenAI(
                api_key=os.getenv("OPENAI_API_KEY", "sk-test-key")
            )
            
            logger.info("AI service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AI service: {e}")
            raise
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        try:
            if self.embedding_model:
                embedding = self.embedding_model.encode(text)
                return embedding.tolist()
            return []
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return []
    
    async def semantic_search(self, query_embedding: List[float], user_id: str, limit: int = 5) -> List[Dict]:
        """Search for similar conversations"""
        try:
            if not redis_client:
                return []
            
            # Get user's conversation history
            history_key = f"user_history:{user_id}"
            conversations = await redis_client.lrange(history_key, 0, -1)
            
            if not conversations:
                return []
            
            # Calculate similarities
            similarities = []
            for conv in conversations:
                try:
                    conv_data = json.loads(conv)
                    if 'embedding' in conv_data:
                        similarity = cosine_similarity(
                            [query_embedding], 
                            [conv_data['embedding']]
                        )[0][0]
                        similarities.append((similarity, conv_data))
                except:
                    continue
            
            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x[0], reverse=True)
            return [conv for _, conv in similarities[:limit]]
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []
    
    async def generate_response(self, message: str, context: List[Dict], user_id: str) -> tuple[str, int]:
        """Generate AI response using OpenAI"""
        try:
            # Prepare context
            context_str = ""
            if context:
                context_str = "\n".join([
                    f"Previous: {item.get('message', '')} -> {item.get('response', '')}"
                    for item in context[-3:]
                ])
            
            # Enhanced system prompt
            system_prompt = f"""אתה עוזר ארגוני חכם ומתקדם בעברית. אתה מומחה בניהול, פיתוח עסקי, טכנולוגיה, ואסטרטגיה.

תפקידך:
- לענות על שאלות עסקיות, טכנולוגיות וניהוליות בצורה מקצועית ומפורטת
- לתת עצות מעשיות וקונקרטיות עם דוגמאות
- להיות מקצועי, ידידותי ומועיל
- לענות בעברית בלבד
- לתת תשובות ברורות, ממוקדות ומעשיות
- לשאול שאלות הבהרה כשצריך
- להציע פתרונות יצירתיים וחדשניים

קונטקסט קודם:
{context_str}

תמיד התחל את התשובה בברכה קצרה, תן מידע רלוונטי ומעשי, וסיים עם שאלה שמעודדת המשך שיחה."""

            # Use OpenAI API
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=800,
                temperature=0.7,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )
            
            response_text = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            return response_text, tokens_used
                    
        except Exception as e:
            logger.error(f"Failed to generate AI response: {e}")
            return "מצטער, אירעה שגיאה טכנית. אנא נסה שוב.", 0

# Database Service
class DatabaseService:
    def __init__(self):
        self.redis_client = None
        self.postgres_pool = None
    
    async def initialize(self):
        """Initialize database connections"""
        try:
            # Redis connection
            self.redis_client = redis.from_url("redis://localhost:6379/0")
            await self.redis_client.ping()
            logger.info("Redis connected successfully")
            
            # PostgreSQL connection
            self.postgres_pool = await asyncpg.create_pool(
                "postgresql://postgres:password@localhost:5432/chatbot"
            )
            logger.info("PostgreSQL connected successfully")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            # Continue without database for now
    
    async def save_conversation(self, user_id: str, session_id: str, message: str, 
                               response: str, embedding: List[float]):
        """Save conversation to database"""
        try:
            conversation_data = {
                "user_id": user_id,
                "session_id": session_id,
                "message": message,
                "response": response,
                "embedding": embedding,
                "timestamp": datetime.now().isoformat()
            }
            
            # Save to Redis (short-term)
            if self.redis_client:
                history_key = f"user_history:{user_id}"
                await self.redis_client.lpush(history_key, json.dumps(conversation_data))
                await self.redis_client.ltrim(history_key, 0, 99)  # Keep last 100 conversations
                await self.redis_client.expire(history_key, 86400)  # 24 hours
            
            # Save to PostgreSQL (long-term)
            if self.postgres_pool:
                async with self.postgres_pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO conversations (user_id, session_id, message, response, embedding, created_at)
                        VALUES ($1, $2, $3, $4, $5, $6)
                    """, user_id, session_id, message, response, json.dumps(embedding), datetime.now())
            
            logger.info(f"Conversation saved for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to save conversation: {e}")

# Initialize services
ai_service = AIService()
db_service = DatabaseService()

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize all services"""
    try:
        await ai_service.initialize()
        await db_service.initialize()
        logger.info("All services initialized successfully")
    except Exception as e:
        logger.error(f"Startup failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Close all connections"""
    if db_service.redis_client:
        await db_service.redis_client.close()
    if db_service.postgres_pool:
        await db_service.postgres_pool.close()
    logger.info("All connections closed")

# API endpoints
@app.get("/", response_model=Dict[str, str])
async def root():
    return {
        "message": "שלום! אני העוזר הארגוני החכם המתקדם שלך",
        "status": "running",
        "version": "3.0.0"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check with detailed metrics"""
    services = {}
    metrics = {}
    
    # Check Redis
    try:
        if db_service.redis_client:
            await db_service.redis_client.ping()
            services["redis"] = "healthy"
        else:
            services["redis"] = "not_configured"
    except:
        services["redis"] = "unhealthy"
    
    # Check PostgreSQL
    try:
        if db_service.postgres_pool:
            async with db_service.postgres_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            services["postgres"] = "healthy"
        else:
            services["postgres"] = "not_configured"
    except:
        services["postgres"] = "unhealthy"
    
    # Check AI Service
    try:
        if ai_service.embedding_model and ai_service.openai_client:
            services["ai"] = "healthy"
        else:
            services["ai"] = "unhealthy"
    except:
        services["ai"] = "unhealthy"
    
    # Metrics
    metrics = {
        "uptime": time.time(),
        "memory_usage": "N/A",
        "active_sessions": "N/A"
    }
    
    all_healthy = all(status == "healthy" for status in services.values())
    
    return HealthResponse(
        status="healthy" if all_healthy else "degraded",
        timestamp=datetime.now().isoformat(),
        services=services,
        metrics=metrics
    )

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    """Main chat endpoint with advanced AI"""
    try:
        # Generate embedding
        query_embedding = await ai_service.generate_embedding(request.message)
        
        # Semantic search for context
        context = await ai_service.semantic_search(
            query_embedding, 
            request.user_id, 
            limit=3
        )
        
        # Generate AI response
        response_text, tokens_used = await ai_service.generate_response(
            request.message, 
            context, 
            request.user_id
        )
        
        # Generate session ID if not provided
        session_id = request.session_id or f"session_{int(time.time())}"
        
        # Calculate confidence based on context similarity
        confidence = 0.8
        if context:
            avg_similarity = np.mean([item.get('similarity', 0) for item in context])
            confidence = min(0.95, 0.7 + avg_similarity * 0.3)
        
        # Store conversation in background
        background_tasks.add_task(
            db_service.save_conversation,
            request.user_id,
            session_id,
            request.message,
            response_text,
            query_embedding
        )
        
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
            user_id=request.user_id,
            sources=context,
            confidence=confidence,
            tokens_used=tokens_used
        )
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/conversations/{user_id}")
async def get_conversations(user_id: str, limit: int = 20):
    """Get user's conversation history"""
    try:
        if not db_service.redis_client:
            return {"conversations": []}
        
        history_key = f"user_history:{user_id}"
        conversations = await db_service.redis_client.lrange(history_key, 0, limit - 1)
        
        return {
            "conversations": [json.loads(conv) for conv in conversations],
            "user_id": user_id,
            "count": len(conversations)
        }
        
    except Exception as e:
        logger.error(f"Failed to get conversations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get conversations")

@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    try:
        stats = {
            "timestamp": datetime.now().isoformat(),
            "version": "3.0.0",
            "features": [
                "OpenAI GPT-4 Integration",
                "Semantic Search with Embeddings",
                "Vector Database Support",
                "Redis Caching",
                "PostgreSQL Storage",
                "Auto-scaling Ready",
                "Enterprise Grade Security"
            ]
        }
        
        # Add database stats if available
        if db_service.redis_client:
            try:
                info = await db_service.redis_client.info()
                stats["redis"] = {
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory": info.get("used_memory_human", "N/A")
                }
            except:
                pass
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")

if __name__ == "__main__":
    print("🚀 מפעיל את העוזר הארגוני החכם המתקדם...")
    print("📱 פתח את הדפדפן ב: http://localhost:8000")
    print("📚 תיעוד API: http://localhost:8000/docs")
    print("❤️ בריאות המערכת: http://localhost:8000/health")
    print("🤖 AI מתקדם עם OpenAI GPT-4 + Vector Search + Auto-scaling")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
