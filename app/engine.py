"""
Core workflow engine module.
Defines the graph structure, nodes, execution logic, and state management.
"""

from typing import Callable, Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
import uuid
from datetime import datetime
import json


class NodeType(str, Enum):
    """Types of nodes in the workflow."""
    STANDARD = "standard"
    CONDITIONAL = "conditional"
    LOOP = "loop"


@dataclass
class ExecutionStep:
    """Represents a single step in workflow execution."""
    node_id: str
    timestamp: datetime
    input_state: Dict[str, Any]
    output_state: Dict[str, Any]
    status: str  # "completed", "failed", "skipped"
    error_message: Optional[str] = None


@dataclass
class Node:
    """Represents a node in the workflow graph."""
    id: str
    name: str
    func: Callable[[Dict[str, Any]], Dict[str, Any]]
    node_type: NodeType = NodeType.STANDARD
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowRun:
    """Represents an execution of a workflow."""
    run_id: str
    graph_id: str
    state: Dict[str, Any]
    execution_log: List[ExecutionStep] = field(default_factory=list)
    is_completed: bool = False
    final_state: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class WorkflowGraph:
    """
    The core workflow graph engine.
    Manages nodes, edges, and execution logic.
    """

    def __init__(self, graph_id: str, name: str = ""):
        self.graph_id = graph_id
        self.name = name
        self.nodes: Dict[str, Node] = {}
        self.edges: Dict[str, str] = {}  # From node_id -> to node_id
        self.branching_rules: Dict[str, Callable[[Dict[str, Any]], str]] = {}  # node_id -> condition function
        self.loop_conditions: Dict[str, Callable[[Dict[str, Any]], bool]] = {}  # node_id -> loop condition
        self.start_node: Optional[str] = None
        self.created_at = datetime.utcnow()

    def add_node(
        self,
        node_id: str,
        name: str,
        func: Callable[[Dict[str, Any]], Dict[str, Any]],
        node_type: NodeType = NodeType.STANDARD,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a node to the graph."""
        node = Node(
            id=node_id,
            name=name,
            func=func,
            node_type=node_type,
            metadata=metadata or {},
        )
        self.nodes[node_id] = node

    def add_edge(self, from_node_id: str, to_node_id: str) -> None:
        """Add an edge from one node to another."""
        if from_node_id not in self.nodes:
            raise ValueError(f"Source node '{from_node_id}' does not exist")
        if to_node_id not in self.nodes:
            raise ValueError(f"Target node '{to_node_id}' does not exist")
        self.edges[from_node_id] = to_node_id

    def set_branching(
        self,
        node_id: str,
        condition_func: Callable[[Dict[str, Any]], str],
        branches: Dict[str, str],
    ) -> None:
        """
        Set branching logic for a node.
        condition_func should return a key from branches dict.
        branches maps condition results to next node IDs.
        """
        if node_id not in self.nodes:
            raise ValueError(f"Node '{node_id}' does not exist")
        
        self.nodes[node_id].node_type = NodeType.CONDITIONAL
        self.branching_rules[node_id] = condition_func
        
        # Add edges for each branch
        for branch_key, next_node_id in branches.items():
            if next_node_id not in self.nodes:
                raise ValueError(f"Target node '{next_node_id}' does not exist")
            # Store as "{node_id}_{branch_key}" -> next_node_id for tracking
            self.edges[f"{node_id}_{branch_key}"] = next_node_id

    def set_loop(
        self,
        node_id: str,
        condition_func: Callable[[Dict[str, Any]], bool],
        loop_back_node_id: str,
    ) -> None:
        """
        Set loop logic for a node.
        If condition_func returns True, execution loops back to loop_back_node_id.
        """
        if node_id not in self.nodes:
            raise ValueError(f"Node '{node_id}' does not exist")
        if loop_back_node_id not in self.nodes:
            raise ValueError(f"Loop back node '{loop_back_node_id}' does not exist")
        
        self.nodes[node_id].node_type = NodeType.LOOP
        self.loop_conditions[node_id] = condition_func
        # Store the loop back target as a special edge
        self.edges[f"{node_id}_loop"] = loop_back_node_id

    def set_start_node(self, node_id: str) -> None:
        """Set the starting node for execution."""
        if node_id not in self.nodes:
            raise ValueError(f"Node '{node_id}' does not exist")
        self.start_node = node_id

    def get_next_node(self, current_node_id: str, state: Dict[str, Any]) -> Optional[str]:
        """
        Determine the next node to execute.
        Handles branching, looping, and linear flow.
        """
        node = self.nodes[current_node_id]

        # Handle looping (check this first)
        if current_node_id in self.loop_conditions:
            loop_func = self.loop_conditions[current_node_id]
            if loop_func(state):
                # Loop back to the specified node
                loop_target = self.edges.get(f"{current_node_id}_loop")
                if loop_target:
                    return loop_target

        # Handle branching
        if current_node_id in self.branching_rules:
            condition_func = self.branching_rules[current_node_id]
            branch_result = condition_func(state)
            branch_key = f"{current_node_id}_{branch_result}"
            return self.edges.get(branch_key)

        # Handle linear flow
        return self.edges.get(current_node_id)

    def execute(self, initial_state: Dict[str, Any], max_steps: int = 100) -> WorkflowRun:
        """
        Execute the workflow with the given initial state.
        Returns a WorkflowRun object containing final state and execution log.
        """
        if not self.start_node:
            raise ValueError("Start node not set. Call set_start_node() first.")

        run_id = str(uuid.uuid4())
        run = WorkflowRun(
            run_id=run_id,
            graph_id=self.graph_id,
            state=initial_state.copy(),
        )

        current_node_id = self.start_node
        step_count = 0

        while current_node_id and step_count < max_steps:
            step_count += 1
            node = self.nodes.get(current_node_id)

            if not node:
                break

            try:
                # Record input state
                input_state = run.state.copy()

                # Execute node function
                result = node.func(run.state)
                
                # Update state with result
                if result:
                    run.state.update(result)

                # Record execution step
                step = ExecutionStep(
                    node_id=current_node_id,
                    timestamp=datetime.utcnow(),
                    input_state=input_state,
                    output_state=run.state.copy(),
                    status="completed",
                )
                run.execution_log.append(step)

                # Determine next node
                current_node_id = self.get_next_node(current_node_id, run.state)

            except Exception as e:
                # Record failed step
                step = ExecutionStep(
                    node_id=current_node_id,
                    timestamp=datetime.utcnow(),
                    input_state=input_state,
                    output_state=run.state.copy(),
                    status="failed",
                    error_message=str(e),
                )
                run.execution_log.append(step)
                break

        # Mark execution as complete
        run.is_completed = True
        run.final_state = run.state.copy()
        run.completed_at = datetime.utcnow()

        return run

    def to_dict(self) -> Dict[str, Any]:
        """Serialize graph to dict (without functions)."""
        return {
            "graph_id": self.graph_id,
            "name": self.name,
            "nodes": list(self.nodes.keys()),
            "edges": self.edges,
            "start_node": self.start_node,
            "created_at": self.created_at.isoformat(),
        }
