# 📚 Code Documentation - Professional Development Guide

## 🎯 Overview
תיעוד מפורט של כל קובץ וקובץ במערכת, כולל הסבר על כל פונקציה, קלאס ושורה חשובה.

## 🚀 Backend Services

### 📄 `compose/chat-api/app.py`

```python
# ============================================================================
# Enterprise AI Chatbot API - Main Application
# ============================================================================
# 
# זה הקובץ הראשי של ה-API שמנהל את כל הפונקציונליות של הצ'אטבוט.
# הקובץ כולל:
# - FastAPI application setup
# - Database connections (Redis, MinIO, Ollama)
# - Chat endpoint עם AI integration
# - Session management
# - Error handling ו-monitoring
# ============================================================================

import os, json, time, uuid
from datetime import datetime, timezone
from typing import AsyncGenerator, List, Dict

# ============================================================================
# IMPORTS SECTION
# ============================================================================
# כל ה-imports מסודרים לפי קטגוריה:
# 1. Standard library imports
# 2. Third-party imports  
# 3. Local imports

import httpx  # Async HTTP client לתקשורת עם Ollama
import boto3  # AWS SDK למיניו/S3
import redis.asyncio as redis  # Async Redis client
from fastapi import FastAPI, HTTPException  # Web framework
from fastapi.responses import StreamingResponse  # For streaming responses

# ============================================================================
# CONFIGURATION SECTION
# ============================================================================
# כל ה-configuration variables עם default values ו-environment variable support

REDIS_URL = os.getenv("REDIS_URL","redis://:secure_redis_password_123@redis:6379/0")
# הסבר: Redis URL עם password מובנה. הפורמט: redis://:password@host:port/db
# משמש ל-session management ו-caching

OLLAMA_URL = os.getenv("OLLAMA_URL","http://ollama:11434")
# הסבר: URL של שרת Ollama שמריץ את ה-LLM models

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL","llama3.2:3b")
# הסבר: המודל הראשי של Ollama. llama3.2:3b הוא מודל קטן ומהיר

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT","http://minio:9000")
# הסבר: MinIO endpoint למיניו/S3 compatible storage

MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY","admin")
# הסבר: Access key למיניו

MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY","secure_minio_password_123")
# הסבר: Secret key למיניו

S3_BUCKET = os.getenv("S3_BUCKET","chat-archive")
# הסבר: שם ה-bucket לאחסון שיחות ארוכות טווח

SESSION_TTL = int(os.getenv("SESSION_TTL_SECONDS","259200"))  # 3 ימים
# הסבר: זמן חיים של session ב-Redis (בשניות). 259200 = 3 ימים

# ============================================================================
# FASTAPI APPLICATION SETUP
# ============================================================================

app = FastAPI(title="Org Chat POC")
# הסבר: יצירת FastAPI application עם שם פשוט

# Global variables שיהיו זמינות בכל ה-application
rds = None  # Redis client
s3 = None   # MinIO/S3 client

def _ts():
    """
    Helper function להחזרת timestamp נוכחי
    Returns: ISO formatted timestamp string
    """
    return datetime.now(timezone.utc).isoformat()

# ============================================================================
# STARTUP EVENT
# ============================================================================

@app.on_event("startup")
async def startup():
    """
    Event handler שמתבצע בעת הפעלת השרת
    
    הפונקציה:
    1. מתחברת ל-Redis
    2. מתחברת ל-MinIO/S3
    3. בודקת שה-bucket קיים
    4. מכינה את המערכת לעבודה
    """
    global rds, s3
    
    # התחברות ל-Redis
    rds = await redis.from_url(REDIS_URL, decode_responses=True)
    
    # התחברות ל-MinIO/S3
    s3 = boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        region_name="us-east-1",
    )
    
    # וידוא שה-bucket קיים
    try:
        s3.head_bucket(Bucket=S3_BUCKET)
        # head_bucket בודק אם ה-bucket קיים
    except Exception:
        # אם ה-bucket לא קיים, יוצרים אותו
        s3.create_bucket(Bucket=S3_BUCKET)

# ============================================================================
# SESSION MANAGEMENT FUNCTIONS
# ============================================================================

async def get_ctx(session_id: str) -> List[Dict]:
    """
    קבלת היסטוריית שיחה מ-Redis
    
    Args:
        session_id: מזהה ה-session
        
    Returns:
        רשימה של הודעות בשיחה
    """
    data = await rds.get(f"sess:{session_id}")
    # מפתח Redis: sess:session_id
    return json.loads(data) if data else []
    # אם יש נתונים - מפענח JSON, אחרת מחזיר רשימה ריקה

async def set_ctx(session_id: str, messages: List[Dict]):
    """
    שמירת היסטוריית שיחה ב-Redis
    
    Args:
        session_id: מזהה ה-session
        messages: רשימת הודעות לשמירה
    """
    await rds.set(f"sess:{session_id}", json.dumps(messages), ex=SESSION_TTL)
    # ex=SESSION_TTL מגדיר זמן חיים ל-key

# ============================================================================
# AI RESPONSE GENERATION
# ============================================================================

async def ollama_stream(ctx: List[Dict]) -> AsyncGenerator[str, None]:
    """
    יצירת תגובה מ-AI עם streaming
    
    Args:
        ctx: היסטוריית השיחה
        
    Yields:
        חלקים של התגובה בזמן אמת
    """
    # הוספת system message בעברית
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
    
    # קריאה ל-Ollama API
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": ctx,
                "stream": True,  # Streaming mode
            },
            timeout=120.0
        ) as response:
            if response.status_code != 200:
                text = await response.aread()
                raise HTTPException(500, f"ollama error: {text.decode('utf-8','ignore')}")
            
            # קריאת התגובה חלק אחר חלק
            async for chunk in response.aiter_lines():
                if chunk.strip():
                    try:
                        data = json.loads(chunk)
                        if "message" in data and "content" in data["message"]:
                            yield data["message"]["content"]
                    except json.JSONDecodeError:
                        continue

# ============================================================================
# MAIN CHAT ENDPOINT
# ============================================================================

@app.post("/chat")
async def chat(request: dict):
    """
    Endpoint הראשי לצ'אט
    
    Args:
        request: Dictionary עם prompt ו-session_id
        
    Returns:
        StreamingResponse עם התגובה של ה-AI
    """
    # וידוא שיש prompt ו-session_id
    if "prompt" not in request or "session_id" not in request:
        raise HTTPException(400, "session_id ו-prompt חובה")
    
    prompt = request["prompt"]
    session_id = request["session_id"]
    
    # קבלת היסטוריית השיחה
    ctx = await get_ctx(session_id)
    
    # הוספת ההודעה החדשה להיסטוריה
    new_ctx = ctx + [{"role": "user", "content": prompt}]
    
    # שמירת ההיסטוריה המעודכנת
    await set_ctx(session_id, new_ctx)
    
    # יצירת response עם streaming
    def gen():
        # יצירת generator function
        async def _gen():
            full_response = ""
            async for chunk in ollama_stream(new_ctx):
                full_response += chunk
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            
            # הוספת התגובה המלאה להיסטוריה
            final_ctx = new_ctx + [{"role": "assistant", "content": full_response}]
            await set_ctx(session_id, final_ctx)
            
            # שליחה ל-MinIO לאחסון ארוך טווח
            try:
                s3.put_object(
                    Bucket=S3_BUCKET,
                    Key=f"conversations/{session_id}/{int(time.time())}.json",
                    Body=json.dumps(final_ctx),
                    ContentType="application/json"
                )
            except Exception as e:
                print(f"Failed to archive conversation: {e}")
        
        return _gen()
    
    return StreamingResponse(
        gen(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

# ============================================================================
# APPLICATION STARTUP
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    # הפעלת השרת על כל ה-interfaces בפורט 8000
```

