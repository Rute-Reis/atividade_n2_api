# ------------------------------------------ ajuste e rodar versão com procedimento --------------------------------------------------------- #


import oracledb
import pandas as pd
import concurrent.futures
from datetime import datetime, timedelta
import os
from tqdm import tqdm
from urllib.parse import quote_plus
from sqlalchemy import create_engine, text
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import timedelta
import numpy as np
from email.message import EmailMessage
import smtplib
from email.message import EmailMessage
import os

## SIGITM
username="NOC_PROJETOS"
password="X;W2izyd"
host="10.240.47.114"
port=1521
service_name="SIGITM"
sigitm = create_engine(f'oracle+oracledb://{username}:{password}@{host}:{port}/?service_name={service_name}')

## VM WINDOWS
user_base="rodrigo"
pass_base=quote_plus("aQ1>tH8;jA")
host_base="10.8.141.212"
nexus = create_engine(f'mysql+pymysql://{user_base}:{pass_base}@{host_base}/nexus') 

## NEXUS
user_base = "dev"
pass_base = quote_plus("Server@noc1")
host_base = "10.126.112.251"
engine_noc = create_engine(f'mysql+pymysql://{user_base}:{pass_base}@{host_base}/NOC')

## BPI
oracle_password = quote_plus('GDJ3#kl2Fw1')
bpi = create_engine(f'oracle+oracledb://NOC_AD:{oracle_password}@10.215.39.45:1521/RIOREDESPRD')


## SCIENCE
science_password = quote_plus('hut5Ryt#juH')
science = create_engine(f'oracle+oracledb://NOC_AD:{science_password}@10.240.2.12:1521/SMAPBCV')


## ALTAIA
altaia_password = quote_plus('vivo15vivo')
altaia = create_engine(f'oracle+oracledb://a0095640:{altaia_password}@10.240.52.207:1521/?service_name=dbn1')


# oracledb.init_oracle_client(lib_dir=r"C:\Users\A0169662\OneDrive - Telefonica\Analitycs\instantclient-basic-windows.x64-23.7.0.25.01\instantclient_23_7")
oracledb.defaults.arraysize = 10000
oracledb.defaults.prefetchrows = 10000




# Ex.: engine com pool (ajuste a URL Oracle conforme seu ambiente)
# engine = create_engine("oracle+cx_oracle://user:pwd@host:port/?service_name=...", pool_size=5, max_overflow=5)

#============================================================================TA´S_ATIVOS==============================================================
#
tipo_ciclo = 'diario'

def gerar_intervalos(inicio, fim, tipo='diario'):
    intervalos = []
    atual = inicio.replace(hour=0, minute=0, second=0, microsecond=0)
    fim = fim.replace(hour=0, minute=0, second=0, microsecond=0)
    while atual < fim:
        if tipo == 'mensal':
            proximo = (atual.replace(day=1) + timedelta(days=32)).replace(day=1)
        elif tipo == 'semanal':
            proximo = atual + timedelta(weeks=1)
        elif tipo == 'diario':
            proximo = atual + timedelta(days=1)
        else:
            raise ValueError("Tipo inválido")
        intervalos.append((
            atual.strftime('%Y-%m-%d 00:00:00'),
            min(proximo, fim).strftime('%Y-%m-%d 00:00:00')
        ))
        atual = proximo
    return intervalos

