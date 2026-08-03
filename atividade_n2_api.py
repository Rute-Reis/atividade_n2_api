import os
from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
    BackgroundTasks
)
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from datetime import datetime, date


from .app.database import get_db
from .app import models, schemas

from math import ceil
from fastapi import HTTPException, Query
from sqlalchemy import text

from fastapi.staticfiles import StaticFiles

from fastapi.responses import FileResponse

import logging

logging.basicConfig(level=logging.INFO)

## -- colocar debugs aqui -- ##


def format_timedelta(td):
    total_seconds = int(td.total_seconds())

    horas = total_seconds // 3600
    minutos = (total_seconds % 3600) // 60
    segundos = total_seconds % 60

    return f"{horas:02}:{minutos:02}:{segundos:02}"

# ---------- CONFIGURAÇÃO DO AMBIENTE ----------
load_dotenv()  # Carrega as variáveis de ambiente do arquivo .env

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_DIR = os.path.join(
    BASE_DIR,
    "uploads_atividades_N2"
)

os.makedirs(
    UPLOAD_DIR,
    exist_ok=True
)

router = APIRouter(
    prefix="/atividade-n2",
    tags=["Atividade N2"]
)




print("=" * 60)
print("DEBUG - Atividade N2 API")

print(models.AtividadePadrao.__table__)
print(models.AtividadeSuporte.__table__)

print(
    "DEBUG AtividadePadrao:",
    list(models.AtividadePadrao.__table__.columns.keys())
)

print(
    "DEBUG AtividadeSuporte:",
    list(models.AtividadeSuporte.__table__.columns.keys())
)

print("=" * 60)


# ---------- ROTA: GET - LISTAR ATIVIDADES PADRÃO ----------
# ------- https://10.126.112.251:9001/atividade-n2/atividades-padrao -------
@router.get(
    "/atividades-padrao",
    response_model=List[schemas.AtividadePadraoResponse]
)
def listar_atividades_padrao(
    db: Session = Depends(get_db)
):
    atividades = (
        db.query(models.AtividadePadrao)
        .filter(models.AtividadePadrao.ATIVO == 1)
        .order_by(
            models.AtividadePadrao.CATEGORIA,
            models.AtividadePadrao.NOME_ATIVIDADE
        )
        .all()
    )

    return [
        {
            "id_atividade": item.ID,
            # "categoria": item.CATEGORIA,
            "nome_atividade": item.NOME_ATIVIDADE,
            "tempo_estimado_min": item.TEMPO_ESTIMADO_MIN,
            "observacao": item.OBSERVACAO
        }
        for item in atividades
    ]




# ---------- ROTA: GET GERAL - LISTAR ATIVIDADES DE SUPORTE ----------#
@router.get(
    "",
    response_model=List[schemas.AtividadeSuporteRead]
)
def listar_atividades(
    db: Session = Depends(get_db)
):

    atividades = (
        db.query(
            models.AtividadeSuporte,
            models.AtividadePadrao
        )
        .join(
            models.AtividadePadrao,
            models.AtividadePadrao.ID ==
            models.AtividadeSuporte.ID_ATIVIDADE_PADRAO
        )
        .order_by(
            models.AtividadeSuporte.DATA_INICIO.desc()
        )
        .all()
    )

    resultado = []

    for atividade_suporte, atividade_padrao in atividades:

        arquivos_db = (
            db.query(models.ArquivoAtividadeN2)
            .filter(
                models.ArquivoAtividadeN2.ID_ATIVIDADE ==
                atividade_suporte.ID_ATIVIDADE
            )
            .all()
        )

        arquivos_out = [
            {
                "id_arquivo": arquivo.ID_ARQUIVO,
                "id_atividade": arquivo.ID_ATIVIDADE, 
                "nome_original": arquivo.NOME_ORIGINAL, 
                "nome_arquivo": arquivo.NOME_ARQUIVO,  
                "caminho": arquivo.CAMINHO,
                "content_type": arquivo.CONTENT_TYPE,  
                "tamanho_bytes": arquivo.TAMANHO_BYTES,   
                "data_upload": arquivo.DATA_UPLOAD,  
                "url_download":        
                    f"/atividade-n2/arquivo/{arquivo.ID_ARQUIVO}"
            }
            for arquivo in arquivos_db
        ]

        resultado.append({
            "id_atividade": atividade_suporte.ID_ATIVIDADE,

            "matricula": atividade_suporte.MATRICULA,

            "nome_usuario": atividade_suporte.NOME_USUARIO,

            "id_atividade_padrao":
                atividade_suporte.ID_ATIVIDADE_PADRAO,

            "nome_atividade":
                atividade_padrao.NOME_ATIVIDADE,

            "status":
                atividade_suporte.STATUS,

            "data_inicio":
                atividade_suporte.DATA_INICIO,

            "data_fim":
                atividade_suporte.DATA_FIM,

            "tempo_estimado_min":
                atividade_suporte.TEMPO_ESTIMADO_MIN,

            "tempo_real_min":
                atividade_suporte.TEMPO_REAL_MIN,

            "observacoes":
                atividade_suporte.OBSERVACOES,

            "arquivo": arquivos_out
        })

    return resultado





 





