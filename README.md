# 🎓 StudyMate AI

> **A production-grade, multi-source AI learning assistant** — upload PDFs, YouTube videos, or text notes, then ask questions, generate summaries, take quizzes, listen to content, and get personalized study plans.

---

## 🖼️ Screenshots

> *(Add screenshots of your running app here for portfolio)*

| Upload | Q&A | Quiz | Dashboard |
|--------|-----|------|-----------|
| *(screenshot)* | *(screenshot)* | *(screenshot)* | *(screenshot)* |

---

## ✨ Features

| Feature | Description | Tech |
|---|---|---|
| 📄 **PDF Upload** | Extract, chunk & embed any PDF | PyMuPDF + pdfplumber |
| ▶ **YouTube** | Auto-fetch transcripts or use Whisper | youtube-transcript-api + Whisper |
| 📝 **Text Notes** | Paste raw notes directly | Custom chunker |
| 💬 **RAG Q&A** | Ask questions with source citations | FAISS + OpenAI |
| 📋 **Summarization** | Short / Bullet / Detailed styles | OpenAI GPT |
| 🧪 **Quiz Generator** | 3–10 MCQs with explanations | OpenAI GPT |
| 🔊 **Text-to-Speech** | Multi-language audio output | gTTS |
| 📅 **Study Plans** ⭐ | AI 3-day personalized study plans | OpenAI GPT |
| 📊 **Dashboard** | Usage analytics & library overview | Streamlit |
| 🧠 **ELI5 Explainer** ⭐ | Simple analogy-driven explanations | OpenAI GPT |

---

## 🏗️ Architecture

```
studymate-ai/
│
├── backend/                   # FastAPI REST API
│   ├── main.py                # App entry point & lifecycle
│   ├── config.py              # Pydantic settings (env-driven)
│   ├── routes/
│   │   ├── upload.py          # /upload/pdf, /youtube, /text
│   │   └── query.py           # /query, /summarize, /quiz, /tts
│   ├── services/
│   │   ├── pdf_service.py     # pdfplumber + PyMuPDF fallback
│   │   ├── youtube_service.py # Transcript API + Whisper fallback
│   │   ├── tts_service.py     # gTTS with MD5 caching
│   │   └── llm_service.py     # OpenAI wrapper with retry logic
│   ├── models/
│   │   └── db_models.py       # SQLAlchemy ORM (User, Document, History)
│   ├── schemas/
│   │   └── schemas.py         # Pydantic request/response models
│   ├── database/
│   │   └── session.py         # DB engine + session factory
│   └── utils/
│       ├── chunker.py         # Smart sentence-aware text splitter
│       ├── text_cleaner.py    # PDF artifact removal, normalization
│       └── logger.py          # Loguru rotating logs
│
├── frontend/
│   └── app.py                 # Streamlit UI (dark academic theme)
│
├── rag/
│   ├── embeddings.py          # sentence-transformers (all-MiniLM-L6-v2)
│   ├── vector_store.py        # FAISS IndexFlatIP with persistence
│   ├── retriever.py           # Semantic + MMR + keyword-boost retrieval
│   └── pipeline.py            # Full RAG orchestrator (index → retrieve → generate)
│
├── data/                      # SQLite DB + uploaded files
├── audio_outputs/             # gTTS MP3 cache
├── vector_store_data/         # FAISS index + metadata
├── requirements.txt
├── .env.example
└── README.md
```

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.9+
- `ffmpeg` (required for Whisper fallback): `sudo apt install ffmpeg` / `brew install ffmpeg`
- OpenAI API key

### 1. Clone & Create Environment

```bash
git clone <your-repo-url>
cd studymate-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:
```env
GROQ_API_KEY=gsk_your_groq_api_key_here
```

### 3. Run the Backend

```bash
# From the project root
python -m backend.main

# Or with uvicorn directly:
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at:
- API: `http://localhost:8000`
- Interactive Docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

### 4. Run the Frontend

Open a new terminal:

