"""Agent adapter abstraction for the governance pipeline (Phase 10.5).

`AgentAdapter` decouples the runtime from any specific backend. Implementations:
MockAgentAdapter (10.5.2), ClaudeCodeCliAdapter (10.5.10), and a stubbed
AnthropicApiAdapter. Every backend runs inside the same governed pipeline.
"""
