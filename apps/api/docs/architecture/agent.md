# Agent Architecture

The TaskMate Agent is a multi-step orchestration engine that allows an LLM to interact with both the TaskMate workspace (tasks, projects, clients) and external integrations (GitHub) via native tool calling.

## Core Components

1. **AgentOrchestrator**: The central loop (`apps/api/app/agent/orchestrator.py`).
2. **ToolRegistry**: Explicit allowlist of tools (`apps/api/app/agent/tools/registry.py`).
3. **AgentTools**: Wrappers around internal services (`TaskService`) and external clients (`GitHubClient`).
4. **ToolPermissionService**: Validates ownership, scopes, and intercepts destructive/write actions for user approval.

## Flow

1. User sends prompt.
2. `AgentOrchestrator` builds minimal `WorkspaceContext`.
3. Orchestrator fetches allowed tools from `ToolRegistry`.
4. Orchestrator calls `AIProvider.generate()` with tools.
5. If LLM requests a tool:
   - Check permissions via `ToolPermissionService`.
   - If allowed, execute tool.
   - Record execution in DB.
   - Append tool result to context.
   - Loop back to step 4.
6. If LLM returns text, return to user.

