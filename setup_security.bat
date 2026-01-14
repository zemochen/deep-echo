@echo off
REM Security Setup Script for DeepEcho (Windows)
REM This script helps set up security measures to prevent API key leaks

echo.
echo ============================================
echo   DeepEcho Security Setup (Windows)
echo ============================================
echo.

REM 1. Check if .gitignore includes keys.py
echo Checking .gitignore configuration...
findstr /C:"keys.py" .gitignore >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] keys.py is in .gitignore
) else (
    echo [WARNING] Adding keys.py to .gitignore
    echo keys.py >> .gitignore
)

REM 2. Check if keys.py exists
if exist keys.py (
    echo [WARNING] keys.py file exists
    
    REM Check if it's tracked by git
    git ls-files --error-unmatch keys.py >nul 2>&1
    if %errorlevel% equ 0 (
        echo [WARNING] keys.py is tracked by git!
        echo    Run: git rm --cached keys.py
        echo    Then commit the change to remove it from git tracking
    ) else (
        echo [OK] keys.py is not tracked by git
    )
) else (
    echo [INFO] keys.py does not exist yet
    if exist keys.example.py (
        echo    To create it, run: copy keys.example.py keys.py
    )
)

REM 3. Set up git hooks
echo.
echo Setting up git hooks...

if exist .git (
    if not exist .git\hooks mkdir .git\hooks
    
    if exist .git-hooks\pre-commit (
        copy /Y .git-hooks\pre-commit .git\hooks\pre-commit >nul
        echo [OK] Pre-commit hook installed
    ) else (
        echo [WARNING] Pre-commit hook template not found
    )
) else (
    echo [WARNING] Not a git repository
)

REM 4. Check for accidentally committed secrets
echo.
echo Checking git history for potential secrets...

if exist .git (
    git log --all --full-history --source -- keys.py 2>nul | findstr /C:"commit" >nul 2>&1
    if %errorlevel% equ 0 (
        echo [WARNING] keys.py appears in git history!
        echo    This means it may have been committed in the past.
        echo    Consider using git filter-branch to remove it from history.
        echo    See SECURITY.md for instructions.
    ) else (
        echo [OK] No keys.py found in git history
    )
)

REM 5. Create keys.py from template if needed
echo.
echo API Key Configuration

if not exist keys.py (
    if exist keys.example.py (
        set /p create="Would you like to create keys.py from template? (y/n): "
        if /i "%create%"=="y" (
            copy keys.example.py keys.py >nul
            echo [OK] Created keys.py from template
            echo    Please edit keys.py and add your actual API keys
        )
    )
)

REM 6. Summary
echo.
echo ============================================
echo   Security setup complete!
echo ============================================
echo.
echo Next steps:
echo   1. Edit keys.py and add your API keys
echo   2. Never commit keys.py to git
echo   3. Read SECURITY.md for more information
echo.
echo To verify your setup:
echo   git check-ignore keys.py
echo   git ls-files ^| findstr keys.py
echo.
echo ============================================
echo.

pause
