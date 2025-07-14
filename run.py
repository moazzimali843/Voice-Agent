#!/usr/bin/env python3
"""
Startup script for the Voice Agent application
"""
import sys
import os
import uvicorn

# Add the current directory to Python path to ensure imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

if __name__ == "__main__":
    try:
        print("[ROCKET] Starting Voice Agent with OpenAI Realtime API...")
        print("[NOTES] Voice chat interface at: http://localhost:8000")
        print("[CONFIG] API documentation at: http://localhost:8000/docs")
        print("[HEALTH] Health check at: http://localhost:8000/health")
        print()
        
        # Import the app
        from app.main import app
        
        # Start the server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            access_log=True,
            reload=False
        )
        
    except KeyboardInterrupt:
        print("\n[INFO] Server stopped by user")
    except Exception as e:
        print(f"\n[FAIL] Failed to start server: {str(e)}")
        print("[TIP] Try running: python test_imports.py")
        sys.exit(1) 