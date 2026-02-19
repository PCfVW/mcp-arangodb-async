"""Embedding engine - lazy-loaded Qwen3 model for tag vector generation.

Loads model once on first use, caches in module scope.
All operations are synchronous (CPU inference, fast for short texts).
"""

from __future__ import annotations

import logging
import threading
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# Module-level cache
_model = None
_tokenizer = None
_model_name: Optional[str] = None
_load_lock = threading.Lock()

DEFAULT_MODEL = "Qwen/Qwen3-Embedding-0.6B"


def _load_model(model_name: str | None = None) -> Tuple:
    """Load model and tokenizer, cached after first call."""
    global _model, _tokenizer, _model_name

    target = model_name or DEFAULT_MODEL

    # Fast path: model already loaded for this target
    if _model is not None and _model_name == target:
        return _model, _tokenizer

    with _load_lock:
        # Re-check inside lock to avoid double-load
        if _model is not None and _model_name == target:
            return _model, _tokenizer

        logger.info("Loading embedding model: %s", target)

        import torch
        from transformers import AutoModel, AutoTokenizer

        _tokenizer = AutoTokenizer.from_pretrained(target, trust_remote_code=True)
        _model = AutoModel.from_pretrained(target, trust_remote_code=True)
        _model.eval()
        _model_name = target

        logger.info("Model loaded: %s", target)

    return _model, _tokenizer


def encode_texts(
    texts: List[str],
    model_name: str | None = None,
    batch_size: int = 64,
) -> List[List[float]]:
    """Encode list of texts into embedding vectors.

    Args:
        texts: List of text strings to encode.
        model_name: HuggingFace model name. Uses default if None.
        batch_size: Texts per batch for inference.

    Returns:
        List of embedding vectors (each a list of floats).
    """
    import torch

    model, tokenizer = _load_model(model_name)
    all_embeddings: List[List[float]] = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        encoded = tokenizer(
            batch,
            padding=True,
            truncation=True,
            max_length=128,
            return_tensors="pt",
        )

        with torch.no_grad():
            outputs = model(**encoded)
            # Mean pooling over non-padding tokens (better for short texts)
            attention_mask = encoded["attention_mask"].unsqueeze(-1)
            hidden = outputs.last_hidden_state
            summed = (hidden * attention_mask).sum(dim=1)
            counts = attention_mask.sum(dim=1).clamp(min=1)
            embeddings = summed / counts
            # L2 normalize
            embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)

        all_embeddings.extend(embeddings.tolist())

    return all_embeddings


def get_model_info() -> Dict:
    """Return current model info."""
    return {
        "model_name": _model_name or "(not loaded)",
        "default_model": DEFAULT_MODEL,
        "loaded": _model is not None,
    }
