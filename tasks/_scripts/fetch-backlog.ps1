$ErrorActionPreference = "Stop"

# ========================================
# Paths
# ========================================

$VaultDir = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$EnvFile = Join-Path $VaultDir ".env"
$OutputDir = Join-Path $VaultDir "sources\backlog"

# ========================================
# Load .env
# ========================================

if (-not (Test-Path $EnvFile)) {
    throw ".env not found: $EnvFile"
}

Get-Content $EnvFile | ForEach-Object {
    $line = $_.Trim()

    # 空行・コメント
    if ([string]::IsNullOrWhiteSpace($line) -or $line.StartsWith("#")) {
        return
    }

    $parts = $line -split "=", 2

    if ($parts.Count -ne 2) {
        return
    }

    $name = $parts[0].Trim()
    $value = $parts[1].Trim()

    # "..." / '...' の引用符を除去
    if (
        ($value.StartsWith('"') -and $value.EndsWith('"')) -or
        ($value.StartsWith("'") -and $value.EndsWith("'"))
    ) {
        $value = $value.Substring(1, $value.Length - 2)
    }

    [Environment]::SetEnvironmentVariable(
        $name,
        $value,
        "Process"
    )
}

$BaseUrl = $env:BACKLOG_BASE_URL
$ApiKey = $env:BACKLOG_API_KEY

if ([string]::IsNullOrWhiteSpace($BaseUrl)) {
    throw "BACKLOG_BASE_URL is not defined in .env"
}

if ([string]::IsNullOrWhiteSpace($ApiKey)) {
    throw "BACKLOG_API_KEY is not defined in .env"
}

$BaseUrl = $BaseUrl.TrimEnd("/")

New-Item -ItemType Directory -Force $OutputDir | Out-Null


# ========================================
# Backlog API helper
# ========================================

function Invoke-BacklogGet {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [hashtable]$Query = @{}
    )

    $params = @()

    foreach ($key in $Query.Keys) {
        $encodedKey = [Uri]::EscapeDataString($key)
        $encodedValue = [Uri]::EscapeDataString([string]$Query[$key])

        $params += "$encodedKey=$encodedValue"
    }

    # APIキー
    $params += "apiKey=$([Uri]::EscapeDataString($ApiKey))"

    $uri = "${BaseUrl}${Path}?" + ($params -join "&")

    # Windows PowerShell 5.1 の Invoke-RestMethod は charset 無しの JSON を
    # ISO-8859-1 として読むため、生バイトを UTF-8 でデコードする。
    $response = Invoke-WebRequest `
        -Uri $uri `
        -Method Get `
        -UseBasicParsing

    $stream = $response.RawContentStream
    if ($stream.CanSeek) {
        $stream.Position = 0
    }

    $reader = New-Object System.IO.StreamReader(
        $stream,
        [System.Text.Encoding]::UTF8
    )
    try {
        $json = $reader.ReadToEnd()
    } finally {
        $reader.Dispose()
    }

    return ($json | ConvertFrom-Json)
}


# ========================================
# Current user
# ========================================

Write-Host "Fetching Backlog user..."

$me = Invoke-BacklogGet `
    -Path "/api/v2/users/myself"

Write-Host "User: $($me.name) (ID: $($me.id))"


# ========================================
# Assigned issues
# ========================================

Write-Host "Fetching assigned issues..."

$allIssues = @()
$offset = 0
$count = 100

while ($true) {

    $issues = @(
        Invoke-BacklogGet `
            -Path "/api/v2/issues" `
            -Query @{
                "assigneeId[]" = $me.id
                "sort"         = "updated"
                "order"        = "desc"
                "count"        = $count
                "offset"       = $offset
            }
    )

    $allIssues += $issues

    if ($issues.Count -lt $count) {
        break
    }

    $offset += $count
}

Write-Host "Found: $($allIssues.Count) issues"


# ========================================
# Normalize for Cursor
# ========================================

$result = @(
    $allIssues | ForEach-Object {

        [PSCustomObject]@{
            sourceType     = "backlog_issue"
            sourceId       = $_.issueKey
            sourceUrl      = "$BaseUrl/view/$($_.issueKey)"
            sourceUpdatedAt = $_.updated

            id             = $_.id
            issueKey       = $_.issueKey
            summary        = $_.summary
            description    = $_.description

            project = if ($_.project) {
                [PSCustomObject]@{
                    id   = $_.project.id
                    key  = $_.project.projectKey
                    name = $_.project.name
                }
            } else {
                $null
            }

            status = if ($_.status) {
                [PSCustomObject]@{
                    id   = $_.status.id
                    name = $_.status.name
                }
            } else {
                $null
            }

            priority = if ($_.priority) {
                [PSCustomObject]@{
                    id   = $_.priority.id
                    name = $_.priority.name
                }
            } else {
                $null
            }

            assignee = if ($_.assignee) {
                [PSCustomObject]@{
                    id   = $_.assignee.id
                    name = $_.assignee.name
                }
            } else {
                $null
            }

            startDate      = $_.startDate
            dueDate        = $_.dueDate
            estimatedHours = $_.estimatedHours

            created        = $_.created
            updated        = $_.updated
        }
    }
)


# ========================================
# Save
# ========================================

$OutputFile = Join-Path $OutputDir "assigned-issues.json"

$result `
    | ConvertTo-Json -Depth 20 `
    | Set-Content `
        -Path $OutputFile `
        -Encoding UTF8

Write-Host ""
Write-Host "Backlog data updated."
Write-Host "Issues: $($result.Count)"
Write-Host "Output: sources/backlog/assigned-issues.json"