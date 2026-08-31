import React, { useState, useEffect, useRef } from 'react';
import { Room, RoomEvent, Participant, RemoteParticipant } from 'livekit-client';
import {
  requestLiveKitToken,
  recognizeAttendance,
  analyzeFacialEmotion,
  registerStudentFace,
} from '../services/api';
import { VideoTile } from './VideoTile';
import { ParticipantList } from './ParticipantList';
import { ClassroomControls } from './ClassroomControls';
import { LogOut, Radio, Shield, User, Play, UserPlus } from 'lucide-react';

export interface ClassroomProps {
  initialRoomName?: string;
  initialTeacherName?: string;
}

export const Classroom: React.FC<ClassroomProps> = ({
  initialRoomName = 'CS-101',
  initialTeacherName = 'Prof. Smith',
}) => {
  // Pre-join Form State
  const [roomName, setRoomName] = useState<string>(initialRoomName);
  const [identity, setIdentity] = useState<string>(initialTeacherName);
  const [isTeacher, setIsTeacher] = useState<boolean>(true);

  // Connection & Room Lifecycle State
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [isConnecting, setIsConnecting] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Student Registration Modal State
  const [showRegModal, setShowRegModal] = useState<boolean>(false);
  const [regStudentId, setRegStudentId] = useState<string>('STU-001');
  const [regStudentName, setRegStudentName] = useState<string>('Alice Johnson');
  const [regFile, setRegFile] = useState<File | null>(null);
  const [regStatusMsg, setRegStatusMsg] = useState<string | null>(null);
  const [isRegistering, setIsRegistering] = useState<boolean>(false);

  // LiveKit Room & Media Controls State
  const roomRef = useRef<Room | null>(null);
  const hiddenCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const [isMicEnabled, setIsMicEnabled] = useState<boolean>(true);
  const [isCameraEnabled, setIsCameraEnabled] = useState<boolean>(true);
  const [participantsList, setParticipantsList] = useState<Participant[]>([]);
  const [aiStatusMessage, setAiStatusMessage] = useState<string>('AI Analytics Idle');

  useEffect(() => {
    if (initialRoomName) setRoomName(initialRoomName);
    if (initialTeacherName) setIdentity(initialTeacherName);
  }, [initialRoomName, initialTeacherName]);

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

  const handleJoinRoom = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!roomName.trim() || !identity.trim()) {
      setErrorMessage('Please enter both your name and a valid classroom name.');
      return;
    }

    setIsConnecting(true);
    setErrorMessage(null);

    try {
      // 1. Request LiveKit access token from backend API
      const tokenData = await requestLiveKitToken(
        roomName.trim(),
        identity.trim(),
        isTeacher
      );

      // 2. Instantiate LiveKit Room
      const room = new Room({
        adaptiveStream: true,
        dynacast: true,
      });

      roomRef.current = room;

      // 3. Register LiveKit Room Event Handlers
      room.on(RoomEvent.ParticipantConnected, updateParticipantsList);
      room.on(RoomEvent.ParticipantDisconnected, updateParticipantsList);
      room.on(RoomEvent.TrackSubscribed, updateParticipantsList);
      room.on(RoomEvent.TrackUnsubscribed, updateParticipantsList);
      room.on(RoomEvent.LocalTrackPublished, updateParticipantsList);
      room.on(RoomEvent.Disconnected, () => {
        setIsConnected(false);
        setParticipantsList([]);
      });

      // 4. Connect to LiveKit server via WebSocket
      await room.connect(tokenData.livekit_url, tokenData.token);
      setIsConnected(true);

      // 5. Enable camera & microphone by default
      try {
        await room.localParticipant.enableCameraAndMicrophone();
        setIsMicEnabled(room.localParticipant.isMicrophoneEnabled);
        setIsCameraEnabled(room.localParticipant.isCameraEnabled);
      } catch (mediaErr: any) {
        console.warn('Camera/Microphone permissions skipped or denied:', mediaErr);
      }

      updateParticipantsList();
    } catch (err: any) {
      console.error('Error connecting to classroom:', err);
      setErrorMessage(
        err.message || 'Failed to connect to LiveKit classroom. Please check backend connection.'
      );
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
    setIsConnected(false);
    setParticipantsList([]);
  };

  // Periodic AI Video Frame Sampling for Face Recognition & Emotion Analytics
  useEffect(() => {
    if (!isConnected) return;

    const captureInterval = setInterval(async () => {
      try {
        const videoElement = document.querySelector<HTMLVideoElement>('.video-element');
        if (!videoElement || videoElement.videoWidth === 0) return;

        const canvas = hiddenCanvasRef.current || document.createElement('canvas');
        canvas.width = videoElement.videoWidth || 640;
        canvas.height = videoElement.videoHeight || 480;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);

        canvas.toBlob(async (blob) => {
          if (!blob) return;
          try {
            setAiStatusMessage('Processing AI frame...');
            const [attRes, emoRes] = await Promise.all([
              recognizeAttendance(roomName, roomName, blob).catch(() => null),
              analyzeFacialEmotion(roomName, blob).catch(() => null),
            ]);

            if (attRes || emoRes) {
              const recCount = attRes?.recognized_count || 0;
              const emoLabel = emoRes?.predicted_label || 'analyzed';
              setAiStatusMessage(`AI Active: Recognized ${recCount} student(s) | Emotion: ${emoLabel}`);
            }
          } catch (aiErr) {
            console.warn('Frame AI sampling notice:', aiErr);
          }
        }, 'image/jpeg', 0.85);
      } catch (err) {
        console.warn('Frame capture notice:', err);
      }
    }, 6000); // Sample every 6 seconds

    return () => clearInterval(captureInterval);
  }, [isConnected, roomName]);

  // Clean up on component unmount
  useEffect(() => {
    return () => {
      if (roomRef.current) {
        roomRef.current.disconnect();
      }
    };
  }, []);

  // Handle Face Registration
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

      {/* Face Registration Modal Trigger Bar */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
        <button
          className="role-btn active"
          onClick={() => setShowRegModal(!showRegModal)}
          style={{ width: 'auto', padding: '0.5rem 1rem' }}
        >
          <UserPlus size={16} /> {showRegModal ? 'Close Face Registration' : 'Register Student Face'}
        </button>
      </div>

      {/* Face Registration Modal / Panel */}
      {showRegModal && (
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
              <label>Student ID (e.g. STU-001)</label>
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
                placeholder="e.g. Alice Johnson"
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
        /* Pre-Join Teacher Setup Form */
        <div className="join-card">
          <div className="join-header">
            <div className="join-icon">
              <Radio size={26} />
            </div>
            <h2>Start Online Classroom</h2>
            <p>Connect to real-time LiveKit audio & video classroom session</p>
          </div>

          {errorMessage && (
            <div className="error-alert">
              <span>⚠️ {errorMessage}</span>
            </div>
          )}

          <form onSubmit={handleJoinRoom} className="join-form">
            <div className="form-group">
              <label>Teacher Name / Identity</label>
              <input
                type="text"
                value={identity}
                onChange={(e) => setIdentity(e.target.value)}
                placeholder="e.g. Prof. Smith"
                required
              />
            </div>

            <div className="form-group">
              <label>Classroom / Room Name</label>
              <input
                type="text"
                value={roomName}
                onChange={(e) => setRoomName(e.target.value)}
                placeholder="e.g. CS-101"
                required
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
                <span>Connecting to LiveKit...</span>
              ) : (
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Play size={18} /> Start Classroom
                </span>
              )}
            </button>
          </form>
        </div>
      ) : (
        /* Active Classroom Room View */
        <div className="active-room-container">
          {/* Top Info Bar */}
          <div className="room-top-bar">
            <div className="room-info">
              <span className="live-indicator">● LIVE</span>
              <h3>Room: {roomName}</h3>
              <span className="role-badge">{isTeacher ? 'Teacher / Host View' : 'Student View'}</span>
              <span className="tag-placeholder" style={{ marginLeft: '1rem' }}>{aiStatusMessage}</span>
            </div>
            <button className="leave-btn" onClick={handleLeaveRoom}>
              <LogOut size={16} /> Leave Classroom
            </button>
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

          {/* Room Controls Bar */}
          <ClassroomControls
            isMicEnabled={isMicEnabled}
            isCameraEnabled={isCameraEnabled}
            onToggleMic={toggleMic}
            onToggleCamera={toggleCamera}
            onLeaveRoom={handleLeaveRoom}
          />
        </div>
      )}
    </div>
  );
};

export default Classroom;
