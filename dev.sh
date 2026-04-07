#!/bin/bash

# DeepEcho Development Setup and Build Script
# This script sets up the development environment and runs the application in development mode

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored message
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_header() {
    echo ""
    print_message "$BLUE" "=========================================="
    print_message "$BLUE" "$1"
    print_message "$BLUE" "=========================================="
    echo ""
}

print_success() {
    print_message "$GREEN" "✓ $1"
}

print_error() {
    print_message "$RED" "✗ $1"
}

print_warning() {
    print_message "$YELLOW" "⚠ $1"
}

print_info() {
    print_message "$BLUE" "ℹ $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    local missing_deps=0
    
    # Check Node.js
    if command_exists node; then
        local node_version=$(node --version)
        print_success "Node.js: $node_version"
    else
        print_error "Node.js is not installed"
        print_info "Install from: https://nodejs.org/"
        missing_deps=1
    fi
    
    # Check npm
    if command_exists npm; then
        local npm_version=$(npm --version)
        print_success "npm: v$npm_version"
    else
        print_error "npm is not installed"
        missing_deps=1
    fi
    
    # Check Rust
    if command_exists rustc; then
        local rust_version=$(rustc --version)
        print_success "Rust: $rust_version"
    else
        print_error "Rust is not installed"
        print_info "Install from: https://rustup.rs/"
        missing_deps=1
    fi
    
    # Check Cargo
    if command_exists cargo; then
        local cargo_version=$(cargo --version)
        print_success "Cargo: $cargo_version"
    else
        print_error "Cargo is not installed"
        missing_deps=1
    fi
    
    # Check Python
    if command_exists python3; then
        local python_version=$(python3 --version)
        print_success "Python: $python_version"
    else
        print_error "Python 3 is not installed"
        print_info "Install from: https://www.python.org/"
        missing_deps=1
    fi
    
    # Check pip
    if command_exists pip3; then
        local pip_version=$(pip3 --version | cut -d' ' -f2)
        print_success "pip: v$pip_version"
    else
        print_error "pip3 is not installed"
        missing_deps=1
    fi
    
    # Platform-specific checks
    if [[ "$OSTYPE" == "darwin"* ]]; then
        print_info "Platform: macOS"
        
        # Check for PortAudio
        if brew list portaudio &>/dev/null; then
            print_success "PortAudio: installed"
        else
            print_warning "PortAudio not found"
            print_info "Install with: brew install portaudio"
        fi
        
        # Check for BlackHole
        if brew list blackhole-2ch &>/dev/null; then
            print_success "BlackHole: installed"
        else
            print_warning "BlackHole not found (optional for speaker capture)"
            print_info "Install with: brew install blackhole-2ch"
        fi
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        print_info "Platform: Windows"
        print_info "Ensure Visual Studio Build Tools are installed"
    else
        print_info "Platform: Linux"
        print_info "Ensure ALSA development libraries are installed"
    fi
    
    if [ $missing_deps -eq 1 ]; then
        print_error "Missing required dependencies. Please install them and try again."
        exit 1
    fi
    
    print_success "All prerequisites satisfied"
}

# Setup Python virtual environment
setup_python_env() {
    print_header "Setting Up Python Environment"
    
    # Check if virtual environment exists
    if [ ! -d ".venv" ]; then
        print_info "Creating Python virtual environment..."
        python3 -m venv .venv
        print_success "Virtual environment created"
    else
        print_info "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    print_info "Activating virtual environment..."
    source .venv/bin/activate
    
    # Install/upgrade pip
    print_info "Upgrading pip..."
    pip install --upgrade pip --quiet
    
    # Install Python dependencies
    print_info "Installing Python dependencies..."
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt --quiet
        print_success "Python dependencies installed"
    else
        print_warning "requirements.txt not found"
    fi
    
    # Install development dependencies
    if [ -f "requirements-dev.txt" ]; then
        print_info "Installing development dependencies..."
        pip install -r requirements-dev.txt --quiet
        print_success "Development dependencies installed"
    fi
}

# Setup frontend
setup_frontend() {
    print_header "Setting Up Frontend"
    
    if [ ! -d "frontend" ]; then
        print_error "Frontend directory not found"
        return 1
    fi
    
    cd frontend
    
    # Install dependencies
    if [ ! -d "node_modules" ]; then
        print_info "Installing frontend dependencies..."
        npm install
        print_success "Frontend dependencies installed"
    else
        print_info "Frontend dependencies already installed"
        print_info "Run 'npm install' to update if needed"
    fi
    
    cd ..
}

