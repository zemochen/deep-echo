/**
 * StatusIndicator component
 * Displays current system status and messages
 * Requirements: 1.8
 */

import { Box, Chip, Typography, Alert, Stack } from '@mui/material';
import {
  CheckCircle,
  RadioButtonChecked,
  HourglassEmpty,
  Error as ErrorIcon,
} from '@mui/icons-material';
import type { SystemStatus } from '../types';

interface StatusIndicatorProps {
  status: SystemStatus;
}

export function StatusIndicator({ status }: StatusIndicatorProps) {
  const getStatusIcon = () => {
    switch (status.state) {
      case 'idle':
        return <CheckCircle />;
      case 'recording':
        return <RadioButtonChecked />;
      case 'processing':
        return <HourglassEmpty />;
      case 'error':
        return <ErrorIcon />;
      default:
        return <CheckCircle />;
    }
  };

  const getStatusColor = () => {
    switch (status.state) {
      case 'idle':
        return 'success';
      case 'recording':
        return 'primary';
      case 'processing':
        return 'info';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusLabel = () => {
    switch (status.state) {
      case 'idle':
        return 'Ready';
      case 'recording':
        return 'Recording';
      case 'processing':
        return 'Processing';
      case 'error':
        return 'Error';
      default:
        return 'Unknown';
    }
  };

  const getAlertSeverity = () => {
    switch (status.state) {
      case 'idle':
        return 'success';
      case 'recording':
        return 'info';
      case 'processing':
        return 'info';
      case 'error':
        return 'error';
      default:
        return 'info';
    }
  };

  return (
    <Stack spacing={2}>
      {/* Status Chip */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Chip
          icon={getStatusIcon()}
          label={getStatusLabel()}
          color={getStatusColor() as any}
          sx={{ fontWeight: 'bold' }}
        />
      </Box>

      {/* Status Message */}
      {status.message && (
        <Alert severity={getAlertSeverity() as any} variant="outlined">
          {status.message}
        </Alert>
      )}

      {/* Status Details */}
      {status.details && Object.keys(status.details).length > 0 && (
        <Box sx={{ mt: 1 }}>
          <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 'bold' }}>
            Details:
          </Typography>
          {Object.entries(status.details).map(([key, value]) => (
            <Typography key={key} variant="caption" color="text.secondary" sx={{ display: 'block' }}>
              {key}: {String(value)}
            </Typography>
          ))}
        </Box>
      )}
    </Stack>
  );
}