# ---------- ROTA: POST - CRIAR ATIVIDADE DE SUPORTE ----------
# ------- https://10.126.112.251:9001/atividade-n2/criar -------
# ---------- ROTA: POST - CRIAR ATIVIDADE DE SUPORTE ----------
@router.post(
    "/criar",
    response_model=schemas.CriarAtividadeResponse,
    status_code=status.HTTP_201_CREATED
)
def criar_atividade(
    dados: schemas.AtividadeSuporteCreate,
    db: Session = Depends(get_db)
):

    # valida se atividade padrão existe
    atividade_padrao = (
        db.query(models.AtividadePadrao)
        .filter(
            models.AtividadePadrao.ID
            == dados.id_atividade_padrao
        )
        .first()
    )

    if not atividade_padrao:
        raise HTTPException(
        status_code=400,
        detail="Atividade padrão inválida."
    )

    STATUS_VALIDOS = [
    "Agendado",
    "Em Atuação",
    "Improcedente"
    ]

    if dados.status not in STATUS_VALIDOS:
        raise HTTPException(
        status_code=400,
        detail="Status inválido."
    )

    # cria atividade
    nova_atividade = models.AtividadeSuporte(

        MATRICULA=dados.matricula,

        NOME_USUARIO=dados.nome_usuario,

        ID_ATIVIDADE_PADRAO=dados.id_atividade_padrao,

        STATUS=dados.status,

        DATA_INICIO=datetime.now(),

        DATA_FIM=None,

        TEMPO_ESTIMADO_MIN=
            atividade_padrao.TEMPO_ESTIMADO_MIN,

        TEMPO_REAL_MIN=None,

        OBSERVACOES=dados.observacoes
    )

    db.add(nova_atividade)

    db.commit()

    db.refresh(nova_atividade)

    # --------------------------------------------------
    # HISTÓRICO
    # --------------------------------------------------
    historico = models.HistoricoAtividadeN2(

        ID_ATIVIDADE=nova_atividade.ID_ATIVIDADE,

        MATRICULA_RESPONSAVEL=dados.matricula,

        NOME_USUARIO=dados.nome_usuario,

        TIPO_EVENTO="CRIACAO",

        DESCRICAO_EVENTO="Atividade criada.",

        DATA_EVENTO=datetime.now()
    )

    db.add(historico)

    db.commit()
    db.refresh(historico)   

    return {
        "id_atividade": nova_atividade.ID_ATIVIDADE,
        "mensagem": "Atividade criada com sucesso"
    }





# ---------- ROTA: PUT - ATUALIZAR STATUS ----------
# ------- https://10.126.112.251:9001/atividade-n2/{id_atividade}/status
@router.put(
    "/{id_atividade}/status"
)
def atualizar_status(
    id_atividade: int,
    payload: schemas.AtualizarStatus,
    db: Session = Depends(get_db)
):

    STATUS_VALIDOS = [
        "Agendado",
        "Em Atuação",
        "Finalizado",
        "Improcedente"
    ]

    atividade = (
        db.query(models.AtividadeSuporte)
        .filter(
            models.AtividadeSuporte.ID_ATIVIDADE == id_atividade
        )
        .first()
    )

    if not atividade:
        raise HTTPException(
            status_code=404,
            detail="Atividade não encontrada."
        )

    if payload.status not in STATUS_VALIDOS:
        raise HTTPException(
            status_code=400,
            detail="Status inválido."
        )

    atividade.STATUS = payload.status

    # quando finalizar
    if payload.status == "Finalizado":

        data_fim = datetime.now()

        atividade.DATA_FIM = data_fim

        if atividade.DATA_INICIO:

            diferenca = (
                data_fim - atividade.DATA_INICIO
            )

            atividade.TEMPO_REAL_MIN = int(
                diferenca.total_seconds() / 60
            )

    db.commit()
    db.refresh(atividade)

    # --------------------------------------------------
    # HISTÓRICO
    # --------------------------------------------------
    historico = models.HistoricoAtividadeN2(

        ID_ATIVIDADE=atividade.ID_ATIVIDADE,

        MATRICULA_RESPONSAVEL=atividade.MATRICULA,

        NOME_USUARIO=atividade.NOME_USUARIO,

        TIPO_EVENTO="STATUS_ATUALIZADO",

        DESCRICAO_EVENTO=f"Status alterado para {atividade.STATUS}.",

        DATA_EVENTO=datetime.now()
    )

    db.add(historico)

    db.commit()

    return {
        "mensagem": "Status atualizado com sucesso",
        "id_atividade": atividade.ID_ATIVIDADE,
        "status": atividade.STATUS,
        "tempo_real_min": atividade.TEMPO_REAL_MIN
    }




