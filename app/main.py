"""
FastAPI application for the workflow engine.
Exposes REST endpoints for graph creation, execution, and monitoring.
"""

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.responses import JSONResponse
import uuid
from datetime import datetime
from typing import Optional
import sys
import os
import asyncio
import json

# Add the app directory to sys.path so relative imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine import WorkflowGraph, NodeType
from schemas import (
    CreateGraphRequest,
    GraphResponse,
    RunGraphRequest,
    WorkflowRunResponse,
    StateResponse,
    ErrorResponse,
    ExecutionStepResponse,
)
from database import get_db
from tools import get_global_registry, register_tool
from workflows import CODE_REVIEW_WORKFLOW, extract_functions, check_complexity, detect_issues, suggest_improvements, finalize_review


# Create FastAPI app
app = FastAPI(
    title="Workflow Engine API",
    description="A minimal workflow engine similar to LangGraph",
    version="1.0.0",
)

# In-memory storage for graphs
_graphs: dict = {}


# Register pre-built workflows and tools
def setup_workflows():
    """Initialize built-in workflows and tools."""
    db = get_db()
    
    # Register code review tools
    register_tool(
        "extract_functions",
        extract_functions,
        "Extracts function definitions from Python code",
        tags=["code-review"],
    )
    register_tool(
        "check_complexity",
        check_complexity,
        "Analyzes function complexity",
        tags=["code-review"],
    )
    register_tool(
        "detect_issues",
        detect_issues,
        "Detects common code quality issues",
        tags=["code-review"],
    )
    register_tool(
        "suggest_improvements",
        suggest_improvements,
        "Generates improvement suggestions",
        tags=["code-review"],
    )


setup_workflows()


# ==================== Graph Management Endpoints ====================

