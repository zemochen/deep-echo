#!/usr/bin/env python3
"""
DeepEcho System Requirements Checker

This script checks if your system meets all requirements for running DeepEcho.
"""

import sys
import os
import platform
import subprocess
import importlib
from pathlib import Path


def check_python_version():
    """Check Python version."""
    print("🐍 Python Version Check")
    version = sys.version_info
    
    if version >= (3, 8):
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro} (OK)")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} (Requires 3.8+)")
        return False


def check_platform():
    """Check operating system."""
    print("\n💻 Operating System Check")
    system = platform.system()
    version = platform.version()
    
    if system in ["Windows", "Darwin", "Linux"]:
        print(f"   ✅ {system} {version} (Supported)")
        return True, system
    else:
        print(f"   ⚠️  {system} (May not be fully supported)")
        return False, system


def check_ffmpeg():
    """Check FFmpeg installation."""
    print("\n🎵 FFmpeg Check")
    
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            timeout=10,
            text=True
        )
        
        if result.returncode == 0:
            # Extract version from output
            lines = result.stdout.split('\n')
            version_line = next((line for line in lines if line.startswith('ffmpeg version')), '')
            version = version_line.split()[2] if len(version_line.split()) > 2 else 'unknown'
            print(f"   ✅ FFmpeg {version} (OK)")
            return True
        else:
            print("   ❌ FFmpeg found but not working properly")
            return False
            
    except FileNotFoundError:
        print("   ❌ FFmpeg not found")
        return False
    except subprocess.TimeoutExpired:
        print("   ❌ FFmpeg check timed out")
        return False
    except Exception as e:
        print(f"   ❌ FFmpeg check failed: {e}")
        return False


def check_python_modules():
    """Check required Python modules."""
    print("\n📦 Python Modules Check")
    
    required_modules = [
        ("customtkinter", "UI framework"),
        ("numpy", "Numerical computing"),
        ("threading", "Multi-threading (built-in)"),
        ("queue", "Queue management (built-in)"),
        ("requests", "HTTP requests"),
        ("json", "JSON handling (built-in)"),
        ("pathlib", "Path handling (built-in)"),
    ]
    
    optional_modules = [
        ("openai", "OpenAI API client"),
        ("anthropic", "Claude API client"),
        ("pyaudio", "Audio recording"),
        ("sounddevice", "Audio device management"),
        ("hypothesis", "Property-based testing"),
        ("pytest", "Testing framework"),
    ]
    
    all_good = True
    
    print("   Required modules:")
    for module, description in required_modules:
        try:
            importlib.import_module(module)
            print(f"   ✅ {module} - {description}")
        except ImportError:
            print(f"   ❌ {module} - {description} (MISSING)")
            all_good = False
    
    print("\n   Optional modules:")
    for module, description in optional_modules:
        try:
            importlib.import_module(module)
            print(f"   ✅ {module} - {description}")
        except ImportError:
            print(f"   ⚠️  {module} - {description} (Optional)")
    
    return all_good


def check_audio_system(system_name):
    """Check platform-specific audio requirements."""
    print(f"\n🔊 Audio System Check ({system_name})")
    
    if system_name == "Windows":
        try:
            import pyaudiowpatch
            print("   ✅ PyAudioWPatch (Windows audio support)")
            return True
        except ImportError:
            print("   ❌ PyAudioWPatch (Required for Windows audio)")
            return False
            
    elif system_name == "Darwin":  # macOS
        try:
            import sounddevice
            print("   ✅ SoundDevice (macOS audio support)")
        except ImportError:
            print("   ⚠️  SoundDevice (Recommended for macOS)")
        
        # Check for BlackHole
        try:
            result = subprocess.run(
                ["system_profiler", "SPAudioDataType"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )
            if "BlackHole" in result.stdout:
                print("   ✅ BlackHole virtual audio device detected")
            else:
                print("   ⚠️  BlackHole not detected (Recommended for speaker capture)")
        except:
            print("   ⚠️  Could not check for BlackHole")
        
        return True
        
    elif system_name == "Linux":
        try:
            import pyaudio
            print("   ✅ PyAudio (Linux audio support)")
            return True
        except ImportError:
            print("   ❌ PyAudio (Required for Linux audio)")
            return False
    
    return True


def check_deepecho_files():
    """Check if DeepEcho files are present."""
    print("\n📁 DeepEcho Files Check")
    
    required_files = [
        "main.py",
        "src/main.py",
        "src/integration.py",
        "src/config/config_manager.py",
        "src/ai/adapter.py",
        "src/audio/recorder.py",
    ]
    
    optional_files = [
        "config.json",
        "resources/config.example.json",
        "keys.py",
        "README.md",
        "API_SETUP.md",
    ]
    
    all_good = True
    
    print("   Required files:")
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} (MISSING)")
            all_good = False
    
    print("\n   Optional files:")
    for file_path in optional_files:
        if Path(file_path).exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ⚠️  {file_path} (Recommended)")
    
    return all_good


