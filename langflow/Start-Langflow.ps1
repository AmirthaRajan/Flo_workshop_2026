$ErrorActionPreference = 'Stop'
$executable = Join-Path $PSScriptRoot '.venv\Scripts\langflow.exe'
if (-not (Test-Path -LiteralPath $executable)) {
    throw 'Langflow is not installed in the workshop virtual environment.'
}

$env:LANGFLOW_CONFIG_DIR = Join-Path $PSScriptRoot 'data'
$env:LANGFLOW_SAVE_DB_IN_CONFIG_DIR = 'true'
$env:LANGFLOW_DO_NOT_TRACK = 'true'
$env:DO_NOT_TRACK = '1'
$env:LANGFLOW_AUTO_LOGIN = 'true'

Push-Location $PSScriptRoot
try {
    & $executable run --host 127.0.0.1 --port 7860 --no-open-browser
    if ($LASTEXITCODE -ne 0) {
        throw "Langflow exited with code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}
