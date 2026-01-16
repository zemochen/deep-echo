// Python service management for backend subprocess
use std::process::{Child, Command, Stdio};
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};
use std::thread;
use anyhow::{Result, Context, anyhow};
use serde::{Deserialize, Serialize};

/// Python service state
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ServiceState {
    Stopped,
    Starting,
    Running,
    Stopping,
    Failed,
}

/// Python service configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PythonServiceConfig {
    /// Path to Python executable
    pub python_path: String,
    /// Path to backend service script
    pub service_script: String,
    /// Working directory for the service
    pub working_dir: Option<String>,
    /// Environment variables
    pub env_vars: Vec<(String, String)>,
    /// Startup timeout in seconds
    pub startup_timeout: u64,
    /// Health check interval in seconds
    pub health_check_interval: u64,
    /// Maximum restart attempts
    pub max_restart_attempts: u32,
    /// Restart delay in seconds
    pub restart_delay: u64,
}

impl Default for PythonServiceConfig {
    fn default() -> Self {
        Self {
            python_path: "python3".to_string(),
            service_script: "src/backend_service.py".to_string(),
            working_dir: None,
            env_vars: Vec::new(),
            startup_timeout: 30,
            health_check_interval: 10,
            max_restart_attempts: 3,
            restart_delay: 5,
        }
    }
}

/// Python service manager
pub struct PythonService {
    config: PythonServiceConfig,
    process: Arc<Mutex<Option<Child>>>,
    state: Arc<Mutex<ServiceState>>,
    restart_count: Arc<Mutex<u32>>,
    last_restart: Arc<Mutex<Option<Instant>>>,
}

impl PythonService {
    /// Create a new Python service manager
    pub fn new(config: PythonServiceConfig) -> Self {
        Self {
            config,
            process: Arc::new(Mutex::new(None)),
            state: Arc::new(Mutex::new(ServiceState::Stopped)),
            restart_count: Arc::new(Mutex::new(0)),
            last_restart: Arc::new(Mutex::new(None)),
        }
    }

    /// Start the Python service
    pub fn start(&self) -> Result<()> {
        let mut state = self.state.lock().unwrap();
        
        match *state {
            ServiceState::Running => {
                return Err(anyhow!("Service is already running"));
            }
            ServiceState::Starting => {
                return Err(anyhow!("Service is already starting"));
            }
            _ => {}
        }

        *state = ServiceState::Starting;
        drop(state);

        // Build command
        let mut cmd = Command::new(&self.config.python_path);
        cmd.arg(&self.config.service_script)
            .stdout(Stdio::piped())
            .stderr(Stdio::piped());

        // Set working directory if specified
        if let Some(ref working_dir) = self.config.working_dir {
            cmd.current_dir(working_dir);
        }

        // Set environment variables
        for (key, value) in &self.config.env_vars {
            cmd.env(key, value);
        }

        // Spawn the process
        let child = cmd.spawn()
            .context("Failed to spawn Python service process")?;

        let pid = child.id();
        println!("Python service started with PID: {}", pid);

        // Store the process
        let mut process = self.process.lock().unwrap();
        *process = Some(child);
        drop(process);

        // Update state
        let mut state = self.state.lock().unwrap();
        *state = ServiceState::Running;
        drop(state);

        // Reset restart count on successful start
        let mut restart_count = self.restart_count.lock().unwrap();
        *restart_count = 0;
        drop(restart_count);

        // Update last restart time
        let mut last_restart = self.last_restart.lock().unwrap();
        *last_restart = Some(Instant::now());
        drop(last_restart);

        Ok(())
    }

    /// Stop the Python service
    pub fn stop(&self) -> Result<()> {
        let mut state = self.state.lock().unwrap();
        
        match *state {
            ServiceState::Stopped => {
                return Ok(());
            }
            ServiceState::Stopping => {
                return Err(anyhow!("Service is already stopping"));
            }
            _ => {}
        }

        *state = ServiceState::Stopping;
        drop(state);

        let mut process = self.process.lock().unwrap();
        
        if let Some(ref mut child) = *process {
            // Try to kill the process gracefully
            match child.kill() {
                Ok(_) => {
                    println!("Python service process killed");
                    // Wait for the process to exit
                    let _ = child.wait();
                }
                Err(e) => {
                    eprintln!("Failed to kill Python service process: {}", e);
                }
            }
        }

        *process = None;
        drop(process);

        let mut state = self.state.lock().unwrap();
        *state = ServiceState::Stopped;
        drop(state);

        Ok(())
    }

    /// Restart the Python service
    pub fn restart(&self) -> Result<()> {
        println!("Restarting Python service...");
        
        // Stop the service
        self.stop()?;
        
        // Wait for restart delay
        thread::sleep(Duration::from_secs(self.config.restart_delay));
        
        // Start the service
        self.start()?;
        
        Ok(())
    }

    /// Check if the service is running
    pub fn is_running(&self) -> bool {
        let process = self.process.lock().unwrap();
        
        if let Some(ref child) = *process {
            // Check if process is still alive by trying to get its status
            // This is a non-blocking check
            match child.id() {
                0 => false,
                _ => true,
            }
        } else {
            false
        }
    }

