# app/services/github_service.py
import httpx
import os

_DIFF_MARKER = "diff --git"

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


def _auth_header() -> dict:
    if not GITHUB_TOKEN:
        return {}
    return {"Authorization": f"Bearer {GITHUB_TOKEN}"}


def _diff_headers() -> dict:
    return {
        **_auth_header(),
        "Accept": "application/vnd.github.v3.diff",
    }

def _looks_like_diff(text: str) -> bool:
    return _DIFF_MARKER in text


async def _fetch_diff_url(client: httpx.AsyncClient, diff_url: str) -> str:
    resp = await client.get(diff_url, headers=_diff_headers())
    if resp.status_code != 200:
        raise ValueError(f"Diff URL fetch failed: {resp.status_code}")
    diff_text = resp.text or ""
    if not _looks_like_diff(diff_text):
        raise ValueError("Diff URL returned non-diff content")
    return diff_text


async def _fetch_diff_api(client: httpx.AsyncClient, repo: str, pr_number: int) -> str:
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    resp = await client.get(url, headers=_diff_headers())
    if resp.status_code != 200:
        raise ValueError(f"PR API diff fetch failed: {resp.status_code}")
    diff_text = resp.text or ""
    if not _looks_like_diff(diff_text):
        raise ValueError("PR API returned non-diff content")
    return diff_text


async def fetch_diff(diff_url: str, repo: str, pr_number: int) -> str:
    last_error: Exception | None = None
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            return await _fetch_diff_url(client, diff_url)
        except Exception as exc:  # noqa: BLE001
            last_error = exc

        try:
            return await _fetch_diff_api(client, repo, pr_number)
        except Exception as exc:  # noqa: BLE001
            last_error = exc

    if last_error is not None:
        raise ValueError(str(last_error))
    raise ValueError("Diff fetch failed")

async def post_comment(repo: str, pr_number: int, review: str):
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    async with httpx.AsyncClient() as client:
        await client.post(url, headers={**_auth_header(), "Accept": "application/vnd.github.v3+json"}, json={"body": review})