/**
 * Audio-related type definitions
 */

export interface AudioRecordingState {
  isRecording: boolean;
  deviceType: 'microphone' | 'speaker' | null;
  error: string | null;
}

export interface AudioVisualizationData {
  frequencyData: Uint8Array;
  timeDomainData: Uint8Array;
  volume: number;
}
