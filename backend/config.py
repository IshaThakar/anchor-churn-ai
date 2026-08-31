import os

class Config:
    PROJECT_NAME: str = "Anchor - Predictive Intelligence for Customer Retention"
    VERSION: str = "2.4.0-enterprise"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))
    CORS_ORIGINS: list = ["*"]
