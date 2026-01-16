// File service for secure file operations
use std::path::{Path, PathBuf};
use std::fs;
use anyhow::{Result, Context, bail};
use serde::{Deserialize, Serialize};

/// File operation result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FileOperationResult {
    pub success: bool,
    pub message: String,
    pub path: Option<String>,
}

/// File metadata information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FileMetadata {
    pub path: String,
    pub size: u64,
    pub is_file: bool,
    pub is_dir: bool,
    pub modified: Option<String>,
    pub created: Option<String>,
}

/// File service for handling file operations with security checks
pub struct FileService {
    allowed_directories: Vec<PathBuf>,
}

impl FileService {
    /// Create a new file service with allowed directories
    pub fn new(allowed_directories: Vec<PathBuf>) -> Self {
        Self {
            allowed_directories,
        }
    }

    /// Create a default file service with common allowed directories
    pub fn default_with_app_dirs(app_data_dir: PathBuf, app_config_dir: PathBuf, app_log_dir: PathBuf) -> Self {
        Self {
            allowed_directories: vec![app_data_dir, app_config_dir, app_log_dir],
        }
    }

    /// Validate that a path is within allowed directories
    fn validate_path(&self, path: &Path) -> Result<PathBuf> {
        let canonical_path = path.canonicalize()
            .or_else(|_| {
                // If path doesn't exist yet, try to canonicalize parent
                if let Some(parent) = path.parent() {
                    if let Ok(canonical_parent) = parent.canonicalize() {
                        Ok(canonical_parent.join(path.file_name().unwrap()))
                    } else {
                        bail!("Invalid path: cannot resolve parent directory")
                    }
                } else {
                    bail!("Invalid path: cannot resolve")
                }
            })?;

        // Check if path is within any allowed directory
        for allowed_dir in &self.allowed_directories {
            if canonical_path.starts_with(allowed_dir) {
                return Ok(canonical_path);
            }
        }

        bail!("Access denied: path is outside allowed directories")
    }

    /// Read file contents as string
    pub fn read_file(&self, path: &str) -> Result<String> {
        let path = Path::new(path);
        let validated_path = self.validate_path(path)?;

        fs::read_to_string(&validated_path)
            .with_context(|| format!("Failed to read file: {}", validated_path.display()))
    }

    /// Read file contents as bytes
    pub fn read_file_bytes(&self, path: &str) -> Result<Vec<u8>> {
        let path = Path::new(path);
        let validated_path = self.validate_path(path)?;

        fs::read(&validated_path)
            .with_context(|| format!("Failed to read file: {}", validated_path.display()))
    }

    /// Write string contents to file
    pub fn write_file(&self, path: &str, contents: &str) -> Result<FileOperationResult> {
        let path = Path::new(path);
        let validated_path = self.validate_path(path)?;

        // Create parent directories if they don't exist
        if let Some(parent) = validated_path.parent() {
            fs::create_dir_all(parent)
                .context("Failed to create parent directories")?;
        }

        fs::write(&validated_path, contents)
            .with_context(|| format!("Failed to write file: {}", validated_path.display()))?;

        Ok(FileOperationResult {
            success: true,
            message: "File written successfully".to_string(),
            path: Some(validated_path.to_string_lossy().to_string()),
        })
    }

    /// Write bytes to file
    pub fn write_file_bytes(&self, path: &str, contents: &[u8]) -> Result<FileOperationResult> {
        let path = Path::new(path);
        let validated_path = self.validate_path(path)?;

        // Create parent directories if they don't exist
        if let Some(parent) = validated_path.parent() {
            fs::create_dir_all(parent)
                .context("Failed to create parent directories")?;
        }

        fs::write(&validated_path, contents)
            .with_context(|| format!("Failed to write file: {}", validated_path.display()))?;

        Ok(FileOperationResult {
            success: true,
            message: "File written successfully".to_string(),
            path: Some(validated_path.to_string_lossy().to_string()),
        })
    }

    /// Append string contents to file
    pub fn append_file(&self, path: &str, contents: &str) -> Result<FileOperationResult> {
        let path = Path::new(path);
        let validated_path = self.validate_path(path)?;

        // Create parent directories if they don't exist
        if let Some(parent) = validated_path.parent() {
            fs::create_dir_all(parent)
                .context("Failed to create parent directories")?;
        }

        use std::io::Write;
        let mut file = fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(&validated_path)
            .with_context(|| format!("Failed to open file for appending: {}", validated_path.display()))?;

        file.write_all(contents.as_bytes())
            .context("Failed to append to file")?;

        Ok(FileOperationResult {
            success: true,
            message: "Content appended successfully".to_string(),
            path: Some(validated_path.to_string_lossy().to_string()),
        })
    }

    /// Delete a file
    pub fn delete_file(&self, path: &str) -> Result<FileOperationResult> {
        let path = Path::new(path);
        let validated_path = self.validate_path(path)?;

        if !validated_path.exists() {
            bail!("File does not exist: {}", validated_path.display());
        }

        if !validated_path.is_file() {
            bail!("Path is not a file: {}", validated_path.display());
        }

        fs::remove_file(&validated_path)
            .with_context(|| format!("Failed to delete file: {}", validated_path.display()))?;

        Ok(FileOperationResult {
            success: true,
            message: "File deleted successfully".to_string(),
            path: Some(validated_path.to_string_lossy().to_string()),
        })
    }

