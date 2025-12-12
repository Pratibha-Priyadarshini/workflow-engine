"""
Database module for storing graphs and workflow runs.
Uses SQLite for simplicity and in-memory storage option.
"""

import json
from typing import Dict, Optional, Any, List
from datetime import datetime
from dataclasses import asdict

# Using simple in-memory storage for this assignment
class Database:
    """Simple in-memory database for graphs and runs."""

    def __init__(self):
        self.graphs: Dict[str, Dict[str, Any]] = {}
        self.runs: Dict[str, Dict[str, Any]] = {}

    # Graph operations
    def save_graph(self, graph_id: str, graph_data: Dict[str, Any]) -> None:
        """Save a graph."""
        self.graphs[graph_id] = {
            **graph_data,
            "saved_at": datetime.utcnow().isoformat(),
        }

    def get_graph(self, graph_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a graph."""
        return self.graphs.get(graph_id)

    def list_graphs(self) -> List[Dict[str, Any]]:
        """List all graphs."""
        return list(self.graphs.values())

    def delete_graph(self, graph_id: str) -> bool:
        """Delete a graph."""
        if graph_id in self.graphs:
            del self.graphs[graph_id]
            return True
        return False

    # Run operations
    def save_run(self, run_id: str, run_data: Dict[str, Any]) -> None:
        """Save a workflow run."""
        # Convert datetime objects to ISO format strings
        run_copy = dict(run_data)
        if "created_at" in run_copy and isinstance(run_copy["created_at"], datetime):
            run_copy["created_at"] = run_copy["created_at"].isoformat()
        if "completed_at" in run_copy and isinstance(run_copy["completed_at"], datetime):
            run_copy["completed_at"] = run_copy["completed_at"].isoformat()
        
        # Handle execution_log with datetime objects
        if "execution_log" in run_copy:
            execution_log = []
            for step in run_copy["execution_log"]:
                step_copy = dict(step)
                if isinstance(step_copy.get("timestamp"), datetime):
                    step_copy["timestamp"] = step_copy["timestamp"].isoformat()
                execution_log.append(step_copy)
            run_copy["execution_log"] = execution_log
        
        self.runs[run_id] = run_copy

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a workflow run."""
        return self.runs.get(run_id)

    def list_runs(self, graph_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all runs, optionally filtered by graph_id."""
        if graph_id:
            return [run for run in self.runs.values() if run.get("graph_id") == graph_id]
        return list(self.runs.values())

    def update_run(self, run_id: str, updates: Dict[str, Any]) -> bool:
        """Update a run."""
        if run_id not in self.runs:
            return False
        self.runs[run_id].update(updates)
        return True

    def delete_run(self, run_id: str) -> bool:
        """Delete a run."""
        if run_id in self.runs:
            del self.runs[run_id]
            return True
        return False


# Global database instance
_db = Database()


def get_db() -> Database:
    """Get the global database instance."""
    return _db
