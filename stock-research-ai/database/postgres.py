from collections.abc import Generator

import psycopg2
from psycopg2.extras import RealDictCursor

from core.config import settings

def get_connection():
    return psycopg2.connect(
        settings.database_url,
        cursor_factory=RealDictCursor
    )

def get_db() -> Generator:
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()