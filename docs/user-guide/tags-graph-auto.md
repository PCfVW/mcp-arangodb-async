# Tags Auto Graph Workflow

This guide describes the optional tags graph intelligence workflow in this fork.

It is designed to stay compatible with general-purpose MCP usage:

- Core CRUD/AQL workflows remain unchanged.
- Tags graph logic is triggered only through explicit admin actions.
- You can dry-run everything before writing data.

## Overview

Two admin actions form a closed loop:

1. `sync_run` (structure update)
- reads `notes.tags`
- upserts `tags`
- rebuilds auto `tag_edges` using `AND/OR/NOT/XOR`

2. `optimize_run` (behavior optimization)
- reads `access_logs`
- computes behavior signal by note/tag co-access
- updates `tag_edges.weight`, `confidence`, and `enabled`

3. `quality_check` (health inspection)
- reports noise edges, unstable edges, and orphan tags
- does not mutate graph data

All actions are routed via `arango_admin`.

## Tool Entry

### Dry-run sync

```json
{
  "action": "sync_run",
  "dry_run": true
}
```

### Dry-run optimize

```json
{
  "action": "optimize_run",
  "days": 30,
  "dry_run": true
}
```

### Apply sync

```json
{
  "action": "sync_run",
  "dry_run": false
}
```

### Apply optimize

```json
{
  "action": "optimize_run",
  "days": 30,
  "dry_run": false
}
```

### Inspect quality

```json
{
  "action": "quality_check",
  "top_k": 10,
  "orphan_limit": 20
}
```

## Runtime Defaults

Defaults are centralized in `config/admin.json`.

### Sync defaults

- `min_cooccur_count`
- `and_threshold`
- `or_threshold`
- `min_tag_count_for_not`
- `max_not_tags`
- `xor_shared_min`
- `clear_previous_auto`

### Optimize defaults

- `days`
- `alpha`
- `half_life_days`
- `enable_on`
- `disable_below`

## Data Flow

`notes.tags -> tags -> tag_edges -> behavior logs -> tag_edges`

Operationally:

1. Normalize tags (lowercase, trim, remove `#` prefix).
2. Count per-tag and tag-pair co-occurrence.
3. Generate quaternary relations:
- `AND`: strong mutual co-occurrence
- `OR`: moderate mutual co-occurrence
- `NOT`: frequent tags that do not co-occur
- `XOR`: NOT pairs with shared neighbors
4. Persist one admin run log per action for observability.
5. Use recent `access_logs` to reweight/enable/disable edges over time.

## Recommended Daily Routine

1. Run `sync_run` in dry-run mode and inspect metrics.
2. Run `sync_run` in write mode.
3. Run `optimize_run` in dry-run mode and inspect candidate changes.
4. Run `optimize_run` in write mode.
5. Run `quality_check` and track trend metrics.

Suggested cadence:

- `sync_run`: once per day
- `optimize_run`: once per day (or every few hours for high traffic)

## Safety Notes

- Start with `dry_run: true` for both actions in new environments.
- Keep `clear_previous_auto: true` unless you intentionally preserve old auto edges.
- Tune `enable_on` and `disable_below` conservatively to avoid edge flapping.
