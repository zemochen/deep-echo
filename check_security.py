#!/usr/bin/env python3
"""
Security Check Script for DeepEcho
Verifies that API keys and sensitive files are properly protected
"""

import os
import sys
import subprocess
import re
from pathlib import Path

# ANSI color codes
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    """Print a formatted header"""
    print(f"\n{BLUE}{'=' * 50}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'=' * 50}{RESET}\n")

def print_success(text):
    """Print success message"""
    print(f"{GREEN}✅ {text}{RESET}")

def print_warning(text):
    """Print warning message"""
    print(f"{YELLOW}⚠️  {text}{RESET}")

def print_error(text):
    """Print error message"""
    print(f"{RED}❌ {text}{RESET}")

def check_gitignore():
    """Check if sensitive files are in .gitignore"""
    print_header("Checking .gitignore Configuration")
    
    sensitive_files = ['keys.py', '.env', '.env.local', 'secrets.json', 'config.local.json']
    
    if not os.path.exists('.gitignore'):
        print_error(".gitignore file not found!")
        return False
    
    with open('.gitignore', 'r') as f:
        gitignore_content = f.read()
    
    all_good = True
    for file in sensitive_files:
        if file in gitignore_content:
            print_success(f"{file} is in .gitignore")
        else:
            print_warning(f"{file} is NOT in .gitignore")
            all_good = False
    
    return all_good

def check_keys_file():
    """Check keys.py file status"""
    print_header("Checking keys.py File")
    
    if not os.path.exists('keys.py'):
        print_warning("keys.py does not exist")
        if os.path.exists('keys.example.py'):
            print("   To create it: cp keys.example.py keys.py")
        return True
    
    print_success("keys.py exists")
    
    # Check if it's tracked by git
    try:
        result = subprocess.run(
            ['git', 'ls-files', '--error-unmatch', 'keys.py'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print_error("keys.py is tracked by git!")
            print("   Fix: git rm --cached keys.py")
            return False
        else:
            print_success("keys.py is not tracked by git")
    except FileNotFoundError:
        print_warning("Git not found, skipping git checks")
    
    # Check if keys.py is ignored
    try:
        result = subprocess.run(
            ['git', 'check-ignore', 'keys.py'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print_success("keys.py is properly ignored by git")
        else:
            print_error("keys.py is NOT ignored by git!")
            return False
    except FileNotFoundError:
        pass
    
    return True

def check_git_history():
    """Check if sensitive files appear in git history"""
    print_header("Checking Git History")
    
    try:
        result = subprocess.run(
            ['git', 'log', '--all', '--full-history', '--source', '--', 'keys.py'],
            capture_output=True,
            text=True
        )
        
        if 'commit' in result.stdout:
            print_error("keys.py appears in git history!")
            print("   This is a security risk. See SECURITY.md for remediation.")
            return False
        else:
            print_success("No keys.py found in git history")
            return True
    except FileNotFoundError:
        print_warning("Git not found, skipping history check")
        return True

def check_api_keys():
    """Check if API keys look valid (without exposing them)"""
    print_header("Checking API Keys")
    
    if not os.path.exists('keys.py'):
        print_warning("keys.py not found, skipping key validation")
        return True
    
    try:
        # Import keys module
        import keys
        
        # Check for common API key attributes
        key_attrs = ['OPENAI_API_KEY', 'VOLCENGINE_API_KEY', 'DEEPSEEK_API_KEY']
        found_keys = []
        
        for attr in key_attrs:
            if hasattr(keys, attr):
                key_value = getattr(keys, attr)
                if key_value and len(key_value) > 10:
                    # Check if it's not a placeholder
                    if 'your-' not in key_value.lower() and 'example' not in key_value.lower():
                        found_keys.append(attr)
                        print_success(f"{attr} is configured")
                    else:
                        print_warning(f"{attr} appears to be a placeholder")
        
        if found_keys:
            print_success(f"Found {len(found_keys)} configured API key(s)")
            return True
        else:
            print_warning("No valid API keys found in keys.py")
            return False
            
    except ImportError as e:
        print_error(f"Could not import keys.py: {e}")
        return False
    except Exception as e:
        print_error(f"Error checking API keys: {e}")
        return False

def check_git_hooks():
    """Check if git hooks are installed"""
    print_header("Checking Git Hooks")
    
    hook_path = Path('.git/hooks/pre-commit')
    
    if not Path('.git').exists():
        print_warning("Not a git repository")
        return True
    
    if hook_path.exists():
        print_success("Pre-commit hook is installed")
        
        # Check if it's executable (Unix-like systems)
        if os.name != 'nt' and not os.access(hook_path, os.X_OK):
            print_warning("Pre-commit hook is not executable")
            print("   Fix: chmod +x .git/hooks/pre-commit")
            return False
        
        return True
    else:
        print_warning("Pre-commit hook is not installed")
        print("   Run: ./setup_security.sh (Linux/macOS) or setup_security.bat (Windows)")
        return False

def scan_for_exposed_keys():
    """Scan common files for accidentally exposed keys"""
    print_header("Scanning for Exposed Keys")
    
    # Patterns that might indicate exposed keys
    patterns = [
        (r'sk-[a-zA-Z0-9]{48}', 'OpenAI API key'),
        (r'sk-ant-[a-zA-Z0-9-]{95}', 'Anthropic API key'),
        (r'["\']OPENAI_API_KEY["\']:\s*["\']sk-', 'OpenAI key in config'),
        (r'["\']DEEPSEEK_API_KEY["\']:\s*["\']sk-', 'DeepSeek key in config'),
    ]
    
    # Files to scan (excluding keys.py which should be ignored)
    files_to_scan = [
        'config.json',
        'config.deepseek.json',
        'config.openai.json',
        'README.md',
        'SECURITY.md',
    ]
    
    found_issues = False
    
    for file_path in files_to_scan:
        if not os.path.exists(file_path):
            continue
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for pattern, description in patterns:
                if re.search(pattern, content):
                    print_error(f"Potential {description} found in {file_path}!")
                    found_issues = True
        except Exception as e:
            print_warning(f"Could not scan {file_path}: {e}")
    
    if not found_issues:
        print_success("No exposed keys found in scanned files")
    
    return not found_issues

def main():
    """Run all security checks"""
    print(f"\n{BLUE}🔒 DeepEcho Security Check{RESET}\n")
    
    checks = [
        ("Gitignore Configuration", check_gitignore),
        ("Keys File Status", check_keys_file),
        ("Git History", check_git_history),
        ("API Keys", check_api_keys),
        ("Git Hooks", check_git_hooks),
        ("Exposed Keys Scan", scan_for_exposed_keys),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print_error(f"Error during {name}: {e}")
            results.append((name, False))
    
    # Summary
    print_header("Security Check Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        if result:
            print_success(f"{name}: PASS")
        else:
            print_error(f"{name}: FAIL")
    
    print(f"\n{BLUE}Results: {passed}/{total} checks passed{RESET}\n")
    
    if passed == total:
        print_success("All security checks passed! ✨")
        return 0
    else:
        print_warning("Some security checks failed. Please review the issues above.")
        print(f"\nFor more information, see: {BLUE}SECURITY.md{RESET}\n")
        return 1

if __name__ == '__main__':
    sys.exit(main())
