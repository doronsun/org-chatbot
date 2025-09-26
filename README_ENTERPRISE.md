# 🚀 Enterprise Chatbot System

מערכת צ'אטבוט ארגוני מתקדמת ברמה enterprise עם DevOps מלא, AI מתקדם, ו-observability מלא.

## 🎯 תכונות מתקדמות

### 🤖 AI & Machine Learning
- **OpenAI GPT-4 Integration** - בינה מלאכותית מתקדמת
- **Semantic Search** - חיפוש חכם עם Weaviate Vector DB
- **Graph Database** - Neo4j לניתוח קשרים מורכבים
- **Embedding Models** - Sentence Transformers מתקדמים
- **Context Awareness** - זיכרון שיחות מתקדם

### 🗄️ Databases & Storage
- **PostgreSQL** - מסד נתונים ראשי עם replication
- **Redis** - Caching ו-session management
- **Weaviate** - Vector database לחיפוש סמנטי
- **Neo4j** - Graph database לקשרים מורכבים
- **MinIO** - Object storage לאחסון קבצים

### 🔧 DevOps & Infrastructure
- **Docker Compose** - Containerization מלא
- **Kubernetes** - Orchestration מתקדם
- **CI/CD Pipeline** - GitHub Actions אוטומטי
- **Auto-scaling** - HPA ו-VPA
- **Health Checks** - ניטור מתמיד
- **Security** - JWT, encryption, secrets management

### 📊 Monitoring & Observability
- **Prometheus** - Metrics collection
- **Grafana** - Dashboards מתקדמים
- **Jaeger** - Distributed tracing
- **Elasticsearch** - Log storage
- **Kibana** - Log visualization
- **Structured Logging** - JSON logs

### 🚀 Performance & Scalability
- **Auto-scaling** - עד 10 replicas
- **Load Balancing** - Nginx reverse proxy
- **Caching** - Redis multi-layer
- **Rate Limiting** - הגנה מפני abuse
- **Connection Pooling** - Database optimization

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API    │    │   AI Services   │
│   React + TS    │◄──►│   FastAPI        │◄──►│   OpenAI        │
│   Nginx         │    │   Python 3.11    │    │   Ollama        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   Databases     │    │   Monitoring    │
│   Nginx         │    │   PostgreSQL    │    │   Prometheus    │
│   SSL/TLS       │    │   Redis         │    │   Grafana       │
└─────────────────┘    │   Weaviate      │    │   Jaeger        │
                       │   Neo4j         │    │   Elasticsearch │
                       │   MinIO         │    │   Kibana        │
                       └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### 1. Prerequisites
```bash
# Docker & Docker Compose
docker --version
docker-compose --version

# Git
git --version
```

### 2. Clone & Setup
```bash
git clone <repository-url>
cd org-chatbot
chmod +x start-enterprise.sh
```

### 3. Start System
```bash
./start-enterprise.sh
```

### 4. Access Services
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics

## 📊 Monitoring Dashboard

### Prometheus
- **URL**: http://localhost:9090
- **Metrics**: CPU, Memory, Request rates, Response times

### Grafana
- **URL**: http://localhost:3001
- **Username**: admin
- **Password**: enterprise_grafana_2024
- **Dashboards**: System overview, Application metrics, Database performance

### Jaeger
- **URL**: http://localhost:16686
- **Tracing**: Distributed request tracing

### Kibana
- **URL**: http://localhost:5601
- **Logs**: Application logs, Error tracking

## 🗄️ Database Access

### PostgreSQL
```bash
docker exec -it org-chatbot-postgres-1 psql -U postgres -d enterprise_chatbot
```

### Redis
```bash
docker exec -it org-chatbot-redis-1 redis-cli
```

### Neo4j
- **URL**: http://localhost:7474
- **Username**: neo4j
- **Password**: enterprise_neo4j_2024

### Weaviate
- **URL**: http://localhost:8080
- **GraphQL**: http://localhost:8080/v1/graphql

### MinIO
- **URL**: http://localhost:9000
- **Username**: admin
- **Password**: enterprise_minio_2024

## 🔧 Development

### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.enterprise.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd frontend
npm install
npm start
```

### Testing
```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend
npm test
```

## 🚀 Production Deployment

### Docker Compose
```bash
docker-compose -f docker-compose.enterprise.yml up -d
```

### Kubernetes
```bash
kubectl apply -f k8s/enterprise/
kubectl get pods -n enterprise-chatbot
```

### CI/CD
- **GitHub Actions** - אוטומטי
- **Docker Registry** - GHCR
- **Kubernetes** - Auto-deployment

## 🔒 Security

### Authentication
- **JWT Tokens** - Secure authentication
- **Rate Limiting** - Protection against abuse
- **CORS** - Cross-origin security
- **SSL/TLS** - Encrypted communication

### Secrets Management
- **Environment Variables** - Secure configuration
- **Kubernetes Secrets** - Production secrets
- **Encryption** - Data encryption at rest

## 📈 Performance

### Metrics
- **Request Rate** - Requests per second
- **Response Time** - Average response time
- **Error Rate** - Error percentage
- **Throughput** - Data processed per second

### Scaling
- **Horizontal Pod Autoscaler** - Auto-scaling based on metrics
- **Vertical Pod Autoscaler** - Resource optimization
- **Load Balancing** - Traffic distribution

## 🛠️ Troubleshooting

### Common Issues
```bash
# Check service status
docker-compose -f docker-compose.enterprise.yml ps

# View logs
docker-compose -f docker-compose.enterprise.yml logs -f

# Restart services
docker-compose -f docker-compose.enterprise.yml restart

# Clean restart
docker-compose -f docker-compose.enterprise.yml down -v
docker-compose -f docker-compose.enterprise.yml up -d
```

### Health Checks
```bash
# Backend health
curl http://localhost:8000/health

# Frontend health
curl http://localhost:3000

# Database health
docker exec -it org-chatbot-postgres-1 pg_isready
```

## 📚 API Documentation

### Endpoints
- `GET /` - Root endpoint
- `GET /health` - Health check
- `POST /chat` - Chat endpoint
- `GET /metrics` - Prometheus metrics
- `GET /conversations/{user_id}` - User conversations
- `GET /stats` - System statistics

### Request Format
```json
{
  "message": "איך מנהלים צוות?",
  "user_id": "user_123",
  "session_id": "session_456"
}
```

### Response Format
```json
{
  "response": "ניהול יעיל דורש...",
  "session_id": "session_456",
  "timestamp": "2024-01-01T12:00:00Z",
  "user_id": "user_123",
  "sources": [],
  "confidence": 0.85,
  "tokens_used": 56,
  "processing_time": 0.123
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

- **Issues**: GitHub Issues
- **Documentation**: README files
- **Monitoring**: Grafana dashboards
- **Logs**: Kibana interface

---

**🚀 Enterprise Chatbot System - מערכת מתקדמת ברמה enterprise!**
