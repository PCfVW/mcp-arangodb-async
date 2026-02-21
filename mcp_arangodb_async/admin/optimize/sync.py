"""Sync operations - build/update tags and tag_edges from notes.tags.

Builds quaternary edges (AND/OR/NOT/XOR) based on PMI co-occurrence statistics.

Classification uses Pointwise Mutual Information (PMI):
  PMI(a,b) = log2(P(a,b) / (P(a) * P(b)))
  - AND:  PMI >= pmi_and_threshold  (strong co-occurrence)
  - OR:   0 < PMI < pmi_and_threshold  (weak co-occurrence)
  - NOT:  expected co-occurrence >= min_expected, actual = 0, no shared neighbors
  - XOR:  same as NOT but with shared_neighbors >= xor_shared_min
"""

from __future__ import annotations

import hashlib
import itertools
import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Tuple

from arango.database import StandardDatabase
from ...utility.runtime_defaults import get_admin_defaults
from ...utility.access_log import log_admin_run

AUTO_EDGE_SOURCES = ["auto", "auto-sync"]
_TAG_PREFIX_RE = re.compile(r"^[#]+")
_ALLOWED_KEY_RE = re.compile(r"[^A-Za-z0-9_:\-.@()+,=;\$!\*'%]")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_tag(raw: Any) -> str:
    if not isinstance(raw, str):
        return ""
    value = _TAG_PREFIX_RE.sub("", raw.strip()).strip().lower()
    return value


def _sanitize_key(label: str) -> str:
    base = _ALLOWED_KEY_RE.sub("_", label).strip("._-")
    if not base:
        base = "t_" + hashlib.sha1(label.encode("utf-8")).hexdigest()[:16]
    if len(base) > 254:
        base = base[:254]
    return base


def _edge_key(from_key: str, to_key: str, op: str) -> str:
    payload = f"{from_key}|{to_key}|{op}"
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:24]


def _chunked(items: List[Dict[str, Any]], size: int = 1000) -> Iterable[List[Dict[str, Any]]]:
    for idx in range(0, len(items), size):
        yield items[idx: idx + size]


def _upsert_tags(db: StandardDatabase, docs: List[Dict[str, Any]]) -> int:
    """Upsert tags — full overwrite is safe for tag docs."""
    if not docs:
        return 0
    query = """
    FOR doc IN @docs
      UPSERT { _key: doc._key }
      INSERT doc
      UPDATE doc
      IN tags
    """
    affected = 0
    for chunk in _chunked(docs, 1000):
        cursor = db.aql.execute(query, bind_vars={"docs": chunk})
        list(cursor)
        affected += len(chunk)
    return affected


def _merge_edges(db: StandardDatabase, docs: List[Dict[str, Any]]) -> int:
    """Upsert edges — on UPDATE, only merge sync fields, preserve optimized fields.

    Preserved fields (from optimize_run): weight, confidence, behavior_score.
    Updated fields (from sync): op, p_forward, p_backward, enabled, updated_at.
    """
    if not docs:
        return 0
    query = """
    FOR doc IN @docs
      UPSERT { _key: doc._key }
      INSERT doc
      UPDATE MERGE(
        { op: doc.op, p_forward: doc.p_forward, p_backward: doc.p_backward,
          enabled: doc.enabled, source: doc.source, updated_at: doc.updated_at }
      )
      IN tag_edges
    """
    affected = 0
    for chunk in _chunked(docs, 1000):
        cursor = db.aql.execute(query, bind_vars={"docs": chunk})
        list(cursor)
        affected += len(chunk)
    return affected


def _disable_stale_edges(db: StandardDatabase, current_keys: set[str]) -> int:
    """Disable auto-sync edges that no longer exist in current sync."""
    if not current_keys:
        return 0
    cursor = db.aql.execute(
        """
        FOR e IN tag_edges
          FILTER e.source IN @sources AND e.enabled == true AND e._key NOT IN @keys
          UPDATE e WITH { enabled: false, updated_at: @now } IN tag_edges
          COLLECT WITH COUNT INTO cnt
          RETURN cnt
        """,
        bind_vars={
            "sources": AUTO_EDGE_SOURCES,
            "keys": list(current_keys),
            "now": _now_iso(),
        },
    )
    result = list(cursor)
    return int(result[0]) if result else 0


