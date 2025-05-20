"""Configuration settings for SKAI."""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import dotenv


@dataclass
class LLMConfig:
    """Configuration for LLM models."""

    provider: str = "openrouter"
    # Default model (meta-llama/llama-3.3-8b-instruct has good balance of performance and speed)
    model: str = "meta-llama/llama-3.3-8b-instruct:free"
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1024
    top_p: float = 0.95
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    timeout: int = 60  # Timeout in seconds


@dataclass
class AgentConfig:
    """Configuration for agents."""

    name: str
    model_config: LLMConfig
    description: str
    tools: List[str] = field(default_factory=list)  # Use default_factory for mutable default
    enabled: bool = True


@dataclass
class WakeWordConfig:
    """Configuration for wake word detection."""
    
    enabled: bool = False
    phrase: str = "Hey SKAI"
    sensitivity: float = 0.5
    access_key: Optional[str] = None


@dataclass
class Config:
    """Main configuration for SKAI."""

    # General settings
    app_name: str = "SKAI"
    debug_mode: bool = False
    log_level: str = "info"
    log_to_file: bool = True
    detailed_logs: bool = False
    
    # OpenRouter settings
    openrouter_api_key: Optional[str] = None
    
    # Picovoice settings
    picovoice_access_key: Optional[str] = None
    
    # Default LLM configuration
    default_llm: LLMConfig = field(default_factory=LLMConfig)  # Use default_factory
    
    # Wake word configuration
    wake_word: WakeWordConfig = field(default_factory=WakeWordConfig)  # Use default_factory
    
    # Memory settings
    chroma_path: str = "data/chroma_db"
    
    # Agent settings
    agents: Dict[str, AgentConfig] = field(default_factory=dict)  # Use default_factory
    
    def __post_init__(self):
        """Initialize default values and process environment variables."""
        pass  # No need to initialize agents dict anymore
    
    @classmethod
    def from_env(cls, env_file: str = ".env") -> "Config":
        """Load configuration from environment variables.
        
        Args:
            env_file: Path to .env file
            
        Returns:
            Config object with values from environment
        """
        # Load environment variables from .env file
        dotenv.load_dotenv(env_file)
        
        # Create config with values from environment
        config = cls(
            app_name=os.getenv("APP_NAME", "SKAI"),
            debug_mode=os.getenv("DEBUG_MODE", "False").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "info").lower(),
            log_to_file=os.getenv("LOG_TO_FILE", "True").lower() == "true",
            detailed_logs=os.getenv("DETAILED_LOGS", "False").lower() == "true",
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
            picovoice_access_key=os.getenv("PICOVOICE_ACCESS_KEY"),
            chroma_path=os.getenv("CHROMA_PATH", "data/chroma_db"),
        )
        
        # Set up default LLM configuration
        config.default_llm = LLMConfig(
            provider=os.getenv("LLM_PROVIDER", "openrouter"),
            model=os.getenv("LLM_MODEL", "meta-llama/llama-3.3-8b-instruct:free"),
            api_key=os.getenv("OPENROUTER_API_KEY"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "1024")),
            top_p=float(os.getenv("LLM_TOP_P", "0.95")),
            frequency_penalty=float(os.getenv("LLM_FREQUENCY_PENALTY", "0.0")),
            presence_penalty=float(os.getenv("LLM_PRESENCE_PENALTY", "0.0")),
            timeout=int(os.getenv("LLM_TIMEOUT", "60")),
        )
        
        # Set up wake word configuration
        config.wake_word = WakeWordConfig(
            enabled=os.getenv("WAKE_WORD_ENABLED", "False").lower() == "true",
            phrase=os.getenv("WAKE_WORD_PHRASE", "Hey SKAI"),
            sensitivity=float(os.getenv("WAKE_WORD_SENSITIVITY", "0.5")),
            access_key=os.getenv("PICOVOICE_ACCESS_KEY"),
        )
        
        return config


# Create a global configuration object
config = Config.from_env() 