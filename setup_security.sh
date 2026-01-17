#!/bin/bash
#
# Security Setup Script for DeepEcho
# This script helps set up security measures to prevent API key leaks
#

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔒 DeepEcho Security Setup${NC}"
echo ""

# 1. Check if .gitignore includes keys.py
echo "📋 Checking .gitignore configuration..."
if grep -q "keys.py" .gitignore; then
    echo -e "${GREEN}✅ keys.py is in .gitignore${NC}"
else
    echo -e "${YELLOW}⚠️  Adding keys.py to .gitignore${NC}"
    echo "keys.py" >> .gitignore
fi

# 2. Check if keys.py exists
if [ -f "keys.py" ]; then
    echo -e "${YELLOW}⚠️  keys.py file exists${NC}"
    
    # Check if it's tracked by git
    if git ls-files --error-unmatch keys.py 2>/dev/null; then
        echo -e "${YELLOW}⚠️  WARNING: keys.py is tracked by git!${NC}"
        echo "   Run: git rm --cached keys.py"
        echo "   Then commit the change to remove it from git tracking"
    else
        echo -e "${GREEN}✅ keys.py is not tracked by git${NC}"
    fi
else
    echo -e "${YELLOW}ℹ️  keys.py does not exist yet${NC}"
    
    # Check if template exists
    if [ -f "keys.example.py" ]; then
        echo "   To create it, run: cp keys.example.py keys.py"
    fi
fi

# 3. Set up git hooks
echo ""
echo "🪝 Setting up git hooks..."

if [ -d ".git" ]; then
    # Make hooks directory if it doesn't exist
    mkdir -p .git/hooks
    
    # Copy pre-commit hook
    if [ -f ".git-hooks/pre-commit" ]; then
        cp .git-hooks/pre-commit .git/hooks/pre-commit
        chmod +x .git/hooks/pre-commit
        echo -e "${GREEN}✅ Pre-commit hook installed${NC}"
    else
        echo -e "${YELLOW}⚠️  Pre-commit hook template not found${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Not a git repository${NC}"
fi

# 4. Check for accidentally committed secrets
echo ""
echo "🔍 Checking git history for potential secrets..."

if [ -d ".git" ]; then
    # Check if keys.py was ever committed
    if git log --all --full-history --source -- keys.py 2>/dev/null | grep -q "commit"; then
        echo -e "${YELLOW}⚠️  WARNING: keys.py appears in git history!${NC}"
        echo "   This means it may have been committed in the past."
        echo "   Consider using git filter-branch to remove it from history."
        echo "   See SECURITY.md for instructions."
    else
        echo -e "${GREEN}✅ No keys.py found in git history${NC}"
    fi
fi

# 5. Create keys.py from template if needed
echo ""
echo "🔑 API Key Configuration"

if [ ! -f "keys.py" ] && [ -f "keys.example.py" ]; then
    read -p "Would you like to create keys.py from template? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp keys.example.py keys.py
        echo -e "${GREEN}✅ Created keys.py from template${NC}"
        echo "   Please edit keys.py and add your actual API keys"
    fi
fi

# 6. Summary
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Security setup complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Edit keys.py and add your API keys"
echo "  2. Never commit keys.py to git"
echo "  3. Read SECURITY.md for more information"
echo ""
echo "To verify your setup:"
echo "  git check-ignore keys.py  # Should output: keys.py"
echo "  git ls-files | grep keys.py  # Should output: (nothing)"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
