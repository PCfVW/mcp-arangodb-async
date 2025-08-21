param(
    [string]$RootPassword = "changeme",
    [string]$DbName = "mcp_arangodb_test",
    [string]$User = "mcp_arangodb_user",
    [string]$Password = "mcp_arangodb_password",
    [switch]$Seed
)

Write-Host "Configuring ArangoDB (container: mcp_arangodb_test) ..."

# Wait until container is healthy or at least Up
$maxTries = 30
for ($i = 0; $i -lt $maxTries; $i++) {
    $status = (docker ps --filter name=mcp_arangodb_test --format "{{.Status}}")
    if ($status -match "(healthy|Up)") { break }
    Start-Sleep -Seconds 2
}

if ($i -ge $maxTries) {
    Write-Error "ArangoDB container not healthy. Check 'docker compose logs arangodb'"
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

docker cp $setupJs mcp_arangodb_test:/tmp/setup-db.js | Out-Null
docker compose exec arangodb arangosh --server.username root --server.password "$RootPassword" --javascript.execute /tmp/setup-db.js

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to create database/user. Inspect with: docker compose logs arangodb"
    exit 1
}

if ($Seed) {
    @"
const db = require('@arangodb').db;
db._useDatabase('$DbName');
if (!db._collection('users')) db._createDocumentCollection('users');
db.users.insert([{ name: 'Alice' }, { name: 'Bob' }]);
"@ | Set-Content -NoNewline -Encoding UTF8 $seedJs

    docker cp $seedJs mcp_arangodb_test:/tmp/seed.js | Out-Null
    docker compose exec arangodb arangosh --server.username root --server.password "$RootPassword" --javascript.execute /tmp/seed.js

    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Seeding failed; continue without sample data."
    }
}

Write-Host "Done. Database '$DbName' and user '$User' ready."