# Setup Tauri
setup_tauri() {
    print_header "Setting Up Tauri"
    
    if [ ! -d "src-tauri" ]; then
        print_error "src-tauri directory not found"
        return 1
    fi
    
    cd src-tauri
    
    # Check Tauri CLI
    if ! command_exists cargo-tauri; then
        print_info "Installing Tauri CLI..."
        cargo install tauri-cli
        print_success "Tauri CLI installed"
    else
        print_info "Tauri CLI already installed"
    fi
    
    # Build Tauri dependencies
    print_info "Building Tauri dependencies..."
    cargo build
    print_success "Tauri dependencies built"
    
    cd ..
}

# Setup configuration
setup_config() {
    print_header "Setting Up Configuration"
    
    # Check for API keys
    if [ ! -f "keys.py" ]; then
        if [ -f "keys.example.py" ]; then
            print_warning "keys.py not found"
            print_info "Copying keys.example.py to keys.py..."
            cp keys.example.py keys.py
            print_warning "Please edit keys.py and add your API keys"
        else
            print_error "keys.example.py not found"
        fi
    else
        print_success "keys.py exists"
    fi
    
    # Check for config files
    if [ -d "resources" ]; then
        if [ ! -f "resources/config.json" ]; then
            if [ -f "resources/config.example.json" ]; then
                print_info "Copying config.example.json to config.json..."
                cp resources/config.example.json resources/config.json
                print_success "Configuration file created"
            fi
        else
            print_success "Configuration file exists"
        fi
    fi
}

# Run development server
run_dev() {
    print_header "Starting Development Server"

    print_info "Starting DeepEcho in development mode..."
    print_info "This will start:"
    print_info "  1. Frontend dev server (Vite)"
    print_info "  2. Tauri application"
    print_info "  3. Python backend service"
    echo ""
    print_warning "Press Ctrl+C to stop all services"
    echo ""

    # Check if Python backend can be imported
    print_info "Checking Python backend..."
    if python3 -c "import sys; import os; sys.path.insert(0, os.path.abspath('.')); import backend.backend_service" 2>/dev/null; then
        print_success "Python backend module is importable"
    else
        print_error "Python backend module cannot be imported"
        print_info "This may cause backend service to fail"
        print_warning "Attempting to continue anyway..."
    fi
    echo ""

    cd src-tauri
    cargo tauri dev

    # Capture exit code
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        print_error "Development server exited with error code: $exit_code"
        print_info "Check the terminal output for detailed error messages"
    fi
}

# Run frontend only
run_frontend_only() {
    print_header "Starting Frontend Only"
    
    cd frontend
    print_info "Starting frontend dev server on http://localhost:5173"
    npm run dev
}

# Run backend only
run_backend_only() {
    print_header "Starting Backend Only"
    
    # Activate virtual environment
    source .venv/bin/activate
    
    print_info "Starting Python backend service..."
    python3 backend/backend_service.py
}

# Clean build artifacts
clean() {
    print_header "Cleaning Build Artifacts"
    
    # Clean frontend
    if [ -d "frontend/dist" ]; then
        print_info "Cleaning frontend build..."
        rm -rf frontend/dist
        print_success "Frontend build cleaned"
    fi
    
    # Clean Tauri
    if [ -d "src-tauri/target" ]; then
        print_info "Cleaning Tauri build..."
        cd src-tauri
        cargo clean
        cd ..
        print_success "Tauri build cleaned"
    fi
    
    # Clean Python cache
    print_info "Cleaning Python cache..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    print_success "Python cache cleaned"
    
    print_success "All build artifacts cleaned"
}

# Show help
show_help() {
    echo "DeepEcho Development Script"
    echo ""
    echo "Usage: ./dev.sh [command]"
    echo ""
    echo "Commands:"
    echo "  setup       - Setup development environment (install dependencies)"
    echo "  dev         - Run full development server (default)"
    echo "  frontend    - Run frontend only"
    echo "  backend     - Run backend only"
    echo "  clean       - Clean build artifacts"
    echo "  check       - Check prerequisites only"
    echo "  help        - Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./dev.sh setup    # First time setup"
    echo "  ./dev.sh dev      # Run development server"
    echo "  ./dev.sh frontend # Run frontend only"
    echo "  ./dev.sh clean    # Clean build artifacts"
    echo ""
}

# Main script
main() {
    local command=${1:-dev}
    
    case $command in
        setup)
            check_prerequisites
            setup_python_env
            setup_frontend
            setup_tauri
            setup_config
            print_success "Development environment setup complete!"
            print_info "Run './dev.sh dev' to start the development server"
            ;;
        dev)
            check_prerequisites
            run_dev
            ;;
        frontend)
            run_frontend_only
            ;;
        backend)
            run_backend_only
            ;;
        clean)
            clean
            ;;
        check)
            check_prerequisites
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $command"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