# ---------- ROTA: GET - HISTÓRICO DA ATIVIDADE ----------
# ------ https://10.126.112.251:9001/atividade-n2/{id_atividade }/historico
@router.get(
    "/{id_atividade}/historico"
)
def listar_historico(
    id_atividade: int,
    db: Session = Depends(get_db)
):

    historico = (
        db.query(models.HistoricoAtividadeN2)
        .filter(
            models.HistoricoAtividadeN2.ID_ATIVIDADE == id_atividade
        )
        .order_by(
            models.HistoricoAtividadeN2.DATA_EVENTO.desc()
        )
        .all()
    )

    return [
        {
            "id_historico": item.ID_HISTORICO,
            "id_atividade": item.ID_ATIVIDADE,
            "matricula_responsavel": item.MATRICULA_RESPONSAVEL,
            "nome_usuario": item.NOME_USUARIO,
            "tipo_evento": item.TIPO_EVENTO,
            "descricao_evento": item.DESCRICAO_EVENTO,
            "data_evento": item.DATA_EVENTO,
        }
        for item in historico
    ]



# ---------- ROTA: PUT - ATUALIZAR OBSERVAÇÕES ----------
# ------- https://10.126.112.251:9001/atividade-n2/{id_atividade}/observacoes
@router.put(
    "/{id_atividade}/observacoes"
)
def atualizar_observacoes(
    id_atividade: int,
    payload: schemas.AtualizarObservacao,
    db: Session = Depends(get_db)
):

    atividade = (
        db.query(models.AtividadeSuporte)
        .filter(
            models.AtividadeSuporte.ID_ATIVIDADE == id_atividade
        )
        .first()
    )

    if not atividade:
        raise HTTPException(
            status_code=404,
            detail="Atividade não encontrada."
        )

    atividade.OBSERVACOES = payload.observacoes

    db.commit()
    db.refresh(atividade)

    # --------------------------------------------------
    # HISTÓRICO
    # --------------------------------------------------
    historico = models.HistoricoAtividadeN2(

        ID_ATIVIDADE=atividade.ID_ATIVIDADE,

        MATRICULA_RESPONSAVEL=atividade.MATRICULA,

        NOME_USUARIO=atividade.NOME_USUARIO,

        TIPO_EVENTO="OBSERVACAO_ATUALIZADA",

        DESCRICAO_EVENTO="Observação atualizada.",

        DATA_EVENTO=datetime.now()
    )

    db.add(historico)

    db.commit()

    return {
        "mensagem": "Observação atualizada com sucesso.",
        "id_atividade": atividade.ID_ATIVIDADE,
        "observacoes": atividade.OBSERVACOES
    }





# ---------- ROTA: TA ATIVOS ----------
# ------- https://10.126.112.251:9001/atividade-n2/ta/ativos
# ------- https://10.126.112.251:9001/atividade-n2/ta/ativos?page=1&page_size=10

@router.get(
    "/ta/ativos",
    response_model=schemas.PaginacaoTA
)
def listar_ta_ativos(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):

    # --------------------------------------------------
    # TOTAL DE REGISTROS
    # --------------------------------------------------
    total_query = text("""
        SELECT COUNT(*) AS total
        FROM TBL_ACOMPANHAMENTO_N2_ATIVOS
    """)

    total = db.execute(total_query).scalar()

    if total == 0:
        return {
            "data": [],
            "page": page,
            "page_size": page_size,
            "total": 0,
            "total_pages": 0
        }

    total_pages = ceil(total / page_size)

    offset = (page - 1) * page_size

    # --------------------------------------------------
    # DADOS PAGINADOS
    # --------------------------------------------------
    dados_query = text("""
        SELECT *
        FROM TBL_ACOMPANHAMENTO_N2_ATIVOS
        LIMIT :limit
        OFFSET :offset
    """)

    registros = (
        db.execute(
            dados_query,
            {
                "limit": page_size,
                "offset": offset
            }
        )
        .mappings()
        .all()
    )

    return {
        "data": [dict(row) for row in registros],
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages
    }





# ---------- ROTA: TA FECHADOS ----------
# ------- https://10.126.112.251:9001/atividade-n2/ta/fechados
# ------ https://10.126.112.251:9001/atividade-n2/ta/fechados?page=1&page_size=10

@router.get(
    "/ta/fechados",
    response_model=schemas.PaginacaoTA
)
def listar_ta_fechados(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):

    # --------------------------------------------------
    # TOTAL DE REGISTROS
    # --------------------------------------------------
    total_query = text("""
        SELECT COUNT(*) AS total
        FROM TBL_ACOMPANHAMENTO_N2_FECHADO
    """)

    total = db.execute(total_query).scalar()

    if total == 0:
        return {
            "data": [],
            "page": page,
            "page_size": page_size,
            "total": 0,
            "total_pages": 0
        }

    total_pages = ceil(total / page_size)

    offset = (page - 1) * page_size

    # --------------------------------------------------
    # DADOS PAGINADOS
    # --------------------------------------------------
    dados_query = text("""
        SELECT *
        FROM TBL_ACOMPANHAMENTO_N2_FECHADO
        LIMIT :limit
        OFFSET :offset
    """)

    registros = (
        db.execute(
            dados_query,
            {
                "limit": page_size,
                "offset": offset
            }
        )
        .mappings()
        .all()
    )

    return {
        "data": [dict(row) for row in registros],
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages
    }




