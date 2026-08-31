import React, { useEffect, useState } from 'react';
import {
  fetchBackendHealth,
  fetchAttendanceSummary,
  fetchEmotionSummary,
  fetchSentimentSummary,
  HealthCheckResponse,
  AttendanceSessionSummaryResponse,
  EmotionSessionSummaryResponse,
  SentimentSessionSummaryResponse,
} from '../services/api';
import { Classroom } from './Classroom';
import { StatsCard } from './StatsCard';
import {
  Users,
  UserCheck,
  UserX,
  Radio,
  Smile,
  MessageSquare,
  LayoutDashboard,
  Video,
  Play,
  FileText,
} from 'lucide-react';

export const Dashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'classroom'>('dashboard');
  const [healthData, setHealthData] = useState<HealthCheckResponse | null>(null);

  // Objective 1: Attendance State
  const [attendanceData, setAttendanceData] = useState<AttendanceSessionSummaryResponse>({
    session_id: 'CS-101',
    total_students: 42,
    present_students: 38,
    absent_students: 4,
    attendance_percentage: 90.5,
    records: [],
  });

  // Objective 2: Facial Emotion State
  const [emotionData, setEmotionData] = useState<EmotionSessionSummaryResponse>({
    session_id: 'CS-101',
    total_samples: 0,
    distribution: {
      attentive: 65.0,
      neutral: 20.0,
      confused: 10.0,
      disengaged: 5.0,
    },
    engagement_percentage: 85.0,
  });

  // Objective 3: Text Sentiment State
  const [sentimentData, setSentimentData] = useState<SentimentSessionSummaryResponse>({
    session_id: 'CS-101',
    total_transcripts: 0,
    distribution: {
      positive: 70.0,
      neutral: 25.0,
      negative: 5.0,
    },
    latest_transcript: 'Welcome to the Data Structures & Algorithms live lecture.',
  });

  const [loading, setLoading] = useState<boolean>(true);
  const [selectedRoomName, setSelectedRoomName] = useState<string>('CS-101');
  const [teacherName] = useState<string>('Prof. Smith');

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const [health, att, emo, sent] = await Promise.all([
          fetchBackendHealth().catch(() => null),
          fetchAttendanceSummary('CS-101').catch(() => null),
          fetchEmotionSummary('CS-101').catch(() => null),
          fetchSentimentSummary('CS-101').catch(() => null),
        ]);

        if (health) setHealthData(health);
        if (att) setAttendanceData(att);
        if (emo) setEmotionData(emo);
        if (sent) setSentimentData(sent);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
    const interval = setInterval(fetchAnalytics, 5000); // Poll live session analytics every 5s
    return () => clearInterval(interval);
  }, []);

  const handleStartClassroom = (roomName: string = 'CS-101') => {
    setSelectedRoomName(roomName);
    setActiveTab('classroom');
  };

  return (
    <div className="app-container">
      {/* App Header */}
      <header className="app-header">
        <div className="header-brand">
          <div className="brand-icon">E</div>
          <div className="brand-title">
            <h1>EduSense AI</h1>
            <p>Smart Online Classroom & Student Analytics Platform</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="nav-tabs">
          <button
            className={`nav-tab ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            <LayoutDashboard size={18} /> Teacher Dashboard
          </button>
          <button
            className={`nav-tab ${activeTab === 'classroom' ? 'active' : ''}`}
            onClick={() => setActiveTab('classroom')}
          >
            <Video size={18} /> Live Classroom
          </button>
        </nav>

        {/* Health Status Badge */}
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

      {/* Main View Area */}
      {activeTab === 'dashboard' ? (
        <div className="dashboard-content">
          {/* OBJECTIVE 1: Attendance Section */}
          <div className="dashboard-section">
            <h2 className="section-title" style={{ marginBottom: '1rem', fontSize: '1.25rem', fontFamily: 'var(--font-heading)' }}>
              Objective 1 — Automated Face Recognition Attendance
            </h2>

            <div className="dashboard-grid">
              {/* Total Students */}
              <StatsCard
                title="Total Enrolled"
                value={attendanceData.total_students}
                subtext="Total students registered in course database"
                icon={<Users size={20} />}
                iconBgClass="icon-blue"
                tag="Student Roster DB"
              />

              {/* Present Students */}
              <StatsCard
                title="Present Students"
                value={attendanceData.present_students}
                subtext={`Attendance Rate: ${attendanceData.attendance_percentage}%`}
                icon={<UserCheck size={20} />}
                iconBgClass="icon-green"
                tag="Face Recognition Verified"
              />

              {/* Absent Students */}
              <StatsCard
                title="Absent Students"
                value={attendanceData.absent_students}
                subtext="Unrecognized / absent in current session"
                icon={<UserX size={20} />}
                iconBgClass="icon-rose"
                tag="Automated Attendance Log"
              />

              {/* Active Classroom & Quick Start */}
              <StatsCard
                title="Active Session"
                value={selectedRoomName}
                subtext={`Attendance: ${attendanceData.attendance_percentage}%`}
                icon={<Radio size={20} />}
                iconBgClass="icon-amber"
                actionButton={
                  <button
                    className="card-action-btn"
                    onClick={() => handleStartClassroom(selectedRoomName)}
                  >
                    <Play size={14} /> Start Classroom
                  </button>
                }
                tag="LiveKit WebRTC Stream"
              />
            </div>
          </div>

          {/* OBJECTIVES 2 & 3: Facial Engagement & Text Sentiment Section */}
          <div className="dashboard-section" style={{ marginTop: '2rem' }}>
            <h2 className="section-title" style={{ marginBottom: '1rem', fontSize: '1.25rem', fontFamily: 'var(--font-heading)' }}>
              Objectives 2 & 3 — Facial Engagement & Text Sentiment Analytics
            </h2>

            <div className="dashboard-grid">
              {/* Facial Emotion / Engagement Card */}
              <div className="card">
                <div className="card-header">
                  <div className="card-title">
                    <div className="card-icon icon-purple">
                      <Smile size={20} />
                    </div>
                    Facial Engagement Analytics
                  </div>
                  <div className="status-badge" style={{ padding: '0.2rem 0.6rem', fontSize: '0.75rem' }}>
                    {emotionData.engagement_percentage}% Engaged
                  </div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.5rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
                    <span>Attentive:</span>
                    <strong style={{ color: 'var(--accent-green)' }}>{emotionData.distribution.attentive}%</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
                    <span>Neutral:</span>
                    <strong style={{ color: 'var(--accent-blue)' }}>{emotionData.distribution.neutral}%</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
                    <span>Confused:</span>
                    <strong style={{ color: 'var(--accent-amber)' }}>{emotionData.distribution.confused}%</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
                    <span>Disengaged:</span>
                    <strong style={{ color: 'var(--accent-rose)' }}>{emotionData.distribution.disengaged}%</strong>
                  </div>
                </div>

                <div className="tag-placeholder" style={{ marginTop: '1rem' }}>
                  DeepFace Pretrained Expression Classifier
                </div>
              </div>

              {/* Text Sentiment Card */}
              <div className="card">
                <div className="card-header">
                  <div className="card-title">
                    <div className="card-icon icon-amber">
                      <MessageSquare size={20} />
                    </div>
                    Speech Text Sentiment Analytics
                  </div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.5rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
                    <span>Positive:</span>
                    <strong style={{ color: 'var(--accent-green)' }}>{sentimentData.distribution.positive}%</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
                    <span>Neutral:</span>
                    <strong style={{ color: 'var(--accent-blue)' }}>{sentimentData.distribution.neutral}%</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
                    <span>Negative:</span>
                    <strong style={{ color: 'var(--accent-rose)' }}>{sentimentData.distribution.negative}%</strong>
                  </div>
                </div>

                <div className="tag-placeholder" style={{ marginTop: '1rem' }}>
                  Whisper STT + NLTK VADER Sentiment Pipeline
                </div>
              </div>

              {/* Latest Transcript Card */}
              <div className="card" style={{ gridColumn: 'span 2' }}>
                <div className="card-header">
                  <div className="card-title">
                    <div className="card-icon icon-indigo">
                      <FileText size={20} />
                    </div>
                    Speech Transcription & Latest Transcript Log
                  </div>
                </div>

                <div
                  style={{
                    background: 'var(--bg-primary)',
                    padding: '1rem',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-color)',
                    fontSize: '0.9rem',
                    fontStyle: 'italic',
                    color: 'var(--text-primary)',
                    minHeight: '60px',
                  }}
                >
                  "{sentimentData.latest_transcript || 'No transcript generated yet for active session.'}"
                </div>
                <div className="card-subtext" style={{ marginTop: '0.5rem' }}>
                  Transcribed via Whisper speech-to-text pipeline
                </div>
              </div>
            </div>
          </div>

          {/* Info Banner */}
          <div className="info-banner" style={{ marginTop: '2rem' }}>
            <div className="banner-icon">📡</div>
            <div className="banner-content">
              <h3>Objectives 1, 2, and 3 Active</h3>
              <p>
                Automated Face Recognition Attendance, Facial Engagement Analytics, and Whisper STT + Sentiment Analysis are live.
                Click <strong>Start Classroom</strong> above or switch to the <strong>Live Classroom</strong> tab to begin a session.
              </p>
            </div>
          </div>
        </div>
      ) : (
        <Classroom
          initialRoomName={selectedRoomName}
          initialTeacherName={teacherName}
        />
      )}
    </div>
  );
};

export default Dashboard;