    /// Get the current service state
    pub fn get_state(&self) -> ServiceState {
        let state = self.state.lock().unwrap();
        state.clone()
    }

    /// Perform a health check on the service
    pub fn health_check(&self) -> Result<bool> {
        let state = self.state.lock().unwrap();
        
        match *state {
            ServiceState::Running => {
                drop(state);
                
                // Check if process is still alive
                if !self.is_running() {
                    let mut state = self.state.lock().unwrap();
                    *state = ServiceState::Failed;
                    return Ok(false);
                }
                
                Ok(true)
            }
            _ => Ok(false),
        }
    }

    /// Attempt to restart the service if it has failed
    pub fn attempt_restart(&self) -> Result<()> {
        let restart_count = {
            let count = self.restart_count.lock().unwrap();
            *count
        };

        if restart_count >= self.config.max_restart_attempts {
            return Err(anyhow!(
                "Maximum restart attempts ({}) reached",
                self.config.max_restart_attempts
            ));
        }

        // Increment restart count
        {
            let mut count = self.restart_count.lock().unwrap();
            *count += 1;
        }

        println!(
            "Attempting to restart Python service (attempt {}/{})",
            restart_count + 1,
            self.config.max_restart_attempts
        );

        self.restart()
    }

    /// Get the process ID of the running service
    pub fn get_pid(&self) -> Option<u32> {
        let process = self.process.lock().unwrap();
        
        if let Some(ref child) = *process {
            Some(child.id())
        } else {
            None
        }
    }

    /// Get restart count
    pub fn get_restart_count(&self) -> u32 {
        let count = self.restart_count.lock().unwrap();
        *count
    }

    /// Reset restart count
    pub fn reset_restart_count(&self) {
        let mut count = self.restart_count.lock().unwrap();
        *count = 0;
    }
}

impl Drop for PythonService {
    fn drop(&mut self) {
        // Ensure the service is stopped when the manager is dropped
        let _ = self.stop();
    }
}

/// Python service monitor for automatic health checks and restarts
pub struct PythonServiceMonitor {
    service: Arc<PythonService>,
    monitoring: Arc<Mutex<bool>>,
}

impl PythonServiceMonitor {
    /// Create a new service monitor
    pub fn new(service: Arc<PythonService>) -> Self {
        Self {
            service,
            monitoring: Arc::new(Mutex::new(false)),
        }
    }

    /// Start monitoring the service
    pub fn start_monitoring(&self) {
        let mut monitoring = self.monitoring.lock().unwrap();
        
        if *monitoring {
            println!("Service monitoring is already running");
            return;
        }

        *monitoring = true;
        drop(monitoring);

        let service = Arc::clone(&self.service);
        let monitoring = Arc::clone(&self.monitoring);
        let check_interval = service.config.health_check_interval;

        thread::spawn(move || {
            println!("Python service monitoring started");
            
            loop {
                // Check if monitoring should continue
                {
                    let monitoring = monitoring.lock().unwrap();
                    if !*monitoring {
                        println!("Python service monitoring stopped");
                        break;
                    }
                }

                // Perform health check
                match service.health_check() {
                    Ok(healthy) => {
                        if !healthy {
                            eprintln!("Python service health check failed");
                            
                            // Attempt to restart
                            match service.attempt_restart() {
                                Ok(_) => {
                                    println!("Python service restarted successfully");
                                }
                                Err(e) => {
                                    eprintln!("Failed to restart Python service: {}", e);
                                }
                            }
                        }
                    }
                    Err(e) => {
                        eprintln!("Health check error: {}", e);
                    }
                }

                // Sleep until next check
                thread::sleep(Duration::from_secs(check_interval));
            }
        });
    }

    /// Stop monitoring the service
    pub fn stop_monitoring(&self) {
        let mut monitoring = self.monitoring.lock().unwrap();
        *monitoring = false;
    }

    /// Check if monitoring is active
    pub fn is_monitoring(&self) -> bool {
        let monitoring = self.monitoring.lock().unwrap();
        *monitoring
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_service_config_default() {
        let config = PythonServiceConfig::default();
        assert_eq!(config.python_path, "python3");
        assert_eq!(config.startup_timeout, 30);
        assert_eq!(config.max_restart_attempts, 3);
    }

    #[test]
    fn test_service_initial_state() {
        let config = PythonServiceConfig::default();
        let service = PythonService::new(config);
        
        match service.get_state() {
            ServiceState::Stopped => {}
            _ => panic!("Initial state should be Stopped"),
        }
        
        assert!(!service.is_running());
        assert_eq!(service.get_restart_count(), 0);
    }

    #[test]
    fn test_service_state_transitions() {
        let config = PythonServiceConfig::default();
        let service = PythonService::new(config);
        
        // Initial state should be Stopped
        match service.get_state() {
            ServiceState::Stopped => {}
            _ => panic!("Initial state should be Stopped"),
        }
    }
}
