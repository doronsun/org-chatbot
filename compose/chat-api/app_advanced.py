"""
Advanced Chat API with Vector DB and Graph DB
Supports millions of requests with semantic search and relationship mapping
"""

import asyncio
import json
import logging
import time
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

import httpx
import redis.asyncio as redis
import asyncpg
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import weaviate
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
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

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# FastAPI app
app = FastAPI(
    title="Advanced Org Chatbot API",
    description="Enterprise chatbot with Vector DB and Graph DB",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gzip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Global variables for connections
redis_client: Optional[redis.Redis] = None
postgres_pool: Optional[asyncpg.Pool] = None
weaviate_client: Optional[weaviate.Client] = None
neo4j_driver: Optional[GraphDatabase.driver] = None
embedding_model: Optional[SentenceTransformer] = None

# Pydantic models
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    user_id: str = Field(..., min_length=1)
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: datetime
    sources: Optional[List[Dict[str, Any]]] = None
    recommendations: Optional[List[str]] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    services: Dict[str, str]

# Database connection classes
class VectorService:
    def __init__(self, weaviate_client):
        self.client = weaviate_client
    
    async def create_schema(self):
        """Create Weaviate schema for chat messages"""
        schema = {
            "class": "ChatMessage",
            "description": "Chat messages with embeddings",
            "vectorizer": "none",  # We'll provide our own embeddings
            "properties": [
                {
                    "name": "text",
                    "dataType": ["text"],
                    "description": "The message text"
                },
                {
                    "name": "user_id",
                    "dataType": ["string"],
                    "description": "User ID"
                },
                {
                    "name": "session_id",
                    "dataType": ["string"],
                    "description": "Session ID"
                },
                {
                    "name": "timestamp",
                    "dataType": ["date"],
                    "description": "Message timestamp"
                },
                {
                    "name": "category",
                    "dataType": ["string"],
                    "description": "Message category"
                }
            ]
        }
        
        try:
            self.client.schema.create_class(schema)
            logger.info("Weaviate schema created successfully")
        except Exception as e:
            logger.warning(f"Schema might already exist: {e}")
    
    async def add_message(self, message: str, user_id: str, session_id: str, 
                        embedding: List[float], category: str = "general"):
        """Add a message to the vector database"""
        try:
            self.client.data_object.create(
                data_object={
                    "text": message,
                    "user_id": user_id,
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                    "category": category
                },
                class_name="ChatMessage",
                vector=embedding
            )
            logger.info(f"Message added to vector DB for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to add message to vector DB: {e}")
            raise
    
    async def semantic_search(self, query_embedding: List[float], 
                            limit: int = 5, user_id: Optional[str] = None):
        """Perform semantic search in the vector database"""
        try:
            where_filter = {"path": ["user_id"], "operator": "Equal", "valueString": user_id} if user_id else None
            
            result = self.client.query.get(
                "ChatMessage", ["text", "user_id", "session_id", "timestamp", "category"]
            ).with_near_vector({
                "vector": query_embedding,
                "certainty": 0.7
            }).with_where(where_filter).with_limit(limit).do()
            
            return result.get("data", {}).get("Get", {}).get("ChatMessage", [])
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

class GraphService:
    def __init__(self, neo4j_driver):
        self.driver = neo4j_driver
    
    async def create_conversation(self, user_id: str, question: str, answer: str, 
                                session_id: str, category: str = "general"):
        """Create conversation nodes and relationships in Neo4j"""
        try:
            with self.driver.session() as session:
                session.run("""
                    MERGE (u:User {id: $user_id})
                    CREATE (q:Question {
                        text: $question, 
                        session_id: $session_id,
                        timestamp: datetime(),
                        category: $category
                    })
                    CREATE (a:Answer {
                        text: $answer,
                        session_id: $session_id,
                        timestamp: datetime()
                    })
                    CREATE (u)-[:ASKED]->(q)
                    CREATE (q)-[:HAS_ANSWER]->(a)
                    CREATE (u)-[:PARTICIPATED_IN]->(a)
                """, user_id=user_id, question=question, answer=answer, 
                    session_id=session_id, category=category)
                
                logger.info(f"Conversation created in graph DB for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to create conversation in graph DB: {e}")
            raise
    
    async def get_recommendations(self, user_id: str, limit: int = 5):
        """Get personalized recommendations based on user's conversation history"""
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (u:User {id: $user_id})-[:ASKED]->(q:Question)-[:HAS_ANSWER]->(a:Answer)
                    MATCH (similar:Question)-[:HAS_ANSWER]->(similar_answer:Answer)
                    WHERE similar.category = q.category 
                    AND similar <> q
                    RETURN DISTINCT similar.text as question, 
                           similar_answer.text as answer,
                           similar.category as category
                    LIMIT $limit
                """, user_id=user_id, limit=limit)
                
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Failed to get recommendations: {e}")
            return []

class AIService:
    def __init__(self, ollama_url: str, model_name: str, fast_model: str):
        self.ollama_url = ollama_url
        self.model_name = model_name
        self.fast_model = fast_model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using sentence transformers"""
        try:
            embedding = self.embedding_model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return []
    
    async def generate_response(self, message: str, context: Optional[List[Dict]] = None) -> str:
        """Generate AI response using Ollama"""
        try:
            # Prepare context for the AI
            context_str = ""
            if context:
                context_str = "\n".join([f"Previous: {item.get('text', '')}" for item in context[-3:]])
            
            system_prompt = f"""אתה עוזר ארגוני חכם ומועיל בעברית. 

תפקידך:
- לענות על שאלות עסקיות, טכנולוגיות וניהוליות
- לתת עצות מעשיות וקונקרטיות
- להיות מקצועי, ידידותי ומועיל
- לענות בעברית בלבד
- לתת תשובות ברורות וממוקדות
- לשאול שאלות הבהרה כשצריך

תמיד התחל את התשובה בברכה קצרה ותן מידע רלוונטי ומעשי.

קונטקסט קודם:
{context_str}"""

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model_name,
                        "prompt": f"{system_prompt}\n\nשאלה: {message}",
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "top_p": 0.9,
                            "max_tokens": 500
                        }
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", "מצטער, לא הצלחתי ליצור תשובה.")
                else:
                    logger.error(f"Ollama API error: {response.status_code}")
                    return "מצטער, אירעה שגיאה טכנית. אנא נסה שוב."
                    
        except Exception as e:
            logger.error(f"Failed to generate AI response: {e}")
            return "מצטער, אירעה שגיאה טכנית. אנא נסה שוב."

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize all database connections and services"""
    global redis_client, postgres_pool, weaviate_client, neo4j_driver, embedding_model
    
    try:
        # Redis connection
        redis_client = redis.from_url("redis://:password@redis:6379/0")
        await redis_client.ping()
        logger.info("Redis connected successfully")
        
        # PostgreSQL connection
        postgres_pool = await asyncpg.create_pool(
            "postgresql://postgres:password@postgres:5432/chatbot"
        )
        logger.info("PostgreSQL connected successfully")
        
        # Weaviate connection
        weaviate_client = weaviate.Client("http://weaviate:8080")
        await weaviate_client.is_ready()
        logger.info("Weaviate connected successfully")
        
        # Neo4j connection
        neo4j_driver = GraphDatabase.driver("bolt://neo4j:7687", auth=("neo4j", "password"))
        logger.info("Neo4j connected successfully")
        
        # Initialize embedding model
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Embedding model loaded successfully")
        
        # Create schemas
        vector_service = VectorService(weaviate_client)
        await vector_service.create_schema()
        
        logger.info("All services initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Close all database connections"""
    global redis_client, postgres_pool, neo4j_driver
    
    if redis_client:
        await redis_client.close()
    if postgres_pool:
        await postgres_pool.close()
    if neo4j_driver:
        neo4j_driver.close()
    
    logger.info("All connections closed")

