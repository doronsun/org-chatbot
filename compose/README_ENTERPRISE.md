# 🚀 Enterprise Chatbot - מערכת צ'אטבוט ארגונית מתקדמת

מערכת צ'אטבוט ארגונית שמיועדת לטפל במיליוני בקשות עם אבטחה מתקדמת וארכיטקטורה סקלבילית.

## 🏗️ ארכיטקטורה

```
Internet → CloudFlare → HAProxy → [API Instances] → Redis Cluster
                    ↓                    ↓              ↓
                Rate Limiting        Queue System    MinIO Cluster
                    ↓                    ↓              ↓
                Auth Service         Ollama Cluster   Monitoring
```

## 🚀 תכונות מתקדמות

### ⚡ ביצועים
- **Load Balancing** עם HAProxy
- **Multiple API Instances** (3 instances)
- **Connection Pooling** ו-Keep-Alive
- **Streaming Responses** בזמן אמת
- **Async Processing** עם Queue System

### 🔒 אבטחה
- **JWT Authentication** עם bcrypt
- **Rate Limiting** (100 requests/minute per user)
- **HTTPS Support** עם SSL termination
- **Security Headers** (HSTS, XSS Protection)
- **Input Validation** ו-Sanitization

### 📊 ניטור ומעקב
- **Prometheus Metrics** לכל service
- **Grafana Dashboards** למעקב בזמן אמת
- **Health Checks** אוטומטיים
- **Performance Monitoring**
- **Error Tracking**

### 💾 אחסון וזיכרון
- **Redis Cluster** לזיכרון קצר טווח
- **MinIO S3-compatible** לארכוב
- **Session Management** מתקדם
- **Message Archiving** אוטומטי

## 🛠️ התקנה והפעלה

### דרישות מערכת
- Docker & Docker Compose
- 8GB RAM (מומלץ)
- 4 CPU cores (מומלץ)
- 50GB Disk space

### הפעלה מהירה
```bash
# הפעלת המערכת הארגונית
./deploy_enterprise.sh
```

### הפעלה ידנית
```bash
# בניית השירותים
docker-compose -f docker-compose.production.yml build

# הפעלת השירותים
docker-compose -f docker-compose.production.yml up -d

# בדיקת סטטוס
docker-compose -f docker-compose.production.yml ps
```

## 📊 URLs ופורטים

| שירות | URL | פורט | תיאור |
|--------|-----|------|-------|
| Chat API | http://localhost | 80 | API הראשי |
| Auth Service | http://localhost:8001 | 8001 | אימות משתמשים |
| Grafana | http://localhost:3000 | 3000 | דשבורד ניטור |
| Prometheus | http://localhost:9090 | 9090 | metrics |
| HAProxy Stats | http://localhost:8404/stats | 8404 | load balancer stats |
| MinIO Console | http://localhost:9001 | 9001 | ניהול אחסון |

## 🔐 הרשאות ברירת מחדל

### Grafana
- **משתמש:** admin
- **סיסמה:** EnterpriseGrafana2024!

### MinIO Console
- **משתמש:** admin
- **סיסמה:** EnterpriseMinio2024!Secure

## 🧪 בדיקת המערכת

### 1. הרשמת משתמש חדש
```bash
curl -X POST http://localhost:8001/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123",
    "email": "test@company.com",
    "organization": "TestOrg"
  }'
```

### 2. התחברות
```bash
curl -X POST http://localhost:8001/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123"
  }'
```

### 3. שליחת הודעה
```bash
curl -X POST http://localhost/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "session_id": "session123",
    "prompt": "שלום, איך אתה?"
  }'
```

## 📈 מעקב ביצועים

### Grafana Dashboards
1. פתח http://localhost:3000
2. התחבר עם admin/EnterpriseGrafana2024!
3. צפה ב-dashboards:
   - Chat API Performance
   - System Resources
   - Request Rates
   - Error Rates

### Prometheus Queries
```promql
# מספר בקשות לשנייה
rate(chat_requests_total[5m])

# זמן תגובה ממוצע
histogram_quantile(0.95, chat_request_duration_seconds)

# מספר sessions פעילים
chat_active_sessions_total
```

## 🔧 הגדרות מתקדמות

### Rate Limiting
ערוך את `env.enterprise`:
```bash
RATE_LIMIT_PER_MINUTE=200  # הגדל לפי הצורך
```

### Memory Limits
ערוך את `docker-compose.production.yml`:
```yaml
deploy:
  resources:
    limits:
      memory: 1G  # הגדל לפי הצורך
```

### SSL/TLS
1. הכנס certificates ל-`haproxy/ssl/`
2. עדכן את `haproxy.cfg`
3. הפעל מחדש

## 🚨 Troubleshooting

### בעיות נפוצות

**1. שירות לא עולה**
```bash
# בדוק logs
docker-compose -f docker-compose.production.yml logs [service_name]

# בדוק resources
docker stats
```

**2. Rate Limit גבוה מדי**
```bash
# בדוק Redis
docker exec -it compose-redis-cluster-1 redis-cli
> KEYS rate_limit:*
```

**3. בעיות זיכרון**
```bash
# בדוק memory usage
docker stats --no-stream
```

### Logs
```bash
# כל השירותים
docker-compose -f docker-compose.production.yml logs -f

# שירות ספציפי
docker-compose -f docker-compose.production.yml logs -f chat-api-1
```

## 📊 Benchmarks

### ביצועים צפויים
- **Requests/second:** 1,000+ (עם 3 API instances)
- **Response time:** <200ms (95th percentile)
- **Concurrent users:** 10,000+
- **Memory usage:** ~4GB total
- **CPU usage:** ~60% (under load)

### Scalability
- **Horizontal scaling:** הוסף עוד API instances
- **Vertical scaling:** הגדל memory/CPU limits
- **Database scaling:** Redis Cluster, MinIO Distributed

## 🔄 Updates ו-Maintenance

### עדכון המערכת
```bash
# עצירת השירותים
docker-compose -f docker-compose.production.yml down

# עדכון קוד
git pull

# בנייה מחדש
docker-compose -f docker-compose.production.yml build --no-cache

# הפעלה
docker-compose -f docker-compose.production.yml up -d
```

### Backup
```bash
# Redis backup
docker exec compose-redis-cluster-1 redis-cli BGSAVE

# MinIO backup
mc mirror minio/enterprise-chat-archive backup/
```

## 📞 תמיכה

לשאלות ובעיות:
1. בדוק את ה-logs
2. בדוק את ה-metrics ב-Grafana
3. בדוק את ה-health checks
4. צור issue ב-GitHub

---

**🚀 המערכת מוכנה לטפל במיליוני בקשות!**
