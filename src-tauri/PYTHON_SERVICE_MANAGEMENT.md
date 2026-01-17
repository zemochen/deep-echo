# Python Service Management

This document describes the Python service management implementation in the Tauri layer.

## Overview

The Python service management system provides:
- **Subprocess Management**: Start, stop, and restart the Python backend service
- **Lifecycle Management**: Track service state (stopped, starting, running, stopping, failed)
- **Health Monitoring**: Automatic health checks at configurable intervals
- **Auto-Restart**: Automatic restart on failure with configurable retry limits
- **Process Monitoring**: Track process ID, restart count, and service status

## Architecture

### Components

1. **PythonService**: Core service manager
   - Manages Python subprocess lifecycle
   - Tracks service state and restart attempts
   - Provides health check functionality

2. **PythonServiceMonitor**: Automatic monitoring
   - Runs health checks in background thread
   - Automatically restarts failed services
   - Configurable check intervals

3. **PythonServiceState**: Tauri state wrapper
   - Manages service and monitor instances
   - Provides thread-safe access to service

4. **Tauri Commands**: Frontend API
   - `start_python_service`: Start the backend service
   - `stop_python_service`: Stop the backend service
   - `restart_python_service`: Restart the backend service
   - `get_python_service_status`: Get current service status
   - `start_service_monitoring`: Enable automatic monitoring
   - `stop_service_monitoring`: Disable automatic monitoring
   - `check_service_health`: Manual health check
   - `reset_service_restart_count`: Reset restart counter

## Configuration

### PythonServiceConfig

```rust
pub struct PythonServiceConfig {
    /// Path to Python executable (default: "python3")
    pub python_path: String,
    
    /// Path to backend service script (default: "src/backend_service.py")
    pub service_script: String,
    
    /// Working directory for the service (default: None)
    pub working_dir: Option<String>,
    
    /// Environment variables (default: empty)
    pub env_vars: Vec<(String, String)>,
    
    /// Startup timeout in seconds (default: 30)
    pub startup_timeout: u64,
    
    /// Health check interval in seconds (default: 10)
    pub health_check_interval: u64,
    
    /// Maximum restart attempts (default: 3)
    pub max_restart_attempts: u32,
    
    /// Restart delay in seconds (default: 5)
    pub restart_delay: u64,
}
```

## Service States

- **Stopped**: Service is not running
- **Starting**: Service is being started
- **Running**: Service is running normally
- **Stopping**: Service is being stopped
- **Failed**: Service has failed and needs restart

## Usage

### Starting the Service

```typescript
import { invoke } from '@tauri-apps/api/tauri';

// Start the Python backend service
await invoke('start_python_service');
```

### Stopping the Service

```typescript
// Stop the Python backend service
await invoke('stop_python_service');
```

### Restarting the Service

```typescript
// Restart the Python backend service
await invoke('restart_python_service');
```

### Getting Service Status

```typescript
interface ServiceStatus {
  state: string;           // "stopped" | "starting" | "running" | "stopping" | "failed"
  is_running: boolean;     // Whether the process is alive
  pid: number | null;      // Process ID if running
  restart_count: number;   // Number of restart attempts
  is_monitoring: boolean;  // Whether monitoring is active
}

const status = await invoke<ServiceStatus>('get_python_service_status');
console.log('Service state:', status.state);
console.log('Process ID:', status.pid);
```

### Enabling Automatic Monitoring

```typescript
// Start automatic health checks and restart on failure
await invoke('start_service_monitoring');
```

### Disabling Automatic Monitoring

```typescript
// Stop automatic health checks
await invoke('stop_service_monitoring');
```

### Manual Health Check

```typescript
// Perform a manual health check
const isHealthy = await invoke<boolean>('check_service_health');
if (!isHealthy) {
  console.log('Service is not healthy');
}
```

### Resetting Restart Count

```typescript
// Reset the restart counter (useful after manual intervention)
await invoke('reset_service_restart_count');
```

## Health Monitoring

The health monitoring system:

