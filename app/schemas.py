"""
Pydantic models for API request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime


class NodeDefinition(BaseModel):
    """Definition of a node for graph creation."""
    id: str
    name: str
    node_type: str = "standard"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EdgeDefinition(BaseModel):
    """Definition of an edge between two nodes."""
    from_node: str
    to_node: str


class BranchDefinition(BaseModel):
    """Definition of branching logic for a conditional node."""
    node_id: str
    branches: Dict[str, str]  # branch_name -> target_node_id


class LoopDefinition(BaseModel):
    """Definition of loop logic for a loop node."""
    node_id: str
    loop_back_node_id: str


class CreateGraphRequest(BaseModel):
    """Request to create a new graph."""
    name: str
    nodes: List[NodeDefinition]
    edges: List[EdgeDefinition]
    start_node: str
    branches: Optional[List[BranchDefinition]] = None
    loops: Optional[List[LoopDefinition]] = None


class GraphResponse(BaseModel):
    """Response containing graph information."""
    graph_id: str
    name: str
    nodes: List[str]
    edges: Dict[str, str]
    start_node: str
    created_at: str


class RunGraphRequest(BaseModel):
    """Request to run a graph."""
    graph_id: str
    initial_state: Dict[str, Any] = Field(default_factory=dict)


class WorkflowRequest(BaseModel):
    """Request to run a pre-defined workflow."""
    initial_state: Dict[str, Any] = Field(default_factory=dict)


class ExecutionStepResponse(BaseModel):
    """Response containing a single execution step."""
    node_id: str
    timestamp: str
    input_state: Dict[str, Any]
    output_state: Dict[str, Any]
    status: str
    error_message: Optional[str] = None


class WorkflowRunResponse(BaseModel):
    """Response containing workflow run results."""
    run_id: str
    graph_id: str
    state: Dict[str, Any]
    execution_log: List[ExecutionStepResponse]
    is_completed: bool
    final_state: Optional[Dict[str, Any]]
    created_at: str
    completed_at: Optional[str]


class StateResponse(BaseModel):
    """Response containing current state of a run."""
    run_id: str
    graph_id: str
    state: Dict[str, Any]
    is_completed: bool


class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str
    status_code: int
