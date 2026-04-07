/**
 * Unit tests for AudioDeviceSelector component
 * Requirements: 1.5, 4.1, 4.2, 4.5
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AudioDeviceSelector } from './AudioDeviceSelector';
import type { AudioDevice } from '../types/api';

// ============================================================================
// Test fixtures
// ============================================================================

const mockMicrophones: AudioDevice[] = [
  { id: '0', name: 'Built-in Microphone', deviceType: 'microphone' },
  { id: '1', name: 'USB Microphone', deviceType: 'microphone' },
];

const mockSpeakers: AudioDevice[] = [
  { id: '5', name: 'Built-in Speakers', deviceType: 'speaker' },
];

const defaultProps = {
  devices: [...mockMicrophones, ...mockSpeakers],
  isLoadingDevices: false,
  selectedMicId: null,
  selectedSpeakerId: null,
  loadDevices: vi.fn().mockResolvedValue(undefined),
  selectDevice: vi.fn().mockResolvedValue(undefined),
};

// ============================================================================
// Tests
// ============================================================================

describe('AudioDeviceSelector', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    defaultProps.loadDevices = vi.fn().mockResolvedValue(undefined);
    defaultProps.selectDevice = vi.fn().mockResolvedValue(undefined);
  });

  // Requirement 4.2: loadDevices called automatically on mount
  it('calls loadDevices on mount', () => {
    const loadDevices = vi.fn().mockResolvedValue(undefined);
    render(<AudioDeviceSelector {...defaultProps} loadDevices={loadDevices} />);
    expect(loadDevices).toHaveBeenCalledTimes(1);
  });

  // Requirement 4.1: both dropdowns render when devices are present
  it('renders microphone and speaker dropdowns when devices are present', () => {
    render(<AudioDeviceSelector {...defaultProps} />);

    expect(screen.getByLabelText('麦克风')).toBeInTheDocument();
    expect(screen.getByLabelText('扬声器')).toBeInTheDocument();
  });

  // Requirement 4.1: device names appear as options when dropdown is opened
  it('renders microphone device names when dropdown is opened', () => {
    render(<AudioDeviceSelector {...defaultProps} />);

    // Open the mic dropdown via mouseDown on the select element
    const micSelect = screen.getByRole('combobox', { name: /麦克风/i });
    fireEvent.mouseDown(micSelect);

    expect(screen.getByText('Built-in Microphone')).toBeInTheDocument();
    expect(screen.getByText('USB Microphone')).toBeInTheDocument();
  });

  it('renders speaker device names when dropdown is opened', () => {
    render(<AudioDeviceSelector {...defaultProps} />);

    // Open the speaker dropdown
    const speakerSelect = screen.getByRole('combobox', { name: /扬声器/i });
    fireEvent.mouseDown(speakerSelect);

    expect(screen.getByText('Built-in Speakers')).toBeInTheDocument();
  });

  // Requirement 4.5: "无可用设备" shown when device list is empty
  it('shows "无可用设备" placeholder when microphone list is empty', () => {
    render(
      <AudioDeviceSelector
        {...defaultProps}
        devices={mockSpeakers} // only speakers, no mics
      />
    );

    const placeholders = screen.getAllByText('无可用设备');
    expect(placeholders.length).toBeGreaterThanOrEqual(1);
  });

  it('shows "无可用设备" placeholder when speaker list is empty', () => {
    render(
      <AudioDeviceSelector
        {...defaultProps}
        devices={mockMicrophones} // only mics, no speakers
      />
    );

    const placeholders = screen.getAllByText('无可用设备');
    expect(placeholders.length).toBeGreaterThanOrEqual(1);
  });

  it('shows "无可用设备" in both dropdowns when device list is empty', () => {
    render(<AudioDeviceSelector {...defaultProps} devices={[]} />);

    const placeholders = screen.getAllByText('无可用设备');
    expect(placeholders).toHaveLength(2);
  });

  // Requirement 1.5: loading state display
  it('shows CircularProgress when isLoadingDevices is true', () => {
    render(<AudioDeviceSelector {...defaultProps} isLoadingDevices={true} />);

    // The refresh button shows a CircularProgress when loading
    const progress = document.querySelector('.MuiCircularProgress-root');
    expect(progress).toBeInTheDocument();
  });

  it('disables dropdowns when isLoadingDevices is true', () => {
    render(<AudioDeviceSelector {...defaultProps} isLoadingDevices={true} />);

    // Both FormControls should be disabled
    const selects = screen.getAllByRole('combobox');
    selects.forEach((select) => {
      expect(select).toHaveAttribute('aria-disabled', 'true');
    });
  });

  it('does not show CircularProgress when not loading', () => {
    render(<AudioDeviceSelector {...defaultProps} isLoadingDevices={false} />);

    const progress = document.querySelector('.MuiCircularProgress-root');
    expect(progress).not.toBeInTheDocument();
  });
});
