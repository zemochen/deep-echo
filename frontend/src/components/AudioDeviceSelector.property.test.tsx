// Feature: audio-device-selection, Property 6: 设备选择命令参数正确性

/**
 * Property-based tests for AudioDeviceSelector component
 *
 * Property 6: 设备选择命令参数正确性
 * For any deviceType (microphone/speaker) and deviceId, when the user selects
 * that device in AudioDeviceSelector, `selectDevice` is called with parameters
 * exactly matching the selection.
 *
 * Validates: Requirements 2.1, 3.1
 *
 * Testing framework: fast-check + Vitest (TypeScript)
 */

import { render, fireEvent, act, cleanup } from '@testing-library/react';
import { describe, it, expect, vi, afterEach } from 'vitest';
import * as fc from 'fast-check';
import { AudioDeviceSelector } from './AudioDeviceSelector';
import type { AudioDevice } from '../types/api';

// Clean up DOM after each test to prevent element accumulation
afterEach(() => {
  cleanup();
});

// ---------------------------------------------------------------------------
// Arbitraries
// ---------------------------------------------------------------------------

const deviceTypeArb = fc.constantFrom('microphone' as const, 'speaker' as const);

// Device ids: alphanumeric strings that are safe as CSS attribute selectors
// Avoid special characters that would break querySelector('[data-value="..."]')
const deviceIdArb = fc
  .stringMatching(/^[a-zA-Z0-9_-]{1,20}$/)
  .filter((s) => s.length > 0);

// Build a minimal device list for a given type containing the target device
function makeDevices(deviceType: 'microphone' | 'speaker', targetId: string): AudioDevice[] {
  return [
    { id: targetId, name: `Device ${targetId}`, deviceType },
    { id: `${targetId}x`, name: 'Other Device', deviceType },
  ];
}

// Helper: render the component, interact with a dropdown, and clean up
async function selectDeviceInUI(
  deviceType: 'microphone' | 'speaker',
  deviceId: string,
  selectDevice: ReturnType<typeof vi.fn>,
) {
  const loadDevices = vi.fn().mockResolvedValue(undefined);
  const devices = makeDevices(deviceType, deviceId);

  const { getByRole, unmount } = render(
    <AudioDeviceSelector
      devices={devices}
      isLoadingDevices={false}
      selectedMicId={null}
      selectedSpeakerId={null}
      loadDevices={loadDevices}
      selectDevice={selectDevice}
    />,
  );

  const labelPattern = deviceType === 'microphone' ? /麦克风/i : /扬声器/i;
  const selectEl = getByRole('combobox', { name: labelPattern });

  await act(async () => {
    fireEvent.mouseDown(selectEl);
  });

  // Click the menu item with the target value
  const option = document.querySelector(`[data-value="${deviceId}"]`);
  if (option) {
    await act(async () => {
      fireEvent.click(option);
    });
  }

  // Unmount to clean up this render before the next iteration
  unmount();
}

// ---------------------------------------------------------------------------
// Property 6: 设备选择命令参数正确性
// Validates: Requirements 2.1, 3.1
// ---------------------------------------------------------------------------

describe('Property 6: 设备选择命令参数正确性', () => {
  it('selectDevice is called with exact deviceType and deviceId when user selects a microphone', async () => {
    await fc.assert(
      fc.asyncProperty(deviceIdArb, async (deviceId) => {
        const selectDevice = vi.fn().mockResolvedValue(undefined);
        await selectDeviceInUI('microphone', deviceId, selectDevice);
        expect(selectDevice).toHaveBeenCalledWith('microphone', deviceId);
      }),
      { numRuns: 25 },
    );
  });

  it('selectDevice is called with exact deviceType and deviceId when user selects a speaker', async () => {
    await fc.assert(
      fc.asyncProperty(deviceIdArb, async (deviceId) => {
        const selectDevice = vi.fn().mockResolvedValue(undefined);
        await selectDeviceInUI('speaker', deviceId, selectDevice);
        expect(selectDevice).toHaveBeenCalledWith('speaker', deviceId);
      }),
      { numRuns: 25 },
    );
  });

  it('selectDevice parameters match selection for any deviceType and deviceId combination', async () => {
    await fc.assert(
      fc.asyncProperty(deviceTypeArb, deviceIdArb, async (deviceType, deviceId) => {
        const selectDevice = vi.fn().mockResolvedValue(undefined);
        await selectDeviceInUI(deviceType, deviceId, selectDevice);

        expect(selectDevice).toHaveBeenCalledWith(deviceType, deviceId);
        const [calledType, calledId] = selectDevice.mock.calls[0] as [string, string];
        expect(calledType).toBe(deviceType);
        expect(calledId).toBe(deviceId);
      }),
      { numRuns: 30 },
    );
  });
});

// ---------------------------------------------------------------------------
// Feature: audio-device-selection, Property 7: 刷新后选中状态保持
// ---------------------------------------------------------------------------

/**
 * Property 7: 刷新后选中状态保持
 *
 * For any device list and selected id, after a refresh, if the previously
 * selected device id is still present in the new list, the component should
 * render that device as still selected (i.e. the hidden native input value
 * for the Select equals the previously selected id).
 *
 * Validates: Requirements 5.3
 *
 * Testing framework: fast-check + Vitest (TypeScript)
 *
 * Implementation note: We query the hidden <input> elements inside the MUI
 * Select components (id="mic-select" / id="speaker-select") rather than using
 * `screen.getByRole` to avoid cross-iteration DOM accumulation issues when
 * fast-check runs many iterations in the same document body.
 */

// ---------------------------------------------------------------------------
// Arbitraries for Property 7
// ---------------------------------------------------------------------------

