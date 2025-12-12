# Workflow Engine - Minimal LangGraph Implementation

A lightweight Python workflow engine with state management, tool registry, and FastAPI endpoints.

## What This Engine Does

This is a simplified workflow system that enables:
- **Define workflows** with nodes (Python functions) and edges (connections)
- **Manage shared state** flowing through the workflow
- **Support branching** (conditional routing) and **looping** (repeat until condition)
- **Register tools** for reuse across workflows
- **Execute workflows** via clean REST API
- **Track execution logs** with complete state history

## How to Run

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Server
```bash
python run_server.py
```

### 3. Access the API
- **Interactive Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Core Features

### Workflow Engine
- ✅ Nodes (Python functions that process state)
- ✅ State (dictionary flowing between nodes)
- ✅ Edges (node connections in execution order)
- ✅ Branching (conditional routing to different nodes)
- ✅ Looping (repeat nodes until condition met)
- ✅ Error handling and execution logging

### API Endpoints
- `POST /graph/create` - Create workflow from JSON definition
- `POST /graph/run` - Execute workflow with initial state
- `GET /graph/state/{run_id}` - Check execution status
- `POST /workflows/code-review` - Built-in code review workflow
- `GET /health` - Health check

### Tool Registry
- Register Python functions as reusable tools
- Discover available tools via API
- Call tools by name from workflows

### Example Workflow: Code Review Agent
The implementation includes a complete Code Review workflow that:
1. Extracts function definitions from code
2. Analyzes complexity
3. Detects quality issues
4. Suggests improvements
5. Loops until quality threshold is met

## Code Structure

```
app/
├── engine.py      # Core graph execution engine
├── main.py        # FastAPI application
├── tools.py       # Tool registry system
├── database.py    # In-memory storage
├── schemas.py     # Pydantic validation models
├── workflows.py   # Code review workflow example
└── __init__.py    # Package initialization
```

## Usage Examples

### Run via Python
```python
from app.engine import WorkflowGraph
from app.workflows import extract_functions, check_complexity

graph = WorkflowGraph("review", "Code Review")
graph.add_node("extract", "Extract", extract_functions)
graph.add_node("check", "Check", check_complexity)
graph.add_edge("extract", "check")
graph.set_start_node("extract")

run = graph.execute({"code": "def hello(): pass"})
print(run.final_state)
```

### Run via REST API
```bash
curl -X POST http://localhost:8000/workflows/code-review \
  -H "Content-Type: application/json" \
  -d '{
    "initial_state": {
      "code": "def hello(): pass",
      "quality_threshold": 75
    }
  }'
```

## Architecture Decisions

1. **Function-Based Nodes** - Nodes are simple Python functions. Keeps the engine lightweight and flexible.
2. **Dictionary State** - State is a plain dictionary flowing through nodes. Can be extended to Pydantic models.
3. **In-Memory Storage** - Simple dict-based storage for speed. Easy to replace with database.
4. **Separate Tool Registry** - Tools are decoupled from the engine for flexibility.
5. **Minimal Dependencies** - Only FastAPI, Pydantic, and Uvicorn needed.

## What Would Improve with More Time

### High Priority
1. **Async Execution** - Use asyncio for non-blocking node execution
2. **WebSocket Support** - Stream execution logs in real-time
3. **Persistent Database** - SQLite/PostgreSQL instead of in-memory
4. **Graph Visualization** - Visual representation of workflows

### Medium Priority
5. **Better Error Handling** - More granular exception types
6. **Comprehensive Logging** - Structured JSON logging
7. **State Validation** - Pydantic models for state validation
8. **Unit Tests** - Full test suite with pytest

### Lower Priority
9. **Parallel Execution** - Run independent nodes concurrently
10. **Subgraph Support** - Embed workflows within other workflows
11. **Performance Metrics** - Track execution time and bottlenecks
12. **Config Management** - Environment-based configuration

## Example: Looping in Action

Run the looping demonstration:
```bash
python loop_demo.py
```

This shows the workflow repeating the code review pipeline until the quality score meets the threshold.

## Testing

Try the interactive API at: **http://localhost:8000/docs**

Or use the provided examples:
```bash
python EXAMPLES.py
```

---

**Implementation Summary**:
- Clean Python code with clear structure
- State flows through nodes as dictionaries
- Transitions handled via edges and branching logic
- Looping supported via condition functions
- RESTful API for easy integration
- Minimal dependencies for simplicity
