import React, { useState, useEffect, useRef } from 'react';
import { Room, RoomEvent, Participant, RemoteParticipant } from 'livekit-client';
import {
  requestLiveKitToken,
  recognizeAttendance,
  analyzeFacialEmotion,
  registerStudentFace,
  createClassroom,
  getClassroomByCode,
  fetchAttendanceSummary,
  ClassroomData,
  AttendanceSessionSummaryResponse,
} from '../services/api';
import { VideoTile } from './VideoTile';
import { ParticipantList } from './ParticipantList';
import { ClassroomControls } from './ClassroomControls';
import {
  LogOut,
  Radio,
  Shield,
  User,
  Play,
  UserPlus,
  Copy,
  Check,
  Link as LinkIcon,
  Users,
  UserCheck,
  UserX,
  Percent,
} from 'lucide-react';

export interface ClassroomProps {
  initialRoomName?: string;
  initialTeacherName?: string;
  isStudentView?: boolean;
  studentId?: string;
  preJoinedToken?: string;
}

export const Classroom: React.FC<ClassroomProps> = ({
  initialRoomName = 'CS-101',
  initialTeacherName = 'Prof. Smith',
  isStudentView = false,
  studentId,
  preJoinedToken,
}) => {
  // Pre-join Form State
  const [roomName, setRoomName] = useState<string>(initialRoomName);
  const [identity, setIdentity] = useState<string>(initialTeacherName);
  const [subject, setSubject] = useState<string>('Artificial Intelligence');
  const [isTeacher, setIsTeacher] = useState<boolean>(!isStudentView);
  const [enterCode, setEnterCode] = useState<string>('');

  // Classroom Session Data (Join Code & Share Link)
  const [classroomData, setClassroomData] = useState<ClassroomData | null>(null);
  const [copyCodeSuccess, setCopyCodeSuccess] = useState<boolean>(false);
  const [copyLinkSuccess, setCopyLinkSuccess] = useState<boolean>(false);

  // Live Attendance Summary Roster Data
  const [attendanceSummary, setAttendanceSummary] = useState<AttendanceSessionSummaryResponse | null>(null);

  // Connection & Room Lifecycle State
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [isConnecting, setIsConnecting] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Student Registration Modal State
  const [showRegModal, setShowRegModal] = useState<boolean>(false);
  const [regStudentId, setRegStudentId] = useState<string>('4CB23AI075');
  const [regStudentName, setRegStudentName] = useState<string>('Puneeth');
  const [regFile, setRegFile] = useState<File | null>(null);
  const [regStatusMsg, setRegStatusMsg] = useState<string | null>(null);
  const [isRegistering, setIsRegistering] = useState<boolean>(false);

  // LiveKit Room & Media Controls State
  const roomRef = useRef<Room | null>(null);
  const hiddenCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const localWebcamRef = useRef<HTMLVideoElement | null>(null);
  const localStreamRef = useRef<MediaStream | null>(null);

  const [isMicEnabled, setIsMicEnabled] = useState<boolean>(true);
  const [isCameraEnabled, setIsCameraEnabled] = useState<boolean>(true);
  const [participantsList, setParticipantsList] = useState<Participant[]>([]);
  const [aiStatusMessage, setAiStatusMessage] = useState<string>('AI Analytics Idle');

  useEffect(() => {
    if (initialRoomName) setRoomName(initialRoomName);
    if (initialTeacherName) setIdentity(initialTeacherName);
  }, [initialRoomName, initialTeacherName]);

  // Ensure local camera webcam feed is active for frame capture whenever connected & camera is ON
  useEffect(() => {
    if (!isConnected || !isCameraEnabled) return;

    async function initWebcam() {
      try {
        if (!localStreamRef.current || !localStreamRef.current.active) {
          const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
          localStreamRef.current = stream;
          if (localWebcamRef.current) {
            localWebcamRef.current.srcObject = stream;
            await localWebcamRef.current.play().catch(() => {});
          }
        }
      } catch (err: any) {
        if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
          setErrorMessage('Camera permission denied. Please allow camera access in your browser settings.');
        } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
          setErrorMessage('No camera detected.');
        }
      }
    }

    initWebcam();
  }, [isConnected, isCameraEnabled]);

  // Handle Auto-Connect for Student Join View if preJoinedToken is provided
  useEffect(() => {
    if (preJoinedToken && !isConnected && !isConnecting) {
      connectWithToken(preJoinedToken, initialRoomName);
    }
  }, [preJoinedToken]);

  const updateParticipantsList = () => {
    if (!roomRef.current) return;
    const room = roomRef.current;

    const list: Participant[] = [];
    if (room.localParticipant) {
      list.push(room.localParticipant);
    }
    room.remoteParticipants.forEach((remote: RemoteParticipant) => {
      list.push(remote);
    });

    setParticipantsList(list);
  };

  const setupMediaAndConnect = async (room: Room, wsUrl: string, token: string) => {
    // 1. Explicitly request camera & microphone permissions first
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      localStreamRef.current = stream;
      if (localWebcamRef.current) {
        localWebcamRef.current.srcObject = stream;
        await localWebcamRef.current.play().catch(() => {});
      }
    } catch (mediaErr: any) {
      if (mediaErr.name === 'NotAllowedError' || mediaErr.name === 'PermissionDeniedError') {
        setErrorMessage('Camera permission denied. Please allow camera access in your browser settings.');
      } else if (mediaErr.name === 'NotFoundError' || mediaErr.name === 'DevicesNotFoundError') {
        setErrorMessage('No camera detected.');
      } else {
        console.warn('Browser media permission notice:', mediaErr);
      }
    }

    // 2. Connect to LiveKit Room
    try {
      await room.connect(wsUrl, token);
    } catch (lkErr: any) {
      console.warn('LiveKit signal connection notice (local fallback):', lkErr);
    }

    // 3. Enable local participant camera and microphone
    try {
      await room.localParticipant.enableCameraAndMicrophone();
      setIsMicEnabled(room.localParticipant.isMicrophoneEnabled);
      setIsCameraEnabled(room.localParticipant.isCameraEnabled);
    } catch (pubErr: any) {
      console.warn('LiveKit track publish notice:', pubErr);
    }
  };

  const connectWithToken = async (token: string, _rName: string) => {
    setIsConnecting(true);
    setErrorMessage(null);

    try {
      const room = new Room({
        adaptiveStream: true,
        dynacast: true,
      });
      roomRef.current = room;

      room.on(RoomEvent.ParticipantConnected, updateParticipantsList);
      room.on(RoomEvent.ParticipantDisconnected, updateParticipantsList);
      room.on(RoomEvent.TrackSubscribed, updateParticipantsList);
      room.on(RoomEvent.TrackUnsubscribed, updateParticipantsList);
      room.on(RoomEvent.LocalTrackPublished, updateParticipantsList);
      room.on(RoomEvent.Disconnected, () => {
        setIsConnected(false);
        setParticipantsList([]);
      });

      const livekitUrl = (import.meta.env.VITE_LIVEKIT_URL || 'ws://127.0.0.1:7880').replace('localhost', '127.0.0.1');
      await setupMediaAndConnect(room, livekitUrl, token);

      setIsConnected(true);
      updateParticipantsList();
    } catch (err: any) {
      console.error('Error connecting to classroom:', err);
      setIsConnected(true);
    } finally {
      setIsConnecting(false);
    }
  };

  const handleCreateOrJoinRoom = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsConnecting(true);
    setErrorMessage(null);

    try {
      let createdData: ClassroomData | null = null;
      let targetCode = enterCode.trim();

      // If user typed a join code into the enterCode field, validate it first (Rejoin flow)
      if (targetCode) {
        try {
          createdData = await getClassroomByCode(targetCode);
          setClassroomData(createdData);
        } catch (codeErr: any) {
          setErrorMessage('Invalid or expired classroom code.');
          setIsConnecting(false);
          return;
        }
      } else if (isTeacher) {
        // Create new classroom or fetch existing room for teacher
        if (!roomName.trim() || !identity.trim()) {
          setErrorMessage('Please enter both your name and subject/classroom name.');
          setIsConnecting(false);
          return;
        }
        try {
          createdData = await createClassroom(roomName.trim(), identity.trim(), subject.trim());
          setClassroomData(createdData);
        } catch (cErr: any) {
          console.warn('Classroom creation notice:', cErr);
        }
      }

      const lkRoomName = createdData ? createdData.livekit_room_name : roomName.trim();
      const tokenData = await requestLiveKitToken(lkRoomName, identity.trim(), isTeacher);

      const room = new Room({
        adaptiveStream: true,
        dynacast: true,
      });
      roomRef.current = room;

      room.on(RoomEvent.ParticipantConnected, updateParticipantsList);
      room.on(RoomEvent.ParticipantDisconnected, updateParticipantsList);
      room.on(RoomEvent.TrackSubscribed, updateParticipantsList);
      room.on(RoomEvent.TrackUnsubscribed, updateParticipantsList);
      room.on(RoomEvent.LocalTrackPublished, updateParticipantsList);
      room.on(RoomEvent.Disconnected, () => {
        setIsConnected(false);
        setParticipantsList([]);
      });

      const wsUrl = (tokenData.livekit_url || 'ws://127.0.0.1:7880').replace('localhost', '127.0.0.1');
      await setupMediaAndConnect(room, wsUrl, tokenData.token);

      setIsConnected(true);
      updateParticipantsList();
    } catch (err: any) {
      console.error('Error in classroom setup:', err);
      setIsConnected(true);
    } finally {
      setIsConnecting(false);
    }
  };

  const toggleMic = async () => {
    if (!roomRef.current) return;
    const nextState = !isMicEnabled;
    try {
      await roomRef.current.localParticipant.setMicrophoneEnabled(nextState);
      setIsMicEnabled(nextState);
      updateParticipantsList();
    } catch (err) {
      console.error('Failed to toggle microphone:', err);
    }
  };

  const toggleCamera = async () => {
    if (!roomRef.current) return;
    const nextState = !isCameraEnabled;
    try {
      await roomRef.current.localParticipant.setCameraEnabled(nextState);
      setIsCameraEnabled(nextState);
      if (nextState) {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        localStreamRef.current = stream;
        if (localWebcamRef.current) {
          localWebcamRef.current.srcObject = stream;
          await localWebcamRef.current.play().catch(() => {});
        }
      } else if (localStreamRef.current) {
        localStreamRef.current.getTracks().forEach(t => t.stop());
        localStreamRef.current = null;
      }
      updateParticipantsList();
    } catch (err) {
      console.error('Failed to toggle camera:', err);
    }
  };

  const handleLeaveRoom = () => {
    if (roomRef.current) {
      roomRef.current.disconnect();
      roomRef.current = null;
    }
    if (localStreamRef.current) {
      localStreamRef.current.getTracks().forEach(t => t.stop());
      localStreamRef.current = null;
    }
    setIsConnected(false);
    setParticipantsList([]);
  };

  const handleCopyCode = () => {
    if (!classroomData) return;
    navigator.clipboard.writeText(classroomData.join_code);
    setCopyCodeSuccess(true);
    setTimeout(() => setCopyCodeSuccess(false), 2000);
  };

  const handleCopyLink = () => {
    if (!classroomData) return;
    navigator.clipboard.writeText(classroomData.join_url);
    setCopyLinkSuccess(true);
    setTimeout(() => setCopyLinkSuccess(false), 2000);
  };

  // Student Attendance Recognition State
  const [recognitionResult, setRecognitionResult] = useState<{
    recognized: boolean;
    studentId?: string;
    studentName?: string;
    confidence?: number;
    attendance: string;
    statusText: string;
  } | null>(null);
  const [isVerifyingAttendance, setIsVerifyingAttendance] = useState<boolean>(false);

  // Manual Trigger for Face Attendance Verification
  const triggerAttendanceCheck = async () => {
    if (!isConnected) return;
    const targetSession = classroomData ? classroomData.livekit_room_name : roomName;

    if (!isCameraEnabled) {
      setRecognitionResult({
        recognized: false,
        attendance: 'not_marked',
        statusText: 'Camera OFF — Turn on camera for automatic face attendance',
      });
      return;
    }

    setIsVerifyingAttendance(true);

    try {
      let videoElement: HTMLVideoElement | null = null;
      if (localWebcamRef.current && (localWebcamRef.current.videoWidth > 0 || localWebcamRef.current.readyState >= 2)) {
        videoElement = localWebcamRef.current;
      } else {
        const videoElements = Array.from(document.querySelectorAll<HTMLVideoElement>('video'));
        videoElement = videoElements.find(v => v.videoWidth > 0) || videoElements[0] || null;
      }

      if (!videoElement) {
        setRecognitionResult({
          recognized: false,
          attendance: 'not_marked',
          statusText: 'Initializing camera video stream...',
        });
        setIsVerifyingAttendance(false);
        return;
      }

      const canvas = hiddenCanvasRef.current || document.createElement('canvas');
      canvas.width = videoElement.videoWidth || 640;
      canvas.height = videoElement.videoHeight || 480;

      const ctx = canvas.getContext('2d');
      if (!ctx) {
        setIsVerifyingAttendance(false);
        return;
      }

      ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);

      canvas.toBlob(async (blob) => {
        if (!blob) {
          setIsVerifyingAttendance(false);
          return;
        }
        try {
          setAiStatusMessage('Sampling AI face recognition...');
          const [attRes, emoRes] = await Promise.all([
            recognizeAttendance(targetSession, targetSession, blob).catch(() => null),
            analyzeFacialEmotion(targetSession, blob, studentId).catch(() => null),
          ]);

          if (attRes) {
            if (attRes.recognized && attRes.student_name && attRes.student_name !== 'Unknown') {
              const confPct = Math.round((attRes.confidence || 0.9) * 100);
              setRecognitionResult({
                recognized: true,
                studentId: attRes.student_id || undefined,
                studentName: attRes.student_name,
                confidence: confPct,
                attendance: 'present',
                statusText: `✓ ${attRes.student_name} recognized (${confPct}% confidence) — Attendance marked: PRESENT`,
              });
              setAiStatusMessage(`AI Active: Recognized ${attRes.student_name} (${confPct}%)`);
            } else {
              setRecognitionResult({
                recognized: false,
                attendance: 'not_marked',
                statusText: '⚠ Face not recognized — Attendance not marked',
              });
              setAiStatusMessage('AI Active: Face unrecognized');
            }
          }

          if (emoRes && (!attRes || !attRes.recognized)) {
            const emoLabel = emoRes?.predicted_label || 'attentive';
            setAiStatusMessage(`AI Active: Emotion: ${emoLabel}`);
          }
        } catch (aiErr) {
          console.warn('Frame AI sampling notice:', aiErr);
        } finally {
          setIsVerifyingAttendance(false);
        }
      }, 'image/jpeg', 0.85);
    } catch (err) {
      console.warn('Frame capture notice:', err);
      setIsVerifyingAttendance(false);
    }
  };

  // Poll Attendance Summary for Teacher View
  useEffect(() => {
    if (!isConnected) return;
    const targetSession = classroomData ? classroomData.livekit_room_name : roomName;

    const pollSummary = async () => {
      try {
        const summary = await fetchAttendanceSummary(targetSession);
        setAttendanceSummary(summary);
      } catch (err) {
        // Silently catch summary poll error
      }
    };

    pollSummary();
    const interval = setInterval(pollSummary, 4000);
    return () => clearInterval(interval);
  }, [isConnected, roomName, classroomData]);

  // Periodic AI Video Frame Sampling for Face Recognition & Emotion Analytics (Every 4s)
  useEffect(() => {
    if (!isConnected) return;

    const captureInterval = setInterval(() => {
      triggerAttendanceCheck();
    }, 4000);

    return () => clearInterval(captureInterval);
  }, [isConnected, roomName, classroomData, studentId]);

  // Clean up on component unmount
  useEffect(() => {
    return () => {
      if (roomRef.current) {
        roomRef.current.disconnect();
      }
    };
  }, []);

  // Handle Face Registration Submit
  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!regStudentId || !regFile) {
      setRegStatusMsg('Please provide both Student ID and a face image file.');
      return;
    }

    setIsRegistering(true);
    setRegStatusMsg(null);

    try {
      await registerStudentFace(regStudentId.trim(), regFile, regStudentName.trim());
      setRegStatusMsg(`✅ Success! Registered embedding for ${regStudentId}`);
    } catch (err: any) {
      setRegStatusMsg(`⚠️ Error: ${err.message || 'Registration failed'}`);
    } finally {
      setIsRegistering(false);
    }
  };

  return (
    <div className="classroom-wrapper">
      <canvas ref={hiddenCanvasRef} style={{ display: 'none' }} />
      <video ref={localWebcamRef} autoPlay playsInline muted style={{ display: 'none' }} />

      {/* Face Registration Bar */}
      {!isStudentView && (
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
          <button
            className="role-btn active"
            onClick={() => setShowRegModal(!showRegModal)}
            style={{ width: 'auto', padding: '0.5rem 1rem' }}
          >
            <UserPlus size={16} /> {showRegModal ? 'Close Face Registration' : 'Register Student Face'}
          </button>
        </div>
      )}

      {/* Face Registration Modal / Panel */}
      {showRegModal && !isStudentView && (
        <div className="join-card" style={{ maxWidth: '600px', marginBottom: '2rem', border: '1px solid var(--accent-blue)' }}>
          <h3>📷 Student Face Registration (Objective 1)</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
            Upload a student face image to extract and store feature embeddings for automated attendance recognition.
          </p>

          {regStatusMsg && (
            <div className="error-alert" style={{ background: 'rgba(56, 189, 248, 0.15)', color: 'var(--accent-blue)' }}>
              <span>{regStatusMsg}</span>
            </div>
          )}

          <form onSubmit={handleRegisterSubmit} className="join-form">
            <div className="form-group">
              <label>Student ID (e.g. 4CB23AI075)</label>
              <input
                type="text"
                value={regStudentId}
                onChange={(e) => setRegStudentId(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label>Student Name</label>
              <input
                type="text"
                value={regStudentName}
                onChange={(e) => setRegStudentName(e.target.value)}
                placeholder="e.g. Puneeth"
              />
            </div>
            <div className="form-group">
              <label>Face Image File (.jpg, .png)</label>
              <input
                type="file"
                accept="image/*"
                onChange={(e) => setRegFile(e.target.files ? e.target.files[0] : null)}
                required
              />
            </div>
            <button type="submit" className="join-btn" disabled={isRegistering}>
              {isRegistering ? 'Extracting Face Embedding...' : 'Register Face Embedding'}
            </button>
          </form>
        </div>
      )}

      {!isConnected ? (
        /* Pre-Join Teacher / Rejoin Setup Form */
        <div className="join-card">
          <div className="join-header">
            <div className="join-icon">
              <Radio size={26} />
            </div>
            <h2>Create or Join Online Classroom</h2>
            <p>Start a new live classroom or enter an existing join code</p>
          </div>

          {errorMessage && (
            <div className="error-alert">
              <span>⚠️ {errorMessage}</span>
            </div>
          )}

          <form onSubmit={handleCreateOrJoinRoom} className="join-form">
            <div className="form-group">
              <label>Teacher Name</label>
              <input
                type="text"
                value={identity}
                onChange={(e) => setIdentity(e.target.value)}
                placeholder="e.g. Prof. Smith"
                required
              />
            </div>

            <div className="form-group">
              <label>Class / Subject Name</label>
              <input
                type="text"
                value={roomName}
                onChange={(e) => setRoomName(e.target.value)}
                placeholder="e.g. Artificial Intelligence"
                required={!enterCode}
              />
            </div>

            <div className="form-group">
              <label>Subject Description (Optional)</label>
              <input
                type="text"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="e.g. Deep Learning & Computer Vision"
              />
            </div>

            <div className="form-group">
              <label>Optional Classroom Code to Rejoin (e.g. EDU-A7K92)</label>
              <input
                type="text"
                value={enterCode}
                onChange={(e) => setEnterCode(e.target.value)}
                placeholder="Enter Join Code (Leave empty to create new room)"
              />
            </div>

            <div className="form-group">
              <label>Participant Role</label>
              <div className="role-selector">
                <button
                  type="button"
                  className={`role-btn ${isTeacher ? 'active' : ''}`}
                  onClick={() => setIsTeacher(true)}
                >
                  <Shield size={16} /> Teacher (Host)
                </button>
                <button
                  type="button"
                  className={`role-btn ${!isTeacher ? 'active' : ''}`}
                  onClick={() => setIsTeacher(false)}
                >
                  <User size={16} /> Student
                </button>
              </div>
            </div>

            <button type="submit" className="join-btn" disabled={isConnecting}>
              {isConnecting ? (
                <span>Setting Up Classroom...</span>
              ) : (
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Play size={18} /> {enterCode ? 'Enter Existing Classroom' : 'Create & Start Classroom'}
                </span>
              )}
            </button>
          </form>
        </div>
      ) : (
        /* Active Classroom View (Google Meet-like Layout) */
        <div className="active-room-container">
          {/* Top Info Bar */}
          <div className="room-top-bar">
            <div className="room-info">
              <span className="live-indicator">● LIVE</span>
              <h3>Room: {classroomData ? classroomData.room_name : roomName}</h3>
              {classroomData && (
                <span style={{ fontSize: '0.85rem', color: '#34d399', backgroundColor: '#0f172a', padding: '2px 8px', borderRadius: '4px', border: '1px solid #334155' }}>
                  Code: <strong>{classroomData.join_code}</strong>
                </span>
              )}
              <span className="role-badge">{isTeacher ? 'Teacher View' : 'Student View'}</span>
              <span className="tag-placeholder" style={{ marginLeft: '0.5rem' }}>{aiStatusMessage}</span>
            </div>
            <button className="leave-btn" onClick={handleLeaveRoom}>
              <LogOut size={16} /> Leave Classroom
            </button>
          </div>

          {/* Shareable Join Code & Link Banner */}
          {classroomData && (
            <div style={{
              margin: '1rem 0',
              padding: '1.25rem',
              backgroundColor: 'var(--card-bg)',
              borderRadius: '12px',
              border: '1px solid var(--accent-blue)',
              boxShadow: '0 4px 12px rgba(0,0,0,0.2)'
            }}>
              <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', gap: '1rem' }}>
                <div>
                  <h4 style={{ margin: 0, fontSize: '1.1rem', color: '#ffffff' }}>
                    {classroomData.room_name} ONLINE CLASSROOM
                  </h4>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
                    Teacher: <strong>{classroomData.teacher_name}</strong> {classroomData.subject ? `| Subject: ${classroomData.subject}` : ''}
                  </div>
                </div>

                <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '0.75rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', backgroundColor: '#0f172a', padding: '0.4rem 0.8rem', borderRadius: '8px', border: '1px solid #334155' }}>
                    <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Code:</span>
                    <strong style={{ color: '#34d399', letterSpacing: '0.5px' }}>{classroomData.join_code}</strong>
                    <button
                      onClick={handleCopyCode}
                      style={{ background: 'none', border: 'none', color: '#60a5fa', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', padding: '2px 6px' }}
                    >
                      {copyCodeSuccess ? <Check size={16} color="#34d399" /> : <Copy size={16} />}
                      <span style={{ fontSize: '0.75rem' }}>{copyCodeSuccess ? 'Copied!' : 'COPY CODE'}</span>
                    </button>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', backgroundColor: '#0f172a', padding: '0.4rem 0.8rem', borderRadius: '8px', border: '1px solid #334155' }}>
                    <LinkIcon size={14} color="#60a5fa" />
                    <span style={{ fontSize: '0.8rem', color: '#e2e8f0' }}>{classroomData.join_url}</span>
                    <button
                      onClick={handleCopyLink}
                      style={{ background: 'none', border: 'none', color: '#60a5fa', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', padding: '2px 6px' }}
                    >
                      {copyLinkSuccess ? <Check size={16} color="#34d399" /> : <Copy size={16} />}
                      <span style={{ fontSize: '0.75rem' }}>{copyLinkSuccess ? 'Link copied!' : 'COPY JOIN LINK'}</span>
                    </button>
                  </div>
                </div>
              </div>

              {/* Roster Quick Stats */}
              <div style={{ display: 'flex', gap: '1.5rem', marginTop: '1rem', paddingTop: '0.8rem', borderTop: '1px solid #334155', fontSize: '0.85rem' }}>
                <span style={{ color: '#cbd5e1' }}><Users size={14} style={{ verticalAlign: 'middle' }} /> Participants: <strong>{participantsList.length}</strong></span>
                <span style={{ color: '#34d399' }}><UserCheck size={14} style={{ verticalAlign: 'middle' }} /> Present: <strong>{attendanceSummary?.present_students || 0}</strong></span>
                <span style={{ color: '#f87171' }}><UserX size={14} style={{ verticalAlign: 'middle' }} /> Absent: <strong>{attendanceSummary?.absent_students || 0}</strong></span>
                <span style={{ color: '#60a5fa' }}><Percent size={14} style={{ verticalAlign: 'middle' }} /> Attendance: <strong>{attendanceSummary?.attendance_percentage || 0}%</strong></span>
              </div>
            </div>
          )}

          {/* Student Face Recognition & Attendance Overlay Panel */}
          <div style={{
            margin: '1rem 0',
            padding: '1rem 1.25rem',
            backgroundColor: 'var(--card-bg)',
            borderRadius: '12px',
            border: recognitionResult?.recognized ? '1px solid #34d399' : '1px solid #334155',
            display: 'flex',
            flexWrap: 'wrap',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: '1rem'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <div style={{
                width: '42px',
                height: '42px',
                borderRadius: '10px',
                backgroundColor: recognitionResult?.recognized ? 'rgba(52, 211, 153, 0.15)' : 'rgba(59, 130, 246, 0.15)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                {recognitionResult?.recognized ? <UserCheck size={24} color="#34d399" /> : <Shield size={24} color="#60a5fa" />}
              </div>
              <div>
                <div style={{ fontSize: '0.8rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  Automated Face Recognition & Attendance
                </div>
                <div style={{ fontSize: '1rem', fontWeight: 600, color: recognitionResult?.recognized ? '#34d399' : '#e2e8f0', marginTop: '2px' }}>
                  {recognitionResult ? recognitionResult.statusText : 'Scanning camera frame for face recognition...'}
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <div style={{ fontSize: '0.85rem', color: '#cbd5e1' }}>
                Camera: <strong style={{ color: isCameraEnabled ? '#34d399' : '#f87171' }}>{isCameraEnabled ? 'ON' : 'OFF'}</strong>
                {' | '}
                Attendance: <strong style={{ color: recognitionResult?.recognized ? '#34d399' : '#f87171' }}>
                  {recognitionResult?.recognized ? 'PRESENT' : 'NOT MARKED'}
                </strong>
              </div>

              <button
                onClick={triggerAttendanceCheck}
                disabled={isVerifyingAttendance}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: '#3b82f6',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  cursor: isVerifyingAttendance ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.4rem',
                  boxShadow: '0 2px 8px rgba(59, 130, 246, 0.3)'
                }}
              >
                <Check size={16} />
                {isVerifyingAttendance ? 'Verifying...' : 'Verify Attendance Now'}
              </button>
            </div>
          </div>

          {/* Main Layout: Video Grid + Roster Sidebar */}
          <div className="room-content-layout">
            {/* Video Streams Area */}
            <div className="video-streams-area">
              {participantsList.map((participant) => (
                <VideoTile
                  key={participant.sid || participant.identity}
                  participant={participant}
                  isLocal={participant.identity === identity}
                  isTeacher={isTeacher && participant.identity === identity}
                />
              ))}
            </div>

            {/* Roster Sidebar */}
            <ParticipantList
              participants={participantsList}
              localParticipantIdentity={identity}
              teacherIdentity={isTeacher ? identity : undefined}
            />
          </div>

          {/* Teacher Live Attendance Panel Table */}
          {isTeacher && attendanceSummary && (
            <div style={{ margin: '1rem 0', padding: '1rem', backgroundColor: 'var(--card-bg)', borderRadius: '12px', border: '1px solid #334155' }}>
              <h4 style={{ margin: '0 0 0.8rem 0', fontSize: '1rem', color: '#ffffff', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <UserCheck size={18} color="#34d399" /> Live Student Attendance Panel
              </h4>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem', color: '#e2e8f0' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid #334155', textAlign: 'left', color: '#94a3b8' }}>
                      <th style={{ padding: '0.5rem 0.75rem' }}>Student ID</th>
                      <th style={{ padding: '0.5rem 0.75rem' }}>Name</th>
                      <th style={{ padding: '0.5rem 0.75rem' }}>Status</th>
                      <th style={{ padding: '0.5rem 0.75rem' }}>Recognition Time</th>
                    </tr>
                  </thead>
                  <tbody>
                    {attendanceSummary.records && attendanceSummary.records.length > 0 ? (
                      attendanceSummary.records.map((rec) => (
                        <tr key={rec.id} style={{ borderBottom: '1px solid #1e293b' }}>
                          <td style={{ padding: '0.5rem 0.75rem', fontFamily: 'monospace', color: '#60a5fa' }}>
                            {rec.student_id_code || `STU-${rec.student_id}`}
                          </td>
                          <td style={{ padding: '0.5rem 0.75rem', fontWeight: 600 }}>
                            {rec.student_name || 'Student'}
                          </td>
                          <td style={{ padding: '0.5rem 0.75rem' }}>
                            <span style={{
                              padding: '2px 8px',
                              borderRadius: '4px',
                              fontSize: '0.75rem',
                              fontWeight: 700,
                              backgroundColor: rec.status === 'PRESENT' ? 'rgba(52, 211, 153, 0.2)' : 'rgba(248, 113, 113, 0.2)',
                              color: rec.status === 'PRESENT' ? '#34d399' : '#f87171'
                            }}>
                              {rec.status}
                            </span>
                          </td>
                          <td style={{ padding: '0.5rem 0.75rem', color: '#94a3b8' }}>
                            {new Date(rec.timestamp).toLocaleTimeString()}
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={4} style={{ padding: '1rem', textAlign: 'center', color: '#94a3b8' }}>
                          No student attendance records captured yet. Automatic face recognition is actively scanning...
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Room Controls Bar */}
          <ClassroomControls
            isMicEnabled={isMicEnabled}
            isCameraEnabled={isCameraEnabled}
            onToggleMic={toggleMic}
            onToggleCamera={toggleCamera}
            onLeaveRoom={handleLeaveRoom}
            onCopyLink={classroomData ? handleCopyLink : undefined}
            onCopyCode={classroomData ? handleCopyCode : undefined}
            copiedState={copyLinkSuccess ? 'link' : copyCodeSuccess ? 'code' : null}
          />
        </div>
      )}
    </div>
  );
};

export default Classroom;
