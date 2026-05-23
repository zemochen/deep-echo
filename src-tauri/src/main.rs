// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::Manager;

// Import command modules
mod commands {
    pub mod audio;
    pub mod transcription;
    pub mod ai;
    pub mod config;
    pub mod system;
    pub mod file;
    pub mod system_info;
    pub mod python_service;
}

// Import models
mod models {
    pub mod request;
    pub mod response;
    pub mod event;
}

// Import handlers
mod handlers {
    pub mod ipc_handler;
    pub mod event_handler;
    pub mod error_handler;
}

// Import services
mod services {
    pub mod file_service;
    pub mod system_service;
    pub mod python_service;
}

use commands::audio::{AudioState, start_recording, stop_recording};
use commands::transcription::{TranscriptionState, get_transcript};
use commands::ai::{AIState, generate_response, switch_provider};
use commands::config::{ConfigState, get_config, update_config};
use commands::system::{get_system_info, get_audio_devices, set_audio_device};
use commands::file::{FileServiceState, read_file, write_file, append_file, delete_file, 
                      file_exists, get_file_metadata, list_directory, create_directory, delete_directory};
use commands::system_info::{SystemServiceState, get_system_information, get_audio_device_list,
                             get_network_interfaces, get_disk_information, get_environment_variables,
                             get_current_directory, get_system_locale};
use commands::python_service::{PythonServiceState, start_python_service, stop_python_service,
                                restart_python_service, get_python_service_status,
                                start_service_monitoring, stop_service_monitoring,
                                check_service_health, reset_service_restart_count};
use handlers::event_handler::EventHandlerState;
use handlers::error_handler::ErrorHandlerState;
use services::file_service::FileService;
use services::system_service::SystemService;
use services::python_service::PythonServiceConfig;

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            #[cfg(debug_assertions)]
            {
                let window = app.get_window("main").unwrap();
                window.open_devtools();
            }

            // Initialize file service with app directories
            let app_data_dir = app.path_resolver()
                .app_data_dir()
                .expect("Failed to get app data directory");
            let app_config_dir = app.path_resolver()
                .app_config_dir()
                .expect("Failed to get app config directory");
            let app_log_dir = app.path_resolver()
                .app_log_dir()
                .expect("Failed to get app log directory");

            let file_service = FileService::default_with_app_dirs(
                app_data_dir,
                app_config_dir,
                app_log_dir,
            );
            app.manage(FileServiceState::new(file_service));

            // Initialize system service
            let system_service = SystemService::new();
            app.manage(SystemServiceState::new(system_service));

            // Initialize Python service
            let python_config = PythonServiceConfig {
                python_path: "python3".to_string(),
                service_script: "backend/backend_service.py".to_string(),
                working_dir: Some("..".to_string()),
                env_vars: Vec::new(),
                startup_timeout: 30,
                health_check_interval: 10,
                max_restart_attempts: 3,
                restart_delay: 5,
            };
            let python_service_state = PythonServiceState::new(python_config);

            // Auto-start Python service
            {
                let service = python_service_state.get_service();
                match service.start() {
                    Ok(_) => println!("✓ Python service auto-started successfully"),
                    Err(e) => eprintln!("✗ Failed to auto-start Python service: {}", e),
                }
            }

            app.manage(python_service_state);

            Ok(())
        })
        .manage(AudioState::default())
        .manage(TranscriptionState::default())
        .manage(AIState::default())
        .manage(ConfigState::default())
        .manage(EventHandlerState::default())
        .manage(ErrorHandlerState::default())
        .invoke_handler(tauri::generate_handler![
            // Audio commands
            start_recording,
            stop_recording,
            // Transcription commands
            get_transcript,
            // AI commands
            generate_response,
            switch_provider,
            // Config commands
            get_config,
            update_config,
            // System commands
            get_system_info,
            get_audio_devices,
            set_audio_device,
            // File service commands
            read_file,
            write_file,
            append_file,
            delete_file,
            file_exists,
            get_file_metadata,
            list_directory,
            create_directory,
            delete_directory,
            // System information commands
            get_system_information,
            get_audio_device_list,
            get_network_interfaces,
            get_disk_information,
            get_environment_variables,
            get_current_directory,
            get_system_locale,
            // Python service commands
            start_python_service,
            stop_python_service,
            restart_python_service,
            get_python_service_status,
            start_service_monitoring,
            stop_service_monitoring,
            check_service_health,
            reset_service_restart_count,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
