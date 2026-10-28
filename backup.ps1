# Back up this skill to its private GitHub repo: commit every change, then push.
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
git add -A
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
    git commit -q -m "Backup $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
    if ($LASTEXITCODE -ne 0) { throw 'git commit failed' }
}
git push -q
if ($LASTEXITCODE -ne 0) { throw 'git push failed - run "gh auth login --web" and try again' }
Write-Host "Backed up: $(git log -1 --format='%h %s')"
