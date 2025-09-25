from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import asyncio
import json

app = FastAPI(title="Simple Chat API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_response(prompt: str) -> str:
    """Generate Hebrew responses based on keywords"""
    prompt_lower = prompt.lower()
    
    if any(word in prompt_lower for word in ['מוצר', 'פיתוח', 'חדש']):
        return """שלום! אני שמח לעזור בפיתוח מוצר חדש.

תהליך מומלץ:
1. מחקר שוק - בדוק צרכי לקוחות
2. אפיון מוצר - הגדר תכונות עיקריות  
3. אב טיפוס - צור גרסה ראשונית
4. בדיקת שוק - קבל פידבק
5. שיפורים - תקן בעיות

האם תרצה שאעמיק באחד מהשלבים?"""

    elif any(word in prompt_lower for word in ['שיווק', 'דיגיטלי', 'קמפיין']):
        return """שלום! קמפיין שיווק דיגיטלי הוא דרך מצוינת להגיע ללקוחות.

אסטרטגיה מומלצת:
1. הגדרת יעדים - מה אתה רוצה להשיג?
2. זיהוי קהל יעד - מי הלקוחות שלך?
3. בחירת ערוצים - פייסבוק, גוגל, אינסטגרם?
4. תוכן איכותי - צור תוכן רלוונטי
5. מדידה ומעקב - עקוב אחר תוצאות

איזה ערוץ שיווק מעניין אותך?"""

    elif any(word in prompt_lower for word in ['צוות', 'ניהול', 'יעיל']):
        return """שלום! ניהול צוות יעיל הוא מפתח להצלחה עסקית.

עקרונות חשובים:
1. תקשורת ברורה - הגדר ציפיות ותפקידים
2. האצלת סמכויות - תן לצוות אחריות
3. פידבק קבוע - בדוק התקדמות
4. הכרה והוקרה - הערך עבודה טובה
5. פיתוח אישי - השקע בהכשרה

איך אתה רואה את האתגרים בניהול הצוות?"""

    else:
        return f"""שלום! אני העוזר הארגוני החכם שלך.

אני כאן לעזור עם:
💡 פיתוח מוצרים ושירותים
📈 אסטרטגיות שיווק
👥 ניהול צוותים ופרויקטים
🤖 טכנולוגיה ובינה מלאכותית

השאלה שלך: "{prompt}"

איך אני יכול לעזור לך? נסה לשאול על אחד מהתחומים האלה."""

async def stream_response(text: str):
    """Stream response word by word"""
    words = text.split(' ')
    for i, word in enumerate(words):
        yield word + (' ' if i < len(words) - 1 else '')
        await asyncio.sleep(0.1)

@app.get("/")
async def root():
    return {"message": "Chat API is running!", "status": "ok"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "Simple Chat API"}

@app.post("/chat")
async def chat(data: dict):
    prompt = data.get("prompt", "")
    if not prompt:
        return {"error": "Prompt is required"}
    
    response_text = get_response(prompt)
    
    return StreamingResponse(
        stream_response(response_text),
        media_type="text/plain; charset=utf-8"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
