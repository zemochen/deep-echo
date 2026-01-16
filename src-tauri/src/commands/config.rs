use crate::models::request::{ConfigData, AudioConfig, AIConfig, UIConfig};
use tauri::State;
use std::sync::Mutex;

/// Shared state for configuration
pub struct ConfigState {
    pub config: Mutex<ConfigData>,
}

impl Default for ConfigState {
    fn default() -> Self {
        Self {
            config: Mutex::new(ConfigData {
                audio: AudioConfig {
                    record_timeout: 5,
                    energy_threshold: 300,
                    device: None,
                },
                ai: AIConfig {
                    provider: "openai".to_string(),
                    model: "gpt-4".to_string(),
                    api_key: String::new(),
                },
                ui: UIConfig {
                    update_interval: 1000,
                    theme: "light".to_string(),
                },
            }),
        }
    }
}

/// Get current configuration
/// 
/// # Returns
/// * `Result<ConfigData, String>` - Current configuration or error
#[tauri::command]
pub async fn get_config(
    state: State<'_, ConfigState>,
) -> Result<ConfigData, String> {
    // TODO: Load configuration from file system or Python backend
    // For now, we'll return the state
    
    let config = state.config.lock().map_err(|e| e.to_string())?;
    Ok(config.clone())
}

/// Update configuration
/// 
/// # Arguments
/// * `config` - New configuration data
/// 
/// # Returns
/// * `Result<String, String>` - Success message or error
#[tauri::command]
pub async fn update_config(
    config: ConfigData,
    state: State<'_, ConfigState>,
) -> Result<String, String> {
    // Validate configuration
    validate_config(&config)?;

    // TODO: Send IPC command to Python backend to update config
    // TODO: Save configuration to file system
    // For now, we'll update the state
    println!("Updating configuration");

    let mut current_config = state.config.lock().map_err(|e| e.to_string())?;
    *current_config = config;

    Ok("Configuration updated successfully".to_string())
}

/// Validate configuration data
fn validate_config(config: &ConfigData) -> Result<(), String> {
    // Validate audio config
    if config.audio.record_timeout == 0 {
        return Err("Audio record timeout must be greater than 0".to_string());
    }
    if config.audio.energy_threshold == 0 {
        return Err("Audio energy threshold must be greater than 0".to_string());
    }

    // Validate AI config
    if config.ai.provider.trim().is_empty() {
        return Err("AI provider cannot be empty".to_string());
    }
    if config.ai.model.trim().is_empty() {
        return Err("AI model cannot be empty".to_string());
    }

    // Validate UI config
    if config.ui.update_interval == 0 {
        return Err("UI update interval must be greater than 0".to_string());
    }
    if config.ui.theme != "light" && config.ui.theme != "dark" {
        return Err("UI theme must be 'light' or 'dark'".to_string());
    }

    Ok(())
}
