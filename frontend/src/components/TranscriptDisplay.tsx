/**
 * TranscriptDisplay component
 * Displays real-time transcription results from audio input
 * Requirements: 1.2
 */

import { Box, Typography, Chip, Divider, Stack } from '@mui/material';
import { MicNone, VolumeUp } from '@mui/icons-material';
import type { TranscriptData } from '../types';

interface TranscriptDisplayProps {
  transcripts: TranscriptData[];
  frozen?: boolean;
}

export function TranscriptDisplay({ transcripts, frozen = false }: TranscriptDisplayProps) {
  return (
    <Box>
      {frozen && (
        <Chip
          label="Display Frozen"
          color="warning"
          size="small"
          sx={{ mb: 2 }}
        />
      )}
      
      {transcripts.length === 0 ? (
        <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
          No transcripts yet. Start recording to see transcriptions appear here.
        </Typography>
      ) : (
        <Stack spacing={2} sx={{ maxHeight: '400px', overflowY: 'auto' }}>
          {transcripts.map((transcript) => (
            <Box key={transcript.id}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                {transcript.source === 'microphone' ? (
                  <MicNone fontSize="small" color="primary" />
                ) : (
                  <VolumeUp fontSize="small" color="secondary" />
                )}
                <Typography variant="caption" color="text.secondary">
                  {new Date(transcript.timestamp).toLocaleTimeString()}
                </Typography>
                <Chip
                  label={transcript.source}
                  size="small"
                  variant="outlined"
                  sx={{ height: '20px', fontSize: '0.7rem' }}
                />
                <Typography variant="caption" color="text.secondary">
                  Confidence: {(transcript.confidence * 100).toFixed(0)}%
                </Typography>
              </Box>
              <Typography variant="body1" sx={{ pl: 3 }}>
                {transcript.text}
              </Typography>
              <Divider sx={{ mt: 1 }} />
            </Box>
          ))}
        </Stack>
      )}
    </Box>
  );
}
