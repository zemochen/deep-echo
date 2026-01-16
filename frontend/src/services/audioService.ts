/**
 * Web Audio API Service
 * Provides microphone access and audio visualization
 * Requirements: 5.1-5.6
 */

import type { AudioVisualizationData } from '../types/audio';

// ============================================================================
// Error Handling
// ============================================================================

/**
 * Custom error class for audio service errors
 */
export class AudioServiceError extends Error {
  public code: string;
  public originalError?: unknown;

  constructor(
    code: string,
    message: string,
    originalError?: unknown
  ) {
    super(message);
    this.name = 'AudioServiceError';
    this.code = code;
    this.originalError = originalError;
  }
}

// ============================================================================
// Audio Service Class
// ============================================================================

/**
 * Audio service for microphone access and visualization
 */
export class AudioService {
  private audioContext: AudioContext | null = null;
  private mediaStream: MediaStream | null = null;
  private analyser: AnalyserNode | null = null;
  private microphone: MediaStreamAudioSourceNode | null = null;
  private animationFrameId: number | null = null;

  /**
   * Check if the browser supports Web Audio API
   */
  public isSupported(): boolean {
    return !!(
      window.AudioContext ||
      (window as any).webkitAudioContext
    );
  }

  /**
   * Request microphone access and initialize audio context
   * @param deviceId - Optional device ID to use specific microphone
   * @returns Promise that resolves when microphone is ready
   * @throws AudioServiceError if microphone access fails
   */
  public async requestMicrophoneAccess(deviceId?: string): Promise<void> {
    if (!this.isSupported()) {
      throw new AudioServiceError(
        'NOT_SUPPORTED',
        'Web Audio API is not supported in this browser'
      );
    }

    try {
      // Request microphone permission
      const constraints: MediaStreamConstraints = {
        audio: deviceId
          ? { deviceId: { exact: deviceId } }
          : true,
        video: false,
      };

      this.mediaStream = await navigator.mediaDevices.getUserMedia(constraints);

      // Create audio context
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      this.audioContext = new AudioContextClass();

      // Create analyser node for visualization
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 2048;
      this.analyser.smoothingTimeConstant = 0.8;

      // Connect microphone to analyser
      this.microphone = this.audioContext.createMediaStreamSource(this.mediaStream);
      this.microphone.connect(this.analyser);

      console.log('[AudioService] Microphone access granted');
    } catch (error) {
      console.error('[AudioService] Failed to access microphone:', error);
      
      if (error instanceof Error) {
        if (error.name === 'NotAllowedError') {
          throw new AudioServiceError(
            'PERMISSION_DENIED',
            'Microphone access was denied by the user',
            error
          );
        } else if (error.name === 'NotFoundError') {
          throw new AudioServiceError(
            'DEVICE_NOT_FOUND',
            'No microphone device found',
            error
          );
        }
      }
      
      throw new AudioServiceError(
        'UNKNOWN_ERROR',
        'Failed to access microphone',
        error
      );
    }
  }

  /**
   * Stop microphone access and cleanup resources
   */
  public stopMicrophone(): void {
    // Stop animation frame
    if (this.animationFrameId !== null) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }

    // Disconnect audio nodes
    if (this.microphone) {
      this.microphone.disconnect();
      this.microphone = null;
    }

    // Stop media stream tracks
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(track => track.stop());
      this.mediaStream = null;
    }

    // Close audio context
    if (this.audioContext) {
      this.audioContext.close();
      this.audioContext = null;
    }

    this.analyser = null;

    console.log('[AudioService] Microphone stopped');
  }

  /**
   * Get current audio visualization data
   * @returns Audio visualization data or null if not recording
   */
  public getVisualizationData(): AudioVisualizationData | null {
    if (!this.analyser) {
      return null;
    }

    const bufferLength = this.analyser.frequencyBinCount;
    const frequencyData = new Uint8Array(bufferLength);
    const timeDomainData = new Uint8Array(bufferLength);

    this.analyser.getByteFrequencyData(frequencyData);
    this.analyser.getByteTimeDomainData(timeDomainData);

    // Calculate volume (RMS of time domain data)
    let sum = 0;
    for (let i = 0; i < timeDomainData.length; i++) {
      const normalized = (timeDomainData[i] - 128) / 128;
      sum += normalized * normalized;
    }
    const volume = Math.sqrt(sum / timeDomainData.length);

    return {
      frequencyData,
      timeDomainData,
      volume,
    };
  }

  /**
   * Start continuous visualization updates
   * @param callback - Function to call with visualization data on each frame
   * @returns Function to stop the visualization updates
   */
  public startVisualization(
    callback: (data: AudioVisualizationData) => void
  ): () => void {
    if (!this.analyser) {
      throw new AudioServiceError(
        'NOT_INITIALIZED',
        'Audio service not initialized. Call requestMicrophoneAccess first.'
      );
    }

    const updateVisualization = () => {
      const data = this.getVisualizationData();
      if (data) {
        callback(data);
      }
      this.animationFrameId = requestAnimationFrame(updateVisualization);
    };

    updateVisualization();

    // Return stop function
    return () => {
      if (this.animationFrameId !== null) {
        cancelAnimationFrame(this.animationFrameId);
        this.animationFrameId = null;
      }
    };
  }

  /**
   * Get list of available audio input devices
   * @returns Promise that resolves to array of audio input devices
   * @throws AudioServiceError if device enumeration fails
   */
  public async getAudioInputDevices(): Promise<MediaDeviceInfo[]> {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      return devices.filter(device => device.kind === 'audioinput');
    } catch (error) {
      console.error('[AudioService] Failed to enumerate devices:', error);
      throw new AudioServiceError(
        'ENUMERATION_FAILED',
        'Failed to enumerate audio devices',
        error
      );
    }
  }

  /**
   * Check if microphone is currently active
   */
  public isActive(): boolean {
    return this.mediaStream !== null && this.audioContext !== null;
  }

  /**
   * Get the current audio context state
   */
  public getAudioContextState(): AudioContextState | null {
    return this.audioContext?.state || null;
  }

  /**
   * Resume audio context if suspended (required for some browsers)
   */
  public async resumeAudioContext(): Promise<void> {
    if (this.audioContext && this.audioContext.state === 'suspended') {
      await this.audioContext.resume();
      console.log('[AudioService] Audio context resumed');
    }
  }
}

// ============================================================================
// Singleton Instance
// ============================================================================

/**
 * Singleton instance of AudioService
 */
let audioServiceInstance: AudioService | null = null;

/**
 * Get the singleton AudioService instance
 */
export function getAudioService(): AudioService {
  if (!audioServiceInstance) {
    audioServiceInstance = new AudioService();
  }
  return audioServiceInstance;
}

/**
 * Reset the singleton instance (useful for testing)
 */
export function resetAudioService(): void {
  if (audioServiceInstance) {
    audioServiceInstance.stopMicrophone();
    audioServiceInstance = null;
  }
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Check if browser supports getUserMedia
 */
export function supportsGetUserMedia(): boolean {
  return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
}

/**
 * Check if browser supports Web Audio API
 */
export function supportsWebAudio(): boolean {
  return !!(window.AudioContext || (window as any).webkitAudioContext);
}

/**
 * Check if all required audio features are supported
 */
export function supportsAudioFeatures(): boolean {
  return supportsGetUserMedia() && supportsWebAudio();
}

// ============================================================================
// Exports
// ============================================================================

export default getAudioService;
