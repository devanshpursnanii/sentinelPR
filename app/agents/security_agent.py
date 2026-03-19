# app/agents/security_agent.py
from langchain_core.prompts import ChatPromptTemplate
from app.core.llm_factory import ainvoke_with_key_fallback
from app.models.schemas import AgentFinding
from app.services.metrics_service import findings_counter, agent_errors
import json
import re

SECURITY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a senior application security engineer at a financial institution.
    Analyze the provided code diff for security vulnerabilities.
    
    Focus on:
    - SQL injection, XSS, CSRF vulnerabilities
    - Hardcoded secrets, API keys, passwords
    - Insecure dependencies or imports
    - Authentication/authorization issues
    - Sensitive data exposure
    - Input validation gaps
    
    Respond ONLY with valid JSON matching this schema:
    {{
        "severity": "critical|warning|info",
        "findings": ["finding1", "finding2"],
        "suggestions": ["fix1", "fix2"]
    }}
    If no issues found, return severity "info" with empty lists."""),
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

async def run_security_agent(diff: str) -> AgentFinding:
    try:
        response = await ainvoke_with_key_fallback(SECURITY_PROMPT, {"diff": diff})
        data = _safe_parse_agent_payload(response.content)
        
        # Track findings in Prometheus
        for _ in data["findings"]:
            findings_counter.labels(
                agent_name="security",
                severity=data["severity"]
            ).inc()
        
        return AgentFinding(
            agent="security",
            severity=data["severity"],
            findings=data["findings"],
            suggestions=data["suggestions"]
        )
    except Exception:
        agent_errors.labels(agent_name="security").inc()
        return AgentFinding(
            agent="security",
            severity="info",
            findings=["Agent failed to run"],
            suggestions=["Try again later"]
        )