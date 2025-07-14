import asyncio
import uuid
import json
import logging
from datetime import datetime
from typing import Dict, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse

try:
    from ..services.openai_realtime_service import openai_realtime_service
    from ..services.knowledge_service import knowledge_service
except ImportError:
    from app.services.openai_realtime_service import openai_realtime_service
    from app.services.knowledge_service import knowledge_service

logger = logging.getLogger(__name__)
router = APIRouter()

# Active sessions storage
sessions: Dict[str, dict] = {}

@router.post("/start-session")
async def start_session():
    """Initialize a new voice session"""
    try:
        session_id = str(uuid.uuid4())
        
        # Load knowledge base
        knowledge_loaded = knowledge_service.load_knowledge_base(session_id)
        knowledge_chunks = knowledge_service.get_all_knowledge_chunks(session_id) if knowledge_loaded else []
        
        # Create OpenAI session with knowledge context
        success = await openai_realtime_service.create_session(session_id, knowledge_chunks)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create session")
        
        # Store session info
        sessions[session_id] = {
            "id": session_id,
            "created_at": datetime.now(),
            "status": "ready"
        }
        
        return {"session_id": session_id, "status": "ready"}
        
    except Exception as e:
        logger.error(f"Session creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/session/{session_id}/status")
async def get_session_status(session_id: str):
    """Get session status"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return sessions[session_id]

@router.delete("/session/{session_id}")
async def end_session(session_id: str):
    """End a session and cleanup resources"""
    try:
        if session_id in sessions:
            await openai_realtime_service.disconnect_session(session_id)
            knowledge_service.clear_session_knowledge(session_id)
            del sessions[session_id]
        
        return {"status": "ended"}
        
    except Exception as e:
        logger.error(f"Session cleanup failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """Main WebSocket endpoint for voice interaction"""
    await websocket.accept()
    
    if session_id not in sessions:
        await websocket.send_text(json.dumps({"type": "error", "message": "Session not found"}))
        await websocket.close()
        return
    
    try:
        # Connect to OpenAI Realtime API
        openai_ws = await openai_realtime_service.connect_session(session_id)
        if not openai_ws:
            await websocket.send_text(json.dumps({"type": "error", "message": "Failed to connect to OpenAI"}))
            await websocket.close()
            return
        
        # Audio buffer for collecting response chunks
        audio_buffer = []
        
        async def handle_openai_events():
            """Handle events from OpenAI Realtime API"""
            try:
                async for message in openai_ws:
                    data = json.loads(message)
                    event_type = data.get("type", "")
                    
                    # Handle different event types
                    if event_type == "response.audio.delta":
                        # Collect audio chunks
                        if "delta" in data:
                            import base64
                            audio_chunk = base64.b64decode(data["delta"])
                            audio_buffer.append(audio_chunk)
                    
                    elif event_type == "response.audio.done":
                        # Send complete audio response
                        if audio_buffer:
                            complete_audio = b''.join(audio_buffer)
                            await websocket.send_bytes(complete_audio)
                            audio_buffer.clear()
                    
                    elif event_type == "conversation.item.input_audio_transcription.completed":
                        # Forward transcript to client
                        await websocket.send_text(json.dumps({
                            "type": "conversation.item.input_audio_transcription.completed",
                            "transcript": data.get("transcript", "")
                        }))
                    
                    elif event_type == "response.audio_transcript.done":
                        # Forward AI response transcript
                        await websocket.send_text(json.dumps({
                            "type": "response.audio_transcript.done", 
                            "transcript": data.get("transcript", "")
                        }))
                    
                    elif event_type == "response.done":
                        # Response complete
                        await websocket.send_text(json.dumps({
                            "type": "response.done"
                        }))
                    
                    elif event_type == "error":
                        # Forward errors
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "error": data.get("error", {})
                        }))
                        
            except Exception as e:
                logger.error(f"OpenAI event handling error: {str(e)}")
        
        async def handle_client_audio():
            """Handle audio from client and forward to OpenAI"""
            try:
                while True:
                    message = await websocket.receive()
                    
                    if "bytes" in message:
                        # Forward audio to OpenAI
                        audio_data = message["bytes"]
                        await openai_realtime_service.send_audio_chunk(session_id, audio_data)
                    
            except WebSocketDisconnect:
                logger.info(f"Client disconnected: {session_id}")
            except Exception as e:
                logger.error(f"Client audio handling error: {str(e)}")
        
        # Run both handlers concurrently
        await asyncio.gather(
            handle_openai_events(),
            handle_client_audio()
        )
        
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        # Cleanup
        try:
            await openai_realtime_service.disconnect_session(session_id)
        except:
            pass

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "voice-agent", 
        "version": "1.0.0",
        "active_sessions": len(sessions)
    } 