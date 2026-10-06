$ErrorActionPreference = "Stop"

$VaultDir = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$GithubDir = Join-Path $VaultDir "sources\github"
$NormalizeScript = Join-Path $PSScriptRoot "normalize_github.py"

New-Item -ItemType Directory -Force $GithubDir | Out-Null

function New-Utf8Encoding {
    # No BOM. A BOM would make the following JSON parser fail.
    New-Object System.Text.UTF8Encoding $false
}

function Write-NormalizedGitHub {
    param(
        [Parameter(Mandatory = $true)]
        [string]$SourceType,

        [Parameter(Mandatory = $true)]
        [AllowEmptyString()]
        [string]$RawJson,

        [Parameter(Mandatory = $true)]
        [string]$OutPath
    )

    # PowerShell 5.1 ConvertFrom-Json turns timestamps into DateTime.
    # Piping to Python also breaks non-ASCII text, so pass a UTF-8 file.
    $tempName = "github-raw-" + [guid]::NewGuid().ToString() + ".json"
    $temp = [System.IO.Path]::GetTempPath() + $tempName

    try {
        $encoding = New-Utf8Encoding
        [System.IO.File]::WriteAllText($temp, $RawJson, $encoding)
        & py -3 $NormalizeScript $SourceType $temp $OutPath
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to normalize GitHub data: $OutPath"
        }
    } finally {
        if ($temp -and [System.IO.File]::Exists($temp)) {
            [System.IO.File]::Delete($temp)
        }
    }
}

function Get-GhJson {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    $gh = (Get-Command gh -ErrorAction Stop).Source
    $quoted = $Arguments | ForEach-Object {
        if ($_ -match '[\s"]') {
            '"' + ($_ -replace '"', '\"') + '"'
        } else {
            $_
        }
    }

    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = $gh
    $startInfo.Arguments = ($quoted -join " ")
    $startInfo.UseShellExecute = $false
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $startInfo.CreateNoWindow = $true
    $encoding = New-Utf8Encoding
    $startInfo.StandardOutputEncoding = $encoding
    $startInfo.StandardErrorEncoding = $encoding

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $startInfo
    [void]$process.Start()

    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()
    $process.WaitForExit()

    $stdout = $stdoutTask.Result
    $stderr = $stderrTask.Result

    if ($process.ExitCode -ne 0) {
        throw "Failed to fetch GitHub data: gh $($Arguments -join ' ')`n$stderr"
    }

    if ([string]::IsNullOrWhiteSpace($stdout)) {
        return "[]"
    }

    return $stdout
}

Write-Host "Fetching assigned issues..."

$assigned = Get-GhJson -Arguments @(
    "search", "issues",
    "--assignee=@me",
    "--state=open",
    "--limit=100",
    "--json", "number,title,body,state,repository,labels,assignees,author,createdAt,updatedAt,url"
)

Write-NormalizedGitHub `
    -SourceType "github_issue" `
    -RawJson $assigned `
    -OutPath (Join-Path $GithubDir "assigned-issues.json")

Write-Host "Fetching my PRs..."

$myPrs = Get-GhJson -Arguments @(
    "search", "prs",
    "--author=@me",
    "--state=open",
    "--limit=100",
    "--json", "number,title,body,state,repository,labels,author,isDraft,createdAt,updatedAt,url"
)

Write-NormalizedGitHub `
    -SourceType "github_pr" `
    -RawJson $myPrs `
    -OutPath (Join-Path $GithubDir "my-prs.json")

Write-Host "Fetching review requests..."

$reviews = Get-GhJson -Arguments @(
    "search", "prs",
    "--review-requested=@me",
    "--state=open",
    "--limit=100",
    "--json", "number,title,body,state,repository,labels,author,isDraft,createdAt,updatedAt,url"
)

Write-NormalizedGitHub `
    -SourceType "github_pr" `
    -RawJson $reviews `
    -OutPath (Join-Path $GithubDir "review-requests.json")

Write-Host ""
Write-Host "GitHub data updated."
