param(
    [Parameter(Mandatory = $true)]
    [string]$OutputPath
)

$extensionRoot = Split-Path -Parent $PSScriptRoot
$resolvedOutputPath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutputPath)
$outputDirectory = Split-Path -Parent $resolvedOutputPath

if (-not (Test-Path -LiteralPath $outputDirectory)) {
    New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
}

if (Test-Path -LiteralPath $resolvedOutputPath) {
    Remove-Item -LiteralPath $resolvedOutputPath -Force
}

Push-Location $extensionRoot
try {
    Add-Type -AssemblyName System.IO.Compression
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archive = [System.IO.Compression.ZipFile]::Open(
        $resolvedOutputPath,
        [System.IO.Compression.ZipArchiveMode]::Create
    )
    try {
        $sourceFiles = @(
            (Join-Path $extensionRoot 'manifest.json')
        ) + @(
            Get-ChildItem -LiteralPath (Join-Path $extensionRoot 'files') -File -Recurse |
                Select-Object -ExpandProperty FullName
        )
        foreach ($sourceFile in $sourceFiles) {
            $entryName = $sourceFile.Substring($extensionRoot.Length).TrimStart('\', '/').Replace('\', '/')
            [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
                $archive,
                $sourceFile,
                $entryName,
                [System.IO.Compression.CompressionLevel]::Optimal
            ) | Out-Null
        }
    }
    finally {
        $archive.Dispose()
    }
}
finally {
    Pop-Location
}

Write-Output $resolvedOutputPath
