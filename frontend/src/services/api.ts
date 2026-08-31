export interface HealthCheckResponse {
  status: string;
  app_name: string;
  version: string;
  environment: string;
  timestamp: string;
  services: {
    api: string;
    database: string;
    ai_engine: string;
  };
}

export interface LiveKitTokenResponse {
  token: string;
  room_name: string;
  identity: string;
  livekit_url: string;
}

export interface StudentStatsResponse {
  total_students: number;
  present_students: number;
  absent_students: number;
  attendance_percentage: float;
  active_classroom: string | null;
}

export type float = number;

export interface AttendanceRecordItem {
  id: number;
  student_id: number;
  student_id_code?: string;
  student_name?: string;
  session_id: string;
  room_name: string;
  status: string;
  confidence: number;
  timestamp: string;
}

export interface AttendanceSessionSummaryResponse {
  session_id: string;
  total_students: number;
  present_students: number;
  absent_students: number;
  attendance_percentage: number;
  records: AttendanceRecordItem[];
}

export interface EmotionSessionSummaryResponse {
  session_id: string;
  total_samples: number;
  distribution: {
    attentive: number;
    neutral: number;
    confused: number;
    disengaged: number;
  };
  engagement_percentage: number;
}

export interface SentimentSessionSummaryResponse {
  session_id: string;
  total_transcripts: number;
  distribution: {
    positive: number;
    neutral: number;
    negative: number;
  };
  latest_transcript: string | null;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

/**
 * Fetch backend health status
 */
export async function fetchBackendHealth(): Promise<HealthCheckResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (!response.ok) {
      throw new Error(`Server returned HTTP ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch backend health status:', error);
    throw error;
  }
}

/**
 * Request LiveKit JWT access token and WebSocket URL from FastAPI backend
 */
export async function requestLiveKitToken(
  roomName: string,
  identity: string,
  isTeacher: boolean = false
): Promise<LiveKitTokenResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/livekit/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        room_name: roomName,
        identity: identity,
        is_teacher: isTeacher,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const message = errorData.detail || `HTTP ${response.status} failed to obtain LiveKit token`;
      throw new Error(message);
    }

    return await response.json();
  } catch (error: any) {
    console.error('Failed to request LiveKit token:', error);
    throw new Error(error.message || 'Unable to connect to backend server. Ensure FastAPI is running on port 8000.');
  }
}

/**
 * OBJECTIVE 1: Register Student Face Embedding API
 */
export async function registerStudentFace(
  studentId: string,
  imageBlob: Blob,
  name?: string,
  email?: string
): Promise<any> {
  const formData = new FormData();
  formData.append('student_id', studentId);
  if (name) formData.append('name', name);
  if (email) formData.append('email', email);
  formData.append('file', imageBlob, 'face.jpg');

  const response = await fetch(`${API_BASE_URL}/api/v1/students/register-face`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to register student face.');
  }
  return await response.json();
}

/**
 * OBJECTIVE 1: Recognize Face Frame & Mark Attendance API
 */
export async function recognizeAttendance(
  sessionId: string,
  roomName: string,
  frameBlob: Blob
): Promise<any> {
  const formData = new FormData();
  formData.append('session_id', sessionId);
  formData.append('room_name', roomName);
  formData.append('file', frameBlob, 'frame.jpg');

  const response = await fetch(`${API_BASE_URL}/api/v1/attendance/recognize`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Attendance recognition failed.');
  }
  return await response.json();
}

/**
 * OBJECTIVE 1: Fetch Session Attendance Summary
 */
export async function fetchAttendanceSummary(sessionId: string): Promise<AttendanceSessionSummaryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/attendance/session/${encodeURIComponent(sessionId)}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch attendance summary for ${sessionId}`);
  }
  return await response.json();
}

/**
 * OBJECTIVE 2: Analyze Facial Emotion & Engagement API
 */
export async function analyzeFacialEmotion(
  sessionId: string,
  frameBlob: Blob,
  studentId?: string
): Promise<any> {
  const formData = new FormData();
  formData.append('session_id', sessionId);
  if (studentId) formData.append('student_id', studentId);
  formData.append('file', frameBlob, 'frame.jpg');

  const response = await fetch(`${API_BASE_URL}/api/v1/emotion/analyze`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Facial emotion analysis failed.');
  }
  return await response.json();
}

/**
 * OBJECTIVE 2: Fetch Facial Emotion Session Summary
 */
export async function fetchEmotionSummary(sessionId: string): Promise<EmotionSessionSummaryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/emotion/session/${encodeURIComponent(sessionId)}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch emotion summary for ${sessionId}`);
  }
  return await response.json();
}

/**
 * OBJECTIVE 3: Transcribe Speech Audio Chunk API
 */
export async function transcribeAudio(audioBlob: Blob): Promise<any> {
  const formData = new FormData();
  formData.append('file', audioBlob, 'audio.wav');

  const response = await fetch(`${API_BASE_URL}/api/v1/speech/transcribe`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Speech transcription failed.');
  }
  return await response.json();
}

/**
 * OBJECTIVE 3: Analyze Text Sentiment API
 */
export async function analyzeTextSentiment(
  transcript: string,
  sessionId: string,
  studentId?: string
): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/api/v1/sentiment/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      transcript,
      session_id: sessionId,
      student_id: studentId,
    }),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Sentiment analysis failed.');
  }
  return await response.json();
}

/**
 * OBJECTIVE 3: Fetch Text Sentiment Session Summary
 */
export async function fetchSentimentSummary(sessionId: string): Promise<SentimentSessionSummaryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/sentiment/session/${encodeURIComponent(sessionId)}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch sentiment summary for ${sessionId}`);
  }
  return await response.json();
}
