#!/usr/bin/env python3
"""
Interactive API Keys Setup Script for DeepEcho
Helps users create and configure their keys.py file safely
"""

import os
import sys
import shutil
from pathlib import Path

# ANSI color codes
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'

def print_header(text):
    """Print a formatted header"""
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}{text:^60}{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}\n")

def print_success(text):
    """Print success message"""
    print(f"{GREEN}✅ {text}{RESET}")

def print_warning(text):
    """Print warning message"""
    print(f"{YELLOW}⚠️  {text}{RESET}")

def print_error(text):
    """Print error message"""
    print(f"{RED}❌ {text}{RESET}")

def print_info(text):
    """Print info message"""
    print(f"{CYAN}ℹ️  {text}{RESET}")

def get_input(prompt, default=None):
    """Get user input with optional default"""
    if default:
        user_input = input(f"{prompt} [{default}]: ").strip()
        return user_input if user_input else default
    else:
        return input(f"{prompt}: ").strip()

def validate_api_key(key, provider):
    """Basic validation of API key format"""
    if not key or len(key) < 10:
        return False, "Key is too short"
    
    if 'your-' in key.lower() or 'example' in key.lower() or 'placeholder' in key.lower():
        return False, "Key appears to be a placeholder"
    
    # Provider-specific validation
    if provider == 'openai' and not key.startswith('sk-'):
        return False, "OpenAI keys should start with 'sk-'"
    
    if provider == 'anthropic' and not key.startswith('sk-ant-'):
        return False, "Anthropic keys should start with 'sk-ant-'"
    
    return True, "OK"

def check_existing_keys():
    """Check if keys.py already exists"""
    if os.path.exists('keys.py'):
        print_warning("keys.py already exists!")
        
        # Try to import and show configured keys
        try:
            import keys
            print_info("Currently configured keys:")
            
            key_attrs = ['OPENAI_API_KEY', 'VOLCENGINE_API_KEY', 'DEEPSEEK_API_KEY', 
                        'ANTHROPIC_API_KEY', 'XAI_API_KEY', 'ZHIPU_API_KEY']
            
            for attr in key_attrs:
                if hasattr(keys, attr):
                    key_value = getattr(keys, attr)
                    if key_value and len(key_value) > 10:
                        # Show only first and last 4 characters
                        masked = f"{key_value[:4]}...{key_value[-4:]}"
                        print(f"  • {attr}: {masked}")
        except Exception as e:
            print_error(f"Could not read existing keys.py: {e}")
        
        response = get_input("\nDo you want to overwrite it? (yes/no)", "no")
        return response.lower() in ['yes', 'y']
    
    return True

