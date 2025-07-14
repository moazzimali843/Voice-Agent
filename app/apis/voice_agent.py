import asyncio
import uuid
import logging
from datetime import datetime
from typing import Dict, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
# Fix imports to work from any directory
try:
    from ..models.schemas import (
        TextQuery, VoiceAgentResponse, ErrorResponse, SessionStatus,
        TTSResponse, LLMResponse
    )
    from ..services.stt_service import stt_service
    from ..services.tts_service import tts_service
    from ..services.llm_service import llm_service
    from ..services.knowledge_service import knowledge_service
except ImportError:
    from models.schemas import (
        TextQuery, VoiceAgentResponse, ErrorResponse, SessionStatus,
        TTSResponse, LLMResponse
    )
    from services.stt_service import stt_service
    from services.tts_service import tts_service
    from services.llm_service import llm_service
    from services.knowledge_service import knowledge_service
import json
import io

logger = logging.getLogger(__name__)

router = APIRouter()

# Session management
active_sessions: Dict[str, dict] = {}

class WebSocketManager:
    """Manager for WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept websocket connection and store it"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected for session: {session_id}")
    
    def disconnect(self, session_id: str):
        """Remove websocket connection"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected for session: {session_id}")
    
    async def send_message(self, session_id: str, message: dict):
        """Send message to specific session"""
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to session {session_id}: {str(e)}")
    
    async def send_audio(self, session_id: str, audio_data: bytes):
        """Send audio data to specific session"""
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_bytes(audio_data)
            except Exception as e:
                logger.error(f"Error sending audio to session {session_id}: {str(e)}")

# Global websocket manager
websocket_manager = WebSocketManager()

@router.post("/start-session")
async def start_session(background_tasks: BackgroundTasks):
    """Start a new voice agent session and load knowledge base"""
    try:
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Initialize session
        session_data = {
            "session_id": session_id,
            "status": "loading",
            "created_at": datetime.now(),
            "last_activity": datetime.now(),
            "knowledge_loaded": False
        }
        
        active_sessions[session_id] = session_data
        
        # Load knowledge base in background
        background_tasks.add_task(load_knowledge_for_session, session_id)
        
        logger.info(f"Started new session: {session_id}")
        return {"session_id": session_id, "status": "loading"}
        
    except Exception as e:
        logger.error(f"Error starting session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start session")

async def load_knowledge_for_session(session_id: str):
    """Background task to load knowledge base for a session"""
    try:
        success = knowledge_service.load_knowledge_base(session_id)
        
        if session_id in active_sessions:
            if success:
                active_sessions[session_id]["status"] = "ready"
                active_sessions[session_id]["knowledge_loaded"] = True
                logger.info(f"Knowledge base loaded successfully for session: {session_id}")
            else:
                active_sessions[session_id]["status"] = "error"
                logger.error(f"Failed to load knowledge base for session: {session_id}")
        
        # Notify client via websocket if connected
        await websocket_manager.send_message(session_id, {
            "type": "session_update",
            "status": active_sessions[session_id]["status"],
            "knowledge_loaded": active_sessions[session_id]["knowledge_loaded"]
        })
        
    except Exception as e:
        logger.error(f"Error loading knowledge for session {session_id}: {str(e)}")
        if session_id in active_sessions:
            active_sessions[session_id]["status"] = "error"

