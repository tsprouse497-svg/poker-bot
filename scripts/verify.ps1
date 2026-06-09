$ErrorActionPreference = "Stop"
$uv = Get-Command uv -ErrorAction SilentlyContinue
if ($uv) {
    & $uv.Source run python scripts/run_verify.py @args
} else {
    python -m uv run python scripts/run_verify.py @args
}
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
