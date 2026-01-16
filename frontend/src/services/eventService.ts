/**
 * Event Service
 * Provides event listening and subscription mechanism for Tauri events
 * Requirements: 7.1-7.6
 */

import { listen, type UnlistenFn as TauriUnlistenFn } from '@tauri-apps/api/event';
import {
  TAURI_EVENTS,
  type TauriEventName,
  type TauriEventPayloads,
  type EventHandler,
  type UnlistenFn,
  type EventListenerOptions,
} from '../types/events';
import type {
  TranscriptData,
  ResponseData,
  SystemStatus,
  ConfigData,
  ErrorInfo,
} from '../types/api';

// ============================================================================
// Error Handling
// ============================================================================

/**
 * Custom error class for event service errors
 */
export class EventServiceError extends Error {
  public code: string;
  public originalError?: unknown;

  constructor(
    code: string,
    message: string,
    originalError?: unknown
  ) {
    super(message);
    this.name = 'EventServiceError';
    this.code = code;
    this.originalError = originalError;
  }
}

// ============================================================================
// Event Service Class
// ============================================================================

/**
 * Event service for managing Tauri event subscriptions
 */
export class EventService {
  private listeners: Map<string, TauriUnlistenFn[]> = new Map();
  private debug: boolean = false;

  /**
   * Enable or disable debug logging
   */
  public setDebug(enabled: boolean): void {
    this.debug = enabled;
  }

  /**
   * Log debug message if debug is enabled
   */
  private log(message: string, ...args: any[]): void {
    if (this.debug) {
      console.log(`[EventService] ${message}`, ...args);
    }
  }

  /**
   * Listen to a Tauri event
   * @param eventName - Name of the event to listen to
   * @param handler - Handler function to call when event is received
   * @param options - Optional listener options
   * @returns Function to unlisten from the event
   */
  public async listen<K extends TauriEventName>(
    eventName: K,
    handler: EventHandler<TauriEventPayloads[K]>,
    options: EventListenerOptions = {}
  ): Promise<UnlistenFn> {
    const { debug = false } = options;

    try {
      this.log(`Listening to event: ${eventName}`);

      const unlisten = await listen<TauriEventPayloads[K]>(
        eventName,
        (event) => {
          if (debug || this.debug) {
            this.log(`Event received: ${eventName}`, event.payload);
          }

          try {
            handler(event.payload);
          } catch (error) {
            console.error(
              `[EventService] Error in handler for event '${eventName}':`,
              error
            );
          }
        }
      );

      // Store the unlisten function
      if (!this.listeners.has(eventName)) {
        this.listeners.set(eventName, []);
      }
      this.listeners.get(eventName)!.push(unlisten);

      // Return wrapped unlisten function
      return () => {
        unlisten();
        this.removeListener(eventName, unlisten);
      };
    } catch (error) {
      console.error(`[EventService] Failed to listen to event '${eventName}':`, error);
      throw new EventServiceError(
        'LISTEN_FAILED',
        `Failed to listen to event '${eventName}'`,
        error
      );
    }
  }

  /**
   * Remove a listener from the internal tracking
   */
  private removeListener(eventName: string, unlisten: TauriUnlistenFn): void {
    const listeners = this.listeners.get(eventName);
    if (listeners) {
      const index = listeners.indexOf(unlisten);
      if (index !== -1) {
        listeners.splice(index, 1);
      }
      if (listeners.length === 0) {
        this.listeners.delete(eventName);
      }
    }
  }

  /**
   * Listen to transcript-updated event
   */
  public async onTranscriptUpdated(
    handler: EventHandler<TranscriptData>,
    options?: EventListenerOptions
  ): Promise<UnlistenFn> {
    return this.listen(TAURI_EVENTS.TRANSCRIPT_UPDATED, handler, options);
  }

  /**
   * Listen to response-generated event
   */
  public async onResponseGenerated(
    handler: EventHandler<ResponseData>,
    options?: EventListenerOptions
  ): Promise<UnlistenFn> {
    return this.listen(TAURI_EVENTS.RESPONSE_GENERATED, handler, options);
  }

  /**
   * Listen to status-changed event
   */
  public async onStatusChanged(
    handler: EventHandler<SystemStatus>,
    options?: EventListenerOptions
  ): Promise<UnlistenFn> {
    return this.listen(TAURI_EVENTS.STATUS_CHANGED, handler, options);
  }

  /**
   * Listen to error-occurred event
   */
  public async onErrorOccurred(
    handler: EventHandler<ErrorInfo>,
    options?: EventListenerOptions
  ): Promise<UnlistenFn> {
    return this.listen(TAURI_EVENTS.ERROR_OCCURRED, handler, options);
  }

