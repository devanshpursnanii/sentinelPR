# app/agents/aggregator.py
from langchain_core.prompts import ChatPromptTemplate
from app.core.llm_factory import ainvoke_with_key_fallback
from app.models.schemas import AgentFinding

AGGREGATOR_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a lead engineer synthesizing a code review.
    You will receive findings from a Security Agent and a Code Quality Agent.
    Produce a single, clear, well-formatted GitHub PR comment in Markdown.
    
    Structure it as:
    ## Automated Code Review
    
    ### Security Analysis
    [security findings or ✅ No issues found]
    
    ### Code Quality Analysis  
    [quality findings or ✅ No issues found]
    
    ### Summary & Recommendations
    [brief overall summary, priority actions]
    
    ---
    *Reviewed by AI Code Review Bot*
    """),
    ("human", """Security findings: {security}
    
Quality findings: {quality}""")
])

async def run_aggregator(
    security: AgentFinding,
    quality: AgentFinding
) -> str:
    try:
        response = await ainvoke_with_key_fallback(AGGREGATOR_PROMPT, {
            "security": security.model_dump_json(indent=2),
            "quality": quality.model_dump_json(indent=2)
        })
        return response.content
    except Exception:
        return (
            "## Automated Code Review\n\n"
            "### Security Analysis\n"
            f"- Severity: {security.severity}\n"
            + "\n".join(f"- {item}" for item in security.findings)
            + "\n\n### Code Quality Analysis\n"
            f"- Severity: {quality.severity}\n"
            + "\n".join(f"- {item}" for item in quality.findings)
            + "\n\n### Summary & Recommendations\n"
            "- Agent failed to run\n"
            "- Try again later\n\n"
            "---\n*Reviewed by AI Code Review Bot*"
        )