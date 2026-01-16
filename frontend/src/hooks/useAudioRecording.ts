/**
 * Audio Recording Hook
 * Manages audio recording state and provides recording controls
 * Requirements: 5.1-5.6
 */

import { useState, useCallback, useEffect } from 'react';
import { startRecording, stopRecording, getAudioDevices, setAudioDevice } from '../services/tauriService';
import { getAudioService } from '../services/audioService';
import type { AudioDevice } from '../types/api';
import type { AudioRecordingState, AudioVisualizationData } from '../types/audio';

// ============================================================================
// Hook Options
// ============================================================================

export interface UseAudioRecordingOptions {
  /**
   * Whether to automatically request microphone access on mount
   * @default false
   */
  autoRequestAccess?: boolean;

  /**
   * Whether to enable audio visualization
   * @default false
   */
  enableVisualization?: boolean;

  /**
   * Callback when recording starts
   */
  onRecordingStart?: (deviceType: 'microphone' | 'speaker') => void;

  /**
   * Callback when recording stops
   */
  onRecordingStop?: () => void;

  /**
   * Callback when an error occurs
   */
  onError?: (error: Error) => void;
}

// ============================================================================
// Hook Return Type
// ============================================================================

export interface UseAudioRecordingReturn {
  // State
  isRecording: boolean;
  deviceType: 'microphone' | 'speaker' | null;
  error: string | null;
  devices: AudioDevice[];
  isLoadingDevices: boolean;
  visualizationData: AudioVisualizationData | null;
  isMicrophoneActive: boolean;

  // Actions
  startRecording: (deviceType: 'microphone' | 'speaker') => Promise<void>;
  stopRecording: () => Promise<void>;
  loadDevices: () => Promise<void>;
  selectDevice: (deviceType: 'microphone' | 'speaker', deviceId: string) => Promise<void>;
  requestMicrophoneAccess: (deviceId?: string) => Promise<void>;
  stopMicrophone: () => void;
  clearError: () => void;
}

// ============================================================================
// Hook Implementation
// ============================================================================

/**
 * Hook for managing audio recording
 * 
 * This hook provides:
 * - Recording state management
 * - Device enumeration and selection
 * - Web Audio API integration for microphone access
 * - Audio visualization data
 * - Error handling
 * 
 * @param options - Hook configuration options
 * @returns Audio recording state and control functions
 * 
 * @example
 * ```tsx
 * function AudioRecorder() {
 *   const {
 *     isRecording,
 *     startRecording,
 *     stopRecording,
 *     devices,
 *     loadDevices,
 *   } = useAudioRecording({
 *     onRecordingStart: (type) => console.log(`Recording started: ${type}`),
 *     onError: (error) => console.error(error),
 *   });
 * 
 *   return (
 *     <div>
 *       <button onClick={() => startRecording('microphone')}>
 *         {isRecording ? 'Stop' : 'Start'} Recording
 *       </button>
 *     </div>
 *   );
 * }
 * ```
 */
