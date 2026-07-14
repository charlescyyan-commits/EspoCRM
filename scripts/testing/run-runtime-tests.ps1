[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string]$Command = "help",
    [Parameter()]
    [string]$PythonExecutable,
    [Parameter()]
    [string]$RunId
)

$ErrorActionPreference = "Stop"
$exitCodes = @{ Pass = 0; TestFailure = 1; Configuration = 2; Dependency = 3; Cleanup = 4; Safety = 5 }
$supported = @("help", "check", "smoke", "acl", "cleanup-preview", "cleanup", "all")
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$cli = Join-Path $repoRoot "tests\runtime\runtime_cli.py"

if ($Command -notin $supported) { [Console]::Error.WriteLine("Invalid runtime command '$Command'."); exit $exitCodes.Configuration }
if ($Command -eq "help") {
    @"
Usage: powershell -ExecutionPolicy Bypass -File scripts/testing/run-runtime-tests.ps1 <check|smoke|acl|cleanup-preview|cleanup|all> [-PythonExecutable <path>] [-RunId <id>]

Runtime writes are disabled by default. Set the documented local-only environment contract before using check, smoke, acl, cleanup-preview, cleanup, or all.
Exit codes: 0 pass; 1 test failure; 2 configuration; 3 dependency/credential; 4 cleanup/residue; 5 safety guard.
"@
    exit $exitCodes.Pass
}
if (-not (Test-Path -LiteralPath $cli -PathType Leaf)) { [Console]::Error.WriteLine("Runtime harness CLI is missing."); exit $exitCodes.Dependency }
if ($PythonExecutable) {
    if (-not (Test-Path -LiteralPath $PythonExecutable -PathType Leaf)) { [Console]::Error.WriteLine("Python executable is missing."); exit $exitCodes.Dependency }
    $python = (Resolve-Path -LiteralPath $PythonExecutable).Path
}
else {
    $candidate = Get-Command python -CommandType Application -ErrorAction SilentlyContinue
    if (-not $candidate) { [Console]::Error.WriteLine("Python was not found on PATH."); exit $exitCodes.Dependency }
    $python = $candidate.Source
}
$arguments = @($cli, $Command)
if ($RunId) { $arguments += @("--run-id", $RunId) }
& $python @arguments
exit $LASTEXITCODE
