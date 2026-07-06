"""master_orchestrator MCP server entry point."""

from __future__ import annotations
import os
from fastmcp import FastMCP
from master_orchestrator.config import settings


def _export_langsmith_env() -> None:
    """Export LangSmith settings so LangChain/LangGraph auto-trace runs (R6)."""
    if not settings.langsmith_tracing:
        return
    os.environ["LANGSMITH_TRACING"] = "true"
    if settings.langsmith_api_key:
        os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project


_export_langsmith_env()

from master_orchestrator.tools import orchestrate_tools  # noqa: E402 — after tracing env

mcp = FastMCP("master_orchestrator")
orchestrate_tools.register(mcp)


class _NormalizeHostMiddleware:
    """Rewrite the ``Host`` header to ``localhost:<port>`` on http requests.

    Recent MCP python-SDK versions enable DNS-rebinding protection with a
    localhost-only allowlist, so in-docker calls (``Host: mcp:8100``) are
    rejected with ``421 Misdirected Request``. fastmcp exposes no stable
    kwarg for those settings, so we normalize the header before the SDK's
    validation runs. Safe here: this server listens only on the internal
    docker network and the gateway is its sole client — trust comes from
    network isolation, not Host matching.
    """

    def __init__(self, app, port: int) -> None:
        self._app = app
        self._host = f"localhost:{port}".encode()

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            headers = [(k, v) for k, v in scope.get("headers", []) if k != b"host"]
            headers.append((b"host", self._host))
            scope = {**scope, "headers": headers}
        await self._app(scope, receive, send)


def _disable_sdk_rebinding_protection() -> None:
    """Force-disable the MCP SDK's DNS-rebinding protection for this server.

    The SDK's ``TransportSecurityMiddleware`` answers 421 for any ``Host`` not
    on its allowlist, and with protection enabled the allowlist has NO implicit
    localhost entries — it is whatever the embedding framework passes. fastmcp
    constructs that middleware internally and exposes no stable setting for it,
    so we pin the construction here: every instance gets
    ``enable_dns_rebinding_protection=False``. Deliberate for this deployment:
    the orchestrator listens only on the internal docker network and the
    gateway is its sole client — trust comes from network isolation.
    """
    from mcp.server import transport_security as ts

    original_init = ts.TransportSecurityMiddleware.__init__

    def patched_init(self, settings=None):  # noqa: ANN001 - SDK signature
        original_init(
            self,
            ts.TransportSecuritySettings(enable_dns_rebinding_protection=False),
        )

    ts.TransportSecurityMiddleware.__init__ = patched_init


def _extend_fastmcp_guard_hosts() -> None:
    """Admit the docker service identity in fastmcp 3.x's own request guard.

    fastmcp >= 3 ships its own Host/Origin guard in ``fastmcp.server.http``
    (separate from the MCP SDK middleware) that answers 421 for hosts outside
    ``DEFAULT_HOSTS`` + configured extras. Extending ``DEFAULT_HOSTS`` here
    guarantees ``Host: mcp:8100`` passes even when the installed ``http_app``
    doesn't expose the ``allowed_hosts`` kwarg. No-op on versions without it.
    """
    try:
        from fastmcp.server import http as fastmcp_http
    except ImportError:  # pragma: no cover
        return
    defaults = getattr(fastmcp_http, "DEFAULT_HOSTS", None)
    if defaults is None:
        return
    extra = [h for h in settings.http_allowed_hosts if h not in tuple(defaults)]
    fastmcp_http.DEFAULT_HOSTS = tuple(defaults) + tuple(extra)


def _run_http() -> None:
    """Serve over streamable-HTTP (path ``/mcp``) for the composed stack."""
    import uvicorn  # fastmcp dependency
    from starlette.middleware import Middleware

    _disable_sdk_rebinding_protection()
    _extend_fastmcp_guard_hosts()
    middleware = [Middleware(_NormalizeHostMiddleware, port=settings.http_port)]
    try:
        # fastmcp >= 3.x: its own request guard answers 421 for unknown Host
        # values; `allowed_hosts` is the supported way to admit the docker
        # service identity (`mcp:8100`) the gateway dials.
        app = mcp.http_app(
            allowed_hosts=list(settings.http_allowed_hosts), middleware=middleware
        )
    except TypeError:
        # Older fastmcp (2.x) has no `allowed_hosts` kwarg; there the SDK-level
        # patch above plus the Host normalizer cover the same 421.
        app = mcp.http_app(middleware=middleware)
    uvicorn.run(app, host=settings.http_host, port=settings.http_port)


def main() -> None:
    if settings.transport in ("http", "streamable-http"):
        _run_http()
    else:
        mcp.run(transport=settings.transport)


if __name__ == "__main__":
    main()
