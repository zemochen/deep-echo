/**
 * Tauri Command Hook
 * Generic hook for executing Tauri commands with state management and error handling
 * Requirements: 3.1-3.8
 */

import { useState, useCallback, useRef } from 'react';
import { invoke } from '@tauri-apps/api/tauri';

// ============================================================================
// Hook Options
// ============================================================================

export interface UseTauriCommandOptions<TResult, TParams = void> {
  /**
   * Command name to execute
   */
  command: string;

  /**
   * Whether to execute the command immediately on mount
   * @default false
   */
  immediate?: boolean;

  /**
   * Initial parameters for immediate execution
   */
  initialParams?: TParams;

  /**
   * Callback when command succeeds
   */
  onSuccess?: (result: TResult) => void;

  /**
   * Callback when command fails
   */
  onError?: (error: Error) => void;

  /**
   * Callback when command starts executing
   */
  onStart?: (params: TParams) => void;

  /**
   * Callback when command completes (success or error)
   */
  onComplete?: () => void;

  /**
   * Whether to retry on failure
   * @default false
   */
  retry?: boolean;

  /**
   * Number of retry attempts
   * @default 3
   */
  retryAttempts?: number;

  /**
   * Delay between retries in milliseconds
   * @default 1000
   */
  retryDelay?: number;
}

// ============================================================================
// Hook Return Type
// ============================================================================

export interface UseTauriCommandReturn<TResult, TParams = void> {
  // State
  data: TResult | null;
  error: Error | null;
  isLoading: boolean;
  isSuccess: boolean;
  isError: boolean;

  // Actions
  execute: (params?: TParams) => Promise<TResult>;
  reset: () => void;
  clearError: () => void;