@router.get("/session/{session_id}/status")
async def get_session_status(session_id: str):
    """Get current session status"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_data = active_sessions[session_id]
    knowledge_status = knowledge_service.get_session_status(session_id)
    
    return SessionStatus(
        session_id=session_id,
        status=session_data["status"],
        knowledge_loaded=session_data.get("knowledge_loaded", False),
        created_at=session_data["created_at"],
        last_activity=session_data["last_activity"]
    )

@router.post("/query/text")
async def process_text_query(query: TextQuery):
    """Process text query without voice conversion"""
    try:
        # Validate session
        if query.session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_data = active_sessions[query.session_id]
        
        if session_data["status"] != "ready":
            raise HTTPException(status_code=400, detail="Session not ready")
        
        # Update last activity
        session_data["last_activity"] = datetime.now()
        
        # Search knowledge base
        relevant_chunks = knowledge_service.search_knowledge(query.session_id, query.query)
        
        # Generate response with session_id for context
        llm_response = await llm_service.generate_response(query.query, relevant_chunks, query.session_id)
        
        if not llm_response:
            raise HTTPException(status_code=500, detail="Failed to generate response")
        
        # Convert to speech
        tts_response = await tts_service.convert_text_to_speech(llm_response.response)
        
        if not tts_response:
            raise HTTPException(status_code=500, detail="Failed to convert response to speech")
        
        # Create response
        response = VoiceAgentResponse(
            session_id=query.session_id,
            transcribed_text=query.query,
            llm_response=llm_response.response,
            audio_response=tts_response,
            processing_time=0.0,  # TODO: Calculate actual processing time
            timestamp=datetime.now()
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing text query: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time voice interaction"""
    await websocket_manager.connect(websocket, session_id)
    
    try:
        # Check if session exists
        if session_id not in active_sessions:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Session not found"
            }))
            return
        
        # Send initial status
        await websocket_manager.send_message(session_id, {
            "type": "session_update",
            "status": active_sessions[session_id]["status"],
            "knowledge_loaded": active_sessions[session_id].get("knowledge_loaded", False)
        })
        
        while True:
            # Wait for audio data
            audio_data = await websocket.receive_bytes()
            
            if not audio_data:
                continue
            
            # Update last activity
            active_sessions[session_id]["last_activity"] = datetime.now()
            
            # Send processing status
            await websocket_manager.send_message(session_id, {
                "type": "processing",
                "step": "transcribing"
            })
            
            # Process audio with STT
            transcript = await stt_service.transcribe_audio(audio_data, "wav")
            
            if not transcript:
                await websocket_manager.send_message(session_id, {
                    "type": "error",
                    "message": "Failed to transcribe audio"
                })
                continue
            
            # Send transcription result
            await websocket_manager.send_message(session_id, {
                "type": "transcription",
                "text": transcript
            })
            
            # Send processing status
            await websocket_manager.send_message(session_id, {
                "type": "processing",
                "step": "searching"
            })
            
            # Search knowledge base
            relevant_chunks = knowledge_service.search_knowledge(session_id, transcript)
            
            # Send processing status
            await websocket_manager.send_message(session_id, {
                "type": "processing",
                "step": "generating"
            })
            
            # Generate streaming response
            await websocket_manager.send_message(session_id, {
                "type": "processing",
                "step": "generating"
            })
            
            try:
                # Start streaming response with session_id for context
                text_stream = llm_service.generate_response_streaming(transcript, relevant_chunks, session_id)
                
                # Buffer and chunk the streaming text (reduced chunk size for faster response)
                chunk_stream = llm_service.buffer_text_for_chunking(text_stream, min_chunk_size=5)
                
                full_response = ""
                chunk_count = 0
                
                async for text_chunk in chunk_stream:
                    if not text_chunk:
                        continue
                    
                    chunk_count += 1
                    full_response += text_chunk + " "
                    
                    # Send text chunk to frontend
                    await websocket_manager.send_message(session_id, {
                        "type": "text_chunk",
                        "chunk": text_chunk,
                        "chunk_number": chunk_count
                    })
                    
                    # Convert chunk to speech immediately
                    await websocket_manager.send_message(session_id, {
                        "type": "processing",
                        "step": f"converting_chunk_{chunk_count}"
                    })
                    
                    audio_data = await tts_service.convert_text_chunk_to_speech(text_chunk)
                    
                    if audio_data:
                        # Send audio chunk immediately
                        await websocket_manager.send_audio(session_id, audio_data)
                        
                        await websocket_manager.send_message(session_id, {
                            "type": "audio_chunk_sent",
                            "chunk_number": chunk_count
                        })
                    else:
                        await websocket_manager.send_message(session_id, {
                            "type": "warning",
                            "message": f"Failed to convert chunk {chunk_count} to speech"
                        })
                
                # Send final completion status
                await websocket_manager.send_message(session_id, {
                    "type": "response_complete",
                    "full_response": full_response.strip(),
                    "total_chunks": chunk_count,
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error in streaming response: {str(e)}")
                await websocket_manager.send_message(session_id, {
                    "type": "error",
                    "message": "Failed to generate streaming response"
                })
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {str(e)}")
        await websocket_manager.send_message(session_id, {
            "type": "error",
            "message": "Internal server error"
        })
    finally:
        websocket_manager.disconnect(session_id)

@router.delete("/session/{session_id}")
async def end_session(session_id: str):
    """End a voice agent session and clean up resources"""
    try:
        # Remove session data
        if session_id in active_sessions:
            del active_sessions[session_id]
        
        # Clear knowledge base
        knowledge_service.clear_session_knowledge(session_id)
        
        # Disconnect websocket if connected
        websocket_manager.disconnect(session_id)
        
        logger.info(f"Ended session: {session_id}")
        return {"message": "Session ended successfully"}
        
    except Exception as e:
        logger.error(f"Error ending session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to end session")

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test services
        stt_healthy = True  # Basic check
        tts_healthy = await tts_service.test_tts_connection()
        llm_healthy = await llm_service.test_llm_connection()
        
        return {
            "status": "healthy" if all([stt_healthy, tts_healthy, llm_healthy]) else "unhealthy",
            "services": {
                "stt": "healthy" if stt_healthy else "unhealthy",
                "tts": "healthy" if tts_healthy else "unhealthy",
                "llm": "healthy" if llm_healthy else "unhealthy"
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        } 