```bash
cd studymate-ai
streamlit run frontend/app.py
```

Frontend: `http://localhost:8501`

---

## 🔑 API Reference

### Upload Endpoints

| Method | Endpoint | Body | Description |
|--------|----------|------|-------------|
| `POST` | `/upload/pdf` | `multipart/form-data` | Upload & index a PDF |
| `POST` | `/upload/youtube` | `{url, title?, user_id}` | Index YouTube transcript |
| `POST` | `/upload/text` | `{title, content, user_id}` | Index raw text |

### Feature Endpoints

| Method | Endpoint | Body | Description |
|--------|----------|------|-------------|
| `POST` | `/query` | `{question, document_id?, top_k}` | RAG Q&A |
| `POST` | `/summarize` | `{document_id, style}` | Summarize document |
| `POST` | `/quiz` | `{document_id, num_questions, difficulty}` | Generate MCQ quiz |
| `POST` | `/tts` | `{text, language}` | Text-to-speech |
| `GET` | `/study-plan` | `?document_id=&user_id=` | AI study plan |

### Utility Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/documents` | List all user documents |
| `GET` | `/history` | Query history |
| `GET` | `/health` | System health check |
| `GET` | `/stats` | Vector store statistics |
| `GET` | `/docs` | Swagger UI |

---

## 🧠 How RAG Works

```
User Question
     │
     ▼
Embedding Model (all-MiniLM-L6-v2)
     │
     ▼
Query Embedding (384-dim vector)
     │
     ▼
FAISS IndexFlatIP → Top-K Similar Chunks
     │
     ▼
[Optional] Keyword Boost Re-ranking
     │
     ▼
Context Assembly → LLM Prompt
     │
     ▼
OpenAI GPT-3.5-turbo → Answer + Sources
```

---

## 🌟 Unique Additions (Beyond Spec)

1. **📅 AI Study Plan Generator** — Analyzes content → personalized 3-day learning schedule
2. **🧠 ELI5 Concept Explainer** — "Explain like I'm 5" mode with analogies
3. **🔁 MMR Retrieval** — Maximal Marginal Relevance avoids redundant context chunks
4. **♻️ TTS Audio Caching** — MD5 hash prevents re-generating identical audio
5. **📊 Analytics Dashboard** — Library overview + query type breakdown
6. **🌍 Multilingual TTS** — 12 languages including Hindi, Japanese, Arabic
7. **⏱️ Latency Tracking** — Every query times from start to response
8. **🔄 Retry Logic** — Exponential backoff on OpenAI rate limits (tenacity)
9. **🧹 Smart Chunker** — Sentence-boundary-aware splitter (no mid-sentence cuts)
10. **📝 Keyword Boost** — Re-ranks semantic results by keyword presence

---

## 🔮 Future Improvements

- [ ] User authentication (JWT + FastAPI Users)
- [ ] GPT-4 Vision for image/diagram understanding in PDFs
- [ ] Flashcard generation & spaced repetition scheduler
- [ ] Real-time streaming responses (SSE)
- [ ] Export quiz to PDF / Anki deck
- [ ] WebSocket live Q&A
- [ ] Docker + docker-compose deployment
- [ ] PostgreSQL migration for production
- [ ] Mobile app (React Native + FastAPI)
- [ ] Chrome extension for webpage indexing

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| `Cannot connect to backend` | Run `python -m backend.main` first |
| `Groq key not set` | Add `GROQ_API_KEY` to `.env` (free at console.groq.com) |
| `YouTube transcript failed` | Video may have no captions; try another |
| `PDF empty after extraction` | Ensure PDF is text-based, not scanned |
| `Whisper fails` | Install `ffmpeg`: `brew install ffmpeg` |
| Slow first query | Embedding model downloads on first run (~90MB) |

---

## 📄 License

MIT License — free to use for portfolio, education, and commercial projects.

---

*Built with ❤️ using FastAPI · FAISS · sentence-transformers · OpenAI · Streamlit · gTTS*
