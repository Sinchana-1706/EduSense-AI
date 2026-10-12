export type UserRole = 'TEACHER' | 'STUDENT' | 'ADMIN';

export type SessionStatus = 'SCHEDULED' | 'ACTIVE' | 'COMPLETED' | 'CANCELLED';

export interface TeacherProfile {
  id: string;
  employee_id: string;
  department?: string;
  designation?: string;
}

export interface StudentProfile {
  id: string;
  student_id_number: string;
  department?: string;
  enrollment_year?: number;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  teacher_profile?: TeacherProfile;
  student_profile?: StudentProfile;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Classroom {
  id: string;
  title: string;
  description?: string;
  course_code: string;
  teacher_id: string;
  teacher_name?: string;
  livekit_room_name: string;
  is_active: boolean;
  created_at: string;
}

export interface ClassSession {
  id: string;
  classroom_id: string;
  title: string;
  status: SessionStatus;
  scheduled_start_time: string;
  scheduled_end_time: string;
  actual_start_time?: string;
  actual_end_time?: string;
  livekit_room_name?: string;
  created_at: string;
  classroom_title?: string;
  course_code?: string;
}

export interface JoinSessionResponse {
  token: string;
  server_url: string;
  session_id: string;
  participant_identity: string;
  participant_name: string;
  role: UserRole;
}

export interface ChatMessage {
  id: string;
  senderName: string;
  senderIdentity: string;
  text: string;
  timestamp: number;
}

export interface FaceCaptureResponse {
  passed: boolean;
  num_faces: number;
  message: string;
  embedding?: number[] | null;
  quality_details?: {
    face_width?: number;
    face_height?: number;
    blur_score?: number;
    brightness?: number;
  } | null;
}

export interface EnrollmentCompleteResponse {
  success: boolean;
  message: string;
  enrolled_at?: string;
  consistency_score?: number;
}

export interface EnrollmentStatusResponse {
  is_enrolled: boolean;
  enrolled_at?: string | null;
  student_id: string;
  student_name: string;
  student_id_number: string;
  embedding_dim: number;
}

export interface FaceVerificationResponse {
  verified: boolean;
  identity?: string | null;
  similarity: number;
  message: string;
  quality_details?: {
    face_width?: number;
    face_height?: number;
    blur_score?: number;
    brightness?: number;
  } | null;
}

export interface EmotionPredictionItem {
  student_id?: string | null;
  student_name?: string | null;
  expression: string;
  confidence: number;
  all_scores?: Record<string, number> | null;
  bbox?: number[] | null;
}

export interface EmotionDetectionResponse {
  success: boolean;
  message: string;
  predictions: EmotionPredictionItem[];
  dominant_expression?: string | null;
  model_name: string;
  disclaimer: string;
}

export interface AttendanceVerificationResponse {
  verified: boolean;
  reason: string;
  attendance_status: 'PRESENT' | 'LATE' | 'UNVERIFIED' | 'ABSENT';
  message: string;
  samples_confirmed: number;
  samples_required: number;
  first_verified_at?: string | null;
  last_verified_at?: string | null;
  facial_emotion?: EmotionPredictionItem | null;
}


export interface AttendanceRecordResponse {
  id: string;
  session_id: string;
  student_id: string;
  student_name: string;
  student_id_number: string;
  status: 'PRESENT' | 'LATE' | 'UNVERIFIED' | 'ABSENT';
  marked_at: string;
  first_verified_at?: string | null;
  last_verified_at?: string | null;
  verification_count: number;
  presence_duration_seconds: number;
  is_manually_corrected: boolean;
  corrected_by_name?: string | null;
  correction_reason?: string | null;
}

export interface SessionAttendanceSummaryResponse {
  session_id: string;
  session_title: string;
  classroom_title: string;
  total_students: number;
  present_count: number;
  late_count: number;
  unverified_count: number;
  absent_count: number;
  records: AttendanceRecordResponse[];
}

export interface StudentAttendanceSummaryResponse {
  total_sessions: number;
  present_count: number;
  late_count: number;
  unverified_count: number;
  absent_count: number;
  attendance_percentage: number;
}

export interface TeacherAttendanceSummaryResponse {
  total_classrooms: number;
  total_sessions_conducted: number;
  overall_attendance_rate: number;
}

export interface AudioDiagnostics {
  byte_size: number;
  duration_seconds: number;
  sample_rate: number;
  channel_count: number;
  sample_count: number;
  peak_amplitude: number;
  rms_amplitude: number;
  is_all_zeros: boolean;
  is_silent: boolean;
}

// Phase 4: Speech-to-Text & Vocal Emotion Recognition
export interface TranscriptionResult {
  text: string;
  language?: string | null;
  language_probability?: number | null;
  duration_seconds: number;
  status: string;
  error_message?: string | null;
}

export interface VocalEmotionResult {
  expression?: string | null;
  confidence: number;
  all_scores?: Record<string, number> | null;
}

export interface SpeechAnalysisResponse {
  success: boolean;
  status?: string;
  session_id: string;
  participant_id: string;
  participant_name: string;
  transcription: TranscriptionResult;
  vocal_emotion?: VocalEmotionResult | null;
  duration_seconds: number;
  timestamp: string;
  diagnostics?: AudioDiagnostics | null;
  error?: string | null;
}

export interface SpeechTranscriptItem {
  id: string;
  participant_id: string;
  participant_name: string;
  text: string;
  language?: string | null;
  vocal_emotion?: VocalEmotionResult | null;
  timestamp: number;
}