def consulta_por_mes(data_inicio, data_fim):
    # Abra a conexão dentro da thread
    with sigitm.connect() as conn:
        query = text("""
         SELECT           
             TA.TQA_CODIGO AS ORIGEM,
             TAE.TQA_CODIGO AS ELEMENTO,
             TA.TQA_RAIZ AS TA_RAIZ,
             STAT.STA_NOME AS STATUS,
             TAE.TQA_AREA_CODIGO AS SITE, 
             TAE.TQA_ESTADO_CODIGO AS UF,
             TA.TQA_GERENCIA_CODIGO AS REGIONAL,
             TA.TQA_DATA_CRIACAO AS DATA_CRIACAO,
             TA.TQA_DATA_ENCERRAMENTO AS DATA_ENCERRAMENTO,
             TA.TQA_TIPO_BILHETE AS TIPO_BILHETE,
             TA.TQA_TIPO_SITE AS TIPO_SITE,
             TA.TQA_ALARME_TIPO AS TIPO_DE_ALARME,
             EQP.AEQ_HOSTNAME AS HOSTNAME,
             EQP.AEQ_FABRICANTE AS FABRICANTE,
             TAE.TQA_IMPACTO_EQP AS IMPACTO,
             GRP2.GRP_NOME AS GRUPO_RESPONSAVEL,
                CASE 
                 WHEN EXISTS
                 (SELECT GRP2.GRP_NOME
                  FROM SIGITM3.TBL_TA_VIDA VD2
                  INNER JOIN SIGITM3.TBL_GRUPOS GRP2 ON VD2.VDA_RESPONSAVELPOR_GRUPO = GRP2.GRP_CODIGO
                  WHERE VD2.VDA_TA = TA.TQA_CODIGO 
                  AND VD2.VDA_RESPONSAVELPOR_GRUPO = '6611')
                  THEN 'SIM'
                  ELSE 'NÃO'
             END AS PASSOU_PELO_ACESSO_ERICSON,
             CASE 
                 WHEN EXISTS
                 (SELECT GRP2.GRP_NOME
                  FROM SIGITM3.TBL_TA_VIDA VD2
                  INNER JOIN SIGITM3.TBL_GRUPOS GRP2 ON VD2.VDA_RESPONSAVELPOR_GRUPO = GRP2.GRP_CODIGO
                  WHERE VD2.VDA_TA = TA.TQA_CODIGO 
                  AND VD2.VDA_RESPONSAVELPOR_GRUPO = '6612')
                  THEN 'SIM'
                  ELSE 'NÃO'
             END AS PASSOU_PELO_ACESSO_HUAWEI,
             CASE
                 WHEN EXISTS (
                     SELECT 1
                     FROM SIGITM3.TBL_TA_VIDA v
                     INNER JOIN SIGITM3.TBL_GRUPOS GRP ON GRP.GRP_CODIGO = V.VDA_RESPONSAVELPOR_GRUPO
                     WHERE V.VDA_TA = TA.TQA_CODIGO           
                     AND GRP.GRP_PAI = 1340
                 )
                 THEN 'SIM'
                 ELSE 'NÃO'
             END AS PASSOU_PELO_CAMPO,
             CASE 
                 WHEN EXISTS
                 (SELECT GRP2.GRP_NOME
                  FROM SIGITM3.TBL_TA_VIDA VD2
                  INNER JOIN SIGITM3.TBL_GRUPOS GRP2 ON VD2.VDA_RESPONSAVELPOR_GRUPO = GRP2.GRP_CODIGO
                  WHERE VD2.VDA_TA = TA.TQA_CODIGO 
                  AND VD2.VDA_RESPONSAVELPOR_GRUPO = '6563')
                  THEN 'SIM'
                  ELSE 'NÃO'
             END AS PASSOU_PELO_CORAN
             FROM
             SIGITM3.TBL_TA TA
             LEFT JOIN SIGITM3.TBL_TA TAE ON TAE.TQA_ORIGEM = TA.TQA_CODIGO
             LEFT JOIN SIGITM3.TBL_TA_EQUIPAMENTO EQP ON TAE.TQA_CODIGO = EQP.AEQ_TA
             LEFT JOIN SIGITM3.TBC_STATUS_TA STAT ON STAT.STA_CODIGO = TA.TQA_STATUS
             LEFT JOIN SIGITM3.TBL_GRUPOS GRP2 ON GRP2.GRP_CODIGO = TA.TQA_RESPONSAVELPOR_GRUPO
             INNER JOIN (
             SELECT DISTINCT
                 VD2.VDA_TA
             FROM SIGITM3.TBL_TA_VIDA VD2
                  LEFT JOIN SIGITM3.TBL_GRUPOS GRP2
                     ON VD2.VDA_RESPONSAVELPOR_GRUPO = GRP2.GRP_CODIGO
                  LEFT JOIN SIGITM3.TBL_PROCEDIMENTOS_TA P
                     ON P.PCA_TA = VD2.VDA_TA
             WHERE (
                 VD2.VDA_RESPONSAVELPOR_GRUPO IN ('6611', '6612')
                 OR P.PCA_GRUPO IN ('6611', '6612')
             )
         ) VIDA
             ON VIDA.VDA_TA = TA.TQA_CODIGO
             WHERE TA.TQA_ORIGEM IS NULL
             AND TA.TQA_TIPO_REDE IN ('701')
            -- AND TA.TQA_CODIGO IN ({ta_list_str})
             AND TA.TQA_STATUS IN ('10', '20', '70')
    AND TA.TQA_DATA_CRIACAO >= TO_DATE(:data_inicio, 'YYYY-MM-DD HH24:MI:SS') --sempre manter essa parte
    AND TA.TQA_DATA_CRIACAO <  TO_DATE(:data_fim,    'YYYY-MM-DD HH24:MI:SS') --sempre manter essa parte
        """)
        df = pd.read_sql(query, conn, params={
            "data_inicio": data_inicio,
            "data_fim": data_fim
        })
        return df

# Período total
data_inicio = datetime(2025, 1, 1)
data_atual = datetime.now()
# data_atual = datetime(2026, 7, 11)
# Intervalos diários

#trazer data - formato 2
data_atual = datetime.now()

# data_inicio = (
#     data_atual -
#     timedelta(days=182)
# )


periodos = gerar_intervalos(data_inicio, data_atual, tipo=tipo_ciclo)

resultados = []
max_workers = min(len(periodos), 8)  # evita sobrecarregar o BD

with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
    future_to_periodo = {
        executor.submit(consulta_por_mes, inicio, fim): (inicio, fim)
        for (inicio, fim) in periodos
    }
    for future in concurrent.futures.as_completed(future_to_periodo):
        inicio, fim = future_to_periodo[future]
        try:
            df = future.result()
            if df is not None and not df.empty:
                resultados.append(df)
            print(f"Consulta concluída para: {inicio} a {fim}")
        except Exception as e:
            print(f"Erro na consulta para {inicio} a {fim}: {e}")

if resultados:
    df_ta = pd.concat(resultados, ignore_index=True)
else:
    df_ta = pd.DataFrame()


df_ta = df_ta.drop_duplicates()




print("Linhas:", len(df_ta))

print(
    "TAs únicas:",
    df_ta['origem'].nunique()
)

print(
    "Duplicidades por origem:"
)

print(
    df_ta['origem']
    .value_counts()
    .head(20)
)

print("origem")
print(f"TAs encontrados: {len(df_ta)}")

print("Linhas:", len(df_ta))
print("TAs únicas:", df_ta["origem"].nunique())

