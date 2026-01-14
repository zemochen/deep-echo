#!/usr/bin/env python3
"""
DeepEcho Setup Script

This script helps set up DeepEcho with proper configuration and dependencies.
"""

import os
import sys
import json
import subprocess
import platform
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True


def check_ffmpeg():
    """Check if FFmpeg is installed."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"], 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL,
            timeout=10
        )
        if result.returncode == 0:
            print("✅ FFmpeg is installed")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    print("❌ FFmpeg not found")
    return False


def install_ffmpeg():
    """Provide instructions to install FFmpeg."""
    system = platform.system().lower()
    
    if system == "windows":
        print("\n📦 To install FFmpeg on Windows:")
        print("1. Install Chocolatey (if not already installed):")
        print("   Run PowerShell as Administrator and execute:")
        print("   Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))")
        print("\n2. Install FFmpeg:")
        print("   choco install ffmpeg")
        
    elif system == "darwin":  # macOS
        print("\n📦 To install FFmpeg on macOS:")
        print("1. Install Homebrew (if not already installed):")
        print("   /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
        print("\n2. Install dependencies:")
        print("   brew install ffmpeg portaudio python-tk blackhole-2ch")
        
    else:  # Linux
        print("\n📦 To install FFmpeg on Linux:")
        print("Ubuntu/Debian: sudo apt update && sudo apt install ffmpeg")
        print("CentOS/RHEL: sudo yum install ffmpeg")
        print("Arch: sudo pacman -S ffmpeg")


def install_dependencies():
    """Install Python dependencies."""
    print("\n📦 Installing Python dependencies...")
    
    try:
        # Install main dependencies
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✅ Main dependencies installed")
        
        # Install development dependencies if available
        if Path("requirements-dev.txt").exists():
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", "-r", "requirements-dev.txt"
                ])
                print("✅ Development dependencies installed")
            except subprocess.CalledProcessError:
                print("⚠️  Development dependencies installation failed (optional)")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def create_config_file():
    """Create configuration file interactively."""
    print("\n⚙️  Setting up configuration...")
    
    # Check if config already exists
    if Path("config.json").exists():
        response = input("Configuration file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Keeping existing configuration")
            return True
    
    # Load example config
    try:
        with open("resources/config.example.json", "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        print("❌ resources/config.example.json not found")
        return False
    
    print("\n🤖 AI Provider Setup")
    print("Choose an AI provider:")
    print("1. DeepSeek (recommended - cost-effective)")
    print("2. OpenAI (GPT models)")
    print("3. Claude (Anthropic)")
    print("4. Grok (xAI)")
    print("5. Skip for now")
    
    choice = input("Enter choice (1-5): ").strip()
    
    if choice == "1":
        config["ai_provider"]["provider_type"] = "deepseek"
        config["ai_provider"]["model"] = "deepseek-chat"
        api_key = input("Enter your DeepSeek API key: ").strip()
        if api_key:
            config["ai_provider"]["api_key"] = api_key
            
    elif choice == "2":
        config["ai_provider"]["provider_type"] = "openai"
        config["ai_provider"]["model"] = "gpt-3.5-turbo"
        api_key = input("Enter your OpenAI API key: ").strip()
        if api_key:
            config["ai_provider"]["api_key"] = api_key
            
    elif choice == "3":
        config["ai_provider"]["provider_type"] = "claude"
        config["ai_provider"]["model"] = "claude-3-sonnet"
        api_key = input("Enter your Claude API key: ").strip()
        if api_key:
            config["ai_provider"]["api_key"] = api_key
            
    elif choice == "4":
        config["ai_provider"]["provider_type"] = "grok"
        config["ai_provider"]["model"] = "grok-beta"
        api_key = input("Enter your Grok API key: ").strip()
        if api_key:
            config["ai_provider"]["api_key"] = api_key
    
    # Audio settings
    print("\n🎤 Audio Settings")
    api_mode = input("Use API transcription mode? (more accurate, requires internet) (Y/n): ").strip()
    config["audio"]["use_api_mode"] = api_mode.lower() != 'n'
    
    # UI settings
    print("\n🖥️  UI Settings")
    new_ui = input("Use new integrated UI? (Y/n): ").strip()
    config["ui"]["use_new_ui"] = new_ui.lower() != 'n'
    
    # Save configuration
    try:
        with open("config.json", "w") as f:
            json.dump(config, f, indent=2)
        print("✅ Configuration saved to config.json")
        return True
    except Exception as e:
        print(f"❌ Failed to save configuration: {e}")
        return False


def setup_environment_variables():
    """Help set up environment variables."""
    print("\n🔧 Environment Variables (Optional)")
    print("You can set API keys as environment variables instead of in config file:")
    
    system = platform.system().lower()
    
    if system == "windows":
        print("\nWindows (PowerShell):")
        print("$env:DEEPSEEK_API_KEY=\"your-key-here\"")
        print("$env:OPENAI_API_KEY=\"your-key-here\"")
        
    else:  # Unix-like
        print("\nBash/Zsh:")
        print("export DEEPSEEK_API_KEY=\"your-key-here\"")
        print("export OPENAI_API_KEY=\"your-key-here\"")
        print("\nAdd to ~/.bashrc or ~/.zshrc for persistence")


def run_test():
    """Run a basic test to verify installation."""
    print("\n🧪 Running basic test...")
    
    try:
        # Test imports
        import src.config.config_manager
        import src.ai.adapter
        import src.audio.recorder
        print("✅ Core modules import successfully")
        
        # Test configuration loading
        from src.config.config_manager import get_config_manager
        config_manager = get_config_manager()
        config = config_manager.load_config()
        print("✅ Configuration loads successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def main():
    """Main setup function."""
    print("🎧 DeepEcho Setup Script")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check FFmpeg
    if not check_ffmpeg():
        install_ffmpeg()
        print("\nPlease install FFmpeg and run this script again.")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Create configuration
    if not create_config_file():
        sys.exit(1)
    
    # Show environment variable info
    setup_environment_variables()
    
    # Run test
    if not run_test():
        print("\n⚠️  Setup completed with warnings. Check the error messages above.")
        sys.exit(1)
    
    print("\n🎉 Setup completed successfully!")
    print("\n🚀 To start DeepEcho:")
    print("   python main.py")
    print("\n📚 For more information:")
    print("   - Read README.md")
    print("   - Check API_SETUP.md for detailed API key setup")
    print("   - Use --help flag for command options")


if __name__ == "__main__":
    main()