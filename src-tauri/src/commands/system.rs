use crate::models::response::{SystemInfo, AudioDevice};
use std::env;

/// Get system information
/// 
/// # Returns
/// * `Result<SystemInfo, String>` - System information or error
#[tauri::command]
pub async fn get_system_info() -> Result<SystemInfo, String> {
    // Get system information
    let platform = env::consts::OS.to_string();
    let arch = env::consts::ARCH.to_string();
    
    // Get version from Cargo.toml or environment
    let version = env!("CARGO_PKG_VERSION").to_string();

    Ok(SystemInfo {
        platform,
        version,
        arch,
    })
}

/// Get available audio devices
/// 
/// # Returns
/// * `Result<Vec<AudioDevice>, String>` - List of audio devices or error
#[tauri::command]
pub async fn get_audio_devices() -> Result<Vec<AudioDevice>, String> {
    // TODO: Send IPC command to Python backend to get actual audio devices
    // For now, we'll return mock devices based on platform
    
    let platform = env::consts::OS;
    let mut devices = Vec::new();

    // Add default microphone
    devices.push(AudioDevice {
        id: "default-mic".to_string(),
        name: "Default Microphone".to_string(),
        device_type: "microphone".to_string(),
    });

    // Add platform-specific speaker devices
    match platform {
        "windows" => {
            devices.push(AudioDevice {
                id: "wasapi-loopback".to_string(),
                name: "WASAPI Loopback (Speakers)".to_string(),
                device_type: "speaker".to_string(),
            });
        }
        "macos" => {
            devices.push(AudioDevice {
                id: "blackhole".to_string(),
                name: "BlackHole 2ch".to_string(),
                device_type: "speaker".to_string(),
            });
        }
        _ => {
            // For other platforms, add a generic speaker device
            devices.push(AudioDevice {
                id: "default-speaker".to_string(),
                name: "Default Speaker".to_string(),
                device_type: "speaker".to_string(),
            });
        }
    }

    Ok(devices)
}

/// Set audio device
/// 
/// # Arguments
/// * `device_type` - Type of device ("microphone" or "speaker")
/// * `device_id` - ID of the device to set
/// 
/// # Returns
/// * `Result<String, String>` - Success message or error
#[tauri::command]
pub async fn set_audio_device(
    device_type: String,
    device_id: String,
) -> Result<String, String> {
    // Validate device type
    if device_type != "microphone" && device_type != "speaker" {
        return Err(format!("Invalid device type: {}. Must be 'microphone' or 'speaker'", device_type));
    }

    // Validate device ID
    if device_id.trim().is_empty() {
        return Err("Device ID cannot be empty".to_string());
    }

    // TODO: Send IPC command to Python backend to set audio device
    // For now, we'll just log the action
    println!("Setting {} device to: {}", device_type, device_id);

    Ok(format!("Set {} device to: {}", device_type, device_id))
}
