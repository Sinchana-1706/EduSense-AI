# EduSense AI - System Architecture Overview

EduSense AI is structured as a decoupled multi-modal AI analytics platform.

```mermaid
flowchart TD
    subgraph Client ["Frontend Layer (React + TypeScript)"]
        UI["Teacher Dashboard UI"]
        RTC_Client["LiveKit WebRTC Audio/Video Client"]
    end

    subgraph Backend ["Backend & API Layer (FastAPI Python)"]
        API["FastAPI REST Endpoints (/health, /api/v1)"]
        Service["Analytics & Session Services"]
    end

    subgraph RealTime ["Real-Time Classroom Layer"]
        LiveKit["LiveKit Media Server"]
    end

    subgraph AI_Engine ["AI & Machine Learning Engine"]
        Att["Attendance Engine (Face Recognition)"]
        Emo["Emotion Analyzer (Facial Expression)"]
        Speech["Speech Transcriber (Whisper)"]
        Sent["Sentiment Analyzer (NLP)"]
    end

    subgraph Storage ["Database Layer"]
        DB[(PostgreSQL Database)]
    end

    UI <-->|HTTP / REST API| API
    RTC_Client <-->|WebRTC Video / Audio| LiveKit
    LiveKit -->|Audio / Video Streams| AI_Engine
    AI_Engine -->|Processed Analytics| Service
    Service -->|Save Records| DB
    Service -->|Real-time Metrics| API
```

## System Components

1. **Frontend (React + Vite + TypeScript)**:
   Provides real-time interactive teacher dashboards, video feed visualization, and student engagement metrics.
2. **Backend (FastAPI)**:
   High-performance asynchronous API server handling auth, session management, and routing analytical results.
3. **Database (PostgreSQL + SQLAlchemy)**:
   Relational database storing student profiles, attendance records, classroom session metrics, and analytical logs.
4. **Real-Time Classroom (LiveKit)**:
   Low-latency WebRTC media server streaming student & teacher audio/video feeds.
5. **AI Core Modules**:
   - `ai/attendance`: Face detection & recognition for attendance logging.
   - `ai/emotion`: Facial expression analysis for attention & mood tracking.
   - `ai/speech`: Whisper speech-to-text transcription.
   - `ai/sentiment`: NLP sentiment analysis on transcripts & chat input.
