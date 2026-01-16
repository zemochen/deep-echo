# DeepEcho Frontend

React + TypeScript + Material-UI frontend for the DeepEcho real-time voice AI assistant.

## Technology Stack

- **React 19** - UI framework
- **TypeScript** - Type safety
- **Material-UI (MUI)** - Component library
- **Zustand** - State management
- **Vite** - Build tool
- **Tauri API** - Backend communication

## Project Structure

```
src/
├── components/       # React UI components
├── hooks/           # Custom React hooks
├── services/        # Service layer (Tauri, Audio, Events)
├── store/           # Zustand state stores
├── types/           # TypeScript type definitions
├── theme/           # Material-UI theme configuration
├── App.tsx          # Main application component
└── main.tsx         # Application entry point
```

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Tauri CLI (for integration with backend)

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

This will start the Vite development server at `http://localhost:5173/`.

### Build

```bash
npm run build
```

This will create an optimized production build in the `dist/` directory.

### Lint

```bash
npm run lint
```

## State Management

The application uses Zustand for state management with two main stores:

- **appStore** - Application data (transcripts, responses, status, config)
- **uiStore** - UI state (theme, frozen state, notifications) with persistence

## Theme

The application uses Material-UI's theming system with support for both light and dark modes. Theme configuration is located in `src/theme/`.

## Integration with Tauri

The frontend communicates with the Python backend through Tauri commands. The Tauri API is used for:

- Invoking backend commands
- Listening to backend events
- Accessing system resources

## Next Steps

1. Implement UI components (TranscriptDisplay, ResponseDisplay, ControlPanel, etc.)
2. Implement custom hooks for audio recording, transcripts, and responses
3. Implement service layer for Tauri commands and event handling
4. Connect components to state stores
5. Integrate with Tauri backend

## License

See the main project LICENSE file.
