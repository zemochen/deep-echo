/**
 * ResponseDisplay component
 * Displays AI-generated responses in real-time
 * Requirements: 1.3
 */

import { Box, Typography, Chip, Stack, Paper } from '@mui/material';
import { SmartToy } from '@mui/icons-material';
import type { ResponseData } from '../types';

interface ResponseDisplayProps {
  responses: ResponseData[];
  frozen?: boolean;
}

export function ResponseDisplay({ responses, frozen = false }: ResponseDisplayProps) {
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
      
      {responses.length === 0 ? (
        <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
          No AI responses yet. Responses will appear here as they are generated.
        </Typography>
      ) : (
        <Stack spacing={2} sx={{ maxHeight: '400px', overflowY: 'auto' }}>
          {responses.map((response) => (
            <Paper
              key={response.id}
              elevation={1}
              sx={{
                p: 2,
                bgcolor: 'background.paper',
                borderLeft: 3,
                borderColor: 'primary.main',
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <SmartToy fontSize="small" color="primary" />
                <Typography variant="caption" color="text.secondary">
                  {new Date(response.timestamp).toLocaleTimeString()}
                </Typography>
                <Chip
                  label={response.provider}
                  size="small"
                  color="primary"
                  variant="outlined"
                  sx={{ height: '20px', fontSize: '0.7rem' }}
                />
              </Box>
              <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                {response.text}
              </Typography>
              {response.context && (
                <Box sx={{ mt: 1, pt: 1, borderTop: 1, borderColor: 'divider' }}>
                  <Typography variant="caption" color="text.secondary">
                    Context: {response.context.substring(0, 100)}
                    {response.context.length > 100 ? '...' : ''}
                  </Typography>
                </Box>
              )}
            </Paper>
          ))}
        </Stack>
      )}
    </Box>
  );
}
