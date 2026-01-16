// Handler modules for IPC communication and event processing

pub mod ipc_handler;
pub mod event_handler;
pub mod error_handler;

// Re-export handlers
pub use ipc_handler::*;
pub use event_handler::*;
pub use error_handler::*;
