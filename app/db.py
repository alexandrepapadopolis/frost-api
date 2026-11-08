from contextlib import contextmanager
from urllib.parse import urlparse

import psycopg
from psycopg.rows import dict_row

from .config import settings


@contextmanager
def get_connection():
    database_url = settings.database_url

    print("=== FROST DATABASE DIAGNOSTICO ===")
    print("DATABASE_URL presente:", bool(database_url))
    print("DATABASE_URL tamanho:", len(database_url or ""))

    if database_url:
        parsed = urlparse(database_url)

        print("scheme:", parsed.scheme)
        print("host:", parsed.hostname)
        print("port:", parsed.port)
        print("database:", parsed.path)
    else:
        print("DATABASE_URL esta vazia")

    print("=================================")

    conn = psycopg.connect(
        database_url,
        row_factory=dict_row
    )

    try:
        yield conn
    finally:
        conn.close()