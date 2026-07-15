from __future__ import annotations

import json
import logging
from typing import Any

from django.conf import settings

from .models import Category

logger = logging.getLogger(__name__)

CACHE_KEY = "eops:category_tree:v1"
CACHE_TTL_SECONDS = 60 * 60
ROOT_KEY = "__root__"


def _redis_client():
    try:
        import redis

        return redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Redis unavailable: %s", exc)
        return None


def build_category_tree() -> dict[str, Any]:
    rows = list(Category.objects.all().values("id", "name", "parent_id"))
    nodes: dict[str, dict[str, Any]] = {}
    children: dict[str, list[str]] = {ROOT_KEY: []}

    for row in rows:
        cid = str(row["id"])
        parent_id = str(row["parent_id"]) if row["parent_id"] else ROOT_KEY
        nodes[cid] = {
            "id": cid,
            "name": row["name"],
            "parent_id": None if parent_id == ROOT_KEY else parent_id,
        }
        children.setdefault(parent_id, []).append(cid)
        children.setdefault(cid, [])

    return {"nodes": nodes, "children": children}


def get_category_tree(*, force_refresh: bool = False) -> dict[str, Any]:
    client = _redis_client()
    if client and not force_refresh:
        try:
            cached = client.get(CACHE_KEY)
            if cached:
                return json.loads(cached)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Redis get failed: %s", exc)

    tree = build_category_tree()

    if client:
        try:
            client.setex(CACHE_KEY, CACHE_TTL_SECONDS, json.dumps(tree))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Redis set failed: %s", exc)

    return tree


def invalidate_category_tree() -> None:
    client = _redis_client()
    if not client:
        return
    try:
        client.delete(CACHE_KEY)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Redis delete failed: %s", exc)


def dfs_collect_descendant_ids(category_id: str, tree: dict[str, Any] | None = None) -> list[str]:
    tree = tree or get_category_tree()
    children = tree.get("children", {})
    root = str(category_id)
    if root not in tree.get("nodes", {}):
        return []

    collected: list[str] = []
    stack = [root]
    while stack:
        current = stack.pop()
        collected.append(current)
        for child_id in reversed(children.get(current, [])):
            stack.append(child_id)
    return collected
