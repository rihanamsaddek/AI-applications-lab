"""Simple file-based cache for API responses."""

import json
import logging
import time
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

DEFAULT_TTL = 3600 * 24  # 24 hours


class CacheManager:
    """File-based cache with TTL support."""

    def __init__(self, cache_dir: str = "data/cache", ttl_seconds: int = DEFAULT_TTL):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl_seconds

    def _key_path(self, key: str) -> Path:
        safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in key)
        return self.cache_dir / f"{safe}.json"

    def get(self, key: str) -> Optional[Any]:
        path = self._key_path(key)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text())
            if time.time() - data["ts"] > self.ttl:
                path.unlink(missing_ok=True)
                return None
            return data["value"]
        except Exception:
            return None

    def set(self, key: str, value: Any):
        path = self._key_path(key)
        try:
            path.write_text(json.dumps({"ts": time.time(), "value": value}))
        except Exception as e:
            logger.warning(f"Cache write failed for key '{key}': {e}")

    def invalidate(self, key: str):
        self._key_path(key).unlink(missing_ok=True)

    def clear_expired(self):
        """Remove all expired cache files."""
        now = time.time()
        removed = 0
        for path in self.cache_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text())
                if now - data["ts"] > self.ttl:
                    path.unlink()
                    removed += 1
            except Exception:
                pass
        if removed:
            logger.info(f"Cleared {removed} expired cache entries")
