# app/services/github_service.py
import httpx
import os

_DIFF_MARKER = "diff --git"

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def _looks_like_diff(text: str) -> bool:
    return _DIFF_MARKER in text


async def fetch_diff(diff_url: str) -> str:
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(diff_url, headers=HEADERS)
        if resp.status_code != 200:
            raise ValueError(f"Diff fetch failed: {resp.status_code}")
        diff_text = resp.text or ""
        if not _looks_like_diff(diff_text):
            raise ValueError("Diff fetch returned non-diff content")
        return diff_text

async def post_comment(repo: str, pr_number: int, review: str):
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    async with httpx.AsyncClient() as client:
        await client.post(url, headers=HEADERS, json={"body": review})