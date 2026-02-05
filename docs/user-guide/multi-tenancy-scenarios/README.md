# Multi-Tenancy Scenarios

Progressive tutorials for setting up multi-tenancy with mcp-arangodb-async.

---

**Concepts covered:**
- Multi-database configuration patterns
- Database resolution and switching
- Access control and security models
- Cross-database operations

**Skills you will practice:**
- Configuring multiple databases using Admin CLI
- Setting up ArangoDB instances with Docker
- Managing user permissions and access control
- Testing multi-tenancy setups

---

## Scenario Overview

Each scenario builds incrementally on the previous one, demonstrating different multi-tenancy patterns:

### [Scenario 1: Single Instance, Single Database](01-single-instance-single-database.md)
**Setup:** 1 user + 1 MCP server + 1 ArangoDB instance + 1 database

Learn the basics of database configuration and MCP connection.

### [Scenario 2: Single Instance, Multiple Databases](02-single-instance-multiple-databases.md)
**Setup:** 1 user + 1 MCP server + 1 ArangoDB instance + 2 databases

Add a second database and practice database switching.

### [Scenario 3: Multiple Instances, Multiple Databases](03-multiple-instances-multiple-databases.md)
**Setup:** 1 user + 1 MCP server + 2 ArangoDB instances + 3 databases

Scale to multiple ArangoDB instances for complete isolation.

---

## Prerequisites

- Docker and Docker Compose installed
- Python 3.10+ with mcp-arangodb-async installed
- Basic familiarity with command line operations

## Getting Started

Start with [Scenario 1](01-single-instance-single-database.md) and work through each scenario sequentially.

> **Next:** [Scenario 1: Single Instance, Single Database](01-single-instance-single-database.md)