  /**
   * Listen to config-updated event
   */
  public async onConfigUpdated(
    handler: EventHandler<ConfigData>,
    options?: EventListenerOptions
  ): Promise<UnlistenFn> {
    return this.listen(TAURI_EVENTS.CONFIG_UPDATED, handler, options);
  }

  /**
   * Listen to multiple events at once
   * @param handlers - Map of event names to handlers
   * @param options - Optional listener options
   * @returns Function to unlisten from all events
   */
  public async listenToMultiple(
    handlers: Partial<{
      [K in TauriEventName]: EventHandler<TauriEventPayloads[K]>;
    }>,
    options?: EventListenerOptions
  ): Promise<UnlistenFn> {
    const unlistenFns: UnlistenFn[] = [];

    for (const [eventName, handler] of Object.entries(handlers)) {
      if (handler) {
        const unlisten = await this.listen(
          eventName as TauriEventName,
          handler as any,
          options
        );
        unlistenFns.push(unlisten);
      }
    }

    // Return function that unlistens from all events
    return () => {
      unlistenFns.forEach(unlisten => unlisten());
    };
  }

  /**
   * Unlisten from a specific event
   * @param eventName - Name of the event to unlisten from
   */
  public unlistenFromEvent(eventName: TauriEventName): void {
    const listeners = this.listeners.get(eventName);
    if (listeners) {
      listeners.forEach(unlisten => unlisten());
      this.listeners.delete(eventName);
      this.log(`Unlistened from event: ${eventName}`);
    }
  }

  /**
   * Unlisten from all events
   */
  public unlistenFromAll(): void {
    this.log('Unlistening from all events');
    this.listeners.forEach((listeners) => {
      listeners.forEach(unlisten => unlisten());
    });
    this.listeners.clear();
  }

  /**
   * Get the number of active listeners for an event
   */
  public getListenerCount(eventName: TauriEventName): number {
    return this.listeners.get(eventName)?.length || 0;
  }

  /**
   * Get the total number of active listeners
   */
  public getTotalListenerCount(): number {
    let count = 0;
    this.listeners.forEach(listeners => {
      count += listeners.length;
    });
    return count;
  }

  /**
   * Check if there are any active listeners for an event
   */
  public hasListeners(eventName: TauriEventName): boolean {
    return this.getListenerCount(eventName) > 0;
  }

  /**
   * Get all event names that have active listeners
   */
  public getActiveEvents(): TauriEventName[] {
    return Array.from(this.listeners.keys()) as TauriEventName[];
  }
}

// ============================================================================
// Singleton Instance
// ============================================================================

/**
 * Singleton instance of EventService
 */
let eventServiceInstance: EventService | null = null;

/**
 * Get the singleton EventService instance
 */
export function getEventService(): EventService {
  if (!eventServiceInstance) {
    eventServiceInstance = new EventService();
  }
  return eventServiceInstance;
}

/**
 * Reset the singleton instance (useful for testing)
 */
export function resetEventService(): void {
  if (eventServiceInstance) {
    eventServiceInstance.unlistenFromAll();
    eventServiceInstance = null;
  }
}

// ============================================================================
// Convenience Functions
// ============================================================================

/**
 * Listen to transcript-updated event (convenience function)
 */
export async function onTranscriptUpdated(
  handler: EventHandler<TranscriptData>,
  options?: EventListenerOptions
): Promise<UnlistenFn> {
  return getEventService().onTranscriptUpdated(handler, options);
}

/**
 * Listen to response-generated event (convenience function)
 */
export async function onResponseGenerated(
  handler: EventHandler<ResponseData>,
  options?: EventListenerOptions
): Promise<UnlistenFn> {
  return getEventService().onResponseGenerated(handler, options);
}

/**
 * Listen to status-changed event (convenience function)
 */
export async function onStatusChanged(
  handler: EventHandler<SystemStatus>,
  options?: EventListenerOptions
): Promise<UnlistenFn> {
  return getEventService().onStatusChanged(handler, options);
}

/**
 * Listen to error-occurred event (convenience function)
 */
export async function onErrorOccurred(
  handler: EventHandler<ErrorInfo>,
  options?: EventListenerOptions
): Promise<UnlistenFn> {
  return getEventService().onErrorOccurred(handler, options);
}

/**
 * Listen to config-updated event (convenience function)
 */
export async function onConfigUpdated(
  handler: EventHandler<ConfigData>,
  options?: EventListenerOptions
): Promise<UnlistenFn> {
  return getEventService().onConfigUpdated(handler, options);
}

// ============================================================================
// Exports
// ============================================================================

export default getEventService;
