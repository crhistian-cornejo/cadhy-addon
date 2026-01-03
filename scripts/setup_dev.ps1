# PowerShell Development Setup Script for Windows
# Run with: .\setup_dev.ps1 [-Force] [-Remove] [-BlenderPath <path>]

param(
    [switch]$Force,
    [switch]$Remove,
    [string]$BlenderPath
)

Write-Host "CADHY Development Setup for Windows" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Check for Python
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "Error: Python not found in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.10+ and add to PATH"
    exit 1
}

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SetupScript = Join-Path $ScriptDir "setup_dev.py"

# Build arguments
$args = @()
if ($Force) { $args += "--force" }
if ($Remove) { $args += "--remove" }
if ($BlenderPath) { $args += "--blender-path"; $args += $BlenderPath }

# Run Python setup script
& python $SetupScript @args

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Setup failed. You may need to:" -ForegroundColor Yellow
    Write-Host "1. Run PowerShell as Administrator, or"
    Write-Host "2. Enable Developer Mode in Windows Settings"
    Write-Host "   Settings > Update & Security > For developers"
    Write-Host ""
}
