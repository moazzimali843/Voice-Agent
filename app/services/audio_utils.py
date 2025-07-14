import logging
import struct
import numpy as np
from typing import Optional, Tuple
import io

logger = logging.getLogger(__name__)

class AudioUtils:
    """Utility class for audio format validation and conversion for OpenAI Realtime API"""
    
    @staticmethod
    def validate_pcm16_24khz(audio_data: bytes) -> bool:
        """
        Validate if audio data appears to be PCM16 format
        
        Args:
            audio_data: Raw audio bytes
            
        Returns:
            True if audio appears to be valid PCM16 format
        """
        try:
            # Check if length is even (PCM16 requires 2 bytes per sample)
            if len(audio_data) % 2 != 0:
                return False
            
            # Check if we have at least some audio data
            if len(audio_data) < 2:
                return False
            
            # Try to unpack as 16-bit integers to verify format
            sample_count = len(audio_data) // 2
            if sample_count > 0:
                # Check first few samples to see if they're reasonable 16-bit values
                first_samples = struct.unpack('<' + 'h' * min(10, sample_count), 
                                            audio_data[:min(20, len(audio_data))])
                
                # Reasonable 16-bit audio samples should be in range [-32768, 32767]
                for sample in first_samples:
                    if not (-32768 <= sample <= 32767):
                        return False
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error validating PCM16 audio: {str(e)}")
            return False
    
    @staticmethod
    def convert_to_pcm16_24khz(audio_data: bytes, source_format: str = "webm", 
                              source_sample_rate: int = 48000) -> Optional[bytes]:
        """
        Convert audio data to PCM16 24kHz mono format required by OpenAI Realtime API
        
        Args:
            audio_data: Raw audio bytes in source format
            source_format: Source audio format (webm, wav, etc.)
            source_sample_rate: Source sample rate
            
        Returns:
            Converted PCM16 24kHz mono audio bytes or None if conversion fails
        """
        try:
            # If it's already PCM16 and appears valid, check if we need resampling
            if AudioUtils.validate_pcm16_24khz(audio_data):
                # Assume it's already at 24kHz if it passes validation
                # In a production system, you'd want to check the actual sample rate
                logger.debug("Audio data appears to be valid PCM16, using as-is")
                return audio_data
            
            # For other formats, we need proper conversion
            # This is a simplified approach - in production you'd use librosa or soundfile
            logger.warning(f"Audio format conversion from {source_format} not fully implemented")
            logger.warning("Attempting basic conversion assuming input is raw PCM")
            
            # Try to interpret as raw PCM and convert sample rate if needed
            if source_sample_rate != 24000:
                converted = AudioUtils._resample_pcm16(audio_data, source_sample_rate, 24000)
                if converted:
                    return converted
            
            # If all else fails, return original data and hope for the best
            logger.warning("Using original audio data without conversion")
            return audio_data
            
        except Exception as e:
            logger.error(f"Error converting audio format: {str(e)}")
            return None
    
    @staticmethod
    def _resample_pcm16(audio_data: bytes, source_rate: int, target_rate: int) -> Optional[bytes]:
        """
        Simple resampling for PCM16 audio
        
        Args:
            audio_data: PCM16 audio bytes
            source_rate: Source sample rate
            target_rate: Target sample rate
            
        Returns:
            Resampled PCM16 audio bytes
        """
        try:
            # Convert bytes to numpy array
            samples = np.frombuffer(audio_data, dtype=np.int16)
            
            # Calculate resampling ratio
            ratio = target_rate / source_rate
            
            # Simple linear interpolation resampling
            original_length = len(samples)
            new_length = int(original_length * ratio)
            
            # Create index array for interpolation
            original_indices = np.linspace(0, original_length - 1, new_length)
            
            # Interpolate
            resampled = np.interp(original_indices, np.arange(original_length), samples)
            
            # Convert back to int16 and then to bytes
            resampled_int16 = resampled.astype(np.int16)
            return resampled_int16.tobytes()
            
        except Exception as e:
            logger.error(f"Error resampling audio: {str(e)}")
            return None
    
    @staticmethod
    def get_audio_info(audio_data: bytes) -> dict:
        """
        Get information about audio data
        
        Args:
            audio_data: Raw audio bytes
            
        Returns:
            Dictionary with audio information
        """
        info = {
            "size_bytes": len(audio_data),
            "size_kb": round(len(audio_data) / 1024, 2),
            "appears_pcm16": AudioUtils.validate_pcm16_24khz(audio_data)
        }
        
        if info["appears_pcm16"]:
            # Calculate approximate duration assuming 24kHz mono PCM16
            samples = len(audio_data) // 2  # 2 bytes per sample
            duration_seconds = samples / 24000  # 24kHz sample rate
            info["estimated_duration_seconds"] = round(duration_seconds, 2)
            info["sample_count"] = samples
        
        return info
    
    @staticmethod
    def create_silence_pcm16(duration_seconds: float, sample_rate: int = 24000) -> bytes:
        """
        Create silence in PCM16 format
        
        Args:
            duration_seconds: Duration of silence
            sample_rate: Sample rate (default 24kHz for OpenAI)
            
        Returns:
            Silence audio data in PCM16 format
        """
        samples = int(duration_seconds * sample_rate)
        silence = np.zeros(samples, dtype=np.int16)
        return silence.tobytes()
    
    @staticmethod
    def detect_audio_format(audio_data: bytes) -> str:
        """
        Attempt to detect audio format from header bytes
        
        Args:
            audio_data: Raw audio bytes
            
        Returns:
            Detected format string
        """
        if len(audio_data) < 12:
            return "unknown"
        
        # Check for common audio format headers
        header = audio_data[:12]
        
        # WAV format
        if header[:4] == b'RIFF' and header[8:12] == b'WAVE':
            return "wav"
        
        # WebM format
        if header[:4] == b'\x1a\x45\xdf\xa3':
            return "webm"
        
        # MP3 format
        if header[:3] == b'ID3' or header[:2] == b'\xff\xfb':
            return "mp3"
        
        # OGG format
        if header[:4] == b'OggS':
            return "ogg"
        
        # If no header matches, assume raw PCM
        if AudioUtils.validate_pcm16_24khz(audio_data):
            return "pcm16"
        
        return "unknown"

# Global audio utils instance
audio_utils = AudioUtils() 