# ---------- ROTA: TA UNIFICADO ----------
# ------- GET https://10.126.112.251:9001/atividade-n2/ta-ativos-fechados
@router.get(
    "/ta-ativos-fechados"
)
def listar_ta_unificado(
    data_inicio: date = Query(
        ...,
        description="Data inicial (YYYY-MM-DD)"
    ),
    data_fim: date = Query(
        ...,
        description="Data final (YYYY-MM-DD)"
    ),
    db: Session = Depends(get_db)
):

    dados_query = text("""
        SELECT *
        FROM (

            SELECT
                *,
                'ATIVO' AS origem_tabela
            FROM TBL_ACOMPANHAMENTO_N2_ATIVOS

            UNION ALL

            SELECT
                *,
                'FECHADO' AS origem_tabela
            FROM TBL_ACOMPANHAMENTO_N2_FECHADO

        ) t

        WHERE data_criacao >= :data_inicio
          AND data_criacao < DATE_ADD(:data_fim, INTERVAL 1 DAY)

        ORDER BY data_criacao DESC
    """)

    registros = (
        db.execute(
            dados_query,
            {
                "data_inicio": data_inicio,
                "data_fim": data_fim
            }
        )
        .mappings()
        .all()
    )

    return [
        dict(row)
        for row in registros
    ]
#buscar por ano: https://10.126.112.251:9001/atividade-n2/ta-ativos-fechados?data_inicio=2026-01-01&data_fim=2026-12-31
#buscar por mês específico: https://10.126.112.251:9001/atividade-n2/ta-ativos-fechados?data_inicio=2026-07-01&data_fim=2026-07-31
#buscar por dia específico: https://10.126.112.251:9001/atividade-n2/ta-ativos-fechados?data_inicio=2026-07-15&data_fim=2026-07-15
#buscar por semana específica: https://10.126.112.251:9001/atividade-n2/ta-ativos-fechados?data_inicio=2026-07-11&data_fim=2026-07-17




# # ---------- ROTA: TA UNIFICADO ----------
# # ------- GET https://10.126.112.251:9001/atividade-n2/ta-ativos-fechados

# @router.get(
#     "/ta-ativos-fechados"
# )
# def listar_ta_unificado(
#     db: Session = Depends(get_db)
# ):

#     dados_query = text("""
#         SELECT *
#         FROM (

#             SELECT
#                 *,
#                 'ATIVO' AS origem_tabela
#             FROM TBL_ACOMPANHAMENTO_N2_ATIVOS

#             UNION ALL

#             SELECT
#                 *,
#                 'FECHADO' AS origem_tabela
#             FROM TBL_ACOMPANHAMENTO_N2_FECHADO

#         ) t

#         ORDER BY data_criacao DESC
#     """)

#     registros = (
#         db.execute(dados_query)
#         .mappings()
#         .all()
#     )

#     return [dict(row) for row in registros]



# ---------- ROTA: DASHBOARD VOLUMETRIA ----------
# ------- GET /atividade-n2/volumetria

@router.get(
    "/volumetria",
    response_model=List[schemas.VolumetriaTA]
)
def dashboard_volumetria(
    db: Session = Depends(get_db)
):

    query = text("""
            WITH ANALITICO AS (
    SELECT *
    FROM NOC.TBL_ACOMPANHAMENTO_N2_ATIVOS
    UNION ALL
    SELECT *
    FROM NOC.TBL_ACOMPANHAMENTO_N2_FECHADO
)
SELECT
    CAST(YEAR(DATA_ENTRADA_N2) AS CHAR) AS ANO,
    LPAD(CAST(MONTH(DATA_ENTRADA_N2) AS CHAR), 2,'0') AS MES,
    '' AS SEMANA,
    '' AS DIA,
    '' AS HORA,
    'ANO_MES' AS VISAO,
    TIPO_BILHETE,
    TEVE_ATUACAO,
    COUNT(DISTINCT CONCAT(ORIGEM, '|', DATA_ENTRADA_N2)) AS TOTAL
FROM ANALITICO
GROUP BY
    CAST(YEAR(DATA_ENTRADA_N2) AS CHAR),
    LPAD(CAST(MONTH(DATA_ENTRADA_N2) AS CHAR), 2,'0'),
    TIPO_BILHETE,
    TEVE_ATUACAO
UNION ALL
SELECT
    CAST(YEAR(DATA_ENTRADA_N2) AS CHAR) AS ANO,
    '' AS MES,
    CAST(WEEK(DATA_ENTRADA_N2, 1) AS CHAR) AS SEMANA,
    '' AS DIA,
    '' AS HORA,
    'SEMANAL' AS VISAO,
    TIPO_BILHETE,
    TEVE_ATUACAO,
    COUNT(DISTINCT CONCAT(ORIGEM, '|', DATA_ENTRADA_N2)) AS TOTAL
FROM ANALITICO
GROUP BY
    CAST(YEAR(DATA_ENTRADA_N2) AS CHAR),
    CAST(WEEK(DATA_ENTRADA_N2, 1) AS CHAR),
    TIPO_BILHETE,
    TEVE_ATUACAO
UNION ALL
SELECT
    CAST(YEAR(DATA_ENTRADA_N2) AS CHAR) AS ANO,
    '' AS MES,
    '' AS SEMANA,
    DATE(DATA_ENTRADA_N2) AS DIA,
    '' AS HORA,
    'DIARIO' AS VISAO,
    TIPO_BILHETE,
    TEVE_ATUACAO AS TEVE_ATUACAO,
    COUNT(DISTINCT CONCAT(ORIGEM, '|', DATA_ENTRADA_N2)) AS TOTAL
FROM ANALITICO
WHERE DATA_ENTRADA_N2 >= DATE_SUB(
    CURDATE(),
    INTERVAL 31 DAY)
GROUP BY
    CAST(YEAR(DATA_ENTRADA_N2) AS CHAR),
    DATE(DATA_ENTRADA_N2),
    TIPO_BILHETE,
    TEVE_ATUACAO;
    """)

    registros = (
        db.execute(query)
        .mappings()
        .all()
    )

    return [
        {
            "ano": row["ANO"],
            "mes": row["MES"],
            "semana": row["SEMANA"],
            "dia": row["DIA"],
            "hora": row["HORA"],
            "visao": row["VISAO"],
            "tipo_bilhete": row["TIPO_BILHETE"],
            "teve_atuacao": row["TEVE_ATUACAO"],
            "total": row["TOTAL"]
        }
        for row in registros
    ]



