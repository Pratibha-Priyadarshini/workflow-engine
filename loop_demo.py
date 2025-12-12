"""
Enhanced workflow with proper looping demonstration for Code Review.
This demonstrates the full looping capability required by the assignment.
"""

from typing import Dict, Any
from app.engine import WorkflowGraph, NodeType
from app.workflows import (
    extract_functions, check_complexity, detect_issues, 
    suggest_improvements, finalize_review, loop_check
)


def create_code_review_with_loop() -> WorkflowGraph:
    """
    Create a code review workflow with proper looping.
    This demonstrates the loop requirement: "Loop until quality_score >= threshold"
    """
    graph = WorkflowGraph("code-review-loop", "Code Review with Loop")
    
    # Add all nodes
    graph.add_node("extract", "Extract Functions", extract_functions)
    graph.add_node("check_complexity", "Check Complexity", check_complexity)
    graph.add_node("detect_issues", "Detect Issues", detect_issues)
    graph.add_node("suggest_improvements", "Suggest Improvements", suggest_improvements)
    graph.add_node("finalize", "Finalize Review", finalize_review)
    
    # Add edges for linear flow
    graph.add_edge("extract", "check_complexity")
    graph.add_edge("check_complexity", "detect_issues")
    graph.add_edge("detect_issues", "suggest_improvements")
    
    # Add loop: if quality_score < threshold, go back to extract
    # Otherwise, go to finalize
    graph.set_loop(
        "suggest_improvements",
        loop_check,
        "extract"
    )
    
    # Normal flow after suggest_improvements (when loop condition is False)
    graph.add_edge("suggest_improvements", "finalize")
    
    graph.set_start_node("extract")
    
    return graph


def demonstrate_loop():
    """
    Demonstrate the looping capability.
    """
    print("\n" + "="*70)
    print("DEMONSTRATING LOOP FUNCTIONALITY")
    print("="*70)
    
    graph = create_code_review_with_loop()
    
    # Poor quality code that should trigger multiple iterations
    poor_code = '''
def calc(x):
    t = 0
    for i in x:
        if i > 100:
            t = t + i
    return t
'''
    
    initial_state = {
        "code": poor_code,
        "quality_threshold": 80,  # High threshold to trigger loop
        "iteration": 0
    }
    
    print(f"\nExecuting workflow with quality threshold: 80")
    print(f"Expected: Multiple iterations until quality improves\n")
    
    run = graph.execute(initial_state)
    
    print(f"Execution Results:")
    print(f"  - Total Steps: {len(run.execution_log)}")
    print(f"  - Iterations: {run.final_state.get('iteration', 0)}")
    print(f"  - Final Quality Score: {run.final_state.get('quality_score', 0)}")
    print(f"  - Review Completed: {run.final_state.get('review_completed', False)}")
    
    print(f"\nExecution Log:")
    for i, step in enumerate(run.execution_log, 1):
        print(f"  {i}. {step.node_id} - {step.status}")
    
    return run


if __name__ == "__main__":
    demonstrate_loop()
