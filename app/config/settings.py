from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Project Info
    PROJECT_NAME: str = "Chezious Bot API"
    VERSION: str = "1.0.0"
    
    DATABASE_URL: str = "sqlite:///./data/database.db"
    CHECKPOINT_DB_PATH: str = "./data/checkpoints.sqlite"
    
    
    #GROQ SETTINGS
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = ""
    ADVANCE_GROQ_MODEL: str = ""
    API_KEY: str = ""

    # MEMORY SETTINGS
    # Approximate token count (chars/4) before conversation history is summarized.
    SUMMARIZE_TOKEN_THRESHOLD: int = 3000
    # When a summary exists, how many recent messages to pass to the LLM.
    RECENT_CONTEXT_MESSAGES: int = 10

    # CONFIRMATION SETTINGS
    # Max times to re-prompt the user before auto-cancelling the order.
    MAX_CONFIRMATION_RETRIES: int = 2
    # Max times the incomplete→extract loop can retry before auto-cancelling.
    MAX_EXTRACTION_RETRIES: int = 3

    # LLM retry settings
    MAX_LLM_RETRIES: int = 2

    # Pydantic Configuration
    model_config = SettingsConfigDict(
        env_file=".env",            
        env_file_encoding="utf-8",
        extra="ignore"           
    )

# Create a singleton instance to use across the app
settings = Settings()