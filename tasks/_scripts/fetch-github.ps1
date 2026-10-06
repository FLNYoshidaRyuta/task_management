$ErrorActionPreference = "Stop"

$VaultDir = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$GithubDir = Join-Path $VaultDir "sources\github"

New-Item -ItemType Directory -Force $GithubDir | Out-Null

Write-Host "Fetching assigned issues..."

gh search issues `
  --assignee=@me `
  --state=open `
  --limit=100 `
  --json number,title,body,state,repository,labels,assignees,author,createdAt,updatedAt,url `
  | Set-Content `
      -Encoding UTF8 `
      -Path (Join-Path $GithubDir "assigned-issues.json")

if ($LASTEXITCODE -ne 0) {
    throw "Failed to fetch assigned issues"
}

Write-Host "Fetching my PRs..."

gh search prs `
  --author=@me `
  --state=open `
  --limit=100 `
  --json number,title,body,state,repository,labels,author,isDraft,createdAt,updatedAt,url `
  | Set-Content `
      -Encoding UTF8 `
      -Path (Join-Path $GithubDir "my-prs.json")

if ($LASTEXITCODE -ne 0) {
    throw "Failed to fetch my PRs"
}

Write-Host "Fetching review requests..."

gh search prs `
  --review-requested=@me `
  --state=open `
  --limit=100 `
  --json number,title,body,state,repository,labels,author,isDraft,createdAt,updatedAt,url `
  | Set-Content `
      -Encoding UTF8 `
      -Path (Join-Path $GithubDir "review-requests.json")

if ($LASTEXITCODE -ne 0) {
    throw "Failed to fetch review requests"
}

Write-Host ""
Write-Host "GitHub data updated."