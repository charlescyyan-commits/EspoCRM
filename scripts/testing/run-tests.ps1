[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateNotNullOrEmpty()]
    [string]$Suite = "help",

    [Parameter()]
    [string]$PythonExecutable
)

$ErrorActionPreference = "Stop"

$ExitCodes = @{
    Pass = 0
    TestFailure = 1
    ConfigurationError = 2
    MissingDependency = 3
}

$SupportedSuites = @("extension", "connector", "worker", "static", "runtime", "baseline", "regression", "all", "help")
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$ResultsRoot = Join-Path $RepoRoot "temp\test-results"

function Write-Usage {
    @"
Usage:
  powershell -ExecutionPolicy Bypass -File scripts/testing/run-tests.ps1 <suite> [-PythonExecutable <path>]

Suites:
  extension   Extension metadata and static tests.
  connector   Connector and contract tests.
  worker      Acquisition worker and runner tests.
  static      Deployment-static validation tests.
  runtime     Offline runtime-harness safety tests.
  baseline    Extension package and metadata preflight tests.
  regression  Required offline regression set.
  all         All currently implemented safe suites; reports unimplemented layers.
  help        Show this help.

Exit codes:
  0  All required suites passed.
  1  One or more suites failed.
  2  Invalid arguments or runner configuration error.
  3  Python or a required test entrypoint is missing.
"@
}

function Resolve-PythonExecutable {
    param([string]$RequestedPython)

    if ($RequestedPython) {
        if (-not (Test-Path -LiteralPath $RequestedPython -PathType Leaf)) {
            throw "Requested Python executable was not found: $RequestedPython"
        }
        return (Resolve-Path -LiteralPath $RequestedPython).Path
    }

    $python = Get-Command python -CommandType Application -ErrorAction SilentlyContinue
    if ($python) {
        return $python.Source
    }

    throw "Python was not found on PATH. Install Python 3.12+ or pass -PythonExecutable <path>."
}

function Get-TestCounts {
    param([string]$Text)

    $discovered = 0
    $skipped = 0
    $failed = 0
    $ranMatch = [regex]::Match($Text, "Ran\s+(\d+)\s+test")
    if ($ranMatch.Success) { $discovered = [int]$ranMatch.Groups[1].Value }

    $skippedMatch = [regex]::Match($Text, "skipped=(\d+)")
    if ($skippedMatch.Success) { $skipped = [int]$skippedMatch.Groups[1].Value }

    foreach ($name in @("failures", "errors", "unexpected successes")) {
        $match = [regex]::Match($Text, ("{0}=(\d+)" -f [regex]::Escape($name)))
        if ($match.Success) { $failed += [int]$match.Groups[1].Value }
    }

    return [pscustomobject]@{
        Discovered = $discovered
        Passed = [Math]::Max(0, $discovered - $skipped - $failed)
        Failed = $failed
        Skipped = $skipped
    }
}

function Test-Entrypoint {
    param([string]$Path, [string]$Label)

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "$Label test entrypoint is missing: $Path"
    }
}

function Invoke-TestSuite {
    param(
        [string]$Name,
        [string[]]$CommandArguments,
        [string[]]$RequiredPaths
    )

    foreach ($path in $RequiredPaths) {
        Test-Entrypoint -Path $path -Label $Name
    }

    New-Item -ItemType Directory -Force -Path $ResultsRoot | Out-Null
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss-fff"
    $logPath = Join-Path $ResultsRoot ("{0}-{1}.log" -f $Name.ToLowerInvariant(), $timestamp)
    $commandDisplay = ('"{0}" {1}' -f $script:Python, ($CommandArguments -join " "))
    $started = Get-Date

    $escapedArguments = ($CommandArguments | ForEach-Object {
        if ($_ -match '[\s"]') { '"{0}"' -f ($_ -replace '"', '\"') } else { $_ }
    }) -join " "
    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = $script:Python
    $startInfo.Arguments = $escapedArguments
    $startInfo.WorkingDirectory = $RepoRoot
    $startInfo.UseShellExecute = $false
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $startInfo
    [void]$process.Start()
    $standardOutputTask = $process.StandardOutput.ReadToEndAsync()
    $standardErrorTask = $process.StandardError.ReadToEndAsync()
    $process.WaitForExit()
    $standardOutput = $standardOutputTask.GetAwaiter().GetResult()
    $standardError = $standardErrorTask.GetAwaiter().GetResult()
    $processExitCode = $process.ExitCode
    $text = $standardOutput + $standardError
    $text | Out-File -LiteralPath $logPath -Encoding utf8
    $output = $text -split "`r?`n"
    Write-Host ($output | Out-String)
    $duration = (Get-Date) - $started
    $counts = Get-TestCounts -Text $text
    $status = if ($processExitCode -eq 0 -and $counts.Discovered -gt 0) { "PASS" } else { "FAIL" }
    $exitCode = if ($status -eq "PASS") { $ExitCodes.Pass } elseif ($processExitCode -eq 0) { $ExitCodes.ConfigurationError } else { $ExitCodes.TestFailure }

    Write-Host ""
    Write-Host "SUITE SUMMARY"
    Write-Host "Suite: $Name"
    Write-Host "Status: $status"
    Write-Host "Command: $commandDisplay"
    Write-Host "Tests discovered: $($counts.Discovered)"
    Write-Host "Tests passed: $($counts.Passed)"
    Write-Host "Tests failed: $($counts.Failed)"
    Write-Host "Tests skipped: $($counts.Skipped)"
    Write-Host ("Duration: {0:N3}s" -f $duration.TotalSeconds)
    Write-Host "Exit code: $exitCode"
    Write-Host "Log path: $logPath"

    return [pscustomobject]@{
        Name = $Name
        Status = $status
        ExitCode = $exitCode
        Counts = $counts
        Duration = $duration
        LogPath = $logPath
    }
}

