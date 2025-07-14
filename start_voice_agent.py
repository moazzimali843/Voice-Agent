#!/usr/bin/env python3
"""
Simple startup script for Voice Agent
"""
import subprocess
import sys
import os

def install_dependencies():
    """Install missing dependencies"""
    try:
        print("[INFO] Installing dependencies...")
        result = subprocess.run([sys.executable, "-m", "pip", "install", "cachetools==5.3.2"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("[OK] Dependencies installed successfully")
        else:
            print(f"[WARNING] Dependency installation issues: {result.stderr}")
    except Exception as e:
        print(f"[WARNING] Could not install dependencies: {e}")

def start_server():
    """Start the voice agent server"""
    try:
        print("\n[ROCKET] Starting Voice Agent...")
        print("[INFO] Voice interface will be available at: http://localhost:8000")
        print("[INFO] Press Ctrl+C to stop\n")
        
        # Start the server
        subprocess.run([sys.executable, "run.py"])
        
    except KeyboardInterrupt:
        print("\n[INFO] Server stopped by user")
    except Exception as e:
        print(f"\n[FAIL] Error starting server: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("           Voice Agent - OpenAI Realtime API")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists("run.py"):
        print("[FAIL] Please run this script from the Voice-Agent-main directory")
        sys.exit(1)
    
    # Install dependencies
    install_dependencies()
    
    # Start server
    start_server() 