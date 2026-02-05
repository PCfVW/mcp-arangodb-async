"""Operations for arango_admin_optimize.

Analyzes access_logs and dynamically adjusts tag_edges weights/enabled state.
"""

from __future__ import annotations

import itertools
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from arango.database import StandardDatabase
from ..utility.runtime_defaults import get_admin_defaults
from ..utility.access_log import log_admin_run

_TAG_PREFIX_RE = re.compile(r"^[#]+")
AUTO_EDGE_SOURCES = ["auto", "auto-sync"]
ACCESS_WEIGHTS = {
    1: 1.0,  # query hit
    2: 2.0,  # update operation
    3: 1.5,  # template execution
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_tag(raw: Any) -> str:
    if not isinstance(raw, str):
        return ""
    value = _TAG_PREFIX_RE.sub("", raw.strip()).strip().lower()
    return value


def _age_days_from_edge(edge: Dict[str, Any]) -> float:
    raw = edge.get("updated_at")
    if isinstance(raw, str):
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            return max(0.0, (datetime.now(timezone.utc) - dt).total_seconds() / 86400.0)
        except ValueError:
            pass

    created_ms = edge.get("created_at")
    if isinstance(created_ms, (int, float)):
        created_dt = datetime.fromtimestamp(created_ms / 1000.0, tz=timezone.utc)
        return max(0.0, (datetime.now(timezone.utc) - created_dt).total_seconds() / 86400.0)

    return 0.0


def _fetch_recent_log_rows(db: StandardDatabase, days: int) -> List[Dict[str, Any]]:
    query = """
    FOR l IN access_logs
      FILTER DATE_TIMESTAMP(l.timestamp) >= DATE_SUBTRACT(DATE_NOW(), @days, 'days')
      FILTER IS_STRING(l.target_ref) AND STARTS_WITH(l.target_ref, 'notes/')
      COLLECT note_id = l.target_ref, access_type = l.access_type WITH COUNT INTO cnt
      RETURN { note_id: note_id, access_type: access_type, count: cnt }
    """
    return list(db.aql.execute(query, bind_vars={"days": days}))


def _fetch_note_tags(db: StandardDatabase, note_ids: List[str]) -> List[Dict[str, Any]]:
    if not note_ids:
        return []
    query = """
    FOR n IN notes
      FILTER n._id IN @ids
      RETURN { id: n._id, tags: (IS_ARRAY(n.tags) ? n.tags : []) }
    """
    return list(db.aql.execute(query, bind_vars={"ids": note_ids}))


def _fetch_tag_maps(db: StandardDatabase) -> Tuple[Dict[str, str], Dict[str, str]]:
    query = """
    FOR t IN tags
      LET clean = LOWER(TRIM(REGEX_REPLACE(TO_STRING(t.label), '^[#]+', '')))
      FILTER LENGTH(clean) > 0
      RETURN { clean: clean, key: t._key }
    """
    label_to_key: Dict[str, str] = {}
    key_to_label: Dict[str, str] = {}
    for row in db.aql.execute(query):
        label_to_key[row["clean"]] = row["key"]
        key_to_label[row["key"]] = row["clean"]
    return label_to_key, key_to_label


def _fetch_auto_edges(db: StandardDatabase) -> List[Dict[str, Any]]:
    query = """
    FOR e IN tag_edges
      FILTER e.source IN @sources
      RETURN e
    """
    return list(db.aql.execute(query, bind_vars={"sources": AUTO_EDGE_SOURCES}))


def _fetch_edges_for_quality_check(
    db: StandardDatabase, include_all_sources: bool
) -> List[Dict[str, Any]]:
    if include_all_sources:
        query = """
        FOR e IN tag_edges
          RETURN e
        """
        return list(db.aql.execute(query))

    return _fetch_auto_edges(db)


def _fetch_tags(db: StandardDatabase) -> List[Dict[str, Any]]:
    query = """
    FOR t IN tags
      RETURN {
        _key: t._key,
        label: t.label,
        count: TO_NUMBER(t.count || 0)
      }
    """
    return list(db.aql.execute(query))


def _bulk_update_edges(db: StandardDatabase, docs: List[Dict[str, Any]]) -> int:
    if not docs:
        return 0

    query = """
    FOR doc IN @docs
      UPDATE doc._key WITH doc IN tag_edges
    """

    total = 0
    for i in range(0, len(docs), 1000):
        chunk = docs[i:i + 1000]
        cursor = db.aql.execute(query, bind_vars={"docs": chunk})
        list(cursor)
        total += len(chunk)
    return total


def optimize_edges_from_logs(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Optimize tag_edges using access_logs behavior signals."""
    defaults = get_admin_defaults("optimize")
    dry_run = bool(args.get("dry_run", defaults.get("dry_run", False)))
    days = int(args.get("days", defaults.get("days", 30)))
    alpha = float(args.get("alpha", defaults.get("alpha", 0.35)))
    half_life_days = float(args.get("half_life_days", defaults.get("half_life_days", 14.0)))
    enable_on = int(args.get("enable_on", defaults.get("enable_on", 18)))
    disable_below = int(args.get("disable_below", defaults.get("disable_below", 12)))

    logs = _fetch_recent_log_rows(db, days)

    note_scores: Dict[str, float] = defaultdict(float)
    for row in logs:
        access_type = int(row.get("access_type") or 1)
        count = int(row.get("count") or 0)
        note_scores[row["note_id"]] += ACCESS_WEIGHTS.get(access_type, 1.0) * count

    note_ids = list(note_scores.keys())
    note_tag_rows = _fetch_note_tags(db, note_ids)
    label_to_key, key_to_label = _fetch_tag_maps(db)

    pair_behavior: Counter[Tuple[str, str]] = Counter()
    for row in note_tag_rows:
        score = note_scores.get(row["id"], 0.0)
        if score <= 0:
            continue

        labels = sorted({_normalize_tag(t) for t in row.get("tags", []) if _normalize_tag(t)})
        keys = sorted({label_to_key[lbl] for lbl in labels if lbl in label_to_key})
        if len(keys) < 2:
            continue

        for a, b in itertools.combinations(keys, 2):
            pair_behavior[(a, b)] += score

    max_signal = max(pair_behavior.values()) if pair_behavior else 0.0

    edges = _fetch_auto_edges(db)
    updates: List[Dict[str, Any]] = []
    enabled_changes = 0

    for edge in edges:
        from_key = edge.get("_from", "").split("/", 1)[-1]
        to_key = edge.get("_to", "").split("/", 1)[-1]
        left, right = sorted((from_key, to_key))

        raw_signal = float(pair_behavior.get((left, right), 0.0))
        normalized_signal = (raw_signal / max_signal) if max_signal > 0 else 0.0

        age_days = _age_days_from_edge(edge)
        decay = 0.5 ** (age_days / half_life_days)
        behavior_signal = normalized_signal * decay

        old_weight = float(edge.get("weight", 0.0))
        old_conf = float(edge.get("confidence", 0.5))
        op = edge.get("op", "OR")

        if op == "NOT":
            target = max(1.0, 16.0 - (behavior_signal * 24.0))
            new_weight = ((1.0 - alpha) * old_weight) + (alpha * target)
            new_conf = ((1.0 - alpha) * old_conf) + (alpha * (1.0 - behavior_signal))
            new_enabled = new_weight >= disable_below and behavior_signal < 0.35
        else:
            target = 10.0 + (behavior_signal * 40.0)
            new_weight = ((1.0 - alpha) * old_weight) + (alpha * target)
            new_conf = ((1.0 - alpha) * old_conf) + (alpha * behavior_signal)
            if new_weight >= enable_on:
                new_enabled = True
            elif new_weight < disable_below:
                new_enabled = False
            else:
                new_enabled = bool(edge.get("enabled", True))

        new_weight_i = int(max(1, min(64, round(new_weight))))
        new_conf_f = float(max(0.0, min(1.0, round(new_conf, 4))))

        if bool(edge.get("enabled", True)) != new_enabled:
            enabled_changes += 1

        updates.append(
            {
                "_key": edge["_key"],
                "weight": new_weight_i,
                "confidence": new_conf_f,
                "behavior_score": round(behavior_signal, 6),
                "enabled": new_enabled,
                "updated_at": _now_iso(),
            }
        )

    written = 0
    if not dry_run:
        written = _bulk_update_edges(db, updates)

    top_pairs = [
        {
            "from": key_to_label.get(a, a),
            "to": key_to_label.get(b, b),
            "score": round(float(score), 4),
        }
        for (a, b), score in pair_behavior.most_common(10)
    ]

    result = {
        "status": "ok",
        "dry_run": dry_run,
        "days": days,
        "logs_aggregated": len(logs),
        "notes_scored": len(note_scores),
        "pairs_with_signal": len(pair_behavior),
        "edges_considered": len(edges),
        "edges_updated": written,
        "enabled_changes": enabled_changes,
        "top_behavior_pairs": top_pairs,
        "params": {
            "alpha": alpha,
            "half_life_days": half_life_days,
            "enable_on": enable_on,
            "disable_below": disable_below,
        },
    }

    # Persist one admin run log for observability and behavior analysis.
    log_admin_run(
        db,
        action="optimize_run",
        dry_run=dry_run,
        status=result["status"],
        metrics={
            "logs_aggregated": result["logs_aggregated"],
            "pairs_with_signal": result["pairs_with_signal"],
            "edges_considered": result["edges_considered"],
            "edges_updated": result["edges_updated"],
            "enabled_changes": result["enabled_changes"],
        },
        args=result["params"],
    )
    return result


def quality_check_edges(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Inspect tag_edges quality and report graph health metrics."""
    defaults = get_admin_defaults("optimize")
    include_all_sources = bool(args.get("include_all_sources", False))
    top_k = int(args.get("top_k", 10))
    orphan_limit = int(args.get("orphan_limit", 20))
    min_confidence = float(args.get("min_confidence", 0.35))
    low_weight_threshold = int(
        args.get("low_weight_threshold", defaults.get("disable_below", 12))
    )
    enable_on = int(args.get("enable_on", defaults.get("enable_on", 18)))
    disable_below = int(args.get("disable_below", defaults.get("disable_below", 12)))

    edges = _fetch_edges_for_quality_check(db, include_all_sources=include_all_sources)
    tags = _fetch_tags(db)

    if not edges:
        result = {
            "status": "ok",
            "summary": {
                "edges_total": 0,
                "edges_enabled": 0,
                "edges_disabled": 0,
                "enabled_ratio": 0.0,
                "disabled_ratio": 0.0,
                "noise_edges": 0,
                "noise_rate": 0.0,
                "unstable_edges": 0,
                "orphan_tag_count": len(tags),
            },
            "thresholds": {
                "low_weight_threshold": low_weight_threshold,
                "min_confidence": min_confidence,
                "enable_on": enable_on,
                "disable_below": disable_below,
            },
            "top_noise_edges": [],
            "top_unstable_edges": [],
            "orphan_tags": sorted(
                [{"key": t["_key"], "label": t.get("label"), "count": int(t.get("count", 0))} for t in tags],
                key=lambda x: x["count"],
                reverse=True,
            )[:orphan_limit],
            "params": {
                "include_all_sources": include_all_sources,
                "top_k": top_k,
                "orphan_limit": orphan_limit,
            },
        }
        log_admin_run(
            db,
            action="quality_check",
            dry_run=True,
            status=result["status"],
            metrics={
                "edges_total": 0,
                "noise_edges": 0,
                "unstable_edges": 0,
                "orphan_tag_count": len(tags),
            },
            args=result["params"],
        )
        return result

    edge_total = len(edges)
    enabled_edges = [e for e in edges if bool(e.get("enabled", True))]
    disabled_edges = [e for e in edges if not bool(e.get("enabled", True))]

    noise_edges: List[Dict[str, Any]] = []
    unstable_edges: List[Dict[str, Any]] = []
    referenced_enabled_keys = set()

    for edge in edges:
        from_key = edge.get("_from", "").split("/", 1)[-1]
        to_key = edge.get("_to", "").split("/", 1)[-1]
        if bool(edge.get("enabled", True)):
            if from_key:
                referenced_enabled_keys.add(from_key)
            if to_key:
                referenced_enabled_keys.add(to_key)

        weight = float(edge.get("weight", 0.0))
        confidence = float(edge.get("confidence", 0.5))
        behavior_score = float(edge.get("behavior_score", 0.0))
        enabled = bool(edge.get("enabled", True))

        is_noise = enabled and (
            weight < low_weight_threshold or confidence < min_confidence
        )
        if is_noise:
            noise_edges.append(
                {
                    "key": edge.get("_key"),
                    "from": edge.get("_from"),
                    "to": edge.get("_to"),
                    "op": edge.get("op"),
                    "weight": int(round(weight)),
                    "confidence": round(confidence, 4),
                    "behavior_score": round(behavior_score, 6),
                    "source": edge.get("source"),
                }
            )

        is_unstable = (enabled and weight < disable_below) or (
            (not enabled) and weight >= enable_on
        )
        if is_unstable:
            unstable_edges.append(
                {
                    "key": edge.get("_key"),
                    "from": edge.get("_from"),
                    "to": edge.get("_to"),
                    "op": edge.get("op"),
                    "enabled": enabled,
                    "weight": int(round(weight)),
                    "confidence": round(confidence, 4),
                    "behavior_score": round(behavior_score, 6),
                    "source": edge.get("source"),
                }
            )

    orphan_tags = []
    for tag in tags:
        key = tag.get("_key")
        if key not in referenced_enabled_keys:
            orphan_tags.append(
                {
                    "key": key,
                    "label": tag.get("label"),
                    "count": int(tag.get("count", 0)),
                }
            )
    orphan_tags.sort(key=lambda t: t["count"], reverse=True)

    noise_edges.sort(key=lambda e: (e["weight"], e["confidence"]))
    unstable_edges.sort(key=lambda e: (e["weight"], e["confidence"]))

    result = {
        "status": "ok",
        "summary": {
            "edges_total": edge_total,
            "edges_enabled": len(enabled_edges),
            "edges_disabled": len(disabled_edges),
            "enabled_ratio": round(len(enabled_edges) / edge_total, 4),
            "disabled_ratio": round(len(disabled_edges) / edge_total, 4),
            "noise_edges": len(noise_edges),
            "noise_rate": round(len(noise_edges) / edge_total, 4),
            "unstable_edges": len(unstable_edges),
            "orphan_tag_count": len(orphan_tags),
        },
        "thresholds": {
            "low_weight_threshold": low_weight_threshold,
            "min_confidence": min_confidence,
            "enable_on": enable_on,
            "disable_below": disable_below,
        },
        "top_noise_edges": noise_edges[:top_k],
        "top_unstable_edges": unstable_edges[:top_k],
        "orphan_tags": orphan_tags[:orphan_limit],
        "params": {
            "include_all_sources": include_all_sources,
            "top_k": top_k,
            "orphan_limit": orphan_limit,
        },
    }

    log_admin_run(
        db,
        action="quality_check",
        dry_run=True,
        status=result["status"],
        metrics={
            "edges_total": result["summary"]["edges_total"],
            "noise_edges": result["summary"]["noise_edges"],
            "unstable_edges": result["summary"]["unstable_edges"],
            "orphan_tag_count": result["summary"]["orphan_tag_count"],
        },
        args=result["params"],
    )
    return result
