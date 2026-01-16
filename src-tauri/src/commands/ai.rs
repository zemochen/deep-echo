use tauri::State;
use std::sync::Mutex;

/// Shared state for AI provider
pub struct AIState {
    pub current_provider: Mutex<String>,
    pub last_response: Mutex<Option<String>>,
}

impl Default for AIState {
    fn default() -> Self {
        Self {
            current_provider: Mutex::new("openai".to_string()),
            last_response: Mutex::new(None),
        }
    }
}

/// Generate AI response
/// 
/// # Arguments
/// * `context` - Context string for AI to generate response from
/// 
/// # Returns
/// * `Result<String, String>` - Generated response or error
#[tauri::command]
pub async fn generate_response(
    context: String,
    state: State<'_, AIState>,
) -> Result<String, String> {
    // Validate context
    if context.trim().is_empty() {
        return Err("Context cannot be empty".to_string());
    }

    // TODO: Send IPC command to Python backend to generate response
    // For now, we'll simulate the response
    let provider = state.current_provider.lock().map_err(|e| e.to_string())?;
    println!("Generating response using provider: {} with context: {}", provider, context);

    // Simulate response generation
    let response = format!("AI response from {} based on: {}", provider, context);
    
    // Store last response
    let mut last_response = state.last_response.lock().map_err(|e| e.to_string())?;
    *last_response = Some(response.clone());

    Ok(response)
}

/// Switch AI provider
/// 
/// # Arguments
/// * `provider` - Name of the AI provider to switch to
/// 
/// # Returns
/// * `Result<String, String>` - Success message or error
#[tauri::command]
pub async fn switch_provider(
    provider: String,
    state: State<'_, AIState>,
) -> Result<String, String> {
    // Validate provider
    let valid_providers = vec!["openai", "claude", "deepseek", "grok", "glm", "volcano"];
    if !valid_providers.contains(&provider.as_str()) {
        return Err(format!(
            "Invalid provider: {}. Valid providers are: {}",
            provider,
            valid_providers.join(", ")
        ));
    }

    // TODO: Send IPC command to Python backend to switch provider
    // For now, we'll update the state
    println!("Switching to provider: {}", provider);

    let mut current_provider = state.current_provider.lock().map_err(|e| e.to_string())?;
    *current_provider = provider.clone();

    Ok(format!("Switched to provider: {}", provider))
}
