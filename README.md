# FROST API

API limpa do projeto FROST usando **FastAPI + PostgreSQL**.

## Endpoints

- `GET /health`
- `GET /aparelhos`
- `POST /medicoes`
- `GET /aparelhos/{id}/estado`
- `POST /comandos`
- `GET /aparelhos/{id}/comandos/pendente`
- `PUT /comandos/{id}/processado`
- `PUT /comandos/{id}/erro`

Swagger automatico:

- `GET /docs`
- `GET /openapi.json`

A autenticacao usa o header:

```text
X-API-Key: FROST-ESP32-CHAVE-001
```

## Ambiente local com Docker

Requisitos:

- Docker Desktop
- Docker Compose

Na raiz do projeto:

```bash
docker compose up --build
```

A API ficara disponivel em:

```text
http://localhost:8000
```

Swagger:

```text
http://localhost:8000/docs
```

PostgreSQL:

```text
host: localhost
port: 5432
database: frost
user: frost
password: frost
```

Para parar:

```bash
docker compose down
```

Para apagar tambem os dados do PostgreSQL:

```bash
docker compose down -v
```

## Testes rapidos

Health:

```bash
curl http://localhost:8000/health
```

Lista de aparelhos:

```bash
curl http://localhost:8000/aparelhos   -H "X-API-Key: FROST-ESP32-CHAVE-001"
```

Inserir temperatura ambiente:

```bash
curl -X POST http://localhost:8000/medicoes   -H "Content-Type: application/json"   -H "X-API-Key: FROST-ESP32-CHAVE-001"   -d '{"id_aparelho":1,"mnemonico":"AMBIENTE","valor":25.3}'
```

Inserir insuflamento e retorno juntos:

```bash
curl -X POST http://localhost:8000/medicoes   -H "Content-Type: application/json"   -H "X-API-Key: FROST-ESP32-CHAVE-001"   -d '{
    "id_aparelho":1,
    "medicoes":[
      {"mnemonico":"INSUFLAMENTO","valor":12.7},
      {"mnemonico":"RETORNO","valor":24.1}
    ]
  }'
```

Estado consolidado:

```bash
curl http://localhost:8000/aparelhos/1/estado   -H "X-API-Key: FROST-ESP32-CHAVE-001"
```

Criar comando:

```bash
curl -X POST http://localhost:8000/comandos   -H "Content-Type: application/json"   -H "X-API-Key: FROST-ESP32-CHAVE-001"   -d '{"id_aparelho":1,"comando":"SETPOINT","setpoint":22}'
```

Buscar comando pendente:

```bash
curl http://localhost:8000/aparelhos/1/comandos/pendente   -H "X-API-Key: FROST-ESP32-CHAVE-001"
```

## Deploy no Railway

1. Crie um projeto no Railway.
2. Adicione PostgreSQL.
3. Suba este repositorio no GitHub.
4. Crie um servico a partir do repositorio.
5. No servico da API, configure a variavel:

```text
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

6. Configure tambem, se quiser alterar os valores iniciais:

```text
INITIAL_API_KEY
INITIAL_DEVICE_IDENTIFIER
INITIAL_DEVICE_DESCRIPTION
INITIAL_DEVICE_LOCATION
INITIAL_DEVICE_MANUFACTURER
INITIAL_DEVICE_MODEL
```

7. Gere um dominio publico no Railway.

A aplicacao cria automaticamente as tabelas e a massa inicial quando inicia.

## Observacao de seguranca

Para producao, troque a chave inicial padrao e nao publique senhas ou chaves no repositorio.
