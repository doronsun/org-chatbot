# 🆘 Support & Help

## 🚀 Getting Started

### 📖 Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/doronsun/org-chatbot.git
   cd org-chatbot
   ```

2. **Run the quick start script**:
   ```bash
   ./quick-start.sh
   ```

3. **Access the application**:
   - Frontend: http://localhost:3000
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### 📚 Documentation

- 📖 [Complete README](README.md)
- 🏗️ [Architecture Guide](docs/architecture-diagrams.md)
- 🚀 [Deployment Guide](docs/deployment-guide.md)
- 🔒 [Security Guide](SECURITY.md)
- 🤝 [Contributing Guide](CONTRIBUTING.md)

## 🆘 Getting Help

### 🔍 Before Asking for Help

1. **Check existing issues**: Search [GitHub Issues](https://github.com/doronsun/org-chatbot/issues)
2. **Read the documentation**: Check the [README](README.md) and [docs](docs/)
3. **Search discussions**: Look through [GitHub Discussions](https://github.com/doronsun/org-chatbot/discussions)
4. **Check the FAQ**: See common questions below

### 📞 How to Get Support

#### 🐛 Bug Reports

Found a bug? Please:

1. **Search existing issues** to avoid duplicates
2. **Use the bug report template** when creating an issue
3. **Provide detailed information**:
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details
   - Error logs

#### ✨ Feature Requests

Have an idea? Please:

1. **Check existing feature requests**
2. **Use the feature request template**
3. **Provide clear description** of the feature
4. **Explain the problem** it solves

#### 💬 General Questions

For general questions:

1. **GitHub Discussions**: [Ask a question](https://github.com/doronsun/org-chatbot/discussions/categories/q-a)
2. **Discord Community**: Join our [Discord server](https://discord.gg/org-chatbot)
3. **Email Support**: support@org-chatbot.com

## ❓ Frequently Asked Questions

### 🚀 Deployment Questions

**Q: How do I deploy to production?**
A: Use the production deployment script:
```bash
./scripts/deploy.sh production
```

**Q: Can I deploy to Kubernetes?**
A: Yes! Use the Kubernetes manifests in the `k8s/` directory:
```bash
kubectl apply -f k8s/
```

**Q: What are the system requirements?**
A: Minimum requirements:
- 4GB RAM
- 2 CPU cores
- 20GB disk space
- Docker and Docker Compose

### 🤖 AI Questions

**Q: How do I change the AI model?**
A: Update the `OLLAMA_MODEL` environment variable in your `.env` file:
```bash
OLLAMA_MODEL=llama3.2:3b
```

**Q: Can I use my own AI models?**
A: Yes! Ollama supports custom models. Add them to your Ollama instance.

**Q: How do I improve AI responses?**
A: Customize the system prompt in the chat API configuration.

### 🔧 Technical Questions

**Q: How do I enable HTTPS?**
A: Configure SSL certificates in your ingress configuration or use a reverse proxy.

**Q: How do I scale the application?**
A: Use Kubernetes HPA (Horizontal Pod Autoscaler) or Docker Swarm scaling.

**Q: How do I backup the data?**
A: Use the built-in backup scripts or implement your own backup strategy.

### 🔒 Security Questions

**Q: How do I secure the application?**
A: Follow the [Security Guide](SECURITY.md) and use the provided security configurations.

**Q: How do I enable authentication?**
A: Configure JWT tokens and implement user management in your deployment.

**Q: How do I audit user activities?**
A: Enable audit logging and use the monitoring stack to track activities.

## 🛠️ Troubleshooting

### 🐳 Docker Issues

**Problem**: Docker containers not starting
**Solution**:
```bash
# Check Docker status
docker ps
docker logs <container_name>

# Restart services
docker-compose down
docker-compose up -d
```

**Problem**: Port conflicts
**Solution**:
```bash
# Check what's using the port
lsof -i :8000
lsof -i :3000

# Kill conflicting processes
kill -9 <PID>
```

### ☸️ Kubernetes Issues

**Problem**: Pods not starting
**Solution**:
```bash
# Check pod status
kubectl get pods -n org-chatbot

# Check pod logs
kubectl logs <pod-name> -n org-chatbot

# Check events
kubectl get events -n org-chatbot
```

**Problem**: Services not accessible
**Solution**:
```bash
# Check service status
kubectl get svc -n org-chatbot

# Check ingress
kubectl get ingress -n org-chatbot

# Port forward for testing
kubectl port-forward svc/frontend 3000:80 -n org-chatbot
```

### 🤖 AI Service Issues

**Problem**: AI not responding
**Solution**:
```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# Restart Ollama service
docker restart ollama

# Check model availability
ollama list
```

**Problem**: Slow AI responses
**Solution**:
- Use a faster model (phi3 instead of llama3.2)
- Increase GPU resources
- Optimize prompt length

### 💾 Database Issues

**Problem**: Database connection errors
**Solution**:
```bash
# Check database status
docker exec postgres pg_isready

# Check connection string
echo $DATABASE_URL

# Restart database
docker restart postgres
```

**Problem**: Data loss
**Solution**:
- Check backup files
- Restore from latest backup
- Verify data persistence configuration

## 📊 Monitoring & Debugging

### 📈 Health Checks

**Check application health**:
```bash
# API health
curl http://localhost:8000/health

# Frontend health
curl http://localhost:3000/health

# Database health
docker exec postgres pg_isready
```

### 📊 Monitoring Dashboard

Access monitoring tools:
- **Grafana**: http://localhost:3001
- **Prometheus**: http://localhost:9090
- **API Metrics**: http://localhost:8000/metrics

### 🔍 Log Analysis

**View logs**:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f chat-api

# Kubernetes logs
kubectl logs -f deployment/chat-api -n org-chatbot
```

## 🆘 Emergency Support

### 🚨 Critical Issues

For critical production issues:

1. **Immediate Response**: Email critical@org-chatbot.com
2. **Include**: Error logs, impact description, urgency level
3. **Response Time**: Within 2 hours for critical issues

### 📞 Contact Information

- **General Support**: support@org-chatbot.com
- **Security Issues**: security@org-chatbot.com
- **Critical Issues**: critical@org-chatbot.com
- **Business Inquiries**: business@org-chatbot.com

### 💬 Community Support

- **Discord**: [Join our community](https://discord.gg/org-chatbot)
- **GitHub Discussions**: [Ask questions](https://github.com/doronsun/org-chatbot/discussions)
- **Stack Overflow**: Tag questions with `org-chatbot`

## 📚 Additional Resources

### 🎓 Learning Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://reactjs.org/docs/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Docker Documentation](https://docs.docker.com/)

### 🛠️ Development Tools

- [VS Code Extensions](docs/vscode-extensions.md)
- [Development Setup](docs/development-setup.md)
- [Testing Guide](docs/testing-guide.md)
- [Code Style Guide](docs/code-style.md)

### 🔗 External Links

- [Docker Hub](https://hub.docker.com/r/doronsun/org-chatbot)
- [Helm Charts](https://github.com/doronsun/org-chatbot-helm)
- [Live Demo](https://org-chatbot-demo.vercel.app)
- [API Documentation](https://api.org-chatbot.com/docs)

---

## 💝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

**Thank you for using Org Chatbot! 🎉**
