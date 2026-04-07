@echo off
REM DeepEcho Development Setup and Build Script for Windows
REM This script sets up the development environment and runs the application in development mode

setlocal enabledelayedexpansion

REM Colors are limited in Windows CMD, using simple text markers
set "SUCCESS=[OK]"
set "ERROR=[ERROR]"
set "WARNING=[WARNING]"
set "INFO=[INFO]"

REM Print header
:print_header
echo.
echo ==========================================
echo %~1
echo ==========================================
echo.
goto :eof

REM Check if command exists
:command_exists
where %1 >nul 2>&1
exit /b %errorlevel%

REM Check prerequisites
:check_prerequisites
call :print_header "Checking Prerequisites"

set missing_deps=0

REM Check Node.js
call :command_exists node
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('node --version') do set node_version=%%i
    echo %SUCCESS% Node.js: !node_version!
) else (
    echo %ERROR% Node.js is not installed
    echo %INFO% Install from: https://nodejs.org/
    set missing_deps=1
)

REM Check npm
call :command_exists npm
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('npm --version') do set npm_version=%%i
    echo %SUCCESS% npm: v!npm_version!
) else (
    echo %ERROR% npm is not installed
    set missing_deps=1
)

REM Check Rust
call :command_exists rustc
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('rustc --version') do set rust_version=%%i
    echo %SUCCESS% Rust: !rust_version!
) else (
    echo %ERROR% Rust is not installed
    echo %INFO% Install from: https://rustup.rs/
    set missing_deps=1
)

REM Check Cargo
call :command_exists cargo
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('cargo --version') do set cargo_version=%%i
    echo %SUCCESS% Cargo: !cargo_version!
) else (
    echo %ERROR% Cargo is not installed
    set missing_deps=1
)

REM Check Python
call :command_exists python
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('python --version') do set python_version=%%i
    echo %SUCCESS% Python: !python_version!
) else (
    echo %ERROR% Python is not installed
    echo %INFO% Install from: https://www.python.org/
    set missing_deps=1
)

REM Check pip
call :command_exists pip
if %errorlevel% equ 0 (
    for /f "tokens=2" %%i in ('pip --version') do set pip_version=%%i
    echo %SUCCESS% pip: v!pip_version!
) else (
    echo %ERROR% pip is not installed
    set missing_deps=1
)

echo %INFO% Platform: Windows
echo %INFO% Ensure Visual Studio Build Tools are installed

if !missing_deps! equ 1 (
    echo %ERROR% Missing required dependencies. Please install them and try again.
    exit /b 1
)

echo %SUCCESS% All prerequisites satisfied
goto :eof

REM Setup Python virtual environment
:setup_python_env
call :print_header "Setting Up Python Environment"

REM Check if virtual environment exists
if not exist ".venv" (
    echo %INFO% Creating Python virtual environment...
    python -m venv .venv
    echo %SUCCESS% Virtual environment created
) else (
    echo %INFO% Virtual environment already exists
)

REM Activate virtual environment
echo %INFO% Activating virtual environment...
call .venv\Scripts\activate.bat

REM Install/upgrade pip
echo %INFO% Upgrading pip...
python -m pip install --upgrade pip --quiet

REM Install Python dependencies
echo %INFO% Installing Python dependencies...
if exist "requirements.txt" (
    pip install -r requirements.txt --quiet
    echo %SUCCESS% Python dependencies installed
) else (
    echo %WARNING% requirements.txt not found
)

REM Install development dependencies
if exist "requirements-dev.txt" (
    echo %INFO% Installing development dependencies...
    pip install -r requirements-dev.txt --quiet
    echo %SUCCESS% Development dependencies installed
)

goto :eof

REM Setup frontend
:setup_frontend
call :print_header "Setting Up Frontend"

if not exist "frontend" (
    echo %ERROR% Frontend directory not found
    exit /b 1
)

cd frontend

REM Install dependencies
if not exist "node_modules" (
    echo %INFO% Installing frontend dependencies...
    call npm install
    echo %SUCCESS% Frontend dependencies installed
) else (
    echo %INFO% Frontend dependencies already installed
    echo %INFO% Run 'npm install' to update if needed
)

cd ..
goto :eof

REM Setup Tauri
:setup_tauri
call :print_header "Setting Up Tauri"

if not exist "src-tauri" (
    echo %ERROR% src-tauri directory not found
    exit /b 1
)

cd src-tauri

REM Check Tauri CLI
call :command_exists cargo-tauri
if %errorlevel% neq 0 (
    echo %INFO% Installing Tauri CLI...
    cargo install tauri-cli
    echo %SUCCESS% Tauri CLI installed
) else (
    echo %INFO% Tauri CLI already installed
)

