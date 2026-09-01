import React, { useEffect, useRef, useState } from 'react';
import {
  Participant,
  Track,
  RemoteTrackPublication,
  LocalTrackPublication,
  ParticipantEvent,
} from 'livekit-client';
import { User, Mic, MicOff, VideoOff, Shield } from 'lucide-react';

export interface VideoTileProps {
  participant: Participant;
  isLocal?: boolean;
  isTeacher?: boolean;
}

export const VideoTile: React.FC<VideoTileProps> = ({
  participant,
  isLocal = false,
  isTeacher = false,
}) => {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const [hasVideoTrack, setHasVideoTrack] = useState<boolean>(false);
  const [isMicEnabled, setIsMicEnabled] = useState<boolean>(participant.isMicrophoneEnabled);
  const [isCameraEnabled, setIsCameraEnabled] = useState<boolean>(participant.isCameraEnabled);

  useEffect(() => {
    setIsMicEnabled(participant.isMicrophoneEnabled);
    setIsCameraEnabled(participant.isCameraEnabled);

    const attachTracks = () => {
      participant.trackPublications.forEach((publication) => {
        if (publication.track) {
          if (publication.kind === Track.Kind.Video && videoRef.current) {
            publication.track.attach(videoRef.current);
            setHasVideoTrack(true);
          } else if (publication.kind === Track.Kind.Audio && audioRef.current && !isLocal) {
            publication.track.attach(audioRef.current);
          }
        }
      });
    };

    const handleTrackSubscribed = (
      publication: RemoteTrackPublication | LocalTrackPublication
    ) => {
      if (publication.track) {
        if (publication.kind === Track.Kind.Video && videoRef.current) {
          publication.track.attach(videoRef.current);
          setHasVideoTrack(true);
        } else if (publication.kind === Track.Kind.Audio && audioRef.current && !isLocal) {
          publication.track.attach(audioRef.current);
        }
      }
    };

    const handleTrackUnsubscribed = (
      publication: RemoteTrackPublication | LocalTrackPublication
    ) => {
      if (publication.track) {
        publication.track.detach();
        if (publication.kind === Track.Kind.Video) {
          setHasVideoTrack(false);
        }
      }
    };

    const handleMuteChanged = () => {
      setIsMicEnabled(participant.isMicrophoneEnabled);
      setIsCameraEnabled(participant.isCameraEnabled);
      attachTracks();
    };

    // Attach existing published tracks immediately
    attachTracks();

    // Subscribe to participant events using ParticipantEvent enum
    participant.on(ParticipantEvent.TrackSubscribed, (_track, publication) => {
      handleTrackSubscribed(publication as any);
    });

    participant.on(ParticipantEvent.TrackUnsubscribed, (_track, publication) => {
      handleTrackUnsubscribed(publication as any);
    });

    participant.on(ParticipantEvent.LocalTrackPublished, () => {
      attachTracks();
    });

    participant.on(ParticipantEvent.TrackMuted, handleMuteChanged);
    participant.on(ParticipantEvent.TrackUnmuted, handleMuteChanged);

    // Periodic check to ensure video element remains attached
    const interval = setInterval(() => {
      setIsMicEnabled(participant.isMicrophoneEnabled);
      setIsCameraEnabled(participant.isCameraEnabled);
      if (participant.isCameraEnabled && !hasVideoTrack) {
        attachTracks();
      }
    }, 1500);

    return () => {
      clearInterval(interval);
      participant.trackPublications.forEach((pub) => {
        if (pub.track) {
          pub.track.detach();
        }
      });
      participant.off(ParticipantEvent.TrackSubscribed, (_track, publication) => {
        handleTrackSubscribed(publication as any);
      });
      participant.off(ParticipantEvent.TrackUnsubscribed, (_track, publication) => {
        handleTrackUnsubscribed(publication as any);
      });
      participant.off(ParticipantEvent.TrackMuted, handleMuteChanged);
      participant.off(ParticipantEvent.TrackUnmuted, handleMuteChanged);
    };
  }, [participant, isLocal]);

  return (
    <div className={`video-box ${isLocal ? 'local-video-box' : 'remote-video-box'}`}>
      {/* Hidden audio element for listening to remote participant audio */}
      {!isLocal && <audio ref={audioRef} autoPlay />}

      {/* Video Element */}
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted={isLocal}
        className={`video-element ${!isCameraEnabled || !hasVideoTrack ? 'hidden-video' : ''}`}
      />

      {/* Avatar Fallback when camera is disabled or track is unavailable */}
      {(!isCameraEnabled || !hasVideoTrack) && (
        <div className="video-avatar-fallback">
          <div className="avatar-circle">
            <User size={36} />
          </div>
          <p className="avatar-name">{participant.identity || 'Participant'}</p>
          <span className="camera-off-badge">
            <VideoOff size={14} /> Camera Off
          </span>
        </div>
      )}

      {/* Participant Overlay Header & Footer */}
      <div className="video-overlay">
        <div className="overlay-identity">
          {isTeacher && (
            <span className="teacher-icon-badge" title="Teacher / Host">
              <Shield size={12} />
            </span>
          )}
          <span>{participant.identity}</span>
          {isLocal && <span className="you-tag">You</span>}
        </div>

        <div className="overlay-audio-status">
          {isMicEnabled ? (
            <span className="mic-badge mic-on" title="Microphone Active">
              <Mic size={14} />
            </span>
          ) : (
            <span className="mic-badge mic-off" title="Microphone Muted">
              <MicOff size={14} />
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default VideoTile;