export function useAudioRecording(
  options: UseAudioRecordingOptions = {}
): UseAudioRecordingReturn {
  const {
    autoRequestAccess = false,
    enableVisualization = false,
    onRecordingStart,
    onRecordingStop,
    onError,
  } = options;

  // ============================================================================
  // State
  // ============================================================================

  const [state, setState] = useState<AudioRecordingState>({
    isRecording: false,
    deviceType: null,
    error: null,
  });

  const [devices, setDevices] = useState<AudioDevice[]>([]);
  const [isLoadingDevices, setIsLoadingDevices] = useState(false);
  const [visualizationData, setVisualizationData] = useState<AudioVisualizationData | null>(null);
  const [isMicrophoneActive, setIsMicrophoneActive] = useState(false);

  // ============================================================================
  // Audio Service
  // ============================================================================

  const audioService = getAudioService();

  // ============================================================================
  // Actions
  // ============================================================================

  /**
   * Start recording from specified device
   */
  const handleStartRecording = useCallback(
    async (deviceType: 'microphone' | 'speaker') => {
      try {
        setState(prev => ({ ...prev, error: null }));

        // Call Tauri command to start backend recording
        await startRecording(deviceType);

        setState({
          isRecording: true,
          deviceType,
          error: null,
        });

        onRecordingStart?.(deviceType);
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to start recording';
        setState(prev => ({
          ...prev,
          error: errorMessage,
        }));
        onError?.(error instanceof Error ? error : new Error(errorMessage));
      }
    },
    [onRecordingStart, onError]
  );

  /**
   * Stop recording
   */
  const handleStopRecording = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, error: null }));

      // Call Tauri command to stop backend recording
      await stopRecording();

      setState({
        isRecording: false,
        deviceType: null,
        error: null,
      });

      onRecordingStop?.();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to stop recording';
      setState(prev => ({
        ...prev,
        error: errorMessage,
      }));
      onError?.(error instanceof Error ? error : new Error(errorMessage));
    }
  }, [onRecordingStop, onError]);

  /**
   * Load available audio devices
   */
  const loadDevices = useCallback(async () => {
    try {
      setIsLoadingDevices(true);
      setState(prev => ({ ...prev, error: null }));

      const deviceList = await getAudioDevices();
      setDevices(deviceList);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load devices';
      setState(prev => ({
        ...prev,
        error: errorMessage,
      }));
      onError?.(error instanceof Error ? error : new Error(errorMessage));
    } finally {
      setIsLoadingDevices(false);
    }
  }, [onError]);

  /**
   * Select a specific audio device
   */
  const selectDevice = useCallback(
    async (deviceType: 'microphone' | 'speaker', deviceId: string) => {
      try {
        setState(prev => ({ ...prev, error: null }));

        await setAudioDevice(deviceType, deviceId);
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to set device';
        setState(prev => ({
          ...prev,
          error: errorMessage,
        }));
        onError?.(error instanceof Error ? error : new Error(errorMessage));
      }
    },
    [onError]
  );

  /**
   * Request microphone access for Web Audio API
   */
  const requestMicrophoneAccess = useCallback(
    async (deviceId?: string) => {
      try {
        setState(prev => ({ ...prev, error: null }));

        await audioService.requestMicrophoneAccess(deviceId);
        setIsMicrophoneActive(true);

        // Start visualization if enabled
        if (enableVisualization) {
          audioService.startVisualization((data) => {
            setVisualizationData(data);
          });
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to access microphone';
        setState(prev => ({
          ...prev,
          error: errorMessage,
        }));
        setIsMicrophoneActive(false);
        onError?.(error instanceof Error ? error : new Error(errorMessage));
      }
    },
    [audioService, enableVisualization, onError]
  );

  /**
   * Stop microphone access
   */
  const stopMicrophone = useCallback(() => {
    audioService.stopMicrophone();
    setIsMicrophoneActive(false);
    setVisualizationData(null);
  }, [audioService]);

  /**
   * Clear error state
   */
  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  // ============================================================================
  // Effects
  // ============================================================================

  /**
   * Auto-request microphone access on mount if enabled
   */
  useEffect(() => {
    if (autoRequestAccess) {
      requestMicrophoneAccess();
    }

    // Cleanup on unmount
    return () => {
      if (isMicrophoneActive) {
        stopMicrophone();
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoRequestAccess]);

  // ============================================================================
  // Return
  // ============================================================================

  return {
    // State
    isRecording: state.isRecording,
    deviceType: state.deviceType,
    error: state.error,
    devices,
    isLoadingDevices,
    visualizationData,
    isMicrophoneActive,

    // Actions
    startRecording: handleStartRecording,
    stopRecording: handleStopRecording,
    loadDevices,
    selectDevice,
    requestMicrophoneAccess,
    stopMicrophone,
    clearError,
  };
}

export default useAudioRecording;