REM Build Tauri dependencies
echo %INFO% Building Tauri dependencies...
cargo build
echo %SUCCESS% Tauri dependencies built

cd ..
goto :eof

REM Setup configuration
:setup_config
call :print_header "Setting Up Configuration"

REM Check for API keys
if not exist "keys.py" (
    if exist "keys.example.py" (
        echo %WARNING% keys.py not found
        echo %INFO% Copying keys.example.py to keys.py...
        copy keys.example.py keys.py
        echo %WARNING% Please edit keys.py and add your API keys
    ) else (
        echo %ERROR% keys.example.py not found
    )
) else (
    echo %SUCCESS% keys.py exists
)

REM Check for config files
if exist "resources" (
    if not exist "resources\config.json" (
        if exist "resources\config.example.json" (
            echo %INFO% Copying config.example.json to config.json...
            copy resources\config.example.json resources\config.json
            echo %SUCCESS% Configuration file created
        )
    ) else (
        echo %SUCCESS% Configuration file exists
    )
)

goto :eof

REM Run development server
:run_dev
call :print_header "Starting Development Server"

echo %INFO% Starting DeepEcho in development mode...
echo %INFO% This will start:
echo %INFO%   1. Frontend dev server (Vite)
echo %INFO%   2. Tauri application
echo %INFO%   3. Python backend service
echo.
echo %WARNING% Press Ctrl+C to stop all services
echo.

REM Run Tauri dev (this will start frontend and backend)
cd src-tauri
cargo tauri dev
cd ..
goto :eof

REM Run frontend only
:run_frontend_only
call :print_header "Starting Frontend Only"

cd frontend
echo %INFO% Starting frontend dev server on http://localhost:5173
call npm run dev
cd ..
goto :eof

REM Run backend only
:run_backend_only
call :print_header "Starting Backend Only"

REM Activate virtual environment
call .venv\Scripts\activate.bat

echo %INFO% Starting Python backend service...
python src\backend_service.py
goto :eof

REM Clean build artifacts
:clean
call :print_header "Cleaning Build Artifacts"

REM Clean frontend
if exist "frontend\dist" (
    echo %INFO% Cleaning frontend build...
    rmdir /s /q frontend\dist
    echo %SUCCESS% Frontend build cleaned
)

REM Clean Tauri
if exist "src-tauri\target" (
    echo %INFO% Cleaning Tauri build...
    cd src-tauri
    cargo clean
    cd ..
    echo %SUCCESS% Tauri build cleaned
)

REM Clean Python cache
echo %INFO% Cleaning Python cache...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
del /s /q *.pyc >nul 2>&1
echo %SUCCESS% Python cache cleaned

echo %SUCCESS% All build artifacts cleaned
goto :eof

REM Show help
:show_help
echo DeepEcho Development Script
echo.
echo Usage: dev.bat [command]
echo.
echo Commands:
echo   setup       - Setup development environment (install dependencies)
echo   dev         - Run full development server (default)
echo   frontend    - Run frontend only
echo   backend     - Run backend only
echo   clean       - Clean build artifacts
echo   check       - Check prerequisites only
echo   help        - Show this help message
echo.
echo Examples:
echo   dev.bat setup    # First time setup
echo   dev.bat dev      # Run development server
echo   dev.bat frontend # Run frontend only
echo   dev.bat clean    # Clean build artifacts
echo.
goto :eof

REM Main script
:main
set command=%1
if "%command%"=="" set command=dev

if "%command%"=="setup" (
    call :check_prerequisites
    if errorlevel 1 exit /b 1
    call :setup_python_env
    call :setup_frontend
    call :setup_tauri
    call :setup_config
    echo %SUCCESS% Development environment setup complete!
    echo %INFO% Run 'dev.bat dev' to start the development server
) else if "%command%"=="dev" (
    call :check_prerequisites
    if errorlevel 1 exit /b 1
    call :run_dev
) else if "%command%"=="frontend" (
    call :run_frontend_only
) else if "%command%"=="backend" (
    call :run_backend_only
) else if "%command%"=="clean" (
    call :clean
) else if "%command%"=="check" (
    call :check_prerequisites
) else if "%command%"=="help" (
    call :show_help
) else if "%command%"=="--help" (
    call :show_help
) else if "%command%"=="-h" (
    call :show_help
) else (
    echo %ERROR% Unknown command: %command%
    echo.
    call :show_help
    exit /b 1
)

goto :eof

REM Entry point
call :main %*
