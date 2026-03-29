# SentinelPR
A FastAPI-based GitHub PR review bot that runs parallel LLM agents and posts structured review comments.

![Build](https://img.shields.io/badge/build-passing-brightgreen)
![Python](https://img.shields.io/badge/python-3.11-blue)
![License](https://img.shields.io/badge/license-MIT-lightgrey)
![Docker](https://img.shields.io/badge/docker-ready-blue)

## What is SentinelPR?
SentinelPR receives GitHub pull request webhooks, fetches the PR diff, runs security and quality reviews in parallel using Gemini via LangChain, and posts a synthesized comment back to the PR. It exposes Prometheus metrics and includes a Docker Compose stack with Prometheus and Grafana.

## Live Demo
https://sentinelpr.onrender.com

health check -> https://sentinelpr.onrender.com/health
webhook -> https://sentinelpr.onrender.com/webhook/github
metrics -> https://sentinelpr.onrender.com/metrics

## Architecture
Actual runtime flow from the code:

```
GitHub PR webhook
        |
        v
POST /webhook/github (FastAPI)
        |
        v
verify_signature -> fetch diff (GitHub API)
        |
        v
LangGraph orchestrator
  |            |
  v            v
Security agent  Quality agent
  |            |
  v            v
   Aggregator (LLM)
        |
        v
Post comment to PR
```

## Tech Stack
| Category | Tools |
| --- | --- |
| API | FastAPI, Uvicorn |
| LLM Orchestration | LangGraph, LangChain |
| LLM Provider | Gemini via langchain-google-genai, google-generativeai |
| HTTP Client | httpx |
| Config | python-dotenv |
| Observability | prometheus-client, Prometheus, Grafana |
| Testing | pytest, pytest-asyncio |
| Containers | Docker, Docker Compose |
| CI | GitHub Actions |

## Features
- GitHub webhook verification using HMAC SHA256
- Parallel security and code-quality analysis using async agents
- Defensive JSON parsing and graceful agent fallbacks
- Prometheus metrics for webhook volume, latency, and agent health
- Docker Compose stack for app + Prometheus + Grafana

## Getting Started

### Local (venv)
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Docker Compose
```
docker compose up --build
```

### Environment Variables
Copy .env.example and fill in values:
- GOOGLE_API_KEYS=GOOGLE_API_KEY1,GOOGLE_API_KEY2
- GOOGLE_API_KEY1=...
- GOOGLE_API_KEY2=...
- GITHUB_TOKEN=...
- GITHUB_WEBHOOK_SECRET=...

## Monitoring
Prometheus scrapes /metrics from the bot container. Metrics defined in code:
- bot_webhooks_total
- bot_review_duration_seconds
- bot_active_reviews
- bot_agent_errors_total
- bot_findings_total

Grafana provisioning directory exists but contains no dashboards in this repo.

## CI/CD
GitHub Actions workflow runs on push and PR to main:
1. Checkout code
2. Setup Python 3.11
3. Install dependencies
4. Run pytest
5. Build Docker image

A separate workflow sends a signed webhook on PR opened/synchronize events.

## Project Structure
```
app/
  agents/                 # security, quality, aggregation, orchestration
  core/                   # LLM factory and key rotation
  models/                 # pydantic schemas
  services/               # GitHub API client and Prometheus metrics
  main.py                 # FastAPI entrypoint
  __init__.py
.github/workflows/        # CI and webhook trigger workflows
k8s/                      # Kubernetes manifests (deployment defined, others empty)
monitoring/               # Prometheus config, Grafana provisioning folder
Dockerfile
docker-compose.yml
pytest.ini
requirements.txt
render.yaml
README.md
```
