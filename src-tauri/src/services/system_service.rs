// System service for retrieving system information and device enumeration
use serde::{Deserialize, Serialize};
use anyhow::{Result, Context};
use std::collections::HashMap;

/// System information structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SystemInfo {
    pub os: String,
    pub os_version: String,
    pub arch: String,
    pub hostname: String,
    pub cpu_count: usize,
    pub total_memory: u64,
    pub available_memory: u64,
    pub uptime: u64,
}

/// Audio device information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AudioDevice {
    pub id: String,
    pub name: String,
    pub device_type: String, // "input" or "output"
    pub is_default: bool,
    pub sample_rate: Option<u32>,
    pub channels: Option<u32>,
}

/// Network interface information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NetworkInterface {
    pub name: String,
    pub mac_address: Option<String>,
    pub ip_addresses: Vec<String>,
    pub is_up: bool,
    pub is_loopback: bool,
}

/// Disk information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DiskInfo {
    pub name: String,
    pub mount_point: String,
    pub total_space: u64,
    pub available_space: u64,
    pub file_system: String,
}

/// System service for retrieving system information
pub struct SystemService;

impl SystemService {
    /// Create a new system service
    pub fn new() -> Self {
        Self
    }

    /// Get comprehensive system information
    pub fn get_system_info(&self) -> Result<SystemInfo> {
        let os = std::env::consts::OS.to_string();
        let arch = std::env::consts::ARCH.to_string();
        
        // Get OS version
        let os_version = self.get_os_version()?;
        
        // Get hostname
        let hostname = hostname::get()
            .context("Failed to get hostname")?
            .to_string_lossy()
            .to_string();

        // Get CPU count
        let cpu_count = num_cpus::get();

        // Get memory information
        let (total_memory, available_memory) = self.get_memory_info()?;

        // Get system uptime
        let uptime = self.get_uptime()?;

        Ok(SystemInfo {
            os,
            os_version,
            arch,
            hostname,
            cpu_count,
            total_memory,
            available_memory,
            uptime,
        })
    }

    /// Get OS version string
    fn get_os_version(&self) -> Result<String> {
        #[cfg(target_os = "windows")]
        {
            Ok(format!("Windows {}", self.get_windows_version()?))
        }

        #[cfg(target_os = "macos")]
        {
            Ok(format!("macOS {}", self.get_macos_version()?))
        }

        #[cfg(target_os = "linux")]
        {
            Ok(format!("Linux {}", self.get_linux_version()?))
        }

        #[cfg(not(any(target_os = "windows", target_os = "macos", target_os = "linux")))]
        {
            Ok("Unknown".to_string())
        }
    }

    #[cfg(target_os = "windows")]
    fn get_windows_version(&self) -> Result<String> {
        use std::process::Command;
        let output = Command::new("cmd")
            .args(&["/C", "ver"])
            .output()
            .context("Failed to execute ver command")?;
        
        let version = String::from_utf8_lossy(&output.stdout);
        Ok(version.trim().to_string())
    }

    #[cfg(target_os = "macos")]
    fn get_macos_version(&self) -> Result<String> {
        use std::process::Command;
        let output = Command::new("sw_vers")
            .arg("-productVersion")
            .output()
            .context("Failed to execute sw_vers command")?;
        
        let version = String::from_utf8_lossy(&output.stdout);
        Ok(version.trim().to_string())
    }

    #[cfg(target_os = "linux")]
    fn get_linux_version(&self) -> Result<String> {
        use std::fs;
        let content = fs::read_to_string("/etc/os-release")
            .context("Failed to read /etc/os-release")?;
        
        for line in content.lines() {
            if line.starts_with("PRETTY_NAME=") {
                let version = line.trim_start_matches("PRETTY_NAME=")
                    .trim_matches('"');
                return Ok(version.to_string());
            }
        }
        
        Ok("Unknown".to_string())
    }

    /// Get memory information (total and available in bytes)
    fn get_memory_info(&self) -> Result<(u64, u64)> {
        use sysinfo::System;
        
        let mut sys = System::new_all();
        sys.refresh_memory();
        
        let total = sys.total_memory();
        let available = sys.available_memory();
        
        Ok((total, available))
    }

    /// Get system uptime in seconds
    fn get_uptime(&self) -> Result<u64> {
        use sysinfo::System;
        Ok(System::uptime())
    }

