"""
Tool registry module.
Manages registered tools that can be called by workflow nodes.
"""

from typing import Callable, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class Tool:
    """Represents a tool that can be called in a workflow."""
    name: str
    func: Callable
    description: str = ""
    tags: list = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

    def __call__(self, *args, **kwargs):
        """Allow tool to be called directly."""
        return self.func(*args, **kwargs)


class ToolRegistry:
    """
    Registry for managing tools available to workflow nodes.
    Tools are functions that perform specific operations.
    """

    def __init__(self):
        self.tools: Dict[str, Tool] = {}

    def register(
        self,
        name: str,
        func: Callable,
        description: str = "",
        tags: Optional[list] = None,
    ) -> None:
        """Register a new tool."""
        tool = Tool(
            name=name,
            func=func,
            description=description,
            tags=tags or [],
        )
        self.tools[name] = tool

    def unregister(self, name: str) -> None:
        """Unregister a tool."""
        if name in self.tools:
            del self.tools[name]

    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self.tools.get(name)

    def call(self, name: str, *args, **kwargs) -> Any:
        """Call a tool by name."""
        tool = self.get(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found in registry")
        return tool(*args, **kwargs)

    def list_tools(self) -> Dict[str, Dict[str, Any]]:
        """List all available tools with metadata."""
        return {
            name: {
                "description": tool.description,
                "tags": tool.tags,
            }
            for name, tool in self.tools.items()
        }

    def has_tool(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self.tools


# Global registry instance
_global_registry = ToolRegistry()


def get_global_registry() -> ToolRegistry:
    """Get the global tool registry."""
    return _global_registry


def register_tool(
    name: str,
    func: Callable,
    description: str = "",
    tags: Optional[list] = None,
) -> None:
    """Register a tool in the global registry."""
    _global_registry.register(name, func, description, tags)
