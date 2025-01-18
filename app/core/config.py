# app/core/config.py

from pydantic_settings import BaseSettings
from pydantic import BaseModel
from typing import List, Dict, Any
from pathlib import Path
from functools import lru_cache


class PricingTier(BaseModel):
    max_chars: int
    price: int


class Settings(BaseSettings):
    # Project directories
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    STATIC_DIR: Path = BASE_DIR / "app" / "static"
    TEMPLATE_DIR: Path = BASE_DIR / "app" / "templates"

    # API Settings
    PROJECT_NAME: str = "Dreamer Document AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str

    # Security
    SECRET_KEY: str = "your-secret-key-here"  # Change in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # File Upload
    MAX_UPLOAD_SIZE: int = 20 * 1024 * 1024  # 20MB
    ALLOWED_EXTENSIONS: set = {"pdf", "docx"}

    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_TEMPERATURE: float = 0.7
    OPENAI_MAX_TOKENS: int = 4096

    # Stripe
    STRIPE_SECRET_KEY: str
    STRIPE_PUBLISHABLE_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    STRIPE_CURRENCY: str = "cny"

    # Pricing (in cents)
    MIN_CHARGE: int = 350  # ¥3.50
    PRICING_TIERS: List[PricingTier] = [
        PricingTier(max_chars=1000, price=100),
        PricingTier(max_chars=5000, price=200),
        PricingTier(max_chars=10000, price=300),
        PricingTier(max_chars=50000, price=500),
        PricingTier(max_chars=100000, price=800),
        PricingTier(max_chars=float('inf'), price=1000)
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True

    def calculate_price(self, char_count: int) -> int:
        """Calculate price based on character count."""
        for tier in self.PRICING_TIERS:
            if char_count <= tier.max_chars:
                return max(tier.price, self.MIN_CHARGE)
        return max(self.PRICING_TIERS[-1].price, self.MIN_CHARGE)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Create required directories
def create_directories(settings: Settings):
    """Create necessary directories if they don't exist."""
    directories = [
        settings.UPLOAD_DIR,
        settings.STATIC_DIR,
        settings.TEMPLATE_DIR,
        settings.STATIC_DIR / "css",
        settings.STATIC_DIR / "js"
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


# Initialize settings and create directories
settings = get_settings()
create_directories(settings)