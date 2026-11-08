from pathlib import Path
from .db import get_connection
from .config import settings


def bootstrap_database():
    sql_path = Path(__file__).resolve().parent.parent / "sql" / "init.sql"
    sql = sql_path.read_text(encoding="utf-8")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)

            cur.execute(
                '''
                INSERT INTO frost_api_chave (descricao, chave_api)
                VALUES (%s, %s)
                ON CONFLICT (chave_api) DO NOTHING
                ''',
                ("ESP32 FROST", settings.initial_api_key),
            )

            cur.execute(
                '''
                INSERT INTO frost_aparelho
                    (identificador, descricao, localizacao, fabricante, modelo)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (identificador) DO NOTHING
                ''',
                (
                    settings.initial_device_identifier,
                    settings.initial_device_description,
                    settings.initial_device_location,
                    settings.initial_device_manufacturer,
                    settings.initial_device_model,
                ),
            )

        conn.commit()
