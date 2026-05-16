# Запуск API + admin через Daphne (ASGI)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

if (-not $env:DJANGO_SETTINGS_MODULE) {
    $env:DJANGO_SETTINGS_MODULE = "config.settings"
}

$bind = if ($env:DAPHNE_BIND) { $env:DAPHNE_BIND } else { "127.0.0.1" }
$port = if ($env:DAPHNE_PORT) { $env:DAPHNE_PORT } else { "8000" }

Write-Host "Daphne: http://${bind}:${port}/  (ASGI: config.asgi:application)" -ForegroundColor Cyan

$python = Join-Path (Resolve-Path "$PSScriptRoot\..") "env\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Error "Не найден venv: $python"
}

& $python -m daphne -b $bind -p $port config.asgi:application
