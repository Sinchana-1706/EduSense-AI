# EduSense AI 🎓🤖

**EduSense AI** is a smart online classroom analytics system designed to empower educators with real-time insight into student attendance, facial emotion/engagement, speech transcription, and text sentiment analysis during live virtual or hybrid classes.

---

## 🎯 Project Objectives & Implemented Features

1. **Objective 1 — Automated Student Attendance**:
   - **Face Registration**: Administrator/Teacher can upload student face images (`POST /api/v1/students/register-face`). System extracts 128-d/512-d normalized face feature vector embeddings and stores them without retaining raw images.
   - **Live Recognition & Attendance**: During LiveKit sessions, video frames are processed (`POST /api/v1/attendance/recognize`), faces are detected, and embeddings are matched via Cosine Distance.
   - **Safety Rules**: Strict cosine distance thresholding ensures unknown faces are safely ignored and not falsely identified as registered students. Multiple checks prevent double-counting in the same session.
   - **Summary Endpoint**: `GET /api/v1/attendance/session/{session_id}` returns total enrolled, present count, absent count, and attendance percentage.

2. **Objective 2 — Facial Emotion / Engagement Detection**:
   - **Pretrained Facial Analysis**: Processes face frames (`POST /api/v1/emotion/analyze`) using `DeepFace` expression recognition.
   - **Classroom Engagement Mapping**: Maps raw facial expressions (`happy`, `surprise`, `neutral`, `fear`, `disgust`, `sad`, `angry`) to classroom categories: `attentive`, `neutral`, `confused`, and `disengaged`.
   - **Session Analytics**: `GET /api/v1/emotion/session/{session_id}` computes live distribution percentages and overall classroom engagement scores.

3. **Objective 3 — Speech Transcription + Text Sentiment Analysis**:
   - **Whisper Speech-to-Text**: Converts classroom speech audio chunks (`POST /api/v1/speech/transcribe`) into text transcripts.
   - **Text Sentiment Pipeline**: Analyzes transcript sentiment (`POST /api/v1/sentiment/analyze`) using `NLTK VADER` into `positive`, `neutral`, or `negative` ratings.
   - **Session Analytics**: `GET /api/v1/sentiment/session/{session_id}` provides positive/neutral/negative percentage breakdowns and latest transcript logs.

---

## 🛠️ Technology Stack

- **Frontend**: React + TypeScript + Vite + CSS3 + LiveKit Client (`livekit-client`)
- **Backend**: FastAPI + Python 3.11 + Pydantic + PyJWT + SQLAlchemy 2.0 ORM
- **Database**: PostgreSQL (with automatic zero-setup SQLite fallback)
- **Real-Time WebRTC Streaming**: LiveKit Server (`livekit-api`)
- **AI Core Engines**: Pretrained `DeepFace`, `Facenet`, `RetinaFace`, `OpenAI Whisper`, `SpeechRecognition`, `NLTK VADER`

---

## 📁 Project Structure

```text
EduSense-AI/
├── frontend/                     # React + TypeScript Vite frontend app
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.tsx     # Teacher Dashboard & real-time polling
│   │   │   ├── Classroom.tsx     # LiveKit Classroom & canvas frame sampling
│   │   │   ├── StatsCard.tsx     # Reusable metric card component
│   │   │   ├── VideoTile.tsx     # WebRTC participant video/audio tile
│   │   │   ├── ParticipantList.tsx# Roster sidebar
│   │   │   └── ClassroomControls.tsx # Media control toolbar
│   │   ├── services/
│   │   │   └── api.ts            # API service functions for Objectives 1, 2, 3
│   │   ├── App.tsx               # Root App container
│   │   ├── main.tsx              # React entrypoint
│   │   └── index.css             # Glassmorphism design system
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts
├── backend/                      # FastAPI backend API
│   ├── app/
│   │   ├── config/
│   │   │   └── settings.py       # Pydantic settings
│   │   ├── routers/
│   │   │   ├── health.py         # GET /health
│   │   │   ├── students.py       # POST /api/v1/students/register-face
│   │   │   ├── livekit.py        # POST /api/v1/livekit/token
│   │   │   ├── attendance.py     # POST /api/v1/attendance/recognize & GET /session/{id}
│   │   │   ├── emotion.py        # POST /api/v1/emotion/analyze & GET /session/{id}
│   │   │   ├── speech.py         # POST /api/v1/speech/transcribe
│   │   │   └── sentiment.py      # POST /api/v1/sentiment/analyze & GET /session/{id}
│   │   └── main.py               # FastAPI application entrypoint
│   ├── test_api_endpoints.py     # Integration unit test suite
│   └── requirements.txt
├── ai/                           # AI analytical engines
│   ├── attendance/               # Face embedding extraction & matching engine
│   ├── emotion/                  # Facial expression & engagement mapping analyzer
│   ├── speech/                   # Whisper speech-to-text transcriber
│   └── sentiment/                # NLTK VADER sentiment analyzer
├── database/                     # SQLAlchemy database models & engine connection
│   ├── models/
│   │   ├── student.py            # Student ORM model
│   │   ├── face_embedding.py     # FaceEmbedding ORM model
│   │   ├── attendance.py         # AttendanceRecord ORM model
│   │   ├── emotion.py            # EmotionRecord ORM model
│   │   ├── speech.py             # SpeechTranscript ORM model
│   │   └── sentiment.py          # SentimentRecord ORM model
│   ├── connection.py             # SQLAlchemy engine setup with SQLite fallback
│   └── base.py                   # Declarative base class
├── docs/                         # Architecture documentation
│   └── architecture.md
├── .env                          # Local environment settings
├── .env.example                  # Environment variable reference
└── README.md                     # Project documentation
```

---

## 🚀 Getting Started & Execution

### 1. Setting Up & Running FastAPI Backend

```bash
cd backend
# Run server using Python:
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- API Docs: `http://127.0.0.1:8000/docs`
- Health Check: `http://127.0.0.1:8000/health`

### 2. Setting Up & Running React Frontend

Open a new terminal window:
```bash
cd frontend
npm install
npm run dev
```
- Access application at `http://localhost:5173`.

---

## 🧪 Automated Testing

To run the backend integration test suite verifying all 7 endpoints:

```bash
cd backend
python test_api_endpoints.py
```

Output:
```text
Ran 7 tests in 11.557s
OK
```