    /// Get list of audio devices
    pub fn get_audio_devices(&self) -> Result<Vec<AudioDevice>> {
        let mut devices = Vec::new();

        // Use cpal to enumerate audio devices
        #[cfg(feature = "audio-devices")]
        {
            use cpal::traits::{DeviceTrait, HostTrait};
            
            let host = cpal::default_host();
            
            // Get default devices
            let default_input = host.default_input_device();
            let default_output = host.default_output_device();
            
            // Enumerate input devices
            if let Ok(input_devices) = host.input_devices() {
                for (idx, device) in input_devices.enumerate() {
                    if let Ok(name) = device.name() {
                        let is_default = default_input.as_ref()
                            .and_then(|d| d.name().ok())
                            .map(|n| n == name)
                            .unwrap_or(false);
                        
                        let (sample_rate, channels) = device.default_input_config()
                            .ok()
                            .map(|config| (Some(config.sample_rate().0), Some(config.channels() as u32)))
                            .unwrap_or((None, None));
                        
                        devices.push(AudioDevice {
                            id: format!("input_{}", idx),
                            name,
                            device_type: "input".to_string(),
                            is_default,
                            sample_rate,
                            channels,
                        });
                    }
                }
            }
            
            // Enumerate output devices
            if let Ok(output_devices) = host.output_devices() {
                for (idx, device) in output_devices.enumerate() {
                    if let Ok(name) = device.name() {
                        let is_default = default_output.as_ref()
                            .and_then(|d| d.name().ok())
                            .map(|n| n == name)
                            .unwrap_or(false);
                        
                        let (sample_rate, channels) = device.default_output_config()
                            .ok()
                            .map(|config| (Some(config.sample_rate().0), Some(config.channels() as u32)))
                            .unwrap_or((None, None));
                        
                        devices.push(AudioDevice {
                            id: format!("output_{}", idx),
                            name,
                            device_type: "output".to_string(),
                            is_default,
                            sample_rate,
                            channels,
                        });
                    }
                }
            }
        }

        // Fallback: return mock devices if audio enumeration is not available
        #[cfg(not(feature = "audio-devices"))]
        {
            devices.push(AudioDevice {
                id: "default_input".to_string(),
                name: "Default Microphone".to_string(),
                device_type: "input".to_string(),
                is_default: true,
                sample_rate: Some(44100),
                channels: Some(1),
            });
            
            devices.push(AudioDevice {
                id: "default_output".to_string(),
                name: "Default Speaker".to_string(),
                device_type: "output".to_string(),
                is_default: true,
                sample_rate: Some(44100),
                channels: Some(2),
            });
        }

        Ok(devices)
    }

    /// Get network interfaces
    pub fn get_network_interfaces(&self) -> Result<Vec<NetworkInterface>> {
        use pnet::datalink;
        
        let interfaces = datalink::interfaces();
        let mut result = Vec::new();

        for interface in interfaces {
            let ip_addresses: Vec<String> = interface.ips
                .iter()
                .map(|ip| ip.ip().to_string())
                .collect();

            let mac_address = interface.mac.map(|mac| mac.to_string());

            result.push(NetworkInterface {
                name: interface.name.clone(),
                mac_address,
                ip_addresses,
                is_up: interface.is_up(),
                is_loopback: interface.is_loopback(),
            });
        }

        Ok(result)
    }

    /// Get disk information
    pub fn get_disk_info(&self) -> Result<Vec<DiskInfo>> {
        // Note: sysinfo 0.30 has limited disk API
        // For now, return empty list or use platform-specific methods
        let disks = Vec::new();
        
        // TODO: Implement platform-specific disk enumeration if needed
        // For Windows: use WMI or GetLogicalDrives
        // For macOS/Linux: parse /proc/mounts or use statvfs
        
        Ok(disks)
    }

    /// Get environment variables (filtered for security)
    pub fn get_environment_variables(&self, filter: Option<Vec<String>>) -> Result<HashMap<String, String>> {
        let mut env_vars = HashMap::new();

        if let Some(allowed_keys) = filter {
            for key in allowed_keys {
                if let Ok(value) = std::env::var(&key) {
                    env_vars.insert(key, value);
                }
            }
        } else {
            // Return only safe environment variables
            let safe_keys = vec![
                "PATH", "HOME", "USER", "SHELL", "LANG", "TERM",
                "TMPDIR", "TEMP", "TMP", "APPDATA", "LOCALAPPDATA",
            ];
            
            for key in safe_keys {
                if let Ok(value) = std::env::var(key) {
                    env_vars.insert(key.to_string(), value);
                }
            }
        }

        Ok(env_vars)
    }

    /// Get current working directory
    pub fn get_current_directory(&self) -> Result<String> {
        let cwd = std::env::current_dir()
            .context("Failed to get current directory")?;
        Ok(cwd.to_string_lossy().to_string())
    }

    /// Get system locale
    pub fn get_system_locale(&self) -> Result<String> {
        #[cfg(target_os = "windows")]
        {
            use std::process::Command;
            let output = Command::new("powershell")
                .args(&["-Command", "Get-Culture | Select-Object -ExpandProperty Name"])
                .output()
                .context("Failed to get system locale")?;
            
            let locale = String::from_utf8_lossy(&output.stdout);
            Ok(locale.trim().to_string())
        }

        #[cfg(not(target_os = "windows"))]
        {
            std::env::var("LANG")
                .or_else(|_| std::env::var("LC_ALL"))
                .context("Failed to get system locale")
        }
    }
}

impl Default for SystemService {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_get_system_info() {
        let service = SystemService::new();
        let info = service.get_system_info();
        assert!(info.is_ok());
        
        let info = info.unwrap();
        assert!(!info.os.is_empty());
        assert!(!info.arch.is_empty());
        assert!(info.cpu_count > 0);
        assert!(info.total_memory > 0);
    }

    #[test]
    fn test_get_audio_devices() {
        let service = SystemService::new();
        let devices = service.get_audio_devices();
        assert!(devices.is_ok());
        
        let devices = devices.unwrap();
        assert!(!devices.is_empty());
    }

    #[test]
    fn test_get_environment_variables() {
        let service = SystemService::new();
        let env_vars = service.get_environment_variables(None);
        assert!(env_vars.is_ok());
        
        let env_vars = env_vars.unwrap();
        assert!(!env_vars.is_empty());
    }

    #[test]
    fn test_get_current_directory() {
        let service = SystemService::new();
        let cwd = service.get_current_directory();
        assert!(cwd.is_ok());
        assert!(!cwd.unwrap().is_empty());
    }
}
