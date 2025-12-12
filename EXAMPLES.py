"""
Comprehensive example and documentation of the Workflow Engine API.
Shows how to use all major features and endpoints.
"""

# ============================================================================
# 1. DIRECT PYTHON API USAGE (for testing without server)
# ============================================================================

from app.engine import WorkflowGraph, NodeType
from app.workflows import extract_functions, check_complexity, detect_issues, suggest_improvements, finalize_review

# Create a simple workflow graph
graph = WorkflowGraph("example-review", "Code Review Workflow")

# Add nodes
graph.add_node("extract", "Extract Functions", extract_functions)
graph.add_node("check", "Check Complexity", check_complexity)
graph.add_node("detect", "Detect Issues", detect_issues)
graph.add_node("suggest", "Suggest Improvements", suggest_improvements)
graph.add_node("finalize", "Finalize Review", finalize_review)

# Add edges
graph.add_edge("extract", "check")
graph.add_edge("check", "detect")
graph.add_edge("detect", "suggest")
graph.add_edge("suggest", "finalize")

# Set start node
graph.set_start_node("extract")

# Execute the workflow
code_sample = '''
def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

def process_data(numbers):
    result = []
    for num in numbers:
        fib = calculate_fibonacci(num)
        result.append(fib)
    return result
'''

initial_state = {
    "code": code_sample,
    "quality_threshold": 70
}

run = graph.execute(initial_state)

# Display results
print("=== WORKFLOW EXECUTION RESULTS ===\n")
print(f"Run ID: {run.run_id}")
print(f"Completed: {run.is_completed}")
print(f"Total Steps: {len(run.execution_log)}\n")

print("Execution Log:")
for i, step in enumerate(run.execution_log, 1):
    print(f"  {i}. {step.node_id}: {step.status}")

print(f"\nFinal State Summary:")
print(f"  - Functions Found: {run.final_state.get('function_count', 0)}")
print(f"  - Quality Score: {run.final_state.get('quality_score', 0)}")
print(f"  - Issues Detected: {len(run.final_state.get('detected_issues', []))}")
print(f"  - Suggestions: {len(run.final_state.get('suggestions', []))}")

if run.final_state.get('detected_issues'):
    print(f"\n  Issues Found:")
    for issue in run.final_state['detected_issues']:
        print(f"    - {issue}")

if run.final_state.get('suggestions'):
    print(f"\n  Suggestions:")
    for suggestion in run.final_state['suggestions']:
        print(f"    - {suggestion}")


# ============================================================================
# 2. API EXAMPLES (when server is running)
# ============================================================================

"""
To test these endpoints, start the server:
    python run_server.py

Then use curl or any HTTP client:

1. CHECK HEALTH
   GET http://localhost:8000/health

2. LIST AVAILABLE TOOLS
   GET http://localhost:8000/tools

3. CREATE A CUSTOM GRAPH
   POST http://localhost:8000/graph/create
   Body:
   {
     "name": "Simple Pipeline",
     "nodes": [
       {"id": "step1", "name": "Step 1"},
       {"id": "step2", "name": "Step 2"}
     ],
     "edges": [
       {"from_node": "step1", "to_node": "step2"}
     ],
     "start_node": "step1"
   }

4. RUN A GRAPH
   POST http://localhost:8000/graph/run
   Body:
   {
     "graph_id": "<returned_graph_id>",
     "initial_state": {
       "input": "test data"
     }
   }

5. GET RUN STATE
   GET http://localhost:8000/graph/state/{run_id}

6. LIST ALL RUNS
   GET http://localhost:8000/runs

7. RUN CODE REVIEW WORKFLOW (built-in)
   POST http://localhost:8000/workflows/code-review
   Body:
   {
     "initial_state": {
       "code": "def hello(): pass",
       "quality_threshold": 75
     }
   }

8. GET INTERACTIVE DOCS
   Visit: http://localhost:8000/docs
"""


# ============================================================================
# 3. PYTHON HTTP CLIENT EXAMPLE
# ============================================================================

"""
import requests
import json

BASE_URL = "http://localhost:8000"

# Example: Run code review workflow
response = requests.post(
    f"{BASE_URL}/workflows/code-review",
    json={
        "initial_state": {
            "code": '''
def calculate_sum(numbers):
    total = 0
    for num in numbers:
        total += num
    return total
''',
            "quality_threshold": 70
        }
    }
)

if response.status_code == 200:
    result = response.json()
    print(f"Quality Score: {result['final_state']['quality_score']}")
    print(f"Issues: {result['final_state']['detected_issues']}")
    print(f"Suggestions: {result['final_state']['suggestions']}")
else:
    print(f"Error: {response.status_code}")
    print(response.json())
"""