# ---------- ROTA: DASHBOARD VOLUMETRIA USUARIO----------
# ------- GET /atividade-n2/volumetriausuario

@router.get(
    "/volumetriausuario",
    response_model=List[schemas.VolumetriaUsuario]
)
def dashboard_volumetria(
    db: Session = Depends(get_db)
):

    query = text("""
                   WITH ANALITICO AS (
    SELECT *
    FROM NOC.TBL_ACOMPANHAMENTO_N2_ATIVOS
    WHERE USUARIO_ATUACAO IS NOT NULL
    UNION ALL
    SELECT *
    FROM NOC.TBL_ACOMPANHAMENTO_N2_FECHADO
    WHERE USUARIO_ATUACAO IS NOT NULL
)
SELECT
    CAST(YEAR(DATA_ENTRADA_N2) AS CHAR) AS ANO,
    LPAD(CAST(MONTH(DATA_ENTRADA_N2) AS CHAR), 2,'0') AS MES,
    '' AS SEMANA,
    '' AS DIA,
    '' AS HORA,
    'ANO_MES' AS VISAO,
    TIPO_BILHETE,
    USUARIO_ATUACAO,
    COUNT(DISTINCT CONCAT(ORIGEM, '|', DATA_ENTRADA_N2)) AS TOTAL
FROM ANALITICO
GROUP BY
    CAST(YEAR(DATA_ENTRADA_N2) AS CHAR),
    LPAD(CAST(MONTH(DATA_ENTRADA_N2) AS CHAR), 2,'0'),
    TIPO_BILHETE,
    USUARIO_ATUACAO
UNION ALL
SELECT
    CAST(YEAR(DATA_ENTRADA_N2) AS CHAR) AS ANO,
    '' AS MES,
    CAST(WEEK(DATA_ENTRADA_N2, 1) AS CHAR) AS SEMANA,
    '' AS DIA,
    '' AS HORA,
    'SEMANAL' AS VISAO,
    TIPO_BILHETE,
    USUARIO_ATUACAO,
    COUNT(DISTINCT CONCAT(ORIGEM, '|', DATA_ENTRADA_N2)) AS TOTAL
FROM ANALITICO
GROUP BY
    CAST(YEAR(DATA_ENTRADA_N2) AS CHAR),
    CAST(WEEK(DATA_ENTRADA_N2, 1) AS CHAR),
    TIPO_BILHETE,
    USUARIO_ATUACAO
UNION ALL
SELECT
    CAST(YEAR(DATA_ENTRADA_N2) AS CHAR) AS ANO,
    '' AS MES,
    '' AS SEMANA,
    DATE(DATA_ENTRADA_N2) AS DIA,
    '' AS HORA,
    'DIARIO' AS VISAO,
    TIPO_BILHETE,
    USUARIO_ATUACAO,
    COUNT(DISTINCT CONCAT(ORIGEM, '|', DATA_ENTRADA_N2)) AS TOTAL
FROM ANALITICO
WHERE DATA_ENTRADA_N2 >= DATE_SUB(
    CURDATE(),
    INTERVAL 31 DAY)
GROUP BY
    CAST(YEAR(DATA_ENTRADA_N2) AS CHAR),
    DATE(DATA_ENTRADA_N2),
    TIPO_BILHETE,
    USUARIO_ATUACAO
    """)

    registros = (
        db.execute(query)
        .mappings()
        .all()
    )

    return [
        {
            "ano": row["ANO"],
            "mes": row["MES"],
            "semana": row["SEMANA"],
            "dia": row["DIA"],
            "hora": row["HORA"],
            "visao": row["VISAO"],
            "tipo_bilhete": row["TIPO_BILHETE"],
            "usuario_atuacao": row["USUARIO_ATUACAO"],
            "total": row["TOTAL"]
        }
        for row in registros
    ]



