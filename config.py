from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    WHATSAPP_TOKEN: str = "your_token"
    WHATSAPP_PHONE_ID: str = "your_phone_id"
    WHATSAPP_VERIFY_TOKEN: str = "shopyai123"
    GEMINI_API_KEY: str = "your_gemini_key"
    OWNER_WHATSAPP: str = "+923001234567"
    CCTV_CONFIDENCE_THRESHOLD: float = 0.65
    CCTV_ALERT_COOLDOWN_SECONDS: int = 60
    class Config:
        env_file = ".env"
settings = Settings()
