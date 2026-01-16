use serde::{Deserialize, Serialize};

/// Request to start audio recording
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StartRecordingRequest {
    pub device_type: String, // "microphone" or "speaker"
}

/// Request to set audio device
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SetAudioDeviceRequest {
    pub device_type: String,
    pub device_id: String,
}

/// Request to generate AI response
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GenerateResponseRequest {
    pub context: String,
}

/// Request to switch AI provider
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SwitchProviderRequest {
    pub provider: String,
}

/// Request to update configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UpdateConfigRequest {
    pub config: ConfigData,
}

/// Configuration data structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConfigData {
    pub audio: AudioConfig,
    pub ai: AIConfig,
    pub ui: UIConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AudioConfig {
    pub record_timeout: u32,
    pub energy_threshold: u32,
    pub device: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AIConfig {
    pub provider: String,
    pub model: String,
    pub api_key: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UIConfig {
    pub update_interval: u32,
    pub theme: String, // "light" or "dark"
}
