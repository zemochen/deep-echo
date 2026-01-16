/**
 * Response Hook
 * Manages AI response data and real-time updates from backend
 * Requirements: 1.3
 */

import { useState, useEffect, useCallback } from 'react';
import { getEventService } from '../services/eventService';
import { generateResponse } from '../services/tauriService';
import { useAppStore } from '../store/appStore';
import type { ResponseData } from '../types/api';
import type { UnlistenFn } from '../types/events';

// ============================================================================
// Hook Options
// ============================================================================

export interface UseResponseOptions {
  /**
   * Whether to automatically listen for response updates
   * @default true
   */
  autoListen?: boolean;

  /**
   * Filter responses by provider
   */
  filterByProvider?: string;

  /**
   * Maximum number of responses to keep in memory
   * @default undefined (no limit)
   */
  maxResponses?: number;

  /**
   * Callback when a new response is received
   */
  onResponseUpdate?: (response: ResponseData) => void;

  /**
   * Callback when response generation starts
   */
  onGenerationStart?: (context: string) => void;

  /**
   * Callback when response generation completes
   */
  onGenerationComplete?: (response: string) => void;

  /**
   * Callback when an error occurs
   */
  onError?: (error: Error) => void;
}

// ============================================================================
// Hook Return Type
// ============================================================================

export interface UseResponseReturn {
  // State
  responses: ResponseData[];
  latestResponse: ResponseData | null;
  isGenerating: boolean;
  isListening: boolean;
  error: string | null;

  // Actions
  generate: (context: string) => Promise<void>;
  clearResponses: () => void;
  startListening: () => Promise<void>;
  stopListening: () => void;
  clearError: () => void;

  // Computed
  responseCount: number;
  responsesByProvider: Record<string, ResponseData[]>;
}

// ============================================================================
// Hook Implementation
// ============================================================================

/**
 * Hook for managing AI response data
 * 
 * This hook provides:
 * - Real-time response updates from backend events
 * - Response generation control
 * - Response history management
 * - Filtering by provider
 * - Integration with app store
 * - Error handling
 * 
 * @param options - Hook configuration options
 * @returns Response state and control functions
 * 
 * @example
 * ```tsx
 * function ResponseViewer() {
 *   const {
 *     responses,
 *     latestResponse,
 *     isGenerating,
 *     generate,
 *   } = useResponse({
 *     onResponseUpdate: (response) => {
 *       console.log('New response:', response.text);
 *     },
 *   });
 * 
 *   return (
 *     <div>
 *       <button
 *         onClick={() => generate('Hello, AI!')}
 *         disabled={isGenerating}
 *       >
 *         Generate Response
 *       </button>
 *       {responses.map(r => (
 *         <div key={r.id}>{r.text}</div>
 *       ))}
 *     </div>
 *   );
 * }
 * ```
 */
export function useResponse(
  options: UseResponseOptions = {}
): UseResponseReturn {
  const {
    autoListen = true,
    filterByProvider,
    maxResponses,
    onResponseUpdate,
    onGenerationStart,
    onGenerationComplete,
    onError,
  } = options;

  // ============================================================================
  // State
  // ============================================================================

  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isListening, setIsListening] = useState(false);
  const [unlistenFn, setUnlistenFn] = useState<UnlistenFn | null>(null);

  // Get responses from app store
  const responses = useAppStore(state => state.responses);
  const addResponse = useAppStore(state => state.addResponse);
  const clearResponsesStore = useAppStore(state => state.clearResponses);

  // ============================================================================
  // Event Service
  // ============================================================================

  const eventService = getEventService();

  // ============================================================================
  // Computed Values
  // ============================================================================

  /**
   * Get filtered responses based on options
   */
  const filteredResponses = filterByProvider
    ? responses.filter(r => r.provider === filterByProvider)
    : responses;

  /**
   * Apply max responses limit if specified
   */
  const limitedResponses = maxResponses
    ? filteredResponses.slice(-maxResponses)
    : filteredResponses;

  /**
   * Get latest response
   */
  const latestResponse = limitedResponses.length > 0
    ? limitedResponses[limitedResponses.length - 1]
    : null;

  /**
   * Get total response count
   */
  const responseCount = limitedResponses.length;

  /**
   * Group responses by provider
   */
  const responsesByProvider = responses.reduce((acc, response) => {
    if (!acc[response.provider]) {
      acc[response.provider] = [];
    }
    acc[response.provider].push(response);
    return acc;
  }, {} as Record<string, ResponseData[]>);

  // ============================================================================
  // Actions
  // ============================================================================

  /**
   * Generate a new AI response
   */
  const generate = useCallback(
    async (context: string) => {
      try {
        setIsGenerating(true);
        setError(null);

        onGenerationStart?.(context);

        const responseText = await generateResponse(context);

        onGenerationComplete?.(responseText);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to generate response';
        setError(errorMessage);
        onError?.(err instanceof Error ? err : new Error(errorMessage));
      } finally {
        setIsGenerating(false);
      }
    },
    [onGenerationStart, onGenerationComplete, onError]
  );

  /**
   * Clear all responses
   */
  const clearResponses = useCallback(() => {
    clearResponsesStore();
  }, [clearResponsesStore]);

  /**
   * Start listening for response updates
   */
  const startListening = useCallback(async () => {
    if (isListening) {
      return;
    }

    try {
      setError(null);

      const unlisten = await eventService.onResponseGenerated((response) => {
        // Add response to store
        addResponse(response);

        // Call callback if provided
        onResponseUpdate?.(response);
      });

      setUnlistenFn(() => unlisten);
      setIsListening(true);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to start listening';
      setError(errorMessage);
      onError?.(err instanceof Error ? err : new Error(errorMessage));
    }
  }, [isListening, eventService, addResponse, onResponseUpdate, onError]);

  /**
   * Stop listening for response updates
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
   * Auto-listen on mount
   */
  useEffect(() => {
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
  }, [autoListen]);

  // ============================================================================
  // Return
  // ============================================================================

  return {
    // State
    responses: limitedResponses,
    latestResponse,
    isGenerating,
    isListening,
    error,

    // Actions
    generate,
    clearResponses,
    startListening,
    stopListening,
    clearError,

    // Computed
    responseCount,
    responsesByProvider,
  };
}

export default useResponse;
