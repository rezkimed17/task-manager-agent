from __future__ import annotations

from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter("app_request_count", "Total HTTP requests", ["method", "path", "code"])
REQUEST_LATENCY = Histogram("app_request_latency_seconds", "Request latency", ["method", "path"])

