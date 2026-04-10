import json

import redis
from flask import current_app


class RouteCache:
    def __init__(self):
        self._client = None

    def _client_or_none(self):
        if self._client is not None:
            return self._client

        try:
            redis_url = current_app.config.get("REDIS_URL", "redis://localhost:6379/0")
            self._client = redis.from_url(redis_url, decode_responses=True)
            return self._client
        except Exception:
            return None

    def get_json(self, key):
        client = self._client_or_none()
        if not client:
            return None

        try:
            raw = client.get(key)
            return json.loads(raw) if raw else None
        except Exception:
            return None

    def set_json(self, key, value, ttl_seconds):
        client = self._client_or_none()
        if not client:
            return False

        try:
            client.set(key, json.dumps(value), ex=ttl_seconds)
            return True
        except Exception:
            return False

    def delete_keys(self, *keys):
        client = self._client_or_none()
        if not client or not keys:
            return 0

        try:
            return client.delete(*keys)
        except Exception:
            return 0

    def delete_prefix(self, prefix):
        client = self._client_or_none()
        if not client:
            return 0

        deleted = 0
        try:
            for key in client.scan_iter(match=f"{prefix}*"):
                deleted += client.delete(key)
            return deleted
        except Exception:
            return deleted

    def scan_json(self, prefix, limit=20):
        client = self._client_or_none()
        if not client:
            return []

        records = []
        try:
            for key in client.scan_iter(match=f"{prefix}*"):
                raw = client.get(key)
                if not raw:
                    continue
                try:
                    value = json.loads(raw)
                except Exception:
                    continue

                records.append({"key": key, "value": value})
                if len(records) >= int(limit):
                    break
        except Exception:
            return records

        return records
