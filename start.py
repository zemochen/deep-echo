#!/usr/bin/env python3
"""
DeepEcho Quick Start Script

This script provides a simple way to start DeepEcho with common configurations.
"""

import sys
import os
import subprocess
from pathlib import Path


def show_menu():
    """Show the startup menu."""
    print("🎧 DeepEcho Quick Start")
    print("=" * 30)
    print("1. Start with default settings")
    print("2. Start with API transcription (more accurate)")
    print("3. Start with verbose logging")
    print("4. Start with specific AI provider")
    print("5. Run system diagnostics")
    print("6. Show help")
    print("7. Exit")
    print()


def check_setup():
    """Check if DeepEcho is properly set up."""
    issues = []
    
    # Check if main.py exists
    if not Path("main.py").exists():
        issues.append("main.py not found")
    
    # Check if src directory exists
    if not Path("src").exists():
        issues.append("src directory not found")
    
    # Check if configuration exists
    if not Path("config.json").exists() and not Path("keys.py").exists():
        issues.append("No configuration found (config.json or keys.py)")
    
    # Check FFmpeg
    try:
        subprocess.run(
            ["ffmpeg", "-version"], 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL,
            timeout=5
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        issues.append("FFmpeg not found")
    
    return issues


def run_diagnostics():
    """Run system diagnostics."""
    print("🔍 Running system diagnostics...")
    print()
    
    # Check setup
    issues = check_setup()
    if issues:
        print("❌ Setup Issues:")
        for issue in issues:
            print(f"   - {issue}")
        print()
        print("💡 Run 'python setup.py' to fix setup issues")
        return
    
    print("✅ Basic setup looks good")
    
    # Try to import core modules
    try:
        import src.config.config_manager
        print("✅ Configuration module available")
    except ImportError as e:
        print(f"❌ Configuration module error: {e}")
    
    try:
        import src.ai.adapter
        print("✅ AI adapter module available")
    except ImportError as e:
        print(f"❌ AI adapter module error: {e}")
    
    try:
        import src.audio.recorder
        print("✅ Audio recorder module available")
    except ImportError as e:
        print(f"❌ Audio recorder module error: {e}")
    
    # Check configuration
    try:
        from src.config.config_manager import get_config_manager
        config_manager = get_config_manager()
        config = config_manager.load_config()
        print("✅ Configuration loads successfully")
        
        # Show current AI provider
        if hasattr(config, 'ai_provider'):
            provider = config.ai_provider.provider_type
            model = config.ai_provider.model
            has_key = config.ai_provider.api_key != "your-api-key-here"
            print(f"✅ AI Provider: {provider} ({model}) - Key configured: {has_key}")
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
    
    print()
    print("🚀 If everything looks good, you can start DeepEcho!")


def start_deepecho(args=None):
    """Start DeepEcho with given arguments."""
    if args is None:
        args = []
    
    # Check setup first
    issues = check_setup()
    if issues:
        print("❌ Setup issues detected:")
        for issue in issues:
            print(f"   - {issue}")
        print()
        print("💡 Run 'python setup.py' first to set up DeepEcho")
        return
    
    # Build command
    cmd = [sys.executable, "main.py"] + args
    
    print(f"🚀 Starting DeepEcho with: {' '.join(cmd)}")
    print("   Press Ctrl+C to stop")
    print()
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n👋 DeepEcho stopped")
    except Exception as e:
        print(f"\n❌ Error starting DeepEcho: {e}")


def select_ai_provider():
    """Let user select AI provider and start."""
    print("🤖 Select AI Provider:")
    print("1. DeepSeek (cost-effective)")
    print("2. OpenAI GPT-3.5 (balanced)")
    print("3. OpenAI GPT-4 (high quality)")
    print("4. Claude Sonnet (balanced)")
    print("5. Claude Opus (high quality)")
    print("6. Grok (real-time info)")
    print("7. Auto-detect from config")
    
    choice = input("\nEnter choice (1-7): ").strip()
    
    # For now, just start with default and let the system auto-detect
    # In the future, we could add provider-specific startup options
    if choice in ["1", "2", "3", "4", "5", "6", "7"]:
        print(f"Starting with provider selection {choice}...")
        start_deepecho()
    else:
        print("Invalid choice")


def show_help():
    """Show help information."""
    print("🎧 DeepEcho Help")
    print("=" * 20)
    print()
    print("Command line options:")
    print("  python main.py              # Default mode")
    print("  python main.py --api        # API transcription mode")
    print("  python main.py --verbose    # Verbose logging")
    print("  python main.py --help       # Show all options")
    print()
    print("Configuration:")
    print("  - Edit config.json for settings")
    print("  - See API_SETUP.md for API key setup")
    print("  - Use setup.py for initial configuration")
    print()
    print("Troubleshooting:")
    print("  - Run diagnostics (option 5) to check setup")
    print("  - Check README.md for detailed instructions")
    print("  - Use --verbose flag for detailed error messages")


def main():
    """Main function."""
    while True:
        show_menu()
        choice = input("Enter your choice (1-7): ").strip()
        
        if choice == "1":
            start_deepecho()
        elif choice == "2":
            start_deepecho(["--api"])
        elif choice == "3":
            start_deepecho(["--verbose"])
        elif choice == "4":
            select_ai_provider()
        elif choice == "5":
            run_diagnostics()
        elif choice == "6":
            show_help()
        elif choice == "7":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")
        
        if choice != "7":
            input("\nPress Enter to continue...")
            print()


if __name__ == "__main__":
    main()