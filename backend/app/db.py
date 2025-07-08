import psycopg2
from contextlib import contextmanager
from .config import settings

@contextmanager
def get_db_connection():
    connection = psycopg2.connect(dsn=settings.database_url)
    try:
        yield connection
    finally:
        connection.close()
