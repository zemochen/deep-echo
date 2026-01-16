// Command modules for Tauri application

pub mod audio;
pub mod transcription;
pub mod ai;
pub mod config;
pub mod system;
pub mod file;
pub mod system_info;
pub mod python_service;

// Re-export all commands
pub use audio::*;
pub use transcription::*;
pub use ai::*;
pub use config::*;
pub use system::*;
pub use file::*;
pub use system_info::*;
pub use python_service::*;
