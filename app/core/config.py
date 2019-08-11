import os

from databases import DatabaseURL
from dotenv import load_dotenv

load_dotenv(".env")

DATABASE_URL = os.getenv("DATABASE_URL", "")  # deploying without docker-compose
if not DATABASE_URL:
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    if POSTGRES_HOST == "0.0.0.0":
        POSTGRES_HOST = "localhost"
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5433))
    POSTGRES_USER = os.getenv("POSTGRES_USER", "daler")
    POSTGRES_PASS = os.getenv("POSTGRES_PASSWORD", "daler")
    POSTGRES_NAME = os.getenv("POSTGRES_DB", "citizens_db")

    DATABASE_URL = DatabaseURL(
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASS}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_NAME}"
    )
else:
    DATABASE_URL = DatabaseURL(DATABASE_URL)


MAX_CONNECTIONS_COUNT = int(os.getenv("MAX_CONNECTIONS_COUNT", 5))
MIN_CONNECTIONS_COUNT = int(os.getenv("MIN_CONNECTIONS_COUNT", 3))