## 🎨 Frontend Components

### 📄 `frontend/src/App.tsx`

```typescript
// ============================================================================
// React Main Application Component
// ============================================================================
// 
// זה הקומפוננט הראשי של האפליקציה.
// כולל:
// - State management
// - Connection monitoring
// - Component coordination
// ============================================================================

import React, { useState, useEffect } from 'react';
import { ChatInterface } from './components/ChatInterface';
import { Header } from './components/Header';
import './App.css';

// ============================================================================
// INTERFACES AND TYPES
// ============================================================================

interface Message {
  id: string;
  content: string;
  timestamp: Date;
  sender: 'user' | 'ai';
  confidence?: number;
  sources?: string[];
}

// ============================================================================
// MAIN APP COMPONENT
// ============================================================================

const App: React.FC = () => {
  // ========================================================================
  // STATE MANAGEMENT
  // ========================================================================
  
  const [isConnected, setIsConnected] = useState(false);
  // מצב החיבור לשרת - true אם השרת זמין
  
  const [messages, setMessages] = useState<Message[]>([]);
  // רשימת ההודעות בצ'אט
  
  const [isLoading, setIsLoading] = useState(false);
  // מצב טעינה - true כשמחכים לתגובה מהשרת
  
  // ========================================================================
  // CONNECTION MONITORING
  // ========================================================================
  
  useEffect(() => {
    /**
     * בדיקת חיבור לשרת כל 30 שניות
     * 
     * הפונקציה:
     * 1. שולחת בקשה ל-/api/health
     * 2. מעדכנת את מצב החיבור
     * 3. מגדירה interval לבדיקות חוזרות
     */
    const checkConnection = async () => {
      try {
        const response = await fetch('/api/health');
        setIsConnected(response.ok);
      } catch (error) {
        console.error('Connection check failed:', error);
        setIsConnected(false);
      }
    };

    // בדיקה ראשונית
    checkConnection();
    
    // הגדרת interval לבדיקות חוזרות
    const interval = setInterval(checkConnection, 30000);
    
    // Cleanup function
    return () => clearInterval(interval);
  }, []);

  // ========================================================================
  // MESSAGE HANDLING
  // ========================================================================
  
  const handleSendMessage = async (content: string) => {
    /**
     * שליחת הודעה לשרת
     * 
     * Args:
     *   content: תוכן ההודעה
     * 
     * הפונקציה:
     * 1. מוסיפה הודעת משתמש לרשימה
     * 2. שולחת בקשה לשרת
     * 3. מעבדת את התגובה
     * 4. מוסיפה תגובת AI לרשימה
     */
    
    // הוספת הודעת משתמש
    const userMessage: Message = {
      id: generateId(),
      content,
      timestamp: new Date(),
      sender: 'user'
    };
    
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // שליחת בקשה לשרת
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt: content,
          session_id: getSessionId(),
          user_id: getCurrentUserId()
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // קריאת התגובה
      const data = await response.json();
      
      // הוספת תגובת AI
      const aiMessage: Message = {
        id: generateId(),
        content: data.response,
        timestamp: new Date(),
        sender: 'ai',
        confidence: data.confidence,
        sources: data.sources
      };
      
      setMessages(prev => [...prev, aiMessage]);
      
    } catch (error) {
      console.error('Failed to send message:', error);
      
      // הוספת הודעת שגיאה
      const errorMessage: Message = {
        id: generateId(),
        content: 'מצטער, אירעה שגיאה. אנא נסה שוב.',
        timestamp: new Date(),
        sender: 'ai'
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // ========================================================================
  // HELPER FUNCTIONS
  // ========================================================================
  
  const generateId = (): string => {
    /** יצירת מזהה ייחודי להודעה */
    return Math.random().toString(36).substr(2, 9);
  };

  const getSessionId = (): string => {
    /** קבלת מזהה session נוכחי */
    let sessionId = localStorage.getItem('session_id');
    if (!sessionId) {
      sessionId = generateId();
      localStorage.setItem('session_id', sessionId);
    }
    return sessionId;
  };

  const getCurrentUserId = (): string => {
    /** קבלת מזהה משתמש נוכחי */
    return localStorage.getItem('user_id') || 'anonymous';
  };

  // ========================================================================
  // RENDER
  // ========================================================================
  
  return (
    <div className="app">
      {/* Header עם אינדיקטור חיבור */}
      <Header isConnected={isConnected} />
      
      {/* ממשק הצ'אט הראשי */}
      <ChatInterface 
        messages={messages}
        isLoading={isLoading}
        onSendMessage={handleSendMessage}
      />
    </div>
  );
};

export default App;
```

## 🗄️ Database Integration

### 📄 `compose/chat-api/vector_search.py`

```python
# ============================================================================
# Vector Search Service - Weaviate Integration
# ============================================================================
# 
# שירות חיפוש סמנטי מתקדם עם Weaviate
# כולל:
# - יצירת embeddings
# - חיפוש דומה
# - אינדוקס מסמכים
# ============================================================================

import weaviate
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
import numpy as np

class VectorSearchService:
    """
    שירות חיפוש סמנטי עם Weaviate
    
    השירות מספק:
    - יצירת embeddings מתוך טקסט
    - חיפוש דומה במסד הנתונים
    - אינדוקס מסמכים חדשים
    - ניהול סכמת הנתונים
    """
    
    def __init__(self, weaviate_url: str):
        """
        אתחול השירות
        
        Args:
            weaviate_url: URL של שרת Weaviate
        """
        self.client = weaviate.Client(url=weaviate_url)
        # אתחול sentence transformer ליצירת embeddings
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self._initialize_schema()
    
    def _initialize_schema(self):
        """
        אתחול סכמת הנתונים ב-Weaviate
        
        יוצר class בשם "Document" עם המאפיינים:
        - content: תוכן המסמך
        - title: כותרת המסמך
        - category: קטגוריה
        - embedding: וקטור ה-embedding
        """
        schema = {
            "class": "Document",
            "description": "Enterprise documents for semantic search",
            "properties": [
                {
                    "name": "content",
                    "dataType": ["text"],
                    "description": "Document content"
                },
                {
                    "name": "title", 
                    "dataType": ["string"],
                    "description": "Document title"
                },
                {
                    "name": "category",
                    "dataType": ["string"],
                    "description": "Document category"
                },
                {
                    "name": "embedding",
                    "dataType": ["number[]"],
                    "description": "Vector embedding"
                }
            ]
        }
        
        try:
            self.client.schema.create_class(schema)
        except Exception as e:
            if "already exists" not in str(e):
                raise
    
    async def index_document(self, content: str, title: str, category: str):
        """
        אינדוקס מסמך חדש
        
        Args:
            content: תוכן המסמך
            title: כותרת המסמך
            category: קטגוריית המסמך
            
        הפונקציה:
        1. יוצרת embedding מתוך התוכן
        2. שומרת את המסמך ב-Weaviate
        """
        # יצירת embedding
        embedding = self.embedder.encode(content).tolist()
        
        # יצירת אובייקט מסמך
        document = {
            "content": content,
            "title": title,
            "category": category,
            "embedding": embedding
        }
        
        # שמירה ב-Weaviate
        self.client.data_object.create(
            data_object=document,
            class_name="Document"
        )
    
    async def search_similar(self, query: str, limit: int = 5) -> List[Dict]:
        """
        חיפוש מסמכים דומים
        
        Args:
            query: שאילתת חיפוש
            limit: מספר תוצאות מקסימלי
            
        Returns:
            רשימת מסמכים דומים עם ציונים
            
        הפונקציה:
        1. יוצרת embedding מהשאילתה
        2. מחפשת מסמכים דומים
        3. מחזירה תוצאות עם ציוני דמיון
        """
        # יצירת embedding מהשאילתה
        query_embedding = self.embedder.encode(query).tolist()
        
        # ביצוע חיפוש וקטורי
        result = (
            self.client.query
            .get("Document", ["content", "title", "category"])
            .with_near_vector({"vector": query_embedding})
            .with_limit(limit)
            .with_additional(["certainty"])
            .do()
        )
        
        return result["data"]["Get"]["Document"]
```

