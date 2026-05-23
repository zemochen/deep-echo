/**
 * AudioDeviceSelector component
 * Provides dropdowns for selecting microphone and speaker audio devices
 * Requirements: 1.5, 2.1, 2.5, 3.1, 3.5, 4.1, 4.4, 4.5
 */

import { useState, useEffect } from 'react';
import {
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
  IconButton,
  CircularProgress,
  Alert,
  Stack,
  Tooltip,
  type SelectChangeEvent,
} from '@mui/material';
import { Refresh } from '@mui/icons-material';
import type { AudioDevice } from '../types/api';

// ============================================================================
// Props
// ============================================================================

export interface AudioDeviceSelectorProps {
  devices: AudioDevice[];
  isLoadingDevices: boolean;
  selectedMicId: string | null;
  selectedSpeakerId: string | null;
  loadDevices: () => Promise<void>;
  selectDevice: (deviceType: 'microphone' | 'speaker', deviceId: string) => Promise<void>;
  onDeviceChange?: (deviceType: 'microphone' | 'speaker', deviceId: string) => void;
}

// ============================================================================
// Component
// ============================================================================

export function AudioDeviceSelector({
  devices,
  isLoadingDevices,
  selectedMicId,
  selectedSpeakerId,
  loadDevices,
  selectDevice,
  onDeviceChange,
}: AudioDeviceSelectorProps) {
  const [switchError, setSwitchError] = useState<string | null>(null);

  // Load devices on mount only
  useEffect(() => {
    loadDevices();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const microphones = devices.filter((d) => d.deviceType === 'microphone');
  const speakers = devices.filter((d) => d.deviceType === 'speaker');

  const handleMicChange = async (event: SelectChangeEvent<string>) => {
    const deviceId = event.target.value;
    const prevId = selectedMicId;
    setSwitchError(null);

    try {
      await selectDevice('microphone', deviceId);
      onDeviceChange?.('microphone', deviceId);
    } catch (err) {
      const msg = err instanceof Error ? err.message : '切换麦克风失败';
      setSwitchError(msg);
      // State rollback is handled by the hook (store not updated on failure)
      // The Select value is bound to selectedMicId from the store, so it reverts automatically
      void prevId; // suppress unused warning
    }
  };

  const handleSpeakerChange = async (event: SelectChangeEvent<string>) => {
    const deviceId = event.target.value;
    const prevId = selectedSpeakerId;
    setSwitchError(null);

    try {
      await selectDevice('speaker', deviceId);
      onDeviceChange?.('speaker', deviceId);
    } catch (err) {
      const msg = err instanceof Error ? err.message : '切换扬声器失败';
      setSwitchError(msg);
      void prevId;
    }
  };

  const handleRefresh = () => {
    setSwitchError(null);
    loadDevices();
  };

  return (
    <Stack spacing={2}>
      {/* Header row */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography variant="subtitle2">AudioDevices</Typography>
        <Tooltip title="Refresh Device">
          <span>
            <IconButton
              size="small"
              onClick={handleRefresh}
              disabled={isLoadingDevices}
              aria-label="Refresh Device"
            >
              {isLoadingDevices ? (
                <CircularProgress size={16} />
              ) : (
                <Refresh fontSize="small" />
              )}
            </IconButton>
          </span>
        </Tooltip>
      </Box>

      {/* Error alert */}
      {switchError && (
        <Alert severity="error" onClose={() => setSwitchError(null)}>
          {switchError}
        </Alert>
      )}

      {/* Microphone selector */}
      <FormControl fullWidth size="small" disabled={isLoadingDevices || microphones.length === 0}>
        <InputLabel id="mic-select-label" shrink>麦克风</InputLabel>
        <Select
          labelId="mic-select-label"
          id="mic-select"
          value={selectedMicId ?? ''}
          label="麦克风"
          onChange={handleMicChange}
          displayEmpty
          notched
        >
          <MenuItem value="" disabled>
            <em>{microphones.length === 0 ? '无可用设备' : '请选择麦克风'}</em>
          </MenuItem>
          {microphones.map((device) => (
            <MenuItem key={device.id} value={device.id}>
              {device.name}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      {/* Speaker selector */}
      <FormControl fullWidth size="small" disabled={isLoadingDevices || speakers.length === 0}>
        <InputLabel id="speaker-select-label" shrink>Speaker</InputLabel>
        <Select
          labelId="speaker-select-label"
          id="speaker-select"
          value={selectedSpeakerId ?? ''}
          label="Speaker"
          onChange={handleSpeakerChange}
          displayEmpty
          notched
        >
          <MenuItem value="" disabled>
            <em>{speakers.length === 0 ? 'No devices available' : 'Select speaker'}</em>
          </MenuItem>
          {speakers.map((device) => (
            <MenuItem key={device.id} value={device.id}>
              {device.name}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
    </Stack>
  );
}
