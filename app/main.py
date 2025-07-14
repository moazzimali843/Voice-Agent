import logging
import sys
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from contextlib import asynccontextmanager

# Add the app directory to the Python path to fix import issues
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from .config import settings
    from .apis.voice_agent import router as voice_agent_router
except ImportError:
    from app.config import settings
    from app.apis.voice_agent import router as voice_agent_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('voice_agent.log')
    ]
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Voice Agent application...")
    
    # Validate configuration
    if not settings.validate():
        logger.error("Configuration validation failed! Please check your API keys.")
        raise RuntimeError("Invalid configuration")
    
    # Create knowledge base directory if it doesn't exist
    knowledge_dir = "knowledge_base"
    if not os.path.exists(knowledge_dir):
        os.makedirs(knowledge_dir, exist_ok=True)
        logger.info(f"Created {knowledge_dir} directory")
    
    # Create static directory if it doesn't exist
    static_dir = "app/static"
    if not os.path.exists(static_dir):
        os.makedirs(static_dir, exist_ok=True)
        logger.info(f"Created {static_dir} directory")
    
    yield
    
    logger.info("Voice Agent application stopped")

# Create FastAPI app
app = FastAPI(
    title="Voice Agent",
    description="Voice Assistant with OpenAI Realtime API",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
if os.path.exists("app/static"):
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main application page"""
    try:
        # Try to serve static HTML file if it exists
        static_path = "app/static/index.html"
        if os.path.exists(static_path):
            with open(static_path, 'r', encoding='utf-8') as f:
                return HTMLResponse(content=f.read())
        else:
            # Minimal fallback if no static file exists
            return HTMLResponse(content="""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Voice Assistant</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
            </head>
            <body>
                <h1>Voice Assistant</h1>
                <p>Please create app/static/index.html file</p>
            </body>
            </html>
            """)
    except Exception as e:
        logger.error(f"Error serving root page: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Include API routes
app.include_router(voice_agent_router, prefix="/api/v1", tags=["voice"])

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "voice-agent",
        "version": "1.0.0"
    }

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Global exception: {str(exc)}")
    return {"error": "Internal server error", "detail": str(exc)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG,
        log_level="info"
    ) 