## 🔧 Configuration Files

### 📄 `docker-compose.advanced.yml`

```yaml
# ============================================================================
# Docker Compose - Advanced Enterprise Setup
# ============================================================================
# 
# קובץ Docker Compose למערכת מתקדמת עם:
# - Vector Database (Weaviate)
# - Graph Database (Neo4j)
# - PostgreSQL עם replication
# - Redis clustering
# - Monitoring stack
# ============================================================================

version: '3.8'

services:
  # ========================================================================
  # VECTOR DATABASE - WEAVIATE
  # ========================================================================
  weaviate:
    image: semitechnologies/weaviate:1.25.0
    restart: on-failure
    ports:
      - "8080:8080"    # HTTP API
      - "50051:50051"  # gRPC API
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'
      PERSISTENCE_DATA_PATH: '/var/lib/weaviate'
      DEFAULT_VECTORIZER_MODULE: 'none'  # נשתמש ב-embeddings שלנו
      ENABLE_MODULES: 'text2vec-transformers'
      CLUSTER_HOSTNAME: 'node1'
    volumes:
      - weaviate_data:/var/lib/weaviate
    networks:
      - chatnet
    # הסבר: Weaviate הוא vector database מתקדם לחיפוש סמנטי

  # ========================================================================
  # GRAPH DATABASE - NEO4J
  # ========================================================================
  neo4j:
    image: neo4j:5.19.0-community
    restart: on-failure
    ports:
      - "7474:7474"  # HTTP interface
      - "7687:7687"  # Bolt protocol
    environment:
      NEO4J_AUTH: neo4j/secure_neo4j_password_123
      NEO4J_db_fsync__metadata: "false"
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
    networks:
      - chatnet
    # הסבר: Neo4j הוא graph database לקשרים מורכבים

  # ========================================================================
  # POSTGRESQL DATABASE
  # ========================================================================
  postgres:
    image: postgres:15-alpine
    restart: on-failure
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-org_chatbot}
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-secure_postgres_password}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - chatnet
    # הסבר: PostgreSQL הוא ה-database הראשי

  # ========================================================================
  # REDIS CACHE
  # ========================================================================
  redis:
    image: redis:7-alpine
    restart: on-failure
    ports:
      - "6379:6379"
    command: redis-server --requirepass ${REDIS_PASSWORD:-secure_redis_password_123}
    volumes:
      - redis_data:/data
    networks:
      - chatnet
    # הסבר: Redis ל-session management ו-caching

  # ========================================================================
  # AI/LLM SERVICE - OLLAMA
  # ========================================================================
  ollama:
    image: ollama/ollama:latest
    restart: unless-stopped
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    networks:
      - chatnet
    entrypoint: ["/bin/sh","-lc","ollama serve & sleep 5 && ollama pull ${OLLAMA_MODEL:-llama3.2:3b} && ollama pull ${OLLAMA_FAST_MODEL:-phi3:3.8b} && wait"]
    # הסבר: Ollama מריץ LLM models מקומית

  # ========================================================================
  # CHAT API SERVICE
  # ========================================================================
  chat-api:
    build:
      context: ./chat-api
      dockerfile: Dockerfile.advanced
    restart: unless-stopped
    depends_on:
      - redis
      - minio
      - ollama
      - weaviate
      - neo4j
    environment:
      REDIS_URL: redis://:${REDIS_PASSWORD:-secure_redis_password_123}@redis:6379/0
      MINIO_ENDPOINT: http://minio:9000
      MINIO_ACCESS_KEY: ${MINIO_ROOT_USER:-admin}
      MINIO_SECRET_KEY: ${MINIO_ROOT_PASSWORD:-secure_minio_password_123}
      S3_BUCKET: ${S3_BUCKET:-chat-archive}
      OLLAMA_URL: http://ollama:11434
      OLLAMA_MODEL: ${OLLAMA_MODEL:-llama3.2:3b}
      OLLAMA_FAST_MODEL: ${OLLAMA_FAST_MODEL:-phi3:3.8b}
      SESSION_TTL_SECONDS: ${SESSION_TTL_SECONDS:-259200}
      WEAVIATE_URL: http://weaviate:8080
      NEO4J_URI: bolt://neo4j:7687
      NEO4J_USER: neo4j
      NEO4J_PASSWORD: secure_neo4j_password_123
    ports:
      - "8000:8000"
    networks:
      - chatnet
    # הסבר: השירות הראשי שמחבר בין כל הרכיבים

# ========================================================================
# VOLUMES
# ========================================================================
volumes:
  weaviate_data:
  neo4j_data:
  neo4j_logs:
  postgres_data:
  redis_data:
  ollama_data:
  minio_data:
  # הסבר: Volumes לאחסון נתונים מתמיד

# ========================================================================
# NETWORKS
# ========================================================================
networks:
  chatnet:
    driver: bridge
    # הסבר: רשת פנימית לכל השירותים
```

---

**תיעוד זה מספק הסבר מפורט על כל חלק במערכת, כולל מטרות, פונקציונליות, ופרטים טכניים.**
