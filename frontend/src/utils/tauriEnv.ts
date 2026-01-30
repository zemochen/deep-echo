/**
 * Tauri Environment Detection Utility
 *
 * This module provides utilities to detect if the code is running
 * inside a Tauri application environment.
 */

import { invoke } from '@tauri-apps/api/tauri';

/**
 * Check if running in Tauri environment
 */
export async function isTauriAvailable(): Promise<boolean> {
  try {
    // Check if Tauri invoke function is available
    if (typeof window.__TAURI_INTERNALS__ === 'undefined') {
      console.warn('[TauriEnv] window.__TAURI_INTERNALS__ is undefined');
      return false;
    }

    if (typeof invoke === 'undefined') {
      console.warn('[TauriEnv] invoke function is undefined');
      return false;
    }

    // Try a simple ping command
    const result = await invoke('ping');
    console.log('[TauriEnv] Tauri is available:', result);
    return true;
  } catch (error) {
    console.error('[TauriEnv] Tauri not available:', error);
    return false;
  }
}

/**
 * Initialize Tauri environment check
 */
export async function initializeTauriEnvironment(): Promise<void> {
  console.log('[TauriEnv] Initializing Tauri environment check...');

  const isAvailable = await isTauriAvailable();

  if (!isAvailable) {
    console.warn('[TauriEnv] ==========================================');
    console.warn('[TauriEnv] ⚠️  NOT RUNNING IN TAURI ENVIRONMENT');
    console.warn('[TauriEnv] =========================================');
    console.warn('[TauriEnv]');
    console.warn('[TauriEnv] Your application appears to be running in a web browser');
    console.warn('[TauriEnv] Please start the application using:');
    console.warn('[TauriEnv]   - ./dev.sh dev (recommended)');
    console.warn('[TauriEnv]   - npm run tauri dev');
    console.warn('[TauriEnv]');
    console.warn('[TauriEnv] Direct Tauri functions (invoke, listen) will not work');
    console.warn('[TauriEnv] =========================================');
  } else {
    console.log('[TauriEnv] ✓ Tauri environment detected');
  }
}
