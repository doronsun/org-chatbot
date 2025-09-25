import os
import json
import time
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator, List, Dict

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Simple Org Chat API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for demo
sessions = {}

def _ts():
    return datetime.now(timezone.utc).isoformat()

def get_mock_response(user_prompt: str) -> str:
    """Generate a mock intelligent response in Hebrew"""
    
    # Simple keyword-based responses
    prompt_lower = user_prompt.lower()
    
    if any(word in prompt_lower for word in ['מוצר', 'פיתוח', 'חדש']):
        return """שלום! אני שמח לעזור בפיתוח מוצר חדש. 

להלן תהליך מומלץ:
1. **מחקר שוק** - בדוק את הצרכים של הלקוחות
2. **אפיון מוצר** - הגדר את התכונות העיקריות
3. **אב טיפוס** - צור גרסה ראשונית לבדיקה
4. **בדיקת שוק** - קבל פידבק מהלקוחות
5. **שיפורים** - תקן בעיות ושלם תכונות

האם תרצה שאעמיק באחד מהשלבים?"""

    elif any(word in prompt_lower for word in ['שיווק', 'דיגיטלי', 'קמפיין']):
        return """שלום! קמפיין שיווק דיגיטלי הוא דרך מצוינת להגיע ללקוחות.

**אסטרטגיה מומלצת:**
1. **הגדרת יעדים** - מה אתה רוצה להשיג?
2. **זיהוי קהל יעד** - מי הלקוחות שלך?
3. **בחירת ערוצים** - פייסבוק, גוגל, אינסטגרם?
4. **תוכן איכותי** - צור תוכן רלוונטי ומעניין
5. **מדידה ומעקב** - עקוב אחר התוצאות

איזה ערוץ שיווק מעניין אותך הכי הרבה?"""

    elif any(word in prompt_lower for word in ['צוות', 'ניהול', 'יעיל']):
        return """שלום! ניהול צוות יעיל הוא מפתח להצלחה עסקית.

**עקרונות חשובים:**
1. **תקשורת ברורה** - הגדר ציפיות ותפקידים
2. **האצלת סמכויות** - תן לצוות אחריות
3. **פידבק קבוע** - בדוק התקדמות באופן קבוע
4. **הכרה והוקרה** - הערך את העבודה הטובה
5. **פיתוח אישי** - השקע בהכשרה והתפתחות

איך אתה רואה את האתגרים הנוכחיים בניהול הצוות?"""

    elif any(word in prompt_lower for word in ['בינה', 'מלאכותית', 'ai', 'טכנולוגיה']):
        return """שלום! בינה מלאכותית יכולה לשנות את העסק שלך לטובה!

**שימושים עסקיים:**
1. **אוטומציה** - משימות חוזרות ופשוטות
2. **ניתוח נתונים** - הבנת הלקוחות והשוק
3. **שירות לקוחות** - צ'אטבוטים ועזרה 24/7
4. **תוכן** - יצירת טקסטים ותמונות
5. **חיזוי** - תחזיות מכירות ומגמות

איזה תחום בעסק שלך הכי מעניין אותך לשפר עם AI?"""

    else:
        return f"""שלום! אני העוזר הארגוני החכם שלך.

אני כאן לעזור לך עם:
- 💡 פיתוח מוצרים ושירותים
- 📈 אסטרטגיות שיווק ועסקים
- 👥 ניהול צוותים ופרויקטים
- 🤖 טכנולוגיה ובינה מלאכותית
- 📊 ניתוח נתונים ותחזיות

השאלה שלך: "{user_prompt}"

איך אני יכול לעזור לך באופן ספציפי יותר? נסה לשאול על אחד מהתחומים האלה או ספר לי יותר על האתגר שלך."""

async def mock_stream_response(response_text: str) -> AsyncGenerator[str, None]:
    """Simulate streaming response by sending chunks"""
    words = response_text.split(' ')
    for i, word in enumerate(words):
        yield word + (' ' if i < len(words) - 1 else '')
        # Small delay to simulate real streaming
        await asyncio.sleep(0.05)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Simple Chat API",
        "timestamp": _ts()
    }

@app.post("/chat")
async def chat(body: Dict):
    session_id = (body.get("session_id") or "").strip()
    prompt = (body.get("prompt") or "").strip()
    
    if not session_id or not prompt:
        raise HTTPException(400, "session_id ו-prompt חובה")

    # Get or create session
    if session_id not in sessions:
        sessions[session_id] = []
    
    # Store user message
    user_message = {
        "id": f"user_{int(time.time())}",
        "role": "user", 
        "content": prompt,
        "timestamp": _ts()
    }
    sessions[session_id].append(user_message)

    # Generate response
    response_text = get_mock_response(prompt)
    
    # Store assistant message
    assistant_message = {
        "id": f"assistant_{int(time.time())}",
        "role": "assistant",
        "content": response_text,
        "timestamp": _ts()
    }
    sessions[session_id].append(assistant_message)

    async def generate_response():
        async for chunk in mock_stream_response(response_text):
            yield chunk

    return StreamingResponse(
        generate_response(),
        media_type="text/plain; charset=utf-8"
    )

@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    if session_id not in sessions:
        return {"session_id": session_id, "messages": []}
    
    return {
        "session_id": session_id,
        "messages": sessions[session_id]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
