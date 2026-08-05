"""guardrails — the single owner of content-safety and PII policy (TASK R1).

Callers (master_orchestrator, doc_analyzer) reach this service over HTTP and
forward its verdict; they never re-implement policy.
"""

__all__ = ["__version__"]
__version__ = "0.1.0"