# ---------- ROTA: DASHBOARD GRAFICO TMA----------
# ------- GET /atividade-n2/tma
@router.get(
    "/tma",
    response_model=List[schemas.tma]
)
def dashboard_volumetria(
    db: Session = Depends(get_db)
):

    query = text("""
WITH ANALITICO AS (
       SELECT *
    FROM NOC.TBL_ACOMPANHAMENTO_N2_ATIVOS
    UNION ALL
    SELECT *
    FROM NOC.TBL_ACOMPANHAMENTO_N2_FECHADO
)
SELECT
    CAST(YEAR(DATA_ENTRADA_N2) AS CHAR) AS ANO,
    LPAD(MONTH(DATA_ENTRADA_N2),2,'0') AS MES,
    '' AS SEMANA,
    '' AS DIA,
    'ANO_MES' AS VISAO,
    SEC_TO_TIME(
        AVG(TIME_TO_SEC(tma_n2))
    ) AS TMA_MEDIO
FROM ANALITICO
GROUP BY
    CAST(YEAR(DATA_ENTRADA_N2) AS CHAR),
    LPAD(MONTH(DATA_ENTRADA_N2),2,'0')
UNION ALL
SELECT
    CAST(YEAR(DATA_ENTRADA_N2) AS CHAR) AS ANO,
    '' AS MES,
    CAST(WEEK(DATA_ENTRADA_N2,1) AS CHAR) AS SEMANA,
    '' AS DIA,
    'SEMANAL' AS VISAO,
    SEC_TO_TIME(
        AVG(TIME_TO_SEC(tma_n2))
    ) AS TMA_MEDIO
FROM ANALITICO
GROUP BY
    CAST(YEAR(DATA_ENTRADA_N2) AS CHAR),
    CAST(WEEK(DATA_ENTRADA_N2,1) AS CHAR)
UNION ALL
SELECT
    CAST(YEAR(DATA_ENTRADA_N2) AS CHAR) AS ANO,
    '' AS MES,
    '' AS SEMANA,
    DATE(DATA_ENTRADA_N2) AS DIA,
    'DIARIO' AS VISAO,
    SEC_TO_TIME(
        AVG(TIME_TO_SEC(tma_n2))
    ) AS TMA_MEDIO
FROM ANALITICO
WHERE DATA_ENTRADA_N2 >= DATE_SUB(
    CURDATE(),
    INTERVAL 31 DAY)
GROUP BY
    CAST(YEAR(DATA_ENTRADA_N2) AS CHAR),
DATE(DATA_ENTRADA_N2);
    """)

    registros = (
        db.execute(query)
        .mappings()
        .all()
    )


    return [
        {
            "ano": row["ANO"],
            "mes": row["MES"],
            "semana": row["SEMANA"],
            "dia": row["DIA"],
            "visao": row["VISAO"],
            "tma_medio": format_timedelta(row["TMA_MEDIO"])
        }
        for row in registros
    ]



# ---------- ROTA: UPLOAD DE ARQUIVOS ----------
# ------- POST /atividade-n2/upload-arquivos
# ------- https://10.126.112.251:9001/atividade-n2/upload-arquivos
# ------- https://10.126.112.251:9001/atividade-n2/upload-arquivos?id_atividade=1

