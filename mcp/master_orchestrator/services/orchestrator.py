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
import time
import uuid

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from agent_core.files import FilePayload
from agent_core.guardrails import (
    REFUSAL_INPUT,
    REFUSAL_OUTPUT,
    GuardrailsUnavailable,
    check_input,
    check_output,
)
from agent_core.llm import get_llm
from agent_core.ratelimit import RateLimited, RateLimiter
from master_orchestrator.config import settings
from master_orchestrator.services.files import FileService
from master_orchestrator.services.memory import get_store
from master_orchestrator.prompts.generator import PromptGenerator
from master_orchestrator.schemas.http import (
    GuardrailInfo,
    OrchestrateRequest,
    OrchestrationResult,
    SubTaskResult,
)
from master_orchestrator.services.subagents import SubagentToolset


TURN_TIMEOUT_CODE = "turn_timeout"
RATE_LIMITED_CODE = "rate_limited"

# Anonymous turns (no thread_id) share one bucket rather than each getting its own
# unbounded allowance (PLAN D3).
_ANONYMOUS_THREAD_KEY = "__anonymous__"
_GLOBAL_KEY = "__global__"

# Module-level, process-lifetime buckets (PLAN D3/D4): the storage backing them must
# persist across turns for the limit to mean anything, so they are not per-call state.
_thread_limiter = RateLimiter()
_global_limiter = RateLimiter()


class TurnTimeout(TimeoutError):
    """The turn outlived its own budget.

    Typed, because the caller must tell it from any other failure: this is the one
    outcome the UI answers with a retry the user can press, and matching on a message
    string is how that breaks the first time the wording changes.
    """


