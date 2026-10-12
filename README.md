# EduSense AI – Smart Classroom Attendance and Student Engagement Analytics

EduSense AI is a next-generation real-time web classroom platform designed to modernize remote and hybrid education. Built similar to Zoom and Google Meet, EduSense AI integrates computer vision, speech analytics, emotion recognition, and natural language processing to deliver real-time automated attendance and multi-modal student engagement insights.

---

## 🏗️ Architecture Overview & Design Principles

EduSense AI is structured into decoupled, modular layers to ensure real-time classroom transport is never blocked by compute-heavy AI inference workloads:

1. **Frontend Layer (`frontend/`)**: React + Vite + TypeScript single-page application providing clean classroom controls, participant grids, and real-time dashboard analytics.
2. **Backend Application (`backend/`)**: FastAPI (Python 3.12) REST API for authentication, classroom session scheduling, participant tracking, and analytics aggregation.
3. **Database Layer (`database/` & PostgreSQL)**: PostgreSQL database managed via SQLAlchemy 2.0 ORM with UUID primary keys and Alembic schema migrations.
4. **Real-time Classroom Transport**: Powered by LiveKit WebRTC server (integrated in Phase 2).
5. **Asynchronous AI Pipeline (`ai/`)**: Compute-heavy AI models (ArcFace/InsightFace, Whisper, BERT, YOLO, wav2vec 2.0) execute out-of-band on sampled intervals via background workers, preventing audio/video latency degradation.

---

## 🛠️ Technology Stack

* **Frontend**: React, Vite, TypeScript
* **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0, Pydantic v2
* **Database**: PostgreSQL 16+, Alembic
* **Real-time Video/Audio**: LiveKit (Phase 2 integration)
* **AI/ML Layer (Future Phases)**: InsightFace/ArcFace, Whisper, BERT, YOLO, wav2vec 2.0, late-fusion models

---

## 📁 Folder Structure

```
EduSense-AI/
│
├── frontend/
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── layouts/
│       ├── hooks/
│       ├── services/
│       ├── types/
│       ├── utils/
│       ├── context/
│       ├── features/
│       │   ├── auth/
│       │   ├── classroom/
│       │   ├── registration/
│       │   ├── attendance/
│       │   ├── analytics/
│       │   ├── reports/
│       │   └── agent/
│       ├── App.tsx
│       └── main.tsx
│
├── backend/
│   └── app/
│       ├── main.py
│       ├── core/
│       │   └── config.py
│       ├── api/
│       │   └── health.py
│       ├── models/
│       │   ├── base.py
│       │   ├── enums.py
│       │   ├── user.py
│       │   ├── profile.py
│       │   ├── classroom.py
│       │   ├── session.py
│       │   └── stubs.py
│       ├── schemas/
│       ├── services/
│       ├── repositories/
│       ├── db/
│       ├── middleware/
│       └── utils/
│   ├── alembic/
│   ├── alembic.ini
│   └── requirements.txt
│
├── ai/
├── database/
├── shared/
├── docs/
│
├── .env.example
├── .gitignore
└── README.md
```

---

## 🚀 Setup & Installation

### Prerequisites
- **Python**: 3.12+
- **Node.js**: v20+ & npm
- **PostgreSQL**: 16+

### Quick Start on Windows 🪟

**Option A: Quick Launcher Scripts**
- **PowerShell**: Run `.\run_dev.ps1`
- **CMD / Double-click**: Run `run_dev.bat`

**Option B: Manual Windows PowerShell Setup**

1. **Backend Setup**:
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item ..\.env.example .env
.\venv\Scripts\alembic upgrade head
.\venv\Scripts\uvicorn app.main:app --reload --port 8000
```
Backend API interactive documentation is available at: `http://localhost:8000/docs`
Health Endpoint: `http://localhost:8000/api/health`

2. **Frontend Setup**:
```powershell
cd frontend
npm install
npm run dev
```
Frontend development server will launch at: `http://localhost:5173`

---

### Manual Setup on Linux / macOS 🐧 🍎

### 1. Database Setup
Create the PostgreSQL database locally (or use SQLite in `.env`):
```bash
createdb edusense_db
```

### 2. Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env
venv/bin/alembic upgrade head
venv/bin/uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Frontend development server will launch at: `http://localhost:5173`

---

## 🎭 Facial Emotion Recognition (EmotiEffLib)

EduSense AI integrates [EmotiEffLib](https://github.com/sb-ai-lab/EmotiEffLib) for real-time facial expression analysis during classroom sessions.

### Features & Architecture
* **Pretrained ONNX Model**: Utilizes `enet_b0_8_best_vgaf` executed via ONNX Runtime on CPU for lightweight (~40ms), accurate facial expression classification.
* **Non-Blocking Inference**: Face crops extracted from InsightFace SCRFD detections are normalized (BGR to RGB) and evaluated without stalling WebRTC real-time media streaming.
* **Database Persistence**: Periodically logged into PostgreSQL / SQLite (`facial_analyses` table) linked to `session_id` and `student_id`.
* **LiveKit Broadcast**: Expressive states are broadcast across participants via WebRTC data packets (`EMOTION_UPDATE`) and rendered directly on student video tiles (`ParticipantTile`).

### API Endpoints
* `POST /api/face/emotion`: Predict facial expressions directly from an image or face crop.
* `GET /api/face/emotion/models`: Returns list of available models and active runtime configuration.
* `POST /api/attendance/verify`: Periodically returns detected expression alongside attendance verification.

### Ethical & Scientific Notice
> [!IMPORTANT]
> Facial expression classifications represent **visible morphological cues** (e.g., smiling, frowning, neutral gaze). They **do not** prove internal psychological affect, comprehension, or academic engagement. In accordance with affective computing best practices, predictions are displayed as observable expressions rather than subjective conclusions.

---

## 🔑 Environment Variables Reference

| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `ENVIRONMENT` | Execution mode | `development` |
| `DATABASE_URL` | SQLAlchemy PostgreSQL Connection URI | `postgresql://apple@localhost:5432/edusense_db` |
| `SECRET_KEY` | JWT signing secret key | *(Keep secure, do not commit)* |
| `ALLOWED_ORIGINS` | Permitted CORS origins | `http://localhost:5173,http://127.0.0.1:5173` |
| `LIVEKIT_URL` | LiveKit server endpoint | `http://localhost:7880` |
| `EMOTION_MODEL_NAME` | EmotiEffLib pretrained model | `enet_b0_8_best_vgaf` |
| `EMOTION_INFERENCE_ENGINE` | Inference backend runtime (`onnx`, `torch`) | `onnx` |
| `EMOTION_DEVICE` | Hardware device for emotion inference | `cpu` |

---

## 📊 Project Milestones & Status Summary

* [x] **Phase 1: Project Foundation & Architecture**: Modular structure, FastAPI backend, SQLAlchemy ORM, Alembic migrations, React + Vite shell.
* [x] **Phase 2: Real-time Communication**: LiveKit WebRTC classroom integration, room management, media controls.
* [x] **Phase 3A: Student Face Enrollment & Verification**: InsightFace SCRFD face detection, ArcFace 512-d embeddings, temporal multi-sample verification.
* [x] **Phase 3B: Automated Classroom Attendance**: Non-intrusive periodic frame capture, attendance lifecycle, DB sync.
* [x] **EmotiEffLib Facial Emotion Recognition**: Integrated `enet_b0_8_best_vgaf` ONNX emotion recognition pipeline, REST endpoints, database persistence, LiveKit data channel broadcasting, and UI expression pills.


---
