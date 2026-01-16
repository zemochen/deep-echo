use crate::models::response::TranscriptData;
use tauri::State;
use std::sync::Mutex;

/// Shared state for transcription data
pub struct TranscriptionState {
    pub transcripts: Mutex<Vec<TranscriptData>>,
}

impl Default for TranscriptionState {
    fn default() -> Self {
        Self {
            transcripts: Mutex::new(Vec::new()),
        }
    }
}

/// Get transcript data
/// 
/// # Returns
/// * `Result<TranscriptData, String>` - Latest transcript or error
#[tauri::command]
pub async fn get_transcript(
    state: State<'_, TranscriptionState>,
) -> Result<TranscriptData, String> {
    // TODO: Send IPC command to Python backend to get transcript
    // For now, we'll return the latest transcript from state or a mock
    
    let transcripts = state.transcripts.lock().map_err(|e| e.to_string())?;
    
    if let Some(latest) = transcripts.last() {
        Ok(latest.clone())
    } else {
        // Return a mock transcript if none exists
        Ok(TranscriptData {
            id: "mock-1".to_string(),
            timestamp: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs(),
            source: "microphone".to_string(),
            text: "No transcript available yet".to_string(),
            confidence: 0.0,
        })
    }
}

/// Add a transcript to the state (internal helper for testing/IPC)
#[allow(dead_code)]
pub fn add_transcript(state: &TranscriptionState, transcript: TranscriptData) -> Result<(), String> {
    let mut transcripts = state.transcripts.lock().map_err(|e| e.to_string())?;
    transcripts.push(transcript);
    Ok(())
}
