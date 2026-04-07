/**
 * Property-based tests for useAudioRecording.selectDevice
 *
 * Feature: audio-device-selection
 * Properties 3, 4, 5 (design.md)
 *
 * Uses fast-check + Vitest.
 * Validates: Requirements 2.3, 3.3, 4.3, 4.4, 5.1, 5.2
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import * as fc from 'fast-check';
import { useAudioRecording } from './useAudioRecording';

// ---------------------------------------------------------------------------
// Module mocks
// ---------------------------------------------------------------------------

// Mock tauriService functions used by the hook
const mockStartRecording = vi.fn();
const mockStopRecording = vi.fn();
const mockSetAudioDevice = vi.fn();
const mockGetAudioDevices = vi.fn();

vi.mock('../services/tauriService', () => ({
  startRecording: (...args: unknown[]) => mockStartRecording(...args),
  stopRecording: (...args: unknown[]) => mockStopRecording(...args),
  setAudioDevice: (...args: unknown[]) => mockSetAudioDevice(...args),
  getAudioDevices: (...args: unknown[]) => mockGetAudioDevices(...args),
}));

// Mock audioService (not under test here)
vi.mock('../services/audioService', () => ({
  getAudioService: () => ({
    requestMicrophoneAccess: vi.fn(),
    startVisualization: vi.fn(),
    stopMicrophone: vi.fn(),
  }),
}));

// ---------------------------------------------------------------------------
// Zustand store spy helpers
// ---------------------------------------------------------------------------

// We import the real store so we can inspect its state after hook calls.
// The store is NOT mocked — we test real store updates.
import { useAppStore } from '../store/appStore';

function getStoreState() {
  return useAppStore.getState();
}

function resetStore() {
  useAppStore.setState({ selectedMicId: null, selectedSpeakerId: null });
}

// ---------------------------------------------------------------------------
// Arbitraries
// ---------------------------------------------------------------------------

const deviceTypeArb = fc.constantFrom('microphone' as const, 'speaker' as const);
const deviceIdArb = fc.string({ minLength: 1, maxLength: 20 }).filter(s => s.trim().length > 0);

// ---------------------------------------------------------------------------
// Helper: render hook in a known recording state
// ---------------------------------------------------------------------------

async function renderHookWithRecordingState(isRecording: boolean) {
  mockStartRecording.mockResolvedValue('ok');
  mockStopRecording.mockResolvedValue('ok');
  mockSetAudioDevice.mockResolvedValue('ok');

  const { result } = renderHook(() => useAudioRecording());

  if (isRecording) {
    await act(async () => {
      await result.current.startRecording('microphone');
    });
    expect(result.current.isRecording).toBe(true);
  }

  return result;
}

// ---------------------------------------------------------------------------
// Property 3: 设备切换操作顺序
// Feature: audio-device-selection, Property 3
// Validates: Requirements 2.3, 3.3, 4.3
// ---------------------------------------------------------------------------

describe('Property 3: selectDevice operation order', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    resetStore();
    mockStartRecording.mockResolvedValue('ok');
    mockStopRecording.mockResolvedValue('ok');
    mockSetAudioDevice.mockResolvedValue('ok');
  });

  it('when NOT recording: setAudioDevice is called without stopRecording', async () => {
    await fc.assert(
      fc.asyncProperty(deviceTypeArb, deviceIdArb, async (deviceType, deviceId) => {
        vi.clearAllMocks();
        mockStartRecording.mockResolvedValue('ok');
        mockStopRecording.mockResolvedValue('ok');
        mockSetAudioDevice.mockResolvedValue('ok');
        resetStore();

        const result = await renderHookWithRecordingState(false);

        await act(async () => {
          await result.current.selectDevice(deviceType, deviceId);
        });

        expect(mockStopRecording).not.toHaveBeenCalled();
        expect(mockSetAudioDevice).toHaveBeenCalledWith(deviceType, deviceId);
        // startRecording should NOT be called again (was not recording before)
        // (it was called 0 times since we started not-recording)
        expect(mockStartRecording).not.toHaveBeenCalled();
      }),
      { numRuns: 20 }
    );
  });

  it('when recording: stopRecording is called before setAudioDevice, then startRecording after', async () => {
    await fc.assert(
      fc.asyncProperty(deviceTypeArb, deviceIdArb, async (deviceType, deviceId) => {
        vi.clearAllMocks();
        mockStartRecording.mockResolvedValue('ok');
        mockStopRecording.mockResolvedValue('ok');
        mockSetAudioDevice.mockResolvedValue('ok');
        resetStore();

        const result = await renderHookWithRecordingState(true);

        // Track call order
        const callOrder: string[] = [];
        mockStopRecording.mockImplementation(async () => { callOrder.push('stop'); return 'ok'; });
        mockSetAudioDevice.mockImplementation(async () => { callOrder.push('set'); return 'ok'; });
        mockStartRecording.mockImplementation(async () => { callOrder.push('start'); return 'ok'; });

        await act(async () => {
          await result.current.selectDevice(deviceType, deviceId);
        });

        expect(callOrder).toEqual(['stop', 'set', 'start']);
        expect(mockSetAudioDevice).toHaveBeenCalledWith(deviceType, deviceId);
        expect(mockStartRecording).toHaveBeenCalledWith(deviceType);
      }),
      { numRuns: 20 }
    );
  });
});

// ---------------------------------------------------------------------------
// Property 4: 设备切换失败时的状态回滚
// Feature: audio-device-selection, Property 4
// Validates: Requirements 4.4
// ---------------------------------------------------------------------------

describe('Property 4: store not updated when setAudioDevice fails', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    resetStore();
    mockStartRecording.mockResolvedValue('ok');
    mockStopRecording.mockResolvedValue('ok');
  });

  it('selectedMicId stays unchanged when setAudioDevice throws for microphone', async () => {
    await fc.assert(
      fc.asyncProperty(deviceIdArb, deviceIdArb, async (initialId, newId) => {
        vi.clearAllMocks();
        mockStartRecording.mockResolvedValue('ok');
        mockStopRecording.mockResolvedValue('ok');
        mockSetAudioDevice.mockResolvedValue('ok');

        // Set an initial selected mic id in the store
        useAppStore.setState({ selectedMicId: initialId, selectedSpeakerId: null });

        const result = await renderHookWithRecordingState(false);

        // Now make setAudioDevice fail
        mockSetAudioDevice.mockRejectedValue(new Error('device not found'));

        await act(async () => {
          try {
            await result.current.selectDevice('microphone', newId);
          } catch {
            // expected to throw
          }
        });

        // Store must NOT have been updated
        expect(getStoreState().selectedMicId).toBe(initialId);
      }),
      { numRuns: 20 }
    );
  });

  it('selectedSpeakerId stays unchanged when setAudioDevice throws for speaker', async () => {
    await fc.assert(
      fc.asyncProperty(deviceIdArb, deviceIdArb, async (initialId, newId) => {
        vi.clearAllMocks();
        mockStartRecording.mockResolvedValue('ok');
        mockStopRecording.mockResolvedValue('ok');
        mockSetAudioDevice.mockResolvedValue('ok');

        useAppStore.setState({ selectedMicId: null, selectedSpeakerId: initialId });

        const result = await renderHookWithRecordingState(false);

        mockSetAudioDevice.mockRejectedValue(new Error('device not found'));

        await act(async () => {
          try {
            await result.current.selectDevice('speaker', newId);
          } catch {
            // expected to throw
          }
        });

        expect(getStoreState().selectedSpeakerId).toBe(initialId);
      }),
      { numRuns: 20 }
    );
  });
});

// ---------------------------------------------------------------------------
// Property 5: Store 与 UI 选中状态同步
// Feature: audio-device-selection, Property 5
// Validates: Requirements 5.1, 5.2
// ---------------------------------------------------------------------------

describe('Property 5: store selectedMicId/selectedSpeakerId matches last successful selectDevice', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    resetStore();
    mockStartRecording.mockResolvedValue('ok');
    mockStopRecording.mockResolvedValue('ok');
    mockSetAudioDevice.mockResolvedValue('ok');
  });

  it('after successful selectDevice, store reflects the chosen deviceId', async () => {
    await fc.assert(
      fc.asyncProperty(deviceTypeArb, deviceIdArb, async (deviceType, deviceId) => {
        vi.clearAllMocks();
        mockStartRecording.mockResolvedValue('ok');
        mockStopRecording.mockResolvedValue('ok');
        mockSetAudioDevice.mockResolvedValue('ok');
        resetStore();

        const result = await renderHookWithRecordingState(false);

        await act(async () => {
          await result.current.selectDevice(deviceType, deviceId);
        });

        const state = getStoreState();
        if (deviceType === 'microphone') {
          expect(state.selectedMicId).toBe(deviceId);
        } else {
          expect(state.selectedSpeakerId).toBe(deviceId);
        }

        // Hook return values also reflect store
        if (deviceType === 'microphone') {
          expect(result.current.selectedMicId).toBe(deviceId);
        } else {
          expect(result.current.selectedSpeakerId).toBe(deviceId);
        }
      }),
      { numRuns: 30 }
    );
  });

  it('after a sequence of successful selections, store reflects the last one', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.array(fc.tuple(deviceTypeArb, deviceIdArb), { minLength: 2, maxLength: 5 }),
        async (selections) => {
          vi.clearAllMocks();
          mockStartRecording.mockResolvedValue('ok');
          mockStopRecording.mockResolvedValue('ok');
          mockSetAudioDevice.mockResolvedValue('ok');
          resetStore();

          const result = await renderHookWithRecordingState(false);

          for (const [deviceType, deviceId] of selections) {
            await act(async () => {
              await result.current.selectDevice(deviceType, deviceId);
            });
          }

          // Find last mic and last speaker selection
          const lastMic = [...selections].reverse().find(([t]) => t === 'microphone');
          const lastSpeaker = [...selections].reverse().find(([t]) => t === 'speaker');

          const state = getStoreState();
          if (lastMic) expect(state.selectedMicId).toBe(lastMic[1]);
          if (lastSpeaker) expect(state.selectedSpeakerId).toBe(lastSpeaker[1]);
        }
      ),
      { numRuns: 20 }
    );
  });
});
