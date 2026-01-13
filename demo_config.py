#!/usr/bin/env python3
"""
Demo script for DeepEcho configuration system.

This script demonstrates the new configuration management capabilities
without requiring GUI dependencies.
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

from src.config.config_manager import get_config_manager
from src.config.validator import ConfigValidator

def main():
    print("=== DeepEcho Configuration System Demo ===\n")
    
    # Initialize configuration manager
    print("1. Initializing configuration manager...")
    manager = get_config_manager()
    
    # Load configuration
    print("2. Loading configuration...")
    config = manager.load_config()
    
    print(f"   ✓ Default AI provider: {config.default_provider}")
    print(f"   ✓ Audio record timeout: {config.audio.record_timeout}s")
    print(f"   ✓ UI update interval: {config.ui.update_interval}s")
    print(f"   ✓ Use API mode: {config.audio.use_api_mode}")
    print(f"   ✓ Use new UI: {config.ui.use_new_ui}")
    
    # Show available providers
    print("\n3. Available AI providers:")
    providers = manager.get_available_providers()
    for provider in providers:
        models = manager.get_provider_models(provider)
        print(f"   ✓ {provider}: {', '.join(models)}")
    
    # Test API key validation
    print("\n4. Testing API key validation:")
    validator = ConfigValidator()
    
    test_keys = [
        ("openai", "sk-" + "a" * 48, True),
        ("openai", "invalid-key", False),
        ("deepseek", "sk-" + "b" * 48, True),
        ("grok", "xai-" + "c" * 48, True),
        ("claude", "sk-ant-" + "d" * 48, True),
    ]
    
    for provider, key, expected in test_keys:
        is_valid, message = validator.validate_api_key(provider, key)
        status = "✓" if is_valid == expected else "✗"
        print(f"   {status} {provider}: {message}")
    
    # Test configuration update
    print("\n5. Testing configuration updates:")
    
    # Update UI settings
    success = manager.update_ui_config(update_interval=10)
    print(f"   ✓ Update UI interval: {'Success' if success else 'Failed'}")
    
    # Update audio settings
    success = manager.update_audio_config(use_api_mode=True)
    print(f"   ✓ Update audio mode: {'Success' if success else 'Failed'}")
    
    # Show updated config
    updated_config = manager.get_current_config()
    print(f"   ✓ New update interval: {updated_config.ui.update_interval}s")
    print(f"   ✓ New API mode: {updated_config.audio.use_api_mode}")
    
    # Test validation
    print("\n6. Testing configuration validation:")
    is_valid, messages = manager.validate_current_config()
    print(f"   Configuration valid: {is_valid}")
    if messages:
        for msg in messages:
            print(f"   - {msg}")
    
    print("\n=== Demo completed successfully! ===")
    print("\nThe new configuration system provides:")
    print("• Comprehensive AI provider support (6 providers)")
    print("• Automatic configuration validation")
    print("• Environment variable and keys.py integration")
    print("• Configuration import/export capabilities")
    print("• Robust error handling and recovery")

if __name__ == "__main__":
    main()