// System resource service for Tauri commands
import { invoke } from '@tauri-apps/api/tauri';
import type {
  FileOperationResult,
  FileMetadata,
  DetailedSystemInfo,
  DetailedAudioDevice,
  NetworkInterface,
  DiskInfo,
} from '../types/system';

/**
 * File Service - Secure file operations
 */
export class FileService {
  /**
   * Read file contents as string
   */
  static async readFile(path: string): Promise<string> {
    return invoke<string>('read_file', { path });
  }

  /**
   * Write string contents to file
   */
  static async writeFile(path: string, contents: string): Promise<FileOperationResult> {
    return invoke<FileOperationResult>('write_file', { path, contents });
  }

  /**
   * Append string contents to file
   */
  static async appendFile(path: string, contents: string): Promise<FileOperationResult> {
    return invoke<FileOperationResult>('append_file', { path, contents });
  }

  /**
   * Delete a file
   */
  static async deleteFile(path: string): Promise<FileOperationResult> {
    return invoke<FileOperationResult>('delete_file', { path });
  }

  /**
   * Check if file exists
   */
  static async fileExists(path: string): Promise<boolean> {
    return invoke<boolean>('file_exists', { path });
  }

  /**
   * Get file metadata
   */
  static async getFileMetadata(path: string): Promise<FileMetadata> {
    return invoke<FileMetadata>('get_file_metadata', { path });
  }

  /**
   * List files in a directory
   */
  static async listDirectory(path: string): Promise<FileMetadata[]> {
    return invoke<FileMetadata[]>('list_directory', { path });
  }

  /**
   * Create a directory
   */
  static async createDirectory(path: string): Promise<FileOperationResult> {
    return invoke<FileOperationResult>('create_directory', { path });
  }

  /**
   * Delete a directory
   */
  static async deleteDirectory(path: string, recursive: boolean = false): Promise<FileOperationResult> {
    return invoke<FileOperationResult>('delete_directory', { path, recursive });
  }
}

/**
 * System Service - System information and device enumeration
 */
export class SystemService {
  /**
   * Get comprehensive system information
   */
  static async getSystemInformation(): Promise<DetailedSystemInfo> {
    return invoke<DetailedSystemInfo>('get_system_information');
  }

  /**
   * Get list of audio devices
   */
  static async getAudioDeviceList(): Promise<DetailedAudioDevice[]> {
    return invoke<DetailedAudioDevice[]>('get_audio_device_list');
  }

  /**
   * Get network interfaces
   */
  static async getNetworkInterfaces(): Promise<NetworkInterface[]> {
    return invoke<NetworkInterface[]>('get_network_interfaces');
  }

  /**
   * Get disk information
   */
  static async getDiskInformation(): Promise<DiskInfo[]> {
    return invoke<DiskInfo[]>('get_disk_information');
  }

  /**
   * Get environment variables (filtered for security)
   */
  static async getEnvironmentVariables(filter?: string[]): Promise<Record<string, string>> {
    return invoke<Record<string, string>>('get_environment_variables', { filter });
  }

  /**
   * Get current working directory
   */
  static async getCurrentDirectory(): Promise<string> {
    return invoke<string>('get_current_directory');
  }

  /**
   * Get system locale
   */
  static async getSystemLocale(): Promise<string> {
    return invoke<string>('get_system_locale');
  }
}

/**
 * Utility functions for system resources
 */
export class SystemUtils {
  /**
   * Format bytes to human-readable string
   */
  static formatBytes(bytes: number, decimals: number = 2): string {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB'];

    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  }

  /**
   * Format uptime to human-readable string
   */
  static formatUptime(seconds: number): string {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    const parts: string[] = [];
    if (days > 0) parts.push(`${days}d`);
    if (hours > 0) parts.push(`${hours}h`);
    if (minutes > 0) parts.push(`${minutes}m`);

    return parts.join(' ') || '0m';
  }

  /**
   * Get OS display name
   */
  static getOSDisplayName(os: string): string {
    const osMap: Record<string, string> = {
      'windows': 'Windows',
      'macos': 'macOS',
      'linux': 'Linux',
      'darwin': 'macOS',
    };

    return osMap[os.toLowerCase()] || os;
  }
}
