#!/bin/bash

echo "🤖 מתחיל להפעיל את העוזר הארגוני החכם..."

# בדיקה אם Docker מותקן
if ! command -v docker &> /dev/null; then
    echo "❌ Docker לא מותקן. אנא התקן Docker תחילה."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose לא מותקן. אנא התקן Docker Compose תחילה."
    exit 1
fi

# מעבר לתיקיית compose
cd compose

# יצירת קובץ .env אם לא קיים
if [ ! -f .env ]; then
    echo "📝 יוצר קובץ הגדרות..."
    cp env.example .env
    echo "✅ קובץ .env נוצר. תוכל לערוך אותו לפי הצורך."
fi

# הפעלת השירותים
echo "🚀 מפעיל את השירותים..."
docker-compose up -d

# המתנה לשירותים להתחיל
echo "⏳ ממתין לשירותים להתחיל..."
sleep 10

# בדיקת סטטוס השירותים
echo "📊 בודק סטטוס השירותים..."
docker-compose ps

echo ""
echo "🎉 העוזר הארגוני החכם הופעל בהצלחה!"
echo ""
echo "🌐 גישה לאפליקציה:"
echo "   Frontend: http://localhost:3000"
echo "   API:      http://localhost:8000"
echo "   MinIO:    http://localhost:9001"
echo ""
echo "📋 פקודות שימושיות:"
echo "   docker-compose logs -f     # צפייה בלוגים"
echo "   docker-compose down        # עצירת השירותים"
echo "   docker-compose restart     # הפעלה מחדש"
echo ""
echo "🔧 לפתרון בעיות, ראה את ה-README.md"
