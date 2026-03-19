# app/agents/orchestrator.py
from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional
from app.agents.security_agent import run_security_agent
from app.agents.quality_agent import run_quality_agent
from app.agents.aggregator import run_aggregator
from app.models.schemas import AgentFinding
import asyncio

class ReviewState(TypedDict):
    diff: str
    security_result: Optional[AgentFinding]
    quality_result: Optional[AgentFinding]
    final_review: Optional[str]


def _fallback_finding(agent_name: str) -> AgentFinding:
    return AgentFinding(
        agent=agent_name,
        severity="info",
        findings=["Agent failed to run"],
        suggestions=["Try again later"],
    )

# Node: run both agents concurrently
async def parallel_review_node(state: ReviewState) -> ReviewState:
    security, quality = await asyncio.gather(
        run_security_agent(state["diff"]),
        run_quality_agent(state["diff"]),
        return_exceptions=True,
    )

    if isinstance(security, Exception):
        security = _fallback_finding("security")
    if isinstance(quality, Exception):
        quality = _fallback_finding("quality")

    return {
        **state,
        "security_result": security,
        "quality_result": quality
    }

# Node: aggregate results
async def aggregation_node(state: ReviewState) -> ReviewState:
    try:
        review = await run_aggregator(
            state["security_result"],
            state["quality_result"]
        )
    except Exception:
        review = (
            "## Automated Code Review\n\n"
            "### Summary & Recommendations\n"
            "- Agent failed to run\n"
            "- Try again later\n"
        )
    return {**state, "final_review": review}

# Build the graph
def build_graph():
    graph = StateGraph(ReviewState)
    graph.add_node("parallel_review", parallel_review_node)
    graph.add_node("aggregate", aggregation_node)
    graph.set_entry_point("parallel_review")
    graph.add_edge("parallel_review", "aggregate")
    graph.add_edge("aggregate", END)
    return graph.compile()

_graph = build_graph()

async def run_review(diff: str, repo: str, pr_number: int) -> str:
    result = await _graph.ainvoke({
        "diff": diff,
        "security_result": None,
        "quality_result": None,
        "final_review": None
    })
    return result["final_review"]