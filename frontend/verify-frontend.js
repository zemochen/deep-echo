/**
 * Frontend Verification Script
 * Verifies that all components, services, and state management are properly set up
 */

import { readFileSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// ANSI color codes
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function checkFile(path, description) {
  const fullPath = join(__dirname, path);
  if (existsSync(fullPath)) {
    log(`✓ ${description}`, 'green');
    return true;
  } else {
    log(`✗ ${description} - File not found: ${path}`, 'red');
    return false;
  }
}

function checkImport(filePath, importName, description) {
  const fullPath = join(__dirname, filePath);
  if (!existsSync(fullPath)) {
    log(`✗ ${description} - File not found: ${filePath}`, 'red');
    return false;
  }

  const content = readFileSync(fullPath, 'utf-8');
  if (content.includes(importName)) {
    log(`✓ ${description}`, 'green');
    return true;
  } else {
    log(`✗ ${description} - Import not found: ${importName}`, 'red');
    return false;
  }
}

function main() {
  log('\n=== Frontend Verification ===\n', 'cyan');

  let allPassed = true;

  // Check Components
  log('Checking Components:', 'blue');
  allPassed &= checkFile('src/components/TranscriptDisplay.tsx', 'TranscriptDisplay component');
  allPassed &= checkFile('src/components/ResponseDisplay.tsx', 'ResponseDisplay component');
  allPassed &= checkFile('src/components/ControlPanel.tsx', 'ControlPanel component');
  allPassed &= checkFile('src/components/ProviderSelector.tsx', 'ProviderSelector component');
  allPassed &= checkFile('src/components/StatusIndicator.tsx', 'StatusIndicator component');
  allPassed &= checkFile('src/components/index.ts', 'Component exports');

  log('\nChecking Services:', 'blue');
  allPassed &= checkFile('src/services/tauriService.ts', 'Tauri service');
  allPassed &= checkFile('src/services/audioService.ts', 'Audio service');
  allPassed &= checkFile('src/services/eventService.ts', 'Event service');
  allPassed &= checkFile('src/services/index.ts', 'Service exports');

  log('\nChecking State Management:', 'blue');
  allPassed &= checkFile('src/store/appStore.ts', 'App store');
  allPassed &= checkFile('src/store/uiStore.ts', 'UI store');
  allPassed &= checkFile('src/store/index.ts', 'Store exports');

  log('\nChecking Hooks:', 'blue');
  allPassed &= checkFile('src/hooks/useAudioRecording.ts', 'Audio recording hook');
  allPassed &= checkFile('src/hooks/useTranscript.ts', 'Transcript hook');
  allPassed &= checkFile('src/hooks/useResponse.ts', 'Response hook');
  allPassed &= checkFile('src/hooks/useTauriCommand.ts', 'Tauri command hook');
  allPassed &= checkFile('src/hooks/index.ts', 'Hook exports');

  log('\nChecking Types:', 'blue');
  allPassed &= checkFile('src/types/api.ts', 'API types');
  allPassed &= checkFile('src/types/audio.ts', 'Audio types');
  allPassed &= checkFile('src/types/ui.ts', 'UI types');
  allPassed &= checkFile('src/types/commands.ts', 'Command types');
  allPassed &= checkFile('src/types/events.ts', 'Event types');
  allPassed &= checkFile('src/types/index.ts', 'Type exports');

  log('\nChecking Theme:', 'blue');
  allPassed &= checkFile('src/theme/theme.ts', 'Theme configuration');
  allPassed &= checkFile('src/theme/colors.ts', 'Color definitions');

  log('\nChecking Main Files:', 'blue');
  allPassed &= checkFile('src/App.tsx', 'Main App component');
  allPassed &= checkFile('src/main.tsx', 'Application entry point');

  log('\nChecking App.tsx Integration:', 'blue');
  allPassed &= checkImport('src/App.tsx', 'TranscriptDisplay', 'TranscriptDisplay import');
  allPassed &= checkImport('src/App.tsx', 'ResponseDisplay', 'ResponseDisplay import');
  allPassed &= checkImport('src/App.tsx', 'ControlPanel', 'ControlPanel import');
  allPassed &= checkImport('src/App.tsx', 'ProviderSelector', 'ProviderSelector import');
  allPassed &= checkImport('src/App.tsx', 'StatusIndicator', 'StatusIndicator import');
  allPassed &= checkImport('src/App.tsx', 'ThemeProvider', 'ThemeProvider import');

  log('\nChecking Store Integration:', 'blue');
  allPassed &= checkImport('src/hooks/useTranscript.ts', 'useAppStore', 'useAppStore in useTranscript');
  allPassed &= checkImport('src/hooks/useResponse.ts', 'useAppStore', 'useAppStore in useResponse');

  log('\nChecking Tauri Integration:', 'blue');
  allPassed &= checkImport('src/services/tauriService.ts', '@tauri-apps/api/core', 'Tauri API import');
  allPassed &= checkImport('src/hooks/useTauriCommand.ts', '@tauri-apps/api/core', 'Tauri API in hook');

  log('\n=== Verification Summary ===\n', 'cyan');

  if (allPassed) {
    log('✓ All checks passed! Frontend is properly configured.', 'green');
    process.exit(0);
  } else {
    log('✗ Some checks failed. Please review the errors above.', 'red');
    process.exit(1);
  }
}

main();
