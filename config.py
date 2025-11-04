import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DB_URL", "postgresql://postgres:sivaSIVA%4012@localhost:5432/shopit-now"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SERVICE_BEARER = os.getenv("SERVICE_BEARER", "dev-service-token")
