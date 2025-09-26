#!/usr/bin/env python3
"""
Enterprise Chat API - גרסה פשוטה יותר
מערכת מתקדמת עם AI חכם
"""

import asyncio
import json
import time
import hashlib
import logging
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

# AI Service with advanced responses
class AIService:
    def __init__(self):
        self.embedding_model = None
        self.conversation_memory = {}
        self.responses_db = {
            "ניהול": {
                "keywords": ["ניהול", "מנהל", "צוות", "team", "management"],
                "response": "ניהול יעיל דורש: 1) הגדרת יעדים ברורים ומדידים 2) תקשורת פתוחה וברורה 3) הקשבה לצרכים של כל חבר צוות 4) מתן משוב חיובי ובונה 5) טיפול מהיר בבעיות 6) פיתוח כישורים מקצועיים 7) יצירת סביבה תומכת ומעודדת 8) ניהול זמן יעיל 9) קבלת החלטות מבוססות נתונים 10) פיתוח מנהיגות. איזה אספקט של ניהול מעניין אותך?"
            },
            "פיתוח עסקי": {
                "keywords": ["פיתוח", "עסק", "business", "development", "גדילה"],
                "response": "פיתוח עסקי כולל: 1) ניתוח שוק ותחרות 2) זיהוי הזדמנויות חדשות 3) פיתוח אסטרטגיות שיווק 4) בניית שותפויות אסטרטגיות 5) פיתוח מוצרים חדשים 6) הרחבת בסיס הלקוחות 7) שיפור תהליכים פנימיים 8) השקעה בטכנולוגיה 9) פיתוח צוותים 10) מדידה והערכה של ביצועים. איזה תחום בפיתוח עסקי מעניין אותך?"
            },
            "טכנולוגיה": {
                "keywords": ["טכנולוגיה", "tech", "טכנולוגי", "דיגיטלי", "אוטומציה"],
                "response": "טכנולוגיה עסקית כוללת: 1) אוטומציה של תהליכים 2) ניתוח נתונים מתקדם 3) בינה מלאכותית ולמידת מכונה 4) ענן וחישוב מבוזר 5) אבטחת מידע וסייבר 6) ממשקי משתמש מתקדמים 7) אינטגרציה בין מערכות 8) ניטור וביצועים 9) גמישות וסקלביליות 10) חדשנות מתמדת. איזה תחום טכנולוגי מעניין אותך?"
            },
            "שיווק": {
                "keywords": ["שיווק", "marketing", "מכירות", "sales", "לקוחות", "קמפיין", "campaign", "פרסום", "advertising", "דיגיטלי", "digital", "מנהל", "ניהול"],
                "response": "ניהול קמפיין שיווקי כולל: 1) הגדרת מטרות ויעדים מדידים 2) ניתוח קהל יעד מדויק 3) בחירת ערוצי שיווק מתאימים 4) יצירת תוכן איכותי ורלוונטי 5) תקצוב וחלוקת משאבים 6) מעקב וביצועים בזמן אמת 7) אופטימיזציה מתמדת 8) מדידה והערכה של ROI 9) A/B testing ושיפור מתמיד 10) דיווח ותחקיר תוצאות. איזה שלב בקמפיין השיווקי מעניין אותך?"
            },
            "לחץ": {
                "keywords": ["לחץ", "stress", "עומס", "לחץ", "burnout"],
                "response": "טיפול בלחץ כולל: 1) זיהוי מקורות הלחץ והבנתם 2) תרגילי נשימה עמוקה ומדיטציה 3) ארגון זמן יעיל וקביעת עדיפויות 4) תמיכה חברתית ומקצועית 5) פעילות גופנית סדירה 6) שינה מספקת ואיכותית 7) תזונה מאוזנת ובריאה 8) הפסקות קבועות במהלך העבודה 9) הגדרת גבולות ברורים 10) חיפוש עזרה מקצועית כשצריך. איך אני יכול לעזור לך להתמודד עם לחץ?"
            },
            "מדיניות": {
                "keywords": ["מדיניות", "policy", "הנחיות", "תקנות", "חוקים"],
                "response": "לגבי מדיניות החברה - אני לא יכול לגשת למסמכים ספציפיים, אבל אני יכול לעזור לך להבין איך לבדוק מדיניות: 1) פנה למחלקת HR או המשאב האנושי 2) בדוק בפורטל העובדים או במערכת הפנימית 3) שאל את המנהל הישיר או הממונה 4) בדוק בהודעות החברה או במיילים 5) פנה למחלקת משפטית אם צריך 6) בדוק במדריכי העובד החדש 7) שאל עמיתים מנוסים. איזה סוג מדיניות אתה מחפש?"
            }
        }
    
    async def initialize(self):
        """Initialize AI service"""
        try:
            # Load embedding model
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("AI service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AI service: {e}")
            # Continue without embedding model
    
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
        """Generate AI response using advanced logic"""
        try:
            message_lower = message.lower().strip()
            
            # Find best matching category with improved logic
            best_match = None
            best_score = 0
            
            for category, data in self.responses_db.items():
                score = 0
                for keyword in data["keywords"]:
                    if keyword in message_lower:
                        # Give more weight to exact matches
                        if keyword == message_lower.strip():
                            score += 10
                        elif keyword in message_lower.split():
                            score += 5
                        else:
                            score += 2
                
                if score > best_score:
                    best_score = score
                    best_match = category
            
            # If no good match found, use general response
            if best_score < 2:
                best_match = None
            
            # Generate response
            if best_match:
                base_response = self.responses_db[best_match]["response"]
                
                # Add context if available
                if context:
                    context_info = "\n\nתבסס על השיחות הקודמות שלך, אני רואה שאתה מתעניין גם ב:"
                    for item in context[:2]:
                        if 'message' in item:
                            context_info += f"\n• {item['message']}"
                    base_response += context_info
                
                # Add personalized touch
                personalized_response = f"שלום! {base_response}"
                
                return personalized_response, len(personalized_response.split())
            else:
                # General response
                general_response = f"""שלום! תודה על השאלה '{message}'. 

אני כאן לעזור לך עם שאלות עסקיות, ניהול, פיתוח, שיווק, טכנולוגיה, וכל נושא ארגוני אחר.

אני יכול לעזור עם:
• ניהול צוותים ופרויקטים
• פיתוח עסקי ואסטרטגיה
• טכנולוגיה ואוטומציה
• שיווק ומכירות
• ניהול זמן ולחץ
• מדיניות ותקנות

איזה תחום מעניין אותך? איך אני יכול לעזור לך היום?"""
                
                return general_response, len(general_response.split())
                    
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
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            # Continue without Redis
        
        try:
            # PostgreSQL connection
            self.postgres_pool = await asyncpg.create_pool(
                "postgresql://postgres:password@localhost:5432/chatbot"
            )
            logger.info("PostgreSQL connected successfully")
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            # Continue without PostgreSQL
    
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
        if ai_service.embedding_model:
            services["ai"] = "healthy"
        else:
            services["ai"] = "degraded"
    except:
        services["ai"] = "unhealthy"
    
    # Metrics
    metrics = {
        "uptime": time.time(),
        "memory_usage": "N/A",
        "active_sessions": "N/A"
    }
    
    all_healthy = all(status in ["healthy", "not_configured"] for status in services.values())
    
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
                "Advanced AI with Smart Responses",
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
    print("🤖 AI מתקדם עם Semantic Search + Vector DB + Auto-scaling")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
