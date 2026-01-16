use tauri::State;
use std::sync::Mutex;

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

    // Check if already recording
    let mut is_recording = state.is_recording.lock().map_err(|e| e.to_string())?;
    if *is_recording {
        return Err("Recording is already in progress".to_string());
    }

    // TODO: Send IPC command to Python backend to start recording
    // For now, we'll simulate the command
    println!("Starting recording from device type: {}", device_type);

    // Update state
    *is_recording = true;
    let mut current_device = state.current_device.lock().map_err(|e| e.to_string())?;
    *current_device = Some(device_type.clone());

    Ok(format!("Recording started from {}", device_type))
}

/// Stop audio recording
/// 
/// # Returns
/// * `Result<String, String>` - Success message or error
#[tauri::command]
pub async fn stop_recording(
    state: State<'_, AudioState>,
) -> Result<String, String> {
    // Check if recording is active
    let mut is_recording = state.is_recording.lock().map_err(|e| e.to_string())?;
    if !*is_recording {
        return Err("No recording in progress".to_string());
    }

    // TODO: Send IPC command to Python backend to stop recording
    // For now, we'll simulate the command
    println!("Stopping recording");

    // Update state
    *is_recording = false;
    let mut current_device = state.current_device.lock().map_err(|e| e.to_string())?;
    *current_device = None;

    Ok("Recording stopped".to_string())
}