@app.post("/graph/create", response_model=GraphResponse)
async def create_graph(request: CreateGraphRequest):
    """
    Create a new workflow graph.
    
    Request body:
    - name: Name of the graph
    - nodes: List of node definitions
    - edges: List of edge connections
    - start_node: ID of the starting node
    - branches: Optional branching logic definitions
    - loops: Optional loop logic definitions
    
    Returns: graph_id
    """
    try:
        # Create graph instance
        graph_id = str(uuid.uuid4())
        graph = WorkflowGraph(graph_id, request.name)
        
        # Add nodes
        for node_def in request.nodes:
            # For built-in workflows, use pre-defined functions
            if request.name == "Code Review Mini-Agent":
                func_map = {
                    "extract": extract_functions,
                    "check_complexity": check_complexity,
                    "detect_issues": detect_issues,
                    "suggest_improvements": suggest_improvements,
                    "finalize": finalize_review,
                }
                func = func_map.get(node_def.id, lambda state: state)
            else:
                # For custom graphs, use identity function
                func = lambda state, node_id=node_def.id: {f"node_{node_id}_executed": True}
            
            graph.add_node(
                node_def.id,
                node_def.name,
                func,
                NodeType(node_def.node_type),
                node_def.metadata,
            )
        
        # Add edges
        for edge in request.edges:
            graph.add_edge(edge.from_node, edge.to_node)
        
        # Add branching logic if provided
        if request.branches:
            for branch_def in request.branches:
                # Create a simple branching function
                def create_branch_func(branches_dict):
                    def branch_func(state):
                        # Simple routing based on state
                        for key, target in branches_dict.items():
                            if state.get(key):
                                return key
                        return "default"
                    return branch_func
                
                branches_map = {
                    f"branch_{i}": branch_def.branches[key] 
                    for i, key in enumerate(branch_def.branches.keys())
                }
                # graph.set_branching(branch_def.node_id, create_branch_func(branch_def.branches), branch_def.branches)
        
        # Set start node
        graph.set_start_node(request.start_node)
        
        # Store graph
        _graphs[graph_id] = graph
        db = get_db()
        db.save_graph(graph_id, graph.to_dict())
        
        return GraphResponse(
            graph_id=graph_id,
            name=request.name,
            nodes=[node_def.id for node_def in request.nodes],
            edges={edge.from_node: edge.to_node for edge in request.edges},
            start_node=request.start_node,
            created_at=datetime.utcnow().isoformat(),
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating graph: {str(e)}")


@app.get("/graph/{graph_id}", response_model=GraphResponse)
async def get_graph(graph_id: str):
    """Get details of a specific graph."""
    db = get_db()
    graph_data = db.get_graph(graph_id)
    
    if not graph_data:
        raise HTTPException(status_code=404, detail=f"Graph '{graph_id}' not found")
    
    return GraphResponse(**graph_data)


@app.get("/graphs")
async def list_graphs():
    """List all available graphs."""
    db = get_db()
    return {"graphs": db.list_graphs()}


# ==================== Workflow Execution Endpoints ====================

@app.post("/graph/run", response_model=WorkflowRunResponse)
async def run_graph(request: RunGraphRequest):
    """
    Execute a workflow graph with the given initial state.
    
    Request body:
    - graph_id: ID of the graph to run
    - initial_state: Initial state dictionary
    
    Returns: WorkflowRun with execution log and final state
    """
    try:
        # Get graph
        graph = _graphs.get(request.graph_id)
        if not graph:
            raise HTTPException(status_code=404, detail=f"Graph '{request.graph_id}' not found")
        
        # Execute graph
        run = graph.execute(request.initial_state)
        
        # Save run to database
        db = get_db()
        db.save_run(run.run_id, {
            "run_id": run.run_id,
            "graph_id": run.graph_id,
            "state": run.state,
            "execution_log": [
                {
                    "node_id": step.node_id,
                    "timestamp": step.timestamp.isoformat(),
                    "input_state": step.input_state,
                    "output_state": step.output_state,
                    "status": step.status,
                    "error_message": step.error_message,
                }
                for step in run.execution_log
            ],
            "is_completed": run.is_completed,
            "final_state": run.final_state,
            "created_at": run.created_at.isoformat(),
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        })
        
        # Build response
        execution_log = [
            ExecutionStepResponse(
                node_id=step.node_id,
                timestamp=step.timestamp.isoformat(),
                input_state=step.input_state,
                output_state=step.output_state,
                status=step.status,
                error_message=step.error_message,
            )
            for step in run.execution_log
        ]
        
        return WorkflowRunResponse(
            run_id=run.run_id,
            graph_id=run.graph_id,
            state=run.state,
            execution_log=execution_log,
            is_completed=run.is_completed,
            final_state=run.final_state,
            created_at=run.created_at.isoformat(),
            completed_at=run.completed_at.isoformat() if run.completed_at else None,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running graph: {str(e)}")


@app.post("/graph/run/async")
async def run_graph_async(request: RunGraphRequest, background_tasks: BackgroundTasks):
    """
    Execute a workflow graph asynchronously in the background.
    This is an OPTIONAL feature demonstrating async capabilities.
    
    Request body:
    - graph_id: ID of the graph to run
    - initial_state: Initial state dictionary
    
    Returns: run_id immediately, execution happens in background
    """
    try:
        # Get graph
        graph = _graphs.get(request.graph_id)
        if not graph:
            raise HTTPException(status_code=404, detail=f"Graph '{request.graph_id}' not found")
        
        # Generate run ID
        run_id = str(uuid.uuid4())
        
        # Create placeholder run entry
        db = get_db()
        db.save_run(run_id, {
            "run_id": run_id,
            "graph_id": request.graph_id,
            "state": request.initial_state,
            "execution_log": [],
            "is_completed": False,
            "final_state": None,
            "created_at": datetime.utcnow().isoformat(),
            "completed_at": None,
        })
        
        # Execute in background
        async def execute_in_background():
            """Background task to execute the workflow."""
            try:
                # Execute graph
                run = graph.execute(request.initial_state)
                
                # Update database with results
                db.save_run(run.run_id, {
                    "run_id": run_id,
                    "graph_id": run.graph_id,
                    "state": run.state,
                    "execution_log": [
                        {
                            "node_id": step.node_id,
                            "timestamp": step.timestamp.isoformat(),
                            "input_state": step.input_state,
                            "output_state": step.output_state,
                            "status": step.status,
                            "error_message": step.error_message,
                        }
                        for step in run.execution_log
                    ],
                    "is_completed": run.is_completed,
                    "final_state": run.final_state,
                    "created_at": run.created_at.isoformat(),
                    "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                })
            except Exception as e:
                # Update with error status
                db.update_run(run_id, {
                    "is_completed": True,
                    "error": str(e)
                })
        
        # Add to background tasks
        background_tasks.add_task(execute_in_background)
        
        return {
            "run_id": run_id,
            "status": "accepted",
            "message": "Workflow execution started in background",
            "check_status_at": f"/graph/state/{run_id}"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting async execution: {str(e)}")


@app.get("/graph/state/{run_id}", response_model=StateResponse)
async def get_run_state(run_id: str):
    """
    Get the current state of a workflow run.
    
    Returns: Current state and completion status
    """
    db = get_db()
    run_data = db.get_run(run_id)
    
    if not run_data:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
    
    return StateResponse(
        run_id=run_id,
        graph_id=run_data["graph_id"],
        state=run_data["state"],
        is_completed=run_data["is_completed"],
    )


@app.get("/runs")
async def list_runs(graph_id: Optional[str] = Query(None)):
    """
    List all workflow runs, optionally filtered by graph_id.
    """
    db = get_db()
    runs = db.list_runs(graph_id)
    return {"runs": runs, "count": len(runs)}


# ==================== Tool Registry Endpoints ====================

@app.get("/tools")
async def list_tools():
    """List all available tools."""
    registry = get_global_registry()
    tools = registry.list_tools()
    return {"tools": tools, "count": len(tools)}


# ==================== Pre-built Workflows ====================

@app.post("/workflows/code-review", response_model=WorkflowRunResponse)
async def run_code_review(request: RunGraphRequest):
    """
    Run the built-in Code Review workflow.
    
    Initial state should contain:
    - code: Python code to review
    - quality_threshold: Quality score threshold (default: 75)
    """
    try:
        # Create graph from workflow definition
        graph_id = str(uuid.uuid4())
        graph = WorkflowGraph(graph_id, CODE_REVIEW_WORKFLOW["name"])
        
        # Add nodes
        for node_def in CODE_REVIEW_WORKFLOW["nodes"]:
            graph.add_node(
                node_def["id"],
                node_def["name"],
                node_def["func"],
            )
        
        # Add edges
        for from_node, to_node in CODE_REVIEW_WORKFLOW["edges"]:
            graph.add_edge(from_node, to_node)
        
        # Set start node
        graph.set_start_node(CODE_REVIEW_WORKFLOW["start_node"])
        
        # Set defaults in initial state
        initial_state = request.initial_state.copy()
        if "quality_threshold" not in initial_state:
            initial_state["quality_threshold"] = 75
        if "iteration" not in initial_state:
            initial_state["iteration"] = 0
        
        # Execute
        run = graph.execute(initial_state)
        
        # Save run
        db = get_db()
        db.save_run(run.run_id, {
            "run_id": run.run_id,
            "graph_id": graph_id,
            "state": run.state,
            "execution_log": [
                {
                    "node_id": step.node_id,
                    "timestamp": step.timestamp.isoformat(),
                    "input_state": step.input_state,
                    "output_state": step.output_state,
                    "status": step.status,
                    "error_message": step.error_message,
                }
                for step in run.execution_log
            ],
            "is_completed": run.is_completed,
            "final_state": run.final_state,
            "created_at": run.created_at.isoformat(),
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        })
        
        # Build response
        execution_log = [
            ExecutionStepResponse(
                node_id=step.node_id,
                timestamp=step.timestamp.isoformat(),
                input_state=step.input_state,
                output_state=step.output_state,
                status=step.status,
                error_message=step.error_message,
            )
            for step in run.execution_log
        ]
        
        return WorkflowRunResponse(
            run_id=run.run_id,
            graph_id=graph_id,
            state=run.state,
            execution_log=execution_log,
            is_completed=run.is_completed,
            final_state=run.final_state,
            created_at=run.created_at.isoformat(),
            completed_at=run.completed_at.isoformat() if run.completed_at else None,
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running code review: {str(e)}")


# ==================== Health Check ====================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# ==================== WebSocket for Real-time Execution Streaming (OPTIONAL) ====================

@app.websocket("/ws/graph/run/{graph_id}")
async def run_graph_websocket(websocket: WebSocket, graph_id: str):
    """
    WebSocket endpoint to stream execution logs in real-time.
    This is an OPTIONAL feature that demonstrates async capabilities.
    
    Usage:
        Connect to ws://localhost:8000/ws/graph/run/{graph_id}
        Send initial state as JSON
        Receive execution steps as they complete
    """
    await websocket.accept()
    
    try:
        # Receive initial state from client
        data = await websocket.receive_text()
        initial_state = json.loads(data)
        
        # Get graph
        graph = _graphs.get(graph_id)
        if not graph:
            await websocket.send_json({
                "error": f"Graph '{graph_id}' not found",
                "status": "error"
            })
            await websocket.close()
            return
        
        # Send start notification
        await websocket.send_json({
            "event": "started",
            "graph_id": graph_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Execute graph with streaming
        run_id = str(uuid.uuid4())
        current_node_id = graph.start_node
        state = initial_state.copy()
        execution_log = []
        step_count = 0
        max_steps = 100
        
        while current_node_id and step_count < max_steps:
            step_count += 1
            node = graph.nodes.get(current_node_id)
            
            if not node:
                break
            
            try:
                # Send step start event
                await websocket.send_json({
                    "event": "step_start",
                    "node_id": current_node_id,
                    "node_name": node.name,
                    "step": step_count,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # Execute node
                input_state = state.copy()
                result = node.func(state)
                
                if result:
                    state.update(result)
                
                # Send step complete event
                await websocket.send_json({
                    "event": "step_complete",
                    "node_id": current_node_id,
                    "node_name": node.name,
                    "step": step_count,
                    "state": state,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                execution_log.append({
                    "node_id": current_node_id,
                    "status": "completed",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # Get next node
                current_node_id = graph.get_next_node(current_node_id, state)
                
                # Small delay to make streaming visible
                await asyncio.sleep(0.1)
                
            except Exception as e:
                # Send error event
                await websocket.send_json({
                    "event": "step_error",
                    "node_id": current_node_id,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })
                break
        
        # Send completion event
        await websocket.send_json({
            "event": "completed",
            "run_id": run_id,
            "final_state": state,
            "total_steps": len(execution_log),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Save run to database
        db = get_db()
        db.save_run(run_id, {
            "run_id": run_id,
            "graph_id": graph_id,
            "state": state,
            "execution_log": execution_log,
            "is_completed": True,
            "final_state": state,
            "created_at": datetime.utcnow().isoformat(),
            "completed_at": datetime.utcnow().isoformat()
        })
        
    except WebSocketDisconnect:
        print(f"WebSocket client disconnected for graph {graph_id}")
    except Exception as e:
        await websocket.send_json({
            "error": str(e),
            "status": "error"
        })
    finally:
        await websocket.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
