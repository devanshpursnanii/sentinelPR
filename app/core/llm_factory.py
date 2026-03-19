import os
from typing import Any

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI


load_dotenv()


def get_google_api_keys() -> list[str]:
    raw_keys = os.getenv("GOOGLE_API_KEYS", "").strip()
    if raw_keys:
        resolved: list[str] = []
        for item in raw_keys.split(","):
            token = item.strip()
            if not token:
                continue
            if token in os.environ:
                env_value = os.getenv(token, "").strip()
                if env_value:
                    resolved.append(env_value)
            else:
                # Allows direct key values in GOOGLE_API_KEYS if desired.
                resolved.append(token)
        if resolved:
            return resolved

    numbered_keys: list[str] = []
    for index in range(1, 11):
        key_value = os.getenv(f"GOOGLE_API_KEY{index}", "").strip()
        if key_value:
            numbered_keys.append(key_value)
    if numbered_keys:
        return numbered_keys

    single_key = os.getenv("GOOGLE_API_KEY", "").strip()
    return [single_key] if single_key else []


def _build_llm(api_key: str, model: str, temperature: float) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=model,
        temperature=temperature,
        google_api_key=api_key,
    )


async def ainvoke_with_key_fallback(
    prompt: Any,
    payload: dict[str, Any],
    *,
    model: str = "gemini-2.5-flash-lite",
    temperature: float = 0,
):
    keys = get_google_api_keys()
    if not keys:
        raise RuntimeError("No Gemini API keys are configured")

    # Requirement: first key, then retry once with next key.
    keys_to_try = keys[:2] if len(keys) > 1 else keys
    last_error: Exception | None = None

    for key in keys_to_try:
        try:
            llm = _build_llm(key, model=model, temperature=temperature)
            chain = prompt | llm
            return await chain.ainvoke(payload)
        except Exception as exc:  # noqa: BLE001
            last_error = exc

    if last_error is not None:
        raise last_error
    raise RuntimeError("LLM invocation failed with unknown error")
