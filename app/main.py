# app/main.py
from fastapi import FastAPI, Request, HTTPException, Header
from prometheus_client import make_asgi_app
from app.agents.orchestrator import run_review
from app.services.github_service import post_comment, fetch_diff
from app.services.metrics_service import (
    webhook_counter, review_duration, active_reviews
)
import hmac, hashlib, time

app = FastAPI(title="Code Review Bot")

# Mount Prometheus metrics at /metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/webhook/github")
async def github_webhook(
    request: Request,
    x_hub_signature_256: str = Header(None)
):
    payload = await request.body()
    verify_signature(payload, x_hub_signature_256)  # security
    
    data = await request.json()
    
    # Only act on PR open/sync events
    if data.get("action") not in ["opened", "synchronize"]:
        return {"status": "ignored"}
    
    pr = data["pull_request"]
    repo_full_name = data["repository"]["full_name"]
    pr_number = pr["number"]
    diff_url = pr["diff_url"]
    
    # Track metrics
    webhook_counter.inc()
    active_reviews.inc()
    start = time.time()
    
    try:
        diff = await fetch_diff(diff_url)
        review = await run_review(diff, repo_full_name, pr_number)
        await post_comment(repo_full_name, pr_number, review)
    finally:
        active_reviews.dec()
        review_duration.observe(time.time() - start)
    
    return {"status": "review posted"}

def verify_signature(payload: bytes, signature: str):
    import os
    secret = os.getenv("GITHUB_WEBHOOK_SECRET", "").encode()
    expected = "sha256=" + hmac.new(secret, payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature or ""):
        raise HTTPException(status_code=401, detail="Invalid signature")