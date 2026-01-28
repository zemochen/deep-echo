use tauri::State;
use std::sync::Mutex;
use serde_json::json;

/// Shared state for audio recording
pub struct AudioState {
    pub is_recording: Mutex<bool>,
    pub current_device: Mutex<Option<String>>,
}

impl Default for AudioState {
    fn default() -> Self {
        Self {
            is_recording: Mutex::new(false),
            current_device: Mutex::new(None),
        }
    }
}

/// Send IPC command to Python backend
async fn send_ipc_command(command: &str, data: serde_json::Value) -> Result<String, String> {
    use std::io::{Read, Write};
    use std::net::TcpStream;
    
    // Connect to Python backend
    let mut stream = TcpStream::connect("127.0.0.1:9876")
        .map_err(|e| format!("Failed to connect to Python backend: {}", e))?;
    
    // Prepare command
    let command_json = json!({
        "command": command,
        "data": data
    });
    
    let command_str = format!("{}\n", command_json.to_string());
    
    // Send command
    stream.write_all(command_str.as_bytes())
        .map_err(|e| format!("Failed to send command: {}", e))?;
    
    // Read response
    let mut response = String::new();
    stream.read_to_string(&mut response)
        .map_err(|e| format!("Failed to read response: {}", e))?;
    
    Ok(response.trim().to_string())
}

/// Start audio recording
/// 
/// # Arguments
/// * `device_type` - Type of device to record from ("microphone" or "speaker")
/// 
/// # Returns
/// * `Result<String, String>` - Success message or error
#[tauri::command]
pub async fn start_recording(
    device_type: String,
    state: State<'_, AudioState>,
) -> Result<String, String> {
    // Validate device type
    if device_type != "microphone" && device_type != "speaker" {
        return Err(format!("Invalid device type: {}. Must be 'microphone' or 'speaker'", device_type));
    }

    // Check if already recording (release lock before await)
    {
        let is_recording = state.is_recording.lock().map_err(|e| e.to_string())?;
        if *is_recording {
            return Err("Recording is already in progress".to_string());
        }
    }

    // Send IPC command to Python backend to start recording
    let command_data = json!({
        "device_type": device_type
    });
    
    match send_ipc_command("start_recording", command_data).await {
        Ok(response) => {
            println!("Python backend response: {}", response);
            
            // Update state after successful backend call
            {
                let mut is_recording = state.is_recording.lock().map_err(|e| e.to_string())?;
                *is_recording = true;
                let mut current_device = state.current_device.lock().map_err(|e| e.to_string())?;
                *current_device = Some(device_type.clone());
            }

            Ok(format!("Recording started from {}", device_type))
        }
        Err(e) => {
            eprintln!("Failed to start recording: {}", e);
            Err(format!("Failed to start recording: {}", e))
        }
    }
}

/// Stop audio recording
/// 
/// # Returns
/// * `Result<String, String>` - Success message or error
#[tauri::command]
pub async fn stop_recording(
    state: State<'_, AudioState>,
) -> Result<String, String> {
    // Check if recording is active (release lock before await)
    {
        let is_recording = state.is_recording.lock().map_err(|e| e.to_string())?;
        if !*is_recording {
            return Err("No recording in progress".to_string());
        }
    }

    // Send IPC command to Python backend to stop recording
    let command_data = json!({});
    
    match send_ipc_command("stop_recording", command_data).await {
        Ok(response) => {
            println!("Python backend response: {}", response);
            
            // Update state after successful backend call
            {
                let mut is_recording = state.is_recording.lock().map_err(|e| e.to_string())?;
                *is_recording = false;
                let mut current_device = state.current_device.lock().map_err(|e| e.to_string())?;
                *current_device = None;
            }

            Ok("Recording stopped".to_string())
        }
        Err(e) => {
            eprintln!("Failed to stop recording: {}", e);
            // Still update state even if backend call failed
            {
                let mut is_recording = state.is_recording.lock().map_err(|e| e.to_string())?;
                *is_recording = false;
                let mut current_device = state.current_device.lock().map_err(|e| e.to_string())?;
                *current_device = None;
            }
            
            Err(format!("Failed to stop recording: {}", e))
        }
    }
}
