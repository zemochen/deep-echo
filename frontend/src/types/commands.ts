/**
 * Tauri command interface definitions
 * These interfaces define the contract between frontend and Tauri middleware
 */

import type {
  TranscriptData,
  ConfigData,
  AudioDevice,
  SystemInfo,
} from './api';

// ============================================================================
// Command Interfaces
// ============================================================================

/**
 * Audio Commands
 */
export interface AudioCommands {
  /**
   * Start audio recording from specified device
   * @param deviceType - Type of device: "microphone" or "speaker"
   * @returns Success message
   * @throws Error if recording fails to start
   */
  start_recording(deviceType: string): Promise<string>;

  /**
   * Stop audio recording
   * @returns Success message
   * @throws Error if no active recording
   */
  stop_recording(): Promise<string>;

  /**
   * Get list of available audio devices
   * @returns Array of audio devices
   * @throws Error if device enumeration fails
   */
  get_audio_devices(): Promise<AudioDevice[]>;

  /**
   * Set the audio device to use for recording
   * @param deviceType - Type of device: "microphone" or "speaker"
   * @param deviceId - Device ID from get_audio_devices
   * @returns Success message
   * @throws Error if device not found or cannot be set
   */
  set_audio_device(deviceType: string, deviceId: string): Promise<string>;
}

/**
 * Transcription Commands
 */
export interface TranscriptionCommands {
  /**
   * Get the current transcript
   * @returns Transcript data
   * @throws Error if transcript not available
   */
  get_transcript(): Promise<TranscriptData>;
}

/**
 * AI Commands
 */
export interface AICommands {
  /**
   * Generate an AI response based on context
   * @param context - Context for AI response generation
   * @returns Generated response text
   * @throws Error if generation fails
   */
  generate_response(context: string): Promise<string>;

  /**
   * Switch the AI provider
   * @param provider - Provider name (e.g., "deepseek", "openai", "claude")
   * @returns Success message
   * @throws Error if provider not found or switch fails
   */
  switch_provider(provider: string): Promise<string>;
}

/**
 * Configuration Commands
 */
export interface ConfigCommands {
  /**
   * Get the current configuration
   * @returns Configuration data
   * @throws Error if config cannot be read
   */
  get_config(): Promise<ConfigData>;

  /**
   * Update the configuration
   * @param config - New configuration data
   * @returns Success message
   * @throws Error if config cannot be updated
   */
  update_config(config: ConfigData): Promise<string>;
}

/**
 * System Commands
 */
export interface SystemCommands {
  /**
   * Get system information
   * @returns System information
   * @throws Error if system info cannot be retrieved
   */
  get_system_info(): Promise<SystemInfo>;
}

/**
 * All Tauri commands
 */
export interface TauriCommands
  extends AudioCommands,
    TranscriptionCommands,
    AICommands,
    ConfigCommands,
    SystemCommands {}

// ============================================================================
// Command Parameter Types
// ============================================================================

/**
 * Parameters for start_recording command
 */
export interface StartRecordingParams {
  deviceType: string;
}

/**
 * Parameters for set_audio_device command
 */
export interface SetAudioDeviceParams {
  deviceType: string;
  deviceId: string;
}

/**
 * Parameters for generate_response command
 */
export interface GenerateResponseParams {
  context: string;
}

/**
 * Parameters for switch_provider command
 */
export interface SwitchProviderParams {
  provider: string;
}

/**
 * Parameters for update_config command
 */
export interface UpdateConfigParams {
  config: ConfigData;
}

// ============================================================================
// Type Guards
// ============================================================================

/**
 * Check if a value is a valid device type
 */
export function isDeviceType(value: string): value is 'microphone' | 'speaker' {
  return value === 'microphone' || value === 'speaker';
}

/**
 * Check if a value is a valid system state
 */
export function isSystemState(
  value: string
): value is 'idle' | 'recording' | 'processing' | 'error' {
  return ['idle', 'recording', 'processing', 'error'].includes(value);
}

/**
 * Check if a value is a valid theme
 */
export function isTheme(value: string): value is 'light' | 'dark' {
  return value === 'light' || value === 'dark';
}

// ============================================================================
// Command Name Constants
// ============================================================================

/**
 * All available Tauri command names
 */
export const TAURI_COMMANDS = {
  // Audio
  START_RECORDING: 'start_recording',
  STOP_RECORDING: 'stop_recording',
  GET_AUDIO_DEVICES: 'get_audio_devices',
  SET_AUDIO_DEVICE: 'set_audio_device',

  // Transcription
  GET_TRANSCRIPT: 'get_transcript',

  // AI
  GENERATE_RESPONSE: 'generate_response',
  SWITCH_PROVIDER: 'switch_provider',

  // Configuration
  GET_CONFIG: 'get_config',
  UPDATE_CONFIG: 'update_config',

  // System
  GET_SYSTEM_INFO: 'get_system_info',
} as const;

/**
 * Type for command names
 */
export type TauriCommandName = (typeof TAURI_COMMANDS)[keyof typeof TAURI_COMMANDS];
