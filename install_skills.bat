@echo off
REM ========================================
REM HKEX Agent - Skills Installation Script
REM For Windows CMD
REM ========================================

setlocal enabledelayedexpansion

echo.
echo ========================================
echo HKEX Agent - Skills Installation
echo ========================================
echo.

REM Get agent directory name from environment variable or use default
if "%HKEX_AGENT_DIR%"=="" (
    set AGENT_DIR_NAME=.hkex-agent
) else (
    set AGENT_DIR_NAME=%HKEX_AGENT_DIR%
)

REM Define source and destination paths
set SKILLS_SOURCE=examples\skills
set SKILLS_DEST=%USERPROFILE%\%AGENT_DIR_NAME%\hkex-agent\skills

REM Check if source directory exists
if not exist "%SKILLS_SOURCE%" (
    echo [ERROR] Source directory not found: %SKILLS_SOURCE%
    echo Please run this script from the deepagents-hk project root.
    echo.
    pause
    exit /b 1
)

REM Create destination directory if it doesn't exist
echo [1/3] Creating skills directory...
if not exist "%SKILLS_DEST%" (
    mkdir "%SKILLS_DEST%" 2>nul
    if errorlevel 1 (
        echo [ERROR] Failed to create directory: %SKILLS_DEST%
        echo.
        pause
        exit /b 1
    )
    echo      Created: %SKILLS_DEST%
) else (
    echo      Already exists: %SKILLS_DEST%
)

REM Copy skills to destination
echo.
echo [2/3] Copying skills...
xcopy "%SKILLS_SOURCE%\*" "%SKILLS_DEST%\" /E /I /Y >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to copy skills.
    echo.
    pause
    exit /b 1
)

REM Count installed skills
set SKILL_COUNT=0
for /d %%i in ("%SKILLS_DEST%\*") do (
    if exist "%%i\SKILL.md" (
        set /a SKILL_COUNT+=1
    )
)

echo      Copied %SKILL_COUNT% skills successfully.

REM List installed skills
echo.
echo [3/3] Installed skills:
for /d %%i in ("%SKILLS_DEST%\*") do (
    if exist "%%i\SKILL.md" (
        echo      - %%~ni
    )
)

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Skills installed to: %SKILLS_DEST%
echo.
echo Next steps:
echo   1. Start the HKEX Agent: hkex
echo   2. List skills: /skills list
echo   3. View skill details: /skills show hkex-announcement-analysis
echo.
pause

