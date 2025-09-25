# 🤝 Contributing to Org Chatbot

Thank you for your interest in contributing to Org Chatbot! This document provides guidelines and information for contributors.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Guidelines](#contributing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)

## 📜 Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

### Our Pledge

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

## 🚀 Getting Started

### Prerequisites

- **Docker** (v20.10+)
- **Docker Compose** (v2.0+)
- **Node.js** (v18+)
- **Python** (v3.11+)
- **kubectl** (v1.24+)
- **Git** (v2.30+)

### Fork and Clone

```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/YOUR_USERNAME/org-chatbot.git
cd org-chatbot

# Add upstream remote
git remote add upstream https://github.com/original-username/org-chatbot.git
```

## 🛠️ Development Setup

### Backend Development

```bash
cd api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Full Stack Development

```bash
# Start all services with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 📝 Contributing Guidelines

### Types of Contributions

We welcome several types of contributions:

- 🐛 **Bug Fixes**: Fix existing issues
- ✨ **New Features**: Add new functionality
- 📚 **Documentation**: Improve or add documentation
- 🧪 **Tests**: Add or improve test coverage
- 🎨 **UI/UX**: Improve user interface and experience
- 🔧 **DevOps**: Improve CI/CD, deployment, or infrastructure
- 🌐 **Internationalization**: Add support for new languages

### Development Workflow

1. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Your Changes**
   - Write clean, readable code
   - Add tests for new functionality
   - Update documentation as needed
   - Follow our coding standards

3. **Test Your Changes**
   ```bash
   # Run all tests
   npm test              # Frontend tests
   pytest               # Backend tests
   docker-compose -f docker-compose.test.yml up --abort-on-container-exit
   ```

4. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

5. **Push and Create Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```

## 🔄 Pull Request Process

### Before Submitting

- [ ] Ensure all tests pass
- [ ] Update documentation if needed
- [ ] Add tests for new functionality
- [ ] Ensure code follows our style guidelines
- [ ] Update CHANGELOG.md if applicable

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

### Review Process

1. **Automated Checks**: CI/CD pipeline runs automatically
2. **Code Review**: At least one maintainer reviews the PR
3. **Testing**: Ensure all tests pass
4. **Approval**: Maintainer approves the PR
5. **Merge**: PR is merged to main branch

## 🐛 Issue Reporting

### Before Creating an Issue

- Check if the issue already exists
- Search closed issues for similar problems
- Ensure you're using the latest version

### Issue Template

```markdown
## Bug Report

### Description
Clear and concise description of the bug

### Steps to Reproduce
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

### Expected Behavior
What you expected to happen

### Actual Behavior
What actually happened

### Environment
- OS: [e.g., macOS 13.0]
- Browser: [e.g., Chrome 119]
- Version: [e.g., 1.2.3]

### Additional Context
Any other context about the problem
```

## 📏 Coding Standards

### Python (Backend)

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use type hints for all functions
- Maximum line length: 88 characters (Black formatter)
- Use descriptive variable and function names

```python
# Good
async def get_user_by_id(user_id: str) -> Optional[User]:
    """Get user by ID from database."""
    return await db.users.find_one({"_id": user_id})

# Bad
async def get_user(id):
    return await db.users.find_one({"_id": id})
```

### TypeScript/JavaScript (Frontend)

- Use TypeScript for all new code
- Follow [Airbnb Style Guide](https://github.com/airbnb/javascript)
- Use functional components with hooks
- Maximum line length: 100 characters

```typescript
// Good
interface UserProps {
  id: string;
  name: string;
  email: string;
}

const UserComponent: React.FC<UserProps> = ({ id, name, email }) => {
  return (
    <div className="user-card">
      <h3>{name}</h3>
      <p>{email}</p>
    </div>
  );
};

// Bad
const UserComponent = (props) => {
  return <div><h3>{props.name}</h3><p>{props.email}</p></div>
}
```

### Kubernetes Manifests

- Use consistent naming conventions
- Include resource limits and requests
- Add proper labels and annotations
- Include health checks

```yaml
# Good
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chat-api
  labels:
    app: chat-api
    version: v1.0.0
spec:
  replicas: 3
  selector:
    matchLabels:
      app: chat-api
  template:
    metadata:
      labels:
        app: chat-api
    spec:
      containers:
      - name: chat-api
        image: org-chatbot/chat-api:v1.0.0
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
```

## 🧪 Testing

### Frontend Testing

```bash
# Unit tests
npm test

# Integration tests
npm run test:integration

# E2E tests
npm run test:e2e

# Coverage
npm run test:coverage
```

### Backend Testing

```bash
# Unit tests
pytest

# Integration tests
pytest tests/integration/

# Coverage
pytest --cov=app --cov-report=html
```

### Performance Testing

```bash
# Load testing with k6
k6 run tests/performance/load-test.js

# Stress testing
k6 run tests/performance/stress-test.js
```

## 📚 Documentation

### Code Documentation

- Use docstrings for all functions and classes
- Include type hints and return types
- Add inline comments for complex logic

```python
async def process_chat_message(
    message: str,
    user_id: str,
    session_id: str
) -> ChatResponse:
    """
    Process a chat message and generate AI response.
    
    Args:
        message: User's input message
        user_id: Unique identifier for the user
        session_id: Session identifier for context
        
    Returns:
        ChatResponse object containing AI response
        
    Raises:
        ValidationError: If message format is invalid
        RateLimitError: If user exceeds rate limits
    """
    # Implementation here
```

### API Documentation

- Update OpenAPI specification
- Include request/response examples
- Document error codes and messages

### README Updates

- Update installation instructions
- Add new features to feature list
- Update screenshots if UI changes

## 🌍 Internationalization

### Adding New Languages

1. Create language file in `frontend/src/locales/`
2. Add language selector to UI
3. Update language detection logic
4. Test with different languages

```typescript
// Example: frontend/src/locales/he.json
{
  "common": {
    "welcome": "ברוכים הבאים",
    "send": "שלח",
    "cancel": "ביטול"
  },
  "chat": {
    "placeholder": "כתבו את השאלה שלכם כאן...",
    "thinking": "העוזר חושב..."
  }
}
```

## 🔧 DevOps Contributions

### CI/CD Improvements

- Add new test types
- Improve build performance
- Add deployment strategies
- Enhance security scanning

### Infrastructure

- Kubernetes manifest improvements
- Helm chart updates
- Monitoring enhancements
- Security hardening

## 📞 Getting Help

- 💬 **Discussions**: Use GitHub Discussions for questions
- 🐛 **Issues**: Create issues for bugs and feature requests
- 📧 **Email**: Contact maintainers at team@org-chatbot.com
- 📖 **Documentation**: Check our comprehensive docs

## 🏆 Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project documentation
- Social media mentions

Thank you for contributing to Org Chatbot! 🎉
