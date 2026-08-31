import React from 'react';
import { Participant } from 'livekit-client';
import { Users, Mic, MicOff, Video, VideoOff, Shield } from 'lucide-react';

export interface ParticipantListProps {
  participants: Participant[];
  localParticipantIdentity: string;
  teacherIdentity?: string;
}

export const ParticipantList: React.FC<ParticipantListProps> = ({
  participants,
  localParticipantIdentity,
  teacherIdentity,
}) => {
  return (
    <div className="participants-sidebar">
      <div className="sidebar-header">
        <Users size={18} />
        <h4>Classroom Roster ({participants.length})</h4>
      </div>

      <div className="participants-list">
        {participants.length === 0 ? (
          <div className="empty-roster-text">No active participants</div>
        ) : (
          participants.map((p) => {
            const isLocal = p.identity === localParticipantIdentity;
            const isTeacher = teacherIdentity ? p.identity === teacherIdentity : false;
            const isMicOn = p.isMicrophoneEnabled;
            const isCamOn = p.isCameraEnabled;

            return (
              <div key={p.sid || p.identity} className="participant-tile">
                <div className="participant-info-group">
                  <div className="participant-name">
                    {isTeacher && (
                      <span className="roster-teacher-badge" title="Teacher / Host">
                        <Shield size={12} />
                      </span>
                    )}
                    <span>{p.identity || 'Participant'}</span>
                    {isLocal && <span className="you-tag">You</span>}
                  </div>
                </div>

                <div className="participant-media-status">
                  {isMicOn ? (
                    <span title="Microphone Unmuted"><Mic size={14} className="icon-on" /></span>
                  ) : (
                    <span title="Microphone Muted"><MicOff size={14} className="icon-off" /></span>
                  )}
                  {isCamOn ? (
                    <span title="Camera On"><Video size={14} className="icon-on" /></span>
                  ) : (
                    <span title="Camera Off"><VideoOff size={14} className="icon-off" /></span>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

export default ParticipantList;
