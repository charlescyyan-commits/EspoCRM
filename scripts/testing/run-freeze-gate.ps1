[CmdletBinding()]
param(
    [Parameter()]
    [string]$PythonExecutable,

    [Parameter()]
    [string[]]$ChangedPath,

    [Parameter()]
    [switch]$Help
)

$ErrorActionPreference = "Stop"
$ExitCodes = @{ Pass = 0; ConfigurationError = 2; MissingDependency = 3 }
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$RegressionGate = Join-Path $PSScriptRoot "run-regression-gate.ps1"

function Write-Usage {
    @"
Usage:
  powershell -ExecutionPolicy Bypass -File scripts/testing/run-freeze-gate.ps1 [-PythonExecutable <path>] [-ChangedPath <path>...]

Runs the complete offline freeze baseline by delegating to the fail-closed
regression gate. Required coverage is Extension, Connector, Worker, Static,
Runtime, package/metadata Baseline, and runner integrity.

Exit codes are passed through unchanged from run-regression-gate.ps1:
  0  PASS
  1  Required suite failure
  2  Invalid configuration
  3  Missing dependency or entrypoint
  4  Result-artifact write failure
  5  Blocking conditional requirement
"@
}

if ($Help) {
    Write-Usage
    exit $ExitCodes.Pass
}

if (-not (Test-Path -LiteralPath $RegressionGate -PathType Leaf)) {
    [Console]::Error.WriteLine("FREEZE GATE: FAIL - required regression gate is missing: $RegressionGate")
    exit $ExitCodes.MissingDependency
}

$powershell = Get-Command powershell.exe -CommandType Application -ErrorAction SilentlyContinue
if (-not $powershell) {
    [Console]::Error.WriteLine("FREEZE GATE: FAIL - Windows PowerShell is missing.")
    exit $ExitCodes.MissingDependency
}

$arguments = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $RegressionGate)
if ($PythonExecutable) {
    $arguments += @("-PythonExecutable", $PythonExecutable)
}
if ($ChangedPath) {
    $arguments += "-ChangedPath"
    $arguments += $ChangedPath
}

try {
    & $powershell.Source @arguments
    $gateExitCode = $LASTEXITCODE
}
catch {
    [Console]::Error.WriteLine("FREEZE GATE: FAIL - unable to invoke the regression gate: $($_.Exception.Message)")
    exit $ExitCodes.ConfigurationError
}

if ($gateExitCode -eq $ExitCodes.Pass) {
    Write-Host "FREEZE GATE: PASS (exit code 0)"
}
else {
    Write-Host "FREEZE GATE: FAIL (exit code $gateExitCode)"
}

exit $gateExitCode
