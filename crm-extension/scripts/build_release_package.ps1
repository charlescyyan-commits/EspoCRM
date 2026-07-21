param(
    [Parameter(Mandatory = $true)]
    [string]$OutputPath
)

$extensionRoot = Split-Path -Parent $PSScriptRoot
$resolvedOutputPath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutputPath)
$outputDirectory = Split-Path -Parent $resolvedOutputPath
$textSourceExtensions = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
@('.php', '.py', '.js', '.json', '.tpl', '.md', '.css', '.html', '.xml', '.yml', '.yaml', '.txt') |
    ForEach-Object { [void]$textSourceExtensions.Add($_) }

function Copy-CanonicalPackageBytes {
    param(
        [Parameter(Mandatory = $true)]
        [string]$SourcePath,
        [Parameter(Mandatory = $true)]
        [System.IO.Stream]$Destination
    )

    [byte[]]$sourceBytes = [System.IO.File]::ReadAllBytes($SourcePath)
    if (-not $textSourceExtensions.Contains([System.IO.Path]::GetExtension($SourcePath))) {
        $Destination.Write($sourceBytes, 0, $sourceBytes.Length)
        return
    }

    $normalizedBytes = [System.Collections.Generic.List[byte]]::new($sourceBytes.Length)
    for ($index = 0; $index -lt $sourceBytes.Length; $index++) {
        if ($sourceBytes[$index] -eq 13) {
            [void]$normalizedBytes.Add(10)
            if ($index + 1 -lt $sourceBytes.Length -and $sourceBytes[$index + 1] -eq 10) {
                $index++
            }
        }
        else {
            [void]$normalizedBytes.Add($sourceBytes[$index])
        }
    }
    [byte[]]$canonicalBytes = $normalizedBytes.ToArray()
    $Destination.Write($canonicalBytes, 0, $canonicalBytes.Length)
}

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
            (Join-Path $extensionRoot 'manifest.json'),
            (Join-Path $extensionRoot 'scripts\AfterInstall.php')
        ) + @(
            Get-ChildItem -LiteralPath (Join-Path $extensionRoot 'files') -File -Recurse |
                Select-Object -ExpandProperty FullName
        )
        foreach ($sourceFile in $sourceFiles) {
            $entryName = $sourceFile.Substring($extensionRoot.Length).TrimStart('\', '/').Replace('\', '/')
            $entry = $archive.CreateEntry($entryName, [System.IO.Compression.CompressionLevel]::Optimal)
            $entryStream = $entry.Open()
            try {
                Copy-CanonicalPackageBytes -SourcePath $sourceFile -Destination $entryStream
            }
            finally {
                $entryStream.Dispose()
            }
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
