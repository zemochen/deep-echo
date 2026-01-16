/**
 * ControlPanel component
 * Provides controls for freezing display, adjusting update interval, and clearing context
 * Requirements: 1.4, 1.5, 1.7
 */

import { Box, Button, Slider, Typography, Stack, Divider } from '@mui/material';
import { Pause, PlayArrow, Delete } from '@mui/icons-material';

interface ControlPanelProps {
  frozen: boolean;
  updateInterval: number;
  onToggleFreeze: () => void;
  onUpdateIntervalChange: (value: number) => void;
  onClearContext: () => void;
}

export function ControlPanel({
  frozen,
  updateInterval,
  onToggleFreeze,
  onUpdateIntervalChange,
  onClearContext,
}: ControlPanelProps) {
  const handleSliderChange = (_event: Event, value: number | number[]) => {
    onUpdateIntervalChange(value as number);
  };

  return (
    <Stack spacing={3}>
      {/* Freeze/Unfreeze Button */}
      <Box>
        <Typography variant="subtitle2" gutterBottom>
          Display Control
        </Typography>
        <Button
          variant="contained"
          fullWidth
          startIcon={frozen ? <PlayArrow /> : <Pause />}
          onClick={onToggleFreeze}
          color={frozen ? 'success' : 'warning'}
        >
          {frozen ? 'Unfreeze Display' : 'Freeze Display'}
        </Button>
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
          {frozen
            ? 'Display is frozen. Click to resume updates.'
            : 'Display is updating in real-time. Click to pause.'}
        </Typography>
      </Box>

      <Divider />

      {/* Update Interval Slider */}
      <Box>
        <Typography variant="subtitle2" gutterBottom>
          Update Interval: {updateInterval}s
        </Typography>
        <Slider
          value={updateInterval}
          onChange={handleSliderChange}
          min={1}
          max={30}
          step={1}
          marks={[
            { value: 1, label: '1s' },
            { value: 10, label: '10s' },
            { value: 20, label: '20s' },
            { value: 30, label: '30s' },
          ]}
          valueLabelDisplay="auto"
          disabled={frozen}
        />
        <Typography variant="caption" color="text.secondary">
          Controls how often AI responses are generated
        </Typography>
      </Box>

      <Divider />

      {/* Clear Context Button */}
      <Box>
        <Typography variant="subtitle2" gutterBottom>
          Context Management
        </Typography>
        <Button
          variant="outlined"
          fullWidth
          startIcon={<Delete />}
          onClick={onClearContext}
          color="error"
        >
          Clear Context
        </Button>
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
          Clears all transcripts and responses
        </Typography>
      </Box>
    </Stack>
  );
}
