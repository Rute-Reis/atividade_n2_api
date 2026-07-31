# from hamcrest import none
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date



# ---------- SAÍDA: ATIVIDADE PADRÃO ----------
class AtividadePadraoResponse(BaseModel):
    id_atividade: int
    # categoria: str
    nome_atividade: str
    tempo_estimado_min: Optional[int] = None
    observacao: Optional[str] = None




# ---------- ENTRADA: CRIAR ATIVIDADE DE SUPORTE ----------
class AtividadeSuporteCreate(BaseModel):

    matricula: str
    nome_usuario: str
    id_atividade_padrao: int
    status: Optional[str] = None
    observacoes: Optional[str] = None




# --------- SAÍDA: ATIVIDADE DE SUPORTE ----------
class AtualizarStatus(BaseModel):
    status: str




# --------- SAÍDA: ATIVIDADE DE SUPORTE ----------
class AtividadeSuporteRead(BaseModel):
    id_atividade: int
    matricula: Optional[str]
    nome_usuario: Optional[str]
    id_atividade_padrao: int
    nome_atividade: Optional[str]
    status: Optional[str]
    data_inicio: Optional[datetime]
    data_fim: Optional[datetime]
    tempo_estimado_min: Optional[int]
    tempo_real_min: Optional[int]
    observacoes: Optional[str]

    arquivo: Optional[List["ArquivoAtividadeOut"]] = []
    
    class Config:
        from_attributes = True




# ---------- SAÍDA: CRIAÇÃO DE ATIVIDADE ----------
class CriarAtividadeResponse(BaseModel):

    id_atividade: int

    mensagem: str




# ---------- SAÍDA: HISTÓRICO DA ATIVIDADE ----------
class HistoricoAtividadeRead(BaseModel):

    id_historico: int
    id_atividade: int
    matricula_responsavel: Optional[str]
    nome_usuario: Optional[str]
    tipo_evento: Optional[str]
    descricao_evento: Optional[str]
    data_evento: Optional[datetime]




# ---------- ENTRADA: ATUALIZAR OBSERVAÇÃO ----------
class AtualizarObservacao(BaseModel):

    observacoes: str




# ---------- SAÍDA: TA ----------

class TARead(BaseModel):

    origem: Optional[int]
    elemento: Optional[int]
    ta_raiz: Optional[float]
    status: Optional[str]
    site: Optional[str]
    uf: Optional[str]
    regional: Optional[str]
    data_criacao: Optional[datetime]
    data_encerramento: Optional[str]
    tipo_bilhete: Optional[str]
    tipo_site: Optional[str]
    tipo_de_alarme: Optional[str]
    hostname: Optional[str]
    fabricante: Optional[str]
    impacto: Optional[str]
    grupo_responsavel: Optional[str]
    passou_pelo_acesso_ericson: Optional[str]
    passou_pelo_acesso_huawei: Optional[str]
    passou_pelo_campo: Optional[str]
    passou_pelo_coran: Optional[str]
    n2_bloqueio: Optional[str]
    n2_grupo_bloqueio: Optional[str]
    tempo_bloqueio_n2: Optional[str]
    tempo_total_n2: Optional[str]




# ---------- PAGINAÇÃO TA ----------
class PaginacaoTA(BaseModel):

    data: list

    page: int

    page_size: int

    total: int

    total_pages: int



# ---------- SAÍDA: ARQUIVO DA ATIVIDADE ----------
class ArquivoAtividadeResponse(BaseModel):

    id_arquivo: int
    nome_original: Optional[str]
    data_upload: Optional[datetime]


    
# ---------- SAÍDA: ARQUIVO ATIVIDADE N2 ----------
class ArquivoAtividadeOut(BaseModel):

    id_arquivo: int

    id_atividade: int

    nome_original: str

    nome_arquivo: str

    caminho: str

    content_type: Optional[str] = None

    tamanho_bytes: Optional[int] = None

    data_upload: Optional[datetime] = None

    url_download: Optional[str] = None




class VolumetriaTA(BaseModel):

    ano: Optional[int]
    mes: Optional[str]
    semana: Optional[str]
    dia: Optional[str] 
    hora: Optional[str]
    visao: str
    tipo_bilhete: Optional[str]
    teve_atuacao: Optional[str]
    total: int


class VolumetriaUsuario(BaseModel):

    ano: Optional[int]
    mes: Optional[str]
    semana: Optional[str]
    dia: Optional[str] 
    hora: Optional[str]
    visao: str
    tipo_bilhete: Optional[str]
    usuario_atuacao: Optional[str]
    total: int


class tma(BaseModel):

    ano: Optional[int]
    mes: Optional[str]
    semana: Optional[str]
    dia: Optional[str]
    visao: str
    tma_medio: Optional[str]
  
