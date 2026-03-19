# app/models/schemas.py
from pydantic import BaseModel
from typing import Optional

class ReviewRequest(BaseModel):
    diff: str
    repo: str
    pr_number: int

class AgentFinding(BaseModel):
    agent: str
    severity: str          # "critical", "warning", "info"
    findings: list[str]
    suggestions: list[str]

class ReviewResult(BaseModel):
    security: AgentFinding
    quality: AgentFinding
    summary: str