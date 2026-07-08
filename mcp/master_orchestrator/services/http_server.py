"""Streamable-HTTP transport for the orchestrator MCP server.

The composed docker stack sets ``ORCHESTRATOR_TRANSPORT=streamable-http`` and binds
``0.0.0.0:8100`` so the gateway reaches the orchestrator at ``http://mcp:8100/mcp``.
Recent MCP python-SDK / fastmcp versions ship a localhost-only Host allowlist
(DNS-rebinding protection) that 421s in-docker calls (``Host: mcp:8100``); this
module owns the shims that admit the docker service identity. Safe here: the server
listens only on the internal docker network and the gateway is its sole client —
trust comes from network isolation.
"""

from __future__ import annotations

from fastmcp import FastMCP

from master_orchestrator.config import OrchestratorSettings


class _NormalizeHostMiddleware:
    """Rewrite the ``Host`` header to ``localhost:<port>`` on http requests.

    Recent MCP python-SDK versions enable DNS-rebinding protection with a
    localhost-only allowlist, so in-docker calls (``Host: mcp:8100``) are
    rejected with ``421 Misdirected Request``. fastmcp exposes no stable kwarg
    for those settings, so we normalize the header before the SDK's validation
    runs. Safe here: this server listens only on the internal docker network and
    the gateway is its sole client — trust comes from network isolation.
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


class HttpServer:
    """Serves a FastMCP app over streamable-HTTP (path ``/mcp``) for the stack."""

    def __init__(self, mcp: FastMCP, settings: OrchestratorSettings) -> None:
        self._mcp = mcp
        self._settings = settings

    def run(self) -> None:
        """Bind ``http_host:http_port`` and serve, applying the Host / rebinding shims.

        Binds ``http_host:http_port`` (0.0.0.0:8100 in docker) so the gateway can
        reach the orchestrator at ``http://mcp:8100/mcp``, and applies the Host /
        DNS-rebinding shims so in-network calls don't 421.
        """
        import uvicorn  # fastmcp dependency
        from starlette.middleware import Middleware

        self._disable_sdk_rebinding_protection()
        self._extend_fastmcp_guard_hosts()
        middleware = [Middleware(_NormalizeHostMiddleware, port=self._settings.http_port)]
        try:
            # fastmcp >= 3.x: `allowed_hosts` admits the docker service identity.
            app = self._mcp.http_app(
                allowed_hosts=list(self._settings.http_allowed_hosts),
                middleware=middleware,
            )
        except TypeError:
            # Older fastmcp (2.x) has no `allowed_hosts` kwarg; the SDK-level patch
            # above plus the Host normalizer cover the same 421.
            app = self._mcp.http_app(middleware=middleware)
        print(
            f"[orchestrator] serving streamable-HTTP on "
            f"http://{self._settings.http_host}:{self._settings.http_port}/mcp",
            flush=True,
        )
        uvicorn.run(app, host=self._settings.http_host, port=self._settings.http_port)

    @staticmethod
    def _disable_sdk_rebinding_protection() -> None:
        """Force-disable the MCP SDK's DNS-rebinding protection for this server.

        The SDK's ``TransportSecurityMiddleware`` answers 421 for any ``Host`` not on
        its allowlist, and with protection enabled the allowlist has NO implicit
        localhost entries. fastmcp constructs that middleware internally and exposes
        no stable setting for it, so we pin the construction here: every instance
        gets ``enable_dns_rebinding_protection=False``. Deliberate for this
        deployment — the orchestrator listens only on the internal docker network and
        the gateway is its sole client.

        Best-effort: the SDK module path / signature can move between pinned versions
        (root CLAUDE.md tracks latest stable). A failure here must NOT crash startup —
        the ``_NormalizeHostMiddleware`` rewrite (Host -> localhost:<port>) is the
        primary, version-independent defense; this patch is belt-and-suspenders.
        """
        try:
            from mcp.server import transport_security as ts

            original_init = ts.TransportSecurityMiddleware.__init__

            def patched_init(self, settings=None):  # noqa: ANN001 - SDK signature
                original_init(
                    self,
                    ts.TransportSecuritySettings(enable_dns_rebinding_protection=False),
                )

            ts.TransportSecurityMiddleware.__init__ = patched_init
        except Exception as exc:  # noqa: BLE001 - never let a shim sink the server
            print(
                f"[orchestrator] SDK rebinding-protection patch skipped ({exc!r}); "
                "relying on Host-normalizer middleware.",
                flush=True,
            )

    def _extend_fastmcp_guard_hosts(self) -> None:
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
        extra = [
            h for h in self._settings.http_allowed_hosts if h not in tuple(defaults)
        ]
        fastmcp_http.DEFAULT_HOSTS = tuple(defaults) + tuple(extra)
