# Dreamer Document AI

A FastAPI-based web application for AI-powered document analysis, supporting PDF and Word documents with multilingual capabilities.

## 🌟 Features

- **Document Analysis**
  - PDF and DOCX support
  - Character and plot analysis
  - Theme identification
  - Readability assessment
  - Sentiment analysis
  - Style consistency checking

- **Modern Tech Stack**
  - FastAPI for high-performance API
  - Bootstrap 5 for responsive UI
  - Redis for caching
  - PostgreSQL for data storage
  - OpenAI GPT-4 integration

- **Security & Performance**
  - Rate limiting
  - File validation
  - Secure payment processing
  - Background task handling
  - Response caching

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL
- Redis
- OpenAI API key
- Stripe account

### Installation

1. Clone the repository:
```bash
git clone https://github.com/gilzero/dreamer-doc-ai-fastapi.git
cd dreamer-doc-ai-fastapi
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/dreamer_doc_ai
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=your_openai_key
STRIPE_SECRET_KEY=your_stripe_key
STRIPE_WEBHOOK_SECRET=your_webhook_secret
```

5. Run database migrations:
```bash
alembic upgrade head
```

6. Start the application:
```bash
uvicorn app.main:app --reload
```

### Docker Deployment

1. Build and run with Docker Compose:
```bash
docker-compose up --build
```

## 💻 API Documentation

Once running, visit:
- API documentation: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

## 🧪 Testing

Run tests with pytest:
```bash
pytest
```

Run specific test categories:
```bash
pytest tests/test_document.py  # Document tests
pytest tests/test_payment.py   # Payment tests
pytest -m integration          # Integration tests
```

## 📦 Project Structure

```
dreamer-doc-ai/
├── app/
│   ├── api/            # API endpoints
│   ├── core/           # Core configurations
│   ├── db/             # Database models and sessions
│   ├── services/       # Business logic services
│   ├── static/         # Static files
│   └── templates/      # HTML templates
├── tests/              # Test files
├── uploads/            # Upload directory
└── logs/              # Application logs
```

## ⚙️ Configuration

Key configuration options in `app/core/config.py`:
- Document size limits
- Allowed file types
- Analysis options
- Cache settings
- Rate limiting

## 🔒 Security

- File validation
- CORS protection
- Rate limiting
- SQL injection prevention
- XSS protection
- CSRF protection

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- **Your Name** - *Initial work*

## 🙏 Acknowledgments

- OpenAI for GPT-4 API
- FastAPI 
- Bootstrap 
- All contributors

## 📞 Support

For support, email alan at dreamer.xyz or create an issue on GitHub.

## 🚀 Roadmap

- [ ] Multi-language support
- [ ] Enhanced analysis features
- [ ] User authentication
- [ ] API rate limiting tiers
- [ ] Additional file format support

```