def _ensure_collection(db: StandardDatabase, name: str, edge: bool = False) -> None:
    if db.has_collection(name):
        return
    db.create_collection(name, edge=edge)


def _load_note_tag_rows(db: StandardDatabase) -> List[List[str]]:
    query = """
    FOR n IN notes
      FILTER IS_ARRAY(n.tags) AND LENGTH(n.tags) > 0
      LET cleaned = UNIQUE(
        FOR raw IN n.tags
          FILTER IS_STRING(raw)
          LET c = LOWER(TRIM(REGEX_REPLACE(raw, '^[#]+', '')))
          FILTER LENGTH(c) > 0
          RETURN c
      )
      FILTER LENGTH(cleaned) > 0
      RETURN cleaned
    """
    return list(db.aql.execute(query))


def _load_existing_tags(db: StandardDatabase) -> Dict[str, str]:
    query = """
    FOR t IN tags
      LET clean = LOWER(TRIM(REGEX_REPLACE(TO_STRING(t.label), '^[#]+', '')))
      FILTER LENGTH(clean) > 0
      RETURN { clean: clean, key: t._key }
    """
    mapping: Dict[str, str] = {}
    for row in db.aql.execute(query):
        mapping[row["clean"]] = row["key"]
    return mapping


def _make_edge_doc(
    from_key: str,
    to_key: str,
    op: str,
    weight: int,
    p_forward: float,
    p_backward: float,
) -> Dict[str, Any]:
    left, right = sorted((from_key, to_key))
    return {
        "_key": _edge_key(left, right, op),
        "_from": f"tags/{left}",
        "_to": f"tags/{right}",
        "op": op,
        "weight": int(max(1, min(64, weight))),
        "p_forward": round(float(p_forward), 4),
        "p_backward": round(float(p_backward), 4),
        "enabled": True,
        "source": "auto-sync",
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    }


def _compute_pmi(co: int, count_a: int, count_b: int, total: int) -> float:
    """Compute Pointwise Mutual Information: log2(P(a,b) / (P(a)*P(b)))."""
    if co <= 0 or count_a <= 0 or count_b <= 0 or total <= 0:
        return float("-inf")
    p_ab = co / total
    p_a = count_a / total
    p_b = count_b / total
    return math.log2(p_ab / (p_a * p_b))


