# PowerShell to Admin CLI Migration Guide

**Audience:** Developers and System Administrators migrating from PowerShell script  
**Prerequisites:** Python 3.10+, mcp-arangodb-async installed  
**Estimated Time:** 10 minutes

---

## Overview

The `scripts/setup-arango.ps1` PowerShell script has been replaced by the cross-platform Admin CLI. This guide helps you migrate from the monolithic PowerShell script to the granular, safer CLI commands.

### Why Migrate?

**Cross-Platform Support:**
- PowerShell script: Windows only
- Admin CLI: Windows, macOS, Linux

**Granular Control:**
- PowerShell script: Single monolithic operation (create database + user + grant)
- Admin CLI: Separate commands for each operation (add, remove, list, grant, revoke)

**Safety Features:**
- PowerShell script: No preview, no confirmation
- Admin CLI: Interactive confirmations, `--dry-run` mode, `--yes` flag for automation

**Environment Flexibility:**
- PowerShell script: Parameters only
- Admin CLI: Environment variables, `.env` files, parameter overrides

---

## Quick Reference Table

| PowerShell Operation | Admin CLI Equivalent |
|---------------------|---------------------|
| `setup-arango.ps1 -DbName mydb` | `maa db add mydb` |
| `setup-arango.ps1 -User myuser` | `maa user add myuser --arango-password-env USER_PASSWORD` |
| `setup-arango.ps1 -DbName mydb -User myuser` | `maa db add mydb --with-user myuser --arango-password-env USER_PASSWORD` |
| Grant permission (implicit) | `maa user grant myuser mydb --permission rw` |
| List databases (N/A) | `maa db list` |
| List users (N/A) | `maa user list` |
| Test connection (N/A) | `maa db test <key>` |
| Remove database (N/A) | `maa db remove mydb` |
| Remove user (N/A) | `maa user remove myuser` |
| Revoke permission (N/A) | `maa user revoke myuser mydb` |

---

## Key Differences

### 1. Granular Operations

**PowerShell (Monolithic):**
```powershell
# Creates database + user + grants permission in one script
./scripts/setup-arango.ps1 -DbName myapp_prod -User myapp_user -Password "secret"
```

**Admin CLI (Granular):**
```powershell
# Separate commands for each operation
maa db add myapp_prod
maa user add myapp_user --arango-password-env MYAPP_USER_PASSWORD
maa user grant myapp_user myapp_prod --permission rw

# OR atomic operation (equivalent to PowerShell script)
maa db add myapp_prod --with-user myapp_user --arango-password-env MYAPP_USER_PASSWORD
```

### 2. Safety Features

**PowerShell:**
- No preview mode
- No confirmation prompts
- Errors may leave partial state

**Admin CLI:**

Preview changes without executing:
```powershell
maa db add myapp_prod --dry-run
```

Interactive confirmation for destructive operations
```powershell
maa db remove myapp_staging
The following actions will be performed:
  [REMOVE] Database 'myapp_staging'
  [REVOKE] Permission: root → myapp_staging (was: {'permission': 'undefined', 'collections': {'_analyzers': 'undefined', 'methodology_mappings': 'undefined', '_apps': 'undefined', '_pregel_queries': 'undefined', '_appbundles': 'undefined', '_aqlfunctions': 'undefined', '_jobs': 'undefined', '_graphs': 'undefined', '_fishbowl': 'undefined', 'papers': 'undefined', 'extraction_log': 'undefined', 'computational_constructs': 'undefined', '_frontend': 'undefined', 'biological_concepts': 'undefined', '_queues': 'undefined', '*': 'undefined'}})
Are you sure you want to proceed? [y/N]:
```

Skip confirmation for automation:
```
maa db remove myapp_staging --yes
```

### 3. Environment Variable Flexibility

**PowerShell:**
```powershell
# Parameters only
./scripts/setup-arango.ps1 -RootPassword "admin123" -Password "user456"
```

**Admin CLI:**
```powershell
# Environment variables (recommended)
$env:ARANGO_ROOT_PASSWORD = "admin123"
$env:MYAPP_USER_PASSWORD = "user456"
maa db add myapp_prod --with-user myapp_user --arango-password-env MYAPP_USER_PASSWORD

# OR use .env file
maa db add myapp_prod --env-file .env.production --with-user myapp_user --arango-password-env MYAPP_USER_PASSWORD
```

### 4. New Capabilities

The Admin CLI provides operations not available in the PowerShell script:

