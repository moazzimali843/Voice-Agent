import asyncio
import json
import logging
import websockets
from datetime import datetime
from typing import List, Optional, Dict, Any, Callable
from cachetools import TTLCache

try:
    from ..config import settings
    from .knowledge_service import knowledge_service
    from .audio_utils import audio_utils
except ImportError:
    from app.config import settings
    from app.services.knowledge_service import knowledge_service
    from app.services.audio_utils import audio_utils

logger = logging.getLogger(__name__)

class OpenAIRealtimeService:
    def __init__(self):
        self.model = settings.OPENAI_REALTIME_MODEL
        self.voice = settings.OPENAI_REALTIME_VOICE
        self.temperature = 0.8
        self.max_tokens = 4096
        
        # Session management
        self.sessions: Dict[str, dict] = {}
        
        # Prompt caching with 1-hour TTL
        self.context_cache = TTLCache(maxsize=100, ttl=3600)
        
        # Audio processing stats
        self.audio_stats = {
            "total_chunks_processed": 0,
            "valid_chunks": 0,
            "converted_chunks": 0,
            "rejected_chunks": 0
        }

    def _build_cached_system_context(self, knowledge_chunks: List[Any], session_id: str) -> str:
        """Build system context with knowledge base for prompt caching (≥1,024 tokens)"""
        
        # Create cache key based on knowledge content
        knowledge_text = " ".join([chunk.content for chunk in knowledge_chunks])
        cache_key = f"system_context_{hash(knowledge_text)}"
        
        # Check cache first
        if cache_key in self.context_cache:
            logger.info(f"Using cached system context for session {session_id}")
            return self.context_cache[cache_key]
        
        # Build comprehensive system context
        base_instructions = """You are a helpful voice assistant powered by OpenAI's GPT-4o-mini. You provide accurate, helpful responses based on the knowledge base provided below.

Key guidelines:
- Provide clear, conversational responses
- Be concise but informative  
- Use the knowledge base to answer questions accurately
- If information isn't in the knowledge base, say so clearly
- Maintain a helpful and professional tone
- Focus on being useful and accurate

KNOWLEDGE BASE:
"""
        
        # Add knowledge chunks
        for i, chunk in enumerate(knowledge_chunks[:50]):  # Limit to 50 chunks
            content = chunk.content.strip()
            if content:
                base_instructions += f"\n\nDocument {i+1}:\n{content}"
        
        # Ensure minimum token count for caching effectiveness
        while len(base_instructions.split()) < 300:  # Approximately 1,024 tokens
            base_instructions += "\n\nAdditional context: Provide comprehensive and helpful responses based on the available knowledge base content."
        
        # Cache the instructions
        self.context_cache[cache_key] = base_instructions
        
        word_count = len(base_instructions.split())
        logger.info(f"Built and cached system context for session {session_id} (~{word_count} words)")
        
        return base_instructions

    async def create_session(self, session_id: str, knowledge_chunks: List[Any] = None) -> bool:
        """Create a new OpenAI Realtime session with cached context"""
        try:
            # Build cached system instructions
            if knowledge_chunks:
                system_instructions = self._build_cached_system_context(knowledge_chunks, session_id)
            else:
                system_instructions = "You are a helpful voice assistant. Provide clear, conversational responses."
            
            # Store session data
            self.sessions[session_id] = {
                'status': 'created',
                'system_instructions': system_instructions,
                'created_at': datetime.now(),
                'last_activity': datetime.now(),
                'audio_stats': {
                    'chunks_sent': 0,
                    'chunks_converted': 0,
                    'total_audio_bytes': 0
                }
            }
            
            logger.info(f"Created session {session_id} with cached context")
            return True
            
        except Exception as e:
            logger.error(f"Error creating session {session_id}: {str(e)}")
            return False

    async def connect_session(self, session_id: str) -> Optional[Any]:
        """Connect to OpenAI Realtime WebSocket"""
        try:
            if session_id not in self.sessions:
                logger.error(f"Session {session_id} not found")
                return None
            
            session = self.sessions[session_id]
            
            # Connect to OpenAI Realtime API
            url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"
            headers = {
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "OpenAI-Beta": "realtime=v1"
            }
            
            websocket = await websockets.connect(url, extra_headers=headers)
            session['websocket'] = websocket
            session['status'] = 'connected'
            
            # Send session configuration with cached instructions
            await self._send_session_configuration(websocket, session)
            
            logger.info(f"WebSocket connected for session {session_id}")
            return websocket
            
        except Exception as e:
            logger.error(f"WebSocket connection failed for session {session_id}: {str(e)}")
            if session_id in self.sessions:
                self.sessions[session_id]['status'] = 'error'
            return None

    async def _send_session_configuration(self, websocket, session):
        """Send session configuration to OpenAI with cached instructions"""
        try:
            session_config = {
                "type": "session.update",
                "session": {
                    "modalities": ["text", "audio"],
                    "instructions": session['system_instructions'],  # Cached context
                    "voice": self.voice,
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16",
                    "input_audio_transcription": {
                        "model": "whisper-1"
                    },
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.5,
                        "prefix_padding_ms": 300,
                        "silence_duration_ms": 200,
                        "create_response": True
                    },
                    "temperature": self.temperature,
                    "max_response_output_tokens": self.max_tokens
                }
            }
            
            await websocket.send(json.dumps(session_config))
            logger.info("Sent session configuration with cached instructions")
            
        except Exception as e:
            logger.error(f"Error sending session configuration: {str(e)}")

    async def send_audio_chunk(self, session_id: str, audio_data: bytes):
        """Send audio chunk to OpenAI"""
        try:
            if session_id not in self.sessions:
                logger.error(f"Session {session_id} not found")
                return False
            
            session = self.sessions[session_id]
            websocket = session.get('websocket')
            
            if not websocket:
                logger.error(f"No WebSocket connection for session {session_id}")
                return False
            
            # Update stats
            session['last_activity'] = datetime.now()
            session['audio_stats']['chunks_sent'] += 1
            session['audio_stats']['total_audio_bytes'] += len(audio_data)
            self.audio_stats["total_chunks_processed"] += 1
            
            # Validate and convert audio if needed
            processed_audio = audio_data
            
            if not audio_utils.validate_pcm16_24khz(audio_data):
                # Try to convert to PCM16 24kHz
                detected_format = audio_utils.detect_audio_format(audio_data)
                processed_audio = audio_utils.convert_to_pcm16_24khz(audio_data, detected_format)
                
                if processed_audio:
                    session['audio_stats']['chunks_converted'] += 1
                    self.audio_stats["converted_chunks"] += 1
                else:
                    self.audio_stats["rejected_chunks"] += 1
                    logger.error("Failed to convert audio to PCM16 format")
                    return False
            else:
                self.audio_stats["valid_chunks"] += 1
            
            # Send to OpenAI
            import base64
            audio_base64 = base64.b64encode(processed_audio).decode('utf-8')
            
            audio_event = {
                "type": "input_audio_buffer.append",
                "audio": audio_base64
            }
            
            await websocket.send(json.dumps(audio_event))
            return True
            
        except Exception as e:
            logger.error(f"Error sending audio chunk: {str(e)}")
            return False

    async def disconnect_session(self, session_id: str):
        """Disconnect and cleanup session"""
        try:
            if session_id not in self.sessions:
                return
            
            session = self.sessions[session_id]
            
            # Log final stats
            audio_stats = session.get('audio_stats', {})
            logger.info(f"Session {session_id} audio stats: {audio_stats}")
            
            # Close WebSocket
            websocket = session.get('websocket')
            if websocket:
                await websocket.close()
            
            # Clean up session
            logger.info(f"Disconnected and cleaned up session {session_id}")
            del self.sessions[session_id]
            
        except Exception as e:
            logger.error(f"Error disconnecting session {session_id}: {str(e)}")

    def get_session_status(self, session_id: str) -> dict:
        """Get session status"""
        if session_id not in self.sessions:
            return {"status": "not_found"}
        
        session = self.sessions[session_id]
        return {
            "status": session.get('status', 'unknown'),
            "created_at": session.get('created_at'),
            "last_activity": session.get('last_activity'),
            "audio_stats": session.get('audio_stats', {})
        }

    def get_global_audio_stats(self) -> dict:
        """Get global audio processing statistics"""
        total = self.audio_stats["total_chunks_processed"]
        if total > 0:
            success_rate = ((self.audio_stats["valid_chunks"] + self.audio_stats["converted_chunks"]) / total) * 100
        else:
            success_rate = 0
        
        return {
            **self.audio_stats,
            "success_rate": round(success_rate, 2)
        }

    def validate_configuration(self) -> bool:
        """Validate service configuration"""
        return bool(settings.OPENAI_API_KEY and self.model and self.voice)

# Global service instance
openai_realtime_service = OpenAIRealtimeService() 