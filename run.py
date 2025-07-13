#!/usr/bin/env python3
"""
Startup script for the Voice Agent application
"""
import uvicorn
from app.main import app

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="localhost",
        port=8000,
        reload=True,
        log_level="info"
    ) 