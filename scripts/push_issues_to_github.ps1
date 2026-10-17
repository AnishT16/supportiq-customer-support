<#
.SYNOPSIS
    Pushes all structured issue files in .github/issues/ to GitHub repository using gh CLI.
#>

$ErrorActionPreference = "Stop"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  SupportIQ - GitHub Issues Synchronization Tool  " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 1. Check gh CLI
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Error "GitHub CLI ('gh') is not installed."
    exit 1
}

# 2. Check auth
Write-Host "`n[1/4] Checking GitHub CLI authentication..." -ForegroundColor Yellow
$authCheck = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n[!] You are not currently logged into GitHub CLI. Please run 'gh auth login' first." -ForegroundColor Red
    exit 1
}
Write-Host "Authentication confirmed as AnishT16." -ForegroundColor Green

# 3. Locate issue files
$issueDir = Join-Path $PSScriptRoot "..\.github\issues"
$files = Get-ChildItem -Path $issueDir -Filter "ISSUE-*.md" | Sort-Object Name

if ($files.Count -eq 0) {
    Write-Error "No issue markdown files found in $issueDir"
    exit 1
}
Write-Host "`n[2/4] Found $($files.Count) issue files." -ForegroundColor Yellow

# 4. Pre-create all custom labels in GitHub repository
Write-Host "`n[3/4] Ensuring all project labels exist on GitHub..." -ForegroundColor Yellow
$labelPalette = @{
    "backend" = "1d76db";
    "frontend" = "0e8a16";
    "dev-a" = "5319e7";
    "dev-b" = "b60205";
    "ai-engine" = "d93f0b";
    "database" = "0052cc";
    "api" = "fbca04";
    "ui/ux" = "e99695";
    "auth" = "c2e0c6";
    "security" = "ee0701";
    "support" = "006b75";
    "rag" = "bfdadc";
    "llm" = "bfd4f2";
    "tools" = "d4c5f9";
    "predictions" = "fef2c0";
    "machine-learning" = "fad8c7";
    "simulation" = "f9d0c4";
    "policies" = "c5def5";
    "analytics" = "d4c5f9";
    "recharts" = "e11d48";
    "audit" = "6b7280";
    "devops" = "0366d6";
    "docker" = "2496ed";
    "nginx" = "009639";
    "qa" = "22c55e";
    "testing" = "10b981";
    "integration" = "8b5cf6";
}

# Extract all labels from files
$allLabels = [System.Collections.Generic.HashSet[string]]::new()
foreach ($f in $files) {
    $content = Get-Content -Path $f.FullName -Raw
    if ($content -match 'labels:\s*\[(.*?)\]') {
        $matches[1] -split ',' | ForEach-Object {
            $cleaned = $_.Trim().Trim('"').Trim("'")
            if ($cleaned) { [void]$allLabels.Add($cleaned) }
        }
    }
}

foreach ($lbl in $allLabels) {
    $color = if ($labelPalette.ContainsKey($lbl)) { $labelPalette[$lbl] } else { "6b7280" }
    gh label create $lbl --color $color --force 2>$null | Out-Null
}
Write-Host "Labels verified on remote repository." -ForegroundColor Green

# 5. Create issues using --body-file
Write-Host "`n[4/4] Creating remote GitHub issues..." -ForegroundColor Yellow
$createdCount = 0
$tempBodyFile = [System.IO.Path]::GetTempFileName()

try {
    foreach ($file in $files) {
        $raw = Get-Content -Path $file.FullName -Raw
        $title = ""
        $labels = @()
        $body = $raw

        if ($raw -match '(?s)^---\r?\n(.*?)\r?\n---\r?\n(.*)$') {
            $frontmatter = $matches[1]
            $body = $matches[2].Trim()

            foreach ($line in ($frontmatter -split "\r?\n")) {
                if ($line -match '^title:\s*"?(.*?)"?$') {
                    $title = $matches[1]
                }
                if ($line -match '^labels:\s*\[(.*?)\]') {
                    $labels = ($matches[1] -split ',') | ForEach-Object { $_.Trim().Trim('"').Trim("'") }
                }
            }
        }

        if (-not $title) { $title = $file.BaseName }

        # Write clean body to temp file with UTF8 encoding
        [System.IO.File]::WriteAllText($tempBodyFile, $body, [System.Text.Encoding]::UTF8)

        $labelArg = ($labels -join ",")
        Write-Host "Creating $($file.Name): $title..." -NoNewline

        if ($labelArg) {
            $output = gh issue create --title $title --body-file $tempBodyFile --label $labelArg 2>&1
        } else {
            $output = gh issue create --title $title --body-file $tempBodyFile 2>&1
        }

        if ($LASTEXITCODE -eq 0) {
            Write-Host " [OK] -> $output" -ForegroundColor Green
            $createdCount++
        } else {
            Write-Host " [ERR]" -ForegroundColor Red
            Write-Warning "Error output: $output"
        }

        Start-Sleep -Milliseconds 600
    }
}
finally {
    if (Test-Path $tempBodyFile) {
        Remove-Item $tempBodyFile -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "`n==================================================" -ForegroundColor Cyan
Write-Host "Completed! Successfully published $createdCount of $($files.Count) issues to GitHub." -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan
