from fastapi import Header, HTTPException, status
from .config import settings
from .db import get_connection


def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")):
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"codigo": "API_KEY_AUSENTE", "mensagem": "Chave de API nao informada."},
        )

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT id_chave
                FROM frost_api_chave
                WHERE chave_api = %s
                  AND ativo = 'S'
                ''',
                (x_api_key,),
            )
            row = cur.fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"codigo": "API_KEY_INVALIDA", "mensagem": "Chave de API invalida ou inativa."},
        )
