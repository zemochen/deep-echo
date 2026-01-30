/**
 * Transcript Hook
 * Manages transcript data and real-time updates from backend
 * Requirements: 1.2
 */

import { useState, useEffect, useCallback } from 'react';
import { getEventService } from '../services/eventService';
import { getTranscript } from '../services/tauriService';
import { useAppStore } from '../store/appStore';
import type { TranscriptData } from '../types/api';
import type { UnlistenFn } from '../types/events';

// ============================================================================
// Hook Options
// ============================================================================

export interface UseTranscriptOptions {
  /**
   * Whether to automatically load initial transcript on mount
   * @default true
   */
  autoLoad?: boolean;

  /**
   * Whether to automatically listen for transcript updates
   * @default true
   */
  autoListen?: boolean;

  /**
   * Filter transcripts by source
   */
  filterBySource?: 'microphone' | 'speaker';

  /**
   * Maximum number of transcripts to keep in memory
   * @default undefined (no limit)
   */
  maxTranscripts?: number;

  /**
   * Callback when a new transcript is received
   */
  onTranscriptUpdate?: (transcript: TranscriptData) => void;

  /**
   * Callback when an error occurs
   */
  onError?: (error: Error) => void;
}

// ============================================================================
// Hook Return Type
// ============================================================================

export interface UseTranscriptReturn {
  // State
  transcripts: TranscriptData[];
  latestTranscript: TranscriptData | null;
  isLoading: boolean;
  error: string | null;
  isListening: boolean;

  // Actions
  loadTranscript: () => Promise<void>;
  clearTranscripts: () => void;
  startListening: () => Promise<void>;
  stopListening: () => void;
  clearError: () => void;

  // Computed
  microphoneTranscripts: TranscriptData[];
  speakerTranscripts: TranscriptData[];
  transcriptCount: number;
}

// ============================================================================
// Hook Implementation
// ============================================================================

/**
 * Hook for managing transcript data
 * 
 * This hook provides:
 * - Real-time transcript updates from backend events
 * - Transcript history management
 * - Filtering by source (microphone/speaker)
 * - Integration with app store
 * - Error handling
 * 
 * @param options - Hook configuration options
 * @returns Transcript state and control functions
 * 
 * @example
 * ```tsx
 * function TranscriptViewer() {
 *   const {
 *     transcripts,
 *     latestTranscript,
 *     isLoading,
 *   } = useTranscript({
 *     filterBySource: 'microphone',
 *     onTranscriptUpdate: (transcript) => {
 *       console.log('New transcript:', transcript.text);
 *     },
 *   });
 * 
 *   return (
 *     <div>
 *       {transcripts.map(t => (
 *         <div key={t.id}>{t.text}</div>
 *       ))}
 *     </div>
 *   );
 * }
 * ```
 */
