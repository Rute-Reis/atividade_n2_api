from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    Float,
    BigInteger
)

from .database import Base



# DATA_EVENTO = Column(
#     DateTime,
#     server_default=func.now()
# )


#===============================================================
#TABELA: Atividades Padrão (NOC.TBL_ATIVIDADES_PADRAO)
#===============================================================

class AtividadePadrao(Base):
    __tablename__ = "TBL_ATIVIDADES_PADRAO"

    ID = Column(Integer, primary_key=True, index=True)

    CATEGORIA = Column(String(100))
    NOME_ATIVIDADE = Column(String(300))

    TEMPO_ESTIMADO_MIN = Column(Integer)

    OBSERVACAO = Column(String(200))

    ATIVO = Column(Boolean, default=True)


#==============================================================
#TABELA: Atividades de Suporte (NOC.TBL_ATIVIDADE_SUPORTE_N2)
#============================================================== 

class AtividadeSuporte(Base):
    __tablename__ = "TBL_ATIVIDADE_SUPORTE_N2"

    ID_ATIVIDADE = Column(Integer, primary_key=True, index=True)

    MATRICULA = Column(String(50))
    NOME_USUARIO = Column(String(200))

    ID_ATIVIDADE_PADRAO = Column(Integer)


    STATUS = Column(String(50))

    DATA_INICIO = Column(DateTime)
    DATA_FIM = Column(DateTime)

    TEMPO_ESTIMADO_MIN = Column(Integer)
    TEMPO_REAL_MIN = Column(Integer)

    OBSERVACOES = Column(Text)



# ==============================================================
# TABELA: Histórico Atividade N2
# ==============================================================
class HistoricoAtividadeN2(Base):
    __tablename__ = "TBL_HISTORICO_ATIVIDADE_N2"

    ID_HISTORICO = Column(Integer, primary_key=True, index=True)

    ID_ATIVIDADE = Column(Integer)

    MATRICULA_RESPONSAVEL = Column(String(50))

    NOME_USUARIO = Column(String(200))

    TIPO_EVENTO = Column(String(100))

    DESCRICAO_EVENTO = Column(Text)

    DATA_EVENTO = Column(DateTime)



# ==============================================================
# TABELA: Arquivos Atividade N2 
# ==============================================================
class ArquivoAtividadeN2(Base):
    __tablename__ = "TBL_ARQUIVOS_ATIVIDADE_N2"

    ID_ARQUIVO = Column(Integer, primary_key=True, index=True)

    ID_ATIVIDADE = Column(Integer)

    NOME_ORIGINAL = Column(String(255))

    NOME_ARQUIVO = Column(String(255))

    CAMINHO = Column(String(500))

    CONTENT_TYPE = Column(String(100))

    TAMANHO_BYTES = Column(BigInteger)

    DATA_UPLOAD = Column(DateTime)







# # ==============================================================
# # TABELA: TA ATIVOS
# # NOC.TBL_ACOMPANHAMENTO_N2_ATIVOS
# # ==============================================================

# class TAAtivo(Base):
#     __tablename__ = "TBL_ACOMPANHAMENTO_N2_ATIVOS"

#     origem = Column(BigInteger)

#     elemento = Column(BigInteger)

#     ta_raiz = Column(Float)

#     status = Column(Text)

#     site = Column(Text)

#     uf = Column(Text)

#     regional = Column(Text)

#     data_criacao = Column(DateTime)

#     data_encerramento = Column(Text)

#     tipo_bilhete = Column(Text)

#     tipo_site = Column(Text)

#     tipo_de_alarme = Column(Text)

#     hostname = Column(Text)

#     fabricante = Column(Text)

#     impacto = Column(Text)

#     grupo_responsavel = Column(Text)

#     passou_pelo_acesso_ericson = Column(Text)

#     passou_pelo_acesso_huawei = Column(Text)

#     passou_pelo_campo = Column(Text)

#     passou_pelo_coran = Column(Text)

#     n2_bloqueio = Column(Text)

#     n2_grupo_bloqueio = Column(Text)

#     tempo_bloqueio_n2 = Column(Text)

#     tempo_total_n2 = Column(Text)




# # ==============================================================
# # TABELA: TA FECHADOS
# # NOC.TBL_ACOMPANHAMENTO_N2_FECHADO
# # ==============================================================

# class TAFechado(Base):
#     __tablename__ = "TBL_ACOMPANHAMENTO_N2_FECHADO"

#     origem = Column(BigInteger)

#     elemento = Column(BigInteger)

#     ta_raiz = Column(Float)

#     status = Column(Text)

#     site = Column(Text)

#     uf = Column(Text)

#     regional = Column(Text)

#     data_criacao = Column(DateTime)

#     data_encerramento = Column(DateTime)

#     tipo_bilhete = Column(Text)

#     tipo_site = Column(Text)

#     tipo_de_alarme = Column(Text)

#     hostname = Column(Text)

#     fabricante = Column(Text)

#     impacto = Column(Text)

#     grupo_responsavel = Column(Text)

#     passou_pelo_acesso_ericson = Column(Text)

#     passou_pelo_acesso_huawei = Column(Text)

#     passou_pelo_campo = Column(Text)

#     passou_pelo_coran = Column(Text)

#     n2_bloqueio = Column(Text)

#     n2_grupo_bloqueio = Column(Text)

#     tempo_bloqueio_n2 = Column(Text)

#     tempo_total_n2 = Column(Text)