# função que executa a query para um chunk
def query_chunk(ta_chunk):
    ta_list_str = ','.join([f"'{ta}'" for ta in ta_chunk])

    n2_bloqueio_sql = f"""
    WITH BASE_N2 AS (
            SELECT 
                V.VDA_TA AS ORIGEM,
                G.GRP_NOME AS GRUPO_N2,
                U.USR_NOME AS USUARIO_ATUACAO,
                V.VDA_RESPONSAVELPOR_USUARIO,
                V.VDA_DATA_INITIAL AS DATA_ENTRADA_N2,
                V.VDA_DATA_FINAL AS DATA_SAIDA_N2,
                CASE
                    WHEN V.VDA_RESPONSAVELPOR_USUARIO IS NOT NULL
                    THEN 'SIM'
                    ELSE 'NAO'
                END AS TEVE_ATUACAO,
                CASE
                    WHEN V.VDA_DATA_FINAL IS NULL
                    THEN 'SIM'
                    ELSE 'NAO'
                END AS AINDA_NA_FILA,
                ROUND(
                    (
                        COALESCE(
                            V.VDA_DATA_FINAL,
                            SYSDATE
                        )
                        -
                        V.VDA_DATA_INITIAL
                    ) * 86400
                ) AS TOTAL_SEGUNDOS,
                CASE
                    WHEN V.VDA_RESPONSAVELPOR_USUARIO IS NOT NULL
                    THEN ROUND(
                        (
                            COALESCE(
                                V.VDA_DATA_FINAL,
                                SYSDATE
                            )
                            -
                            V.VDA_DATA_INITIAL
                        ) * 86400
                    )
                    ELSE 0
                END AS TOTAL_SEGUNDOS_ATUACAO
            FROM SIGITM3.TBL_TA_VIDA V
            LEFT JOIN SIGITM3.TBL_GRUPOS G
                ON G.GRP_CODIGO = V.VDA_RESPONSAVELPOR_GRUPO
            LEFT JOIN SIGITM3.TBL_USUARIOS U
                ON U.USR_CODIGO = V.VDA_RESPONSAVELPOR_USUARIO
            WHERE V.VDA_TA IN ({ta_list_str})
              AND V.VDA_RESPONSAVELPOR_GRUPO IN (
                    6611,
                    6612
              )
        ),
        BASE_LAG AS (
            SELECT
                B.*,
                LAG(
                    B.VDA_RESPONSAVELPOR_USUARIO
                ) OVER (
                    PARTITION BY B.ORIGEM
                    ORDER BY B.DATA_ENTRADA_N2
                ) AS USUARIO_ANTERIOR
            FROM BASE_N2 B
        ),
        INICIO_ATUACAO AS (
            SELECT
                B.*,
                CASE
                    WHEN B.VDA_RESPONSAVELPOR_USUARIO IS NOT NULL
                         AND (
                                B.USUARIO_ANTERIOR IS NULL
                                OR B.USUARIO_ANTERIOR <> B.VDA_RESPONSAVELPOR_USUARIO)
                    THEN 1
                    ELSE 0
                END AS INICIO_ATUACAO,
                CASE
                    WHEN B.VDA_RESPONSAVELPOR_USUARIO IS NOT NULL
                         AND (
                                B.USUARIO_ANTERIOR IS NULL
                                OR B.USUARIO_ANTERIOR <> B.VDA_RESPONSAVELPOR_USUARIO)
                    THEN 1
                    ELSE 0
                END AS CONTAR_ATUACAO,
                CASE
                    WHEN B.VDA_RESPONSAVELPOR_USUARIO IS NULL
                    THEN 1
                    ELSE 0
                END AS CONTAR_SEM_ATUACAO
            FROM BASE_LAG B
        ),
        ATUACAO_RESUMO AS (
            SELECT
                ORIGEM,
                SUM(INICIO_ATUACAO) AS QUANTIDADE_ATUACAO
            FROM INICIO_ATUACAO
            GROUP BY ORIGEM
        )
        SELECT
            B.ORIGEM,
            B.GRUPO_N2,
            B.USUARIO_ATUACAO,
            B.DATA_ENTRADA_N2,
            B.DATA_SAIDA_N2,
            B.TEVE_ATUACAO,
            B.AINDA_NA_FILA,
            B.INICIO_ATUACAO,
            B.CONTAR_ATUACAO,
            B.CONTAR_SEM_ATUACAO,
            TRUNC(B.TOTAL_SEGUNDOS / 3600)|| ':' ||
            LPAD(TRUNC(MOD(B.TOTAL_SEGUNDOS, 3600) / 60), 2,'0')|| ':' ||
            LPAD(MOD(B.TOTAL_SEGUNDOS, 60), 2, '0') AS TEMPO_NO_GRUPO,
            TRUNC(B.TOTAL_SEGUNDOS / 3600)|| ':' ||
            LPAD(TRUNC(MOD(B.TOTAL_SEGUNDOS, 3600) / 60), 2,'0')|| ':' ||
            LPAD(MOD(B.TOTAL_SEGUNDOS, 60), 2, '0') AS TMA_N2,
            CASE
            WHEN B.TEVE_ATUACAO = 'SIM'
            THEN
                TRUNC(SUM(B.TOTAL_SEGUNDOS_ATUACAO)OVER (PARTITION BY B.ORIGEM) / 3600)|| ':' ||
                LPAD( TRUNC(MOD(SUM(B.TOTAL_SEGUNDOS_ATUACAO)OVER (PARTITION BY B.ORIGEM), 3600) / 60), 2,'0')|| ':' ||
                LPAD(MOD(SUM(B.TOTAL_SEGUNDOS_ATUACAO)OVER (PARTITION BY B.ORIGEM), 60), 2, '0')
            ELSE NULL
        END AS TEMPO_TOTAL_ATUACAO,
            CASE
            WHEN B.TEVE_ATUACAO = 'SIM'
            THEN A.QUANTIDADE_ATUACAO
            ELSE NULL
        END AS QUANTIDADE_ATUACAO,
            TRUNC(SUM(B.TOTAL_SEGUNDOS) OVER (PARTITION BY B.ORIGEM) / 3600)|| ':' ||
            LPAD(TRUNC(MOD(SUM(B.TOTAL_SEGUNDOS) OVER (PARTITION BY B.ORIGEM), 3600) / 60), 2, '0')|| ':' ||
            LPAD(MOD(SUM(B.TOTAL_SEGUNDOS) OVER (PARTITION BY B.ORIGEM), 60),2,'0') AS TEMPO_TOTAL_N2
        FROM INICIO_ATUACAO B
        LEFT JOIN ATUACAO_RESUMO A
            ON A.ORIGEM = B.ORIGEM
        ORDER BY
            B.ORIGEM,
            B.DATA_ENTRADA_N2
    """

    try:
        return pd.read_sql(n2_bloqueio_sql, sigitm)
    except Exception as e:
        print(f"Erro no chunk: {e}")
        return pd.DataFrame()

