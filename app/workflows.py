"""
Code Review Mini-Agent Workflow
A sample workflow that demonstrates the workflow engine capabilities.

This workflow:
1. Extracts functions from code
2. Checks complexity
3. Detects basic issues
4. Suggests improvements
5. Loops until quality_score >= threshold
"""

from typing import Dict, Any
import re


def extract_functions(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract function definitions from code.
    Expects state to contain 'code' key.
    """
    code = state.get("code", "")
    
    # Simple regex to find function definitions
    pattern = r"def\s+(\w+)\s*\((.*?)\):"
    matches = re.finditer(pattern, code)
    
    functions = []
    for match in matches:
        func_name = match.group(1)
        params = match.group(2)
        functions.append({
            "name": func_name,
            "params": [p.strip() for p in params.split(",") if p.strip()],
        })
    
    return {
        "functions": functions,
        "function_count": len(functions),
        "extraction_done": True,
    }


def check_complexity(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check complexity of extracted functions.
    Estimates complexity based on lines of code and nesting.
    """
    functions = state.get("functions", [])
    code = state.get("code", "")
    
    complexity_scores = []
    
    for func in functions:
        func_name = func["name"]
        # Simple heuristic: count indentation levels and lines
        # In a real scenario, use AST analysis
        complexity = 1
        
        # Check for loops and conditionals in function body
        loop_count = code.count("for ") + code.count("while ")
        if_count = code.count("if ") + code.count("elif ")
        
        complexity += loop_count * 2 + if_count * 1
        
        complexity_scores.append({
            "function": func_name,
            "complexity_score": min(complexity, 10),  # Cap at 10
        })
    
    return {
        "complexity_scores": complexity_scores,
        "avg_complexity": sum(c["complexity_score"] for c in complexity_scores) / len(complexity_scores) if complexity_scores else 0,
        "complexity_check_done": True,
    }


def detect_issues(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect basic code quality issues.
    Checks for common anti-patterns.
    """
    code = state.get("code", "")
    issues = []
    
    # Check for magic numbers
    if re.search(r"= \d{2,}", code):
        issues.append("Magic numbers detected")
    
    # Check for long lines
    lines = code.split("\n")
    long_lines = [i for i, line in enumerate(lines) if len(line) > 100]
    if long_lines:
        issues.append(f"Long lines detected (lines: {long_lines})")
    
    # Check for missing docstrings
    func_count = code.count("def ")
    docstring_count = code.count('"""')
    if docstring_count < func_count:
        issues.append("Some functions lack docstrings")
    
    # Check for unused imports or variables
    imports = code.count("import ")
    if imports > 10:
        issues.append("Too many imports")
    
    return {
        "detected_issues": issues,
        "issue_count": len(issues),
        "issues_detected": True,
    }


def suggest_improvements(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate improvement suggestions based on detected issues.
    """
    complexity_scores = state.get("complexity_scores", [])
    issues = state.get("detected_issues", [])
    
    suggestions = []
    
    # Suggest based on complexity
    for score in complexity_scores:
        if score["complexity_score"] > 7:
            suggestions.append(
                f"Function '{score['function']}' has high complexity. Consider breaking it down."
            )
    
    # Suggest based on detected issues
    if "Magic numbers detected" in issues:
        suggestions.append("Define constants for magic numbers")
    
    if "Long lines detected" in issues:
        suggestions.append("Break down long lines for readability")
    
    if "Some functions lack docstrings" in issues:
        suggestions.append("Add docstrings to all functions")
    
    # Calculate quality score
    quality_score = 100
    quality_score -= len(issues) * 10
    quality_score -= state.get("avg_complexity", 0) * 5
    quality_score = max(quality_score, 0)
    
    return {
        "suggestions": suggestions,
        "quality_score": quality_score,
        "improvements_suggested": True,
    }


def loop_check(state: Dict[str, Any]) -> bool:
    """
    Check if we should loop back for another iteration.
    Returns True if quality_score < threshold.
    """
    quality_score = state.get("quality_score", 0)
    threshold = state.get("quality_threshold", 75)
    iteration = state.get("iteration", 0)
    max_iterations = 3  # Prevent infinite loops
    
    should_loop = quality_score < threshold and iteration < max_iterations
    
    if should_loop:
        state["iteration"] = iteration + 1
        # In real scenario, this would be feedback to improve code
        state["code"] = state["code"]  # Placeholder
    
    return should_loop


def finalize_review(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Finalize the code review.
    """
    quality_score = state.get("quality_score", 0)
    iteration = state.get("iteration", 0)
    
    return {
        "final_quality_score": quality_score,
        "review_completed": True,
        "iterations": iteration,
    }


# Workflow configuration
CODE_REVIEW_WORKFLOW = {
    "name": "Code Review Mini-Agent",
    "description": "Reviews code quality and suggests improvements",
    "nodes": [
        {
            "id": "extract",
            "name": "Extract Functions",
            "func": extract_functions,
        },
        {
            "id": "check_complexity",
            "name": "Check Complexity",
            "func": check_complexity,
        },
        {
            "id": "detect_issues",
            "name": "Detect Issues",
            "func": detect_issues,
        },
        {
            "id": "suggest_improvements",
            "name": "Suggest Improvements",
            "func": suggest_improvements,
        },
        {
            "id": "finalize",
            "name": "Finalize Review",
            "func": finalize_review,
        },
    ],
    "edges": [
        ("extract", "check_complexity"),
        ("check_complexity", "detect_issues"),
        ("detect_issues", "suggest_improvements"),
        ("suggest_improvements", "finalize"),
    ],
    "start_node": "extract",
}
