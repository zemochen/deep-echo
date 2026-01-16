# Frontend Hooks

This directory contains custom React hooks for the DeepEcho frontend application.

## Available Hooks

### 1. useAudioRecording

**Purpose**: Manages audio recording state and provides recording controls.

**Features**:
- Start/stop recording from microphone or speaker
- Device enumeration and selection
- Web Audio API integration for microphone access
- Audio visualization data
- Error handling

**Usage**:
```tsx
import { useAudioRecording } from './hooks';

function AudioRecorder() {
  const {
    isRecording,
    startRecording,
    stopRecording,
    devices,
    loadDevices,
  } = useAudioRecording({
    onRecordingStart: (type) => console.log(`Recording started: ${type}`),
    onError: (error) => console.error(error),
  });

  return (
    <button onClick={() => startRecording('microphone')}>
      {isRecording ? 'Stop' : 'Start'} Recording
    </button>
  );
}
```

**Requirements**: 5.1-5.6

---

### 2. useTranscript

**Purpose**: Manages transcript data and real-time updates from backend.

**Features**:
- Real-time transcript updates via events
- Transcript history management
- Filtering by source (microphone/speaker)
- Integration with app store
- Auto-load and auto-listen options

**Usage**:
```tsx
import { useTranscript } from './hooks';

function TranscriptViewer() {
  const {
    transcripts,
    latestTranscript,
    isLoading,
  } = useTranscript({
    filterBySource: 'microphone',
    onTranscriptUpdate: (transcript) => {
      console.log('New transcript:', transcript.text);
    },
  });

  return (
    <div>
      {transcripts.map(t => (
        <div key={t.id}>{t.text}</div>
      ))}
    </div>
  );
}
```

**Requirements**: 1.2

---

### 3. useResponse

**Purpose**: Manages AI response data and real-time updates from backend.

**Features**:
- Real-time response updates via events
- Response generation control
- Response history management
- Filtering by provider
- Integration with app store

**Usage**:
```tsx
import { useResponse } from './hooks';

function ResponseViewer() {
  const {
    responses,
    latestResponse,
    isGenerating,
    generate,
  } = useResponse({
    onResponseUpdate: (response) => {
      console.log('New response:', response.text);
    },
  });

  return (
    <div>
      <button
        onClick={() => generate('Hello, AI!')}
        disabled={isGenerating}
      >
        Generate Response
      </button>
      {responses.map(r => (
        <div key={r.id}>{r.text}</div>
      ))}
    </div>
  );
}
```

**Requirements**: 1.3

---

### 4. useTauriCommand

**Purpose**: Generic hook for executing Tauri commands with state management and error handling.

**Features**:
- Command execution with loading state
- Error handling and retry logic
- Success/error callbacks
- Execution tracking
- Type-safe command parameters and results

**Usage**:
```tsx
import { useTauriCommand } from './hooks';

// Simple usage
function MyComponent() {
  const { data, isLoading, execute } = useTauriCommand<string>({
    command: 'get_system_info',
  });

  return (
    <button onClick={() => execute()} disabled={isLoading}>
      {isLoading ? 'Loading...' : 'Get Info'}
    </button>
  );
}

// With parameters and callbacks
function RecordingControl() {
  const { isLoading, execute } = useTauriCommand<string, { deviceType: string }>({
    command: 'start_recording',
    onSuccess: (result) => console.log('Recording started:', result),
    onError: (error) => console.error('Failed to start:', error),
  });

  return (
    <button
      onClick={() => execute({ deviceType: 'microphone' })}
      disabled={isLoading}
    >
      Start Recording
    </button>
  );
}

// With retry logic
function RobustCommand() {
  const { data, error, execute } = useTauriCommand<ConfigData>({
    command: 'get_config',
    retry: true,
    retryAttempts: 3,
    retryDelay: 1000,
  });

  return <div>{data ? 'Success' : error ? 'Failed' : 'Idle'}</div>;
}
```

**Specialized Variants**:
- `useSimpleTauriCommand`: For commands without parameters
- `useImmediateTauriCommand`: For commands that execute on mount
- `useRetryableTauriCommand`: For commands with automatic retry

**Requirements**: 3.1-3.8

---

## Architecture

All hooks follow these principles:

1. **State Management**: Use React hooks (useState, useEffect, useCallback) for local state
2. **Global State**: Integrate with Zustand store (appStore) for shared state
3. **Services**: Use service layer (tauriService, audioService, eventService) for backend communication
4. **Error Handling**: Provide error state and error callbacks
5. **Type Safety**: Full TypeScript support with proper types
6. **Cleanup**: Proper cleanup in useEffect to prevent memory leaks
7. **Callbacks**: Support for lifecycle callbacks (onSuccess, onError, etc.)

## Dependencies

- React 18+
- Zustand (state management)
- Tauri API (@tauri-apps/api)
- Services layer (tauriService, audioService, eventService)
- Type definitions (types/api.ts, types/events.ts, types/audio.ts)

## Testing

Each hook should be tested with:
- Unit tests for state management logic
- Integration tests with services
- Error handling scenarios
- Cleanup behavior

## Next Steps

These hooks can now be used in React components to:
1. Control audio recording (Task 9.1 ✓)
2. Display real-time transcripts (Task 9.2 ✓)
3. Display AI responses (Task 9.3 ✓)
4. Execute Tauri commands (Task 9.4 ✓)

The next task (Task 10) is to verify all frontend functionality works correctly.
