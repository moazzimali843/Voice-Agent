import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Application configuration settings"""
    
    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Application Configuration
    APP_HOST: str = os.getenv("APP_HOST", "localhost")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # Knowledge Base Configuration
    KNOWLEDGE_BASE_PATH: str = os.getenv("KNOWLEDGE_BASE_PATH", "./knowledge_base")
    
    # Audio Configuration
    AUDIO_SAMPLE_RATE: int = int(os.getenv("AUDIO_SAMPLE_RATE", "24000"))  # OpenAI Realtime API uses 24kHz
    AUDIO_CHANNELS: int = int(os.getenv("AUDIO_CHANNELS", "1"))
    AUDIO_FORMAT: str = os.getenv("AUDIO_FORMAT", "pcm16")  # OpenAI Realtime API format
    
    # OpenAI Realtime API Configuration
    OPENAI_REALTIME_MODEL: str = os.getenv("OPENAI_REALTIME_MODEL", "gpt-4o-mini-realtime-preview")
    OPENAI_REALTIME_VOICE: str = os.getenv("OPENAI_REALTIME_VOICE", "alloy")
    OPENAI_REALTIME_TEMPERATURE: float = float(os.getenv("OPENAI_REALTIME_TEMPERATURE", "0.7"))
    OPENAI_REALTIME_MAX_TOKENS: int = int(os.getenv("OPENAI_REALTIME_MAX_TOKENS", "4096"))
    
    # Voice Activity Detection Settings
    VAD_THRESHOLD: float = float(os.getenv("VAD_THRESHOLD", "0.5"))
    VAD_PREFIX_PADDING_MS: int = int(os.getenv("VAD_PREFIX_PADDING_MS", "300"))
    VAD_SILENCE_DURATION_MS: int = int(os.getenv("VAD_SILENCE_DURATION_MS", "500"))
    
    # Prompt Caching Configuration
    ENABLE_PROMPT_CACHING: bool = os.getenv("ENABLE_PROMPT_CACHING", "True").lower() == "true"
    MIN_CACHE_TOKENS: int = int(os.getenv("MIN_CACHE_TOKENS", "1024"))  # Minimum tokens for caching benefit
    
    # Session Configuration
    SESSION_TIMEOUT_MINUTES: int = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))
    
    def validate(self) -> bool:
        """Validate that all required settings are present"""
        if not self.OPENAI_API_KEY.strip():
            print("❌ OPENAI_API_KEY is missing in environment variables")
            return False
        return True

# Global settings instance
settings = Settings() 