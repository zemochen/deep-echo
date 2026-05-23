use serde::{Deserialize, Serialize};

/// Audio device information
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct AudioDevice {
    pub id: String,
    pub name: String,
    pub device_type: String, // "microphone" or "speaker"
}

/// Transcript data
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TranscriptData {
    pub id: String,
    pub timestamp: u64,
    pub source: String, // "microphone" or "speaker"
    pub text: String,
    pub confidence: f32,
}

/// Response data from AI
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResponseData {
    pub id: String,
    pub timestamp: u64,
    pub provider: String,
    pub text: String,
    pub context: String,
}

/// System information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SystemInfo {
    pub platform: String,
    pub version: String,
    pub arch: String,
}

/// System status
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SystemStatus {
    pub state: String, // "idle", "recording", "processing", "error"
    pub message: String,
    pub details: Option<serde_json::Value>,
}
