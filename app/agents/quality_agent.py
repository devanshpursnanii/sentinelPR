# app/agents/quality_agent.py
from langchain_core.prompts import ChatPromptTemplate
from app.core.llm_factory import ainvoke_with_key_fallback
from app.models.schemas import AgentFinding
from app.services.metrics_service import findings_counter, agent_errors
import json
import re

QUALITY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a senior software engineer focused on code quality and maintainability.
    Analyze the provided code diff for quality issues.
    
    Focus on:
    - Code duplication and DRY violations
    - Missing error handling
    - Poor naming conventions
    - Overly complex functions (high cyclomatic complexity)
    - Missing or inadequate tests
    - Performance anti-patterns
    - Missing docstrings/comments on complex logic
    
    Respond ONLY with valid JSON matching this schema:
    {{
        "severity": "critical|warning|info",
        "findings": ["finding1", "finding2"],
        "suggestions": ["fix1", "fix2"]
    }}
    If code quality is good, return severity "info" with empty lists."""),
    ("human", "Review this diff:\n\n{diff}")
])


def _safe_parse_agent_payload(raw_content: str) -> dict:
    text = (raw_content or "").strip()
    if not text:
        raise ValueError("Empty model response")

    # Gemini may wrap JSON in markdown code fences.
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)

    data = json.loads(text)

    severity = str(data.get("severity", "info")).lower()
    if severity not in {"critical", "warning", "info"}:
        severity = "info"

    findings = data.get("findings", [])
    if not isinstance(findings, list):
        findings = [str(findings)]

    suggestions = data.get("suggestions", [])
    if not isinstance(suggestions, list):
        suggestions = [str(suggestions)]

    return {
        "severity": severity,
        "findings": [str(item) for item in findings],
        "suggestions": [str(item) for item in suggestions],
    }

async def run_quality_agent(diff: str) -> AgentFinding:
    try:
        response = await ainvoke_with_key_fallback(QUALITY_PROMPT, {"diff": diff})
        data = _safe_parse_agent_payload(response.content)
        
        for _ in data["findings"]:
            findings_counter.labels(
                agent_name="quality",
                severity=data["severity"]
            ).inc()
        
        return AgentFinding(
            agent="quality",
            severity=data["severity"],
            findings=data["findings"],
            suggestions=data["suggestions"]
        )
    except Exception:
        agent_errors.labels(agent_name="quality").inc()
        return AgentFinding(
            agent="quality",
            severity="info",
            findings=["Agent failed to run"],
            suggestions=["Try again later"]
        )