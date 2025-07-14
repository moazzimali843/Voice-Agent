import asyncio
import logging
from typing import Optional, Union
import httpx
# Fix imports to work from any directory
try:
    from ..config import settings
    from ..models.schemas import TTSRequest, TTSResponse
except ImportError:
    from config import settings
    from models.schemas import TTSRequest, TTSResponse

logger = logging.getLogger(__name__)

class TTSService:
    """Service for Text-to-Speech conversion using Deepgram API"""
    
    def __init__(self):
        self.api_key = settings.DEEPGRAM_API_KEY
        self.base_url = "https://api.deepgram.com/v1/speak"
    
    async def convert_text_to_speech(self, text: str, voice: str = "aura-asteria-en", format: str = "mp3") -> Optional[TTSResponse]:
        """
        Convert text to speech using Deepgram API
        
        Args:
            text: Text to convert to speech
            voice: Voice model to use
            format: Audio format (mp3, wav, etc.)
            
        Returns:
            TTSResponse object or None if error
        """
        try:
            # Prepare headers
            headers = {
                "Authorization": f"Token {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Prepare request body
            payload = {
                "text": text
            }
            
            # Prepare query parameters
            params = {
                "model": voice,
                "encoding": format
            }
            
            # Only add sample_rate for wav format
            if format.lower() == "wav":
                params["sample_rate"] = str(settings.AUDIO_SAMPLE_RATE)
            
            # Make HTTP request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    headers=headers,
                    params=params,
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    audio_data = response.content
                    
                    # Create response object
                    tts_response = TTSResponse(
                        audio_data=audio_data,
                        format=format,
                        audio_url=None
                    )
                    
                    logger.info(f"Successfully converted text to speech: {text[:50]}...")
                    return tts_response
                else:
                    logger.error(f"Deepgram TTS API error: {response.status_code} - {response.text}")
                    return None
            
        except Exception as e:
            logger.error(f"Error converting text to speech: {str(e)}")
            return None
    
    async def convert_with_options(self, request: TTSRequest) -> Optional[TTSResponse]:
        """
        Convert text to speech with custom options
        
        Args:
            request: TTSRequest object with text and options
            
        Returns:
            TTSResponse object or None if error
        """
        return await self.convert_text_to_speech(
            text=request.text,
            voice=request.voice,
            format=request.format
        )
    
    def validate_voice_model(self, voice: str) -> bool:
        """
        Validate if voice model is supported
        
        Args:
            voice: Voice model name
            
        Returns:
            True if supported, False otherwise
        """
        supported_voices = {
            'aura-asteria-en',
            'aura-luna-en',
            'aura-stella-en',
            'aura-athena-en',
            'aura-hera-en',
            'aura-orion-en',
            'aura-arcas-en',
            'aura-perseus-en',
            'aura-angus-en',
            'aura-orpheus-en',
            'aura-helios-en',
            'aura-zeus-en'
        }
        return voice.lower() in supported_voices
    
    def validate_audio_format(self, format: str) -> bool:
        """
        Validate if audio format is supported for TTS
        
        Args:
            format: Audio format string
            
        Returns:
            True if supported, False otherwise
        """
        supported_formats = {
            'mp3', 'wav', 'aac', 'flac', 'opus'
        }
        return format.lower() in supported_formats
    
    def get_supported_voices(self) -> list:
        """
        Get list of supported voice models
        
        Returns:
            List of supported voice model names
        """
        return [
            'aura-asteria-en',  # Female, American
            'aura-luna-en',     # Female, American
            'aura-stella-en',   # Female, American
            'aura-athena-en',   # Female, British
            'aura-hera-en',     # Female, American
            'aura-orion-en',    # Male, American
            'aura-arcas-en',    # Male, American
            'aura-perseus-en',  # Male, American
            'aura-angus-en',    # Male, Irish
            'aura-orpheus-en',  # Male, American
            'aura-helios-en',   # Male, British
            'aura-zeus-en'      # Male, American
        ]
    
    def get_audio_info(self, audio_data: bytes) -> dict:
        """
        Get basic information about generated audio
        
        Args:
            audio_data: Raw audio bytes
            
        Returns:
            Dictionary with audio information
        """
        return {
            'size_bytes': len(audio_data),
            'size_mb': round(len(audio_data) / (1024 * 1024), 2),
            'estimated_duration_seconds': round(len(audio_data) / (settings.AUDIO_SAMPLE_RATE * 2), 2)  # Rough estimate
        }
    
    async def convert_text_chunk_to_speech(self, text: str, voice: str = "aura-asteria-en", format: str = "mp3") -> Optional[bytes]:
        """
        Convert a small text chunk to speech (optimized for streaming)
        
        Args:
            text: Small text chunk to convert
            voice: Voice model to use
            format: Audio format (mp3, wav, etc.)
            
        Returns:
            Audio bytes or None if error
        """
        try:
            # Skip very short or empty text
            if not text or len(text.strip()) < 3:
                return None
                
            # Prepare headers
            headers = {
                "Authorization": f"Token {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Prepare request body
            payload = {
                "text": text.strip()
            }
            
            # Prepare query parameters
            params = {
                "model": voice,
                "encoding": format
            }
            
            # Only add sample_rate for wav format
            if format.lower() == "wav":
                params["sample_rate"] = str(settings.AUDIO_SAMPLE_RATE)
            
            # Make HTTP request with optimized timeout for fastest response
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    headers=headers,
                    params=params,
                    json=payload,
                    timeout=8.0  # Even shorter timeout for fastest chunks
                )
                
                if response.status_code == 200:
                    logger.info(f"Successfully converted text chunk to speech: {text[:30]}...")
                    return response.content
                else:
                    logger.error(f"Deepgram TTS API error for chunk: {response.status_code} - {response.text}")
                    return None
            
        except Exception as e:
            logger.error(f"Error converting text chunk to speech: {str(e)}")
            return None

    async def test_tts_connection(self) -> bool:
        """
        Test TTS service connection
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            test_response = await self.convert_text_to_speech("Test", "aura-asteria-en", "mp3")
            return test_response is not None
        except Exception as e:
            logger.error(f"TTS connection test failed: {str(e)}")
            return False

# Global TTS service instance
tts_service = TTSService() 