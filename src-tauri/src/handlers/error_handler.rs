/// Error Handler for Exception Handling and Logging
/// 
/// This module provides comprehensive error handling for the Tauri application.
/// It implements error logging, reporting, and recovery mechanisms.

use crate::models::event::ErrorInfo;
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tokio::sync::Mutex;
use std::fmt;

/// Error severity levels
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ErrorSeverity {
    Info,
    Warning,
    Error,
    Critical,
}

impl fmt::Display for ErrorSeverity {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ErrorSeverity::Info => write!(f, "INFO"),
            ErrorSeverity::Warning => write!(f, "WARNING"),
            ErrorSeverity::Error => write!(f, "ERROR"),
            ErrorSeverity::Critical => write!(f, "CRITICAL"),
        }
    }
}

/// Error category for classification
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum ErrorCategory {
    IPC,
    Audio,
    Transcription,
    AI,
    Config,
    System,
    Network,
    Unknown,
}

impl fmt::Display for ErrorCategory {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ErrorCategory::IPC => write!(f, "IPC"),
            ErrorCategory::Audio => write!(f, "AUDIO"),
            ErrorCategory::Transcription => write!(f, "TRANSCRIPTION"),
            ErrorCategory::AI => write!(f, "AI"),
            ErrorCategory::Config => write!(f, "CONFIG"),
            ErrorCategory::System => write!(f, "SYSTEM"),
            ErrorCategory::Network => write!(f, "NETWORK"),
            ErrorCategory::Unknown => write!(f, "UNKNOWN"),
        }
    }
}

/// Detailed error record
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ErrorRecord {
    pub id: String,
    pub timestamp: i64,
    pub severity: ErrorSeverity,
    pub category: ErrorCategory,
    pub code: String,
    pub message: String,
    pub details: Option<serde_json::Value>,
    pub stack_trace: Option<String>,
}

impl ErrorRecord {
    /// Create a new error record
    pub fn new(
        severity: ErrorSeverity,
        category: ErrorCategory,
        code: String,
        message: String,
    ) -> Self {
        Self {
            id: uuid::Uuid::new_v4().to_string(),
            timestamp: chrono::Utc::now().timestamp(),
            severity,
            category,
            code,
            message,
            details: None,
            stack_trace: None,
        }
    }

    /// Add details to the error record
    pub fn with_details(mut self, details: serde_json::Value) -> Self {
        self.details = Some(details);
        self
    }

    /// Add stack trace to the error record
    pub fn with_stack_trace(mut self, stack_trace: String) -> Self {
        self.stack_trace = Some(stack_trace);
        self
    }

    /// Convert to ErrorInfo for event emission
    pub fn to_error_info(&self) -> ErrorInfo {
        ErrorInfo {
            code: self.code.clone(),
            message: self.message.clone(),
            details: self.details.clone(),
        }
    }
}

/// Error handler manages error logging and reporting
pub struct ErrorHandler {
    error_log: Arc<Mutex<Vec<ErrorRecord>>>,
    max_log_size: usize,
}

impl ErrorHandler {
    /// Create a new error handler
    pub fn new() -> Self {
        Self {
            error_log: Arc::new(Mutex::new(Vec::new())),
            max_log_size: 1000,
        }
    }

    /// Create a new error handler with custom max log size
    pub fn with_max_log_size(max_log_size: usize) -> Self {
        Self {
            error_log: Arc::new(Mutex::new(Vec::new())),
            max_log_size,
        }
    }

    /// Log an error
    pub async fn log_error(&self, error: ErrorRecord) {
        let mut log = self.error_log.lock().await;
        
        // Print to console in debug mode
        #[cfg(debug_assertions)]
        {
            eprintln!(
                "[{}] [{}] {}: {}",
                error.severity, error.category, error.code, error.message
            );
            if let Some(details) = &error.details {
                eprintln!("  Details: {}", details);
            }
        }

        // Add to log
        log.push(error);

        // Trim log if it exceeds max size
        if log.len() > self.max_log_size {
            let excess = log.len() - self.max_log_size;
            log.drain(0..excess);
        }
    }

    /// Handle an error with automatic logging
    pub async fn handle_error(
        &self,
        severity: ErrorSeverity,
        category: ErrorCategory,
        code: String,
        message: String,
    ) -> ErrorInfo {
        let record = ErrorRecord::new(severity, category, code, message);
        let error_info = record.to_error_info();
        self.log_error(record).await;
        error_info
    }

    /// Handle an error from anyhow::Error
    pub async fn handle_anyhow_error(
        &self,
        error: anyhow::Error,
        category: ErrorCategory,
    ) -> ErrorInfo {
        let record = ErrorRecord::new(
            ErrorSeverity::Error,
            category,
            "ANYHOW_ERROR".to_string(),
            error.to_string(),
        );
        let error_info = record.to_error_info();
        self.log_error(record).await;
        error_info
    }

    /// Get all error records
    pub async fn get_errors(&self) -> Vec<ErrorRecord> {
        let log = self.error_log.lock().await;
        log.clone()
    }

    /// Get errors by severity
    pub async fn get_errors_by_severity(&self, severity: ErrorSeverity) -> Vec<ErrorRecord> {
        let log = self.error_log.lock().await;
        log.iter()
            .filter(|e| e.severity == severity)
            .cloned()
            .collect()
    }

