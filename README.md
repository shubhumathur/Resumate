# ResuMate - Intelligent Resume Screening System

ResuMate is an **Agentic AI system** for intelligent resume screening and candidate matching, designed to perform semantic understanding, ranking, and explainable evaluation of candidate-job fit using NLP and LLM-based agents.

## 🏗️ Architecture

ResuMate uses a modular, multi-agent architecture:

1. **FileInputAgent** - Extracts text from PDF/DOCX/TXT files
2. **ResumeParsingAgent** - Extracts structured data using spaCy NER
3. **JDParsingAgent** - Parses and vectorizes job descriptions
4. **MatchingAgent** - Computes semantic similarity and matching scores
5. **ImprovementAgent** - Generates explainable summaries using Gemini
6. **QuestionAgent** - Generates personalized interview questions
7. **ModeratorAgent** - Manages state and coordinates agents

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add your Gemini API key and MongoDB URI.

### 3. Start MongoDB (if using local instance)

```bash
# MongoDB should be running on localhost:27017
# Or update MONGODB_URI in .env
```

### 4. Run Backend (FastAPI)

**Option 1: Using the run script (Recommended)**
```bash
# Windows
run_backend.bat

# Linux/Mac
python run_backend.py
```

**Option 2: Manual**
```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 5. Run Frontend (Streamlit)

**Option 1: Using the run script (Recommended)**
```bash
# Windows
run_frontend.bat

# Linux/Mac
python run_frontend.py
```

**Option 2: Manual**
```bash
cd frontend
streamlit run app.py
```

## 📁 Project Structure

```
resumate/
├── backend/
│   ├── main.py
│   ├── agents/
│   ├── models/
│   ├── utils/
│   └── data/
├── frontend/
│   ├── app.py
│   └── components/
├── requirements.txt
├── .env.example
└── README.md
```

## 🔧 Configuration

- **Gemini API**: Required for explainable summaries
- **MongoDB**: Used for knowledge graph storage
- **Sentence Transformers**: Default model is `all-MiniLM-L6-v2`

## 📊 Features

- ✅ Multi-format resume parsing (PDF, DOCX, TXT)
- ✅ Semantic matching using embeddings
- ✅ Explainable candidate scoring
- ✅ Personalized interview questions
- ✅ Knowledge graph integration
- ✅ Interactive Streamlit dashboard

## 📝 API Documentation

Once the backend is running, visit `http://localhost:8000/docs` for interactive API documentation.

## 🧪 Testing

Use Kaggle datasets for training and testing:
- Resume Dataset: https://www.kaggle.com/datasets/gauravduttakiit/resume-dataset
- Job Descriptions: https://www.kaggle.com/datasets/jayakishan225/job-descriptions-dataset

