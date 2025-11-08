# Pombi AI Assistant

An advanced conversational AI assistant with multiple specialized modes, built with FastAPI and React.

## 🚀 Features

### Core Capabilities
- **5 Conversation Modes**: Creative, Precise, Teach, Code, and Analyze modes
- **Multi-Model Support**: OpenAI GPT models and local models via Ollama
- **Smart Model Routing**: Automatic model selection based on task complexity
- **Session Memory**: Temporary conversation history with 2-hour sessions
- **Real-time Streaming**: WebSocket support for streaming responses

### Safety & Privacy
- **Content Filtering**: Multi-layer content moderation
- **Privacy Protection**: Automatic PII redaction and anonymization
- **Rate Limiting**: Configurable usage limits per user
- **Session-Only Storage**: No persistent conversation logs (GDPR compliant)

### Development & Deployment
- **Docker Support**: Full containerization with docker-compose
- **Health Monitoring**: Comprehensive health checks and metrics
- **API Documentation**: Auto-generated Swagger/OpenAPI docs
- **Testing Suite**: Unit and integration tests included

## 🛠️ Quick Start

### Prerequisites
- Python 3.11+
- Node.js 16+ (for frontend)
- Docker and Docker Compose (optional but recommended)

### 1. Clone and Setup
```bash
git clone <repository-url>
cd my-repo
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

### 3. Install Dependencies

#### Backend
```bash
pip install -r requirements.txt
```

#### Frontend (optional, for development)
```bash
cd frontend
npm install
```

### 4. Run the Application

#### Option A: Docker Compose (Recommended)
```bash
docker-compose up --build
```

#### Option B: Manual Backend
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Option C: Manual Frontend Development
```bash
cd frontend
npm start
```

### 5. Access the Application
- **API**: http://localhost:8000
- **Frontend**: http://localhost:3000 (if running)
- **API Documentation**: http://localhost:8000/docs

## 🧠 Conversation Modes

### Creative Mode 🎨
- Generates imaginative and engaging content
- Uses descriptive language and storytelling
- Perfect for creative writing, brainstorming, and idea generation

### Precise Mode 🎯
- Prioritizes factual accuracy and concise answers
- Avoids speculation and creative language
- Ideal for factual questions and technical information

### Teach Mode 📚
- Breaks down complex topics into simple steps
- Uses analogies and real-world examples
- Great for learning new concepts and skills

### Code Mode 💻
- Provides working code examples with explanations
- Includes best practices and optimization suggestions
- Supports multiple programming languages

### Analyze Mode 📊
- Provides systematic analysis and comparisons
- Identifies patterns and balanced perspectives
- Excellent for decision-making and research

## 🔧 Configuration

### Environment Variables
```bash
# API Keys
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# Model Configuration
DEFAULT_MODEL=openai
ENABLE_LOCAL_MODELS=true
OLLAMA_BASE_URL=http://localhost:11434

# Application
DEBUG=false
HOST=0.0.0.0
PORT=8000
RATE_LIMIT_PER_MINUTE=60

# Safety
ENABLE_CONTENT_FILTER=true
MAX_MESSAGE_LENGTH=4000
```

### Model Configuration
- **OpenAI**: Requires API key, supports GPT-3.5 and GPT-4
- **Local**: Requires Ollama, supports Llama, Mistral, and other models
- **Auto**: Automatically selects best model based on task

## 📚 API Usage

### Chat Endpoint
```bash
curl -X POST "http://localhost:8000/api/v1/chat/" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "Explain quantum computing like I'\''m 5",
       "mode": "teach",
       "model_preference": "auto"
     }'
```

### Available Modes
```bash
curl "http://localhost:8000/api/v1/modes/"
```

### Health Check
```bash
curl "http://localhost:8000/api/v1/health/detailed"
```

## 🧪 Testing

### Run All Tests
```bash
pytest
```

### Run Specific Test File
```bash
pytest tests/test_api.py
pytest tests/test_modes.py
```

### Run with Coverage
```bash
pytest --cov=app tests/
```

## 📦 Deployment

### Production Docker Build
```bash
docker build -t pombi-ai .
docker run -p 8000:8000 --env-file .env pombi-ai
```

### Cloud Deployment
The application is designed for easy deployment to:
- **AWS**: ECS, Fargate, or App Runner
- **GCP**: Cloud Run or GKE
- **Azure**: Container Instances or AKS
- **DigitalOcean**: App Platform or Droplets

## 🛡️ Safety Features

### Content Filtering
- Multi-category content moderation
- Configurable filter sensitivity
- Automatic content redaction

### Privacy Protection
- PII detection and redaction
- Session-only conversation storage
- No persistent personal data

### Rate Limiting
- Per-user request limits
- Configurable time windows
- Automatic cleanup of expired data

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run tests: `pytest`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: Check the `/docs` endpoint when running
- **Issues**: Create an issue on GitHub
- **Health Check**: Monitor `/api/v1/health/detailed`

## 🔮 Roadmap

- [ ] Voice input/output support
- [ ] Image processing capabilities
- [ ] Persistent conversation storage (optional)
- [ ] Advanced analytics dashboard
- [ ] Custom model fine-tuning support
- [ ] Multi-language support
- [ ] Plugin system for extensions

---

Built with ❤️ using FastAPI, React, and modern AI technologies.