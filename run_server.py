#!/usr/bin/env python
"""
Simple script to run the workflow engine server.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    from app.main import app
    import uvicorn
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
