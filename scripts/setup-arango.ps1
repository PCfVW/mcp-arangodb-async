<#
.SYNOPSIS
    [DEPRECATED] ArangoDB setup script - Use Admin CLI instead

.DESCRIPTION
    This PowerShell script is deprecated and will be removed in a future release.
    Please use the cross-platform Admin CLI instead:
    
    maa db add <name> --url <url> --database <db> --username <user> --password-env <env>
    maa user add <username> --arango-password-env <env>
    maa user grant <username> <database> --permission rw

.NOTES
    This script still works but is no longer recommended.
    Migration guide: https://github.com/PCfVW/mcp-arango-async/blob/master/docs/getting-started/powershell-migration.md
#>

param(
    [string]$RootPassword = "changeme",
    [string]$DbName = "mcp_arangodb_test",
    [string]$User = "mcp_arangodb_user",
    [string]$Password = "mcp_arangodb_password",
    [string]$ProjectName = "mcp_arangodb_async",
    [string]$ServiceName = "arangodb",
    [switch]$Seed
)

Write-Host "Configuring ArangoDB (service: $ServiceName) ..."

# Get the container name for the service using docker compose ps
$containerName = docker compose -p $ProjectName ps $ServiceName --format "{{.Name}}" 2>$null
if (-not $containerName) {
    Write-Error "Service '$ServiceName' not found or not running. Check 'docker compose ps'"
    exit 1
}

# Wait until container is healthy or at least Up
$maxTries = 30
for ($i = 0; $i -lt $maxTries; $i++) {
    $status = (docker ps --filter name=$containerName --format "{{.Status}}")
    if ($status -match "(healthy|Up)") { break }
    Start-Sleep -Seconds 2
}

if ($i -ge $maxTries) {
    Write-Error "ArangoDB container not healthy. Check 'docker compose logs $ServiceName'"
    exit 1
}

# Prepare temp files for JS to avoid quoting issues
$tmpDir = Join-Path $env:TEMP "arangodb-setup"
if (-not (Test-Path $tmpDir)) { New-Item -Type Directory -Path $tmpDir | Out-Null }
$setupJs = Join-Path $tmpDir "setup-db.js"
$seedJs = Join-Path $tmpDir "seed.js"

@"
const users = require('@arangodb/users');
const db = require('@arangodb').db;
if (!db._databases().includes('$DbName')) db._createDatabase('$DbName');
users.save('$User', '$Password', true);
users.grantDatabase('$User', '$DbName', 'rw');
"@ | Set-Content -NoNewline -Encoding UTF8 $setupJs

docker cp $setupJs ${containerName}:/tmp/setup-db.js | Out-Null
docker compose -p $ProjectName exec $ServiceName arangosh --server.username root --server.password "$RootPassword" --javascript.execute /tmp/setup-db.js

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to create database/user. Inspect with: docker compose logs $ServiceName"
    exit 1
}

if ($Seed) {
    @"
const db = require('@arangodb').db;
db._useDatabase('$DbName');
if (!db._collection('users')) db._createDocumentCollection('users');
db.users.insert([{ name: 'Alice' }, { name: 'Bob' }]);
"@ | Set-Content -NoNewline -Encoding UTF8 $seedJs

    docker cp $seedJs ${containerName}:/tmp/seed.js | Out-Null
    docker compose -p $ProjectName exec $ServiceName arangosh --server.username root --server.password "$RootPassword" --javascript.execute /tmp/seed.js

    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Seeding failed; continue without sample data."
    }
}

Write-Host "Done. Database '$DbName' and user '$User' ready."
