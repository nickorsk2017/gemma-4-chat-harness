"""Streamable-HTTP transport for any FastMCP server in the fleet.

Two agents serve over HTTP — the orchestrator (the gateway dials it) and guardrails
(every other agent dials it) — and both hit the same wall: recent MCP python-SDK /
fastmcp versions ship a localhost-only Host allowlist (DNS-rebinding protection) that
421s in-docker calls like ``Host: mcp:8100``. The shims that get past it are
version-sensitive and must not exist in two copies that can drift apart, so they live
here, in the one distribution every agent already shares.

Safe in this deployment: these servers listen only on the internal docker network.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # fastmcp is every agent's dependency, but agent_core needs no runtime
    from fastmcp import FastMCP  # import of it — only the type.


class _NormalizeHostMiddleware:
    """Rewrite the ``Host`` header to ``localhost:<port>`` on http requests.

    fastmcp exposes no stable kwarg for the SDK's rebinding settings, so the header is
    normalized before the SDK's validation runs. This is the primary, version-independent
    defense; the two patches below are belt-and-suspenders.
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
    """Serves a FastMCP app over streamable-HTTP (path ``/mcp``)."""

    def __init__(
        self,
        mcp: "FastMCP",
        *,
        name: str,
        host: str,
        port: int,
        allowed_hosts: list[str] | None = None,
    ) -> None:
        self._mcp = mcp
        self._name = name
        self._host = host
        self._port = port
        self._allowed_hosts = list(allowed_hosts or [])

    def run(self) -> None:
        """Bind ``host:port`` and serve, applying the Host / rebinding shims."""
        import uvicorn  # fastmcp dependency
        from starlette.middleware import Middleware

        self._disable_sdk_rebinding_protection()
        self._extend_fastmcp_guard_hosts()
        middleware = [Middleware(_NormalizeHostMiddleware, port=self._port)]
        try:
            # fastmcp >= 3.x: `allowed_hosts` admits the docker service identity.
            app = self._mcp.http_app(
                allowed_hosts=list(self._allowed_hosts), middleware=middleware
            )
        except TypeError:
            # Older fastmcp (2.x) has no `allowed_hosts` kwarg; the SDK-level patch
            # above plus the Host normalizer cover the same 421.
            app = self._mcp.http_app(middleware=middleware)
        print(
            f"[{self._name}] serving streamable-HTTP on "
            f"http://{self._host}:{self._port}/mcp",
            flush=True,
        )
        uvicorn.run(app, host=self._host, port=self._port)

    def _disable_sdk_rebinding_protection(self) -> None:
        """Force-disable the MCP SDK's DNS-rebinding protection for this server.

        With protection enabled the SDK's allowlist has NO implicit localhost entries and
        answers 421 for any other Host. fastmcp constructs that middleware internally and
        exposes no stable setting, so the construction is pinned here.

        Best-effort: the SDK module path / signature can move between pinned versions, and
        a failure here must NOT crash startup — the Host normalizer is the real defense.
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
                f"[{self._name}] SDK rebinding-protection patch skipped ({exc!r}); "
                "relying on Host-normalizer middleware.",
                flush=True,
            )

    def _extend_fastmcp_guard_hosts(self) -> None:
        """Admit the docker service identity in fastmcp 3.x's own request guard.

        fastmcp >= 3 ships its own Host/Origin guard (separate from the SDK middleware)
        that answers 421 outside ``DEFAULT_HOSTS``. No-op on versions without it.
        """
        try:
            from fastmcp.server import http as fastmcp_http
        except ImportError:  # pragma: no cover
            return
        defaults = getattr(fastmcp_http, "DEFAULT_HOSTS", None)
        if defaults is None:
            return
        extra = [h for h in self._allowed_hosts if h not in tuple(defaults)]
        fastmcp_http.DEFAULT_HOSTS = tuple(defaults) + tuple(extra)
