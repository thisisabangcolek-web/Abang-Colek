$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host 'ABANGCOLEK setup'
python --version
python -m pip install -r .\requirements.lock

Write-Host 'Checking external no-key collectors...'
$missing = @()
foreach ($cmd in @('yt-dlp','gallery-dl')) {
  if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) { $missing += $cmd }
}
if ($missing.Count -gt 0) {
  Write-Warning ('Optional collector executables missing: ' + ($missing -join ', '))
}
python -m src.scripts.doctor
