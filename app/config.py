import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Application configuration settings"""
    
    # API Keys
    DEEPGRAM_API_KEY: str = os.getenv("DEEPGRAM_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    
    # Application Configuration
    APP_HOST: str = os.getenv("APP_HOST", "localhost")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # Knowledge Base Configuration
    KNOWLEDGE_BASE_PATH: str = os.getenv("KNOWLEDGE_BASE_PATH", "./knowledge_base")
    
    # Audio Configuration
    AUDIO_SAMPLE_RATE: int = int(os.getenv("AUDIO_SAMPLE_RATE", "16000"))
    AUDIO_CHANNELS: int = int(os.getenv("AUDIO_CHANNELS", "1"))
    
    # LLM Configuration (Anthropic Claude) - Optimized for speed
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "300"))  # Reduced for faster response
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.5"))  # Lower for faster, focused responses
    
    def validate(self) -> bool:
        """Validate that all required settings are present"""
        required_keys = [
            self.DEEPGRAM_API_KEY,
            self.ANTHROPIC_API_KEY
        ]
        return all(key.strip() for key in required_keys)

# Global settings instance
settings = Settings() 