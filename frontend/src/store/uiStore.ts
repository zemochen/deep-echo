/**
 * UI state store using Zustand
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { UIState, NotificationMessage } from '../types/ui';

interface UIStoreState extends UIState {
  // Notifications
  notifications: NotificationMessage[];
  addNotification: (notification: Omit<NotificationMessage, 'id' | 'timestamp'>) => void;
  removeNotification: (id: string) => void;

  // UI actions
  setFrozen: (frozen: boolean) => void;
  setUpdateInterval: (interval: number) => void;
  setTheme: (theme: 'light' | 'dark') => void;
  setSidebarOpen: (open: boolean) => void;
  toggleSidebar: () => void;
}

export const useUIStore = create<UIStoreState>()(
  persist(
    (set) => ({
      // Initial state
      isFrozen: false,
      updateInterval: 5000,
      theme: 'light',
      sidebarOpen: true,
      notifications: [],

      // Actions
      addNotification: (notification) =>
        set((state) => ({
          notifications: [
            ...state.notifications,
            {
              ...notification,
              id: `${Date.now()}-${Math.random()}`,
              timestamp: Date.now(),
            },
          ],
        })),

      removeNotification: (id) =>
        set((state) => ({
          notifications: state.notifications.filter((n) => n.id !== id),
        })),

      setFrozen: (frozen) =>
        set({
          isFrozen: frozen,
        }),

      setUpdateInterval: (interval) =>
        set({
          updateInterval: interval,
        }),

      setTheme: (theme) =>
        set({
          theme,
        }),

      setSidebarOpen: (open) =>
        set({
          sidebarOpen: open,
        }),

      toggleSidebar: () =>
        set((state) => ({
          sidebarOpen: !state.sidebarOpen,
        })),
    }),
    {
      name: 'deepecho-ui-storage',
      partialize: (state) => ({
        theme: state.theme,
        updateInterval: state.updateInterval,
        sidebarOpen: state.sidebarOpen,
      }),
    }
  )
);
