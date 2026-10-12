/**
 * audioRecorder.ts
 * Browser-side audio chunker and 16kHz mono WAV encoder.
 * Samples audio directly from MediaStreamTrack and produces standard PCM WAV blobs.
 */

export interface AudioRecorderStatus {
  isRecording: boolean;
  contextState: AudioContextState | 'uninitialized';
  bufferedSeconds: number;
  chunkCount: number;
}

export interface AudioChunkDiagnostics {
  byteSize: number;
  durationSeconds: number;
  sampleRate: number;
  channelCount: number;
  sampleCount: number;
  peakAmplitude: number;
  rmsAmplitude: number;
  isAllZeros: boolean;
  isNearSilence: boolean;
}

export class AudioChunkRecorder {
  private audioContext: AudioContext | null = null;
  private sourceNode: MediaStreamAudioSourceNode | null = null;
  private processorNode: ScriptProcessorNode | null = null;
  private destNode: MediaStreamAudioDestinationNode | null = null;
  private activeStream: MediaStream | null = null;
  private recordedChunks: Float32Array[] = [];
  private isRecording: boolean = false;
  private sampleRate: number = 16000;
  private lastDiagnostics: AudioChunkDiagnostics | null = null;

  constructor(targetSampleRate: number = 16000) {
    this.sampleRate = targetSampleRate;
  }

  /**
   * Initializes audio recording from an active MediaStream.
   * Gracefully handles browser autoplay policies, GC references, and destination routing.
   */
  public async start(stream: MediaStream): Promise<void> {
    if (this.isRecording) return;

    this.recordedChunks = [];
    this.activeStream = stream; // Retain strong reference to prevent Chrome GC

    const audioTracks = stream.getAudioTracks();
    if (!audioTracks || audioTracks.length === 0) {
      console.warn('[AudioChunkRecorder] Warning: MediaStream has no audio tracks.');
    } else {
      const trk = audioTracks[0];
      console.log(`[AudioChunkRecorder] Using audio track: label="${trk.label}", enabled=${trk.enabled}, readyState=${trk.readyState}, muted=${trk.muted}`);
    }

    const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
    if (!AudioContextClass) {
      throw new Error('Web Audio API is not supported in this browser.');
    }

    // Try target sample rate (16000) if browser supports it natively; fallback to default
    try {
      this.audioContext = new AudioContextClass({ sampleRate: this.sampleRate });
    } catch {
      this.audioContext = new AudioContextClass();
    }

    // If context starts in suspended state due to browser autoplay policies, try resuming
    if (this.audioContext.state === 'suspended') {
      try {
        await this.audioContext.resume();
      } catch (err) {
        console.warn('[AudioChunkRecorder] AudioContext initial resume delayed by browser policy:', err);
      }
    }

    const sourceSr = this.audioContext.sampleRate;
    this.sourceNode = this.audioContext.createMediaStreamSource(stream);

    // Buffer size 4096 gives ~85-92ms intervals at typical sample rates
    this.processorNode = this.audioContext.createScriptProcessor(4096, 1, 1);

    // MediaStreamDestination node keeps ScriptProcessor active in destination graph
    // without playing mic audio back through speakers (completely preventing howling & AEC suppression)
    this.destNode = this.audioContext.createMediaStreamDestination();

    this.processorNode.onaudioprocess = (e: AudioProcessingEvent) => {
      if (!this.isRecording) return;
      const inputData = e.inputBuffer.getChannelData(0);
      const resampled = this.downsampleBuffer(inputData, sourceSr, this.sampleRate);
      this.recordedChunks.push(resampled);
    };

    this.sourceNode.connect(this.processorNode);
    this.processorNode.connect(this.destNode);
    this.isRecording = true;
    console.log('[AudioChunkRecorder] Started recording. AudioContext state:', this.audioContext.state, 'sampleRate:', sourceSr);
  }

  /**
   * Manually resumes AudioContext on user gesture if suspended.
   */
  public async resume(): Promise<boolean> {
    if (this.audioContext && this.audioContext.state === 'suspended') {
      try {
        await this.audioContext.resume();
        console.log('[AudioChunkRecorder] AudioContext resumed successfully. State:', this.audioContext.state);
        return true;
      } catch (err) {
        console.warn('[AudioChunkRecorder] AudioContext resume failed:', err);
        return false;
      }
    }
    return this.audioContext?.state === 'running';
  }

  /**
   * Returns current recorder status and buffered audio duration.
   */
  public getStatus(): AudioRecorderStatus {
    let sampleCount = 0;
    for (const chunk of this.recordedChunks) {
      sampleCount += chunk.length;
    }
    return {
      isRecording: this.isRecording,
      contextState: this.audioContext?.state || 'uninitialized',
      bufferedSeconds: sampleCount / this.sampleRate,
      chunkCount: this.recordedChunks.length,
    };
  }

  /**
   * Returns diagnostics of the most recently extracted audio chunk.
   */
  public getLastDiagnostics(): AudioChunkDiagnostics | null {
    return this.lastDiagnostics;
  }

  /**
   * Returns active MediaStream or null.
   */
  public getActiveStream(): MediaStream | null {
    return this.activeStream;
  }

  /**
   * Returns seconds of audio currently buffered.
   */
  public getBufferedSeconds(): number {
    let sampleCount = 0;
    for (const chunk of this.recordedChunks) {
      sampleCount += chunk.length;
    }
    return sampleCount / this.sampleRate;
  }

