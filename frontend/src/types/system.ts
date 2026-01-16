// System resource types for Tauri commands

// File service types
export interface FileOperationResult {
  success: boolean;
  message: string;
  path?: string;
}

export interface FileMetadata {
  path: string;
  size: number;
  is_file: boolean;
  is_dir: boolean;
  modified?: string;  // ISO 8601 timestamp
  created?: string;   // ISO 8601 timestamp
}

// System information types (detailed)
export interface DetailedSystemInfo {
  os: string;              // "windows", "macos", "linux"
  os_version: string;      // OS version string
  arch: string;            // "x86_64", "aarch64", etc.
  hostname: string;        // Computer hostname
  cpu_count: number;       // Number of CPU cores
  total_memory: number;    // Total RAM in bytes
  available_memory: number; // Available RAM in bytes
  uptime: number;          // System uptime in seconds
}

export interface DetailedAudioDevice {
  id: string;
  name: string;
  device_type: string;     // "input" or "output"
  is_default: boolean;
  sample_rate?: number;
  channels?: number;
}

export interface NetworkInterface {
  name: string;
  mac_address?: string;
  ip_addresses: string[];
  is_up: boolean;
  is_loopback: boolean;
}

export interface DiskInfo {
  name: string;
  mount_point: string;
  total_space: number;
  available_space: number;
  file_system: string;
}
