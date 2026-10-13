# ⚙️ LABVEPI — Documentação Técnica do Backend
> **Laboratório de Vigilância de Epizootias — Universidade Federal do Piauí (UFPI)**  
> *API RESTful, Modelos de Domínio Pydantic v2, Regras de Negócio e Repositórios*

---

## 📋 Sumário
1. [Visão Geral do Backend](#1-visão-geral-do-backend)
2. [Estrutura de Diretórios](#2-estrutura-de-diretórios)
3. [Tecnologias e Dependências](#3-tecnologias-e-dependências)
4. [Modelos de Domínio e Entidades (Pydantic v2)](#4-modelos-de-domínio-e-entidades-pydantic-v2)
   - [4.1. Usuário (`Usuario` e Enum `Perfil`)](#41-usuário-usuario-e-enum-perfil)
   - [4.2. Espécie (`Especie` e Enum `Classe`)](#42-espécie-especie-e-enum-classe)
   - [4.3. Animal (`Animal` e Enums de Domínio)](#43-animal-animal-e-enums-de-domínio)
   - [4.4. Amostra Biológica (`Amostra`)](#44-amostra-biológica-amostra)
   - [4.5. Exame Laboratorial (`Exame`)](#45-exame-laboratorial-exame)
   - [4.6. Reagente de Bancada (`Reagente`)](#46-reagente-de-bancada-reagente)
   - [4.7. Estoque Consolidado (`EstoqueReagente` - Modelo Agregado)](#47-estoque-consolidado-estoquereagente---modelo-agregado)
5. [Camada de Serviços e Repositórios](#5-camada-de-serviços-e-repositórios)
   - [5.1. `AnimalService` e Resolução Taxonômica](#51-animalservice-e-resolução-taxonômica)
   - [5.2. `EspecieRepository` e Catálogo em Memória](#52-especierepository-e-catálogo-em-memória)
   - [5.3. `ReagenteService` e Consolidação de Lotes](#53-reagenteservice-e-consolidação-de-lotes)
6. [API HTTP (FastAPI) e Pontos de Entrada](#6-api-http-fastapi-e-pontos-de-entrada)
7. [Como Executar o Backend Localmente](#7-como-executar-o-backend-localmente)
8. [Diretrizes de Qualidade e Boas Práticas](#8-diretrizes-de-qualidade-e-boas-práticas)

---

## 1. Visão Geral do Backend

A camada de backend do **LABVEPI** foi projetada para garantir rigor técnico, integridade de dados científicos e desacoplamento de regras de negócio. Utiliza **Python 3.11+**, **FastAPI** para serviços assíncronos e **Pydantic v2** como núcleo de validação e modelagem de contratos de dados.

Principais responsabilidades do backend:
- **Validação Estrita de Dados**: Garantir que dados biológicos, taxonômicos, diagnósticos e de estoque atendam às regras laboratoriais antes de qualquer persistência.
- **Normalização e Desacoplamento**: Validação e saneamento de termos legados de planilhas e formulários na camada de serviços, mantendo os modelos Pydantic estritamente como entidades puras de domínio.
- **Regras de Negócio e Serviços**: Implementar regras como resolução taxonômica automática, categorização de faixas etárias, conversões dimensionais de reagentes e integridade referencial.
- **Mapeamento Flexível com MongoDB Atlas**: Suporte a aliases (`ConfigDict(populate_by_name=True)`) garantindo compatibilidade direta entre identificadores laboratoriais (`_id`) e chaves Pythonicas.

---

## 2. Estrutura de Diretórios

```
backend/
├── requirements.txt                  # Dependências do backend (fastapi, uvicorn, pydantic, email-validator)
├── database/                         # Scripts e conexões de persistência direta
├── docs/                             # Documentações técnicas e notas analíticas
│   ├── analise_planilhas_models.TXT  # Levantamento taxonômico e correspondência com planilhas
│   ├── campos_impossiveis.txt        # Especificações de restrições de campos
│   └── perfil.txt                    # Mapeamento e normalização de perfis de usuário
├── tests/                            # Testes unitários e de integração
└── src/
    ├── main.py                       # Ponto de entrada da aplicação FastAPI
    ├── config/                       # Configurações globais e variáveis de ambiente
    ├── controllers/                  # Controladores e rotas HTTP (endpoints)
    ├── errors/                       # Tratamento centralizado de exceções
    ├── models/                       # Modelos Pydantic v2 (Entidades de Domínio)
    │   ├── usuario.py                # Modelo Usuario e Enum Perfil
    │   ├── especie.py                # Modelo Especie e Enum Classe
    │   ├── animal.py                 # Modelo Animal e Enums Sexo, FaixaEtaria, Orgao, RegimeVida, etc.
    │   ├── amostra.py                # Modelo Amostra e Enums MetodoColeta, CondicaoArmazenamento, etc.
    │   ├── exame.py                  # Modelo Exame e Enums TesteLaboratorial, TipoExame, ResultadoExame
    │   ├── reagente.py               # Modelo Reagente, unidades e cálculo de vencimento
    │   └── estoqueReagente.py        # Modelo Agregado EstoqueReagente com conversão dimensional
    ├── repositories/                 # Repositórios de dados e catálogos (ex: especie_repository.py)
    ├── services/                     # Serviços de domínio (animal_service.py, reagente_service.py)
    └── utils/                        # Utilitários e formatadores auxiliares
```

---

## 3. Tecnologias e Dependências

| Pacote | Versão Mínima | Finalidade |
| :--- | :--- | :--- |
| **Python** | `3.11+` | Ambiente de execução e tipagem estática moderna. |
| **FastAPI** | `>=0.110.0` | Framework web assíncrono para construção da API RESTful. |
| **Uvicorn** | `>=0.29.0` | Servidor ASGI de alta performance para a aplicação FastAPI. |
| **Pydantic** | `>=2.6.0` | Validação de schemas, serialização e modelos de domínio fortemente tipados. |
| **Email-Validator** | `>=2.0.0` | Validação robusta de endereços de e-mail (`EmailStr`). |

---

## 4. Modelos de Domínio e Entidades (Pydantic v2)

Todos os modelos utilizam `ConfigDict(populate_by_name=True)`, permitindo tanto a instanciação via nomes de atributos padrão do Python quanto via aliases correspondentes aos documentos salvos no MongoDB.

---

### 4.1. Usuário (`Usuario` e Enum `Perfil`)
- **Arquivo**: `backend/src/models/usuario.py`
- **Enum `Perfil`**:
  - `DOCENTE` (`"docente"`)
  - `POS_GRADUANDO` (`"pos_graduando"`)
  - `BOLSISTA_PIBITI` (`"bolsista_pibiti"`)
  - `BOLSISTA_PIBIC` (`"bolsista_pibic"`)
  - `BOLSISTA_EXTERNO` (`"bolsista_externo"`)
- **Campos da Entidade**:
  - `id`: `Optional[Union[int, str]]` (alias `_id`)
  - `username`: `str` (alias `usuario`)
  - `name`: `Optional[str]` (alias `nome`)
  - `email`: `EmailStr` (validação formal de formato de e-mail)
  - `password`: `str` (alias `senha`, hash criptográfico)
  - `created_at`: `datetime` (padrão `datetime.now`)
  - `last_login`: `Optional[Union[datetime, str]]` (data/hora do último acesso)
  - `perfil`: `Perfil` (perfil com normalizador inteligente de termos legados como `"professor"`, `"mestrando"`, `"doutorando"`, `"pibit"`, etc.)
  - `matricula`: `Optional[Union[int, str]]`

---

### 4.2. Espécie (`Especie` e Enum `Classe`)
- **Arquivo**: `backend/src/models/especie.py`
- **Enum `Classe`**:
  - `AVES` (`"Ave"`)
  - `MAMIFERO` (`"Mamífero"`)
  - `REPTIL` (`"Réptil"`)
  - `ANFIBIO` (`"Anfíbio"`)
  - `PEIXE` (`"Peixe"`)
- **Campos da Entidade**:
  - `id`: `Optional[Union[int, str]]` (alias `_id`)
  - `nome_comum`: `str` (alias `nome`)
  - `nome_cientifico`: `str` (binominal científico obrigatório, validado formalmente)
  - `classe`: `Classe`
- **Diretriz de Entidade Pura**: Validação e padronização taxonômica de nomes científicos e normalização de classes delegadas a `EspecieRepository` e `AnimalService`, mantendo o modelo livre de validadores e métodos operacionais.

---

### 4.3. Animal (`Animal` e Enums de Domínio)
- **Arquivo**: `backend/src/models/animal.py`
- **Enums de Domínio**:
  - `Sexo`: `Macho`, `Fêmea`, `Indeterminado`, `Não informado`
  - `FaixaEtaria`: `Filhote`, `Juvenil`, `Jovem`, `Sub Adulto`, `Adulto`, `Senil`, `Idoso`, `Potro`, `Ninhego`, `Não informado`
  - `Orgao`: `UFPI`, `HVU`, `CCZ`, `NEPPAS`, CETAS (PI, CE, RN), `SEMARH - CETAS - PI`, universidades parceiras (`UFPA`, `UFRR`, `UFAC`, `UFOB`), `DSEI LESTE - AM`, `ZOOLOGICO -PI`, `PARTICULAR`, `OUTRO`
  - `RegimeVida`: `Vida livre`, `Cativeiro`, `Domiciliado`, `Não informado` (alias `status` do banco)
  - `Funcao`: `Pet`, `Trabalho`, `Lazer`, `Reprodução`, `Conservação / Zoológico`, `Outro`, `Não aplicável`
  - `StatusVital`: `Vivo`, `Morto`, `Eutanasiado`, `Não informado`
- **Campos Obrigatórios**:
  - `id`: `Optional[int]` (identificador sequencial)
  - `animal_id`: `str` (alias `_id` — ex: `"AN001"`)
  - `classe`: `Classe`
  - `nome_comum`: `str`
  - `nome_cientifico`: `str`
  - `sexo`: `Sexo` (default `Sexo.NAO_INFORMADO`)
  - `peso`: `Union[float, str]` (em kg ou a string `"Não aferido"`)
  - `faixa_etaria`: `FaixaEtaria` (default `FaixaEtaria.NAO_INFORMADO`)
  - `orgao_origem`: `Orgao` (alias `orgao`)
  - `local_origem`: `str` (município ou procedência geográfica)
  - `regime_vida`: `RegimeVida` (alias `status`)
  - `status_vital`: `StatusVital`
- **Campos Opcionais**:
  - `animal_id_projeto`, `id_hvu`, `microchip`, `funcao`, `idade`, `suspeita_clinica`, `animal_observacoes` (alias `observacoes`).
- **Diretriz de Entidade Pura**: Processamento, conversão dimensional de peso (gramas para quilogramas) e validações de biometria delegadas ao `AnimalService`, mantendo o modelo livre de validadores e lógicas de transformação.

---

### 4.4. Amostra Biológica (`Amostra`)
- **Arquivo**: `backend/src/models/amostra.py`
- **Enums de Domínio**:
  - `MetodoColeta`: Swabs (oral, nasal, cloacal, traqueal, ocular, etc.), Sangue e frações (total, EDTA, soro, papel filtro, esfregaço), Tecidos/Órgãos (baço, fígado, pulmão, encéfalo, etc.), Excretas e outros (fezes, enema, líquor, ectoparasita, pele, necrópsia, outro).
  - `CondicaoArmazenamento`: `Temperatura ambiente`, `Refrigerada`, `Congelada`, `Nitrogênio líquido`, `Gelo seco`, etc.
  - `FaseAmostra`: `Extração`, `PCR`, `ELETRO`
  - `DestinoAmostra`: `Biobanco UFPI`, `Biobanco UFPA`, `Fiofruz AM`, `LASAN UFPI`, `LAPATO UFPI`, `LAPATO UFPA`, `LAB VIGILÂNCIA DE EPIZOOTIAS - UFPI`, `Outro`
  - `StatusAmostra`: `Disponível`, `Reservada`, `Em uso`, `Perdida`, `Esgotada`
- **Campos Principais**:
  - `amostra_id`: `str` (alias `_id` — ex: `"AMS001"`)
  - `animal_id`: `str` (chave de vinculação ao animal de origem)
  - `data_coleta_amostra`: `Optional[date]` (alias `data_coleta`)
  - `data_entrega`: `Optional[date]` (alias `data_recebimento`)
  - `metodo_coleta`: `Union[MetodoColeta, str]` (com normalizador heurístico automático)
  - `status_amostra`: `StatusAmostra` (default `Disponível`)
  - `laudo_liberado`: `Optional[str]`
  - `dna_disponivel`, `rna_disponivel`, `sequenciamento_disponivel`: `bool`
  - `caixa_armazenamento`: `Optional[str]` (alias `caixa`)
  - `latitude`, `longitude`: `Optional[float]`

---

### 4.5. Exame Laboratorial (`Exame`)
- **Arquivo**: `backend/src/models/exame.py`
- **Enums de Domínio**:
  - `TesteLaboratorial`: `PCR`, `Sorológico`, `Coproparasitológico`, `Hemoparasito em lâmina`, `Outro`
  - `TipoExame`: `Febre Amarela`, `OrthoFlaviviridae`, `Febre do Nilo`, `Mycoplasma`, `Herpesviridae`, `Trypanosomatidae`, `Resistência Bacteriana`, `Hepatozoon`, `Raiva`, `Chlamydia`, `Sarcocystidae`, `Plasmodium e Haemoproteus`, `Outro`
  - `ResultadoExame`: `Positivo`, `Negativo`, `Inconclusivo`, `Aguardando Resultado`, `Não Realizado`
- **Campos Principais**:
  - `amostra_id`: `str` (chave de vinculação à amostra)
  - `tipo_exame`: `TipoExame`
  - `resultado`: `ResultadoExame` (alias `resultado_detalhado`, normalizado automaticamente)
  - `data_realizacao`: `date`
  - `resultado_detalhe`: `Optional[str]` (alias `resultado_observacoes`)
  - `teste_laboratorial`, `laboratorio_realizador`, `responsavel_exame`, `kit_utilizado`, `protocolo_exame`

---

### 4.6. Reagente de Bancada (`Reagente`)
- **Arquivo**: `backend/src/models/reagente.py`
- **Enum `UnidadeMedida`**: `ml`, `L`, `µl`, `g`, `mg`, `kg`, `un`
- **Campos da Entidade**:
  - `reagente_codigo`: `str` (alias `codigo`)
  - `reagente_nome`: `str` (alias `nome`)
  - `numero_lote`: `str`
  - `marca`: `str` (resolve sinônimo `'fabricante'`)
  - `data_validade`: `date` (suporta formato brasileiro `DD/MM/AAAA`)
  - `quantidade_unidade`: `int` (quantidade física de frascos)
  - `quantidade_volume`: `Optional[float]`
  - `unidade_medida`: `str` (alias `unidade`, normalizado para símbolos padrão)
  - `reagente_local_armazenamento`: `str` (alias `local_armazenamento`)
- **Atributos de Estado de Validade**:
  - `esta_vencido` (`Optional[bool]`): Status de validade calculado pela camada de serviço (`ReagenteService`).
  - `dias_para_vencer` (`Optional[int]`): Dias restantes até o vencimento calculados pelo serviço.

---

### 4.7. Estoque Consolidado (`EstoqueReagente` - Modelo Agregado)
- **Arquivo**: `backend/src/models/estoqueReagente.py`
- Agrupa múltiplos lotes de um mesmo produto sob uma visão única de inventário.
- **Campos Estruturados de Consolidação** (preenchidos e calculados via `ReagenteService`):
  - `quantidade_total_unidades` (`int`): Total de frascos/caixas.
  - `totais_por_unidade` (`Dict[str, float]`): Quantidades segregadas por unidade original.
  - `totais_convertidos_base` (`Dict[str, float]`): Quantidades unificadas em unidades base (`ml` para volumes e `g` para massas).
  - `quantidade_total_volume` (`Optional[float]`): Volume normalizado.
  - `resumo_estoque` (`Optional[str]`): Descrição textual para visualização rápida (ex: `"1500 ml"`).

---

## 5. Camada de Serviços e Repositórios

A camada de serviços (`src/services/`) desacopla as regras operacionais dos endpoints HTTP e formulários.

### 5.1. `AnimalService` e Resolução Taxonômica
- **Arquivo**: `backend/src/services/animal_service.py`
- Interage com `EspecieRepository` para verificar se o binômio científico ou nome popular já existe no acervo.
- Se a espécie for inédita, exige confirmação explícita (`confirmar_nova_especie=True`) e os dados taxonômicos completos (`nome_comum`, `nome_cientifico`, `classe`) antes de permitir a criação da entidade `Animal`.

### 5.2. `EspecieRepository` e Catálogo em Memória
- **Arquivo**: `backend/src/repositories/especie_repository.py`
- Mantém dois índices em memória (`_por_comum` e `_por_cientifico`) com busca normalizada (sem espaços redundantes e *case-insensitive*).
- Inicializado com catálogo padrão de espécies frequentes (cães, gatos, primatas, jiboias, anfíbios, etc.) e aberto a expansão em tempo de execução.

### 5.3. `ReagenteService` e Consolidação de Lotes
- **Arquivo**: `backend/src/services/reagente_service.py`
- Valida unicidade de números de lote, calcula indicadores de vencimento (`esta_vencido`, `dias_para_vencer`) e agrega lotes individuais em instâncias consolidadas de `EstoqueReagente`.
- Aplica a tabela de fatores de conversão dimensional (`FATORES_CONVERSAO`), prevenindo somas cegas entre grandezas incompatíveis (ex: somar $1\text{ L}$ com $500\text{ ml}$ resulta em $1500\text{ ml}$ e não em $501$) e formatando resumos legíveis para a interface.

---

## 6. API HTTP (FastAPI) e Pontos de Entrada

O ponto de entrada da API assíncrona está em `backend/src/main.py`:
- Instância `FastAPI` com documentação interativa automática OpenAPI/Swagger (`/docs`) e ReDoc (`/redoc`).
- Health check padrão em `GET /`.
- Arquitetura pronta para incorporação de roteadores modulares em `src/controllers/` para operações CRUD sobre animais, amostras, exames e insumos.

---

## 7. Como Executar o Backend Localmente

### Pré-requisitos
- Python 3.11+ instalado
- Ambiente virtual configurado

```bash
# 1. Ativar o ambiente virtual (na raiz do projeto)
source .venv/bin/activate  # Linux/macOS
# ou: .venv\Scripts\activate no Windows

# 2. Instalar dependências do backend
pip install -r backend/requirements.txt

# 3. Iniciar o servidor Uvicorn com hot-reload
uvicorn backend.src.main:app --reload --port 8000
```

- **Health check**: `http://localhost:8000/`
- **Documentação Swagger**: `http://localhost:8000/docs`
- **Documentação ReDoc**: `http://localhost:8000/redoc`

---

## 8. Diretrizes de Qualidade e Boas Práticas

1. **Validação na Borda**: Nenhuma informação deve ser enviada ao banco de dados sem antes passar pela validação de seu modelo Pydantic correspondente.
2. **Imutabilidade e Consistência**: Utilizar Enums estritos para categorias fechadas e validadores com `mode="before"` para normalizar strings de entrada legadas.
3. **Isolamento de Segredos**: Nunca gravar credenciais ou URIs de banco diretamente nos arquivos do backend; utilizar `src/config/` e variáveis de ambiente.
