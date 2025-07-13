import asyncio
import logging
from typing import Optional
import httpx
# Fix imports to work from any directory
try:
    from ..config import settings
except ImportError:
    from config import settings

logger = logging.getLogger(__name__)

class STTService:
    """Service for Speech-to-Text conversion using Deepgram API"""
    
    def __init__(self):
        self.api_key = settings.DEEPGRAM_API_KEY
        self.base_url = "https://api.deepgram.com/v1/listen"
    
    async def transcribe_audio(self, audio_data: bytes, format: str = "wav") -> Optional[str]:
        """
        Transcribe audio data to text using Deepgram API
        
        Args:
            audio_data: Raw audio bytes
            format: Audio format (wav, mp3, etc.)
            
        Returns:
            Transcribed text or None if error
        """
        try:
            # Prepare headers
            headers = {
                "Authorization": f"Token {self.api_key}",
                "Content-Type": f"audio/{format}"
            }
            
            # Prepare query parameters
            params = {
                "model": "nova-2",
                "punctuate": "true",
                "diarize": "false",
                "language": "en-US",
                "smart_format": "true"
            }
            
            # Make HTTP request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    headers=headers,
                    params=params,
                    content=audio_data,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Extract transcript
                    if data and "results" in data:
                        channels = data["results"].get("channels", [])
                        if channels and len(channels) > 0:
                            alternatives = channels[0].get("alternatives", [])
                            if alternatives and len(alternatives) > 0:
                                transcript = alternatives[0].get("transcript", "").strip()
                                if transcript:
                                    logger.info(f"Successfully transcribed audio: {transcript[:50]}...")
                                    return transcript
                    
                    logger.warning("No transcript found in Deepgram response")
                    return None
                else:
                    logger.error(f"Deepgram API error: {response.status_code} - {response.text}")
                    return None
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            return None
    
    async def transcribe_streaming(self, audio_stream) -> Optional[str]:
        """
        Transcribe streaming audio using Deepgram's streaming API
        Note: This is a simplified version for compatibility
        
        Args:
            audio_stream: Audio stream generator
            
        Returns:
            Transcribed text or None if error
        """
        try:
            # For now, collect all audio chunks and process as a single file
            audio_chunks = []
            async for chunk in audio_stream:
                if chunk:
                    audio_chunks.append(chunk)
            
            if audio_chunks:
                # Combine all chunks
                combined_audio = b''.join(audio_chunks)
                # Use the regular transcribe method
                return await self.transcribe_audio(combined_audio, "wav")
            
            return None
            
        except Exception as e:
            logger.error(f"Error in streaming transcription: {str(e)}")
            return None
    
    def validate_audio_format(self, format: str) -> bool:
        """
        Validate if audio format is supported
        
        Args:
            format: Audio format string
            
        Returns:
            True if supported, False otherwise
        """
        supported_formats = {
            'wav', 'mp3', 'mp4', 'mpeg', 'mpga', 'm4a', 'ogg', 'wav', 'webm'
        }
        return format.lower() in supported_formats
    
    def get_audio_info(self, audio_data: bytes) -> dict:
        """
        Get basic information about audio data
        
        Args:
            audio_data: Raw audio bytes
            
        Returns:
            Dictionary with audio information
        """
        return {
            'size_bytes': len(audio_data),
            'size_mb': round(len(audio_data) / (1024 * 1024), 2),
            'supported': len(audio_data) > 0
        }

# Global STT service instance
stt_service = STTService() 