/**
 * Main application component
 * Implements the main layout structure with header, content areas, and control panel
 * Requirements: 1.1
 */

import { useState } from 'react';
import { ThemeProvider, CssBaseline, Box, Container, AppBar, Toolbar, Typography, Grid, Paper } from '@mui/material';
import { theme } from './theme/theme';
import {
  TranscriptDisplay,
  ResponseDisplay,
  ControlPanel,
  ProviderSelector,
  StatusIndicator,
} from './components';
import type { TranscriptData, ResponseData, SystemStatus } from './types';

function App() {
  // Mock state for demonstration
  const [transcripts] = useState<TranscriptData[]>([
    {
      id: '1',
      timestamp: Date.now() - 5000,
      source: 'microphone',
      text: 'Hello, this is a test transcript from the microphone.',
      confidence: 0.95,
    },
    {
      id: '2',
      timestamp: Date.now() - 3000,
      source: 'speaker',
      text: 'This is a response from the speaker output.',
      confidence: 0.92,
    },
  ]);

  const [responses] = useState<ResponseData[]>([
    {
      id: '1',
      timestamp: Date.now() - 4000,
      provider: 'OpenAI',
      text: 'This is a sample AI response. The system is working correctly and processing your input.',
      context: 'Sample context for the response',
    },
  ]);

  const [frozen, setFrozen] = useState(false);
  const [updateInterval, setUpdateInterval] = useState(5);
  const [currentProvider, setCurrentProvider] = useState('OpenAI');
  const [currentModel, setCurrentModel] = useState('gpt-4');

  const [status] = useState<SystemStatus>({
    state: 'idle',
    message: 'System is ready and waiting for input',
    details: {
      uptime: '5 minutes',
      lastUpdate: new Date().toLocaleTimeString(),
    },
  });

  const availableProviders = ['OpenAI', 'Claude', 'DeepSeek', 'GLM', 'Grok'];
  const availableModels: Record<string, string[]> = {
    OpenAI: ['gpt-4', 'gpt-3.5-turbo'],
    Claude: ['claude-3-opus', 'claude-3-sonnet'],
    DeepSeek: ['deepseek-chat'],
    GLM: ['glm-4'],
    Grok: ['grok-1'],
  };

  const handleToggleFreeze = () => {
    setFrozen(!frozen);
  };

  const handleUpdateIntervalChange = (value: number) => {
    setUpdateInterval(value);
  };

  const handleClearContext = () => {
    console.log('Clear context clicked');
    // Will be implemented with actual state management
  };

  const handleProviderChange = (provider: string) => {
    setCurrentProvider(provider);
  };

  const handleModelChange = (model: string) => {
    setCurrentModel(model);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box
        sx={{
          minHeight: '100vh',
          bgcolor: 'background.default',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Header */}
        <AppBar position="static" elevation={1}>
          <Toolbar>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              DeepEcho - Real-time Voice AI Assistant
            </Typography>
          </Toolbar>
        </AppBar>

        {/* Main Content */}
        <Container maxWidth="xl" sx={{ py: 3, flex: 1 }}>
          <Grid container spacing={3}>
            {/* Left Column - Transcript and Response Display */}
            <Grid size={{ xs: 12, md: 8 }}>
              <Grid container spacing={3}>
                {/* Transcript Display Area */}
                <Grid size={{ xs: 12 }}>
                  <Paper elevation={2} sx={{ p: 3, minHeight: '300px' }}>
                    <Typography variant="h6" gutterBottom>
                      Transcript
                    </Typography>
                    <TranscriptDisplay transcripts={transcripts} frozen={frozen} />
                  </Paper>
                </Grid>

                {/* Response Display Area */}
                <Grid size={{ xs: 12 }}>
                  <Paper elevation={2} sx={{ p: 3, minHeight: '300px' }}>
                    <Typography variant="h6" gutterBottom>
                      AI Response
                    </Typography>
                    <ResponseDisplay responses={responses} frozen={frozen} />
                  </Paper>
                </Grid>
              </Grid>
            </Grid>

            {/* Right Column - Control Panel and Status */}
            <Grid size={{ xs: 12, md: 4 }}>
              <Grid container spacing={3}>
                {/* Status Indicator */}
                <Grid size={{ xs: 12 }}>
                  <Paper elevation={2} sx={{ p: 3 }}>
                    <Typography variant="h6" gutterBottom>
                      Status
                    </Typography>
                    <StatusIndicator status={status} />
                  </Paper>
                </Grid>

                {/* Control Panel */}
                <Grid size={{ xs: 12 }}>
                  <Paper elevation={2} sx={{ p: 3 }}>
                    <Typography variant="h6" gutterBottom>
                      Controls
                    </Typography>
                    <ControlPanel
                      frozen={frozen}
                      updateInterval={updateInterval}
                      onToggleFreeze={handleToggleFreeze}
                      onUpdateIntervalChange={handleUpdateIntervalChange}
                      onClearContext={handleClearContext}
                    />
                  </Paper>
                </Grid>

                {/* AI Provider Selector */}
                <Grid size={{ xs: 12 }}>
                  <Paper elevation={2} sx={{ p: 3 }}>
                    <Typography variant="h6" gutterBottom>
                      AI Provider
                    </Typography>
                    <ProviderSelector
                      currentProvider={currentProvider}
                      currentModel={currentModel}
                      availableProviders={availableProviders}
                      availableModels={availableModels}
                      onProviderChange={handleProviderChange}
                      onModelChange={handleModelChange}
                    />
                  </Paper>
                </Grid>
              </Grid>
            </Grid>
          </Grid>
        </Container>
      </Box>
    </ThemeProvider>
  );
}

export default App;
