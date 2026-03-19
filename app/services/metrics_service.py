# app/services/metrics_service.py
from prometheus_client import Counter, Histogram, Gauge

webhook_counter = Counter(
    "bot_webhooks_total",
    "Total webhooks received"
)

review_duration = Histogram(
    "bot_review_duration_seconds",
    "Time taken to complete a full review",
    buckets=[1, 5, 10, 30, 60, 120]
)

active_reviews = Gauge(
    "bot_active_reviews",
    "Currently running reviews"
)

agent_errors = Counter(
    "bot_agent_errors_total",
    "Agent failures",
    ["agent_name"]
)

findings_counter = Counter(
    "bot_findings_total",
    "Findings raised by agents",
    ["agent_name", "severity"]
)