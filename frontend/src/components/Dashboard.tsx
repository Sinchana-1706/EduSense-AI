import React, { useEffect, useState } from 'react';
import { fetchBackendHealth, HealthCheckResponse } from '../services/api';
import { UserCheck, Smile, Mic, MessageSquare, Activity, CheckCircle, AlertCircle } from 'lucide-react';

export const Dashboard: React.FC = () => {
  const [healthData, setHealthData] = useState<HealthCheckResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const data = await fetchBackendHealth();
        setHealthData(data);
        setError(null);
      } catch (err) {
        setError('Backend Offline');
      } finally {
        setLoading(false);
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 10000); // poll every 10 seconds
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="header-brand">
          <div className="brand-icon">E</div>
          <div className="brand-title">
            <h1>EduSense AI</h1>
            <p>Online Classroom Analytics Platform</p>
          </div>
        </div>

        <div className="status-badge">
          <span className={`status-dot ${healthData ? 'healthy' : 'offline'}`}></span>
          <span>
            {loading
              ? 'Checking status...'
              : healthData
              ? `Backend Healthy (${healthData.app_name} v${healthData.version})`
              : 'Backend Disconnected (Run FastAPI on port 8000)'}
          </span>
        </div>
      </header>

      {/* Analytics Overview Cards */}
      <div className="dashboard-grid">
        {/* Attendance Card */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <div className="card-icon icon-blue">
                <UserCheck size={20} />
              </div>
              Student Attendance
            </div>
          </div>
          <div className="card-value">Face Recognition</div>
          <div className="card-subtext">Automated facial detection & verification engine</div>
          <div className="tag-placeholder">ai/attendance module ready</div>
        </div>

        {/* Facial Emotion Card */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <div className="card-icon icon-purple">
                <Smile size={20} />
              </div>
              Facial Emotion
            </div>
          </div>
          <div className="card-value">Mood Analysis</div>
          <div className="card-subtext">Attentive, Confused, Bored & Expression tracking</div>
          <div className="tag-placeholder">ai/emotion module ready</div>
        </div>

        {/* Speech-to-Text Card */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <div className="card-icon icon-indigo">
                <Mic size={20} />
              </div>
              Speech Transcription
            </div>
          </div>
          <div className="card-value">Whisper AI</div>
          <div className="card-subtext">Real-time lecture speech-to-text transcriber</div>
          <div className="tag-placeholder">ai/speech module ready</div>
        </div>

        {/* Text Sentiment Card */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <div className="card-icon icon-amber">
                <MessageSquare size={20} />
              </div>
              Text Sentiment
            </div>
          </div>
          <div className="card-value">Comprehension</div>
          <div className="card-subtext">Lecture transcript & student feedback NLP analysis</div>
          <div className="tag-placeholder">ai/sentiment module ready</div>
        </div>
      </div>

      {/* Project Status Info Banner */}
      <div className="info-banner">
        <div className="banner-icon">🚀</div>
        <div className="banner-content">
          <h3>EduSense AI Project Foundation Established</h3>
          <p>
            The scalable baseline structure for <strong>EduSense AI</strong> is successfully initialized. Modules for 
            Attendance, Emotion, Speech, and Sentiment analysis are structured as modular Python packages.
          </p>
          <ul>
            <li><strong>Frontend:</strong> React + TypeScript (Vite dev server running on port 5173)</li>
            <li><strong>Backend:</strong> FastAPI + Python (Modular routers and services running on port 8000)</li>
            <li><strong>Database:</strong> PostgreSQL (SQLAlchemy ORM connection baseline)</li>
            <li><strong>Real-time Streaming:</strong> LiveKit architecture ready</li>
          </ul>
        </div>
      </div>
    </div>
  );
};
