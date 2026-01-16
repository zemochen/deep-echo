/// Event Handler for Backend Event Processing
/// 
/// This module provides the event handler that manages events from the Python backend
/// and forwards them to the frontend. It implements event listening, processing,
/// and forwarding mechanisms.

use crate::models::event::{ErrorInfo, event_names};
use crate::models::response::{TranscriptData, ResponseData, SystemStatus};
use crate::models::request::ConfigData;
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tokio::sync::Mutex;
use tauri::Window;
use anyhow::Result;

/// Backend event structure received from Python
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", content = "data")]
pub enum BackendEvent {
    AudioStarted,
    AudioStopped,
    TranscriptionComplete(TranscriptData),
    ResponseReady(ResponseData),
    StatusChanged(SystemStatus),
    ConfigUpdated(ConfigData),
    Error(ErrorInfo),
}

/// Event handler manages backend events and forwards them to frontend
pub struct EventHandler {
    window: Arc<Mutex<Option<Window>>>,
    event_queue: Arc<Mutex<Vec<BackendEvent>>>,
}

impl EventHandler {
    /// Create a new event handler
    pub fn new() -> Self {
        Self {
            window: Arc::new(Mutex::new(None)),
            event_queue: Arc::new(Mutex::new(Vec::new())),
        }
    }

    /// Set the Tauri window for event emission
    pub async fn set_window(&self, window: Window) {
        let mut w = self.window.lock().await;
        *w = Some(window);
    }

    /// Process a backend event and forward to frontend
    pub async fn handle_event(&self, event: BackendEvent) -> Result<()> {
        // Add to queue
        {
            let mut queue = self.event_queue.lock().await;
            queue.push(event.clone());
        }

        // Forward to frontend
        self.forward_to_frontend(event).await
    }

    /// Forward event to frontend via Tauri event system
    async fn forward_to_frontend(&self, event: BackendEvent) -> Result<()> {
        let window = self.window.lock().await;
        
        if let Some(win) = window.as_ref() {
            match event {
                BackendEvent::AudioStarted => {
                    win.emit("audio-started", ())
                        .map_err(|e| anyhow::anyhow!("Failed to emit audio-started event: {}", e))?;
                }
                BackendEvent::AudioStopped => {
                    win.emit("audio-stopped", ())
                        .map_err(|e| anyhow::anyhow!("Failed to emit audio-stopped event: {}", e))?;
                }
                BackendEvent::TranscriptionComplete(data) => {
                    win.emit(event_names::TRANSCRIPT_UPDATED, data)
                        .map_err(|e| anyhow::anyhow!("Failed to emit transcript-updated event: {}", e))?;
                }
                BackendEvent::ResponseReady(data) => {
                    win.emit(event_names::RESPONSE_GENERATED, data)
                        .map_err(|e| anyhow::anyhow!("Failed to emit response-generated event: {}", e))?;
                }
                BackendEvent::StatusChanged(status) => {
                    win.emit(event_names::STATUS_CHANGED, status)
                        .map_err(|e| anyhow::anyhow!("Failed to emit status-changed event: {}", e))?;
                }
                BackendEvent::ConfigUpdated(config) => {
                    win.emit(event_names::CONFIG_UPDATED, config)
                        .map_err(|e| anyhow::anyhow!("Failed to emit config-updated event: {}", e))?;
                }
                BackendEvent::Error(error) => {
                    win.emit(event_names::ERROR_OCCURRED, error)
                        .map_err(|e| anyhow::anyhow!("Failed to emit error-occurred event: {}", e))?;
                }
            }
        }

        Ok(())
    }

    /// Emit a transcript updated event
    pub async fn emit_transcript_updated(&self, data: TranscriptData) -> Result<()> {
        self.handle_event(BackendEvent::TranscriptionComplete(data)).await
    }

    /// Emit a response generated event
    pub async fn emit_response_generated(&self, data: ResponseData) -> Result<()> {
        self.handle_event(BackendEvent::ResponseReady(data)).await
    }

    /// Emit a status changed event
    pub async fn emit_status_changed(&self, status: SystemStatus) -> Result<()> {
        self.handle_event(BackendEvent::StatusChanged(status)).await
    }

    /// Emit an error occurred event
    pub async fn emit_error(&self, error: ErrorInfo) -> Result<()> {
        self.handle_event(BackendEvent::Error(error)).await
    }

    /// Emit a config updated event
    pub async fn emit_config_updated(&self, config: ConfigData) -> Result<()> {
        self.handle_event(BackendEvent::ConfigUpdated(config)).await
    }

    /// Get the event queue size
    pub async fn queue_size(&self) -> usize {
        let queue = self.event_queue.lock().await;
        queue.len()
    }

    /// Clear the event queue
    pub async fn clear_queue(&self) {
        let mut queue = self.event_queue.lock().await;
        queue.clear();
    }

    /// Get all events from the queue
    pub async fn get_events(&self) -> Vec<BackendEvent> {
        let queue = self.event_queue.lock().await;
        queue.clone()
    }
}

impl Default for EventHandler {
    fn default() -> Self {
        Self::new()
    }
}

/// Global event handler state
pub struct EventHandlerState {
    handler: Arc<Mutex<EventHandler>>,
}

impl EventHandlerState {
    pub fn new() -> Self {
        Self {
            handler: Arc::new(Mutex::new(EventHandler::new())),
        }
    }

    pub async fn get_handler(&self) -> Arc<Mutex<EventHandler>> {
        self.handler.clone()
    }
}

impl Default for EventHandlerState {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_event_handler_creation() {
        let handler = EventHandler::new();
        assert_eq!(handler.queue_size().await, 0);
    }

    #[tokio::test]
    async fn test_event_queue() {
        let handler = EventHandler::new();
        
        let event = BackendEvent::AudioStarted;
        // Note: This will fail to forward without a window, but should still queue
        let _ = handler.handle_event(event).await;
        
        assert_eq!(handler.queue_size().await, 1);
    }

    #[tokio::test]
    async fn test_clear_queue() {
        let handler = EventHandler::new();
        
        let event = BackendEvent::AudioStarted;
        let _ = handler.handle_event(event).await;
        
        assert_eq!(handler.queue_size().await, 1);
        
        handler.clear_queue().await;
        assert_eq!(handler.queue_size().await, 0);
    }

    #[tokio::test]
    async fn test_get_events() {
        let handler = EventHandler::new();
        
        let event1 = BackendEvent::AudioStarted;
        let event2 = BackendEvent::AudioStopped;
        
        let _ = handler.handle_event(event1).await;
        let _ = handler.handle_event(event2).await;
        
        let events = handler.get_events().await;
        assert_eq!(events.len(), 2);
    }
}
