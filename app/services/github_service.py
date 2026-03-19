# app/services/github_service.py
import httpx
import os

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

async def fetch_diff(diff_url: str) -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.get(diff_url, headers=HEADERS)
        return resp.text

async def post_comment(repo: str, pr_number: int, review: str):
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    async with httpx.AsyncClient() as client:
        await client.post(url, headers=HEADERS, json={"body": review})