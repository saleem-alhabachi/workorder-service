from prometheus_client import Counter, Histogram

REQUESTS_TOTAL = Counter("http_requests_total", "Total HTTP requests", ["method", "path", "status"])
REQUEST_LATENCY = Histogram("http_request_latency_seconds", "HTTP request latency", ["method", "path"])
