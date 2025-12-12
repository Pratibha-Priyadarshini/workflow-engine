#!/usr/bin/env python
"""
Test the Code Review workflow endpoint.
"""
import json
import requests
import time
import subprocess
import sys

# Start server in background
print("Starting server...")
proc = subprocess.Popen([sys.executable, "run_server.py"], 
                       stdout=subprocess.PIPE, 
                       stderr=subprocess.PIPE)
time.sleep(3)

# Prepare request
url = "http://localhost:8000/workflows/code-review"
payload = {
    "initial_state": {
        "code": "def hello():\n    print('world')",
        "quality_threshold": 75
    }
}

try:
    # Make request
    print(f"Calling Code Review workflow...\n")
    response = requests.post(url, json=payload)
    result = response.json()
    
    # Display results
    print("✓ Workflow executed successfully!\n")
    print(f"Run ID: {result['run_id']}")
    print(f"Graph ID: {result['graph_id']}")
    print(f"Completed: {result['is_completed']}")
    print(f"Quality Score: {result['final_state'].get('quality_score', 'N/A')}\n")
    
    print("Execution Log:")
    for step in result['execution_log']:
        print(f"  [{step['node_id']}] {step['status']}")
        
except Exception as e:
    print(f"✗ Error: {e}")
finally:
    # Stop server
    proc.terminate()
    print("\nServer stopped.")