1. **Periodic Checks**: Runs health checks at configured intervals (default: 10 seconds)
2. **Process Validation**: Verifies the Python process is still alive
3. **Automatic Restart**: Attempts to restart failed services
4. **Retry Limits**: Stops after maximum restart attempts (default: 3)
5. **Restart Delay**: Waits between restart attempts (default: 5 seconds)

### Health Check Flow

```
┌─────────────────────┐
│  Health Check Timer │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Check Process      │
│  Still Alive?       │
└──────────┬──────────┘
           │
           ├─── Yes ──► Continue Monitoring
           │
           └─── No ───► Mark as Failed
                        │
                        ▼
                ┌───────────────────┐
                │ Attempt Restart   │
                │ (if under limit)  │
                └───────────────────┘
```

## Error Handling

### Startup Errors

If the service fails to start:
- Error is returned to the caller
- Service state is set to `Failed`
- Monitoring can attempt automatic restart

### Runtime Errors

If the service crashes during operation:
- Health check detects the failure
- Service state is set to `Failed`
- Monitor attempts automatic restart (if enabled)
- After max attempts, service remains in `Failed` state

### Restart Limits

After reaching maximum restart attempts:
- Service remains in `Failed` state
- Monitoring continues but won't restart
- Manual intervention required (restart or reset counter)

## Integration with Backend

The Python service manager expects a backend service script at the configured path (default: `src/backend_service.py`).

### Backend Requirements

The backend service should:
1. Accept standard input/output for IPC communication
2. Handle graceful shutdown signals
3. Provide health check endpoints or status indicators
4. Log errors and status to stdout/stderr

### Example Backend Structure

```python
# backend/backend_service.py
import sys
import signal
import logging

class BackendService:
    def __init__(self):
        self.running = False
        
    def start(self):
        self.running = True
        logging.info("Backend service started")
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        signal.signal(signal.SIGINT, self.handle_shutdown)
        
        # Main service loop
        while self.running:
            # Process requests, handle events, etc.
            pass
            
    def handle_shutdown(self, signum, frame):
        logging.info("Shutdown signal received")
        self.running = False
        
if __name__ == "__main__":
    service = BackendService()
    try:
        service.start()
    except Exception as e:
        logging.error(f"Service error: {e}")
        sys.exit(1)
```

## Best Practices

1. **Enable Monitoring**: Always enable monitoring in production
2. **Configure Timeouts**: Adjust timeouts based on service startup time
3. **Set Retry Limits**: Configure appropriate retry limits for your use case
4. **Monitor Logs**: Check service logs for error patterns
5. **Graceful Shutdown**: Ensure backend handles shutdown signals properly
6. **Resource Cleanup**: Service manager cleans up on drop, but explicit stop is better

## Troubleshooting

### Service Won't Start

- Check Python path is correct
- Verify service script exists and is executable
- Check working directory is correct
- Review environment variables
- Check logs for startup errors

### Service Keeps Crashing

- Review backend service logs
- Check for resource issues (memory, CPU)
- Verify dependencies are installed
- Check for configuration errors
- Increase restart delay if startup is slow

### Monitoring Not Working

- Verify monitoring is started
- Check health check interval is reasonable
- Ensure service is actually running
- Review monitor thread logs

### Max Restarts Reached

- Check backend logs for crash cause
- Fix underlying issue
- Reset restart count: `invoke('reset_service_restart_count')`
- Manually restart: `invoke('restart_python_service')`

## Testing

The service management includes unit tests:

```bash
cd backend-tauri
cargo test python_service
```

Test coverage includes:
- Configuration defaults
- Initial state verification
- State transitions
- Service lifecycle operations

## Future Enhancements

Potential improvements:
- [ ] IPC communication for health checks
- [ ] Metrics collection (uptime, restart frequency)
- [ ] Configurable restart strategies (exponential backoff)
- [ ] Service dependency management
- [ ] Multiple service instances
- [ ] Service discovery and registration

## References

- [Tauri Documentation](https://tauri.app/)
- [Rust std::process](https://doc.rust-lang.org/std/process/)
- [Backend Service README](../../backend/README.md)
