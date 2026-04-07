/**
 * Main application component
 * Implements correct hooks integration for real-time data
 * Requirements: 1.1
 */

import { useState, useEffect } from 'react';
import * as React from 'react';
import { ThemeProvider, CssBaseline, Box, Container, AppBar, Toolbar, Typography, Grid, Paper, Stack, Alert, AlertTitle } from '@mui/material';
import { theme } from './theme/theme';
import {
  TranscriptDisplay,
  ResponseDisplay,
  ControlPanel,
  ProviderSelector,
  StatusIndicator,
  AudioDeviceSelector,
} from './components';
import type { TranscriptData, ResponseData, SystemStatus } from './types';
import { useTranscript } from './hooks';
import { useResponse } from './hooks';
import { useAudioRecording } from './hooks';
import { useAppStore } from './store/appStore';

// Check if we're in Tauri environment by trying to access invoke directly
const checkTauriEnvironment = (): boolean => {
  try {
    // Try to access Tauri's internal API
    // This is more reliable than checking __TAURI_INTERNALS__
    if (typeof window !== 'undefined' && (window as any).__TAURI__) {
      return true;
    }
    return false;
  } catch (error) {
    console.warn('[TauriEnv] Error checking environment:', error);
    return false;
  }
};

const IS_TAURI_ENV = checkTauriEnvironment();