@router.post(
    "/upload-arquivos",
    response_model=List[schemas.ArquivoAtividadeOut],
    status_code=status.HTTP_201_CREATED,
)
async def upload_arquivos(
    id_atividade: int,
    arquivos: Optional[List[UploadFile]] = File(None),
    arquivo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):

    # --------------------------------------------------
    # VALIDAR ATIVIDADE
    # --------------------------------------------------
    atividade = (
        db.query(models.AtividadeSuporte)
        .filter(
            models.AtividadeSuporte.ID_ATIVIDADE == id_atividade
        )
        .first()
    )

    if not atividade:
        raise HTTPException(
            status_code=404,
            detail="Atividade não encontrada."
        )

    # --------------------------------------------------
    # VALIDAR ARQUIVOS
    # --------------------------------------------------
    if not arquivos and not arquivo:
        raise HTTPException(
            status_code=400,
            detail="Nenhum arquivo enviado."
        )

    lista_arquivos = []

    if arquivos:
        lista_arquivos.extend(
            [a for a in arquivos if a and a.filename]
        )

    if arquivo and arquivo.filename:
        lista_arquivos.append(arquivo)

    if not lista_arquivos:
        raise HTTPException(
            status_code=400,
            detail="Nenhum arquivo válido enviado."
        )

    arquivos_salvos = []

    # --------------------------------------------------
    # PROCESSAR ARQUIVOS
    # --------------------------------------------------
    for arquivo_upload in lista_arquivos:

        nome_original = arquivo_upload.filename

        _, ext = os.path.splitext(nome_original)

        nome_arquivo = (
            f"{os.urandom(16).hex()}{ext}"
        )

        caminho_fisico = os.path.join(
            UPLOAD_DIR,
            nome_arquivo
        )

        conteudo = await arquivo_upload.read()

        try:

            with open(caminho_fisico, "wb") as f:
                f.write(conteudo)

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao salvar arquivo: {str(e)}"
            )

        novo_arquivo = models.ArquivoAtividadeN2(

            ID_ATIVIDADE=id_atividade,

            NOME_ORIGINAL=nome_original,

            NOME_ARQUIVO=nome_arquivo,

            CAMINHO=caminho_fisico,

            CONTENT_TYPE=arquivo_upload.content_type,

            TAMANHO_BYTES=len(conteudo),

            DATA_UPLOAD=datetime.now()
        )

        db.add(novo_arquivo)

        db.commit()

        db.refresh(novo_arquivo)

        arquivos_salvos.append(novo_arquivo)

        # --------------------------------------------------
        # HISTÓRICO
        # --------------------------------------------------
        historico = models.HistoricoAtividadeN2(

            ID_ATIVIDADE=id_atividade,

            MATRICULA_RESPONSAVEL=atividade.MATRICULA,

            NOME_USUARIO=atividade.NOME_USUARIO,

            TIPO_EVENTO="ARQUIVO_ANEXADO",

            DESCRICAO_EVENTO=(
                f"Arquivo anexado: {nome_original}"
            ),

            DATA_EVENTO=datetime.now()
        )

        db.add(historico)

        db.commit()

    # --------------------------------------------------
    # RETORNO
    # --------------------------------------------------
    return [
        {
            "id_arquivo": item.ID_ARQUIVO,
            "id_atividade": item.ID_ATIVIDADE,
            "nome_original": item.NOME_ORIGINAL,
            "nome_arquivo": item.NOME_ARQUIVO,
            "caminho": item.CAMINHO,
            "content_type": item.CONTENT_TYPE,
            "tamanho_bytes": item.TAMANHO_BYTES,
            "data_upload": item.DATA_UPLOAD,

            "url_download": 
                f"/atividade-n2/arquivo/{item.ID_ARQUIVO}"
        }
        for item in arquivos_salvos
    ]




# ---------- ROTA: LISTAR ARQUIVOS DA ATIVIDADE ----------
# ------- GET /atividade-n2/{id_atividade}/arquivos
# ------- https://10.126.112.251:9001/atividade-n2/3/arquivos

