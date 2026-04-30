from __future__ import annotations

from typing import Any, Dict, List, Union

import requests


def post_infer(
    url: str,
    payload: Dict[str, Any],
    *,
    timeout_s: float,
) -> Dict[str, Any]:
    r = requests.post(url, json=payload, timeout=timeout_s)
    try:
        body = r.json()
    except ValueError:
        r.raise_for_status()
        raise RuntimeError(f"Infer returned non-JSON: {r.text[:500]!r}")

    if r.status_code != 200:
        raise RuntimeError(f"Infer HTTP {r.status_code}: {body}")

    if "error" in body or "detail" in body:
        raise RuntimeError(f"Infer error payload: {body}")

    if "action" not in body:
        raise RuntimeError(f"Infer missing 'action' key: {body.keys()}")

    return body


def normalize_action(action: Union[List[float], Any]) -> List[float]:
    if hasattr(action, "tolist"):
        action = action.tolist()
    if not isinstance(action, (list, tuple)):
        raise TypeError(f"action must be list-like, got {type(action)}")
    return [float(x) for x in action]
