import logging
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import os

# Fix imports to work from any directory
try:
    from .config import settings
    from .apis.voice_agent import router as voice_agent_router
except ImportError:
    # If relative imports fail, try absolute imports
    from config import settings
    from apis.voice_agent import router as voice_agent_router

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
    # Startup
    logger.info("Starting Voice Agent application...")
    
    # Validate configuration
    if not settings.validate():
        logger.error("Configuration validation failed! Please check your API keys.")
        raise RuntimeError("Invalid configuration")
    
    # Create knowledge base directory if it doesn't exist
    knowledge_path = settings.KNOWLEDGE_BASE_PATH
    if not os.path.exists(knowledge_path):
        os.makedirs(knowledge_path)
        logger.info(f"Created knowledge base directory: {knowledge_path}")
    
    logger.info("Voice Agent application started successfully!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Voice Agent application...")

# Create FastAPI app
app = FastAPI(
    title="Voice Agent API",
    description="A voice-powered AI agent with knowledge base integration",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(voice_agent_router, prefix="/api/v1", tags=["voice-agent"])

# Mount static files
if os.path.exists("app/static"):
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main application page"""
    try:
        # Try to serve static HTML file if it exists
        static_path = "app/static/index.html"
        if os.path.exists(static_path):
            with open(static_path, 'r') as f:
                return HTMLResponse(content=f.read())
        else:
            # Return basic HTML page
            return HTMLResponse(content="""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Voice Agent</title>
                <style>
                    body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                    .container { text-align: center; }
                    .status { padding: 10px; margin: 10px; border-radius: 5px; }
                    .loading { background-color: #ffeaa7; }
                    .ready { background-color: #00b894; color: white; }
                    .error { background-color: #e17055; color: white; }
                    button { padding: 10px 20px; margin: 10px; font-size: 16px; cursor: pointer; }
                    #messages { text-align: left; margin-top: 20px; padding: 10px; background-color: #f0f0f0; border-radius: 5px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Voice Agent</h1>
                    <div id="status" class="status">Not connected</div>
                    <button onclick="startSession()">Start Session</button>
                    <button onclick="startRecording()" disabled id="recordBtn">Start Recording</button>
                    <button onclick="stopRecording()" disabled id="stopBtn">Stop Recording</button>
                    <div id="messages"></div>
                </div>
                
                <script>
                    let sessionId = null;
                    let websocket = null;
                    let mediaRecorder = null;
                    let recordingChunks = [];
                    
                    function updateStatus(message, className) {
                        const statusDiv = document.getElementById('status');
                        statusDiv.textContent = message;
                        statusDiv.className = 'status ' + className;
                    }
                    
                    function addMessage(message) {
                        const messagesDiv = document.getElementById('messages');
                        messagesDiv.innerHTML += '<div>' + message + '</div>';
                        messagesDiv.scrollTop = messagesDiv.scrollHeight;
                    }
                    
                    async function startSession() {
                        try {
                            const response = await fetch('/api/v1/start-session', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' }
                            });
                            const data = await response.json();
                            sessionId = data.session_id;
                            updateStatus('Loading knowledge base...', 'loading');
                            connectWebSocket();
                        } catch (error) {
                            updateStatus('Error starting session: ' + error.message, 'error');
                        }
                    }
                    
                    function connectWebSocket() {
                        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                        websocket = new WebSocket(protocol + '//' + window.location.host + '/api/v1/ws/' + sessionId);
                        
                        websocket.onmessage = function(event) {
                            if (event.data instanceof Blob) {
                                // Handle audio response
                                const audio = new Audio();
                                audio.src = URL.createObjectURL(event.data);
                                audio.play();
                                addMessage('🔊 Playing audio response');
                            } else {
                                // Handle text messages
                                const data = JSON.parse(event.data);
                                handleWebSocketMessage(data);
                            }
                        };
                        
                        websocket.onopen = function() {
                            addMessage('WebSocket connected');
                        };
                        
                        websocket.onclose = function() {
                            addMessage('WebSocket disconnected');
                        };
                    }
                    
                    function handleWebSocketMessage(data) {
                        switch(data.type) {
                            case 'session_update':
                                if (data.status === 'ready') {
                                    updateStatus('Ready for voice input', 'ready');
                                    document.getElementById('recordBtn').disabled = false;
                                } else if (data.status === 'error') {
                                    updateStatus('Error loading knowledge base', 'error');
                                }
                                break;
                            case 'transcription':
                                addMessage('📝 You said: ' + data.text);
                                break;
                            case 'response':
                                addMessage('🤖 Assistant: ' + data.text);
                                break;
                            case 'processing':
                                addMessage('⏳ Processing: ' + data.step);
                                break;
                            case 'error':
                                addMessage('❌ Error: ' + data.message);
                                break;
                        }
                    }
                    
                    async function startRecording() {
                        try {
                            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                            mediaRecorder = new MediaRecorder(stream);
                            recordingChunks = [];
                            
                            mediaRecorder.ondataavailable = function(event) {
                                if (event.data.size > 0) {
                                    recordingChunks.push(event.data);
                                }
                            };
                            
                            mediaRecorder.onstop = function() {
                                const blob = new Blob(recordingChunks, { type: 'audio/wav' });
                                blob.arrayBuffer().then(buffer => {
                                    websocket.send(buffer);
                                });
                                stream.getTracks().forEach(track => track.stop());
                            };
                            
                            mediaRecorder.start();
                            document.getElementById('recordBtn').disabled = true;
                            document.getElementById('stopBtn').disabled = false;
                            addMessage('🎤 Recording started...');
                        } catch (error) {
                            addMessage('❌ Error accessing microphone: ' + error.message);
                        }
                    }
                    
                    function stopRecording() {
                        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                            mediaRecorder.stop();
                            document.getElementById('recordBtn').disabled = false;
                            document.getElementById('stopBtn').disabled = true;
                            addMessage('🔍 Processing audio...');
                        }
                    }
                </script>
            </body>
            </html>
            """)
    except Exception as e:
        logger.error(f"Error serving root page: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Global health check endpoint"""
    return {
        "status": "healthy",
        "service": "voice-agent",
        "version": "1.0.0"
    }

# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return {
        "error": "Internal server error",
        "message": "An unexpected error occurred"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG,
        log_level="info"
    ) 