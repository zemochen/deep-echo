/**
 * UI-related type definitions
 */

export interface UIState {
  isFrozen: boolean;
  updateInterval: number;
  theme: 'light' | 'dark';
  sidebarOpen: boolean;
}

export interface NotificationMessage {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  timestamp: number;
}
