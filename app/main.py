from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, Response, status

from .auth import require_api_key
from .bootstrap import bootstrap_database
from .db import get_connection
from .models import ComandoCreate, MedicaoCreate


@asynccontextmanager
async def lifespan(app: FastAPI):
    bootstrap_database()
    yield


app = FastAPI(
    title="FROST API",
    version="2.0.0",
    description="API do projeto FROST em FastAPI e PostgreSQL.",
    lifespan=lifespan,
)


def aparelho_existe(id_aparelho: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT 1
                FROM frost_aparelho
                WHERE id_aparelho = %s
                  AND ativo = 'S'
                ''',
                (id_aparelho,),
            )
            return cur.fetchone() is not None


@app.get("/health")
def health():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 AS ok")
            cur.fetchone()

    return {"status": "OK", "api": "FROST API", "versao": "2.0.0"}


@app.get("/aparelhos", dependencies=[Depends(require_api_key)])
def listar_aparelhos():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT
                    id_aparelho,
                    identificador,
                    descricao,
                    localizacao,
                    fabricante,
                    modelo,
                    ativo,
                    data_cadastro
                FROM frost_aparelho
                ORDER BY id_aparelho
                '''
            )
            rows = cur.fetchall()

    return {"aparelhos": rows}


@app.post("/medicoes", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_api_key)])
def criar_medicoes(payload: MedicaoCreate):
    if not aparelho_existe(payload.id_aparelho):
        raise HTTPException(status_code=404, detail="Aparelho inexistente ou inativo.")

    permitidos = {"AMBIENTE", "CORRENTE", "INSUFLAMENTO", "RETORNO"}

    itens = []

    if payload.medicoes:
        itens = payload.medicoes
    elif payload.mnemonico is not None and payload.valor is not None:
        from .models import MedicaoItem
        itens = [MedicaoItem(mnemonico=payload.mnemonico, valor=payload.valor)]
    else:
        raise HTTPException(
            status_code=400,
            detail="Informe mnemonico e valor, ou um array medicoes.",
        )

    ids = []

    with get_connection() as conn:
        with conn.cursor() as cur:
            for item in itens:
                mnemonico = item.mnemonico.strip().upper()

                if mnemonico not in permitidos:
                    raise HTTPException(status_code=400, detail="Mnemonico de medicao invalido.")

                cur.execute(
                    '''
                    INSERT INTO frost_medicao (id_aparelho, mnemonico, valor)
                    VALUES (%s, %s, %s)
                    RETURNING id_medicao
                    ''',
                    (payload.id_aparelho, mnemonico, item.valor),
                )
                ids.append(cur.fetchone()["id_medicao"])

        conn.commit()

    return {
        "id_aparelho": payload.id_aparelho,
        "ids_medicao": ids,
        "quantidade": len(ids),
    }


@app.get("/aparelhos/{id_aparelho}/estado", dependencies=[Depends(require_api_key)])
def estado_aparelho(id_aparelho: int):
    if not aparelho_existe(id_aparelho):
        raise HTTPException(status_code=404, detail="Aparelho inexistente ou inativo.")

    resultado = {
        "ambiente": None,
        "insuflamento": None,
        "retorno": None,
        "corrente": None,
    }

    mapa = {
        "AMBIENTE": "ambiente",
        "INSUFLAMENTO": "insuflamento",
        "RETORNO": "retorno",
        "CORRENTE": "corrente",
    }

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT mnemonico, valor, data_medicao
                FROM frost_vw_ultima_medicao
                WHERE id_aparelho = %s
                ''',
                (id_aparelho,),
            )

            for row in cur.fetchall():
                resultado[mapa[row["mnemonico"]]] = {
                    "valor": float(row["valor"]),
                    "timestamp": row["data_medicao"],
                }

    return resultado


@app.post("/comandos", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_api_key)])
def criar_comando(payload: ComandoCreate):
    if not aparelho_existe(payload.id_aparelho):
        raise HTTPException(status_code=404, detail="Aparelho inexistente ou inativo.")

    comando = payload.comando.strip().upper()

    if comando not in {"LIGAR", "DESLIGAR", "SETPOINT"}:
        raise HTTPException(status_code=400, detail="Comando invalido.")

    if comando == "SETPOINT" and payload.setpoint is None:
        raise HTTPException(status_code=400, detail="SETPOINT exige setpoint entre 16 e 30.")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                INSERT INTO frost_comando (id_aparelho, comando, setpoint)
                VALUES (%s, %s, %s)
                RETURNING id_comando
                ''',
                (payload.id_aparelho, comando, payload.setpoint),
            )
            id_comando = cur.fetchone()["id_comando"]

        conn.commit()

    return {
        "id_comando": id_comando,
        "id_aparelho": payload.id_aparelho,
        "comando": comando,
        "setpoint": payload.setpoint,
        "status": "PENDENTE",
    }


@app.get(
    "/aparelhos/{id_aparelho}/comandos/pendente",
    dependencies=[Depends(require_api_key)],
)
def comando_pendente(id_aparelho: int, response: Response):
    if not aparelho_existe(id_aparelho):
        raise HTTPException(status_code=404, detail="Aparelho inexistente ou inativo.")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT
                    id_comando,
                    id_aparelho,
                    comando,
                    setpoint,
                    status,
                    data_comando
                FROM frost_comando
                WHERE id_aparelho = %s
                  AND status = 'PENDENTE'
                ORDER BY data_comando ASC, id_comando ASC
                LIMIT 1
                ''',
                (id_aparelho,),
            )
            row = cur.fetchone()

    if not row:
        response.status_code = status.HTTP_204_NO_CONTENT
        return None

    if row["setpoint"] is not None:
        row["setpoint"] = float(row["setpoint"])

    row["timestamp"] = row.pop("data_comando")

    return row


def atualizar_status_comando(id_comando: int, novo_status: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                UPDATE frost_comando
                SET status = %s,
                    data_processado = CURRENT_TIMESTAMP
                WHERE id_comando = %s
                RETURNING id_comando
                ''',
                (novo_status, id_comando),
            )
            row = cur.fetchone()

        conn.commit()

    if not row:
        raise HTTPException(status_code=404, detail="Comando nao encontrado.")

    return {"id_comando": id_comando, "status": novo_status}


@app.put("/comandos/{id_comando}/processado", dependencies=[Depends(require_api_key)])
def marcar_processado(id_comando: int):
    return atualizar_status_comando(id_comando, "PROCESSADO")


@app.put("/comandos/{id_comando}/erro", dependencies=[Depends(require_api_key)])
def marcar_erro(id_comando: int):
    return atualizar_status_comando(id_comando, "ERRO")
