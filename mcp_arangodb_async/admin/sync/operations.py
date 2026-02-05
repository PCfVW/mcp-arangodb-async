"""Operations for arango_admin_sync.

Builds/updates tags and tag_edges (AND/OR/NOT/XOR) from notes.tags.
"""

from __future__ import annotations

import hashlib
import itertools
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Tuple

from arango.database import StandardDatabase
from ..utility.runtime_defaults import get_admin_defaults
from ..utility.access_log import log_admin_run

AUTO_EDGE_SOURCES = ["auto", "auto-sync"]
_TAG_PREFIX_RE = re.compile(r"^[#]+")
_ALLOWED_KEY_RE = re.compile(r"[^A-Za-z0-9_:\-.@()+,=;\$!\*'%]")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _now_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


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


def _upsert_many(db: StandardDatabase, collection: str, docs: List[Dict[str, Any]]) -> int:
    if not docs:
        return 0

    query = f"""
    FOR doc IN @docs
      UPSERT {{ _key: doc._key }}
      INSERT doc
      UPDATE doc
      IN {collection}
    """

    affected = 0
    for chunk in _chunked(docs, 1000):
        cursor = db.aql.execute(query, bind_vars={"docs": chunk})
        list(cursor)
        affected += len(chunk)
    return affected


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
    now_ms: int,
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
        "created_at": now_ms,
        "updated_at": _now_iso(),
    }


def sync_tags_and_edges(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Synchronize tags and quaternary tag_edges from notes.tags."""
    defaults = get_admin_defaults("sync")
    dry_run = bool(args.get("dry_run", defaults.get("dry_run", False)))
    min_cooccur = int(args.get("min_cooccur_count", defaults.get("min_cooccur_count", 2)))
    and_threshold = float(args.get("and_threshold", defaults.get("and_threshold", 0.8)))
    or_threshold = float(args.get("or_threshold", defaults.get("or_threshold", 0.3)))
    min_tag_count_for_not = int(
        args.get("min_tag_count_for_not", defaults.get("min_tag_count_for_not", 4))
    )
    max_not_tags = int(args.get("max_not_tags", defaults.get("max_not_tags", 120)))
    xor_shared_min = int(args.get("xor_shared_min", defaults.get("xor_shared_min", 2)))
    clear_previous_auto = bool(
        args.get("clear_previous_auto", defaults.get("clear_previous_auto", True))
    )

    rows = _load_note_tag_rows(db)

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

    now_ms = _now_ms()
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

    for (a, b), co in pair_counts.items():
        if co < min_cooccur:
            continue

        count_a = tag_counts[a]
        count_b = tag_counts[b]
        p_forward = co / max(1, count_a)
        p_backward = co / max(1, count_b)

        op = None
        if p_forward >= and_threshold and p_backward >= and_threshold:
            op = "AND"
            weight = int(round(24 + 20 * min((p_forward + p_backward) / 2.0, 1.0)))
        elif p_forward >= or_threshold and p_backward >= or_threshold:
            op = "OR"
            weight = int(round(12 + 16 * min((p_forward + p_backward) / 2.0, 1.0)))
        else:
            continue

        edge_docs.append(
            _make_edge_doc(
                from_key=label_to_key[a],
                to_key=label_to_key[b],
                op=op,
                weight=weight,
                p_forward=p_forward,
                p_backward=p_backward,
                now_ms=now_ms,
            )
        )
        op_counter[op] += 1

    frequent_tags = [
        label
        for label, cnt in tag_counts.most_common(max_not_tags)
        if cnt >= min_tag_count_for_not
    ]

    not_pairs: List[Tuple[str, str]] = []
    for a, b in itertools.combinations(sorted(frequent_tags), 2):
        if (a, b) in pair_counts:
            continue
        not_pairs.append((a, b))
        edge_docs.append(
            _make_edge_doc(
                from_key=label_to_key[a],
                to_key=label_to_key[b],
                op="NOT",
                weight=10,
                p_forward=0.0,
                p_backward=0.0,
                now_ms=now_ms,
            )
        )
        op_counter["NOT"] += 1

    for a, b in not_pairs:
        shared = neighbors.get(a, set()) & neighbors.get(b, set())
        if len(shared) < xor_shared_min:
            continue
        weight = int(min(36, 12 + (len(shared) * 3)))
        edge_docs.append(
            _make_edge_doc(
                from_key=label_to_key[a],
                to_key=label_to_key[b],
                op="XOR",
                weight=weight,
                p_forward=0.0,
                p_backward=0.0,
                now_ms=now_ms,
            )
        )
        op_counter["XOR"] += 1

    dedup = {doc["_key"]: doc for doc in edge_docs}
    edge_docs = list(dedup.values())

    written_tags = 0
    removed_edges = 0
    written_edges = 0

    if not dry_run:
        _ensure_collection(db, "tags", edge=False)
        _ensure_collection(db, "tag_edges", edge=True)

        written_tags = _upsert_many(db, "tags", tag_docs)

        if clear_previous_auto:
            remove_query = """
            FOR e IN tag_edges
              FILTER e.source IN @sources
              REMOVE e IN tag_edges
              COLLECT WITH COUNT INTO removed
              RETURN removed
            """
            removed = list(db.aql.execute(remove_query, bind_vars={"sources": AUTO_EDGE_SOURCES}))
            removed_edges = int(removed[0]) if removed else 0

        written_edges = _upsert_many(db, "tag_edges", edge_docs)

    result = {
        "status": "ok",
        "dry_run": dry_run,
        "notes_processed": len(rows),
        "tags_distinct": len(tag_counts),
        "pairs_distinct": len(pair_counts),
        "tags_written": written_tags,
        "edges_removed": removed_edges,
        "edges_written": written_edges,
        "edge_ops": dict(op_counter),
        "params": {
            "min_cooccur_count": min_cooccur,
            "and_threshold": and_threshold,
            "or_threshold": or_threshold,
            "min_tag_count_for_not": min_tag_count_for_not,
            "max_not_tags": max_not_tags,
            "xor_shared_min": xor_shared_min,
            "clear_previous_auto": clear_previous_auto,
        },
    }

    # Persist one admin run log for observability and behavior analysis.
    log_admin_run(
        db,
        action="sync_run",
        dry_run=dry_run,
        status=result["status"],
        metrics={
            "notes_processed": result["notes_processed"],
            "tags_distinct": result["tags_distinct"],
            "edges_written": result["edges_written"],
            "edges_removed": result["edges_removed"],
        },
        args=result["params"],
    )
    return result
