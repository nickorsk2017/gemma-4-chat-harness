"""The numbers the budget policy rests on, asserted where they are declared.

Its own module rather than an addition to the image suite: nothing here is async or
image-specific, and the module-level asyncio mark next door would apply to it wrongly.

Containment is read **per call**, never as a sum: one LLM attempt (30 s) or one gate
call (31 s) sits inside one turn (60 s), which sits inside the gateway request (66 s).
Adding the parts together assumes everything hangs at once, which is not the failure
this system is designed against.

One ladder is `attempts x GUARDRAILS_TIMEOUT_S` plus the flat gaps: 2 x 15 + 1 = 31.
Each assertion below is one term of that sum, so a test that fails names which term
moved.
"""

from __future__ import annotations

from agent_core import guardrails as gr

LADDER_S = 31.0


def _clear(monkeypatch) -> None:
    """Run against the code's own defaults, not this machine's environment."""
    for var in (
        "GUARDRAILS_RETRY_ATTEMPTS",
        "GUARDRAILS_TIMEOUT_S",
        "GUARDRAILS_RETRY_BASE_S",
        "GUARDRAILS_RETRY_FACTOR",
        "GUARDRAILS_OUTPUT_DEADLINE_S",
    ):
        monkeypatch.delenv(var, raising=False)


def test_ladder_defaults_produce_a_31_second_worst_case(monkeypatch):
    """The code defaults must equal the declared ones: `mcp/.env.example` is canonical.

    The docker-free stack sets no `GUARDRAILS_*` at all, so it runs on exactly these
    literals — a process that declares nothing has to behave like one that declares
    everything, or the stack the budget targets is the one it never reaches.
    """
    _clear(monkeypatch)

    attempts, per_attempt, base, factor = (
        gr._attempts(),
        gr._timeout(),
        gr._backoff_base(),
        gr._backoff_factor(),
    )
    gaps = sum(base * factor**i for i in range(attempts - 1))
    worst = attempts * per_attempt + gaps

    assert attempts == 2, "two attempts: one retry, for a gate that is coming back"
    assert factor == 1, "the gap is flat — with two attempts there is only one gap"
    assert worst == LADDER_S, f"one ladder is {worst}s, not the budgeted {LADDER_S}s"


def test_deadline_sits_above_a_full_ladder(monkeypatch):
    """A deadline below the ladder it bounds is not a guard, only a misleading number.

    The margin is deliberate: at exactly 31 s scheduling jitter would cut the second
    attempt short, which is the failure the deadline exists to prevent.
    """
    _clear(monkeypatch)
    assert gr._phase_deadline() > LADDER_S


def test_client_timeout_stays_above_the_gates_judge_budget(monkeypatch):
    """15 s is the gate's own 8 s judge plus transport, not a round number to shave.

    Below the judge's budget a healthy-but-thinking gate reads as an outage — which
    releases answers ungated on the output path and refuses prompts on the input one.
    """
    _clear(monkeypatch)
    assert gr._timeout() >= 15.0


def test_one_call_fits_the_turn_which_fits_the_gateway(monkeypatch):
    """Per-call containment (TASK R22): each single call, not the sum of the parts."""
    _clear(monkeypatch)
    from master_orchestrator.config import OrchestratorSettings

    fields = OrchestratorSettings.model_fields
    turn = fields["turn_budget_s"].default
    llm_attempt = 30.0  # LLM_REQUEST_TIMEOUT_S, declared in both stacks
    gateway = 66.0  # backend `orchestrator_timeout_s`

    assert LADDER_S < turn, "a gate call must fit inside the turn that makes it"
    assert llm_attempt < turn, "one model attempt must fit inside the turn"
    assert turn < gateway, (
        "the turn must end before the gateway gives up, or the timeout can only ever "
        "be reported as a transport error and the user gets no retry"
    )


def test_loop_bound_is_two():
    """Fewer model<->tool rounds is what makes a turn fit the ceiling at all."""
    from master_orchestrator.config import OrchestratorSettings

    # The declared default, not an instance: a stray local `.env` must not be able to
    # make this pass for the wrong reason.
    assert OrchestratorSettings.model_fields["max_tool_iterations"].default == 2
