[CmdletBinding()]
param(
    [Parameter()]
    [string]$PythonExecutable,

    [Parameter()]
    [string[]]$ChangedPath,

    [Parameter()]
    [string]$MapPath,

    [Parameter()]
    [switch]$Help
)

$ErrorActionPreference = "Stop"
$GateExitCodes = @{ Pass = 0; RequiredFailure = 1; ConfigurationError = 2; MissingDependency = 3; ResultWriteFailure = 4; ConditionalBlocking = 5 }
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$RunnerPath = Join-Path $PSScriptRoot "run-tests.ps1"
$ResultsRoot = Join-Path $RepoRoot "temp\test-results"
if (-not $MapPath) { $MapPath = Join-Path $PSScriptRoot "regression-gate-map.json" }

function Write-Usage {
    @"
Usage:
  powershell -ExecutionPolicy Bypass -File scripts/testing/run-regression-gate.ps1 [-PythonExecutable <path>] [-ChangedPath <path>...]

Runs the complete required offline core gate every time: Extension, Connector,
Worker, Static, and runner-integrity checks. Changed paths classify impact for
the report only; they never reduce the required test set.

Exit codes:
  0  Gate passed.
  1  A required suite failed.
  2  Invalid gate configuration or unparseable runner output.
  3  Required dependency or runner entrypoint missing.
  4  Machine-readable result generation failed.
  5  A blocking conditional requirement was unmet.
"@
}

function Quote-ProcessArgument {
    param([string]$Value)
    if ($Value -match '[\s"]') { return '"{0}"' -f ($Value -replace '"', '\"') }
    return $Value
}

function Invoke-ProcessCapture {
    param([string]$FileName, [string[]]$Arguments, [string]$WorkingDirectory)

    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = $FileName
    $startInfo.Arguments = (($Arguments | ForEach-Object { Quote-ProcessArgument $_ }) -join " ")
    $startInfo.WorkingDirectory = $WorkingDirectory
    $startInfo.UseShellExecute = $false
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $startInfo
    [void]$process.Start()
    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()
    $process.WaitForExit()
    return [pscustomobject]@{
        ExitCode = $process.ExitCode
        Output = $stdoutTask.GetAwaiter().GetResult() + $stderrTask.GetAwaiter().GetResult()
    }
}

function Get-FieldValue {
    param([string]$Text, [string]$Field)
    $match = [regex]::Match($Text, ("(?m)^{0}:\s*(?<value>.+?)\s*$" -f [regex]::Escape($Field)))
    if (-not $match.Success) { return $null }
    return $match.Groups["value"].Value.Trim()
}

function Get-IntFieldValue {
    param([string]$Text, [string]$Field)
    $value = Get-FieldValue -Text $Text -Field $Field
    $parsed = 0
    if ($null -eq $value -or -not [int]::TryParse($value, [ref]$parsed)) { return $null }
    return $parsed
}

function Get-RunnerSuites {
    param([string]$Output)

    $blocks = [regex]::Matches($Output, "(?ms)^SUITE SUMMARY\r?\n(?<block>.*?)(?=^SUITE SUMMARY|^TEST SUMMARY|\z)")
    $suites = @()
    foreach ($match in $blocks) {
        $block = $match.Groups["block"].Value
        $name = Get-FieldValue -Text $block -Field "Suite"
        $status = Get-FieldValue -Text $block -Field "Status"
        $command = Get-FieldValue -Text $block -Field "Command"
        $exitCode = Get-IntFieldValue -Text $block -Field "Exit code"
        $discovered = Get-IntFieldValue -Text $block -Field "Tests discovered"
        $passed = Get-IntFieldValue -Text $block -Field "Tests passed"
        $failed = Get-IntFieldValue -Text $block -Field "Tests failed"
        $skipped = Get-IntFieldValue -Text $block -Field "Tests skipped"
        $durationText = Get-FieldValue -Text $block -Field "Duration"
        $logPath = Get-FieldValue -Text $block -Field "Log path"
        if ($null -in @($name, $status, $command, $exitCode, $discovered, $passed, $failed, $skipped, $durationText, $logPath)) { return $null }
        $durationSeconds = [double]0
        if (-not [double]::TryParse(($durationText -replace "s$", ""), [ref]$durationSeconds)) { return $null }
        $suites += [pscustomobject][ordered]@{
            name = $name
            classification = "REQUIRED"
            status = $status
            command = $command
            testsDiscovered = $discovered
            testsPassed = $passed
            testsFailed = $failed
            testsSkipped = $skipped
            durationSeconds = $durationSeconds
            exitCode = $exitCode
            logPath = $logPath
        }
    }
    return $suites
}