function App() {
  // Tauri environment check with delay to allow Tauri to initialize
  useEffect(() => {
    // Check again after component mounts
    const isTauri = checkTauriEnvironment();

    if (!isTauri) {
      console.warn('========================================');
      console.warn('⚠️  NOT RUNNING IN TAURI ENVIRONMENT');
      console.warn('========================================');
      console.warn('Your application is running in a web browser.');
      console.warn('Tauri features (invoke, listen) will NOT work.');
      console.warn('');
      console.warn('To run with Tauri:');
      console.warn('  1. Use: ./dev.sh dev');
      console.warn('  2. Or: cd src-tauri && cargo tauri dev');
      console.warn('========================================');
    } else {
      console.log('[TauriEnv] ✓ Tauri environment detected - Run #', Date.now());
    }
  }, []);

  // ✅ 使用 useTranscript hook（自动加载和监听）
  const {
    transcripts,
    isLoading: isLoadingTranscript,
    isListening: isListeningTranscript,
    error: transcriptError,
    loadTranscript: reloadTranscript
  } = useTranscript({
    autoLoad: IS_TAURI_ENV,  // 只在 Tauri 环境中自动加载
    autoListen: IS_TAURI_ENV,  // 只在 Tauri 环境中自动监听
    onTranscriptUpdate: (transcript) => {
      console.log('🎉 新 transcript:', transcript.text);
    },
    onError: (err) => {
      if (IS_TAURI_ENV) {
        console.error('❌ Transcript 错误:', err);
      } else {
        console.warn('Skipping transcript error (not in Tauri environment):', err);
      }
    }
  });

  // ✅ 使用 useResponse hook
  const {
    responses,
    isLoading: isLoadingResponse,
    generate,
    clearResponses: clearResponsesData
  } = useResponse({
    autoListen: true,
    onResponseUpdate: (response) => {
      console.log('🤖 AI 响应:', response.text);
    }
  });

  // ✅ 使用 useAudioRecording hook
  const {
    isRecording,
    isLoadingDevices,
    startRecording,
    stopRecording,
    devices,
    loadDevices,
    selectDevice,
    selectedMicId,
    selectedSpeakerId,
    error: recordingError
  } = useAudioRecording({
    enableVisualization: false,
    onRecordingStart: (deviceType) => {
      console.log(`🎤 开始录音: ${deviceType}`);
      setStatus({ state: 'recording', message: `Recording from ${deviceType}` });
    },
    onRecordingStop: () => {
      console.log('⏹️ 停止录音');
      setStatus({ state: 'idle', message: 'Recording stopped' });
    },
    onError: (error) => {
      console.error('❌ 录音错误:', error);
      setStatus({ state: 'error', message: `Recording error: ${error.message}` });
    }
  });

  // ✅ 从 Zustand store 获取状态
  const [status, setStatus] = useState<SystemStatus>({
    state: 'idle',
    message: 'System is ready',
  });

  // ✅ 自动启动录音（实时语音转录应用）
  // 使用 ref 来跟踪是否已经尝试启动录音，避免重复启动
  const hasAttemptedStart = React.useRef(false);
  
  useEffect(() => {
    if (IS_TAURI_ENV && !isRecording && !hasAttemptedStart.current) {
      console.log('🎤 自动启动录音（实时语音转录）...');
      hasAttemptedStart.current = true;
      startRecording('microphone').catch((error) => {
        console.error('Failed to auto-start recording:', error);
        hasAttemptedStart.current = false; // 允许重试
      });
    }
    // 注意：不要将startRecording放入依赖数组，否则会导致无限循环
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [IS_TAURI_ENV, isRecording]);

  // ✅ 使用 store 的 clear 方法
  const clearAllData = () => {
    const clearTranscripts = useAppStore(state => state.clearTranscripts);
    const clearResponses = useAppStore(state => state.clearResponses);
    clearTranscripts();
    clearResponses();
    console.log('🗑️ 已清空所有数据');
  };

  const [frozen, setFrozen] = useState(false);
  const [updateInterval, setUpdateInterval] = useState(5);
  const [currentProvider, setCurrentProvider] = useState('DeepSeek');
  const [currentModel, setCurrentModel] = useState('deepseek-chat');

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

  // ✅ 正确的清空上下文处理
  const handleClearContext = () => {
    clearAllData();
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
        {/* Tauri Environment Warning */}
        {!IS_TAURI_ENV && (
          <Alert severity="warning" sx={{ borderRadius: 0 }}>
            <AlertTitle>⚠️ Not Running in Tauri Environment</AlertTitle>
            <Typography variant="body2">
              Your application appears to be running in a web browser.
              Real-time transcript and AI response features require Tauri.
            </Typography>
            <Typography variant="body2" sx={{ mt: 1, fontWeight: 'bold' }}>
              Please run with Tauri:
            </Typography>
            <Typography variant="body2" component="code" sx={{ display: 'block', mt: 1 }}>
              ./dev.sh dev
            </Typography>
            <Typography variant="body2" component="code" sx={{ display: 'block', mt: 0.5 }}>
              npm run tauri dev
            </Typography>
          </Alert>
        )}

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
                    <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
                      <Typography variant="h6" gutterBottom>
                        Transcript
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {isListeningTranscript ? '🔵 Listening' : '⏸️ Not Listening'}
                        {isLoadingTranscript ? '⏳ Loading...' : ''}
                        {transcriptError && '⚠️ Error'}
                      </Typography>
                    </Stack>
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
                       onToggleFreeze={() => setFrozen(!frozen)}
                       onUpdateIntervalChange={setUpdateInterval}
                       onClearContext={clearAllData}
                     />
                     <Box sx={{ mt: 2 }}>
                       <AudioDeviceSelector
                         devices={devices}
                         isLoadingDevices={isLoadingDevices}
                         selectedMicId={selectedMicId}
                         selectedSpeakerId={selectedSpeakerId}
                         loadDevices={loadDevices}
                         selectDevice={selectDevice}
                       />
                     </Box>
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

                {/* Debug Info - 可以在生产环境删除 */}
                <Grid size={{ xs: 12 }}>
                  <Paper elevation={2} sx={{ p: 3 }}>
                    <Typography variant="h6" gutterBottom>
                      Debug Info
                    </Typography>
                    <Stack spacing={1}>
                      <Typography variant="caption">
                        Transcript 数量: {transcripts.length}
                      </Typography>
                      <Typography variant="caption">
                        Response 数量: {responses.length}
                      </Typography>
                      <Typography variant="caption">
                        最新 Transcript: {transcripts.length > 0 ? transcripts[transcripts.length - 1].text.substring(0, 50) + '...' : '无'}
                      </Typography>
                    </Stack>
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