# C14.1 acceptance-runtime configuration preflight.
#
# This runner accepts no credential values and writes no files. It inherits only
# the protected process environment already supplied by the runtime host.
# It never creates a ProviderAdapter, Queue, Worker, CRM record, or email send.

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$PythonExecutable
)

$ErrorActionPreference = 'Stop'

$requiredVariables = @(
    'BREVO_API_KEY',
    'BREVO_SENDER_EMAIL',
    'BREVO_TEST_RECIPIENT'
)

$missing = @()
foreach ($name in $requiredVariables) {
    $value = [Environment]::GetEnvironmentVariable($name)
    if ([string]::IsNullOrWhiteSpace($value)) {
        Write-Output "$name=MISSING"
        $missing += $name
    }
    else {
        Write-Output "$name=PRESENT"
    }
}

if ($missing.Count -gt 0) {
    Write-Output 'C14_ACCEPTANCE_RUNTIME=BLOCKED'
    exit 2
}

if (-not (Test-Path -LiteralPath $PythonExecutable -PathType Leaf)) {
    Write-Output 'C14_ACCEPTANCE_RUNTIME=BLOCKED'
    Write-Output 'PYTHON_EXECUTABLE=UNAVAILABLE'
    exit 3
}

$workspaceRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$connectorPath = Join-Path $workspaceRoot 'chitu-connector'

$configurationCheck = @'
import sys

sys.path.insert(0, sys.argv[1])

from chitu_connector.espocrm_sync.brevo_provider import BrevoConfiguration

missing = BrevoConfiguration.from_environment().missing_configuration_code()
if missing is not None:
    print("BREVO_ADAPTER_CONFIGURATION=" + missing)
    raise SystemExit(2)

print("BREVO_ADAPTER_CONFIGURATION=READY")
print("PROVIDER_SEND=NOT_INVOKED")
print("QUEUE_WORKER=NOT_INVOKED")
print("CRM_WRITE=NOT_INVOKED")
print("C14_ACCEPTANCE_RUNTIME=READY_FOR_LIVE_ACCEPTANCE")
'@


$encodedScript = $configurationCheck.Replace('"', '\"')

& $PythonExecutable -c $encodedScript $connectorPath
exit $LASTEXITCODE

