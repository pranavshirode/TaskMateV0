"""Unit tests for Agent Orchestrator and Tools."""

import pytest
from app.agent.tools.registry import create_default_registry
from app.agent.tools.base import ToolPermission

def test_registry_loads_all_tools():
    """Verify that the default registry contains all necessary tools."""
    registry = create_default_registry()
    
    assert registry.tool_count == 16, f"Expected 16 tools, got {registry.tool_count}"
    
    assert registry.get("task.create") is not None
    assert registry.get("task.create").permission == ToolPermission.WRITE
    
    assert registry.get("github.repository.get") is not None
    assert registry.get("github.repository.get").permission == ToolPermission.READ

def test_tool_definitions_format():
    """Verify tool definitions are correctly formatted for LLM."""
    registry = create_default_registry()
    definitions = registry.get_tool_definitions()
    
    assert len(definitions) == 16
    task_create = next(d for d in definitions if d.name == "task.create")
    assert "title" in task_create.parameters["properties"]
    assert "required" in task_create.parameters
    assert "title" in task_create.parameters["required"]

