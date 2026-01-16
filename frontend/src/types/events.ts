/**
 * Tauri event type definitions
 * These types define all events that can be emitted from backend to frontend
 */

import type {
  TranscriptData,
  ResponseData,
  SystemStatus,
  ConfigData,
  ErrorInfo,
} from './api';

// ============================================================================
// Event Names
// ============================================================================

/**
 * All available Tauri event names
 */
export const TAURI_EVENTS = {
  TRANSCRIPT_UPDATED: 'transcript-updated',
  RESPONSE_GENERATED: 'response-generated',
  STATUS_CHANGED: 'status-changed',
  ERROR_OCCURRED: 'error-occurred',
  CONFIG_UPDATED: 'config-updated',
} as const;

/**
 * Type for event names
 */
export type TauriEventName = (typeof TAURI_EVENTS)[keyof typeof TAURI_EVENTS];

// ============================================================================
// Event Payload Types
// ============================================================================

/**
 * Map of event names to their payload types
 */
export interface TauriEventPayloads {
  [TAURI_EVENTS.TRANSCRIPT_UPDATED]: TranscriptData;
  [TAURI_EVENTS.RESPONSE_GENERATED]: ResponseData;
  [TAURI_EVENTS.STATUS_CHANGED]: SystemStatus;
  [TAURI_EVENTS.ERROR_OCCURRED]: ErrorInfo;
  [TAURI_EVENTS.CONFIG_UPDATED]: ConfigData;
}

// ============================================================================
// Event Handler Types
// ============================================================================

/**
 * Generic event handler type
 */
export type EventHandler<T> = (payload: T) => void | Promise<void>;

/**
 * Event handlers for all Tauri events
 */
export interface TauriEventHandlers {
  [TAURI_EVENTS.TRANSCRIPT_UPDATED]?: EventHandler<TranscriptData>;
  [TAURI_EVENTS.RESPONSE_GENERATED]?: EventHandler<ResponseData>;
  [TAURI_EVENTS.STATUS_CHANGED]?: EventHandler<SystemStatus>;
  [TAURI_EVENTS.ERROR_OCCURRED]?: EventHandler<ErrorInfo>;
  [TAURI_EVENTS.CONFIG_UPDATED]?: EventHandler<ConfigData>;
}

// ============================================================================
// Event Listener Types
// ============================================================================

/**
 * Unlisten function returned by event listeners
 */
export type UnlistenFn = () => void;

/**
 * Event listener options
 */
export interface EventListenerOptions {
  /**
   * Whether to automatically unlisten when component unmounts
   * @default true
   */
  autoUnlisten?: boolean;

  /**
   * Whether to log events to console (for debugging)
   * @default false
   */
  debug?: boolean;
}

// ============================================================================
// Event Emitter Interface
// ============================================================================

/**
 * Interface for event emitter (used in backend)
 */
export interface EventEmitter {
  /**
   * Emit a transcript-updated event
   */
  emitTranscriptUpdated(data: TranscriptData): void;

  /**
   * Emit a response-generated event
   */
  emitResponseGenerated(data: ResponseData): void;

  /**
   * Emit a status-changed event
   */
  emitStatusChanged(status: SystemStatus): void;

  /**
   * Emit an error-occurred event
   */
  emitErrorOccurred(error: ErrorInfo): void;

  /**
   * Emit a config-updated event
   */
  emitConfigUpdated(config: ConfigData): void;
}

// ============================================================================
// Event Utilities
// ============================================================================

/**
 * Check if a string is a valid Tauri event name
 */
export function isTauriEventName(value: string): value is TauriEventName {
  return Object.values(TAURI_EVENTS).includes(value as TauriEventName);
}

/**
 * Get event name from constant
 */
export function getEventName<K extends keyof typeof TAURI_EVENTS>(
  key: K
): (typeof TAURI_EVENTS)[K] {
  return TAURI_EVENTS[key];
}

// ============================================================================
// Event Documentation
// ============================================================================

/**
 * Event documentation for reference
 */
export const EVENT_DOCS = {
  [TAURI_EVENTS.TRANSCRIPT_UPDATED]: {
    description: 'Emitted when a new transcript is available from audio transcription',
    frequency: 'High - emitted for each transcription result',
    payload: 'TranscriptData with id, timestamp, source, text, and confidence',
  },
  [TAURI_EVENTS.RESPONSE_GENERATED]: {
    description: 'Emitted when an AI response is generated',
    frequency: 'Medium - emitted when AI completes response generation',
    payload: 'ResponseData with id, timestamp, provider, text, and context',
  },
  [TAURI_EVENTS.STATUS_CHANGED]: {
    description: 'Emitted when system status changes',
    frequency: 'Low - emitted on state transitions',
    payload: 'SystemStatus with state, message, and optional details',
  },
  [TAURI_EVENTS.ERROR_OCCURRED]: {
    description: 'Emitted when an error occurs in the backend',
    frequency: 'Low - emitted on errors',
    payload: 'ErrorInfo with code, message, and optional details',
  },
  [TAURI_EVENTS.CONFIG_UPDATED]: {
    description: 'Emitted when configuration is updated',
    frequency: 'Low - emitted when config changes',
    payload: 'ConfigData with audio, ai, and ui configuration',
  },
} as const;
