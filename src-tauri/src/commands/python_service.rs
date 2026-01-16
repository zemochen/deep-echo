// Tauri commands for Python service management
use std::sync::{Arc, Mutex};
use tauri::State;
use serde::{Deserialize, Serialize};
use crate::services::python_service::{PythonService, PythonServiceConfig, PythonServiceMonitor, ServiceState};

/// Python service state wrapper for Tauri
pub struct PythonServiceState {
    service: Arc<PythonService>,
    monitor: Arc<Mutex<Option<PythonServiceMonitor>>>,
}

impl PythonServiceState {
    pub fn new(config: PythonServiceConfig) -> Self {
        let service = Arc::new(PythonService::new(config));
        Self {
            service,
            monitor: Arc::new(Mutex::new(None)),
        }
    }

    pub fn get_service(&self) -> Arc<PythonService> {
        Arc::clone(&self.service)
    }

    pub fn get_monitor(&self) -> Arc<Mutex<Option<PythonServiceMonitor>>> {
        Arc::clone(&self.monitor)
    }
}

/// Response for service status
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServiceStatusResponse {
    pub state: String,
    pub is_running: bool,
    pub pid: Option<u32>,
    pub restart_count: u32,
    pub is_monitoring: bool,
}

/// Start the Python backend service
#[tauri::command]
pub async fn start_python_service(
    state: State<'_, PythonServiceState>,
) -> Result<String, String> {
    let service = state.get_service();
    
    service.start()
        .map_err(|e| format!("Failed to start Python service: {}", e))?;
    
    Ok("Python service started successfully".to_string())
}

/// Stop the Python backend service
#[tauri::command]
pub async fn stop_python_service(
    state: State<'_, PythonServiceState>,
) -> Result<String, String> {
    let service = state.get_service();
    
    service.stop()
        .map_err(|e| format!("Failed to stop Python service: {}", e))?;
    
    Ok("Python service stopped successfully".to_string())
}

/// Restart the Python backend service
#[tauri::command]
pub async fn restart_python_service(
    state: State<'_, PythonServiceState>,
) -> Result<String, String> {
    let service = state.get_service();
    
    service.restart()
        .map_err(|e| format!("Failed to restart Python service: {}", e))?;
    
    Ok("Python service restarted successfully".to_string())
}

/// Get the status of the Python backend service
#[tauri::command]
pub async fn get_python_service_status(
    state: State<'_, PythonServiceState>,
) -> Result<ServiceStatusResponse, String> {
    let service = state.get_service();
    let monitor = state.get_monitor();
    
    let state_value = service.get_state();
    let state_str = match state_value {
        ServiceState::Stopped => "stopped",
        ServiceState::Starting => "starting",
        ServiceState::Running => "running",
        ServiceState::Stopping => "stopping",
        ServiceState::Failed => "failed",
    }.to_string();
    
    let is_monitoring = {
        let monitor_lock = monitor.lock().unwrap();
        if let Some(ref m) = *monitor_lock {
            m.is_monitoring()
        } else {
            false
        }
    };
    
    Ok(ServiceStatusResponse {
        state: state_str,
        is_running: service.is_running(),
        pid: service.get_pid(),
        restart_count: service.get_restart_count(),
        is_monitoring,
    })
}

/// Start monitoring the Python backend service
#[tauri::command]
pub async fn start_service_monitoring(
    state: State<'_, PythonServiceState>,
) -> Result<String, String> {
    let service = state.get_service();
    let monitor_arc = state.get_monitor();
    
    let mut monitor_lock = monitor_arc.lock().unwrap();
    
    if monitor_lock.is_none() {
        let monitor = PythonServiceMonitor::new(Arc::clone(&service));
        monitor.start_monitoring();
        *monitor_lock = Some(monitor);
        Ok("Service monitoring started".to_string())
    } else {
        Err("Service monitoring is already running".to_string())
    }
}

/// Stop monitoring the Python backend service
#[tauri::command]
pub async fn stop_service_monitoring(
    state: State<'_, PythonServiceState>,
) -> Result<String, String> {
    let monitor_arc = state.get_monitor();
    let mut monitor_lock = monitor_arc.lock().unwrap();
    
    if let Some(ref monitor) = *monitor_lock {
        monitor.stop_monitoring();
        *monitor_lock = None;
        Ok("Service monitoring stopped".to_string())
    } else {
        Err("Service monitoring is not running".to_string())
    }
}

/// Perform a manual health check on the Python backend service
#[tauri::command]
pub async fn check_service_health(
    state: State<'_, PythonServiceState>,
) -> Result<bool, String> {
    let service = state.get_service();
    
    service.health_check()
        .map_err(|e| format!("Health check failed: {}", e))
}

/// Reset the restart counter for the Python backend service
#[tauri::command]
pub async fn reset_service_restart_count(
    state: State<'_, PythonServiceState>,
) -> Result<String, String> {
    let service = state.get_service();
    service.reset_restart_count();
    
    Ok("Restart count reset successfully".to_string())
}
