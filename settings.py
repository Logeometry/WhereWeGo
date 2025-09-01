# config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGO_ATLAS_URI: str = ""
    SECRET_KEY: str = "y314adfas...23414afdafasf524515411"
    ENVIRONMENT: str = "dev"
    TMAP_API_KEY: str = ""
    FRONTEND_URL: str = "http://localhost:3000"
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    KAKAKO_REST_API_KEY: str = ""
    TOUR_API_KEY_Crowding: str = ""
    GEMINI_API_KEY: str = ""
    APP_KEY: str = ""

    class Config:
        env_file = ".env.prod"