// A non-empty list of devices of a given type, all with unique safe ids
function makeDeviceListArb(deviceType: 'microphone' | 'speaker') {
  return fc
    .array(
      fc.record({
        id: deviceIdArb,
        name: fc.string({ minLength: 1, maxLength: 20 }),
      }),
      { minLength: 1, maxLength: 5 },
    )
    .map((items) => {
      // Deduplicate by id
      const seen = new Set<string>();
      return items
        .filter(({ id }) => {
          if (seen.has(id)) return false;
          seen.add(id);
          return true;
        })
        .map(({ id, name }) => ({ id, name, deviceType } as AudioDevice));
    })
    .filter((list) => list.length > 0);
}

// Pick a random id that exists in the list
function selectedIdFromListArb(listArb: fc.Arbitrary<AudioDevice[]>) {
  return listArb.chain((list) =>
    fc.integer({ min: 0, max: list.length - 1 }).map((idx) => ({
      list,
      selectedId: list[idx].id,
    })),
  );
}

/**
 * Get the value of the hidden native <input> that MUI Select uses to track
 * its current value. We scope the query to `container` to avoid picking up
 * stale DOM from previous fast-check iterations.
 */
function getNativeInputValue(container: HTMLElement, selectId: string): string {
  // MUI renders a hidden <input> sibling to the combobox div; its aria-hidden
  // attribute and tabindex="-1" distinguish it from the visible element.
  const input = container.querySelector<HTMLInputElement>(
    `#${selectId} ~ input[aria-hidden="true"]`,
  );
  return input?.value ?? '';
}

// ---------------------------------------------------------------------------
// Property 7: 刷新后选中状态保持
// Validates: Requirements 5.3
// ---------------------------------------------------------------------------

describe('Property 7: 刷新后选中状态保持', () => {
  it('microphone selection is preserved after device list refresh when selected id is still present', async () => {
    await fc.assert(
      fc.asyncProperty(
        selectedIdFromListArb(makeDeviceListArb('microphone')),
        async ({ list, selectedId }) => {
          const loadDevices = vi.fn().mockResolvedValue(undefined);
          const selectDevice = vi.fn<(deviceType: 'microphone' | 'speaker', deviceId: string) => Promise<void>>()
            .mockResolvedValue(undefined);

          const { container, rerender, unmount } = render(
            <AudioDeviceSelector
              devices={list}
              isLoadingDevices={false}
              selectedMicId={selectedId}
              selectedSpeakerId={null}
              loadDevices={loadDevices}
              selectDevice={selectDevice}
            />,
          );

          // Simulate refresh: same list comes back, selected id still present
          rerender(
            <AudioDeviceSelector
              devices={list}
              isLoadingDevices={false}
              selectedMicId={selectedId}
              selectedSpeakerId={null}
              loadDevices={loadDevices}
              selectDevice={selectDevice}
            />,
          );

          // The hidden native input value reflects the current selection
          expect(getNativeInputValue(container, 'mic-select')).toBe(selectedId);

          unmount();
        },
      ),
      { numRuns: 30 },
    );
  });

  it('speaker selection is preserved after device list refresh when selected id is still present', async () => {
    await fc.assert(
      fc.asyncProperty(
        selectedIdFromListArb(makeDeviceListArb('speaker')),
        async ({ list, selectedId }) => {
          const loadDevices = vi.fn().mockResolvedValue(undefined);
          const selectDevice = vi.fn<(deviceType: 'microphone' | 'speaker', deviceId: string) => Promise<void>>()
            .mockResolvedValue(undefined);

          const { container, rerender, unmount } = render(
            <AudioDeviceSelector
              devices={list}
              isLoadingDevices={false}
              selectedMicId={null}
              selectedSpeakerId={selectedId}
              loadDevices={loadDevices}
              selectDevice={selectDevice}
            />,
          );

          rerender(
            <AudioDeviceSelector
              devices={list}
              isLoadingDevices={false}
              selectedMicId={null}
              selectedSpeakerId={selectedId}
              loadDevices={loadDevices}
              selectDevice={selectDevice}
            />,
          );

          expect(getNativeInputValue(container, 'speaker-select')).toBe(selectedId);

          unmount();
        },
      ),
      { numRuns: 30 },
    );
  });

  it('both mic and speaker selections are preserved after refresh when both ids are still present', async () => {
    await fc.assert(
      fc.asyncProperty(
        selectedIdFromListArb(makeDeviceListArb('microphone')),
        selectedIdFromListArb(makeDeviceListArb('speaker')),
        async ({ list: micList, selectedId: selectedMicId }, { list: speakerList, selectedId: selectedSpeakerId }) => {
          const loadDevices = vi.fn().mockResolvedValue(undefined);
          const selectDevice = vi.fn<(deviceType: 'microphone' | 'speaker', deviceId: string) => Promise<void>>()
            .mockResolvedValue(undefined);

          const allDevices = [...micList, ...speakerList];

          const { container, rerender, unmount } = render(
            <AudioDeviceSelector
              devices={allDevices}
              isLoadingDevices={false}
              selectedMicId={selectedMicId}
              selectedSpeakerId={selectedSpeakerId}
              loadDevices={loadDevices}
              selectDevice={selectDevice}
            />,
          );

          rerender(
            <AudioDeviceSelector
              devices={allDevices}
              isLoadingDevices={false}
              selectedMicId={selectedMicId}
              selectedSpeakerId={selectedSpeakerId}
              loadDevices={loadDevices}
              selectDevice={selectDevice}
            />,
          );

          expect(getNativeInputValue(container, 'mic-select')).toBe(selectedMicId);
          expect(getNativeInputValue(container, 'speaker-select')).toBe(selectedSpeakerId);

          unmount();
        },
      ),
      { numRuns: 20 },
    );
  });
});
