// TypeScript types for Python service management

/**
 * Python service state
 */
export type ServiceState = 'stopped' | 'starting' | 'running' | 'stopping' | 'failed';

/**
 * Service status response from backend
 */
export interface ServiceStatus {
  /** Current service state */
  state: ServiceState;
  /** Whether the process is currently running */
  is_running: boolean;
  /** Process ID if running, null otherwise */
  pid: number | null;
  /** Number of restart attempts */
  restart_count: number;
  /** Whether automatic monitoring is active */
  is_monitoring: boolean;
}

/**
 * Python service configuration
 */
export interface PythonServiceConfig {
  /** Path to Python executable */
  python_path: string;
  /** Path to backend service script */
  service_script: string;
  /** Working directory for the service */
  working_dir?: string;
  /** Environment variables */
  env_vars: Array<[string, string]>;
  /** Startup timeout in seconds */
  startup_timeout: number;
  /** Health check interval in seconds */
  health_check_interval: number;
  /** Maximum restart attempts */
  max_restart_attempts: number;
  /** Restart delay in seconds */
  restart_delay: number;
}

/**
 * Service error types
 */
export const ServiceError = {
  ALREADY_RUNNING: 'Service is already running',
  ALREADY_STARTING: 'Service is already starting',
  ALREADY_STOPPING: 'Service is already stopping',
  NOT_RUNNING: 'Service is not running',
  START_FAILED: 'Failed to start service',
  STOP_FAILED: 'Failed to stop service',
  RESTART_FAILED: 'Failed to restart service',
  MAX_RESTARTS_REACHED: 'Maximum restart attempts reached',
  MONITORING_ALREADY_ACTIVE: 'Service monitoring is already running',
  MONITORING_NOT_ACTIVE: 'Service monitoring is not running',
} as const;