def check_configuration():
    """Check configuration setup."""
    print("\n⚙️  Configuration Check")
    
    has_config = False
    
    # Check config.json
    if Path("config.json").exists():
        print("   ✅ config.json found")
        has_config = True
        
        try:
            import json
            with open("config.json", "r") as f:
                config = json.load(f)
            
            # Check AI provider configuration
            if "ai_provider" in config:
                provider = config["ai_provider"]
                if provider.get("api_key") != "your-api-key-here":
                    print(f"   ✅ AI provider configured: {provider.get('provider_type', 'unknown')}")
                else:
                    print("   ⚠️  AI provider API key not set")
            else:
                print("   ⚠️  AI provider not configured")
                
        except Exception as e:
            print(f"   ❌ Error reading config.json: {e}")
    
    # Check keys.py (legacy)
    if Path("keys.py").exists():
        print("   ✅ keys.py found (legacy configuration)")
        has_config = True
    
    # Check environment variables
    env_keys = ["OPENAI_API_KEY", "DEEPSEEK_API_KEY", "ANTHROPIC_API_KEY"]
    found_env_keys = []
    for key in env_keys:
        if os.getenv(key):
            found_env_keys.append(key)
    
    if found_env_keys:
        print(f"   ✅ Environment variables: {', '.join(found_env_keys)}")
        has_config = True
    
    if not has_config:
        print("   ❌ No configuration found")
        print("      Create config.json or set environment variables")
        return False
    
    return True


def provide_recommendations(issues):
    """Provide recommendations based on found issues."""
    if not issues:
        return
    
    print("\n💡 Recommendations")
    print("=" * 50)
    
    for issue in issues:
        if "Python" in issue:
            print("🐍 Python: Upgrade to Python 3.8 or higher")
            print("   Download from: https://www.python.org/downloads/")
            
        elif "FFmpeg" in issue:
            system = platform.system()
            if system == "Windows":
                print("🎵 FFmpeg (Windows):")
                print("   1. Install Chocolatey: https://chocolatey.org/install")
                print("   2. Run: choco install ffmpeg")
            elif system == "Darwin":
                print("🎵 FFmpeg (macOS):")
                print("   1. Install Homebrew: https://brew.sh/")
                print("   2. Run: brew install ffmpeg")
            else:
                print("🎵 FFmpeg (Linux):")
                print("   Ubuntu/Debian: sudo apt install ffmpeg")
                print("   CentOS/RHEL: sudo yum install ffmpeg")
                
        elif "modules" in issue:
            print("📦 Python Modules:")
            print("   Run: pip install -r requirements.txt")
            
        elif "audio" in issue:
            system = platform.system()
            if system == "Windows":
                print("🔊 Windows Audio:")
                print("   Run: pip install pyaudiowpatch")
            elif system == "Darwin":
                print("🔊 macOS Audio:")
                print("   1. Run: brew install portaudio")
                print("   2. Run: pip install sounddevice")
                print("   3. Install BlackHole: brew install blackhole-2ch")
            else:
                print("🔊 Linux Audio:")
                print("   1. Install system audio dev packages")
                print("   2. Run: pip install pyaudio")
                
        elif "files" in issue:
            print("📁 DeepEcho Files:")
            print("   Ensure you're in the correct DeepEcho directory")
            print("   Re-clone the repository if files are missing")
            
        elif "configuration" in issue:
            print("⚙️  Configuration:")
            print("   1. Run: python setup.py")
            print("   2. Or copy resources/config.example.json to config.json")
            print("   3. Add your AI provider API key")
            print("   4. See API_SETUP.md for detailed instructions")


def main():
    """Main system check function."""
    print("🎧 DeepEcho System Requirements Check")
    print("=" * 50)
    
    issues = []
    
    # Run all checks
    if not check_python_version():
        issues.append("Python version")
    
    platform_ok, system_name = check_platform()
    if not platform_ok:
        issues.append("Operating system")
    
    if not check_ffmpeg():
        issues.append("FFmpeg")
    
    if not check_python_modules():
        issues.append("Python modules")
    
    if not check_audio_system(system_name):
        issues.append("Audio system")
    
    if not check_deepecho_files():
        issues.append("DeepEcho files")
    
    if not check_configuration():
        issues.append("Configuration")
    
    # Summary
    print("\n" + "=" * 50)
    if not issues:
        print("🎉 All checks passed! DeepEcho should work properly.")
        print("\n🚀 To start DeepEcho:")
        print("   python main.py")
        print("   or")
        print("   python start.py")
    else:
        print(f"❌ Found {len(issues)} issue(s):")
        for issue in issues:
            print(f"   - {issue}")
        
        provide_recommendations(issues)
        
        print(f"\n🔧 After fixing these issues, run this script again to verify.")
    
    print("\n📚 For more help:")
    print("   - README.md - Complete setup guide")
    print("   - API_SETUP.md - API key configuration")
    print("   - python setup.py - Interactive setup")


if __name__ == "__main__":
    main()