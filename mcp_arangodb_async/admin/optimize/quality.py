"""Quality check - inspect tag_edges health and report graph metrics."""

from __future__ import annotations

from typing import Any, Dict, List

from arango.database import StandardDatabase
from ...utility.runtime_defaults import get_admin_defaults
from ...utility.access_log import log_admin_run

from .edges import AUTO_EDGE_SOURCES, _fetch_auto_edges


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
