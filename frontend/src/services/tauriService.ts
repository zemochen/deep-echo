/**
 * Tauri Command Service
 * Provides a typed wrapper around Tauri commands with error handling
 * Requirements: 3.1-3.8
 */

import { invoke } from '@tauri-apps/api/tauri';
import type {
  TranscriptData,
  ConfigData,
  AudioDevice,
  SystemInfo,
} from '../types/api';
import { TAURI_COMMANDS } from '../types/commands';

// ============================================================================
// Error Handling
// ============================================================================

/**
 * Custom error class for Tauri command errors
 */
export class TauriCommandError extends Error {
  public command: string;
  public originalError: unknown;

  constructor(
    command: string,
    originalError: unknown,
    message?: string
  ) {
    super(message || `Tauri command '${command}' failed`);
    this.name = 'TauriCommandError';
    this.command = command;
    this.originalError = originalError;
  }
}

/**
 * Handle errors from Tauri commands
 */
function handleCommandError(command: string, error: unknown): never {
  console.error(`[TauriService] Command '${command}' failed:`, error);
  
  if (error instanceof Error) {
    throw new TauriCommandError(command, error, error.message);
  }
  
  throw new TauriCommandError(
    command,
    error,
    `Unknown error in command '${command}'`
  );
}

// ============================================================================
// Audio Commands
// ============================================================================

/**
 * Start audio recording from specified device
 * @param deviceType - Type of device: "microphone" or "speaker"
 * @returns Success message
 * @throws TauriCommandError if recording fails to start
 */
export async function startRecording(deviceType: string): Promise<string> {
  try {
    return await invoke<string>(TAURI_COMMANDS.START_RECORDING, {
      deviceType,
    });
  } catch (error) {
    return handleCommandError(TAURI_COMMANDS.START_RECORDING, error);
  }
}

/**
 * Stop audio recording
 * @returns Success message
 * @throws TauriCommandError if no active recording
 */
export async function stopRecording(): Promise<string> {
  try {
    return await invoke<string>(TAURI_COMMANDS.STOP_RECORDING);
  } catch (error) {
    return handleCommandError(TAURI_COMMANDS.STOP_RECORDING, error);
  }
}

/**
 * Get list of available audio devices.
 * Uses Python backend via IPC for accurate system device enumeration.
 * In non-Tauri environments, falls back to browser's mediaDevices API.
 * @returns Array of audio devices
 * @throws TauriCommandError if device enumeration fails
 */
export async function getAudioDevices(): Promise<AudioDevice[]> {
  // Non-Tauri fallback: use browser mediaDevices API
  if (!(window as any).__TAURI__) {
    try {
      // Request permission with a 3s timeout so we never hang indefinitely
      const permissionTimeout = new Promise<void>((_, reject) =>
        setTimeout(() => reject(new Error('getUserMedia timeout')), 3000)
      );
      const permissionRequest = navigator.mediaDevices
        .getUserMedia({ audio: true })
        .then(s => s.getTracks().forEach(t => t.stop()));
      await Promise.race([permissionRequest, permissionTimeout]).catch(() => {
        // Permission denied or timed out — proceed without labels
      });

      const devices = await navigator.mediaDevices.enumerateDevices();
      return devices
        .filter(d => d.kind === 'audioinput' || d.kind === 'audiooutput')
        .map(d => ({
          id: d.deviceId,
          name: d.label || `${d.kind === 'audioinput' ? 'Microphone' : 'Speaker'} (${d.deviceId.slice(0, 8)})`,
          deviceType: d.kind === 'audioinput' ? 'microphone' : 'speaker',
        } as AudioDevice));
    } catch {
      return [];
    }
  }

  // Use Python backend via Tauri IPC for accurate device enumeration
  const maxAttempts = 3;
  let lastError: unknown;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await invoke<AudioDevice[]>(TAURI_COMMANDS.GET_AUDIO_DEVICES);
    } catch (error) {
      lastError = error;
      if (attempt < maxAttempts) {
        console.warn(
          `[TauriService] get_audio_devices failed on attempt ${attempt}/${maxAttempts}, retrying...`
        );
        // Exponential backoff: 1s, 2s, 4s
        await new Promise(r => setTimeout(r, 1000 * Math.pow(2, attempt - 1)));
      }
    }
  }

  return handleCommandError(TAURI_COMMANDS.GET_AUDIO_DEVICES, lastError);
}

