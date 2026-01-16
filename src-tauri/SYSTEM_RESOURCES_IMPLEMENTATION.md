# System Resources Implementation

This document describes the implementation of system resource access services in the Tauri layer.

## Overview

The system resources implementation provides secure file operations and system information retrieval through two main services:

1. **File Service**: Secure file operations with path validation
2. **System Service**: System information and device enumeration

## Architecture

```
Frontend (TypeScript)
    ↓ invoke Tauri commands
Tauri Commands (Rust)
    ↓ use services
File Service / System Service
    ↓ access system resources
Operating System
```

## File Service

### Purpose

Provides secure file operations with path validation to prevent unauthorized access to system files.

### Security Model

- **Allowed Directories**: Only files within specified directories can be accessed
- **Path Validation**: All paths are canonicalized and checked against allowed directories
- **Automatic Directory Creation**: Parent directories are created automatically when writing files

### Allowed Directories

By default, the file service allows access to:
- App Data Directory (`~/.local/share/deepecho` on Linux/macOS, `%APPDATA%\deepecho` on Windows)
- App Config Directory (`~/.config/deepecho` on Linux/macOS, `%APPDATA%\deepecho` on Windows)
- App Log Directory (`~/.local/share/deepecho/logs` on Linux/macOS, `%APPDATA%\deepecho\logs` on Windows)

### Available Commands

#### File Operations

1. **read_file(path: string): Promise<string>**
   - Reads file contents as UTF-8 string
   - Throws error if file doesn't exist or is outside allowed directories

2. **write_file(path: string, contents: string): Promise<FileOperationResult>**
   - Writes string contents to file
   - Creates parent directories if needed
   - Overwrites existing file

3. **append_file(path: string, contents: string): Promise<FileOperationResult>**
   - Appends string contents to file
   - Creates file if it doesn't exist

4. **delete_file(path: string): Promise<FileOperationResult>**
   - Deletes a file
   - Throws error if path is a directory

5. **file_exists(path: string): Promise<boolean>**
   - Checks if file exists and is a file (not a directory)

6. **get_file_metadata(path: string): Promise<FileMetadata>**
   - Returns file metadata including size, timestamps, and type

#### Directory Operations

7. **list_directory(path: string): Promise<FileMetadata[]>**
   - Lists all files and subdirectories in a directory
   - Returns metadata for each entry

8. **create_directory(path: string): Promise<FileOperationResult>**
   - Creates a directory and all parent directories

9. **delete_directory(path: string, recursive: boolean): Promise<FileOperationResult>**
   - Deletes a directory
   - If recursive is true, deletes all contents

### Data Types

```typescript
interface FileOperationResult {
  success: boolean;
  message: string;
  path?: string;
}

interface FileMetadata {
  path: string;
  size: number;
  is_file: boolean;
  is_dir: boolean;
  modified?: string;  // ISO 8601 timestamp
  created?: string;   // ISO 8601 timestamp
}
```

### Usage Example

```typescript
import { invoke } from '@tauri-apps/api/tauri';

// Read configuration file
const config = await invoke<string>('read_file', {
  path: 'config.json'
});

// Write log file
await invoke<FileOperationResult>('write_file', {
  path: 'logs/app.log',
  contents: 'Application started\n'
});

// List directory contents
const files = await invoke<FileMetadata[]>('list_directory', {
  path: 'data'
});
```

## System Service

### Purpose

Provides system information and device enumeration capabilities.

### Available Commands

#### System Information

1. **get_system_information(): Promise<SystemInfo>**
   - Returns comprehensive system information
   - Includes OS, architecture, CPU, memory, and uptime

2. **get_current_directory(): Promise<string>**
   - Returns current working directory

3. **get_system_locale(): Promise<string>**
   - Returns system locale (e.g., "en_US.UTF-8")

4. **get_environment_variables(filter?: string[]): Promise<Record<string, string>>**
   - Returns environment variables
   - If filter is provided, only returns specified variables
   - Otherwise returns safe variables (PATH, HOME, USER, etc.)

#### Device Enumeration

5. **get_audio_device_list(): Promise<AudioDevice[]>**
   - Returns list of audio input and output devices
   - Note: Requires `audio-devices` feature flag

6. **get_network_interfaces(): Promise<NetworkInterface[]>**
   - Returns list of network interfaces with IP addresses

7. **get_disk_information(): Promise<DiskInfo[]>**
   - Returns disk information
   - Note: Currently returns empty list (to be implemented)

### Data Types

