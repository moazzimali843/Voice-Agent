from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class AudioQuery(BaseModel):
    """Schema for audio query requests"""
    session_id: str
    audio_data: bytes
    format: str = "wav"

class TextQuery(BaseModel):
    """Schema for text query requests"""
    session_id: str
    query: str

class KnowledgeChunk(BaseModel):
    """Schema for knowledge base chunks"""
    content: str
    source: str
    relevance_score: float

class LLMRequest(BaseModel):
    """Schema for LLM API requests"""
    query: str
    context: List[KnowledgeChunk]
    max_tokens: int = 500
    temperature: float = 0.7

class LLMResponse(BaseModel):
    """Schema for LLM API responses"""
    response: str
    tokens_used: int
    model: str

class TTSRequest(BaseModel):
    """Schema for TTS API requests"""
    text: str
    voice: str = "aura-asteria-en"
    format: str = "mp3"

class TTSResponse(BaseModel):
    """Schema for TTS API responses"""
    audio_url: Optional[str] = None
    audio_data: Optional[bytes] = None
    format: str

class VoiceAgentResponse(BaseModel):
    """Schema for complete voice agent responses"""
    session_id: str
    transcribed_text: str
    llm_response: str
    audio_response: TTSResponse
    processing_time: float
    timestamp: datetime

class ErrorResponse(BaseModel):
    """Schema for error responses"""
    error: str
    message: str
    timestamp: datetime
    session_id: Optional[str] = None

class SessionStatus(BaseModel):
    """Schema for session status"""
    session_id: str
    status: str  # "active", "loading", "ready", "error"
    knowledge_loaded: bool
    realtime_connected: bool = False
    created_at: datetime
    last_activity: datetime 