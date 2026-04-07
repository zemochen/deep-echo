use crate::models::response::{SystemInfo, AudioDevice};
use std::env;
use std::io::{Read, Write};
use std::net::TcpStream;
use serde_json::json;

/// Send IPC command to Python backend (mirrors audio.rs implementation)
async fn send_ipc_command(command: &str, data: serde_json::Value) -> Result<String, String> {
    let mut stream = TcpStream::connect("127.0.0.1:9876")
        .map_err(|e| format!("Failed to connect to Python backend: {}", e))?;

    let command_json = json!({ "command": command, "data": data });
    let command_str = format!("{}\n", command_json.to_string());

    stream.write_all(command_str.as_bytes())
        .map_err(|e| format!("Failed to send command: {}", e))?;

    let mut response = String::new();
    stream.read_to_string(&mut response)
        .map_err(|e| format!("Failed to read response: {}", e))?;

    Ok(response.trim().to_string())
}

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

/// Get available audio devices from Python backend
///
/// # Returns
/// * `Result<Vec<AudioDevice>, String>` - List of audio devices or error
#[tauri::command]
pub async fn get_audio_devices() -> Result<Vec<AudioDevice>, String> {
    let response_str = send_ipc_command("get_audio_devices", json!({})).await
        .map_err(|e| format!("IPC error: {}", e))?;

    let response: serde_json::Value = serde_json::from_str(&response_str)
        .map_err(|e| format!("Failed to parse response: {}", e))?;

    // Python backend returns { microphones: [...], speakers: [...] }
    // or wrapped in { data: { microphones: [...], speakers: [...] } }
    let payload = if response.get("data").is_some() {
        &response["data"]
    } else {
        &response
    };

    let mut devices = Vec::new();

    if let Some(mics) = payload["microphones"].as_array() {
        for mic in mics {
            devices.push(AudioDevice {
                id: mic["id"].as_str().unwrap_or("").to_string(),
                name: mic["name"].as_str().unwrap_or("Unknown Microphone").to_string(),
                device_type: "microphone".to_string(),
            });
        }
    }

    if let Some(speakers) = payload["speakers"].as_array() {
        for speaker in speakers {
            devices.push(AudioDevice {
                id: speaker["id"].as_str().unwrap_or("").to_string(),
                name: speaker["name"].as_str().unwrap_or("Unknown Speaker").to_string(),
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
