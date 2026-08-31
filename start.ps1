Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "  Anchor - Predictive Intelligence for Customer Retention" -ForegroundColor White
Write-Host "=========================================================" -ForegroundColor Cyan

if (Get-Command py -ErrorAction SilentlyContinue) {
    py -3.13 run.py
} else {
    python run.py
}