export function useTranscript(
  options: UseTranscriptOptions = {}
): UseTranscriptReturn {
  const {
    autoLoad = true,
    autoListen = true,
    filterBySource,
    maxTranscripts,
    onTranscriptUpdate,
    onError,
  } = options;

  // ============================================================================
  // State
  // ============================================================================

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isListening, setIsListening] = useState(false);
  const [unlistenFn, setUnlistenFn] = useState<UnlistenFn | null>(null);

  // Get transcripts from app store
  const transcripts = useAppStore(state => state.transcripts);
  const addTranscript = useAppStore(state => state.addTranscript);
  const clearTranscriptsStore = useAppStore(state => state.clearTranscripts);

  // ============================================================================
  // Event Service
  // ============================================================================

  const eventService = getEventService();

  // ============================================================================
  // Computed Values
  // ============================================================================

  /**
   * Get filtered transcripts based on options
   */
  const filteredTranscripts = filterBySource
    ? transcripts.filter(t => t.source === filterBySource)
    : transcripts;

  /**
   * Apply max transcripts limit if specified
   */
  const limitedTranscripts = maxTranscripts
    ? filteredTranscripts.slice(-maxTranscripts)
    : filteredTranscripts;

  /**
   * Get latest transcript
   */
  const latestTranscript = limitedTranscripts.length > 0
    ? limitedTranscripts[limitedTranscripts.length - 1]
    : null;

  /**
   * Get microphone transcripts
   */
  const microphoneTranscripts = transcripts.filter(t => t.source === 'microphone');

  /**
   * Get speaker transcripts
   */
  const speakerTranscripts = transcripts.filter(t => t.source === 'speaker');

  /**
   * Get total transcript count
   */
  const transcriptCount = limitedTranscripts.length;

  // ============================================================================
  // Actions
  // ============================================================================

  /**
   * Load current transcript from backend
   */
  const loadTranscript = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const transcript = await getTranscript();

      // 跳过空 transcript（避免 React Strict Mode 导致的重复添加）
      const isEmptyTranscript = transcript.text.trim() === "" && transcript.confidence === 0.0;
      if (isEmptyTranscript) {
        console.log('ℹ️ Skipping empty transcript from backend');
        return;
      }

      // 检查是否已经存在相同的 transcript
      const exists = transcripts.some(t => t.id === transcript.id);
      if (!exists) {
        addTranscript(transcript);
      } else {
        console.log('ℹ️ Transcript already exists, skipping duplicate load');
      }
    } catch (err) {
      // 如果 backend 未启动，静默失败而不是抛出错误
      const errorMessage = err instanceof Error ? err.message : 'Failed to load transcript';

      // 只在非 "command not found" 或类似错误时才记录
      if (!errorMessage.includes('command not found') &&
          !errorMessage.includes('not available')) {
        setError(errorMessage);
        onError?.(err instanceof Error ? err : new Error(errorMessage));
      } else {
        // Backend 可能还没启动，等待事件更新
        console.log('ℹ️ Backend not ready, waiting for transcript events...');
      }
    } finally {
      setIsLoading(false);
    }
  }, [transcripts, addTranscript, onError]);

  /**
   * Clear all transcripts
   */
  const clearTranscripts = useCallback(() => {
    clearTranscriptsStore();
  }, [clearTranscriptsStore]);

  /**
   * Start listening for transcript updates
   */
  const startListening = useCallback(async () => {
    if (isListening) {
      return;
    }

    try {
      setError(null);

      const unlisten = await eventService.onTranscriptUpdated((transcript) => {
        // Add transcript to store
        addTranscript(transcript);

        // Call callback if provided
        onTranscriptUpdate?.(transcript);
      });

      setUnlistenFn(() => unlisten);
      setIsListening(true);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to start listening';
      setError(errorMessage);
      onError?.(err instanceof Error ? err : new Error(errorMessage));
    }
  }, [isListening, eventService, addTranscript, onTranscriptUpdate, onError]);

  /**
   * Stop listening for transcript updates
   */
  const stopListening = useCallback(() => {
    if (unlistenFn) {
      unlistenFn();
      setUnlistenFn(null);
      setIsListening(false);
    }
  }, [unlistenFn]);

  /**
   * Clear error state
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // ============================================================================
  // Effects
  // ============================================================================

  /**
   * Auto-load and auto-listen on mount
   */
  useEffect(() => {
    if (autoLoad) {
      loadTranscript();
    }

    if (autoListen) {
      startListening();
    }

    // Cleanup on unmount
    return () => {
      if (isListening) {
        stopListening();
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoLoad, autoListen]);

  // ============================================================================
  // Return
  // ============================================================================

  return {
    // State
    transcripts: limitedTranscripts,
    latestTranscript,
    isLoading,
    error,
    isListening,

    // Actions
    loadTranscript,
    clearTranscripts,
    startListening,
    stopListening,
    clearError,

    // Computed
    microphoneTranscripts,
    speakerTranscripts,
    transcriptCount,
  };
}

export default useTranscript;