```typescript
interface SystemInfo {
  os: string;              // "windows", "macos", "linux"
  os_version: string;      // OS version string
  arch: string;            // "x86_64", "aarch64", etc.
  hostname: string;        // Computer hostname
  cpu_count: number;       // Number of CPU cores
  total_memory: number;    // Total RAM in bytes
  available_memory: number; // Available RAM in bytes
  uptime: number;          // System uptime in seconds
}

interface AudioDevice {
  id: string;
  name: string;
  device_type: string;     // "input" or "output"
  is_default: boolean;
  sample_rate?: number;
  channels?: number;
}

interface NetworkInterface {
  name: string;
  mac_address?: string;
  ip_addresses: string[];
  is_up: boolean;
  is_loopback: boolean;
}

interface DiskInfo {
  name: string;
  mount_point: string;
  total_space: number;
  available_space: number;
  file_system: string;
}
```

### Usage Example

```typescript
import { invoke } from '@tauri-apps/api/tauri';

// Get system information
const sysInfo = await invoke<SystemInfo>('get_system_information');
console.log(`Running on ${sysInfo.os} ${sysInfo.os_version}`);
console.log(`CPU cores: ${sysInfo.cpu_count}`);
console.log(`Memory: ${sysInfo.available_memory / 1024 / 1024 / 1024} GB available`);

// Get audio devices
const audioDevices = await invoke<AudioDevice[]>('get_audio_device_list');
const defaultMic = audioDevices.find(d => d.device_type === 'input' && d.is_default);
console.log(`Default microphone: ${defaultMic?.name}`);

// Get network interfaces
const interfaces = await invoke<NetworkInterface[]>('get_network_interfaces');
interfaces.forEach(iface => {
  console.log(`${iface.name}: ${iface.ip_addresses.join(', ')}`);
});
```

## Implementation Details

### File Service Implementation

Located in `src-tauri/src/services/file_service.rs`:

- Uses Rust's `std::fs` for file operations
- Path validation using `Path::canonicalize()`
- Automatic parent directory creation
- Comprehensive error handling with context

### System Service Implementation

Located in `src-tauri/src/services/system_service.rs`:

- Uses `sysinfo` crate for system information
- Uses `hostname` crate for hostname
- Uses `num_cpus` crate for CPU count
- Uses `pnet` crate for network interfaces
- Optional `cpal` crate for audio device enumeration

### Command Implementations

Located in:
- `src-tauri/src/commands/file.rs` - File service commands
- `src-tauri/src/commands/system_info.rs` - System service commands

### State Management

Both services use Tauri's state management:

```rust
// In main.rs
app.manage(FileServiceState::new(file_service));
app.manage(SystemServiceState::new(system_service));
```

Commands access state using:

```rust
#[tauri::command]
pub async fn read_file(
    path: String,
    state: State<'_, FileServiceState>,
) -> Result<String, String> {
    let service = state.service.lock().map_err(|e| e.to_string())?;
    service.read_file(&path).map_err(|e| e.to_string())
}
```

## Security Considerations

### File Service Security

1. **Path Validation**: All paths are validated against allowed directories
2. **Canonicalization**: Paths are canonicalized to prevent directory traversal attacks
3. **No Symlink Following**: Symlinks outside allowed directories are rejected
4. **Limited Scope**: Only app-specific directories are accessible by default

### System Service Security

1. **Environment Variables**: Only safe environment variables are exposed by default
2. **No Sensitive Data**: System information doesn't include sensitive data
3. **Read-Only**: All system information commands are read-only

## Testing

### File Service Tests

Located in `src-tauri/src/services/file_service.rs`:

```rust
#[test]
fn test_file_service_security() {
    // Tests path validation
}

#[test]
fn test_file_operations() {
    // Tests read, write, delete operations
}
```

### System Service Tests

Located in `src-tauri/src/services/system_service.rs`:

```rust
#[test]
fn test_get_system_info() {
    // Tests system information retrieval
}

#[test]
fn test_get_audio_devices() {
    // Tests audio device enumeration
}
```

## Dependencies

Added to `Cargo.toml`:

```toml
[dependencies]
sysinfo = "0.30"
hostname = "0.3"
num_cpus = "1.16"
pnet = "0.34"
cpal = { version = "0.15", optional = true }

[features]
audio-devices = ["cpal"]
```

## Future Enhancements

1. **Disk Information**: Implement platform-specific disk enumeration
2. **Audio Device Enumeration**: Enable `audio-devices` feature by default
3. **File Watching**: Add file system watching capabilities
4. **Process Management**: Add process enumeration and management
5. **System Metrics**: Add CPU usage, network traffic monitoring

## Requirements Validation

This implementation satisfies requirements 6.1-6.6:

- ✅ 6.1: File reading through Tauri file system API
- ✅ 6.2: File writing through Tauri file system API
- ✅ 6.3: Device enumeration through system service
- ✅ 6.4: System information through system service
- ✅ 6.5: File access permission control through path validation
- ✅ 6.6: Secure file path handling through canonicalization
