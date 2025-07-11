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
            # Return modern voice interface
            return HTMLResponse(content="""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Voice Agent</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    * {
                        margin: 0;
                        padding: 0;
                        box-sizing: border-box;
                    }
                    
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        min-height: 100vh;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: center;
                        overflow: hidden;
                    }
                    
                    .container {
                        text-align: center;
                        z-index: 10;
                    }
                    
                    .title {
                        color: white;
                        font-size: 2.5rem;
                        font-weight: 300;
                        margin-bottom: 3rem;
                        opacity: 0.9;
                    }
                    
                    .orb-container {
                        position: relative;
                        width: 200px;
                        height: 200px;
                        margin: 0 auto 3rem auto;
                    }
                    
                    .orb {
                        width: 200px;
                        height: 200px;
                        border-radius: 50%;
                        background: linear-gradient(45deg, #00d4ff, #ff00ea, #00ff88, #ffaa00);
                        background-size: 400% 400%;
                        animation: gradientShift 3s ease-in-out infinite;
                        position: relative;
                        box-shadow: 0 0 40px rgba(255, 255, 255, 0.3);
                        cursor: pointer;
                        transition: all 0.3s ease;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: white;
                        font-size: 1.2rem;
                        font-weight: 500;
                    }
                    
                    .orb.listening {
                        animation: gradientShift 1s ease-in-out infinite, pulse 2s ease-in-out infinite;
                        box-shadow: 0 0 60px rgba(255, 255, 255, 0.5);
                        transform: scale(1.1);
                    }
                    
                    .orb.processing {
                        animation: gradientShift 0.5s ease-in-out infinite, rotate 2s linear infinite;
                        box-shadow: 0 0 80px rgba(0, 212, 255, 0.6);
                    }
                    
                    .orb::before {
                        content: '';
                        position: absolute;
                        top: 10%;
                        left: 10%;
                        width: 80%;
                        height: 80%;
                        border-radius: 50%;
                        background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.2));
                        animation: rotate 4s linear infinite reverse;
                    }
                    
                    @keyframes gradientShift {
                        0% { background-position: 0% 50%; }
                        50% { background-position: 100% 50%; }
                        100% { background-position: 0% 50%; }
                    }
                    
                    @keyframes pulse {
                        0%, 100% { transform: scale(1.1); }
                        50% { transform: scale(1.2); }
                    }
                    
                    @keyframes rotate {
                        from { transform: rotate(0deg); }
                        to { transform: rotate(360deg); }
                    }
                    
                    .status {
                        color: white;
                        font-size: 1.2rem;
                        margin: 1rem 0;
                        opacity: 0.8;
                        min-height: 30px;
                    }
                    
                    .buttons {
                        display: flex;
                        gap: 2rem;
                        justify-content: center;
                        margin-top: 2rem;
                    }
                    
                    .btn {
                        padding: 12px 24px;
                        border: 2px solid rgba(255, 255, 255, 0.3);
                        background: rgba(255, 255, 255, 0.1);
                        color: white;
                        border-radius: 25px;
                        font-size: 1rem;
                        font-weight: 500;
                        cursor: pointer;
                        transition: all 0.3s ease;
                        backdrop-filter: blur(10px);
                        min-width: 120px;
                    }
                    
                    .btn:hover {
                        background: rgba(255, 255, 255, 0.2);
                        border-color: rgba(255, 255, 255, 0.5);
                        transform: translateY(-2px);
                        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
                    }
                    
                    .btn:disabled {
                        opacity: 0.5;
                        cursor: not-allowed;
                        transform: none;
                    }
                    
                    .btn.primary {
                        background: linear-gradient(45deg, #00d4ff, #ff00ea);
                        border: none;
                    }
                    
                    .btn.primary:hover {
                        box-shadow: 0 5px 20px rgba(0, 212, 255, 0.4);
                    }
                    

                    
                    .wave-animation {
                        position: absolute;
                        top: 50%;
                        left: 50%;
                        width: 300px;
                        height: 300px;
                        margin: -150px 0 0 -150px;
                        border-radius: 50%;
                        border: 2px solid rgba(255, 255, 255, 0.1);
                        animation: wave 3s ease-in-out infinite;
                        pointer-events: none;
                    }
                    
                    .wave-animation:nth-child(2) {
                        animation-delay: 1s;
                        width: 400px;
                        height: 400px;
                        margin: -200px 0 0 -200px;
                    }
                    
                    .wave-animation:nth-child(3) {
                        animation-delay: 2s;
                        width: 500px;
                        height: 500px;
                        margin: -250px 0 0 -250px;
                    }
                    
                    @keyframes wave {
                        0% { transform: scale(0); opacity: 1; }
                        100% { transform: scale(1); opacity: 0; }
                    }
                    
                    @media (max-width: 768px) {
                        .title { font-size: 2rem; }
                        .orb-container { width: 150px; height: 150px; }
                        .orb { width: 150px; height: 150px; }
                        .buttons { flex-direction: column; align-items: center; gap: 1rem; }
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1 class="title">Voice Agent</h1>
                    
                    <div class="orb-container">
                        <div class="orb" id="mainOrb" onclick="toggleRecording()">
                            <span id="orbText">Tap to speak</span>
                            <div class="wave-animation"></div>
                            <div class="wave-animation"></div>
                            <div class="wave-animation"></div>
                        </div>
                    </div>
                    
                    <div class="status" id="status">Ready to start</div>
                    
                    <div class="buttons">
                        <button class="btn primary" onclick="startSession()" id="startBtn">Start Session</button>
                        <button class="btn" onclick="endSession()" id="endBtn" disabled>End Session</button>
                    </div>
                </div>
                
                <script>
                    let sessionId = null;
                    let websocket = null;
                    let mediaRecorder = null;
                    let recordingChunks = [];
                    let isRecording = false;
                    let isSessionActive = false;
                    
                    // Audio queue system
                    let currentResponse = "";
                    let audioQueue = [];
                    let isPlayingAudio = false;
                    let currentAudio = null;
                    let chunkCounter = 0;
                    
                    const orb = document.getElementById('mainOrb');
                    const orbText = document.getElementById('orbText');
                    const status = document.getElementById('status');
                    const startBtn = document.getElementById('startBtn');
                    const endBtn = document.getElementById('endBtn');
                    
                    function updateStatus(message) {
                        status.textContent = message;
                    }
                    
                    function updateOrbText(text) {
                        orbText.textContent = text;
                    }
                    
                    async function startSession() {
                        try {
                            updateStatus('Starting session...');
                            orb.classList.add('processing');
                            updateOrbText('Loading...');
                            
                            const response = await fetch('/api/v1/start-session', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' }
                            });
                            const data = await response.json();
                            sessionId = data.session_id;
                            
                            connectWebSocket();
                            
                            startBtn.disabled = true;
                            endBtn.disabled = false;
                            isSessionActive = true;
                            
                        } catch (error) {
                            updateStatus('Error starting session: ' + error.message);
                            orb.classList.remove('processing');
                            updateOrbText('Error');
                        }
                    }
                    
                    function connectWebSocket() {
                        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                        websocket = new WebSocket(protocol + '//' + window.location.host + '/api/v1/ws/' + sessionId);
                        
                        websocket.onmessage = function(event) {
                            if (event.data instanceof Blob) {
                                chunkCounter++;
                                queueAudioChunk(event.data, chunkCounter);
                            } else {
                                try {
                                    const data = JSON.parse(event.data);
                                    handleWebSocketMessage(data);
                                } catch (e) {
                                    console.error('Error parsing WebSocket message:', e);
                                }
                            }
                        };
                        
                        websocket.onopen = function() {
                            console.log('WebSocket connected - Audio Queue System Active');
                        };
                        
                        websocket.onclose = function() {
                            console.log('WebSocket disconnected');
                        };
                    }
                    
                    function handleWebSocketMessage(data) {
                        switch(data.type) {
                            case 'session_update':
                                if (data.status === 'ready') {
                                    updateStatus('Ready for voice input');
                                    orb.classList.remove('processing');
                                    updateOrbText('Tap to speak');
                                } else if (data.status === 'error') {
                                    updateStatus('Error loading knowledge base');
                                    orb.classList.remove('processing');
                                    updateOrbText('Error');
                                }
                                break;
                            case 'transcription':
                                // Just clear audio queue, don't show text
                                currentResponse = "";
                                audioQueue = [];
                                chunkCounter = 0;
                                if (currentAudio) {
                                    currentAudio.pause();
                                    currentAudio = null;
                                }
                                isPlayingAudio = false;
                                break;
                            case 'text_chunk':
                                // Build response but don't display it
                                currentResponse += data.chunk + " ";
                                break;
                            case 'processing':
                                if (data.step === 'transcribing') {
                                    updateStatus('Transcribing...');
                                    orb.classList.add('processing');
                                    updateOrbText('Listening...');
                                } else if (data.step === 'searching') {
                                    updateStatus('Searching knowledge base...');
                                    updateOrbText('Thinking...');
                                } else if (data.step === 'generating') {
                                    updateStatus('Generating response...');
                                    updateOrbText('Responding...');
                                }
                                break;
                            case 'response_complete':
                                updateStatus('Response complete');
                                orb.classList.remove('processing');
                                updateOrbText('Tap to speak');
                                break;
                            case 'error':
                                updateStatus('Error: ' + data.message);
                                orb.classList.remove('processing', 'listening');
                                updateOrbText('Error');
                                break;
                        }
                    }
                    
                    function queueAudioChunk(audioBlob, chunkNumber) {
                        audioQueue.push({
                            blob: audioBlob,
                            number: chunkNumber
                        });
                        
                        if (!isPlayingAudio) {
                            playNextAudioChunk();
                        }
                    }
                    
                    function playNextAudioChunk() {
                        if (audioQueue.length === 0) {
                            isPlayingAudio = false;
                            return;
                        }
                        
                        isPlayingAudio = true;
                        const audioItem = audioQueue.shift();
                        
                        currentAudio = new Audio();
                        currentAudio.src = URL.createObjectURL(audioItem.blob);
                        
                        currentAudio.play().catch(error => {
                            console.error('Error playing audio chunk:', error);
                            playNextAudioChunk();
                        });
                        
                        currentAudio.onended = function() {
                            URL.revokeObjectURL(currentAudio.src);
                            currentAudio = null;
                            
                            setTimeout(() => {
                                playNextAudioChunk();
                            }, 50);
                        };
                        
                        currentAudio.onerror = function() {
                            URL.revokeObjectURL(currentAudio.src);
                            currentAudio = null;
                            setTimeout(() => {
                                playNextAudioChunk();
                            }, 50);
                        };
                    }
                    
                    async function toggleRecording() {
                        if (!isSessionActive) {
                            updateStatus('Please start a session first');
                            return;
                        }
                        
                        if (isRecording) {
                            stopRecording();
                        } else {
                            startRecording();
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
                            isRecording = true;
                            
                            orb.classList.add('listening');
                            orb.classList.remove('processing');
                            updateOrbText('Listening...');
                            updateStatus('Recording... tap to stop');
                            
                        } catch (error) {
                            updateStatus('Error accessing microphone: ' + error.message);
                        }
                    }
                    
                    function stopRecording() {
                        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                            mediaRecorder.stop();
                            isRecording = false;
                            
                            orb.classList.remove('listening');
                            orb.classList.add('processing');
                            updateOrbText('Processing...');
                            updateStatus('Processing audio...');
                        }
                    }
                    
                    async function endSession() {
                        if (sessionId) {
                            try {
                                await fetch('/api/v1/session/' + sessionId, { method: 'DELETE' });
                            } catch (error) {
                                console.error('Error ending session:', error);
                            }
                        }
                        
                        if (websocket) {
                            websocket.close();
                        }
                        
                        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                            mediaRecorder.stop();
                        }
                        
                        sessionId = null;
                        isSessionActive = false;
                        isRecording = false;
                        
                        startBtn.disabled = false;
                        endBtn.disabled = true;
                        
                        orb.classList.remove('listening', 'processing');
                        updateOrbText('Tap to speak');
                        updateStatus('Session ended');
                        
                        // Clear audio queue
                        audioQueue = [];
                        if (currentAudio) {
                            currentAudio.pause();
                            currentAudio = null;
                        }
                        isPlayingAudio = false;
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