class Orchestrator:
    """Runs one orchestration turn: prompt in -> one merged answer out."""

    def __init__(self) -> None:
        self._files = FileService()
        self._deadline: float | None = None

    def _check_rate_limits(self, thread_id: str | None) -> None:
        """Reject an over-limit turn before any billable or stateful work (R2/R3).

        Two independent buckets, per-thread then process-global (PLAN D3): a caller
        that rotates thread_ids to dodge the first bucket still lands in the second.
        """
        thread_key = thread_id or _ANONYMOUS_THREAD_KEY
        if not _thread_limiter.hit(thread_key, settings.rate_limit_thread_rpm):
            raise RateLimited(
                _thread_limiter.retry_after_s(thread_key, settings.rate_limit_thread_rpm)
            )
        if not _global_limiter.hit(_GLOBAL_KEY, settings.rate_limit_global_rpm):
            raise RateLimited(
                _global_limiter.retry_after_s(_GLOBAL_KEY, settings.rate_limit_global_rpm)
            )

    async def run(self, request: OrchestrateRequest) -> OrchestrationResult:
        """Bound the turn, then run it.

        The rate-limit check (R2/R3/PLAN D4) runs first, before the budget clock starts
        and before `_run_turn` does anything: a rejected turn must never call the LLM,
        the guardrails gate, or touch the store, and it must never race the timeout
        (RK4 — inside `wait_for` a rejection could misreport as a timeout instead).

        The budget itself lives here rather than at the gateway because of what each
        layer can still do when it fires. The gateway's ceiling can only produce a
        transport error — by then there is no agent response left to shape. This one
        fires while a live code path still exists, so the turn can report *why* it ended.
        """
        self._check_rate_limits(request.thread_id)
        self._deadline = time.monotonic() + settings.turn_budget_s
        try:
            # `wait_for`, not `asyncio.timeout`: same cancellation semantics for a single
            # coroutine, and it does not require 3.11+ of anything that imports this.
            return await asyncio.wait_for(
                self._run_turn(request), timeout=settings.turn_budget_s
            )
        except (TimeoutError, asyncio.TimeoutError) as exc:
            raise TurnTimeout(
                f"the turn exceeded its {settings.turn_budget_s:g}s budget"
            ) from exc

    def _budget_spent(self) -> bool:
        """True once this turn has no time left to be doing anything, including saving."""
        return self._deadline is not None and time.monotonic() >= self._deadline

    async def _run_turn(self, request: OrchestrateRequest) -> OrchestrationResult:
        """Run one orchestration turn and return the merged answer.

        The agent owns thread_id generation and input validation (the gateway is a
        pure proxy): a missing thread_id is generated here and returned, and the
        attached file is validated before the loop runs.
        """
        self._files.validate(request.file)
        thread_id = request.thread_id or uuid.uuid4().hex

        store = await get_store()
        state = await store.load(thread_id)

        # --- input gate (TASK R6a, PLAN D5/D5a) -------------------------------------
        # Ordering matters and is asserted by test: the gate runs BEFORE anything is
        # persisted, so raw PII never reaches the checkpointer even though it would
        # never have reached the LLM either. Thread state is loaded first only because
        # the gate needs somewhere to record a held turn against.
        verdict = await check_input(
            request.prompt, source="orchestrator", surface="prompt", thread_id=thread_id
        )
        info = GuardrailInfo(
            redacted_types=verdict.redacted_types, notice=verdict.notice
        )
        if not verdict.allowed:
            info.blocked = True
            return await self._halt(store, thread_id, request, REFUSAL_INPUT, info)

        # From here on the redacted prompt is the only prompt. The original is dropped.
        prompt = verdict.text or request.prompt
        if verdict.notice:
            prompt = f"{prompt}\n\n{verdict.notice}"

        loaded = await SubagentToolset.load()
        model = get_llm().bind_tools(loaded.tools)

        # The PromptGenerator turns the payload into the turn's system prompts.
        messages: list[BaseMessage] = [
            SystemMessage(content=text)
            for text in PromptGenerator(request).system_messages()
        ]
        messages += self._rehydrate(state.messages)
        messages.append(HumanMessage(content=prompt))

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

        # --- output gate (TASK R6c, PLAN D6) ----------------------------------------
        out = await check_output(
            answer,
            source="orchestrator",
            thread_id=thread_id,
            known_pii_types=verdict.redacted_types,
        )
        if not out.allowed:
            info.blocked = True
            answer = REFUSAL_OUTPUT
        else:
            answer = out.text or answer

        # A turn that has lost its budget writes nothing (PLAN D20). The gateway has
        # already given up on it and the user may have pressed retry; a late writer would
        # append this turn's pair *after* the retry's, so the thread ends up holding two
        # answers to one question. Cancellation normally gets here first — this check is
        # what makes it true even when it does not.
        if self._budget_spent():
            raise TurnTimeout("budget spent before the turn could be persisted")

        # Only redacted text is ever persisted (PLAN D5a, R-5).
        user_message: dict[str, str | bool] = {"role": "user", "text": prompt}
        if request.is_retry:
            # Inert on the model-facing path: `_rehydrate` reads `role` and `text` only,
            # so a retried turn does not read to the model as the user asking twice.
            user_message["retry"] = True
        state.messages.append(user_message)  # type: ignore[arg-type]
        state.messages.append({"role": "assistant", "text": answer})
        await store.save(thread_id, state)
        return OrchestrationResult(
            prompt=prompt, answer=answer, thread_id=thread_id, results=results,
            guardrails=info,
        )

    async def _halt(
        self,
        store,
        thread_id: str,
        request: OrchestrateRequest,
        answer: str,
        info: GuardrailInfo,
    ) -> OrchestrationResult:
        """End the turn without running the loop: no LLM call is made (TASK R7).

        The offending prompt is never echoed and never stored — only the outcome is.
        """
        return OrchestrationResult(
            prompt="", answer=answer, thread_id=thread_id, results=[], guardrails=info
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
            output = str(await tool.ainvoke(args))
        except Exception as exc:  # noqa: BLE001 - fail soft across the sub-agent boundary
            return False, f"sub-agent error: {exc}"
        if call["name"] in loaded.untrusted_tool_names:
            return await self._gate_result(call["name"], output)
        return True, output

    async def _gate_result(self, tool_name: str, output: str) -> tuple[bool, str]:
        """Gate a sub-agent result on its way back into the model's context (PLAN D5).

        A poisoned result fails the **tool**, not the **turn** (D5a). Blocking the whole
        turn would hand any third party a denial of service on any user query whose
        search happens to reach a page they control; dropping one result degrades the
        answer instead, which is what the loop already handles for a failed sub-agent.

        Single-shot on purpose (D5b): the R6 ladder is the output path's. Inside the loop
        it would multiply the worst case by the iteration count, and an unreachable gate
        here costs one dropped source rather than an ungated one.
        """
        try:
            verdict = await check_input(
                output, source=f"orchestrator:{tool_name}", surface="tool_result"
            )
        except GuardrailsUnavailable:
            return False, f"{tool_name}: result discarded (the safety gate is unavailable)"
        if not verdict.allowed:
            # Deliberately not "violates policy": the gate also returns `blocked` when its
            # own model is unavailable (fail-closed), and a marker that names the wrong
            # cause is how an outage gets debugged as a false positive.
            return False, f"{tool_name}: result discarded (it did not pass the safety gate)"
        text = verdict.text
        # The gate returns untrusted text fenced; the note is what tells the model the
        # fence is data. Both are the gate's, forwarded unchanged.
        if verdict.system_note:
            text = f"{verdict.system_note}\n\n{text}"
        return True, text

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
