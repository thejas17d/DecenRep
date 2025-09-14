#!/usr/bin/env python3
"""
DecenRep Application Launcher
----------------------------
This script launches the DecenRep Flask application from the backend directory.
"""

import os
import sys

# Add the backend directory to the Python path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

# Change to the root directory so relative paths work correctly
os.chdir(os.path.dirname(__file__))

if __name__ == "__main__":
    # Import and run the Flask app from backend
    from backend.app import app
    
    print("🚀 Starting DecenRep server - Decentralized Medical Records Platform")
    
    # Run the Flask application
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )