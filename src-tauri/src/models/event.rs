use serde::{Deserialize, Serialize};
use super::response::{TranscriptData, ResponseData, SystemStatus};
use super::request::ConfigData;

/// Events that can be emitted from backend to frontend
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", content = "payload")]
pub enum TauriEvent {
    TranscriptUpdated(TranscriptData),
    ResponseGenerated(ResponseData),
    StatusChanged(SystemStatus),
    ErrorOccurred(ErrorInfo),
    ConfigUpdated(ConfigData),
}

/// Error information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ErrorInfo {
    pub code: String,
    pub message: String,
    pub details: Option<serde_json::Value>,
}

/// Event names as constants
pub mod event_names {
    pub const TRANSCRIPT_UPDATED: &str = "transcript-updated";
    pub const RESPONSE_GENERATED: &str = "response-generated";
    pub const STATUS_CHANGED: &str = "status-changed";
    pub const ERROR_OCCURRED: &str = "error-occurred";
    pub const CONFIG_UPDATED: &str = "config-updated";
}