    /// Get errors by category
    pub async fn get_errors_by_category(&self, category: ErrorCategory) -> Vec<ErrorRecord> {
        let log = self.error_log.lock().await;
        log.iter()
            .filter(|e| e.category == category)
            .cloned()
            .collect()
    }

    /// Get recent errors (last n)
    pub async fn get_recent_errors(&self, count: usize) -> Vec<ErrorRecord> {
        let log = self.error_log.lock().await;
        let start = if log.len() > count {
            log.len() - count
        } else {
            0
        };
        log[start..].to_vec()
    }

    /// Clear error log
    pub async fn clear_errors(&self) {
        let mut log = self.error_log.lock().await;
        log.clear();
    }

    /// Get error count
    pub async fn error_count(&self) -> usize {
        let log = self.error_log.lock().await;
        log.len()
    }
}

impl Default for ErrorHandler {
    fn default() -> Self {
        Self::new()
    }
}

/// Global error handler state
pub struct ErrorHandlerState {
    handler: Arc<Mutex<ErrorHandler>>,
}

impl ErrorHandlerState {
    pub fn new() -> Self {
        Self {
            handler: Arc::new(Mutex::new(ErrorHandler::new())),
        }
    }

    pub async fn get_handler(&self) -> Arc<Mutex<ErrorHandler>> {
        self.handler.clone()
    }
}

impl Default for ErrorHandlerState {
    fn default() -> Self {
        Self::new()
    }
}

/// Helper macro for error handling
#[macro_export]
macro_rules! handle_error {
    ($handler:expr, $severity:expr, $category:expr, $code:expr, $message:expr) => {
        $handler.handle_error($severity, $category, $code.to_string(), $message.to_string()).await
    };
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_error_handler_creation() {
        let handler = ErrorHandler::new();
        assert_eq!(handler.error_count().await, 0);
    }

    #[tokio::test]
    async fn test_log_error() {
        let handler = ErrorHandler::new();
        let error = ErrorRecord::new(
            ErrorSeverity::Error,
            ErrorCategory::IPC,
            "TEST_ERROR".to_string(),
            "Test error message".to_string(),
        );

        handler.log_error(error).await;
        assert_eq!(handler.error_count().await, 1);
    }

    #[tokio::test]
    async fn test_handle_error() {
        let handler = ErrorHandler::new();
        let error_info = handler.handle_error(
            ErrorSeverity::Warning,
            ErrorCategory::Audio,
            "AUDIO_WARNING".to_string(),
            "Audio device not found".to_string(),
        ).await;

        assert_eq!(error_info.code, "AUDIO_WARNING");
        assert_eq!(handler.error_count().await, 1);
    }

    #[tokio::test]
    async fn test_get_errors_by_severity() {
        let handler = ErrorHandler::new();
        
        handler.handle_error(
            ErrorSeverity::Error,
            ErrorCategory::IPC,
            "ERROR1".to_string(),
            "Error 1".to_string(),
        ).await;

        handler.handle_error(
            ErrorSeverity::Warning,
            ErrorCategory::Audio,
            "WARNING1".to_string(),
            "Warning 1".to_string(),
        ).await;

        let errors = handler.get_errors_by_severity(ErrorSeverity::Error).await;
        assert_eq!(errors.len(), 1);
        assert_eq!(errors[0].code, "ERROR1");
    }

    #[tokio::test]
    async fn test_get_errors_by_category() {
        let handler = ErrorHandler::new();
        
        handler.handle_error(
            ErrorSeverity::Error,
            ErrorCategory::IPC,
            "IPC_ERROR".to_string(),
            "IPC Error".to_string(),
        ).await;

        handler.handle_error(
            ErrorSeverity::Error,
            ErrorCategory::Audio,
            "AUDIO_ERROR".to_string(),
            "Audio Error".to_string(),
        ).await;

        let errors = handler.get_errors_by_category(ErrorCategory::IPC).await;
        assert_eq!(errors.len(), 1);
        assert_eq!(errors[0].code, "IPC_ERROR");
    }

    #[tokio::test]
    async fn test_clear_errors() {
        let handler = ErrorHandler::new();
        
        handler.handle_error(
            ErrorSeverity::Error,
            ErrorCategory::IPC,
            "ERROR1".to_string(),
            "Error 1".to_string(),
        ).await;

        assert_eq!(handler.error_count().await, 1);
        
        handler.clear_errors().await;
        assert_eq!(handler.error_count().await, 0);
    }

    #[tokio::test]
    async fn test_max_log_size() {
        let handler = ErrorHandler::with_max_log_size(5);
        
        for i in 0..10 {
            handler.handle_error(
                ErrorSeverity::Error,
                ErrorCategory::IPC,
                format!("ERROR{}", i),
                format!("Error {}", i),
            ).await;
        }

        assert_eq!(handler.error_count().await, 5);
    }

    #[tokio::test]
    async fn test_get_recent_errors() {
        let handler = ErrorHandler::new();
        
        for i in 0..10 {
            handler.handle_error(
                ErrorSeverity::Error,
                ErrorCategory::IPC,
                format!("ERROR{}", i),
                format!("Error {}", i),
            ).await;
        }

        let recent = handler.get_recent_errors(3).await;
        assert_eq!(recent.len(), 3);
        assert_eq!(recent[2].code, "ERROR9");
    }
}
