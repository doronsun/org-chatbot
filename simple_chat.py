#!/usr/bin/env python3
"""
Simple Chat API - ללא Docker
מערכת פשוטה שתעבוד מיד
"""

import json
import time
from datetime import datetime
from typing import List, Dict, Any
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# FastAPI app
app = FastAPI(
    title="Simple Org Chatbot",
    description="צ'אטבוט ארגוני פשוט",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ChatRequest(BaseModel):
    message: str
    user_id: str = "default_user"
    session_id: str = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: str
    user_id: str

# Simple AI responses
AI_RESPONSES = {
    "איך מנהלים צוות": "ניהול צוות דורש תקשורת פתוחה, הגדרת יעדים ברורים, והקשבה לצרכים של כל חבר צוות. חשוב לתת משוב חיובי ולטפל בבעיות במהירות.",
    "מה השעה": "אני לא יכול לראות את השעה הנוכחית, אבל אני כאן לעזור עם שאלות ארגוניות!",
    "איך מתחילים פרויקט": "התחלת פרויקט כוללת: 1) הגדרת מטרות ברורות 2) תכנון לוח זמנים 3) הקצאת משאבים 4) זיהוי סיכונים 5) יצירת צוות מתאים.",
    "מה המדיניות החדשה": "אני לא יכול לגשת למדיניות ספציפית, אבל אני יכול לעזור להבין איך לבדוק מדיניות בחברה שלך.",
    "איך מטפלים בלחץ": "טיפול בלחץ כולל: 1) זיהוי מקורות הלחץ 2) תרגילי נשימה 3) ארגון זמן 4) תמיכה חברתית 5) פעילות גופנית.",
    "איך משפרים ביצועים": "שיפור ביצועים כולל: 1) הגדרת יעדים מדידים 2) משוב קבוע 3) פיתוח כישורים 4) אוטומציה של תהליכים 5) עבודה בצוות."
}

# Simple conversation storage
conversations = []

def get_ai_response(message: str) -> str:
    """מחזיר תשובה חכמה לפי מילות מפתח"""
    message_lower = message.lower().strip()
    
    # בדיקות ספציפיות
    if "לחץ" in message_lower or "stress" in message_lower:
        return "טיפול בלחץ כולל: 1) זיהוי מקורות הלחץ 2) תרגילי נשימה עמוקה 3) ארגון זמן יעיל 4) תמיכה חברתית ומקצועית 5) פעילות גופנית סדירה 6) שינה מספקת. חשוב לזהות את הסימנים המוקדמים ולטפל בהם לפני שהם מתגברים."
    
    elif "מדיניות" in message_lower or "policy" in message_lower:
        return "לגבי מדיניות החברה - אני לא יכול לגשת למסמכים ספציפיים, אבל אני יכול לעזור לך להבין איך לבדוק מדיניות: 1) פנה למחלקת HR 2) בדוק בפורטל העובדים 3) שאל את המנהל הישיר 4) בדוק בהודעות החברה. איזה סוג מדיניות אתה מחפש?"
    
    elif "צוות" in message_lower or "team" in message_lower or "מנהל" in message_lower:
        return "ניהול צוות דורש: 1) תקשורת פתוחה וברורה 2) הגדרת יעדים מדידים 3) הקשבה לצרכים של כל חבר צוות 4) מתן משוב חיובי ובונה 5) טיפול מהיר בבעיות 6) פיתוח כישורים 7) יצירת סביבה תומכת. איזה אספקט של ניהול צוות מעניין אותך?"
    
    elif "פרויקט" in message_lower or "project" in message_lower:
        return "התחלת פרויקט כוללת: 1) הגדרת מטרות ברורות ומדידות 2) תכנון לוח זמנים מציאותי 3) הקצאת משאבים מתאימים 4) זיהוי וניהול סיכונים 5) יצירת צוות מתאים 6) הגדרת תהליכי עבודה 7) מערכת מעקב והערכה. איזה שלב בפרויקט אתה מתחיל?"
    
    elif "ביצועים" in message_lower or "performance" in message_lower or "שיפור" in message_lower:
        return "שיפור ביצועים כולל: 1) הגדרת יעדים מדידים וברורים 2) מתן משוב קבוע ומבנה 3) פיתוח כישורים מקצועיים 4) אוטומציה של תהליכים חוזרים 5) עבודה בצוות יעילה 6) ניהול זמן טוב 7) למידה מתמדת. איזה תחום ביצועים אתה רוצה לשפר?"
    
    elif "שעה" in message_lower or "time" in message_lower:
        return "אני לא יכול לראות את השעה הנוכחית, אבל אני כאן לעזור עם שאלות ארגוניות וניהוליות! איך אני יכול לעזור לך עם עבודה או פיתוח עסקי?"
    
    elif "שלום" in message_lower or "היי" in message_lower or "hello" in message_lower:
        return "שלום! אני העוזר הארגוני החכם שלך. אני כאן לעזור עם שאלות עסקיות, ניהול, פיתוח מוצרים, אסטרטגיות שיווק, וניהול צוותים. איך אני יכול לעזור לך היום?"
    
    # תשובה כללית חכמה יותר
    return f"תודה על השאלה '{message}'. אני כאן לעזור עם שאלות ארגוניות, ניהול, פיתוח עסקי, וניהול צוותים. איזה תחום ספציפי מעניין אותך? אוכל לעזור עם ניהול, פיתוח, שיווק, או כל נושא עסקי אחר."

@app.get("/")
async def root():
    return {"message": "שלום! אני העוזר הארגוני החכם שלך", "status": "running"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "conversations_count": len(conversations)
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """נקודת קצה לצ'אט"""
    try:
        # יצירת session_id אם לא קיים
        session_id = request.session_id or f"session_{int(time.time())}"
        
        # קבלת תשובה מ-AI
        response = get_ai_response(request.message)
        
        # שמירת השיחה
        conversation = {
            "user_id": request.user_id,
            "session_id": session_id,
            "message": request.message,
            "response": response,
            "timestamp": datetime.now().isoformat()
        }
        conversations.append(conversation)
        
        return ChatResponse(
            response=response,
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
            user_id=request.user_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"שגיאה: {str(e)}")

@app.get("/conversations")
async def get_conversations(user_id: str = None):
    """קבלת היסטוריית שיחות"""
    if user_id:
        user_conversations = [c for c in conversations if c["user_id"] == user_id]
        return {"conversations": user_conversations}
    return {"conversations": conversations}

@app.get("/stats")
async def get_stats():
    """סטטיסטיקות"""
    return {
        "total_conversations": len(conversations),
        "unique_users": len(set(c["user_id"] for c in conversations)),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    print("🚀 מפעיל את העוזר הארגוני החכם...")
    print("📱 פתח את הדפדפן ב: http://localhost:8000")
    print("📚 תיעוד API: http://localhost:8000/docs")
    print("❤️ בריאות המערכת: http://localhost:8000/health")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
