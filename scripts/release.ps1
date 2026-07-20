[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Version,

    [string]$PythonExecutable,

    [string]$RequiredBranch = 'master',

    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $PSScriptRoot

function Stop-Release {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message,

        [int]$ExitCode = 1
    )

    [Console]::Error.WriteLine("STOP: $Message")
    exit $ExitCode
}

function Invoke-External {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,

        [Parameter(Mandatory = $true)]
        [string[]]$ArgumentList,

        [Parameter(Mandatory = $true)]
        [string]$Step
    )

    Write-Host "==> $Step"
    & $FilePath @ArgumentList
    if ($LASTEXITCODE -ne 0) {
        Stop-Release "$Step failed with exit code $LASTEXITCODE."
    }
}

function Get-CommandPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($null -eq $command) {
        Stop-Release "Required command '$Name' was not found on PATH." 3
    }

    return $command.Source
}

function Assert-FileContains {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [Parameter(Mandatory = $true)]
        [string]$RequiredText,

        [Parameter(Mandatory = $true)]
        [string]$Description
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        Stop-Release "$Description is missing: $Path" 2
    }

    $content = Get-Content -LiteralPath $Path -Raw
    if (-not $content.Contains($RequiredText)) {
        Stop-Release "$Description does not contain the required value '$RequiredText': $Path" 2
    }
}

if ($Version -notmatch '^\d+\.\d+\.\d+(?:-[0-9A-Za-z][0-9A-Za-z.-]*)?$') {
    Stop-Release "Version '$Version' is invalid. Expected MAJOR.MINOR.PATCH with an optional prerelease suffix." 2
}

Set-Location -LiteralPath $RepoRoot

$git = Get-CommandPath 'git.exe'
$branch = (& $git branch --show-current).Trim()
if ($LASTEXITCODE -ne 0) {
    Stop-Release 'Unable to determine the current Git branch.' 3
}
if ($branch -ne $RequiredBranch) {
    Stop-Release "Current branch '$branch' does not match required branch '$RequiredBranch'." 3
}

$dirtyEntries = & $git status --porcelain
if ($LASTEXITCODE -ne 0) {
    Stop-Release 'Unable to inspect the Git working tree.' 3
}
if ($null -ne $dirtyEntries -and @($dirtyEntries).Count -gt 0) {
    Stop-Release 'Git working tree is not clean. Commit, stash, or discard changes before release automation.' 3
}

$manifestPath = Join-Path $RepoRoot 'crm-extension\manifest.json'
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
    Stop-Release "Extension manifest is missing: $manifestPath" 2
}
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
if ($manifest.version -ne $Version) {
    Stop-Release "Manifest version '$($manifest.version)' does not match requested version '$Version'." 2
}

$archiveName = "prospecting-extension-$Version.zip"
$versionPolicyPath = Join-Path $RepoRoot 'docs\release\VERSION_POLICY.md'
$releaseReadmePath = Join-Path $RepoRoot 'docs\release\README.md'
$releaseNotesPath = Join-Path $RepoRoot ("docs\release\RELEASE_NOTES_{0}.md" -f $Version)
Assert-FileContains -Path $versionPolicyPath -RequiredText ('**Current packaged release:** `{0}`' -f $Version) -Description 'Release version policy'
Assert-FileContains -Path $releaseReadmePath -RequiredText $archiveName -Description 'Release documentation index'
Assert-FileContains -Path $releaseNotesPath -RequiredText $archiveName -Description 'Version-specific release notes'

if ([string]::IsNullOrWhiteSpace($PythonExecutable)) {
    $PythonExecutable = Get-CommandPath 'python.exe'
}
elseif (-not (Test-Path -LiteralPath $PythonExecutable -PathType Leaf)) {
    Stop-Release "Python executable does not exist: $PythonExecutable" 3
}

$unifiedGatePath = Join-Path $RepoRoot 'scripts\testing\run-unified-gate.ps1'
$builderPath = Join-Path $RepoRoot 'crm-extension\scripts\build_release_package.py'
$deploymentDirectory = Join-Path $RepoRoot 'deployment'
$artifactPath = Join-Path $deploymentDirectory $archiveName
$sidecarPath = "$artifactPath.sha256"
$powershell = Get-CommandPath 'powershell.exe'

if (-not (Test-Path -LiteralPath $unifiedGatePath -PathType Leaf)) {
    Stop-Release "Unified gate runner is missing: $unifiedGatePath" 2
}
if (-not (Test-Path -LiteralPath $builderPath -PathType Leaf)) {
    Stop-Release "Release builder is missing: $builderPath" 2
}

Invoke-External -FilePath $powershell -ArgumentList @(
    '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $unifiedGatePath,
    '-Profile', 'release', '-PythonExecutable', $PythonExecutable
) -Step 'Unified release gate'

if ($DryRun) {
    Write-Host '==> Dry run: build and checksum generation skipped; validating the existing canonical artifact.'
}
else {
    Invoke-External -FilePath $PythonExecutable -ArgumentList @($builderPath) -Step 'Deterministic extension build and SHA-256 generation'
}

if (-not (Test-Path -LiteralPath $artifactPath -PathType Leaf)) {
    Stop-Release "Release artifact is missing: $artifactPath"
}
if (-not (Test-Path -LiteralPath $sidecarPath -PathType Leaf)) {
    Stop-Release "Release checksum sidecar is missing: $sidecarPath"
}

$sidecarParts = (Get-Content -LiteralPath $sidecarPath -Raw).Trim() -split '\s+'
if ($sidecarParts.Count -ne 2 -or $sidecarParts[1] -ne $archiveName) {
    Stop-Release "Release checksum sidecar has an invalid format: $sidecarPath"
}
$actualHash = (Get-FileHash -LiteralPath $artifactPath -Algorithm SHA256).Hash.ToUpperInvariant()
if ($sidecarParts[0].ToUpperInvariant() -ne $actualHash) {
    Stop-Release "Release checksum sidecar does not match artifact bytes: $artifactPath"
}

Invoke-External -FilePath $PythonExecutable -ArgumentList @($builderPath, '--check') -Step 'Artifact source-byte, ZIP-content, version, and SHA-256 verification'

Write-Host ''
Write-Host 'READY_FOR_RELEASE'
Write-Host "Version: $Version"
Write-Host "Artifact: $artifactPath"
Write-Host "SHA256: $actualHash"
Write-Host ('Mode: {0}' -f $(if ($DryRun) { 'DRY_RUN' } else { 'BUILD' }))
