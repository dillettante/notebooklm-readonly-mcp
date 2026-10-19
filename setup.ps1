$ErrorActionPreference = "Stop"
Push-Location $PSScriptRoot
try {
    uv sync --frozen --no-editable
    if ($LASTEXITCODE -ne 0) { throw "Installation failed" }
    Write-Host "Installed. Next: uv run --frozen --no-editable playwright install chromium"
    Write-Host "Then: uv run --frozen --no-editable notebooklm login"
} finally {
    Pop-Location
}
