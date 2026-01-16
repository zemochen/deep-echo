// Python service management for frontend
import { invoke } from '@tauri-apps/api/core';
import type { ServiceStatus } from '../types/python-service';

/**
 * Python service management API
 */
export class PythonServiceAPI {
  /**
   * Start the Python backend service
   * @returns Success message
   * @throws Error if service fails to start
   */
  static async start(): Promise<string> {
    return await invoke<string>('start_python_service');
  }

  /**
   * Stop the Python backend service
   * @returns Success message
   * @throws Error if service fails to stop
   */
  static async stop(): Promise<string> {
    return await invoke<string>('stop_python_service');
  }

  /**
   * Restart the Python backend service
   * @returns Success message
   * @throws Error if service fails to restart
   */
  static async restart(): Promise<string> {
    return await invoke<string>('restart_python_service');
  }

  /**
   * Get the current status of the Python backend service
   * @returns Service status information
   */
  static async getStatus(): Promise<ServiceStatus> {
    return await invoke<ServiceStatus>('get_python_service_status');
  }

  /**
   * Start automatic monitoring of the Python backend service
   * @returns Success message
   * @throws Error if monitoring is already active
   */
  static async startMonitoring(): Promise<string> {
    return await invoke<string>('start_service_monitoring');
  }

  /**
   * Stop automatic monitoring of the Python backend service
   * @returns Success message
   * @throws Error if monitoring is not active
   */
  static async stopMonitoring(): Promise<string> {
    return await invoke<string>('stop_service_monitoring');
  }

  /**
   * Perform a manual health check on the Python backend service
   * @returns True if service is healthy, false otherwise
   */
  static async checkHealth(): Promise<boolean> {
    return await invoke<boolean>('check_service_health');
  }

  /**
   * Reset the restart counter for the Python backend service
   * @returns Success message
   */
  static async resetRestartCount(): Promise<string> {
    return await invoke<string>('reset_service_restart_count');
  }

  /**
   * Check if the service is running
   * @returns True if service is running, false otherwise
   */
  static async isRunning(): Promise<boolean> {
    const status = await this.getStatus();
    return status.is_running;
  }

  /**
   * Check if monitoring is active
   * @returns True if monitoring is active, false otherwise
   */
  static async isMonitoring(): Promise<boolean> {
    const status = await this.getStatus();
    return status.is_monitoring;
  }

  /**
   * Get the process ID of the running service
   * @returns Process ID if running, null otherwise
   */
  static async getPid(): Promise<number | null> {
    const status = await this.getStatus();
    return status.pid;
  }

  /**
   * Get the number of restart attempts
   * @returns Restart count
   */
  static async getRestartCount(): Promise<number> {
    const status = await this.getStatus();
    return status.restart_count;
  }

  /**
   * Wait for service to reach a specific state
   * @param targetState - The state to wait for
   * @param timeout - Maximum time to wait in milliseconds (default: 30000)
   * @param pollInterval - How often to check status in milliseconds (default: 500)
   * @returns True if state reached, false if timeout
   */
  static async waitForState(
    targetState: string,
    timeout: number = 30000,
    pollInterval: number = 500
  ): Promise<boolean> {
    const startTime = Date.now();
    
    while (Date.now() - startTime < timeout) {
      const status = await this.getStatus();
      if (status.state === targetState) {
        return true;
      }
      await new Promise(resolve => setTimeout(resolve, pollInterval));
    }
    
    return false;
  }

  /**
   * Ensure service is running, start if not
   * @returns True if service is running or was started successfully
   */
  static async ensureRunning(): Promise<boolean> {
    try {
      const status = await this.getStatus();
      
      if (status.is_running) {
        return true;
      }
      
      if (status.state === 'failed') {
        // Reset restart count and try again
        await this.resetRestartCount();
      }
      
      await this.start();
      return await this.waitForState('running', 30000);
    } catch (error) {
      console.error('Failed to ensure service is running:', error);
      return false;
    }
  }

  /**
   * Ensure monitoring is active, start if not
   * @returns True if monitoring is active or was started successfully
   */
  static async ensureMonitoring(): Promise<boolean> {
    try {
      const status = await this.getStatus();
      
      if (status.is_monitoring) {
        return true;
      }
      
      await this.startMonitoring();
      return true;
    } catch (error) {
      console.error('Failed to ensure monitoring is active:', error);
      return false;
    }
  }
}

export default PythonServiceAPI;
