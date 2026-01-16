@echo off
REM Script to check if Tauri development environment is properly set up

echo ===================================
echo Tauri Development Environment Check
echo ===================================
echo.

REM Check Rust
echo Checking Rust installation...
rustc --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('rustc --version') do set RUST_VERSION=%%i
    echo [OK] Rust is installed: %RUST_VERSION%
) else (
    echo [FAIL] Rust is NOT installed
    echo   Please install from: https://rustup.rs/
    exit /b 1
)

REM Check Cargo
echo.
echo Checking Cargo installation...
cargo --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('cargo --version') do set CARGO_VERSION=%%i
    echo [OK] Cargo is installed: %CARGO_VERSION%
) else (
    echo [FAIL] Cargo is NOT installed
    echo   Cargo should be installed with Rust
    exit /b 1
)

REM Check Tauri CLI
echo.
echo Checking Tauri CLI...
cargo tauri --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('cargo tauri --version') do set TAURI_VERSION=%%i
    echo [OK] Tauri CLI is installed: %TAURI_VERSION%
) else (
    echo [FAIL] Tauri CLI is NOT installed
    echo   Install with: cargo install tauri-cli
    echo   (This may take several minutes)
)

echo.
echo ===================================
echo Setup check complete!
echo ===================================
echo.
echo Please ensure the following are also installed:
echo   - Microsoft C++ Build Tools
echo   - WebView2 Runtime
echo.
echo If all checks passed, you can proceed with:
echo   cd src-tauri
echo   cargo build
