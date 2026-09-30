<#
  init_genesis.ps1
  Initialize the Integrated Avodah genesis workspace.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Host 'Initializing Integrated Avodah genesis workspace...' -ForegroundColor Cyan

$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $root

if (-not (Test-Path '.git')) {
    Write-Host 'Initializing git repository...' -ForegroundColor Yellow
    git init | Out-Null
} else {
    Write-Host 'Git repository already initialized.' -ForegroundColor Green
}

$dirs = @('plan', 'images')
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        Write-Host "Creating directory: $dir" -ForegroundColor Yellow
        New-Item -ItemType Directory -Path $dir | Out-Null
    }
}

if (-not (Test-Path 'styles.css')) {
    Write-Host 'Warning: styles.css not found in repository root.' -ForegroundColor Red
}

Write-Host 'Genesis initialization complete.' -ForegroundColor Green
Write-Host 'Next steps:'
Write-Host '  1. Review index.html and plan/index.html'
Write-Host '  2. Add a remote and push to your repository if desired.'
