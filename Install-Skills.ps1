# ========================================
# HKEX Agent - Skills Installation Script
# For Windows PowerShell
# ========================================

# Enable strict mode for better error handling
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "HKEX Agent - Skills Installation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get agent directory name from environment variable or use default
$AgentDirName = if ($env:HKEX_AGENT_DIR) { $env:HKEX_AGENT_DIR } else { ".hkex-agent" }

# Define source and destination paths
$SkillsSource = Join-Path $PSScriptRoot "examples\skills"
$SkillsDest = Join-Path $env:USERPROFILE "$AgentDirName\hkex-agent\skills"

# Check if source directory exists
if (-not (Test-Path $SkillsSource)) {
    Write-Host "[ERROR] Source directory not found: $SkillsSource" -ForegroundColor Red
    Write-Host "Please run this script from the deepagents-hk project root." -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

try {
    # Create destination directory if it doesn't exist
    Write-Host "[1/3] Creating skills directory..." -ForegroundColor Yellow
    if (-not (Test-Path $SkillsDest)) {
        New-Item -ItemType Directory -Force -Path $SkillsDest | Out-Null
        Write-Host "     Created: $SkillsDest" -ForegroundColor Green
    } else {
        Write-Host "     Already exists: $SkillsDest" -ForegroundColor Green
    }

    # Copy skills to destination
    Write-Host ""
    Write-Host "[2/3] Copying skills..." -ForegroundColor Yellow
    
    # Get all skill directories
    $SkillDirs = Get-ChildItem -Path $SkillsSource -Directory
    
    foreach ($SkillDir in $SkillDirs) {
        $DestPath = Join-Path $SkillsDest $SkillDir.Name
        Copy-Item -Path $SkillDir.FullName -Destination $DestPath -Recurse -Force
    }
    
    # Count installed skills
    $InstalledSkills = Get-ChildItem -Path $SkillsDest -Directory | 
                       Where-Object { Test-Path (Join-Path $_.FullName "SKILL.md") }
    $SkillCount = $InstalledSkills.Count
    
    Write-Host "     Copied $SkillCount skills successfully." -ForegroundColor Green

    # List installed skills
    Write-Host ""
    Write-Host "[3/3] Installed skills:" -ForegroundColor Yellow
    foreach ($Skill in $InstalledSkills) {
        Write-Host "     - $($Skill.Name)" -ForegroundColor Cyan
    }

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Installation Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Skills installed to: $SkillsDest" -ForegroundColor White
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  1. Start the HKEX Agent: hkex" -ForegroundColor White
    Write-Host "  2. List skills: /skills list" -ForegroundColor White
    Write-Host "  3. View skill details: /skills show hkex-announcement-analysis" -ForegroundColor White
    Write-Host ""

} catch {
    Write-Host ""
    Write-Host "[ERROR] Installation failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Read-Host "Press Enter to exit"