function Get-ChangedAreas {
    param([object]$Map, [string[]]$ExplicitPaths)

    $paths = @($ExplicitPaths | Where-Object { $_ })
    if ($paths.Count -eq 0) {
        $git = Get-Command git -CommandType Application -ErrorAction SilentlyContinue
        if ($git) {
            $gitStatus = Invoke-ProcessCapture -FileName $git.Source -Arguments @("-C", $RepoRoot, "status", "--porcelain") -WorkingDirectory $RepoRoot
            if ($gitStatus.ExitCode -eq 0) {
                foreach ($line in ($gitStatus.Output -split "`r?`n")) {
                    if ($line.Length -ge 4) { $paths += $line.Substring(3).Trim() }
                }
            }
        }
    }
    if ($paths.Count -eq 0) { return @("unknown") }

    $areas = @()
    foreach ($path in $paths) {
        $normalized = $path.Replace("\", "/")
        $matched = $false
        foreach ($rule in $Map.rules) {
            if ($normalized -like $rule.pattern) {
                $areas += [string]$rule.area
                $matched = $true
            }
        }
        if (-not $matched) { $areas += "unknown" }
    }
    return @($areas | Sort-Object -Unique)
}

function New-GateResult {
    param([object]$Map, [string[]]$ChangedAreas, [object[]]$Suites, [int]$ExitCode, [double]$DurationSeconds, [string[]]$Warnings)

    $requiredSuites = @($Map.requiredSuites | ForEach-Object { [string]$_ })
    $conditional = @()
    foreach ($definition in $Map.conditionalSuites) {
        $shouldReport = @($definition.triggerAreas | Where-Object { $ChangedAreas -contains $_ }).Count -gt 0
        if ($shouldReport) {
            $conditional += [pscustomobject][ordered]@{
                name = [string]$definition.name
                classification = "CONDITIONAL"
                status = [string]$definition.status
                blocking = [bool]$definition.blocking
                reason = [string]$definition.reason
            }
        }
    }
    $optional = @($Map.optionalSuites | ForEach-Object {
        [pscustomobject][ordered]@{ name = [string]$_.name; classification = "OPTIONAL"; status = [string]$_.status; reason = [string]$_.reason }
    })
    $allSuites = @($Suites) + @($conditional) + @($optional)
    $failedRequired = @($Suites | Where-Object { $_.classification -eq "REQUIRED" -and $_.status -ne "PASS" })
    $blockingConditional = @($conditional | Where-Object { $_.blocking -and $_.status -ne "PASS" })
    $failures = @($failedRequired + $blockingConditional)
    if ($ExitCode -ne 0 -and $failures.Count -eq 0) {
        $failures += [pscustomobject][ordered]@{
            name = "Gate"
            classification = "REQUIRED"
            status = "FAIL"
            reason = if ($Warnings.Count -gt 0) { $Warnings[0] } else { "Gate failed without a parseable suite failure." }
        }
    }
    $overallStatus = if ($ExitCode -eq 0) { "PASS" } else { "FAIL" }
    $totals = [ordered]@{
        testsDiscovered = [int](@($Suites | Measure-Object -Property testsDiscovered -Sum).Sum)
        testsPassed = [int](@($Suites | Measure-Object -Property testsPassed -Sum).Sum)
        testsFailed = [int](@($Suites | Measure-Object -Property testsFailed -Sum).Sum)
        testsSkipped = [int](@($Suites | Measure-Object -Property testsSkipped -Sum).Sum)
        requiredSuites = $requiredSuites.Count
        requiredSuitesPassed = @($Suites | Where-Object { $_.classification -eq "REQUIRED" -and $_.status -eq "PASS" }).Count
        conditionalBlockingFailures = $blockingConditional.Count
    }
    return [pscustomobject][ordered]@{
        schemaVersion = "1.0"
        timestamp = (Get-Date).ToUniversalTime().ToString("o")
        gateVersion = [string]$Map.gateVersion
        overallStatus = $overallStatus
        exitCode = $ExitCode
        durationSeconds = [Math]::Round($DurationSeconds, 3)
        requiredSuites = $requiredSuites
        conditionalSuites = $conditional
        optionalSuites = $optional
        changedAreas = $ChangedAreas
        suites = $allSuites
        totals = $totals
        failures = $failures
        warnings = $Warnings
    }
}

function Write-GateArtifacts {
    param([object]$Result)

    New-Item -ItemType Directory -Force -Path $ResultsRoot | Out-Null
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss-fff"
    $jsonPath = Join-Path $ResultsRoot ("regression-gate-{0}.json" -f $timestamp)
    $Result | ConvertTo-Json -Depth 8 | Out-File -LiteralPath $jsonPath -Encoding utf8

    Write-Host ""
    Write-Host "CORE REGRESSION GATE"
    foreach ($suite in $Result.suites | Where-Object { $_.classification -eq "REQUIRED" }) {
        Write-Host ("{0}: {1} - {2} passed, {3} failed, {4} skipped" -f $suite.name, $suite.status, $suite.testsPassed, $suite.testsFailed, $suite.testsSkipped)
    }
    Write-Host ("Required suites: {0}/{1} passed" -f $Result.totals.requiredSuitesPassed, $Result.totals.requiredSuites)
    $conditionalCount = @($Result.conditionalSuites).Count
    if ($conditionalCount -gt 0) {
        Write-Host ("Conditional suites: {0} reported; {1} blocking failures" -f $conditionalCount, $Result.totals.conditionalBlockingFailures)
    }
    Write-Host ("Overall: {0}" -f $Result.overallStatus)
    Write-Host ("Exit code: {0}" -f $Result.exitCode)
    Write-Host ("JSON result: {0}" -f $jsonPath)
    return $jsonPath
}

if ($Help) {
    Write-Usage
    exit $GateExitCodes.Pass
}

$started = Get-Date
$map = $null
$suites = @()
$warnings = @()
$exitCode = $GateExitCodes.Pass
$changedAreas = @("unknown")

try {
    if (-not (Test-Path -LiteralPath $RunnerPath -PathType Leaf)) { throw "MISSING_RUNNER" }
    if (-not (Test-Path -LiteralPath $MapPath -PathType Leaf)) { throw "INVALID_MAP" }
    $map = Get-Content -Raw -LiteralPath $MapPath | ConvertFrom-Json
    if ($map.schemaVersion -ne "1.0" -or $null -eq $map.requiredSuites -or $null -eq $map.rules) { throw "INVALID_MAP" }
    $changedAreas = Get-ChangedAreas -Map $map -ExplicitPaths $ChangedPath
    $blockingConditional = @($map.conditionalSuites | Where-Object {
        $_.blocking -and @($_.triggerAreas | Where-Object { $changedAreas -contains $_ }).Count -gt 0
    })

    $powershell = Get-Command powershell.exe -CommandType Application -ErrorAction SilentlyContinue
    if (-not $powershell) { throw "MISSING_POWERSHELL" }
    $runnerArguments = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $RunnerPath, "regression")
    if ($PythonExecutable) { $runnerArguments += @("-PythonExecutable", $PythonExecutable) }
    $runner = Invoke-ProcessCapture -FileName $powershell.Source -Arguments $runnerArguments -WorkingDirectory $RepoRoot
    Write-Host $runner.Output

    if ($runner.ExitCode -eq 3) {
        $exitCode = $GateExitCodes.MissingDependency
        $warnings += "The underlying test runner reported a missing dependency or entrypoint."
    }
    else {
        $suites = Get-RunnerSuites -Output $runner.Output
        $expectedNames = @("Extension", "Connector", "Worker", "Static", "Runtime", "Baseline")
        $actualNames = (@($suites | ForEach-Object { $_.name } | Sort-Object) -join "|")
        $expectedNamesText = (@($expectedNames | Sort-Object) -join "|")
        if ($null -eq $suites -or @($suites).Count -ne 6 -or $actualNames -ne $expectedNamesText) {
            $exitCode = $GateExitCodes.ConfigurationError
            $warnings += "Runner output could not be parsed into all required suite summaries."
        }
        else {
            $suites += [pscustomobject][ordered]@{
                name = "Runner integrity"; classification = "REQUIRED"; status = "PASS"; command = $RunnerPath; testsDiscovered = 0; testsPassed = 0; testsFailed = 0; testsSkipped = 0; durationSeconds = 0; exitCode = 0; logPath = "Runner output captured by gate"
            }
            if ($runner.ExitCode -eq 0 -and @($suites | Where-Object { $_.status -ne "PASS" }).Count -eq 0) {
                if ($blockingConditional.Count -gt 0) {
                    $exitCode = $GateExitCodes.ConditionalBlocking
                    $warnings += "Blocking conditional requirement(s) unmet: $($blockingConditional.name -join ', ')."
                }
                else {
                    $exitCode = $GateExitCodes.Pass
                }
            }
            elseif ($runner.ExitCode -eq 2) {
                $exitCode = $GateExitCodes.ConfigurationError
            }
            else {
                $exitCode = $GateExitCodes.RequiredFailure
            }
        }
    }
}
catch {
    switch ($_.Exception.Message) {
        "MISSING_RUNNER" { $exitCode = $GateExitCodes.MissingDependency; $warnings += "Required T02 runner is missing." }
        "MISSING_POWERSHELL" { $exitCode = $GateExitCodes.MissingDependency; $warnings += "Windows PowerShell is missing." }
        "INVALID_MAP" { $exitCode = $GateExitCodes.ConfigurationError; $warnings += "Gate map is missing or invalid." }
        default { $exitCode = $GateExitCodes.ConfigurationError; $warnings += "Gate configuration error: $($_.Exception.Message)" }
    }
}

$duration = ((Get-Date) - $started).TotalSeconds
if ($null -eq $map) {
    $map = [pscustomobject]@{ gateVersion = "T05.1"; requiredSuites = @("Extension", "Connector", "Worker", "Static", "Runtime", "Baseline", "Runner integrity"); conditionalSuites = @(); optionalSuites = @() }
}
$result = New-GateResult -Map $map -ChangedAreas $changedAreas -Suites $suites -ExitCode $exitCode -DurationSeconds $duration -Warnings $warnings

try {
    [void](Write-GateArtifacts -Result $result)
}
catch {
    [Console]::Error.WriteLine("Gate result generation failed: $($_.Exception.Message)")
    exit $GateExitCodes.ResultWriteFailure
}

exit $exitCode