- **List operations:** `maa db list`, `maa user list`
- **Test connections:** `maa db test production`
- **Revoke permissions:** `maa user revoke myuser mydb`
- **Remove users:** `maa user remove myuser`
- **Remove databases:** `maa db remove mydb`
- **Self-service:** `maa user databases`, `maa user password`
- **Configuration management:** `maa db config add/remove/list`

---

## Migration Steps

### Step 1: Identify Current PowerShell Usage

Review your current PowerShell script invocations:

```powershell
# Example current usage
./scripts/setup-arango.ps1 -DbName myapp_prod -User myapp_user -Password "secret123"
```

### Step 2: Set Up Environment Variables

Replace password parameters with environment variables:

```powershell
# Set passwords as environment variables
$env:ARANGO_ROOT_PASSWORD = "admin-password"
$env:MYAPP_USER_PASSWORD = "user-password"
```

**Tip:** Use `.env` files for multiple environments:

```bash
# .env.production
ARANGO_ROOT_PASSWORD=prod-admin-password
MYAPP_USER_PASSWORD=prod-user-password
```

### Step 3: Map to CLI Commands

**Option A: Atomic Operation (closest to PowerShell script)**

```powershell
maa db add myapp_prod --with-user myapp_user --arango-password-env MYAPP_USER_PASSWORD
```

**Option B: Granular Operations (more control)**

```powershell
maa db add myapp_prod
maa user add myapp_user --arango-password-env MYAPP_USER_PASSWORD
maa user grant myapp_user myapp_prod --permission rw
```

### Step 4: Test with Dry-Run

Preview changes before executing:

```powershell
maa db add myapp_prod --with-user myapp_user --arango-password-env MYAPP_USER_PASSWORD --dry-run
```

### Step 5: Execute Migration

Run the actual commands:

```powershell
maa db add myapp_prod --with-user myapp_user --arango-password-env MYAPP_USER_PASSWORD
```

### Step 6: Verify

Test the connection:

```powershell
# Add to YAML config first
maa db config add production `
  --url http://localhost:8529 `
  --database myapp_prod `
  --username myapp_user `
  --password-env MYAPP_USER_PASSWORD

# Test connection
maa db test production
```

---

## Examples

### Example 1: Basic Database Setup

**Before (PowerShell):**
```powershell
./scripts/setup-arango.ps1 -DbName myapp_prod -User myapp_user -Password "secret123"
```

**After (Admin CLI):**
```powershell
# Set password
$env:MYAPP_USER_PASSWORD = "secret123"

# Atomic operation
maa db add myapp_prod --with-user myapp_user --arango-password-env MYAPP_USER_PASSWORD
```

### Example 2: Multiple Environments

**Before (PowerShell):**
```powershell
./scripts/setup-arango.ps1 -DbName myapp_dev -User dev_user -Password "dev123"
./scripts/setup-arango.ps1 -DbName myapp_staging -User staging_user -Password "staging456"
./scripts/setup-arango.ps1 -DbName myapp_prod -User prod_user -Password "prod789"
```

**After (Admin CLI):**
```powershell
# Set passwords
$env:DEV_USER_PASSWORD = "dev123"
$env:STAGING_USER_PASSWORD = "staging456"
$env:PROD_USER_PASSWORD = "prod789"

# Create databases with users
maa db add myapp_dev --with-user dev_user --arango-password-env DEV_USER_PASSWORD
maa db add myapp_staging --with-user staging_user --arango-password-env STAGING_USER_PASSWORD
maa db add myapp_prod --with-user prod_user --arango-password-env PROD_USER_PASSWORD
```

### Example 3: Using .env Files

**Before (PowerShell):**
```powershell
./scripts/setup-arango.ps1 -RootPassword "admin123" -DbName myapp_prod -User myapp_user -Password "user456"
```

**After (Admin CLI):**

Create `.env.production`:
```bash
ARANGO_ROOT_PASSWORD=admin123
MYAPP_USER_PASSWORD=user456
```

Run command:
```powershell
maa db add myapp_prod --env-file .env.production --with-user myapp_user --arango-password-env MYAPP_USER_PASSWORD
```

---

## Related Documentation

- [CLI Reference](../user-guide/cli-reference.md) - Complete documentation of all CLI commands
- [Multi-Tenancy Guide](../user-guide/multi-tenancy-guide.md) - Advanced multi-database scenarios
- [Quickstart Guide](quickstart.md) - Getting started with mcp-arangodb-async
