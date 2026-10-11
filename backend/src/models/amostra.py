from datetime import date
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

class MetodoColeta(str, Enum): 
    SWAB_NASAL = 'Swab nasal'
    SWAB_ORAL = 'Swab oral'
    SWAB_CLOACAL = 'Swab cloacal'
    SANGUE = 'Sangue'
    NECROPSIA = 'Necrópsia'
    FEZES = 'Fezes'
    TECIDO = 'Tecido'
    PELE = 'Pele'
    PELO = 'Pelo'
    ESFREGACO_SANGUINEO = 'Esfregaço sanguíneo'
    OUTRO = 'Outro'

class CondicaoArmazenamento(str, Enum): 
    TEMPERATURA_AMBIENTE = 'Temperatura ambiente'
    REFRIGERADA = 'Refrigerada'
    CONGELADA = 'Congelada'
    SEM_IDENTIFICACAO = 'Sem identificação'
    COAGULADA = 'Coagulada'
    HEMOLISADA = 'Hemolisada'
    NITROGENIO_LIQUIDO = 'Nitrogênio líquido'
    GELO_SECO = 'Gelo seco'

class FaseAmostra(str, Enum): 
    EXTRACAO = 'Extração'
    PCR = 'PCR'
    ELETRO = 'ELETRO'

class DestinoAmostra(str, Enum): 
    BIOBANCO_UFPI = 'Biobanco UFPI'
    BIOBANCO_UFPA = 'Biobanco UFPA'
    FIOFRUZ_AM = 'Fiofruz AM'
    LASAN_UFPI = 'LASAN UFPI'
    LAPATO_UFPI = 'LAPATO UFPI'
    LAPATO_UFPA = 'LAPATO UFPA'
    LAB_VIGILANCIA_EPIZOOTIAS_UFPI = 'LAB VIGILÂNCIA DE EPIZOOTIAS - UFPI'
    OUTRO = 'Outro'

class StatusAmostra(str, Enum): 
    DISPONIVEL = 'Disponível'
    RESERVADA = 'Reservada'
    EM_USO = 'Em uso'
    PERDIDA = 'Perdida'
    ESGOTADA = 'Esgotada'

class Amostra(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    # obrigatorios       
    id: Optional[int] = None  # Autoincrementado no banco
    amostra_id: str = Field(..., alias="_id", description="ID único do laboratório (ex: AN001)")    
    animal_id: int # chave estrangeira para a tabela de animais
    data_coleta_amostra: date # alarmar se não informado
    local_coleta_amostra: str # alarmar se não informado
    nome_coletor: str # alarmar se não informado
    metodo_coleta: MetodoColeta # alarmar se não informado
    condicao_armazenamento: CondicaoArmazenamento # alarmar se não informado
    fase_amostra: FaseAmostra # alarmar se não informado
    destino_amostra: DestinoAmostra # alarmar se não informado    
    kit_utilizado: str # alarmar se não informado 
    caixa_armazenamento: str = Field(..., alias="caixa", description="Caixa de armazenamento da amostra") # alarmar se não informado
    status_amostra: StatusAmostra = StatusAmostra.DISPONIVEL  # alarmar se não informado # nasce disponível
    sequenciamento_disponivel: bool = Field(default=False, alias="sequenciamento") # alarmar se não informado
    dna_disponivel: bool # alarmar se não informado
    rna_disponivel: bool # alarmar se não informado

    # opcionais
    amostra_id_projeto: Optional[str] = None # id do projeto a que a amostra pertence
    longitude: Optional[float] = None # TEM NAS PLANILHAS? SE NÃO, TIRAR
    latitude: Optional[float] = None # TEM NAS PLANILHAS? SE NÃO, TIRAR
    amostra_observacoes: Optional[str] = Field(default=None, alias="observacoes")