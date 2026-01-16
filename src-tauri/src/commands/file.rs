// File service commands
use crate::services::file_service::{FileService, FileOperationResult, FileMetadata};
use std::sync::Mutex;
use tauri::State;

/// File service state
pub struct FileServiceState {
    service: Mutex<FileService>,
}

impl FileServiceState {
    pub fn new(service: FileService) -> Self {
        Self {
            service: Mutex::new(service),
        }
    }
}

impl Default for FileServiceState {
    fn default() -> Self {
        // Create with empty allowed directories - will be initialized in setup
        Self::new(FileService::new(vec![]))
    }
}

/// Read file contents as string
#[tauri::command]
pub async fn read_file(
    path: String,
    state: State<'_, FileServiceState>,
) -> Result<String, String> {
    let service = state.service.lock().map_err(|e| e.to_string())?;
    service.read_file(&path).map_err(|e| e.to_string())
}

/// Write string contents to file
#[tauri::command]
pub async fn write_file(
    path: String,
    contents: String,
    state: State<'_, FileServiceState>,
) -> Result<FileOperationResult, String> {
    let service = state.service.lock().map_err(|e| e.to_string())?;
    service.write_file(&path, &contents).map_err(|e| e.to_string())
}

/// Append string contents to file
#[tauri::command]
pub async fn append_file(
    path: String,
    contents: String,
    state: State<'_, FileServiceState>,
) -> Result<FileOperationResult, String> {
    let service = state.service.lock().map_err(|e| e.to_string())?;
    service.append_file(&path, &contents).map_err(|e| e.to_string())
}

/// Delete a file
#[tauri::command]
pub async fn delete_file(
    path: String,
    state: State<'_, FileServiceState>,
) -> Result<FileOperationResult, String> {
    let service = state.service.lock().map_err(|e| e.to_string())?;
    service.delete_file(&path).map_err(|e| e.to_string())
}

/// Check if file exists
#[tauri::command]
pub async fn file_exists(
    path: String,
    state: State<'_, FileServiceState>,
) -> Result<bool, String> {
    let service = state.service.lock().map_err(|e| e.to_string())?;
    service.file_exists(&path).map_err(|e| e.to_string())
}

/// Get file metadata
#[tauri::command]
pub async fn get_file_metadata(
    path: String,
    state: State<'_, FileServiceState>,
) -> Result<FileMetadata, String> {
    let service = state.service.lock().map_err(|e| e.to_string())?;
    service.get_file_metadata(&path).map_err(|e| e.to_string())
}

/// List files in a directory
#[tauri::command]
pub async fn list_directory(
    path: String,
    state: State<'_, FileServiceState>,
) -> Result<Vec<FileMetadata>, String> {
    let service = state.service.lock().map_err(|e| e.to_string())?;
    service.list_directory(&path).map_err(|e| e.to_string())
}

/// Create a directory
#[tauri::command]
pub async fn create_directory(
    path: String,
    state: State<'_, FileServiceState>,
) -> Result<FileOperationResult, String> {
    let service = state.service.lock().map_err(|e| e.to_string())?;
    service.create_directory(&path).map_err(|e| e.to_string())
}

/// Delete a directory
#[tauri::command]
pub async fn delete_directory(
    path: String,
    recursive: bool,
    state: State<'_, FileServiceState>,
) -> Result<FileOperationResult, String> {
    let service = state.service.lock().map_err(|e| e.to_string())?;
    service.delete_directory(&path, recursive).map_err(|e| e.to_string())
}
