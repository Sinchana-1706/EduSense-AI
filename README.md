# EduSense AI 🎓🤖

**EduSense AI** is an online classroom analytics system designed to empower educators with real-time insight into student engagement, attendance, facial emotions, speech transcription, and sentiment analysis during live virtual or hybrid classes.

---

## 🎯 Project Objectives

1. **Student Attendance**: Face-recognition based automated attendance tracking.
2. **Facial Emotion Analysis**: Real-time facial expression and mood monitoring (Attentive, Confused, Bored, Neutral, Happy).
3. **Speech-to-Text**: Automatic speech transcription during lecture sessions (Whisper AI).
4. **Text Sentiment Analysis**: NLP sentiment and comprehension monitoring on lecture transcripts and chat messages.
5. **Student Engagement Analytics**: Consolidated multi-modal engagement scoring.
6. **Teacher Dashboard**: Real-time interactive dashboard for classroom monitoring and post-session insights.

---

## 🛠️ Technology Stack

- **Frontend**: React + TypeScript + Vite + CSS3
- **Backend**: FastAPI + Python 3.10+ + Pydantic
- **Database**: PostgreSQL (SQLAlchemy ORM prep)
- **Real-time Streaming**: LiveKit
- **AI / ML Core**: Python (Modular placeholders for attendance, emotion, speech, and sentiment engines)

---

## 📁 Project Structure

```text
EduSense-AI/
├── frontend/             # React + TypeScript Vite frontend app
│   ├── src/
│   │   ├── components/   # Dashboard & UI components
│   │   ├── services/     # Backend API integration service
│   │   ├── App.tsx       # Root App container
│   │   ├── main.tsx      # React entrypoint
│   │   └── index.css     # Design system & dark mode styles
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts
├── backend/              # FastAPI backend API
│   ├── app/
│   │   ├── config/       # App settings & environment variables
│   │   ├── routers/      # API Routers (GET /health)
│   │   ├── services/     # Core business logic services
│   │   └── main.py       # FastAPI application entrypoint
│   └── requirements.txt
├── ai/                   # Modular AI analytical placeholders
│   ├── attendance/       # Face recognition attendance module
│   ├── emotion/          # Facial emotion analysis module
│   ├── speech/           # Whisper speech-to-text module
│   └── sentiment/        # Text sentiment analysis module
├── database/             # Database connection & ORM model base
│   ├── connection.py     # SQLAlchemy PostgreSQL engine setup
│   └── base.py           # Declarative base class
├── models/               # Model weights storage directory (.gitkeep)
├── datasets/             # Training datasets storage directory (.gitkeep)
├── docs/                 # Documentation & Architecture diagrams
│   └── architecture.md
├── .env.example          # Environment variable reference
├── .gitignore            # Git exclusion rules
└── README.md             # Project documentation
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+** installed
- **Node.js 18+** and **npm** installed

---

### 1. Setting Up & Running the FastAPI Backend

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment and activate it:
   - **Windows (PowerShell):**
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - **Linux / macOS:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

5. Verify backend health endpoint:
   Open your browser or run:
   ```bash
   curl http://127.0.0.1:8000/health
   ```
   *Expected Response:*
   ```json
   {
     "status": "ok",
     "app_name": "EduSense AI",
     "message": "Backend service is healthy",
     "timestamp": "..."
   }
   ```

---

### 2. Setting Up & Running the React Frontend

1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install Node dependencies:
   ```bash
   npm install
   ```

3. Start the Vite development server:
   ```bash
   npm run dev
   ```

4. Open the application:
   Access `http://localhost:5173` in your web browser to view the **EduSense AI Teacher Dashboard**.

---

## 📑 Next Steps & Development Roadmap

- [x] **Phase 1**: Clean & Scalable Repository Foundation (Completed)
- [ ] **Phase 2**: Database schema design & PostgreSQL migration setup (Alembic)
- [ ] **Phase 3**: LiveKit real-time classroom audio/video WebRTC integration
- [ ] **Phase 4**: AI Model integration (Face Recognition, Facial Emotion, Whisper Speech-to-Text, Sentiment Analysis)
- [ ] **Phase 5**: Real-time analytics streaming & teacher dashboard visualizer
