# Quick Start Guide

## 5-Minute Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Examples (No Server Needed)
```bash
# Basic example
python EXAMPLES.py

# Advanced features demo
python ADVANCED_EXAMPLES.py
```

### 3. Start the Server
```bash
python run_server.py
```

Then visit: `http://localhost:8000/docs`

---

## Common Tasks

### Test Code Review Workflow
```python
from app.engine import WorkflowGraph
from app.workflows import extract_functions, check_complexity, detect_issues, suggest_improvements, finalize_review

# Create graph
graph = WorkflowGraph("review", "Code Review")
graph.add_node("extract", "Extract", extract_functions)
graph.add_node("check", "Check", check_complexity)  
graph.add_node("detect", "Detect", detect_issues)
graph.add_node("suggest", "Suggest", suggest_improvements)
graph.add_node("finalize", "Finalize", finalize_review)

# Connect
graph.add_edge("extract", "check")
graph.add_edge("check", "detect")
graph.add_edge("detect", "suggest")
graph.add_edge("suggest", "finalize")

# Run
graph.set_start_node("extract")
run = graph.execute({"code": "def hello(): pass"})

# See results
print(f"Quality: {run.final_state['quality_score']}")
print(f"Issues: {run.final_state['detected_issues']}")
```

### Create Custom Workflow
```python
from app.engine import WorkflowGraph

def my_step(state):
    return {"result": "done"}

graph = WorkflowGraph("my-graph", "My Workflow")
graph.add_node("step1", "My Step", my_step)
graph.set_start_node("step1")

run = graph.execute({"input": "data"})
print(run.final_state)
```

### Use the API
```bash
# Health check
curl http://localhost:8000/health

# List tools  
curl http://localhost:8000/tools

# Run code review
curl -X POST http://localhost:8000/workflows/code-review \
  -H "Content-Type: application/json" \
  -d '{"initial_state": {"code": "def hello(): pass"}}'
```

---

## Project Files

| File | Purpose |
|------|---------|
| `app/engine.py` | Core workflow engine |
| `app/main.py` | FastAPI server |
| `app/tools.py` | Tool registry |
| `app/database.py` | State persistence |
| `app/schemas.py` | Pydantic models |
| `app/workflows.py` | Code review workflow |
| `run_server.py` | Start server script |
| `EXAMPLES.py` | Basic usage examples |
| `ADVANCED_EXAMPLES.py` | Advanced features demo |
| `README.md` | Full documentation |
| `ASSIGNMENT_SUMMARY.md` | Assignment completion report |

---

## Troubleshooting

**Server won't start?**
- Check Python version: `python --version` (need 3.8+)
- Check dependencies: `pip list | grep fastapi`
- Try: `pip install -r requirements.txt --upgrade`

**Import errors?**
- Ensure you're in the `workflow-engine` directory
- Run: `python -c "from app import engine; print('OK')"`

**Examples fail?**
- Check Python path: `python -c "import sys; print(sys.path)"`
- Reinstall: `pip uninstall -y fastapi pydantic uvicorn && pip install -r requirements.txt`

---

## Next Steps

1. **Review Code**: Check `app/engine.py` for the main engine
2. **Understand API**: Visit http://localhost:8000/docs
3. **Try Examples**: Run `ADVANCED_EXAMPLES.py` to see features
4. **Build Custom**: Create your own workflows in `app/workflows.py`
5. **Deploy**: Add to Docker, use with gunicorn, etc.

---

## Key Features

✅ Graph-based workflow engine  
✅ Stateful execution with history  
✅ Tool registry for extensibility  
✅ FastAPI REST API with auto-docs  
✅ Code review workflow example  
✅ Error handling and recovery  
✅ Multiple execution models (linear, branching, loops)  
✅ Complete execution tracking  

See `README.md` for full documentation.
