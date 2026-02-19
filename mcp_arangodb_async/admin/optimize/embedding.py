"""Embedding operations - generate, search, status.

Uses AQL COSINE_SIMILARITY for brute-force tag matching (1989 tags, millisecond-level).
No vector index required.
"""

from __future__ import annotations

import logging
import re
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List

from arango.database import StandardDatabase

from .engine import encode_texts, get_model_info

logger = logging.getLogger(__name__)


@contextmanager
def _safe_cursor(cursor):
    try:
        yield cursor
    finally:
        try:
            cursor.close()
        except Exception:
            pass


def embedding_generate(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Generate embeddings for tags and store in tags collection.

    If args["tags"] is provided, generates only for those tags.
    Otherwise generates for all tags missing embeddings.
    """
    model_name = args.get("model_name")
    batch_size = args.get("batch_size", 64)
    specific_tags = args.get("tags")

    if specific_tags:
        cursor = db.aql.execute(
            "FOR t IN tags FILTER t.label IN @labels RETURN { _key: t._key, label: t.label }",
            bind_vars={"labels": specific_tags},
        )
    else:
        cursor = db.aql.execute(
            "FOR t IN tags FILTER t.embedding == null RETURN { _key: t._key, label: t.label }"
        )

    with _safe_cursor(cursor):
        tags_to_process = list(cursor)

    if not tags_to_process:
        return {"message": "All tags already have embeddings", "count": 0}

    labels = [t["label"].lstrip("#") for t in tags_to_process]
    keys = [t["_key"] for t in tags_to_process]

    logger.info("Generating embeddings for %d tags", len(labels))
    start = time.time()

    embeddings = encode_texts(labels, model_name=model_name, batch_size=batch_size)

    elapsed_encode = time.time() - start
    dimension = len(embeddings[0]) if embeddings else 0

    model_info = get_model_info()
    embedded_at = datetime.now(timezone.utc).isoformat()

    updates = []
    for key, label, emb in zip(keys, labels, embeddings):
        updates.append({
            "_key": key,
            "embedding": emb,
            "embedding_text": label,
            "embedding_model": model_info["model_name"],
            "embedded_at": embedded_at,
        })

    start_write = time.time()
    write_cursor = db.aql.execute(
        """
        FOR item IN @updates
            UPDATE { _key: item._key } WITH {
                embedding: item.embedding,
                embedding_text: item.embedding_text,
                embedding_model: item.embedding_model,
                embedded_at: item.embedded_at
            } IN tags
        """,
        bind_vars={"updates": updates},
    )
    with _safe_cursor(write_cursor):
        pass  # write query returns no documents; cursor must still be closed
    elapsed_write = time.time() - start_write

    return {
        "generated": len(embeddings),
        "dimension": dimension,
        "model": model_info["model_name"],
        "time_encode_sec": round(elapsed_encode, 2),
        "time_write_sec": round(elapsed_write, 2),
    }


def embedding_search(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Semantic search: query -> tokenize -> match tags -> score notes."""
    query_text = args.get("query")
    if not query_text:
        return {"error": "Missing 'query' parameter"}

    top_k = args.get("top_k", 5)
    threshold = args.get("threshold", 0.5)
    limit = args.get("limit", 20)

    tokens = _tokenize(query_text)
    if not tokens:
        return {"error": "Query produced no tokens", "query": query_text}

    token_vecs = encode_texts(tokens)

    all_matched_tags: Dict[str, float] = {}

    for token, vec in zip(tokens, token_vecs):
        cursor = db.aql.execute(
            """
            FOR t IN tags
                FILTER t.embedding != null
                LET score = COSINE_SIMILARITY(t.embedding, @qvec)
                FILTER score > @threshold
                SORT score DESC
                LIMIT @top_k
                RETURN { label: t.label, score }
            """,
            bind_vars={"qvec": vec, "threshold": threshold, "top_k": top_k},
        )
        with _safe_cursor(cursor):
            for row in cursor:
                label = row["label"]
                score = row["score"]
                if label not in all_matched_tags or score > all_matched_tags[label]:
                    all_matched_tags[label] = score

    if not all_matched_tags:
        return {
            "query": query_text,
            "tokens": tokens,
            "matched_tags": [],
            "notes": [],
            "message": "No tags matched above threshold",
        }

    matched_list = [
        {"label": k, "score": round(v, 4)} for k, v in all_matched_tags.items()
    ]
    matched_list.sort(key=lambda x: x["score"], reverse=True)

    tag_scores_map = all_matched_tags

    cursor = db.aql.execute(
        """
        LET tag_scores = @tag_scores

        FOR n IN notes
            LET matched = (
                FOR t IN n.tags
                    FILTER t IN ATTRIBUTES(tag_scores)
                    RETURN tag_scores[t]
            )
            FILTER LENGTH(matched) > 0
            LET total = SUM(matched)
            SORT total DESC
            LIMIT @limit
            RETURN {
                _key: n._key,
                title: n.title,
                tags: n.tags,
                score: ROUND(total * 10000) / 10000,
                matched_count: LENGTH(matched)
            }
        """,
        bind_vars={"tag_scores": tag_scores_map, "limit": limit},
    )

    with _safe_cursor(cursor):
        notes = list(cursor)

    return {
        "query": query_text,
        "tokens": tokens,
        "matched_tags": matched_list,
        "notes": notes,
        "note_count": len(notes),
    }


def embedding_status(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Report embedding coverage and model info."""
    cursor = db.aql.execute(
        """
        LET total = LENGTH(FOR t IN tags RETURN 1)
        LET with_emb = LENGTH(FOR t IN tags FILTER t.embedding != null RETURN 1)
        LET sample = (FOR t IN tags FILTER t.embedding != null LIMIT 1 RETURN {
            dimension: LENGTH(t.embedding),
            model: t.embedding_model
        })
        RETURN {
            total_tags: total,
            with_embedding: with_emb,
            without_embedding: total - with_emb,
            coverage_pct: total > 0 ? ROUND(with_emb * 10000 / total) / 100 : 0,
            sample: LENGTH(sample) > 0 ? sample[0] : null
        }
        """
    )
    with _safe_cursor(cursor):
        result = list(cursor)[0]
    result["engine"] = get_model_info()
    return result


def _tokenize(text: str) -> List[str]:
    """Simple tokenization for search queries."""
    raw = re.split(r"[\s,;|]+", text.strip())
    tokens = [t.lstrip("#").strip() for t in raw if t.strip()]
    seen = set()
    result = []
    for t in tokens:
        if t and t not in seen:
            seen.add(t)
            result.append(t)
    return result
