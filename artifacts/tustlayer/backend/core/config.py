import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "TrustLayer AI"
    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    
    # Firebase
    FIREBASE_CREDENTIALS_PATH: str = os.getenv("FIREBASE_CREDENTIALS_PATH", "")

    # AI Providers
    NVIDIA_API_KEY: str = os.getenv("NVIDIA_API_KEY", "")
    NVIDIA_BASE_URL: str = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
    QWEN_MODEL: str = os.getenv("QWEN_MODEL", "qwen/qwen3.5-122b-a10b")
    OCR_MODEL: str = os.getenv("OCR_MODEL", "nvidia/llama-3.1-nemotron-nano-vl-8b-v1")
    FALLBACK_MODEL: str = os.getenv("FALLBACK_MODEL", "microsoft/phi-4-mini-instruct")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    class Config:
        env_file = ".env"

settings = Settings()
