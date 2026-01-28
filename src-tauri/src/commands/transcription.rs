use crate::models::response::TranscriptData;
use std::sync::Mutex;
use tauri::State;

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

impl TranscriptionState {
    /// Add a new transcript to the state
    pub fn add_transcript(&self, transcript: TranscriptData) -> Result<(), String> {
        let mut transcripts = self.transcripts.lock().map_err(|e| e.to_string())?;
        transcripts.push(transcript);
        
        // Keep only the last 100 transcripts to prevent memory issues
        if transcripts.len() > 100 {
            let excess = transcripts.len() - 100;
            transcripts.drain(0..excess);
        }
        
        Ok(())
    }
    
    /// Clear all transcripts
    pub fn clear_transcripts(&self) -> Result<(), String> {
        let mut transcripts = self.transcripts.lock().map_err(|e| e.to_string())?;
        transcripts.clear();
        Ok(())
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
    // Get the latest transcript from state
    let transcripts = state.transcripts.lock().map_err(|e| e.to_string())?;
    
    if let Some(latest) = transcripts.last() {
        Ok(latest.clone())
    } else {
        // Return empty transcript data with unique ID to avoid React key conflicts
        let timestamp = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_secs();
        
        Ok(TranscriptData {
            id: format!("empty-{}", timestamp),
            timestamp,
            source: "microphone".to_string(),
            text: "".to_string(),
            confidence: 0.0,
        })
    }
}

/// Add a transcript to the state (internal helper for testing/IPC)
#[allow(dead_code)]
pub fn add_transcript(
    state: &TranscriptionState,
    transcript: TranscriptData,
) -> Result<(), String> {
    let mut transcripts = state.transcripts.lock().map_err(|e| e.to_string())?;
    transcripts.push(transcript);
    Ok(())
}
