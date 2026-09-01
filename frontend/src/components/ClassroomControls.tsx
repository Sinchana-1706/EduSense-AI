import React from 'react';
import { Mic, MicOff, Video, VideoOff, LogOut, Copy, Link } from 'lucide-react';

export interface ClassroomControlsProps {
  isMicEnabled: boolean;
  isCameraEnabled: boolean;
  onToggleMic: () => void;
  onToggleCamera: () => void;
  onLeaveRoom: () => void;
  onCopyLink?: () => void;
  onCopyCode?: () => void;
  copiedState?: string | null;
}

export const ClassroomControls: React.FC<ClassroomControlsProps> = ({
  isMicEnabled,
  isCameraEnabled,
  onToggleMic,
  onToggleCamera,
  onLeaveRoom,
  onCopyLink,
  onCopyCode,
  copiedState,
}) => {
  return (
    <div className="controls-bar">
      <button
        className={`control-btn ${!isMicEnabled ? 'muted' : ''}`}
        onClick={onToggleMic}
        title={isMicEnabled ? 'Mute Microphone' : 'Unmute Microphone'}
      >
        {isMicEnabled ? <Mic size={20} /> : <MicOff size={20} />}
        <span>{isMicEnabled ? 'Mute Mic' : 'Unmute Mic'}</span>
      </button>

      <button
        className={`control-btn ${!isCameraEnabled ? 'off' : ''}`}
        onClick={onToggleCamera}
        title={isCameraEnabled ? 'Turn Off Camera' : 'Turn On Camera'}
      >
        {isCameraEnabled ? <Video size={20} /> : <VideoOff size={20} />}
        <span>{isCameraEnabled ? 'Stop Video' : 'Start Video'}</span>
      </button>

      {onCopyLink && (
        <button
          className="control-btn"
          onClick={onCopyLink}
          title="Copy Shareable Join Link"
          style={{ border: '1px solid #334155', background: '#1e293b' }}
        >
          <Link size={18} color="#60a5fa" />
          <span>{copiedState === 'link' ? 'Copied Link!' : 'Copy Link'}</span>
        </button>
      )}

      {onCopyCode && (
        <button
          className="control-btn"
          onClick={onCopyCode}
          title="Copy Classroom Join Code"
          style={{ border: '1px solid #334155', background: '#1e293b' }}
        >
          <Copy size={18} color="#34d399" />
          <span>{copiedState === 'code' ? 'Copied Code!' : 'Copy Code'}</span>
        </button>
      )}

      <button className="control-btn leave-control-btn" onClick={onLeaveRoom} title="Leave Classroom">
        <LogOut size={20} />
        <span>Leave Classroom</span>
      </button>
    </div>
  );
};

export default ClassroomControls;