  /**
   * Extracts currently recorded audio as a 16kHz mono WAV Blob and resets buffer, keeping recording active.
   */
  public getChunkAndReset(): Blob | null {
    if (this.audioContext && this.audioContext.state === 'suspended') {
      this.audioContext.resume().catch(() => {});
    }

    if (!this.isRecording || this.recordedChunks.length === 0) return null;

    const chunks = this.recordedChunks;
    this.recordedChunks = [];

    let totalLength = 0;
    for (const chunk of chunks) {
      totalLength += chunk.length;
    }
    if (totalLength === 0) return null;

    const merged = new Float32Array(totalLength);
    let offset = 0;
    let peak = 0;
    let sumSq = 0;

    for (const chunk of chunks) {
      merged.set(chunk, offset);
      offset += chunk.length;
      for (let i = 0; i < chunk.length; i++) {
        const val = Math.abs(chunk[i]);
        if (val > peak) peak = val;
        sumSq += val * val;
      }
    }

    const rms = Math.sqrt(sumSq / totalLength);
    const isAllZeros = peak === 0;
    const isNearSilence = peak < 0.001 && rms < 0.0001;

    this.lastDiagnostics = {
      byteSize: 44 + totalLength * 2,
      durationSeconds: Number((totalLength / this.sampleRate).toFixed(2)),
      sampleRate: this.sampleRate,
      channelCount: 1,
      sampleCount: totalLength,
      peakAmplitude: Number(peak.toFixed(5)),
      rmsAmplitude: Number(rms.toFixed(6)),
      isAllZeros,
      isNearSilence,
    };

    console.log(
      `[AudioChunkRecorder DIAG] Chunk: ${totalLength} samples (${this.lastDiagnostics.durationSeconds}s), Peak: ${this.lastDiagnostics.peakAmplitude}, RMS: ${this.lastDiagnostics.rmsAmplitude}, AllZeros: ${isAllZeros}`
    );

    return this.encodeWAV(merged, this.sampleRate);
  }

  /**
   * Stops recording and returns an encoded 16kHz mono 16-bit PCM WAV Blob.
   */
  public stopAndGetBlob(): Blob | null {
    if (!this.isRecording) return null;
    this.isRecording = false;

    // Disconnect audio nodes
    try {
      this.processorNode?.disconnect();
      this.sourceNode?.disconnect();
      this.destNode?.disconnect();
      if (this.audioContext && this.audioContext.state !== 'closed') {
        this.audioContext.close().catch(() => {});
      }
    } catch {
      // Non-blocking cleanup
    }

    this.activeStream = null;

    if (this.recordedChunks.length === 0) return null;

    // Merge recorded buffers
    let totalLength = 0;
    for (const chunk of this.recordedChunks) {
      totalLength += chunk.length;
    }

    const merged = new Float32Array(totalLength);
    let offset = 0;
    for (const chunk of this.recordedChunks) {
      merged.set(chunk, offset);
      offset += chunk.length;
    }

    this.recordedChunks = [];
    return this.encodeWAV(merged, this.sampleRate);
  }

  /**
   * Downsamples an audio buffer from source sample rate to target sample rate using linear interpolation.
   */
  private downsampleBuffer(buffer: Float32Array, sourceRate: number, targetRate: number): Float32Array {
    if (sourceRate === targetRate) {
      return new Float32Array(buffer);
    }
    const ratio = sourceRate / targetRate;
    const newLength = Math.round(buffer.length / ratio);
    const result = new Float32Array(newLength);
    let offsetResult = 0;
    let offsetBuffer = 0;

    while (offsetResult < result.length) {
      const nextOffsetBuffer = Math.round((offsetResult + 1) * ratio);
      let accum = 0;
      let count = 0;
      for (let i = offsetBuffer; i < nextOffsetBuffer && i < buffer.length; i++) {
        accum += buffer[i];
        count++;
      }
      result[offsetResult] = count > 0 ? accum / count : 0;
      offsetResult++;
      offsetBuffer = nextOffsetBuffer;
    }
    return result;
  }

  /**
   * Encodes a float32 mono array into a standard 16-bit PCM WAV Blob.
   */
  private encodeWAV(samples: Float32Array, sampleRate: number): Blob {
    const buffer = new ArrayBuffer(44 + samples.length * 2);
    const view = new DataView(buffer);

    // RIFF chunk descriptor
    this.writeString(view, 0, 'RIFF');
    view.setUint32(4, 36 + samples.length * 2, true);
    this.writeString(view, 8, 'WAVE');

    // fmt sub-chunk
    this.writeString(view, 12, 'fmt ');
    view.setUint32(16, 16, true); // SubChunk1Size (16 for PCM)
    view.setUint16(20, 1, true); // AudioFormat (1 = PCM)
    view.setUint16(22, 1, true); // NumChannels (1 = Mono)
    view.setUint32(24, sampleRate, true); // SampleRate
    view.setUint32(28, sampleRate * 2, true); // ByteRate (SampleRate * NumChannels * BitsPerSample/8)
    view.setUint16(32, 2, true); // BlockAlign (NumChannels * BitsPerSample/8)
    view.setUint16(34, 16, true); // BitsPerSample (16 bits)

    // data sub-chunk
    this.writeString(view, 36, 'data');
    view.setUint32(40, samples.length * 2, true);

    // Write PCM 16-bit samples
    let index = 44;
    for (let i = 0; i < samples.length; i++) {
      const s = Math.max(-1, Math.min(1, samples[i]));
      view.setInt16(index, s < 0 ? s * 0x8000 : s * 0x7fff, true);
      index += 2;
    }

    return new Blob([view], { type: 'audio/wav' });
  }

  private writeString(view: DataView, offset: number, string: string): void {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  }
}
