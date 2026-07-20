[CmdletBinding()]
param(
    [ValidateSet("release", "offline", "help")]
    [string]$Profile = "release",

    [string]$PythonExecutable
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$ResultsRoot = Join-Path $RepoRoot "temp\test-results"

function Write-Usage {
    @"
Usage:
  powershell -ExecutionPolicy Bypass -File scripts/testing/run-unified-gate.ps1 [-Profile release|offline] -PythonExecutable <path>

Profiles:
  release  S01 release-integrity pytest, unittest, and artifact gates.
  offline  release plus deployment static validation.

The runner does not replace existing scripts/testing/run-tests.ps1, runtime,
regression, or freeze entrypoints. It invokes no CRM, database, or network API.

Exit codes:
  0  Every selected gate passed.
  1  One or more selected gates failed.
  2  Runner configuration is invalid.
  3  Python or a required entrypoint is missing.
"@
}

function Resolve-PythonExecutable {
    if ($PythonExecutable) {
        if (-not (Test-Path -LiteralPath $PythonExecutable -PathType Leaf)) {
            throw "Requested Python executable was not found: $PythonExecutable"
        }
        return (Resolve-Path -LiteralPath $PythonExecutable).Path
    }

    $python = Get-Command python -CommandType Application -ErrorAction SilentlyContinue
    if ($python) { return $python.Source }
    throw "Python was not found on PATH. Pass -PythonExecutable explicitly."
}

function Get-Counts {
    param([string]$Output)

    $passed = 0; $failed = 0; $skipped = 0
    $pytest = [regex]::Match($Output, "(?m)(?<passed>\d+) passed(?:, (?<failed>\d+) failed)?(?:, (?<skipped>\d+) skipped)?")
    if ($pytest.Success) {
        $passed = [int]$pytest.Groups["passed"].Value
        if ($pytest.Groups["failed"].Success) { $failed = [int]$pytest.Groups["failed"].Value }
        if ($pytest.Groups["skipped"].Success) { $skipped = [int]$pytest.Groups["skipped"].Value }
        return [pscustomobject]@{ Passed = $passed; Failed = $failed; Skipped = $skipped }
    }

    $unittest = [regex]::Match($Output, "Ran\s+(?<ran>\d+)\s+test")
    if ($unittest.Success) {
        $passed = [int]$unittest.Groups["ran"].Value
        if ($Output -match "FAILED") { $failed = 1; $passed = 0 }
    }
    return [pscustomobject]@{ Passed = $passed; Failed = $failed; Skipped = $skipped }
}

function Invoke-Gate {
    param([hashtable]$Definition)

    foreach ($path in $Definition.RequiredPaths) {
        if (-not (Test-Path -LiteralPath $path)) {
            return [pscustomobject]@{ Name = $Definition.Name; Status = "CONFIGURATION ERROR"; ExitCode = 3; Counts = (Get-Counts ""); Command = ""; LogPath = "" }
        }
    }

    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $script:Python
    $startInfo.Arguments = (($Definition.Arguments | ForEach-Object {
        if ($_ -match '[\s"]') { '"{0}"' -f ($_ -replace '"', '\"') } else { $_ }
    }) -join " ")
    $startInfo.WorkingDirectory = $Definition.WorkingDirectory
    $startInfo.UseShellExecute = $false
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $startInfo
    [void]$process.Start()
    $stdout = $process.StandardOutput.ReadToEndAsync()
    $stderr = $process.StandardError.ReadToEndAsync()
    $process.WaitForExit()
    $output = $stdout.GetAwaiter().GetResult() + $stderr.GetAwaiter().GetResult()
    $counts = Get-Counts $output
    $status = if ($process.ExitCode -eq 0 -and ($Definition.AllowZeroTests -or $counts.Passed -gt 0)) { "PASS" } else { "FAIL" }

    New-Item -ItemType Directory -Force -Path $ResultsRoot | Out-Null
    $logPath = Join-Path $ResultsRoot ("unified-{0}-{1}.log" -f $Definition.Name, (Get-Date -Format "yyyyMMdd-HHmmss-fff"))
    $output | Out-File -LiteralPath $logPath -Encoding utf8
    Write-Host $output
    Write-Host ("GATE {0}: {1} (passed={2}, failed={3}, skipped={4}, exit={5})" -f $Definition.Name, $status, $counts.Passed, $counts.Failed, $counts.Skipped, $process.ExitCode)
    return [pscustomobject]@{ Name = $Definition.Name; Status = $status; ExitCode = $process.ExitCode; Counts = $counts; Command = ('"{0}" {1}' -f $script:Python, $startInfo.Arguments); LogPath = $logPath }
}

if ($Profile -eq "help") { Write-Usage; exit 0 }

try { $script:Python = Resolve-PythonExecutable }
catch { [Console]::Error.WriteLine($_.Exception.Message); exit 3 }

$extensionTests = Join-Path $RepoRoot "crm-extension\tests"
$connectorTests = Join-Path $RepoRoot "chitu-connector\tests"
$rootTests = Join-Path $RepoRoot "tests"
$runtimeScripts = Join-Path $RepoRoot "scripts\runtime"
$regressionTests = Join-Path $RepoRoot "tests\regression"
$deploymentValidation = Join-Path $RepoRoot "deployment\validation"
$builder = Join-Path $RepoRoot "crm-extension\scripts\build_release_package.py"

$gates = @(
    @{ Name = "extension-pytest"; WorkingDirectory = $RepoRoot; Arguments = @("-m", "pytest", "crm-extension/tests", "-q"); RequiredPaths = @($extensionTests); AllowZeroTests = $false },
    @{ Name = "connector-pytest"; WorkingDirectory = (Join-Path $RepoRoot "chitu-connector"); Arguments = @("-m", "pytest", "tests", "-q"); RequiredPaths = @($connectorTests); AllowZeroTests = $false },
    @{ Name = "root-runtime-pytest"; WorkingDirectory = $RepoRoot; Arguments = @("-m", "pytest", "tests", "scripts/runtime", "-q"); RequiredPaths = @($rootTests, $runtimeScripts); AllowZeroTests = $false },
    @{ Name = "s01-integrity-pytest"; WorkingDirectory = $RepoRoot; Arguments = @("-m", "pytest", "tests/regression/test_phase3s01_release_integrity.py", "-q"); RequiredPaths = @((Join-Path $regressionTests "test_phase3s01_release_integrity.py")); AllowZeroTests = $false },
    @{ Name = "package-baseline-pytest"; WorkingDirectory = $RepoRoot; Arguments = @("-m", "pytest", "tests/regression/test_extension_package_baseline.py", "-q"); RequiredPaths = @((Join-Path $regressionTests "test_extension_package_baseline.py"), $builder); AllowZeroTests = $false },
    @{ Name = "extension-unittest"; WorkingDirectory = $RepoRoot; Arguments = @("-m", "unittest", "discover", "-s", "crm-extension/tests"); RequiredPaths = @($extensionTests); AllowZeroTests = $false },
    @{ Name = "artifact-check"; WorkingDirectory = $RepoRoot; Arguments = @("crm-extension/scripts/build_release_package.py", "--check"); RequiredPaths = @($builder); AllowZeroTests = $true }
)

if ($Profile -eq "offline") {
    $gates += @{ Name = "deployment-validation-pytest"; WorkingDirectory = $RepoRoot; Arguments = @("-m", "pytest", "deployment/validation", "-q"); RequiredPaths = @($deploymentValidation); AllowZeroTests = $false }
}

$results = @($gates | ForEach-Object { Invoke-Gate $_ })
Write-Host ""
Write-Host "UNIFIED GATE SUMMARY"
$results | ForEach-Object { Write-Host ("{0}: {1}" -f $_.Name, $_.Status) }
$failed = @($results | Where-Object { $_.Status -ne "PASS" })
if ($failed.Count -gt 0) { exit 1 }
exit 0
