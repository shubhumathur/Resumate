# ResuMate - Intelligent Resume Screening System

ResuMate is an **Agentic AI system** for intelligent resume screening and candidate matching, designed to perform semantic understanding, ranking, and explainable evaluation of candidate-job fit using NLP and LLM-based agents.

## 🏗️ Architecture

ResuMate uses a modular, multi-agent architecture with multiple frontend options:

### Backend (FastAPI)
- **FileInputAgent** - Extracts text from PDF/DOCX/TXT files
- **ResumeParsingAgent** - Extracts structured data using spaCy NER
- **JDParsingAgent** - Parses and vectorizes job descriptions
- **MatchingAgent** - Computes semantic similarity and matching scores
- **ImprovementAgent** - Generates explainable summaries using Gemini
- **QuestionAgent** - Generates personalized interview questions
- **ModeratorAgent** - Manages state and coordinates agents

### Frontend Options
1. **Next.js Web App** (`/webapp`) - Modern React-based UI with authentication
2. **Streamlit App** (`/frontend`) - Simple Python-based dashboard
3. **Hybrid Analyzer** - Advanced RAG-based analysis routes

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+ (for Next.js frontend)
- MongoDB (local or cloud)
- Gemini API key

### 1. Install Backend Dependencies

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add:
- `GEMINI_API_KEY` - Your Gemini API key
- `MONGODB_URI` - MongoDB connection string
- `JWT_SECRET_KEY` - Secret for JWT tokens

### 3. Start MongoDB

Ensure MongoDB is running on `localhost:27017` or update `MONGODB_URI` in `.env`.

### 4. Run Backend (FastAPI)

**Option 1: Using Python**
```bash
cd backend
uvicorn main:app --reload --port 8000
```

**Option 2: Using scripts**
```bash
# Windows
python un/run_backend.py

# Linux/Mac
python un/run_backend.py
```

### 5. Choose Your Frontend

#### Option A: Next.js Web App (Recommended)
```bash
cd webapp
npm install
cp env.example .env.local
# Edit .env.local with your configuration
npm run dev
```
Visit: `http://localhost:3000`



## 📁 Project Structure

```
resumate/
├── backend/                    # FastAPI backend
│   ├── agents/                # AI agents
│   ├── models/                # ML models
│   ├── utils/                 # Utilities (RAG, scoring, etc.)
│   ├── routes/                # API routes
│   ├── db/                    # Database clients
│   ├── auth.py                # Authentication
│   └── main.py                # FastAPI app
├── webapp/                    # Next.js frontend (recommended)
│   ├── app/                   # Next.js pages
│   ├── components/            # React components
│   ├── lib/                   # API client & utils
│   └── package.json
├── frontend/                  # Streamlit frontend
│   ├── app.py                 # Main Streamlit app
│   └── components/            # Streamlit components
├── un/                        # Utilities & scripts
├── requirements.txt           # Python dependencies
├── setup.py                   # Package setup
├── .env.example               # Environment template
└── README.md
```

## 🔧 Configuration

### Required Environment Variables
- **GEMINI_API_KEY**: Required for AI summaries and question generation
- **MONGODB_URI**: Database connection (default: `mongodb://localhost:27017/resumate`)
- **JWT_SECRET_KEY**: Secret for authentication tokens

### Optional
- **MONGODB_DB_NAME**: Database name (default: `resumate`)
- **ACCESS_TOKEN_EXPIRE_MINUTES**: JWT expiration (default: 30)

## 📊 Features

### Core Features
- ✅ Multi-format resume parsing (PDF, DOCX, TXT)
- ✅ Semantic matching using sentence transformers
- ✅ Explainable candidate scoring with AI summaries
- ✅ Personalized interview question generation
- ✅ Knowledge graph integration with Neo4j
- ✅ Vector search with FAISS
- ✅ User authentication and data persistence

### Frontend Features (Next.js)
- 🎨 Modern gradient UI with dark mode
- 🔐 Authentication (Google, GitHub, Email/Password)
- 📊 Interactive dashboard with analytics
- 📈 Score visualization and trends
- 💼 Resume enhancement tools
- 🎯 Interview preparation chat
- 💡 Job recommendations

### Frontend Features (Streamlit)
- 📄 Simple file upload interface
- 📊 Results table and charts
- 📈 Basic skill overlap visualization
- 📥 CSV export functionality

## 📝 API Documentation

Once the backend is running, visit `http://localhost:8000/docs` for interactive API documentation.

### Key Endpoints
- `POST /parse_resume_file` - Parse resume from file
- `POST /parse_jd` - Parse job description
- `POST /match` - Match single resume-JD pair
- `POST /batch_match` - Match multiple resumes
- `POST /generate_summary` - Generate AI summary
- `POST /generate_questions` - Generate interview questions
- `POST /auth/login` - User authentication
- `GET /analytics/summary` - User analytics

## 🧪 Testing

### Unit Tests
```bash
# Test matching agent
python -m pytest backend/agents/matching_agent.py::MatchingAgent::test_matching_cases -v

# Test API endpoints
python test_api.py
```

### Sample Data
Use Kaggle datasets for testing:
- [Resume Dataset](https://www.kaggle.com/datasets/gauravduttakiit/resume-dataset)
- [Job Descriptions](https://www.kaggle.com/datasets/jayakishan225/job-descriptions-dataset)

## 🔍 Advanced Features

### Hybrid Analyzer
The hybrid analyzer combines traditional matching with RAG (Retrieval-Augmented Generation):

```bash
# Use hybrid analysis
POST /hybrid/analyze
{
  "resume": {...},
  "job": {...}
}
```

### Knowledge Graph
Integrated with Neo4j for advanced relationship analysis:
- Store resume and job entities
- Query skill relationships
- Find similar candidates

### Vector Search
FAISS-based semantic search for:
- Similar resumes
- Related job descriptions
- Skill matching

## 🚢 Deployment

### Docker (Recommended)
```bash
# Build and run
docker-compose up --build
```

### Manual Deployment
1. Set up MongoDB and Neo4j
2. Configure environment variables
3. Run backend: `uvicorn backend.main:app --host 0.0.0.0 --port 8000`
4. Build frontend: `cd webapp && npm run build && npm start`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📈 Roadmap

### Planned Improvements
- [ ] Mobile app (React Native)
- [ ] Advanced analytics dashboard
- [ ] Integration with ATS systems
- [ ] Multi-language support
- [ ] Real-time collaboration features
- [ ] API rate limiting and caching
- [ ] Comprehensive test suite

### Known Issues
- Multiple frontend options create maintenance overhead
- Some dependencies may need updating
- Documentation needs consolidation

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- Built with FastAPI, Next.js, and Streamlit
- Powered by Google's Gemini AI
- Sentence Transformers for embeddings
- spaCy for NLP processing
- MongoDB for data persistence