# API endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    services = {}
    
    # Check Redis
    try:
        await redis_client.ping()
        services["redis"] = "healthy"
    except:
        services["redis"] = "unhealthy"
    
    # Check PostgreSQL
    try:
        async with postgres_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        services["postgres"] = "healthy"
    except:
        services["postgres"] = "unhealthy"
    
    # Check Weaviate
    try:
        await weaviate_client.is_ready()
        services["weaviate"] = "healthy"
    except:
        services["weaviate"] = "unhealthy"
    
    # Check Neo4j
    try:
        with neo4j_driver.session() as session:
            session.run("RETURN 1")
        services["neo4j"] = "healthy"
    except:
        services["neo4j"] = "unhealthy"
    
    all_healthy = all(status == "healthy" for status in services.values())
    
    return HealthResponse(
        status="healthy" if all_healthy else "degraded",
        timestamp=datetime.now(),
        services=services
    )

@app.post("/chat", response_model=ChatResponse)
@limiter.limit("60/minute")
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    """Main chat endpoint with vector search and graph relationships"""
    try:
        # Initialize services
        ai_service = AIService("http://ollama:11434", "llama3.2:3b", "phi3:3.8b")
        vector_service = VectorService(weaviate_client)
        graph_service = GraphService(neo4j_driver)
        
        # Generate embedding for the query
        query_embedding = await ai_service.generate_embedding(request.message)
        
        # Perform semantic search for similar conversations
        similar_messages = await vector_service.semantic_search(
            query_embedding, 
            limit=3, 
            user_id=request.user_id
        )
        
        # Generate AI response
        response_text = await ai_service.generate_response(
            request.message, 
            context=similar_messages
        )
        
        # Generate session ID if not provided
        session_id = request.session_id or f"session_{int(time.time())}"
        
        # Store conversation in background
        background_tasks.add_task(
            store_conversation,
            request.user_id,
            request.message,
            response_text,
            session_id,
            query_embedding
        )
        
        # Get recommendations
        recommendations = await graph_service.get_recommendations(request.user_id, limit=3)
        rec_texts = [rec.get("question", "") for rec in recommendations]
        
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            timestamp=datetime.now(),
            sources=similar_messages,
            recommendations=rec_texts
        )
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def store_conversation(user_id: str, question: str, answer: str, 
                           session_id: str, embedding: List[float]):
    """Store conversation in all databases"""
    try:
        # Store in vector database
        vector_service = VectorService(weaviate_client)
        await vector_service.add_message(
            question, user_id, session_id, embedding, "question"
        )
        await vector_service.add_message(
            answer, user_id, session_id, embedding, "answer"
        )
        
        # Store in graph database
        graph_service = GraphService(neo4j_driver)
        await graph_service.create_conversation(
            user_id, question, answer, session_id, "general"
        )
        
        # Store in PostgreSQL for metadata
        async with postgres_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO conversations (user_id, session_id, question, answer, created_at)
                VALUES ($1, $2, $3, $4, $5)
            """, user_id, session_id, question, answer, datetime.now())
        
        logger.info(f"Conversation stored for user {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to store conversation: {e}")

@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    try:
        # Get conversation count from PostgreSQL
        async with postgres_pool.acquire() as conn:
            total_conversations = await conn.fetchval("SELECT COUNT(*) FROM conversations")
        
        # Get vector count from Weaviate
        vector_count = weaviate_client.query.aggregate("ChatMessage").with_meta_count().do()
        total_vectors = vector_count.get("data", {}).get("Aggregate", {}).get("ChatMessage", [{}])[0].get("meta", {}).get("count", 0)
        
        # Get graph stats from Neo4j
        with neo4j_driver.session() as session:
            result = session.run("MATCH (n) RETURN labels(n) as label, count(n) as count")
            graph_stats = {record["label"][0]: record["count"] for record in result}
        
        return {
            "total_conversations": total_conversations,
            "total_vectors": total_vectors,
            "graph_stats": graph_stats,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