def divide_list(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


ta_list = df_ta['origem'].dropna().astype(str).unique().tolist()
# divide a lista
ta_chunks = list(divide_list(ta_list, 999))

# executa em paralelo
resultados = []
with ThreadPoolExecutor(max_workers=5) as executor:  # ajuste aqui
    futures = [executor.submit(query_chunk, chunk) for chunk in ta_chunks]

    for future in as_completed(futures):
        resultados.append(future.result())

# consolida
n2_bloqueio = pd.concat(resultados, ignore_index=True)





duplicadas = (
    n2_bloqueio.groupby("origem")
    .size()
    .reset_index(name="qtd")
    .sort_values("qtd", ascending=False)
)


print("N2")

print(
    "Linhas:",
    len(n2_bloqueio)
)

print(
    "TAs únicas:",
    n2_bloqueio['origem'].nunique()
)


print(n2_bloqueio.columns.tolist())


print(
    "DF_TA:",
    df_ta.shape
)

print(
    "N2:",
    n2_bloqueio.shape
)


n2_consolidado_ativos = pd.merge(df_ta, n2_bloqueio, left_on='origem', right_on='origem', how='left')


print(
    "FINAL:",
    n2_consolidado_ativos.shape
)



n2_consolidado_ativos

n2_consolidado_ativos ["classificacao_atuacao"] = np.select(
    [
        n2_consolidado_ativos["contar_atuacao"] == 1,
        n2_consolidado_ativos["contar_sem_atuacao"] == 1
    ],
    [
        "SIM",
        "NAO"
    ],
    default="VAZIO"
)


# n2_vida = n2_bloqueio.copy()
# n2_vida["origem_atuacao"] = "VIDA"



# ---------------------------------------------------------------------------- BUSCA PROCEDIMENTO - ATIVOS --------------------------------------------------------------------------------------------------------#
def query_procedimento_chunk(
    ta_chunk
):

    ta_list_str = ",".join(
        [f"'{ta}'" for ta in ta_chunk]
    )
    procedimento_sql = f"""
    SELECT
    P.PCA_TA AS ORIGEM,
    G.GRP_NOME AS GRUPO_N2,
    U.USR_NOME AS USUARIO_ATUACAO,
    MIN(P.PCA_DATA) AS DATA_ENTRADA_N2,
    MAX(P.PCA_DATA) AS DATA_SAIDA_N2,
    ROUND(
        (MAX(P.PCA_DATA) - MIN(P.PCA_DATA)) * 86400
    ) AS TOTAL_SEGUNDOS
    FROM SIGITM3.TBL_PROCEDIMENTOS_TA P
    LEFT JOIN SIGITM3.TBL_GRUPOS G
        ON G.GRP_CODIGO = P.PCA_GRUPO
    LEFT JOIN SIGITM3.TBL_USUARIOS U
        ON U.USR_CODIGO = P.PCA_USUARIO
    WHERE P.PCA_TA IN ({ta_list_str})
    AND P.PCA_GRUPO IN (
        6611,
        6612
    )
    GROUP BY
        P.PCA_TA,
        G.GRP_NOME,
        U.USR_NOME
    """

    try:

        return pd.read_sql(
            procedimento_sql,
            sigitm
        )

    except Exception as e:

        print(e)

        return pd.DataFrame()

# -----
def segundos_para_hms(seg):
    
    if pd.isna(seg):
        return None

    horas = int(seg // 3600)

    minutos = int(
        (seg % 3600) // 60
    )

    segundos = int(
        seg % 60
    )

    return (
        f"{horas}:"
        f"{minutos:02d}:"
        f"{segundos:02d}"
    )


resultados_proc = []

with ThreadPoolExecutor(
    max_workers=5
) as executor:

    futures = [

        executor.submit(
            query_procedimento_chunk,
            chunk
        )

        for chunk in ta_chunks
    ]


    for future in as_completed(
        futures
    ):

        resultados_proc.append(
            future.result()
        )


df_procedimento = pd.concat(
    resultados_proc,
    ignore_index=True
)


df_procedimento[
    "teve_atuacao"
] = "SIM"



df_procedimento[
    "ainda_na_fila"
] = None



df_procedimento[
    "inicio_atuacao"
] = 1



df_procedimento[
    "contar_atuacao"
] = 1



df_procedimento[
    "contar_sem_atuacao"
] = 0



df_procedimento[
    "tempo_no_grupo"
] = None



df_procedimento[
    "tma_n2"
] = None



df_procedimento[
    "tempo_total_atuacao"
] = None



df_procedimento[
    "quantidade_atuacao"
] = 1



df_procedimento[
    "tempo_total_n2"
] = None



df_procedimento[
    "origem_atuacao"
] = "PROCEDIMENTO"



# -- tempo no grupo --#
df_procedimento[
    "tempo_no_grupo"
] = (
    df_procedimento[
        "total_segundos"
    ].apply(
        segundos_para_hms
    )
)


# -- TMA --#
df_procedimento[
    "tma_n2"
] = (
    df_procedimento[
        "tempo_no_grupo"
    ]
)


# -- tempo total N2 --#
df_procedimento[
    "tempo_total_n2"
] = (
    df_procedimento[
        "tempo_no_grupo"
    ]
)


# -- tempo total atuação --#
df_procedimento[
    "tempo_total_atuacao"
] = (
    df_procedimento[
        "tempo_no_grupo"
    ]
)



# -- quantidade atuação --#
df_procedimento[
    "quantidade_atuacao"
] = 1





# n2_ativos_final = pd.concat(

#     [
#         n2_vida,
#         df_procedimento
#     ],

#     ignore_index=True
# )



# df_procedimento = (

#     df_procedimento[
#         ~df_procedimento[
#             "origem"
#         ].isin(
#             origens_vida
#         )
#     ]
# )




print(
    df_procedimento .shape
)



print(
    df_procedimento [
        "origem_atuacao"
    ].value_counts()
)


print(
    df_procedimento [
        df_procedimento ["origem_atuacao"]
        == "PROCEDIMENTO"
    ].shape
)



if "total_segundos" in df_procedimento .columns:

    df_procedimento  = (
        df_procedimento 
        .drop(
            columns=["total_segundos"]
        )
    )


df_procedimento = df_procedimento.rename(
    columns=lambda col: f"{col}_PROCEDIMENTO"
)
df_procedimento 


n2_consolidado_ativos1 = pd.merge(n2_consolidado_ativos, df_procedimento, left_on='origem', right_on='origem_PROCEDIMENTO', how='left')


# n2_consolidado_ativos.to_sql(name='TBL_ACOMPANHAMENTO_N2_ATIVOS', con=engine_noc,if_exists='replace', index=False)

n2_consolidado_ativos1.to_sql(name='TBL_ACOMPANHAMENTO_N2_ATIVOS', con=engine_noc,if_exists='replace', index=False)


with engine_noc.connect() as connection:
    setAtualizacao = text("UPDATE NOC.TBL_UPDATE_SCRIPTS SET DATA_UPDATE = DATE_FORMAT(NOW(), '%d-%m-%Y %H:%i') WHERE NOME_SCRIPT = 'ACOMPANHAMENTO_N2'")
    connection.execute(setAtualizacao)
    connection.commit()






# Ex.: engine com pool (ajuste a URL Oracle conforme seu ambiente)
# engine = create_engine("oracle+cx_oracle://user:pwd@host:port/?service_name=...", pool_size=5, max_overflow=5)

#============================================================================TA´S_FECHADOS==============================================================

n2 = pd.read_sql("SELECT MAX(DATA_ENCERRAMENTO) AS DATA_ENCERRAMENTO FROM NOC.TBL_ACOMPANHAMENTO_N2_FECHADO", engine_noc)
n2


n2['DATA_INICIO'] = pd.to_datetime(n2['DATA_ENCERRAMENTO'], dayfirst=True)
 
 
data_inicio= n2['DATA_INICIO'].max()
data_inicio

tipo_ciclo = 'diario'

def gerar_intervalos(inicio, fim, tipo='diario'):
    intervalos = []
    atual = inicio.replace(hour=0, minute=0, second=0, microsecond=0)
    fim = fim.replace(hour=0, minute=0, second=0, microsecond=0)
    while atual < fim:
        if tipo == 'mensal':
            proximo = (atual.replace(day=1) + timedelta(days=32)).replace(day=1)
        elif tipo == 'semanal':
            proximo = atual + timedelta(weeks=1)
        elif tipo == 'diario':
            proximo = atual + timedelta(days=1)
        else:
            raise ValueError("Tipo inválido")
        intervalos.append((
            atual.strftime('%Y-%m-%d 00:00:00'),
            min(proximo, fim).strftime('%Y-%m-%d 00:00:00')
        ))
        atual = proximo
    return intervalos

def consulta_por_mes(data_inicio, data_fim):
    # Abra a conexão dentro da thread
    with sigitm.connect() as conn:
        query = text("""
                 SELECT           
    TA.TQA_CODIGO AS ORIGEM,
    TAE.TQA_CODIGO AS ELEMENTO,
    TA.TQA_RAIZ AS TA_RAIZ,
    STAT.STA_NOME AS STATUS,
    TAE.TQA_AREA_CODIGO AS SITE, 
    TAE.TQA_ESTADO_CODIGO AS UF,
    TA.TQA_GERENCIA_CODIGO AS REGIONAL,
    TA.TQA_DATA_CRIACAO AS DATA_CRIACAO,
    TA.TQA_DATA_ENCERRAMENTO AS DATA_ENCERRAMENTO,
    TA.TQA_TIPO_BILHETE AS TIPO_BILHETE,
    TA.TQA_TIPO_SITE AS TIPO_SITE,
    TA.TQA_ALARME_TIPO AS TIPO_DE_ALARME,
    EQP.AEQ_HOSTNAME AS HOSTNAME,
    EQP.AEQ_FABRICANTE AS FABRICANTE,
    TAE.TQA_IMPACTO_EQP AS IMPACTO,
    GRP2.GRP_NOME AS GRUPO_RESPONSAVEL,
       CASE 
		 WHEN EXISTS
		 (SELECT GRP2.GRP_NOME
         FROM SIGITM3.TBL_TA_VIDA VD2
         INNER JOIN SIGITM3.TBL_GRUPOS GRP2 ON VD2.VDA_RESPONSAVELPOR_GRUPO = GRP2.GRP_CODIGO
         WHERE VD2.VDA_TA = TA.TQA_CODIGO 
         AND VD2.VDA_RESPONSAVELPOR_GRUPO = '6611')
         THEN 'SIM'
         ELSE 'NÃO'
    END AS PASSOU_PELO_ACESSO_ERICSON,
    CASE 
		 WHEN EXISTS
		 (SELECT GRP2.GRP_NOME
         FROM SIGITM3.TBL_TA_VIDA VD2
         INNER JOIN SIGITM3.TBL_GRUPOS GRP2 ON VD2.VDA_RESPONSAVELPOR_GRUPO = GRP2.GRP_CODIGO
         WHERE VD2.VDA_TA = TA.TQA_CODIGO 
         AND VD2.VDA_RESPONSAVELPOR_GRUPO = '6612')
         THEN 'SIM'
         ELSE 'NÃO'
    END AS PASSOU_PELO_ACESSO_HUAWEI,
    CASE
        WHEN EXISTS (
            SELECT 1
            FROM SIGITM3.TBL_TA_VIDA v
            INNER JOIN SIGITM3.TBL_GRUPOS GRP ON GRP.GRP_CODIGO = V.VDA_RESPONSAVELPOR_GRUPO
            WHERE V.VDA_TA = TA.TQA_CODIGO           
            AND GRP.GRP_PAI = 1340
        )
        THEN 'SIM'
        ELSE 'NÃO'
    END AS PASSOU_PELO_CAMPO,
    CASE 
		 WHEN EXISTS
		 (SELECT GRP2.GRP_NOME
         FROM SIGITM3.TBL_TA_VIDA VD2
         INNER JOIN SIGITM3.TBL_GRUPOS GRP2 ON VD2.VDA_RESPONSAVELPOR_GRUPO = GRP2.GRP_CODIGO
         WHERE VD2.VDA_TA = TA.TQA_CODIGO 
         AND VD2.VDA_RESPONSAVELPOR_GRUPO = '6563')
         THEN 'SIM'
         ELSE 'NÃO'
    END AS PASSOU_PELO_CORAN
    FROM
    SIGITM3.TBL_TA TA
    LEFT JOIN SIGITM3.TBL_TA TAE ON TAE.TQA_ORIGEM = TA.TQA_CODIGO
    LEFT JOIN SIGITM3.TBL_TA_EQUIPAMENTO EQP ON TAE.TQA_CODIGO = EQP.AEQ_TA
    LEFT JOIN SIGITM3.TBC_STATUS_TA STAT ON STAT.STA_CODIGO = TA.TQA_STATUS
    LEFT JOIN SIGITM3.TBL_GRUPOS GRP2 ON GRP2.GRP_CODIGO = TA.TQA_RESPONSAVELPOR_GRUPO
    INNER JOIN (
    SELECT DISTINCT
        VD2.VDA_TA
    FROM SIGITM3.TBL_TA_VIDA VD2
         LEFT JOIN SIGITM3.TBL_GRUPOS GRP2
            ON VD2.VDA_RESPONSAVELPOR_GRUPO = GRP2.GRP_CODIGO
         LEFT JOIN SIGITM3.TBL_PROCEDIMENTOS_TA P
            ON P.PCA_TA = VD2.VDA_TA
    WHERE (
        VD2.VDA_RESPONSAVELPOR_GRUPO IN ('6611', '6612')
        OR P.PCA_GRUPO IN ('6611', '6612')
    )
) VIDA
    ON VIDA.VDA_TA = TA.TQA_CODIGO
    WHERE TA.TQA_ORIGEM IS NULL
    AND TA.TQA_TIPO_REDE IN ('701')
    -- AND TA.TQA_CODIGO IN ({ta_list_str})
    AND TA.TQA_STATUS IN ('90')
    AND TA.TQA_DATA_CRIACAO >= TO_DATE('2025-01-01','YYYY-MM-DD')
    AND TA.TQA_DATA_ENCERRAMENTO > TO_DATE(:data_inicio, 'YYYY-MM-DD HH24:MI:SS') --sempre manter essa parte
    AND TA.TQA_DATA_ENCERRAMENTO <=  TO_DATE(:data_fim,    'YYYY-MM-DD HH24:MI:SS') --sempre manter essa parte
        """)
        df = pd.read_sql(query, conn, params={
            "data_inicio": data_inicio,
            "data_fim": data_fim
        })
        return df

# Período total
data_inicio = datetime(2025, 1, 1)
data_atual = datetime.now()
# data_atual = datetime(2026, 7, 11)
# Intervalos diários

#trazer data - formato 2
data_atual = datetime.now()

# data_inicio = (
#     data_atual -
#     timedelta(days=182)
# )


periodos = gerar_intervalos(data_inicio, data_atual, tipo=tipo_ciclo)

resultados = []
max_workers = min(len(periodos), 8)  # evita sobrecarregar o BD

with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
    future_to_periodo = {
        executor.submit(consulta_por_mes, inicio, fim): (inicio, fim)
        for (inicio, fim) in periodos
    }
    for future in concurrent.futures.as_completed(future_to_periodo):
        inicio, fim = future_to_periodo[future]
        try:
            df = future.result()
            if df is not None and not df.empty:
                resultados.append(df)
            print(f"Consulta concluída para: {inicio} a {fim}")
        except Exception as e:
            print(f"Erro na consulta para {inicio} a {fim}: {e}")

if resultados:
    df_ta = pd.concat(resultados, ignore_index=True)
else:
    df_ta = pd.DataFrame()


df_ta = df_ta.drop_duplicates()



 
print(f"TAs encontrados: {len(df_ta)}")

print("=" * 80)
print("BASE FECHADOS")
print("=" * 80)

print(
    "Shape:",
    df_ta.shape
)

print(
    "TAs únicas:",
    df_ta["origem"].nunique()
)

df_ta


# função que executa a query para um chunk
def query_chunk(ta_chunk):
    ta_list_str = ','.join([f"'{ta}'" for ta in ta_chunk])

    n2_bloqueio_sql = f"""
    WITH BASE_N2 AS (
            SELECT 
                V.VDA_TA AS ORIGEM,
                G.GRP_NOME AS GRUPO_N2,
                U.USR_NOME AS USUARIO_ATUACAO,
                V.VDA_RESPONSAVELPOR_USUARIO,
                V.VDA_DATA_INITIAL AS DATA_ENTRADA_N2,
                V.VDA_DATA_FINAL AS DATA_SAIDA_N2,
                CASE
                    WHEN V.VDA_RESPONSAVELPOR_USUARIO IS NOT NULL
                    THEN 'SIM'
                    ELSE 'NAO'
                END AS TEVE_ATUACAO,
                CASE
                    WHEN V.VDA_DATA_FINAL IS NULL
                    THEN 'SIM'
                    ELSE 'NAO'
                END AS AINDA_NA_FILA,
                ROUND(
                    (
                        COALESCE(
                            V.VDA_DATA_FINAL,
                            SYSDATE
                        )
                        -
                        V.VDA_DATA_INITIAL
                    ) * 86400
                ) AS TOTAL_SEGUNDOS,
                CASE
                    WHEN V.VDA_RESPONSAVELPOR_USUARIO IS NOT NULL
                    THEN ROUND(
                        (
                            COALESCE(
                                V.VDA_DATA_FINAL,
                                SYSDATE
                            )
                            -
                            V.VDA_DATA_INITIAL
                        ) * 86400
                    )
                    ELSE 0
                END AS TOTAL_SEGUNDOS_ATUACAO
            FROM SIGITM3.TBL_TA_VIDA V
            LEFT JOIN SIGITM3.TBL_GRUPOS G
                ON G.GRP_CODIGO = V.VDA_RESPONSAVELPOR_GRUPO
            LEFT JOIN SIGITM3.TBL_USUARIOS U
                ON U.USR_CODIGO = V.VDA_RESPONSAVELPOR_USUARIO
            WHERE V.VDA_TA IN ({ta_list_str})
              AND V.VDA_RESPONSAVELPOR_GRUPO IN (
                    6611,
                    6612
              )
        ),
        BASE_LAG AS (
            SELECT
                B.*,
                LAG(
                    B.VDA_RESPONSAVELPOR_USUARIO
                ) OVER (
                    PARTITION BY B.ORIGEM
                    ORDER BY B.DATA_ENTRADA_N2
                ) AS USUARIO_ANTERIOR
            FROM BASE_N2 B
        ),
        INICIO_ATUACAO AS (
            SELECT
                B.*,
                CASE
                    WHEN B.VDA_RESPONSAVELPOR_USUARIO IS NOT NULL
                         AND (
                                B.USUARIO_ANTERIOR IS NULL
                                OR B.USUARIO_ANTERIOR <> B.VDA_RESPONSAVELPOR_USUARIO)
                    THEN 1
                    ELSE 0
                END AS INICIO_ATUACAO,
                CASE
                    WHEN B.VDA_RESPONSAVELPOR_USUARIO IS NOT NULL
                         AND (
                                B.USUARIO_ANTERIOR IS NULL
                                OR B.USUARIO_ANTERIOR <> B.VDA_RESPONSAVELPOR_USUARIO)
                    THEN 1
                    ELSE 0
                END AS CONTAR_ATUACAO,
                CASE
                    WHEN B.VDA_RESPONSAVELPOR_USUARIO IS NULL
                    THEN 1
                    ELSE 0
                END AS CONTAR_SEM_ATUACAO
            FROM BASE_LAG B
        ),
        ATUACAO_RESUMO AS (
            SELECT
                ORIGEM,
                SUM(INICIO_ATUACAO) AS QUANTIDADE_ATUACAO
            FROM INICIO_ATUACAO
            GROUP BY ORIGEM
        )
        SELECT
            B.ORIGEM,
            B.GRUPO_N2,
            B.USUARIO_ATUACAO,
            B.DATA_ENTRADA_N2,
            B.DATA_SAIDA_N2,
            B.TEVE_ATUACAO,
            B.AINDA_NA_FILA,
            B.INICIO_ATUACAO,
            B.CONTAR_ATUACAO,
            B.CONTAR_SEM_ATUACAO,
            TRUNC(B.TOTAL_SEGUNDOS / 3600)|| ':' ||
            LPAD(TRUNC(MOD(B.TOTAL_SEGUNDOS, 3600) / 60), 2,'0')|| ':' ||
            LPAD(MOD(B.TOTAL_SEGUNDOS, 60), 2, '0') AS TEMPO_NO_GRUPO,
            TRUNC(B.TOTAL_SEGUNDOS / 3600)|| ':' ||
            LPAD(TRUNC(MOD(B.TOTAL_SEGUNDOS, 3600) / 60), 2,'0')|| ':' ||
            LPAD(MOD(B.TOTAL_SEGUNDOS, 60), 2, '0') AS TMA_N2,
            CASE
            WHEN B.TEVE_ATUACAO = 'SIM'
            THEN
                TRUNC(SUM(B.TOTAL_SEGUNDOS_ATUACAO)OVER (PARTITION BY B.ORIGEM) / 3600)|| ':' ||
                LPAD( TRUNC(MOD(SUM(B.TOTAL_SEGUNDOS_ATUACAO)OVER (PARTITION BY B.ORIGEM), 3600) / 60), 2,'0')|| ':' ||
                LPAD(MOD(SUM(B.TOTAL_SEGUNDOS_ATUACAO)OVER (PARTITION BY B.ORIGEM), 60), 2, '0')
            ELSE NULL
        END AS TEMPO_TOTAL_ATUACAO,
            CASE
            WHEN B.TEVE_ATUACAO = 'SIM'
            THEN A.QUANTIDADE_ATUACAO
            ELSE NULL
        END AS QUANTIDADE_ATUACAO,
            TRUNC(SUM(B.TOTAL_SEGUNDOS) OVER (PARTITION BY B.ORIGEM) / 3600)|| ':' ||
            LPAD(TRUNC(MOD(SUM(B.TOTAL_SEGUNDOS) OVER (PARTITION BY B.ORIGEM), 3600) / 60), 2, '0')|| ':' ||
            LPAD(MOD(SUM(B.TOTAL_SEGUNDOS) OVER (PARTITION BY B.ORIGEM), 60),2,'0') AS TEMPO_TOTAL_N2
        FROM INICIO_ATUACAO B
        LEFT JOIN ATUACAO_RESUMO A
            ON A.ORIGEM = B.ORIGEM
        ORDER BY
            B.ORIGEM,
            B.DATA_ENTRADA_N2
    """

    try:
        return pd.read_sql(n2_bloqueio_sql, sigitm)
    except Exception as e:
        print(f"Erro no chunk: {e}")
        return pd.DataFrame()

def divide_list(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


ta_list = df_ta['origem'].dropna().astype(str).unique().tolist()
# divide a lista
ta_chunks = list(divide_list(ta_list, 999))

# executa em paralelo
resultados = []
with ThreadPoolExecutor(max_workers=5) as executor:  # ajuste aqui
    futures = [executor.submit(query_chunk, chunk) for chunk in ta_chunks]

    for future in as_completed(futures):
        resultados.append(future.result())

# consolida
n2_bloqueio = pd.concat(resultados, ignore_index=True)

duplicadas = (
    n2_bloqueio.groupby("origem")
    .size()
    .reset_index(name="qtd")
    .sort_values("qtd", ascending=False)
)

n2_consolidado_fechados = pd.merge(df_ta,n2_bloqueio,left_on="origem",right_on="origem",how="left")

n2_consolidado_fechados ["classificacao_atuacao"] = np.select(
    [
        n2_consolidado_fechados["contar_atuacao"] == 1,
        n2_consolidado_fechados["contar_sem_atuacao"] == 1
    ],
    [
        "SIM",
        "NAO"
    ],
    default="VAZIO"
)


# ---------------------------------------------------------------------------- BUSCA PROCEDIMENTO - FECHADOS --------------------------------------------------------------------------------------------------------#
def query_procedimento_fechado_chunk(
    ta_chunk
):

    ta_list_str = ",".join(
        [f"'{ta}'" for ta in ta_chunk]
    )
    procedimento_sql = f"""
    SELECT
    P.PCA_TA AS ORIGEM,
    G.GRP_NOME AS GRUPO_N2,
    U.USR_NOME AS USUARIO_ATUACAO,
    MIN(P.PCA_DATA) AS DATA_ENTRADA_N2,
    MAX(P.PCA_DATA) AS DATA_SAIDA_N2,
    ROUND(
        (MAX(P.PCA_DATA) - MIN(P.PCA_DATA)) * 86400
    ) AS TOTAL_SEGUNDOS
    FROM SIGITM3.TBL_PROCEDIMENTOS_TA P
    LEFT JOIN SIGITM3.TBL_GRUPOS G
        ON G.GRP_CODIGO = P.PCA_GRUPO
    LEFT JOIN SIGITM3.TBL_USUARIOS U
        ON U.USR_CODIGO = P.PCA_USUARIO
    WHERE P.PCA_TA IN ({ta_list_str})
    AND P.PCA_GRUPO IN (
        6611,
        6612
    )
    GROUP BY
        P.PCA_TA,
        G.GRP_NOME,
        U.USR_NOME
    """



    try:

        return pd.read_sql(
            procedimento_sql,
            sigitm
        )

    except Exception as e:

        print(e)

        return pd.DataFrame()



# -----
def segundos_para_hms(seg):
    
    if pd.isna(seg):
        return None

    horas = int(seg // 3600)

    minutos = int(
        (seg % 3600) // 60
    )

    segundos = int(
        seg % 60
    )

    return (
        f"{horas}:"
        f"{minutos:02d}:"
        f"{segundos:02d}"
    )



resultados_proc_fechado = []



with ThreadPoolExecutor(
    max_workers=5
) as executor:

    futures = [

        executor.submit(
            query_procedimento_fechado_chunk,
            chunk
        )

        for chunk in ta_chunks
    ]



    for future in as_completed(
        futures
    ):

        resultados_proc_fechado.append(
    future.result()
)



df_procedimento_fechado = pd.concat(
    resultados_proc_fechado,
    ignore_index=True
)



df_procedimento_fechado[
    "teve_atuacao"
] = "SIM"



df_procedimento_fechado[
    "ainda_na_fila"
] = None



df_procedimento_fechado[
    "inicio_atuacao"
] = 1



df_procedimento_fechado[
    "contar_atuacao"
] = 1



df_procedimento_fechado[
    "contar_sem_atuacao"
] = 0



df_procedimento_fechado[
    "tempo_no_grupo"
] = None



df_procedimento_fechado[
    "tma_n2"
] = None



df_procedimento_fechado[
    "tempo_total_atuacao"
] = None



df_procedimento_fechado[
    "quantidade_atuacao"
] = 1



df_procedimento_fechado[
    "tempo_total_n2"
] = None



df_procedimento_fechado[
    "origem_atuacao"
] = "PROCEDIMENTO"



# -- tempo no grupo --#
df_procedimento_fechado[
    "tempo_no_grupo"
] = (
    df_procedimento_fechado[
        "total_segundos"
    ].apply(
        segundos_para_hms
    )
)



# -- TMA --#
df_procedimento_fechado[
    "tma_n2"
] = (
    df_procedimento_fechado[
        "tempo_no_grupo"
    ]
)



# -- tempo total N2 --#
df_procedimento_fechado[
    "tempo_total_n2"
] = (
    df_procedimento_fechado[
        "tempo_no_grupo"
    ]
)



# -- tempo total atuação --#
df_procedimento_fechado[
    "tempo_total_atuacao"
] = (
    df_procedimento_fechado[
        "tempo_no_grupo"
    ]
)



# -- quantidade atuação --#
df_procedimento_fechado[
    "quantidade_atuacao"
] = 1



if "total_segundos" in df_procedimento_fechado.columns:

    df_procedimento_fechado = (
        df_procedimento_fechado
        .drop(
            columns=["total_segundos"]
        )
    )


    df_procedimento_fechado = df_procedimento_fechado.rename(
    columns=lambda col: f"{col}_PROCEDIMENTO"
)
df_procedimento_fechado 

n2_consolidado_fechados_final = pd.merge(n2_consolidado_fechados,df_procedimento_fechado ,left_on="origem",right_on="origem_PROCEDIMENTO",how="left")


# n2_consolidado_fechados.to_sql(name='TBL_ACOMPANHAMENTO_N2_FECHADO', con=engine_noc,if_exists='append', index=False)

n2_consolidado_fechados_final.to_sql(name='TBL_ACOMPANHAMENTO_N2_FECHADO', con=engine_noc, if_exists='replace', index=False)