def sync_tags_and_edges(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Synchronize tags and quaternary tag_edges from notes.tags.

    Uses PMI-based classification:
      AND:  PMI >= pmi_and (strong co-occurrence)
      OR:   0 < PMI < pmi_and (weak co-occurrence)
      NOT:  expected >= min_expected, actual=0, no shared neighbors (true exclusion)
      XOR:  expected >= min_expected, actual=0, shared_neighbors >= threshold (competitive exclusion)
    """
    defaults = get_admin_defaults("sync")
    dry_run = bool(args.get("dry_run", defaults.get("dry_run", False)))
    min_cooccur = int(args.get("min_cooccur_count", defaults.get("min_cooccur_count", 2)))
    pmi_and = float(args.get("pmi_and", defaults.get("pmi_and", 3.0)))
    min_expected = float(args.get("min_expected", defaults.get("min_expected", 3.0)))
    min_tag_count = int(args.get("min_tag_count", defaults.get("min_tag_count", 4)))
    xor_shared_min = int(args.get("xor_shared_min", defaults.get("xor_shared_min", 2)))

    rows = _load_note_tag_rows(db)
    total_notes = len(rows)

    tag_counts: Counter[str] = Counter()
    pair_counts: Counter[Tuple[str, str]] = Counter()
    neighbors: Dict[str, set[str]] = defaultdict(set)

    for row in rows:
        normalized = sorted({_normalize_tag(t) for t in row if _normalize_tag(t)})
        if not normalized:
            continue
        tag_counts.update(normalized)
        for a, b in itertools.combinations(normalized, 2):
            pair_counts[(a, b)] += 1
            neighbors[a].add(b)
            neighbors[b].add(a)

    existing = _load_existing_tags(db)
    used_keys = set(existing.values())

    label_to_key: Dict[str, str] = {}
    for label in tag_counts.keys():
        if label in existing:
            label_to_key[label] = existing[label]
            continue

        key = _sanitize_key(label)
        if key in used_keys:
            key = "t_" + hashlib.sha1(label.encode("utf-8")).hexdigest()[:16]
        used_keys.add(key)
        label_to_key[label] = key

    tag_docs = [
        {
            "_key": label_to_key[label],
            "label": label,
            "count": int(cnt),
            "source": "auto-sync",
            "updated_at": _now_iso(),
        }
        for label, cnt in tag_counts.items()
    ]

    edge_docs: List[Dict[str, Any]] = []
    op_counter: Counter[str] = Counter()
    noise_count = 0

    # --- Phase 1: AND/OR from co-occurring pairs (PMI-based) ---
    cooccur_set: set[Tuple[str, str]] = set()

    for (a, b), co in pair_counts.items():
        if co < min_cooccur:
            continue

        count_a = tag_counts[a]
        count_b = tag_counts[b]
        pmi = _compute_pmi(co, count_a, count_b, total_notes)

        if pmi <= 0:
            noise_count += 1
            continue

        p_forward = co / max(1, count_a)
        p_backward = co / max(1, count_b)
        cooccur_set.add((a, b))

        if pmi >= pmi_and:
            op = "AND"
            weight = int(round(24 + 20 * min(pmi / 10.0, 1.0)))
        else:
            op = "OR"
            weight = int(round(12 + 16 * min(pmi / pmi_and, 1.0)))

        edge_docs.append(
            _make_edge_doc(
                from_key=label_to_key[a],
                to_key=label_to_key[b],
                op=op,
                weight=weight,
                p_forward=p_forward,
                p_backward=p_backward,
            )
        )
        op_counter[op] += 1

    # --- Phase 2: NOT/XOR from non-co-occurring pairs (expected-based) ---
    eligible_tags = [
        label for label, cnt in tag_counts.items()
        if cnt >= min_tag_count
    ]

    for a, b in itertools.combinations(sorted(eligible_tags), 2):
        if (a, b) in pair_counts:
            continue

        count_a = tag_counts[a]
        count_b = tag_counts[b]
        expected = (count_a * count_b) / max(1, total_notes)
        if expected < min_expected:
            continue

        shared = neighbors.get(a, set()) & neighbors.get(b, set())

        if len(shared) >= xor_shared_min:
            op = "XOR"
            weight = int(min(36, 12 + (len(shared) * 3)))
        else:
            op = "NOT"
            weight = int(round(10 + 10 * min(expected / 10.0, 1.0)))

        edge_docs.append(
            _make_edge_doc(
                from_key=label_to_key[a],
                to_key=label_to_key[b],
                op=op,
                weight=weight,
                p_forward=0.0,
                p_backward=0.0,
            )
        )
        op_counter[op] += 1

    dedup = {doc["_key"]: doc for doc in edge_docs}
    edge_docs = list(dedup.values())
    current_edge_keys = set(dedup.keys())

    written_tags = 0
    merged_edges = 0
    disabled_edges = 0

    if not dry_run:
        _ensure_collection(db, "tags", edge=False)
        _ensure_collection(db, "tag_edges", edge=True)

        written_tags = _upsert_tags(db, tag_docs)
        merged_edges = _merge_edges(db, edge_docs)
        disabled_edges = _disable_stale_edges(db, current_edge_keys)

    result = {
        "status": "ok",
        "dry_run": dry_run,
        "notes_processed": total_notes,
        "tags_distinct": len(tag_counts),
        "pairs_distinct": len(pair_counts),
        "tags_written": written_tags,
        "edges_merged": merged_edges,
        "edges_disabled": disabled_edges,
        "noise_skipped": noise_count,
        "edge_ops": dict(op_counter),
        "params": {
            "min_cooccur_count": min_cooccur,
            "pmi_and": pmi_and,
            "min_expected": min_expected,
            "min_tag_count": min_tag_count,
            "xor_shared_min": xor_shared_min,
        },
    }

    log_admin_run(
        db,
        action="sync_run",
        dry_run=dry_run,
        status=result["status"],
        metrics={
            "notes_processed": result["notes_processed"],
            "tags_distinct": result["tags_distinct"],
            "edges_merged": merged_edges,
            "edges_disabled": disabled_edges,
            "noise_skipped": noise_count,
        },
        args=result["params"],
    )
    return result
