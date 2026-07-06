"""Planner: a LangChain structured-output chain that emits the sub-task plan.

Runs ``with_structured_output(Plan)`` over the planner prompt against the real
gemma model (no mock fallback — missing GEMMA_API_KEY raises LLMConfigError).
"""

from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from agent_core.llm import build_chat_model
from master_orchestrator.config import settings
from master_orchestrator.prompts.orchestrate import PLANNER_HUMAN, PLANNER_SYSTEM
from master_orchestrator.schemas.http import OrchestrateRequest
from master_orchestrator.schemas.plan import Plan, SubTask


def build_planner_chain() -> Runnable:
    """Build the planning chain: prompt -> chat model -> ``Plan``."""
    prompt = ChatPromptTemplate.from_messages(
        [("system", PLANNER_SYSTEM), ("human", PLANNER_HUMAN)]
    )
    model = build_chat_model(
        provider=settings.llm_provider,
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
    )
    return prompt | model.with_structured_output(Plan)


_chain: Runnable | None = None


async def plan(
    request: OrchestrateRequest, history: str = "", documents: str = ""
) -> list[SubTask]:
    """Split the request into parallel sub-tasks via the planning chain.

    ``history`` and ``documents`` are pre-formatted thread-memory summaries
    (recent conversation, stored document paths) so the planner can return an
    empty task list for follow-ups answerable from the thread.
    """
    global _chain
    if _chain is None:
        _chain = build_planner_chain()
    result: Plan = await _chain.ainvoke(
        {
            "prompt": request.prompt,
            "context": request.context,
            "history": history or "(empty)",
            "documents": documents or "(none)",
        }
    )
    return result.tasks