def create_keys_file():
    """Interactive creation of keys.py file"""
    print_header("DeepEcho API Keys Setup")
    
    print("This script will help you create your keys.py file.")
    print("You'll need at least one API key from a supported provider.\n")
    
    # Check if keys.py exists
    if not check_existing_keys():
        print_info("Setup cancelled. Your existing keys.py was not modified.")
        return False
    
    # Check if template exists
    if not os.path.exists('keys.example.py'):
        print_error("keys.example.py template not found!")
        print_info("Creating a basic template...")
        create_basic_template()
    
    print_info("Supported providers:")
    print("  1. OpenAI (GPT models, Whisper API)")
    print("  2. DeepSeek (Cost-effective alternative)")
    print("  3. Volcano Engine (ByteDance)")
    print("  4. Anthropic (Claude models)")
    print("  5. xAI (Grok models)")
    print("  6. Zhipu AI (GLM models)")
    print()
    
    # Collect API keys
    keys_config = {}
    
    # OpenAI
    print(f"\n{CYAN}OpenAI API Key{RESET}")
    print("Get your key from: https://platform.openai.com/api-keys")
    openai_key = get_input("Enter your OpenAI API key (or press Enter to skip)", "")
    if openai_key:
        valid, msg = validate_api_key(openai_key, 'openai')
        if valid:
            keys_config['OPENAI_API_KEY'] = openai_key
            print_success("OpenAI key added")
        else:
            print_warning(f"OpenAI key validation warning: {msg}")
            if get_input("Add it anyway? (yes/no)", "no").lower() in ['yes', 'y']:
                keys_config['OPENAI_API_KEY'] = openai_key
    
    # DeepSeek
    print(f"\n{CYAN}DeepSeek API Key{RESET}")
    print("Get your key from: https://platform.deepseek.com/api_keys")
    deepseek_key = get_input("Enter your DeepSeek API key (or press Enter to skip)", "")
    if deepseek_key:
        valid, msg = validate_api_key(deepseek_key, 'deepseek')
        if valid:
            keys_config['DEEPSEEK_API_KEY'] = deepseek_key
            print_success("DeepSeek key added")
        else:
            print_warning(f"DeepSeek key validation warning: {msg}")
            if get_input("Add it anyway? (yes/no)", "no").lower() in ['yes', 'y']:
                keys_config['DEEPSEEK_API_KEY'] = deepseek_key
    
    # Volcano Engine
    print(f"\n{CYAN}Volcano Engine API Key{RESET}")
    print("Get your key from: https://console.volcengine.com/")
    volcano_key = get_input("Enter your Volcano Engine API key (or press Enter to skip)", "")
    if volcano_key:
        valid, msg = validate_api_key(volcano_key, 'volcano')
        if valid:
            keys_config['VOLCENGINE_API_KEY'] = volcano_key
            print_success("Volcano Engine key added")
        else:
            print_warning(f"Volcano Engine key validation warning: {msg}")
            if get_input("Add it anyway? (yes/no)", "no").lower() in ['yes', 'y']:
                keys_config['VOLCENGINE_API_KEY'] = volcano_key
    
    # Anthropic
    print(f"\n{CYAN}Anthropic API Key (Optional){RESET}")
    print("Get your key from: https://console.anthropic.com/settings/keys")
    anthropic_key = get_input("Enter your Anthropic API key (or press Enter to skip)", "")
    if anthropic_key:
        valid, msg = validate_api_key(anthropic_key, 'anthropic')
        if valid:
            keys_config['ANTHROPIC_API_KEY'] = anthropic_key
            print_success("Anthropic key added")
        else:
            print_warning(f"Anthropic key validation warning: {msg}")
            if get_input("Add it anyway? (yes/no)", "no").lower() in ['yes', 'y']:
                keys_config['ANTHROPIC_API_KEY'] = anthropic_key
    
    # Check if at least one key was provided
    if not keys_config:
        print_error("No API keys provided!")
        print_info("You need at least one API key to use DeepEcho.")
        return False
    
    # Write keys.py file
    print(f"\n{CYAN}Creating keys.py file...{RESET}")
    
    try:
        with open('keys.py', 'w') as f:
            f.write("# API Keys Configuration for DeepEcho\n")
            f.write("# WARNING: This file contains sensitive information!\n")
            f.write("# Never commit this file to version control.\n")
            f.write("# This file is automatically excluded by .gitignore\n\n")
            
            for key_name, key_value in keys_config.items():
                f.write(f'{key_name} = "{key_value}"\n')
            
            f.write("\n# Add more API keys as needed\n")
        
        print_success("keys.py created successfully!")
        
        # Set file permissions (Unix-like systems)
        if os.name != 'nt':
            os.chmod('keys.py', 0o600)
            print_success("File permissions set to 600 (owner read/write only)")
        
        return True
        
    except Exception as e:
        print_error(f"Failed to create keys.py: {e}")
        return False

def create_basic_template():
    """Create a basic keys.example.py template if it doesn't exist"""
    template_content = '''# API Keys Configuration Template
# 
# IMPORTANT: This is a template file. DO NOT put your actual API keys here!
# 
# Instructions:
# 1. Copy this file and rename it to 'keys.py'
# 2. Replace the placeholder values with your actual API keys
# 3. The 'keys.py' file is already in .gitignore and will not be committed

# OpenAI API Key
OPENAI_API_KEY = "sk-your-openai-api-key-here"

# Volcano Engine API Key
VOLCENGINE_API_KEY = "your-volcengine-api-key-here"

# DeepSeek API Key (optional)
# DEEPSEEK_API_KEY = "your-deepseek-api-key-here"

# Anthropic API Key (optional)
# ANTHROPIC_API_KEY = "your-anthropic-api-key-here"
'''
    
    try:
        with open('keys.example.py', 'w') as f:
            f.write(template_content)
        print_success("Created keys.example.py template")
    except Exception as e:
        print_error(f"Failed to create template: {e}")

def verify_security():
    """Verify that keys.py is properly secured"""
    print_header("Security Verification")
    
    # Check .gitignore
    if os.path.exists('.gitignore'):
        with open('.gitignore', 'r') as f:
            if 'keys.py' in f.read():
                print_success("keys.py is in .gitignore")
            else:
                print_warning("keys.py is NOT in .gitignore!")
                print_info("Adding keys.py to .gitignore...")
                with open('.gitignore', 'a') as f:
                    f.write('\n# API Keys\nkeys.py\n')
                print_success("Added keys.py to .gitignore")
    else:
        print_warning(".gitignore not found")
    
    # Check if keys.py is tracked by git
    try:
        import subprocess
        result = subprocess.run(
            ['git', 'ls-files', '--error-unmatch', 'keys.py'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print_error("keys.py is tracked by git!")
            print_info("Run: git rm --cached keys.py")
        else:
            print_success("keys.py is not tracked by git")
    except:
        print_info("Could not verify git status (git may not be installed)")

def main():
    """Main function"""
    try:
        if create_keys_file():
            verify_security()
            
            print_header("Setup Complete!")
            print_success("Your API keys have been configured!")
            print()
            print_info("Next steps:")
            print("  1. Run: python check_security.py")
            print("  2. Start DeepEcho: python main.py")
            print()
            print_warning("Remember: Never commit keys.py to version control!")
            print()
            
            return 0
        else:
            print_error("Setup failed or was cancelled")
            return 1
            
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Setup cancelled by user{RESET}")
        return 1
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
