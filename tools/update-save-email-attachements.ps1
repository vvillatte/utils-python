# Rebuild and upgrade the save-email-attachments wheel package
# Project root: D:\Projects\dev-lab\utils\python\

$projectRoot = "D:\Projects\dev-lab\utils\python"
$distPath    = Join-Path $projectRoot "dist"

Write-Host "=== Rebuilding save-email-attachments wheel ==="

# Step 1 — Run Makefile target inside the project root
Push-Location $projectRoot
make build-save-email-attachments
Pop-Location

Write-Host "=== Build complete ==="

# Step 2 — Find newest wheel
$latestWheel = Get-ChildItem "$distPath\save_email_attachments-*.whl" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if (-not $latestWheel) {
    Write-Host "ERROR: No wheel found in dist folder."
    exit 1
}

Write-Host "Latest wheel: $($latestWheel.Name)"

# Step 3 — Install wheel using pip
Write-Host "=== Installing wheel with pip ==="

pip install $latestWheel.FullName --force-reinstall

Write-Host "=== Installation complete ==="

# Step 4 — Optional: verify CLI works
Write-Host "=== Running save-email-attachments --help ==="
save-email-attachments --help
