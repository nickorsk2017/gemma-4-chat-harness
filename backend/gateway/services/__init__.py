"""Gateway proxy layer: the agent MCP client + the thin chat proxy service."""

from gateway.services.agent_client import (
    AgentClient,
    AgentOutcome,
    McpAgentClient,
    build_agent_client,
)
from gateway.services.chat_service import ChatService, GatewayError

__all__ = [
    "ChatService",
    "GatewayError",
    "AgentClient",
    "AgentOutcome",
    "McpAgentClient",
    "build_agent_client",
]