/**
 * Set the audio device to use for recording
 * @param deviceType - Type of device: "microphone" or "speaker"
 * @param deviceId - Device ID from getAudioDevices
 * @returns Success message
 * @throws TauriCommandError if device not found or cannot be set
 */
export async function setAudioDevice(
  deviceType: string,
  deviceId: string
): Promise<string> {
  try {
    return await invoke<string>(TAURI_COMMANDS.SET_AUDIO_DEVICE, {
      deviceType,
      deviceId,
    });
  } catch (error) {
    return handleCommandError(TAURI_COMMANDS.SET_AUDIO_DEVICE, error);
  }
}

// ============================================================================
// Transcription Commands
// ============================================================================

/**
 * Get the current transcript
 * @returns Transcript data
 * @throws TauriCommandError if transcript not available
 */
export async function getTranscript(): Promise<TranscriptData> {
  try {
    return await invoke<TranscriptData>(TAURI_COMMANDS.GET_TRANSCRIPT);
  } catch (error) {
    return handleCommandError(TAURI_COMMANDS.GET_TRANSCRIPT, error);
  }
}

// ============================================================================
// AI Commands
// ============================================================================

/**
 * Generate an AI response based on context
 * @param context - Context for AI response generation
 * @returns Generated response text
 * @throws TauriCommandError if generation fails
 */
export async function generateResponse(context: string): Promise<string> {
  try {
    return await invoke<string>(TAURI_COMMANDS.GENERATE_RESPONSE, {
      context,
    });
  } catch (error) {
    return handleCommandError(TAURI_COMMANDS.GENERATE_RESPONSE, error);
  }
}

/**
 * Switch the AI provider
 * @param provider - Provider name (e.g., "deepseek", "openai", "claude")
 * @returns Success message
 * @throws TauriCommandError if provider not found or switch fails
 */
export async function switchProvider(provider: string): Promise<string> {
  try {
    return await invoke<string>(TAURI_COMMANDS.SWITCH_PROVIDER, {
      provider,
    });
  } catch (error) {
    return handleCommandError(TAURI_COMMANDS.SWITCH_PROVIDER, error);
  }
}

// ============================================================================
// Configuration Commands
// ============================================================================

/**
 * Get the current configuration
 * @returns Configuration data
 * @throws TauriCommandError if config cannot be read
 */
export async function getConfig(): Promise<ConfigData> {
  try {
    return await invoke<ConfigData>(TAURI_COMMANDS.GET_CONFIG);
  } catch (error) {
    return handleCommandError(TAURI_COMMANDS.GET_CONFIG, error);
  }
}

/**
 * Update the configuration
 * @param config - New configuration data
 * @returns Success message
 * @throws TauriCommandError if config cannot be updated
 */
export async function updateConfig(config: ConfigData): Promise<string> {
  try {
    return await invoke<string>(TAURI_COMMANDS.UPDATE_CONFIG, {
      config,
    });
  } catch (error) {
    return handleCommandError(TAURI_COMMANDS.UPDATE_CONFIG, error);
  }
}

// ============================================================================
// System Commands
// ============================================================================

/**
 * Get system information
 * @returns System information
 * @throws TauriCommandError if system info cannot be retrieved
 */
export async function getSystemInfo(): Promise<SystemInfo> {
  try {
    return await invoke<SystemInfo>(TAURI_COMMANDS.GET_SYSTEM_INFO);
  } catch (error) {
    return handleCommandError(TAURI_COMMANDS.GET_SYSTEM_INFO, error);
  }
}

// ============================================================================
// Service Object (Alternative API)
// ============================================================================

/**
 * Tauri service object with all commands
 * Provides an alternative object-oriented API
 */
export const tauriService = {
  // Audio
  audio: {
    startRecording,
    stopRecording,
    getDevices: getAudioDevices,
    setDevice: setAudioDevice,
  },
  
  // Transcription
  transcription: {
    getTranscript,
  },
  
  // AI
  ai: {
    generateResponse,
    switchProvider,
  },
  
  // Configuration
  config: {
    get: getConfig,
    update: updateConfig,
  },
  
  // System
  system: {
    getInfo: getSystemInfo,
  },
} as const;

// ============================================================================
// Exports
// ============================================================================

export default tauriService;