  // Metadata
  executionCount: number;
  lastExecutedAt: Date | null;
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Sleep for specified milliseconds
 */
function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// ============================================================================
// Hook Implementation
// ============================================================================

/**
 * Generic hook for executing Tauri commands
 * 
 * This hook provides:
 * - Command execution with loading state
 * - Error handling and retry logic
 * - Success/error callbacks
 * - Execution tracking
 * - Type-safe command parameters and results
 * 
 * @param options - Hook configuration options
 * @returns Command state and execution function
 * 
 * @example
 * ```tsx
 * // Simple usage
 * function MyComponent() {
 *   const { data, isLoading, execute } = useTauriCommand<string>({
 *     command: 'get_system_info',
 *   });
 * 
 *   return (
 *     <button onClick={() => execute()} disabled={isLoading}>
 *       {isLoading ? 'Loading...' : 'Get Info'}
 *     </button>
 *   );
 * }
 * 
 * // With parameters and callbacks
 * function RecordingControl() {
 *   const { isLoading, execute } = useTauriCommand<string, { deviceType: string }>({
 *     command: 'start_recording',
 *     onSuccess: (result) => console.log('Recording started:', result),
 *     onError: (error) => console.error('Failed to start:', error),
 *   });
 * 
 *   return (
 *     <button
 *       onClick={() => execute({ deviceType: 'microphone' })}
 *       disabled={isLoading}
 *     >
 *       Start Recording
 *     </button>
 *   );
 * }
 * 
 * // With retry logic
 * function RobustCommand() {
 *   const { data, error, execute } = useTauriCommand<ConfigData>({
 *     command: 'get_config',
 *     retry: true,
 *     retryAttempts: 3,
 *     retryDelay: 1000,
 *   });
 * 
 *   return <div>{data ? 'Success' : error ? 'Failed' : 'Idle'}</div>;
 * }
 * ```
 */
export function useTauriCommand<TResult, TParams = void>(
  options: UseTauriCommandOptions<TResult, TParams>
): UseTauriCommandReturn<TResult, TParams> {
  const {
    command,
    immediate = false,
    initialParams,
    onSuccess,
    onError,
    onStart,
    onComplete,
    retry = false,
    retryAttempts = 3,
    retryDelay = 1000,
  } = options;

  // ============================================================================
  // State
  // ============================================================================

  const [data, setData] = useState<TResult | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [executionCount, setExecutionCount] = useState(0);
  const [lastExecutedAt, setLastExecutedAt] = useState<Date | null>(null);

  // Use ref to track if component is mounted
  const isMountedRef = useRef(true);

  // ============================================================================
  // Computed State
  // ============================================================================

  const isSuccess = data !== null && error === null;
  const isError = error !== null;

  // ============================================================================
  // Actions
  // ============================================================================

  /**
   * Execute the Tauri command
   */
  const execute = useCallback(
    async (params?: TParams): Promise<TResult> => {
      // Don't execute if component is unmounted
      if (!isMountedRef.current) {
        throw new Error('Component is unmounted');
      }

      setIsLoading(true);
      setError(null);
      onStart?.(params as TParams);

      let lastError: Error | null = null;
      let attempts = 0;
      const maxAttempts = retry ? retryAttempts : 1;

      while (attempts < maxAttempts) {
        try {
          attempts++;

          // Execute the command
          const result = await invoke<TResult>(command, params as any);

          // Only update state if component is still mounted
          if (isMountedRef.current) {
            setData(result);
            setError(null);
            setIsLoading(false);
            setExecutionCount(prev => prev + 1);
            setLastExecutedAt(new Date());

            onSuccess?.(result);
            onComplete?.();
          }

          return result;
        } catch (err) {
          lastError = err instanceof Error ? err : new Error(String(err));

          // If we have more attempts and retry is enabled, wait and try again
          if (attempts < maxAttempts) {
            await sleep(retryDelay);
            continue;
          }

          // All attempts failed, update error state
          if (isMountedRef.current) {
            setError(lastError);
            setData(null);
            setIsLoading(false);
            setExecutionCount(prev => prev + 1);
            setLastExecutedAt(new Date());

            onError?.(lastError);
            onComplete?.();
          }

          throw lastError;
        }
      }

      // This should never be reached, but TypeScript needs it
      throw lastError || new Error('Command execution failed');
    },
    [
      command,
      retry,
      retryAttempts,
      retryDelay,
      onStart,
      onSuccess,
      onError,
      onComplete,
    ]
  );

  /**
   * Reset the command state
   */
  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setIsLoading(false);
    setExecutionCount(0);
    setLastExecutedAt(null);
  }, []);

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
   * Execute immediately on mount if enabled
   */
  React.useEffect(() => {
    if (immediate) {
      execute(initialParams as TParams);
    }

    // Cleanup: mark component as unmounted
    return () => {
      isMountedRef.current = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [immediate]);

  // ============================================================================
  // Return
  // ============================================================================

  return {
    // State
    data,
    error,
    isLoading,
    isSuccess,
    isError,

    // Actions
    execute,
    reset,
    clearError,

    // Metadata
    executionCount,
    lastExecutedAt,
  };
}

// ============================================================================
// Specialized Command Hooks
// ============================================================================

/**
 * Hook for commands that don't require parameters
 */
export function useSimpleTauriCommand<TResult>(
  command: string,
  options?: Omit<UseTauriCommandOptions<TResult, void>, 'command'>
): UseTauriCommandReturn<TResult, void> {
  return useTauriCommand<TResult, void>({
    command,
    ...options,
  });
}

/**
 * Hook for commands with automatic execution on mount
 */
export function useImmediateTauriCommand<TResult, TParams = void>(
  command: string,
  params: TParams,
  options?: Omit<UseTauriCommandOptions<TResult, TParams>, 'command' | 'immediate' | 'initialParams'>
): UseTauriCommandReturn<TResult, TParams> {
  return useTauriCommand<TResult, TParams>({
    command,
    immediate: true,
    initialParams: params,
    ...options,
  });
}

/**
 * Hook for commands with retry logic
 */
export function useRetryableTauriCommand<TResult, TParams = void>(
  command: string,
  options?: Omit<UseTauriCommandOptions<TResult, TParams>, 'command' | 'retry'>
): UseTauriCommandReturn<TResult, TParams> {
  return useTauriCommand<TResult, TParams>({
    command,
    retry: true,
    ...options,
  });
}

// ============================================================================
// Exports
// ============================================================================

export default useTauriCommand;

// Import React for useEffect
import * as React from 'react';
