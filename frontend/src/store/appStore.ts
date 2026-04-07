/**
 * Application state store using Zustand
 */

import { create } from 'zustand';
import type { TranscriptData, ResponseData, SystemStatus, ConfigData } from '../types/api';

interface AppState {
  // Transcript state
  transcripts: TranscriptData[];
  addTranscript: (transcript: TranscriptData) => void;
  clearTranscripts: () => void;

  // Response state
  responses: ResponseData[];
  addResponse: (response: ResponseData) => void;
  clearResponses: () => void;

  // System status
  status: SystemStatus;
  setStatus: (status: SystemStatus) => void;

  // Configuration
  config: ConfigData | null;
  setConfig: (config: ConfigData) => void;

  // Audio device selection
  selectedMicId: string | null;
  selectedSpeakerId: string | null;
  setSelectedMicId: (id: string | null) => void;
  setSelectedSpeakerId: (id: string | null) => void;

  // Clear all context
  clearContext: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  // Initial state
  transcripts: [],
  responses: [],
  status: {
    state: 'idle',
    message: 'Ready',
  },
  config: null,
  selectedMicId: null,
  selectedSpeakerId: null,

  // Actions
  addTranscript: (transcript) =>
    set((state) => ({
      transcripts: [...state.transcripts, transcript],
    })),

  clearTranscripts: () =>
    set({
      transcripts: [],
    }),

  addResponse: (response) =>
    set((state) => ({
      responses: [...state.responses, response],
    })),

  clearResponses: () =>
    set({
      responses: [],
    }),

  setStatus: (status) =>
    set({
      status,
    }),

  setConfig: (config) =>
    set({
      config,
    }),

  setSelectedMicId: (id) =>
    set({
      selectedMicId: id,
    }),

  setSelectedSpeakerId: (id) =>
    set({
      selectedSpeakerId: id,
    }),

  clearContext: () =>
    set({
      transcripts: [],
      responses: [],
    }),
}));
