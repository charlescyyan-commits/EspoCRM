[CmdletBinding()]
param(
    [ValidateSet("test", "run")]
    [string]$Mode = "test",
    [string]$PythonExecutable
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$runtimeDir = Join-Path $repoRoot "scripts\runtime"

if ($PythonExecutable) {
    if (-not (Test-Path -LiteralPath $PythonExecutable -PathType Leaf)) {
        [Console]::Error.WriteLine("Python executable is missing.")
        exit 2
    }
    $python = (Resolve-Path -LiteralPath $PythonExecutable).Path
}
else {
    $candidate = Get-Command python -CommandType Application -ErrorAction SilentlyContinue
    if (-not $candidate) {
        [Console]::Error.WriteLine("Python was not found on PATH.")
        exit 2
    }
    $python = $candidate.Source
}

if ($Mode -eq "test") {
    & $python -m unittest discover -s $runtimeDir -p "test_*.py" -v
}
else {
    & $python (Join-Path $runtimeDir "runtime_gate.py")
}
exit $LASTEXITCODE
