"""The Gemma tool-calling loop: the model routes, the orchestrator dispatches.

The shared agent_core LLM is bound the sub-agents' tools; the model decides which
to call. Requested tools run concurrently and fail soft — a failing sub-agent is
captured as an error result and never sinks the run.

The orchestrator does NOT process the attached file. When a file is present it
announces its kind (Document or Image) so the model routes to the right tool, and
injects the raw base64 file into that tool's args at dispatch. The model never
carries the file bytes.
"""

from __future__ import annotations

import asyncio
import uuid

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from agent_core.files import FilePayload
from agent_core.llm import get_llm
from master_orchestrator.config import settings
from master_orchestrator.services.files import FileService
from master_orchestrator.services.memory import get_store
from master_orchestrator.prompts.generator import PromptGenerator
from master_orchestrator.schemas.http import (
    OrchestrateRequest,
    OrchestrationResult,
    SubTaskResult,
)
from master_orchestrator.services.subagents import SubagentToolset


class Orchestrator:
    """Runs one orchestration turn: prompt in -> one merged answer out."""

    def __init__(self) -> None:
        self._files = FileService()

    async def run(self, request: OrchestrateRequest) -> OrchestrationResult:
        """Run one orchestration turn and return the merged answer.

        The agent owns thread_id generation and input validation (the gateway is a
        pure proxy): a missing thread_id is generated here and returned, and the
        attached file is validated before the loop runs.
        """
        self._files.validate(request.file)
        thread_id = request.thread_id or uuid.uuid4().hex

        store = await get_store()
        state = await store.load(thread_id)

        loaded = await SubagentToolset.load()
        model = get_llm().bind_tools(loaded.tools)

        # The PromptGenerator turns the payload into the turn's system prompts.
        messages: list[BaseMessage] = [
            SystemMessage(content=text)
            for text in PromptGenerator(request).system_messages()
        ]
        messages += self._rehydrate(state.messages)
        messages.append(HumanMessage(content=request.prompt))

        results: list[SubTaskResult] = []
        answer = ""
        for _ in range(settings.max_tool_iterations):
            ai: AIMessage = await model.ainvoke(messages)
            messages.append(ai)
            if not ai.tool_calls:
                answer = self._text(ai.content)
                break
            
            outcomes = await asyncio.gather(
                *(self._dispatch(call, loaded, request.file) for call in ai.tool_calls)
            )
            for call, (ok, output) in zip(ai.tool_calls, outcomes):
                results.append(SubTaskResult(tool=call["name"], ok=ok, output=output))
                messages.append(ToolMessage(content=output, tool_call_id=call["id"]))
        else:
            # Iterations exhausted with the model still wanting tools: force a final
            # text answer from what it has gathered.
            answer = self._text((await get_llm().ainvoke(messages)).content)

        state.messages.append({"role": "user", "text": request.prompt})
        state.messages.append({"role": "assistant", "text": answer})
        await store.save(thread_id, state)
        return OrchestrationResult(
            prompt=request.prompt, answer=answer, thread_id=thread_id, results=results
        )

    async def _dispatch(
        self, call: dict, loaded: SubagentToolset, file: FilePayload | None
    ) -> tuple[bool, str]:
        """Execute one tool call, fail-soft, injecting the raw file when needed."""
        tool = loaded.by_name.get(call["name"])
        if tool is None:
            return False, f"unknown tool {call['name']!r}"
        args = dict(call.get("args") or {})
        if call["name"] in loaded.file_tool_names:
            self._files.inject(args, file)
        try:
            return True, str(await tool.ainvoke(args))
        except Exception as exc:  # noqa: BLE001 - fail soft across the sub-agent boundary
            return False, f"sub-agent error: {exc}"

    def _rehydrate(self, history: list[dict[str, str]]) -> list[BaseMessage]:
        out: list[BaseMessage] = []
        for m in history:
            if m["role"] == "user":
                out.append(HumanMessage(content=m["text"]))
            else:
                out.append(AIMessage(content=m["text"]))
        return out

    def _text(self, content: object) -> str:
        """Flatten LangChain message content (str or list of blocks) to text."""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "".join(
                block.get("text", "") if isinstance(block, dict) else str(block)
                for block in content
            )
        return str(content)
