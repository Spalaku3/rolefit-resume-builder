from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo
import os
from dotenv import load_dotenv

load_dotenv(interpolate=False)

@dataclass(frozen=True)
class Config:
    database_url: str = os.getenv('DATABASE_URL', 'sqlite:///./data/rolefit.db')
    password: str = os.getenv('APP_PASSWORD', '')
    secret: str = os.getenv('SESSION_SECRET', '')
    environment: str = os.getenv('APP_ENV', 'development')
    timezone: str = os.getenv('APP_TIMEZONE', 'America/Chicago')
    daily_limit: int = 15
    groq_key: str = os.getenv('GROQ_API_KEY', '')
    groq_free: bool = os.getenv('GROQ_FREE_TIER_CONFIRMED', 'false').lower() == 'true'
    groq_models: tuple = tuple(x.strip() for x in os.getenv('GROQ_MODELS', 'openai/gpt-oss-20b,openai/gpt-oss-120b').split(',') if x.strip())
    openrouter_key: str = os.getenv('OPENROUTER_API_KEY', '')
    openrouter_models: tuple = tuple(x.strip() for x in os.getenv('OPENROUTER_MODELS', 'openai/gpt-oss-20b:free,openai/gpt-oss-120b:free').split(',') if x.strip())
    ollama_url: str = os.getenv('OLLAMA_BASE_URL', '')
    ollama_model: str = os.getenv('OLLAMA_MODEL', 'gpt-oss:20b')
    secure_cookie: bool = os.getenv('COOKIE_SECURE', 'false').lower() == 'true'

    def validate(self):
        if len(self.password) < 12 or self.password == 'change-this-password':
            raise RuntimeError('Set APP_PASSWORD to a unique password of at least 12 characters in .env or hosting settings.')
        if len(self.secret) < 32:
            raise RuntimeError('Set SESSION_SECRET to a random value of at least 32 characters.')
        ZoneInfo(self.timezone)
        if self.environment == 'production' and not self.secure_cookie:
            raise RuntimeError('Production requires COOKIE_SECURE=true and HTTPS.')
        if os.getenv('RENDER') and self.database_url.startswith('sqlite'):
            raise RuntimeError('Render has ephemeral local storage. Set DATABASE_URL to a persistent PostgreSQL database.')
        if self.database_url.startswith('sqlite:///'):
            Path(self.database_url.removeprefix('sqlite:///')).parent.mkdir(parents=True, exist_ok=True)

config = Config()
