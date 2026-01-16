// System information commands
use crate::services::system_service::{
    SystemService, SystemInfo, AudioDevice, NetworkInterface, DiskInfo
};
use std::sync::Mutex;
use std::collections::HashMap;
use tauri::State;

/// System service state
pub struct SystemServiceState {
    service: Mutex<SystemService>,
}

impl SystemServiceState {
    pub fn new(service: SystemService) -> Self {
        Self {
            service: Mutex::new(service),
        }
    }
}

impl Default for SystemServiceState {
    fn default() -> Self {
        Self::new(SystemService::new())
    }
}

/// Get comprehensive system information
#[tauri::command]
pub async fn get_system_information(
    state: State<'_, SystemServiceState>,
) -> Result<SystemInfo, String> {
    let service = state.service.lock().map_err(|e| e.to_string())?;
    service.get_system_info().map_err(|e| e.to_string())
}

/// Get list of audio devices
#[tauri::command]
pub async fn get_audio_device_list(
    state: State<'_, SystemServiceState>,
) -> Result<Vec<AudioDevice>, String> {
    let service = state.service.lock().map_err(|e| e.to_string())?;
    service.get_audio_devices().map_err(|e| e.to_string())
}

/// Get network interfaces
#[tauri::command]
pub async fn get_network_interfaces(
    state: State<'_, SystemServiceState>,
) -> Result<Vec<NetworkInterface>, String> {
    let service = state.service.lock().map_err(|e| e.to_string())?;
    service.get_network_interfaces().map_err(|e| e.to_string())
}

/// Get disk information
#[tauri::command]
pub async fn get_disk_information(
    state: State<'_, SystemServiceState>,
) -> Result<Vec<DiskInfo>, String> {
    let service = state.service.lock().map_err(|e| e.to_string())?;
    service.get_disk_info().map_err(|e| e.to_string())
}

/// Get environment variables (filtered for security)
#[tauri::command]
pub async fn get_environment_variables(
    filter: Option<Vec<String>>,
    state: State<'_, SystemServiceState>,
) -> Result<HashMap<String, String>, String> {
    let service = state.service.lock().map_err(|e| e.to_string())?;
    service.get_environment_variables(filter).map_err(|e| e.to_string())
}

/// Get current working directory
#[tauri::command]
pub async fn get_current_directory(
    state: State<'_, SystemServiceState>,
) -> Result<String, String> {
    let service = state.service.lock().map_err(|e| e.to_string())?;
    service.get_current_directory().map_err(|e| e.to_string())
}

/// Get system locale
#[tauri::command]
pub async fn get_system_locale(
    state: State<'_, SystemServiceState>,
) -> Result<String, String> {
    let service = state.service.lock().map_err(|e| e.to_string())?;
    service.get_system_locale().map_err(|e| e.to_string())
}