    /// Check if file exists
    pub fn file_exists(&self, path: &str) -> Result<bool> {
        let path = Path::new(path);
        let validated_path = self.validate_path(path)?;
        Ok(validated_path.exists() && validated_path.is_file())
    }

    /// Get file metadata
    pub fn get_file_metadata(&self, path: &str) -> Result<FileMetadata> {
        let path = Path::new(path);
        let validated_path = self.validate_path(path)?;

        let metadata = fs::metadata(&validated_path)
            .with_context(|| format!("Failed to get metadata: {}", validated_path.display()))?;

        let modified = metadata.modified()
            .ok()
            .and_then(|t| {
                use std::time::SystemTime;
                t.duration_since(SystemTime::UNIX_EPOCH)
                    .ok()
                    .map(|d| chrono::DateTime::from_timestamp(d.as_secs() as i64, 0))
                    .flatten()
                    .map(|dt| dt.to_rfc3339())
            });

        let created = metadata.created()
            .ok()
            .and_then(|t| {
                use std::time::SystemTime;
                t.duration_since(SystemTime::UNIX_EPOCH)
                    .ok()
                    .map(|d| chrono::DateTime::from_timestamp(d.as_secs() as i64, 0))
                    .flatten()
                    .map(|dt| dt.to_rfc3339())
            });

        Ok(FileMetadata {
            path: validated_path.to_string_lossy().to_string(),
            size: metadata.len(),
            is_file: metadata.is_file(),
            is_dir: metadata.is_dir(),
            modified,
            created,
        })
    }

    /// List files in a directory
    pub fn list_directory(&self, path: &str) -> Result<Vec<FileMetadata>> {
        let path = Path::new(path);
        let validated_path = self.validate_path(path)?;

        if !validated_path.is_dir() {
            bail!("Path is not a directory: {}", validated_path.display());
        }

        let entries = fs::read_dir(&validated_path)
            .with_context(|| format!("Failed to read directory: {}", validated_path.display()))?;

        let mut results = Vec::new();
        for entry in entries {
            let entry = entry.context("Failed to read directory entry")?;
            let entry_path = entry.path();
            
            if let Ok(metadata) = self.get_file_metadata(&entry_path.to_string_lossy()) {
                results.push(metadata);
            }
        }

        Ok(results)
    }

    /// Create a directory
    pub fn create_directory(&self, path: &str) -> Result<FileOperationResult> {
        let path = Path::new(path);
        let validated_path = self.validate_path(path)?;

        fs::create_dir_all(&validated_path)
            .with_context(|| format!("Failed to create directory: {}", validated_path.display()))?;

        Ok(FileOperationResult {
            success: true,
            message: "Directory created successfully".to_string(),
            path: Some(validated_path.to_string_lossy().to_string()),
        })
    }

    /// Delete a directory
    pub fn delete_directory(&self, path: &str, recursive: bool) -> Result<FileOperationResult> {
        let path = Path::new(path);
        let validated_path = self.validate_path(path)?;

        if !validated_path.exists() {
            bail!("Directory does not exist: {}", validated_path.display());
        }

        if !validated_path.is_dir() {
            bail!("Path is not a directory: {}", validated_path.display());
        }

        if recursive {
            fs::remove_dir_all(&validated_path)
                .with_context(|| format!("Failed to delete directory: {}", validated_path.display()))?;
        } else {
            fs::remove_dir(&validated_path)
                .with_context(|| format!("Failed to delete directory: {}", validated_path.display()))?;
        }

        Ok(FileOperationResult {
            success: true,
            message: "Directory deleted successfully".to_string(),
            path: Some(validated_path.to_string_lossy().to_string()),
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::env;

    #[test]
    fn test_file_service_security() {
        let temp_dir = env::temp_dir().canonicalize().unwrap();
        let service = FileService::new(vec![temp_dir.clone()]);

        // Test valid path
        let valid_path = temp_dir.join("test.txt");
        assert!(service.validate_path(&valid_path).is_ok());

        // Test invalid path (outside allowed directories)
        // Use a path that definitely exists for canonicalization
        let home_dir = env::var("HOME")
            .or_else(|_| env::var("USERPROFILE"))
            .unwrap();
        let invalid_path = PathBuf::from(home_dir);
        
        // Only test if the invalid path is actually outside temp_dir
        if !invalid_path.starts_with(&temp_dir) {
            assert!(service.validate_path(&invalid_path).is_err());
        }
    }

    #[test]
    fn test_file_operations() {
        let temp_dir = env::temp_dir().canonicalize().unwrap();
        let service = FileService::new(vec![temp_dir.clone()]);

        let test_file = temp_dir.join("test_file_service.txt");
        let test_path = test_file.to_string_lossy().to_string();

        // Write file
        let result = service.write_file(&test_path, "Hello, World!");
        assert!(result.is_ok(), "Failed to write file: {:?}", result.err());

        // Read file
        let content = service.read_file(&test_path);
        assert!(content.is_ok());
        assert_eq!(content.unwrap(), "Hello, World!");

        // Check file exists
        let exists = service.file_exists(&test_path);
        assert!(exists.is_ok());
        assert!(exists.unwrap());

        // Get metadata
        let metadata = service.get_file_metadata(&test_path);
        assert!(metadata.is_ok());

        // Delete file
        let result = service.delete_file(&test_path);
        assert!(result.is_ok());

        // Verify deletion
        let exists = service.file_exists(&test_path);
        assert!(exists.is_ok());
        assert!(!exists.unwrap());
    }
}
