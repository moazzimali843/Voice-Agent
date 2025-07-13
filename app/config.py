import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Application configuration settings"""
    
    # API Keys
    DEEPGRAM_API_KEY: str = os.getenv("DEEPGRAM_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Application Configuration
    APP_HOST: str = os.getenv("APP_HOST", "localhost")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # Knowledge Base Configuration
    KNOWLEDGE_BASE_PATH: str = os.getenv("KNOWLEDGE_BASE_PATH", "./knowledge_base")
    
    # Audio Configuration
    AUDIO_SAMPLE_RATE: int = int(os.getenv("AUDIO_SAMPLE_RATE", "16000"))
    AUDIO_CHANNELS: int = int(os.getenv("AUDIO_CHANNELS", "1"))
    
    # LLM Configuration
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "500"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
    
    def validate(self) -> bool:
        """Validate that all required settings are present"""
        required_keys = [
            self.DEEPGRAM_API_KEY,
            self.OPENAI_API_KEY
        ]
        return all(key.strip() for key in required_keys)

# Global settings instance
settings = Settings() 