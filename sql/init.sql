CREATE TABLE IF NOT EXISTS frost_aparelho (
    id_aparelho BIGSERIAL PRIMARY KEY,
    identificador VARCHAR(50) NOT NULL UNIQUE,
    descricao VARCHAR(200),
    localizacao VARCHAR(200),
    fabricante VARCHAR(100),
    modelo VARCHAR(100),
    ativo CHAR(1) NOT NULL DEFAULT 'S' CHECK (ativo IN ('S', 'N')),
    data_cadastro TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS frost_api_chave (
    id_chave BIGSERIAL PRIMARY KEY,
    descricao VARCHAR(200),
    chave_api VARCHAR(128) NOT NULL UNIQUE,
    ativo CHAR(1) NOT NULL DEFAULT 'S' CHECK (ativo IN ('S', 'N')),
    data_cadastro TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS frost_medicao (
    id_medicao BIGSERIAL PRIMARY KEY,
    id_aparelho BIGINT NOT NULL REFERENCES frost_aparelho(id_aparelho),
    mnemonico VARCHAR(30) NOT NULL CHECK (
        mnemonico IN ('AMBIENTE', 'CORRENTE', 'INSUFLAMENTO', 'RETORNO')
    ),
    valor NUMERIC(12,4) NOT NULL,
    data_medicao TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_frost_medicao_01
    ON frost_medicao (id_aparelho, mnemonico, data_medicao DESC, id_medicao DESC);

CREATE TABLE IF NOT EXISTS frost_comando (
    id_comando BIGSERIAL PRIMARY KEY,
    id_aparelho BIGINT NOT NULL REFERENCES frost_aparelho(id_aparelho),
    comando VARCHAR(20) NOT NULL CHECK (
        comando IN ('LIGAR', 'DESLIGAR', 'SETPOINT')
    ),
    setpoint NUMERIC(4,1),
    status VARCHAR(20) NOT NULL DEFAULT 'PENDENTE' CHECK (
        status IN ('PENDENTE', 'PROCESSADO', 'ERRO')
    ),
    data_comando TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_processado TIMESTAMPTZ,
    CHECK (setpoint IS NULL OR setpoint BETWEEN 16 AND 30)
);

CREATE INDEX IF NOT EXISTS ix_frost_comando_01
    ON frost_comando (id_aparelho, status, data_comando ASC, id_comando ASC);

CREATE OR REPLACE VIEW frost_vw_ultima_medicao AS
SELECT id_aparelho, mnemonico, valor, data_medicao
FROM (
    SELECT
        m.id_aparelho,
        m.mnemonico,
        m.valor,
        m.data_medicao,
        ROW_NUMBER() OVER (
            PARTITION BY m.id_aparelho, m.mnemonico
            ORDER BY m.data_medicao DESC, m.id_medicao DESC
        ) AS rn
    FROM frost_medicao m
) x
WHERE rn = 1;
