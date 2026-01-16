/**
 * API type definitions for Tauri commands and responses
 * These types must match the Rust models in src-tauri/src/models/
 */

// ============================================================================
// Data Models
// ============================================================================

/**
 * Transcript data from audio transcription
 */
export interface TranscriptData {
  id: string;
  timestamp: number;
  source: 'microphone' | 'speaker';
  text: string;
  confidence: number;
}

/**
 * AI-generated response data
 */
export interface ResponseData {
  id: string;
  timestamp: number;
  provider: string;
  text: string;
  context: string;
}

/**
 * System status information
 */
export interface SystemStatus {
  state: 'idle' | 'recording' | 'processing' | 'error';
  message: string;
  details?: Record<string, any>;
}

/**
 * Application configuration
 */
export interface ConfigData {
  audio: AudioConfig;
  ai: AIConfig;
  ui: UIConfig;
}

export interface AudioConfig {
  recordTimeout: number;
  energyThreshold: number;
  device?: string;
}

export interface AIConfig {
  provider: string;
  model: string;
  apiKey: string;
}

export interface UIConfig {
  updateInterval: number;
  theme: 'light' | 'dark';
}

/**
 * Audio device information
 */
export interface AudioDevice {
  id: string;
  name: string;
  deviceType: string; // "microphone" or "speaker"
}

/**
 * System information
 */
export interface SystemInfo {
  platform: string;
  version: string;
  arch: string;
}

/**
 * Error information
 */
export interface ErrorInfo {
  code: string;
  message: string;
  details?: any;
}

// ============================================================================
// Command Request Types
// ============================================================================

/**
 * Request to start audio recording
 */
export interface StartRecordingRequest {
  deviceType: string; // "microphone" or "speaker"
}

/**
 * Request to set audio device
 */
export interface SetAudioDeviceRequest {
  deviceType: string;
  deviceId: string;
}

/**
 * Request to generate AI response
 */
export interface GenerateResponseRequest {
  context: string;
}

/**
 * Request to switch AI provider
 */
export interface SwitchProviderRequest {
  provider: string;
}

/**
 * Request to update configuration
 */
export interface UpdateConfigRequest {
  config: ConfigData;
}

// Event types are now defined in events.ts to avoid duplication

// ============================================================================
// Command Response Types
// ============================================================================

/**
 * Generic success response
 */
export interface SuccessResponse {
  message: string;
}

/**
 * Generic error response
 */
export interface ErrorResponse {
  error: ErrorInfo;
}
