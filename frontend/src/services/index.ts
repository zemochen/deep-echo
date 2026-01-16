/**
 * Services index
 * Exports all service modules for convenient importing
 */

// Tauri Command Service
export {
  default as tauriService,
  TauriCommandError,
  startRecording,
  stopRecording,
  getAudioDevices,
  setAudioDevice,
  getTranscript,
  generateResponse,
  switchProvider,
  getConfig,
  updateConfig,
  getSystemInfo,
} from './tauriService';

// Audio Service
export {
  default as getAudioService,
  AudioService,
  AudioServiceError,
  resetAudioService,
  supportsGetUserMedia,
  supportsWebAudio,
  supportsAudioFeatures,
} from './audioService';

// Event Service
export {
  default as getEventService,
  EventService,
  EventServiceError,
  resetEventService,
  onTranscriptUpdated,
  onResponseGenerated,
  onStatusChanged,
  onErrorOccurred,
  onConfigUpdated,
} from './eventService';

// System Resource Services
export {
  FileService,
  SystemService,
  SystemUtils,
} from './systemService';

// Python Service Management
export { default as PythonServiceAPI } from './pythonService';