@router.get(
    "/{id_atividade}/arquivos",
    response_model=List[schemas.ArquivoAtividadeOut]
)
def listar_arquivos_atividade(
    id_atividade: int,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------
    # VALIDAR ATIVIDADE
    # --------------------------------------------------
    atividade = (
        db.query(models.AtividadeSuporte)
        .filter(
            models.AtividadeSuporte.ID_ATIVIDADE == id_atividade
        )
        .first()
    )

    if not atividade:
        raise HTTPException(
            status_code=404,
            detail="Atividade não encontrada."
        )

    # --------------------------------------------------
    # BUSCAR ARQUIVOS
    # --------------------------------------------------
    arquivos = (
        db.query(models.ArquivoAtividadeN2)
        .filter(
            models.ArquivoAtividadeN2.ID_ATIVIDADE == id_atividade
        )
        .order_by(
            models.ArquivoAtividadeN2.DATA_UPLOAD.desc()
        )
        .all()
    )

    return [
        {
            "id_arquivo": item.ID_ARQUIVO,
            "id_atividade": item.ID_ATIVIDADE,
            "nome_original": item.NOME_ORIGINAL,
            "nome_arquivo": item.NOME_ARQUIVO,

            # manter ou remover conforme necessidade
            "caminho": item.CAMINHO,

            "content_type": item.CONTENT_TYPE,
            "tamanho_bytes": item.TAMANHO_BYTES,
            "data_upload": item.DATA_UPLOAD,

            "url_download":
                f"/atividade-n2/arquivo/{item.ID_ARQUIVO}"
        }
        for item in arquivos
    ]





# ---------- ROTA: DOWNLOAD DE ARQUIVO ----------
# ------- GET /atividade-n2/arquivo/{id_arquivo}

@router.get(
    "/arquivo/{id_arquivo}"
)
def download_arquivo(
    id_arquivo: int,
    db: Session = Depends(get_db)
):

    arquivo = (
        db.query(models.ArquivoAtividadeN2)
        .filter(
            models.ArquivoAtividadeN2.ID_ARQUIVO == id_arquivo
        )
        .first()
    )

    if not arquivo:
        raise HTTPException(
            status_code=404,
            detail="Arquivo não encontrado."
        )

    if not os.path.exists(arquivo.CAMINHO):
        raise HTTPException(
            status_code=404,
            detail="Arquivo físico não encontrado."
        )

    return FileResponse(
        path=arquivo.CAMINHO,
        filename=arquivo.NOME_ORIGINAL,
        media_type=arquivo.CONTENT_TYPE
    )





# ---------- ROTA: GET - OBTER ATIVIDADE POR ID ----------
# ------ https://10.126.112.251:9001/atividade-n2/{id_atividade}
@router.get(
    "/{id_atividade}",
    response_model=schemas.AtividadeSuporteRead
)
def obter_atividade(
    id_atividade: int,
    db: Session = Depends(get_db)
):

    atividade = (
        db.query(
            models.AtividadeSuporte,
            models.AtividadePadrao
        )
        .join(
            models.AtividadePadrao,
            models.AtividadePadrao.ID ==
            models.AtividadeSuporte.ID_ATIVIDADE_PADRAO
        )
        .filter(
            models.AtividadeSuporte.ID_ATIVIDADE ==
            id_atividade
        )
        .first()
    )

    if not atividade:
        raise HTTPException(
            status_code=404,
            detail="Atividade não encontrada."
        )

    atividade_suporte, atividade_padrao = atividade

    # --------------------------------------------
    # ARQUIVOS DA ATIVIDADE
    # --------------------------------------------
    arquivos_db = (
        db.query(models.ArquivoAtividadeN2)
        .filter(
            models.ArquivoAtividadeN2.ID_ATIVIDADE ==
            atividade_suporte.ID_ATIVIDADE
        )
        .all()
    )

    arquivos_out = [
        {
            "id_arquivo": arquivo.ID_ARQUIVO,
            "id_atividade": arquivo.ID_ATIVIDADE,
            "nome_original": arquivo.NOME_ORIGINAL,
            "nome_arquivo": arquivo.NOME_ARQUIVO,
            "caminho": arquivo.CAMINHO,
            "content_type": arquivo.CONTENT_TYPE,
            "tamanho_bytes": arquivo.TAMANHO_BYTES,
            "data_upload": arquivo.DATA_UPLOAD,
        }
        for arquivo in arquivos_db
    ]

    return {
        "id_atividade":
            atividade_suporte.ID_ATIVIDADE,

        "matricula":
            atividade_suporte.MATRICULA,

        "nome_usuario":
            atividade_suporte.NOME_USUARIO,

        "id_atividade_padrao":
            atividade_suporte.ID_ATIVIDADE_PADRAO,

        "nome_atividade":
            atividade_padrao.NOME_ATIVIDADE,

        "status":
            atividade_suporte.STATUS,

        "data_inicio":
            atividade_suporte.DATA_INICIO,

        "data_fim":
            atividade_suporte.DATA_FIM,

        "tempo_estimado_min":
            atividade_suporte.TEMPO_ESTIMADO_MIN,

        "tempo_real_min":
            atividade_suporte.TEMPO_REAL_MIN,

        "observacoes":
            atividade_suporte.OBSERVACOES,

        "arquivo":
            arquivos_out
    }







# # ---------- ROTA: TA UNIFICADO - PAGINADO ----------
# # ------- GET /atividade-n2/ta-ativos-fechados
# # ------- GET /atividade-n2/ta-ativos-fechados?page=1&page_size=50

# @router.get(
#     "/ta-ativos-fechados",
#     response_model=schemas.PaginacaoTA
# )
# def listar_ta_unificado(
#     page: int = Query(1, ge=1),
#     page_size: int = Query(50, ge=1, le=200),
#     db: Session = Depends(get_db)
# ):

#     # --------------------------------------------------
#     # TOTAL DE REGISTROS
#     # --------------------------------------------------
#     total_query = text("""
#         SELECT COUNT(*) AS total
#         FROM (

#             SELECT origem
#             FROM TBL_ACOMPANHAMENTO_N2_ATIVOS

#             UNION ALL

#             SELECT origem
#             FROM TBL_ACOMPANHAMENTO_N2_FECHADO

#         ) t
#     """)

#     total = db.execute(total_query).scalar()

#     if total == 0:
#         return {
#             "data": [],
#             "page": page,
#             "page_size": page_size,
#             "total": 0,
#             "total_pages": 0
#         }

#     total_pages = ceil(total / page_size)

#     offset = (page - 1) * page_size

#     # --------------------------------------------------
#     # DADOS PAGINADOS
#     # --------------------------------------------------
#     dados_query = text("""
#         SELECT *
#         FROM (

#             SELECT
#                 *,
#                 'ATIVO' AS origem_tabela
#             FROM TBL_ACOMPANHAMENTO_N2_ATIVOS

#             UNION ALL

#             SELECT
#                 *,
#                 'FECHADO' AS origem_tabela
#             FROM TBL_ACOMPANHAMENTO_N2_FECHADO

#         ) t

#         LIMIT :limit
#         OFFSET :offset
#     """)

#     registros = (
#         db.execute(
#             dados_query,
#             {
#                 "limit": page_size,
#                 "offset": offset
#             }
#         )
#         .mappings()
#         .all()
#     )

#     return {
#         "data": [dict(row) for row in registros],
#         "page": page,
#         "page_size": page_size,
#         "total": total,
#         "total_pages": total_pages
#     }
