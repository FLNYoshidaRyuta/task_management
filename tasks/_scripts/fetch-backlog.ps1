param(
    [switch]$RefreshStatuses
)

$ErrorActionPreference = "Stop"

# ========================================
# Paths
# ========================================

$VaultDir = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$EnvFile = Join-Path $VaultDir ".env"
$OutputDir = Join-Path $VaultDir "sources\backlog"
$ConfigDir = Join-Path $VaultDir "tasks\_config"
$ProjectsConfigFile = Join-Path $ConfigDir "backlog-projects.json"
$StatusesConfigFile = Join-Path $ConfigDir "backlog-statuses.json"

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
        foreach ($value in @($Query[$key])) {
            $encodedValue = [Uri]::EscapeDataString([string]$value)
            $params += "$encodedKey=$encodedValue"
        }
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


function Read-JsonConfig {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path $Path)) {
        throw "Config not found: $Path"
    }

    $utf8 = New-Object System.Text.UTF8Encoding $false
    $raw = [System.IO.File]::ReadAllText($Path, $utf8)

    return ($raw | ConvertFrom-Json)
}


function Write-JsonConfig {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [Parameter(Mandatory = $true)]
        $Object
    )

    $parent = Split-Path -Parent $Path
    if (-not (Test-Path $parent)) {
        New-Item -ItemType Directory -Force $parent | Out-Null
    }

    $json = $Object | ConvertTo-Json -Depth 20
    $utf8 = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($Path, $json + "`n", $utf8)
}


function Get-DefaultStatusInclude {
    param(
        [Parameter(Mandatory = $true)]
        [string]$StatusName
    )

    if ($StatusName -eq "完了" -or $StatusName -eq "却下") {
        return $false
    }

    return $true
}


function Get-FetchFilterIds {
    param(
        [Parameter(Mandatory = $true)]
        $ProjectsConfig,

        [Parameter(Mandatory = $true)]
        $StatusesConfig
    )

    $projectIds = @(
        $ProjectsConfig.projects |
            Where-Object { $_.include -eq $true } |
            ForEach-Object { [int]$_.projectId }
    )

    if ($projectIds.Count -eq 0) {
        return @{
            ProjectIds = @()
            StatusIds  = @()
        }
    }

    $includedProjects = [System.Collections.Generic.HashSet[int]]::new()
    foreach ($projectId in $projectIds) {
        [void]$includedProjects.Add($projectId)
    }

    $statusIds = @(
        $StatusesConfig.statuses |
            Where-Object {
                $_.include -eq $true -and $includedProjects.Contains([int]$_.projectId)
            } |
            ForEach-Object { [int]$_.statusId } |
            Select-Object -Unique
    )

    return @{
        ProjectIds = $projectIds
        StatusIds  = $statusIds
    }
}


function Update-BacklogConfig {
    $existingProjects = $null
    $existingStatuses = $null

    if (Test-Path $ProjectsConfigFile) {
        $existingProjects = Read-JsonConfig -Path $ProjectsConfigFile
    }
    if (Test-Path $StatusesConfigFile) {
        $existingStatuses = Read-JsonConfig -Path $StatusesConfigFile
    }

    $projectIncludeById = @{}
    if ($existingProjects -and $existingProjects.projects) {
        foreach ($row in $existingProjects.projects) {
            $projectIncludeById[[int]$row.projectId] = [bool]$row.include
        }
    }

    $statusIncludeByKey = @{}
    if ($existingStatuses -and $existingStatuses.statuses) {
        foreach ($row in $existingStatuses.statuses) {
            $key = "{0}:{1}" -f [int]$row.projectId, [int]$row.statusId
            $statusIncludeByKey[$key] = [bool]$row.include
        }
    }

    Write-Host "Refreshing Backlog project and status config..."

    $apiProjects = @(Invoke-BacklogGet -Path "/api/v2/projects")

    $mergedProjects = @()
    foreach ($project in $apiProjects) {
        $projectId = [int]$project.id
        $include = $true
        if ($projectIncludeById.ContainsKey($projectId)) {
            $include = $projectIncludeById[$projectId]
        }

        $mergedProjects += [PSCustomObject]@{
            projectId   = $projectId
            projectKey  = $project.projectKey
            projectName = $project.name
            include     = $include
        }
    }

    $mergedProjects = @(
        $mergedProjects | Sort-Object projectKey
    )

    $mergedStatuses = @()
    foreach ($project in $mergedProjects) {
        if (-not $project.include) {
            continue
        }

        $apiStatuses = @(
            Invoke-BacklogGet -Path "/api/v2/projects/$($project.projectId)/statuses"
        )

        foreach ($status in $apiStatuses) {
            $statusId = [int]$status.id
            $key = "{0}:{1}" -f $project.projectId, $statusId
            $include = Get-DefaultStatusInclude -StatusName $status.name
            if ($statusIncludeByKey.ContainsKey($key)) {
                $include = $statusIncludeByKey[$key]
            }

            $mergedStatuses += [PSCustomObject]@{
                projectId   = $project.projectId
                projectKey  = $project.projectKey
                projectName = $project.projectName
                statusId    = $statusId
                statusName  = $status.name
                include     = $include
            }
        }
    }

    Write-JsonConfig -Path $ProjectsConfigFile -Object @{ projects = $mergedProjects }
    Write-JsonConfig -Path $StatusesConfigFile -Object @{ statuses = $mergedStatuses }

    Write-Host ""
    Write-Host "Backlog config updated."
    Write-Host "Projects: $($mergedProjects.Count)"
    Write-Host "Statuses: $($mergedStatuses.Count)"
    Write-Host "Output: tasks/_config/backlog-projects.json"
    Write-Host "Output: tasks/_config/backlog-statuses.json"
}


if ($RefreshStatuses) {
    Update-BacklogConfig
    return
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

try {
    $projectsConfig = Read-JsonConfig -Path $ProjectsConfigFile
    $statusesConfig = Read-JsonConfig -Path $StatusesConfigFile
    $filter = Get-FetchFilterIds -ProjectsConfig $projectsConfig -StatusesConfig $statusesConfig
}
catch {
    Write-Host ""
    Write-Host "Backlog fetch skipped: $($_.Exception.Message)"
    Write-Host "Existing cache was not modified."
    return
}

if ($filter.ProjectIds.Count -eq 0 -or $filter.StatusIds.Count -eq 0) {
    Write-Host ""
    Write-Host "Backlog fetch skipped: no included projectId or statusId in config."
    Write-Host "Existing cache was not modified."
    return
}

Write-Host "Fetching assigned issues..."
Write-Host ("Included projects: {0}" -f $filter.ProjectIds.Count)
Write-Host ("Included statuses: {0}" -f $filter.StatusIds.Count)

$allIssues = @()
$offset = 0
$count = 100

while ($true) {

    $issues = @(
        Invoke-BacklogGet `
            -Path "/api/v2/issues" `
            -Query @{
                "assigneeId[]" = $me.id
                "projectId[]"  = $filter.ProjectIds
                "statusId[]"   = $filter.StatusIds
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