function Show-FinalSummary {
    param([object[]]$SuiteResults)

    Write-Host ""
    Write-Host "TEST SUMMARY"
    foreach ($result in $SuiteResults) {
        Write-Host ("{0}: {1}" -f $result.Name, $result.Status)
    }
    $overall = if ($SuiteResults | Where-Object { $_.Status -ne "PASS" }) { "FAIL" } else { "PASS" }
    if ($overall -eq "PASS") {
        $exitCode = $ExitCodes.Pass
    }
    elseif ($SuiteResults | Where-Object { $_.ExitCode -eq $ExitCodes.MissingDependency }) {
        $exitCode = $ExitCodes.MissingDependency
    }
    elseif ($SuiteResults | Where-Object { $_.ExitCode -eq $ExitCodes.ConfigurationError }) {
        $exitCode = $ExitCodes.ConfigurationError
    }
    else {
        $exitCode = $ExitCodes.TestFailure
    }
    Write-Host "Overall: $overall"
    Write-Host "Exit code: $exitCode"
    return $exitCode
}

if ($Suite -notin $SupportedSuites) {
    [Console]::Error.WriteLine("Invalid suite '$Suite'.")
    Write-Usage
    exit $ExitCodes.ConfigurationError
}

if ($Suite -eq "help") {
    Write-Usage
    exit $ExitCodes.Pass
}

try {
    $script:Python = Resolve-PythonExecutable -RequestedPython $PythonExecutable
}
catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit $ExitCodes.MissingDependency
}

$previousPythonPath = $env:PYTHONPATH
$connectorPath = Join-Path $RepoRoot "chitu-connector"
$env:PYTHONPATH = if ($previousPythonPath) { "$connectorPath;$previousPythonPath" } else { $connectorPath }

$definitions = @{
    extension = @{ Name = "Extension"; Arguments = @("-m", "unittest", "discover", "-s", (Join-Path $RepoRoot "crm-extension\tests"), "-p", "test_*.py", "-v"); RequiredPaths = @((Join-Path $RepoRoot "crm-extension\tests")) }
    connector = @{ Name = "Connector"; Arguments = @("-m", "unittest", "discover", "-s", (Join-Path $RepoRoot "chitu-connector\tests"), "-p", "test_*.py", "-v"); RequiredPaths = @((Join-Path $RepoRoot "chitu-connector\tests")) }
    worker = @{ Name = "Worker"; Arguments = @("-m", "unittest", "discover", "-s", (Join-Path $RepoRoot "chitu-connector\tests"), "-p", "test_phase3c02_*.py", "-v"); RequiredPaths = @((Join-Path $RepoRoot "chitu-connector\tests")) }
    static = @{ Name = "Static"; Arguments = @("-m", "unittest", "discover", "-s", (Join-Path $RepoRoot "deployment\validation"), "-p", "test_*.py", "-v"); RequiredPaths = @((Join-Path $RepoRoot "deployment\validation")) }
    runtime = @{ Name = "Runtime"; Arguments = @("-m", "unittest", "discover", "-s", (Join-Path $RepoRoot "tests\runtime"), "-p", "test_*.py", "-v"); RequiredPaths = @((Join-Path $RepoRoot "tests\runtime")) }
    baseline = @{ Name = "Baseline"; Arguments = @("-m", "unittest", "discover", "-s", (Join-Path $RepoRoot "tests\regression"), "-p", "test_*.py", "-v"); RequiredPaths = @((Join-Path $RepoRoot "tests\regression"), (Join-Path $RepoRoot "crm-extension\scripts\build_release_package.ps1")) }
}

try {
    $results = @()
    if ($Suite -in @("extension", "connector", "worker", "static", "runtime", "baseline")) {
        $definition = $definitions[$Suite]
        $results += Invoke-TestSuite -Name $definition.Name -CommandArguments $definition.Arguments -RequiredPaths $definition.RequiredPaths
    }
    else {
        foreach ($key in @("extension", "connector", "worker", "static", "runtime", "baseline")) {
            $definition = $definitions[$key]
            $results += Invoke-TestSuite -Name $definition.Name -CommandArguments $definition.Arguments -RequiredPaths $definition.RequiredPaths
        }

        $regressionStatus = if ($results | Where-Object { $_.Status -ne "PASS" }) { "FAIL" } else { "PASS" }
        $results += [pscustomobject]@{ Name = "Regression"; Status = $regressionStatus; ExitCode = if ($regressionStatus -eq "PASS") { 0 } else { 1 }; Counts = $null; Duration = [TimeSpan]::Zero; LogPath = "See suite logs above" }

        if ($Suite -eq "all") {
            Write-Host ""
            Write-Host "OPTIONAL: Browser - NOT IMPLEMENTED - SKIPPED - no test suite implemented"
            Write-Host "OPTIONAL: Performance - NOT IMPLEMENTED - SKIPPED - no test suite implemented"
            Write-Host "OPTIONAL: Install/upgrade/rollback lifecycle - NOT IMPLEMENTED - SKIPPED - archive preflight is covered by Baseline"
        }
    }

    $finalExitCode = Show-FinalSummary -SuiteResults $results
    exit $finalExitCode
}
catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit $ExitCodes.MissingDependency
}
finally {
    $env:PYTHONPATH = $previousPythonPath
}
