import React, { useState, useEffect } from 'react';
import { getClassroomByCode, joinClassroomByCode, ClassroomData } from '../services/api';
import { Classroom } from './Classroom';
import { Video, ShieldCheck, AlertCircle, ArrowRight } from 'lucide-react';

interface StudentJoinViewProps {
  joinCode: string;
}

export const StudentJoinView: React.FC<StudentJoinViewProps> = ({ joinCode }) => {
  const [classroom, setClassroom] = useState<ClassroomData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [studentId, setStudentId] = useState<string>('4CB23AI075');
  const [studentName, setStudentName] = useState<string>('Puneeth');
  const [isJoining, setIsJoining] = useState<boolean>(false);

  // Joined State credentials
  const [joinedSession, setJoinedSession] = useState<{
    livekitRoomName: string;
    studentName: string;
    studentId: string;
    token: string;
  } | null>(null);

  useEffect(() => {
    async function loadClassroom() {
      setLoading(true);
      setErrorMsg(null);
      try {
        const data = await getClassroomByCode(joinCode);
        setClassroom(data);
      } catch (err: any) {
        setErrorMsg(err.message || 'Classroom not found or inactive.');
      } finally {
        setLoading(false);
      }
    }
    if (joinCode) {
      loadClassroom();
    }
  }, [joinCode]);

  const handleStudentJoin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!studentId.trim() || !studentName.trim()) {
      setErrorMsg('Please enter both Student ID and Student Name.');
      return;
    }

    setIsJoining(true);
    setErrorMsg(null);

    try {
      const joinData = await joinClassroomByCode(joinCode, studentId.trim(), studentName.trim());
      setJoinedSession({
        livekitRoomName: joinData.classroom.livekit_room_name,
        studentName: joinData.student_name,
        studentId: joinData.student_id,
        token: joinData.token,
      });
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to join classroom.');
    } finally {
      setIsJoining(false);
    }
  };

  if (joinedSession) {
    return (
      <Classroom
        initialRoomName={joinedSession.livekitRoomName}
        initialTeacherName={joinedSession.studentName}
        isStudentView={true}
        studentId={joinedSession.studentId}
        preJoinedToken={joinedSession.token}
      />
    );
  }

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#0f172a',
      color: '#f8fafc',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px',
      fontFamily: 'Inter, system-ui, sans-serif'
    }}>
      <div style={{
        width: '100%',
        maxWidth: '520px',
        backgroundColor: '#1e293b',
        borderRadius: '16px',
        border: '1px solid #334155',
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.5)',
        overflow: 'hidden'
      }}>
        {/* Header */}
        <div style={{
          padding: '28px 32px 20px 32px',
          borderBottom: '1px solid #334155',
          background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: '10px',
              backgroundColor: '#3b82f6',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Video size={24} color="#ffffff" />
            </div>
            <div>
              <h2 style={{ margin: 0, fontSize: '22px', fontWeight: 700, color: '#ffffff' }}>
                JOIN ONLINE CLASS
              </h2>
              <span style={{ fontSize: '13px', color: '#94a3b8' }}>
                EduSense AI Smart Classroom
              </span>
            </div>
          </div>
        </div>

        {/* Content Area */}
        <div style={{ padding: '32px' }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '32px 0', color: '#94a3b8' }}>
              Validating join code <strong>{joinCode}</strong>...
            </div>
          ) : errorMsg && !classroom ? (
            <div style={{
              padding: '16px',
              borderRadius: '12px',
              backgroundColor: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              color: '#fca5a5',
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              marginBottom: '20px'
            }}>
              <AlertCircle size={20} color="#ef4444" />
              <span>{errorMsg}</span>
            </div>
          ) : (
            classroom && (
              <>
                {/* Classroom Metadata Card */}
                <div style={{
                  padding: '18px 20px',
                  borderRadius: '12px',
                  backgroundColor: '#0f172a',
                  border: '1px solid #334155',
                  marginBottom: '24px'
                }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                    <div>
                      <span style={{ fontSize: '12px', color: '#94a3b8', display: 'block', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                        Classroom
                      </span>
                      <strong style={{ fontSize: '16px', color: '#60a5fa' }}>
                        {classroom.room_name}
                      </strong>
                    </div>
                    <div>
                      <span style={{ fontSize: '12px', color: '#94a3b8', display: 'block', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                        Join Code
                      </span>
                      <strong style={{ fontSize: '16px', color: '#34d399', letterSpacing: '1px' }}>
                        {classroom.join_code}
                      </strong>
                    </div>
                    {classroom.subject && (
                      <div style={{ gridColumn: 'span 2' }}>
                        <span style={{ fontSize: '12px', color: '#94a3b8', display: 'block', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                          Subject
                        </span>
                        <span style={{ fontSize: '14px', color: '#e2e8f0' }}>
                          {classroom.subject}
                        </span>
                      </div>
                    )}
                    <div style={{ gridColumn: 'span 2' }}>
                      <span style={{ fontSize: '12px', color: '#94a3b8', display: 'block', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                        Teacher
                      </span>
                      <span style={{ fontSize: '14px', color: '#e2e8f0' }}>
                        {classroom.teacher_name}
                      </span>
                    </div>
                  </div>
                </div>

                {errorMsg && (
                  <div style={{
                    padding: '12px 16px',
                    borderRadius: '8px',
                    backgroundColor: 'rgba(239, 68, 68, 0.15)',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    color: '#fca5a5',
                    fontSize: '14px',
                    marginBottom: '20px'
                  }}>
                    ⚠️ {errorMsg}
                  </div>
                )}

                {/* Form */}
                <form onSubmit={handleStudentJoin} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#cbd5e1', marginBottom: '8px' }}>
                      Student ID (e.g. 4CB23AI075)
                    </label>
                    <input
                      type="text"
                      value={studentId}
                      onChange={(e) => setStudentId(e.target.value)}
                      placeholder="Enter Student ID"
                      required
                      style={{
                        width: '100%',
                        padding: '12px 16px',
                        backgroundColor: '#0f172a',
                        border: '1px solid #334155',
                        borderRadius: '8px',
                        color: '#ffffff',
                        fontSize: '15px',
                        outline: 'none',
                        boxSizing: 'border-box'
                      }}
                    />
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#cbd5e1', marginBottom: '8px' }}>
                      Student Name (e.g. Puneeth)
                    </label>
                    <input
                      type="text"
                      value={studentName}
                      onChange={(e) => setStudentName(e.target.value)}
                      placeholder="Enter Student Full Name"
                      required
                      style={{
                        width: '100%',
                        padding: '12px 16px',
                        backgroundColor: '#0f172a',
                        border: '1px solid #334155',
                        borderRadius: '8px',
                        color: '#ffffff',
                        fontSize: '15px',
                        outline: 'none',
                        boxSizing: 'border-box'
                      }}
                    />
                  </div>

                  <div style={{
                    padding: '12px',
                    borderRadius: '8px',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    border: '1px solid rgba(59, 130, 246, 0.2)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    fontSize: '12px',
                    color: '#93c5fd'
                  }}>
                    <ShieldCheck size={18} color="#60a5fa" />
                    <span>Your camera will activate upon joining for automated AI face attendance.</span>
                  </div>

                  <button
                    type="submit"
                    disabled={isJoining}
                    style={{
                      marginTop: '8px',
                      padding: '14px 20px',
                      backgroundColor: '#3b82f6',
                      color: '#ffffff',
                      border: 'none',
                      borderRadius: '10px',
                      fontSize: '16px',
                      fontWeight: 600,
                      cursor: isJoining ? 'not-allowed' : 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '8px',
                      boxShadow: '0 4px 12px rgba(59, 130, 246, 0.3)',
                      transition: 'background-color 0.2s ease'
                    }}
                  >
                    {isJoining ? 'Connecting to Classroom...' : 'JOIN CLASSROOM'}
                    {!isJoining && <ArrowRight size={18} />}
                  </button>
                </form>
              </>
            )
          )}
        </div>
      </div>
    </div>
  );
};
