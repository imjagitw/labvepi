# ⚙️ LABVEPI — Documentação Técnica do Backend
> **Laboratório de Vigilância de Epizootias — Universidade Federal do Piauí (UFPI)**  
> *API RESTful, Modelos de Domínio Pydantic v2, Pipeline de ETL Desacoplado, Regras de Negócio, Repositórios e Testes*

---

## 📋 Sumário
1. [Visão Geral e Arquitetura em Camadas](#1-visão-geral-e-arquitetura-em-camadas)
2. [Estrutura de Diretórios](#2-estrutura-de-diretórios)
3. [Tecnologias e Dependências](#3-tecnologias-e-dependências)
4. [Modelos de Domínio e Entidades (Pydantic v2)](#4-modelos-de-domínio-e-entidades-pydantic-v2)
   - [4.1. Usuário (`Usuario` e Enum `Perfil`)](#41-usuário-usuario-e-enum-perfil)
   - [4.2. Módulo de Espécie (`Especie`, DTOs e Enum `Classe`)](#42-módulo-de-espécie-especie-dtos-e-enum-classe)
   - [4.3. Módulo de Animal (`Animal`, DTOs e Enums de Domínio)](#43-módulo-de-animal-animal-dtos-e-enums-de-domínio)
   - [4.4. Módulo de Amostra Biológica (`Amostra`, DTOs e Enums)](#44-módulo-de-amostra-biológica-amostra-dtos-e-enums)
   - [4.5. Exame Laboratorial (`Exame` e Enums)](#45-exame-laboratorial-exame-e-enums)
   - [4.6. Reagente e Estoque (`Reagente` e `EstoqueReagente`)](#46-reagente-e-estoque-reagente-e-estoquereagente)
5. [Camada de Serviços e Regras de Negócio (`src/services/`)](#5-camada-de-serviços-e-regras-de-negócio-srcservices)
   - [5.1. `AnimalService` e Regras de Biometria/Faixa Etária](#51-animalservice-e-regras-de-biometriafaixa-etária)
   - [5.2. `EspecieService` e Taxonomia Zoológica](#52-especieservice-e-taxonomia-zoológica)
   - [5.3. `AmostraService` e Normalização de Matrizes](#53-amostraservice-e-normalização-de-matrizes)
   - [5.4. Simplificação dos Services e Eliminação de `carga_legada`](#54-simplificação-dos-services-e-eliminação-de-carga_legada)
   - [5.5. Regras de Integridade, Bloqueio de Exclusão e Permissões (RBAC)](#55-regras-de-integridade-bloqueio-de-exclusão-e-permissões-rbac)
   - [5.6. `ReagenteService`, `EstoqueReagenteService` e Sincronização Automática](#56-reagenteservice-estoquereagenteservice-e-sincronização-automática)
6. [Módulo de Utilitários e Normalização de Domínio (`src/utils/`)](#6-módulo-de-utilitários-e-normalização-de-domínio-srcutils)
   - [6.1. Pacote Modular de Normalização (`src/utils/normalizacao/`)](#61-pacote-modular-de-normalização-srcutilsnormalizacao)
7. [Pipeline de ETL e Migração de Planilhas (`etl/`)](#7-pipeline-de-etl-e-migração-de-planilhas-etl)
   - [7.1. Arquitetura do Pipeline de Dados](#71-arquitetura-do-pipeline-de-dados)
   - [7.2. Extrator Base e Dataclasses (`etl/base.py`)](#72-extrator-base-e-dataclasses-etlbasepy)
   - [7.3. Extrator de Morcegos (`etl/morcegos.py`)](#73-extrator-de-morcegos-etlmorcegospy)
   - [7.4. Catálogo e Seeding Taxonômico (`etl/catalogo.py`)](#74-catálogo-e-seeding-taxonômico-etlcatalogopy)
   - [7.5. Carregador e Validador Canônico (`etl/carregar.py`)](#75-carregador-e-validador-canônico-etlcarregarpy)
8. [Camada de Repositórios e Persistência (`src/repositories/`)](#8-camada-de-repositórios-e-persistência-srcrepositories)
   - [8.1. Padrão DAO e Indexação em Memória $O(1)$](#81-padrão-dao-e-indexação-em-memória-o1)
   - [8.2. Matriz de Repositórios e Métodos Disponíveis](#82-matriz-de-repositórios-e-métodos-disponíveis)
9. [API HTTP (FastAPI) e Controladores (`src/controllers/`)](#9-api-http-fastapi-e-controladores-srccontrollers)
   - [9.1. Centralização de Respostas HTTP e Tratamento de Erros (`response_controller.py`)](#91-centralização-de-respostas-http-e-tratamento-de-erros-response_controllerpy)
   - [9.2. Endpoints de Animais (`/animal`)](#92-endpoints-de-animais-animal)
   - [9.3. Endpoints de Espécies (`/especie`)](#93-endpoints-de-espécies-especie)
   - [9.4. Endpoints de Amostras (`/amostra`)](#94-endpoints-de-amostras-amostra)
   - [9.5. Endpoints de Exames (`/exame`)](#95-endpoints-de-exames-exame)
   - [9.6. Endpoints de Reagentes (`/reagente`)](#96-endpoints-de-reagentes-reagente)
   - [9.7. Endpoints de Estoque Consolidado (`/estoque_reagente`)](#97-endpoints-de-estoque-consolidado-estoque_reagente)
10. [Suíte de Testes Automatizados (`tests/`)](#10-suíte-de-testes-automatizados-tests)
11. [Como Executar o Backend e o ETL Localmente](#11-como-executar-o-backend-e-o-etl-localmente)
12. [Diretrizes de Qualidade e Boas Práticas](#12-diretrizes-de-qualidade-e-boas-práticas)

---

## 1. Visão Geral e Arquitetura em Camadas

A arquitetura do **LABVEPI** foi projetada para garantir rigor técnico, reprodutibilidade científica e separação estrita de responsabilidades. Utiliza **Python 3.11+**, **FastAPI** para serviços web assíncronos, **Pydantic v2** para validação e tipagem estrita de contratos de dados, e um **Pipeline de ETL dedicado** para a ingestão e saneamento de planilhas históricas de campo.

### 1.1. Filosofia de Design e Desacoplamento

A aplicação opera através de dois subsistemas complementares e desacoplados:

1. **Subsistema da Aplicação Web (API RESTful)**:
   - Focado na operação rotineira do laboratório: cadastro, atualização, busca e relatórios com validação uniforme e previsível.
   - **Sem tolerâncias anômalas**: a API e os Services não aceitam dados deformados sob argumentos de "carga legada".
2. **Subsistema de Engenharia de Dados (ETL / Ingestão)**:
   - Isola toda a complexidade de leitura de planilhas Excel/CSV históricas (colunas esparsas, variações de digitação, valores sentinela).
   - Extrai, higieniza e gera documentos canônicos em formato `.jsonl` e registra anomalias em `problemas.csv`.
   - Carrega os lotes gerados diretamente no MongoDB (`pibit_app_dev`) validando-os diretamente contra os schemas de domínio Pydantic, garantindo 100% de conformidade com a API.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            PIPELINE DE ETL (DADOS)                          │
│   Planilhas Excel/CSV ──► Extratores (ex: etl/morcegos.py, etl/catalogo.py) │
│                                  │                                          │
│                                  ▼                                          │
│                    Documentos Canônicos (.jsonl)                            │
│                                  │                                          │
│                                  ▼                                          │
│       Carregador (etl/carregar.py) ──► Validação Canônica Pydantic v2       │
│                                  │                                          │
└──────────────────────────────────┼──────────────────────────────────────────┘
                                   │  Upsert Idempotente
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          BANCO DE DADOS (PERSISTÊNCIA)                      │
│                    MongoDB Atlas / Local (pibit_app_dev)                    │
└──────────────────────────────────▲──────────────────────────────────────────┘
                                   │
┌──────────────────────────────────┴──────────────────────────────────────────┐
│                         APLICAÇÃO WEB / API RESTful                         │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      1. CONTROLLERS (API HTTP)                      │   │
│   │   FastAPI APIRouter · Respostas HTTP · Erros Centralizados          │   │
│   └────────────────────────────────┬────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                     2. SERVICES (REGRAS DE NEGÓCIO)                 │   │
│   │   Resolução Taxonômica · Conversão de Unidades · Deduções           │   │
│   │   Saneamento Canônico · Integridade Referencial · RBAC              │   │
│   └────────────────────┬───────────────────────────────┬────────────────┘   │
│                        │                               │                    │
│                        ▼                               ▼                    │
│   ┌────────────────────────────────────────┐  ┌─────────────────────────┐   │
│   │        3. REPOSITORIES (DAO)           │  │   4. MODELS & DTOs      │   │
│   │   Persistência · Índices em Memória    │  │   Pydantic v2 Models    │   │
│   │   Busca Textual · Filtros · Paginação  │  │   Create / Update / DTO │   │
│   └────────────────────────────────────────┘  │   Details Agregados     │   │
│                                               │   Enums de Domínio      │   │
│                                               └─────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Estrutura de Diretórios

```
backend/
├── requirements.txt                  # Dependências do backend (fastapi, uvicorn, pydantic, pymongo, openpyxl)
├── database/                         # Scripts e conexões de persistência direta
├── docs/                             # Documentações técnicas e especificações
│   ├── DOCUMENTACAO_BACKEND.md       # Documentação técnica consolidada do backend (este documento)
│   ├── analise_planilhas_models.TXT  # Mapeamento campo a campo com as planilhas laboratoriais
│   ├── campos_impossiveis.txt        # Especificações de restrições de campos
│   └── regras.txt                    # Regras de negócio, permissões e diretrizes operacionais
├── etl/                              # Pipeline de Engenharia de Dados (ETL)
│   ├── base.py                       # ExtratorBase, dataclasses Resultado, ProblemaLinha e StatusExtracao
│   ├── morcegos.py                   # Extrator especializado da planilha histórica de Morcegos (Excel)
│   ├── catalogo.py                   # Utilitário e CLI de carga/seeding do Catálogo de Espécies (CSV)
│   ├── carregar.py                   # Carregador genérico com validação canônica e upsert no MongoDB
│   └── saida/                        # Lotes canônicos gerados em .jsonl e relatórios problemas.csv
├── tests/                            # Suíte de testes automatizados (84 testes)
│   ├── test_animal_service.py        # Testes de unidade e regras de negócio de Animais
│   ├── test_especie_service.py       # Testes de taxonomia, classes e importação CSV
│   ├── test_amostra_service.py       # Testes de Amostras e ciclo laboratorial
│   ├── test_etl_base.py              # Testes da infraestrutura base de ETL
│   ├── test_etl_morcegos.py          # Testes de extração, tolerâncias e parsing de morcegos
│   ├── test_etl_carregar.py          # Testes do carregador, validação de schemas e integridade
│   ├── test_model_corrections.py     # Testes de correções de modelos e saneamento
│   ├── test_utils_normalizacao.py    # Testes unitários do pacote modular de normalização
│   ├── test_reagente_controlller.py  # Testes de integração HTTP de Reagente e EstoqueReagente
│   └── test_controllers_centralized_responses.py # Testes de respostas HTTP padronizadas e tratamento centralizado de erros
└── src/
    ├── main.py                       # Ponto de entrada FastAPI com registro global de handlers de erro
    ├── config/                       # Configurações globais e variáveis de ambiente
    ├── controllers/                  # Controladores e rotas HTTP (endpoints RESTful sem try/except)
    │   ├── response_controller.py    # Respostas HTTP padronizadas e tratamento centralizado de erros: TratamentoErrosRoute, criar_router e catálogo RESPOSTAS
    │   ├── animal_controller.py      # Endpoints RESTful de Animais (/animal)
    │   ├── especie_controller.py     # Endpoints RESTful de Espécies (/especie)
    │   ├── amostra_controller.py     # Endpoints RESTful de Amostras (/amostra)
    │   ├── exame_controller.py       # Endpoints RESTful de Exames (/exame)
    │   ├── reagente_controller.py    # Endpoints RESTful de Lotes de Reagentes (/reagente)
    │   └── estoque_reagente_controller.py # Endpoints de Estoque Consolidado (/estoque_reagente)
    ├── data/                         # Dados de referência estáticos
    │   └── especies_catalogo.csv     # Catálogo taxonômico padrão de espécies
    ├── models/                       # Modelos Pydantic v2 e DTOs (Diretriz de Entidade Pura)
    │   ├── Animal/                   # Entidade, DTOs (Create, Update, Details) e Enums
    │   ├── Especie/                  # Entidade, DTOs (Create, Update, Details) e Enum Classe
    │   ├── Amostra/                  # Entidade, DTOs (Create, Update, Details) e Enums
    │   ├── Exame/                    # Entidade, DTOs (Create, Update, Details) e Enums
    │   ├── Reagente/                 # Entidade Reagente (lotes), DTOs (Create, Update, Details) e Enums
    │   ├── EstoqueReagente/          # Modelo Agregado EstoqueReagente e DTOs (Create, Update, Details)
    │   └── Usuario/                  # Modelo Usuario e Enum Perfil
    ├── repositories/                 # Repositórios de dados e índices em memória (DAO O(1))
    │   ├── animal_repository.py      # Repositório de Animais
    │   ├── especie_repository.py     # Repositório de Espécies
    │   ├── amostra_repository.py     # Repositório de Amostras
    │   ├── exame_repository.py       # Repositório de Exames Laboratoriais
    │   ├── reagente_repository.py    # Repositório de Lotes Físicos de Reagentes
    │   └── estoque_reagente_repository.py # Repositório de Estoque Consolidado
    ├── services/                     # Serviços de domínio e regras de negócio
    │   ├── animal_service.py         # Regras de biometria, idade e ciclo de vida de Animal
    │   ├── especie_service.py        # Resolução taxonômica, reconstrução de schemas e catálogo
    │   ├── amostra_service.py        # Normalização de matriz biológica e integridade com Animal
    │   ├── exame_service.py          # Ciclo de vida de Exames e integridade referencial com Amostras
    │   ├── reagente_service.py       # Validação de lotes, datas de validade e gatilho de estoque
    │   └── estoque_reagente_service.py # Agregação dimensional, conversões de unidade e inventário
    └── utils/                        # Utilitários e formatadores auxiliares
        ├── __init__.py               # Fachada de re-exportação canônica e retrocompatibilidade
        └── normalizacao/             # Pacote modular especializado de normalização
            ├── comum.py              # Tratamento de sentinelas, booleanos tolerantes, datas e Enums
            ├── local.py              # Coordenadas decimais/DMS e composição/decomposição de localidade
            ├── animal.py             # Sanitização de peso, dedução de faixa etária, sexo e status vital
            ├── amostra_exame.py      # Matrizes biológicas, metodologias e resultados de ensaios
            ├── reagente.py           # Conversões de unidade, unicidade de lotes, validade e métricas
            └── __init__.py           # Exportador consolidado do ecossistema de normalização
```

---

## 3. Tecnologias e Dependências

| Pacote | Versão Mínima | Finalidade |
| :--- | :--- | :--- |
| **Python** | `3.11+` | Ambiente de execução e tipagem estática moderna (totalmente compatível com Python 3.14). |
| **FastAPI** | `>=0.110.0` | Framework web assíncrono para construção da API RESTful com OpenAPI/Swagger automático. |
| **Uvicorn** | `>=0.29.0` | Servidor ASGI de alta performance para a aplicação FastAPI. |
| **Pydantic** | `>=2.6.0` | Validação de schemas, serialização e contratos de dados fortemente tipados. |
| **PyMongo** | `>=4.6.0` | Driver oficial do MongoDB para persistência atômica e upserts idempotentes. |
| **Openpyxl** | `>=3.1.0` | Leitura de alta performance de planilhas Excel estruturadas para o ETL. |
| **Email-Validator** | `>=2.0.0` | Validação formal de formato de e-mail (`EmailStr`). |

---

## 4. Modelos de Domínio e Entidades (Pydantic v2)

Todos os modelos utilizam `ConfigDict(populate_by_name=True)`, permitindo instanciação tanto via atributos padrão do Python quanto via aliases correspondentes aos documentos salvos no MongoDB (ex.: `_id` $\leftrightarrow$ `id`/`animal_id`/`amostra_id`).

### 4.1. Usuário (`Usuario` e Enum `Perfil`)
- **Arquivo**: [src/models/Usuario/usuario.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/models/Usuario/usuario.py)
- **Enum `Perfil`**: `DOCENTE`, `POS_GRADUANDO`, `BOLSISTA_PIBITI`, `BOLSISTA_PIBIC`, `BOLSISTA_EXTERNO`.
- **Campos**: `id`, `username`, `name`, `email` (`EmailStr`), `password` (hash Bcrypt), `created_at`, `last_login`, `perfil`, `matricula`.

### 4.2. Módulo de Espécie (`Especie`, DTOs e Enum `Classe`)
- **Modelos e DTOs** em `src/models/Especie/`:
  - `Especie`: Entidade contendo `id`, `nome_comum`, `nome_cientifico` e `classe`.
  - `EspecieCreate`: DTO com flag `confirmar_nova_especie: bool = False`.
  - `EspecieUpdate`: DTO com flag `confirmar_atualizacao_especie: bool = False`.
  - `EspecieDetails`: Schema de resposta agregando contagem e lista de animais associados.
- **Enum `Classe`**: `AVES` (`"Ave"`), `MAMIFERO` (`"Mamífero"`), `REPTIL` (`"Réptil"`), `ANFIBIO` (`"Anfíbio"`), `PEIXE` (`"Peixe"`).

### 4.3. Módulo de Animal (`Animal`, DTOs e Enums de Domínio)
- **Modelos e DTOs** em `src/models/Animal/`:
  - `Animal`: Entidade central contendo `animal_id` (alias `_id`), `classe`, `nome_comum`, `nome_cientifico`, `sexo`, `peso`, `faixa_etaria`, `orgao_origem`, `local_origem`, `regime_vida`, `status_vital`, além dos opcionais `animal_id_projeto`, `microchip`, `funcao`, `idade`, `suspeita_clinica` e `animal_observacoes`.
  - `AnimalCreate`: DTO estrito para novos cadastros (com flags de confirmação `confirmar_novo_animal` e `confirmar_nova_especie`).
  - `AnimalUpdate`: DTO para atualização parcial de dados cadastrais.
  - `AnimalDetails`: Schema enriquecido que substitui campos nulos por `"Não informado"`, aninha o modelo `Especie` e agrega `quantidade_amostras` e a lista `amostras: List[Amostra]`.
- **Enums de Domínio**:
  - `Sexo`: `Macho`, `Fêmea`, `Indeterminado`, `Não informado`.
  - `FaixaEtaria`: `Filhote`, `Juvenil`, `Jovem`, `Sub Adulto`, `Adulto`, `Senil`, `Idoso`, `Potro`, `Ninhego`, `Não informado`.
  - `Orgao`: Órgãos de custódia e origem (`UFPI`, `HVU`, `CCZ`, CETAS, `NAO INFORMADO`, etc.).
  - `RegimeVida`: `Vida livre`, `Cativeiro`, `Domiciliado`, `Não informado`.
  - `Funcao`: `Pet`, `Trabalho`, `Lazer`, `Reprodução`, `Conservação / Zoológico`, `Outro`, `Não aplicável`.
  - `StatusVital`: `Vivo`, `Morto`, `Eutanasiado`, `Não informado`.

### 4.4. Módulo de Amostra Biológica (`Amostra`, DTOs e Enums)
- **Modelos e DTOs** em `src/models/Amostra/`:
  - `Amostra`: `amostra_id`, `animal_id`, `data_coleta_amostra`, `data_entrega`, `material_biologico`, `status_amostra`, `laudo_liberado`, `local_coleta_amostra`, `nome_coletor`, `condicao_armazenamento`, `fase_amostra`, `destino_amostra`, `kit_utilizado`, `caixa_armazenamento`, frações disponíveis (`dna_disponivel`, `rna_disponivel`, `sequenciamento_disponivel`), latitude, longitude e observações.
  - `AmostraCreate`: DTO estrito de criação com flags `confirmar_nova_amostra` e `confirmar_novo_animal`.
  - `AmostraUpdate`: DTO de atualização parcial com flag `confirmar_atualizacao_amostra`.
  - `AmostraDetails`: Schema com objeto `Animal` agregado e lista/contagem de exames laboratoriais.
- **Enums de Domínio**:
  - `MaterialBiologico`: 29 matrizes biológicas normalizadas (Swabs, Sangue, Órgãos, Tecidos, Fezes, etc.).
  - `CondicaoArmazenamento`: `Temperatura ambiente`, `Refrigerada`, `Congelada`, `Sem identificação`, `Coagulada`, `Hemolisada`, `Nitrogênio líquido`, `Gelo seco`.
  - `FaseAmostra`: `Extração`, `PCR`, `ELETRO`.
  - `DestinoAmostra`: `Biobanco UFPI`, `Biobanco UFPA`, `Fiofruz AM`, `LAB VIGILÂNCIA DE EPIZOOTIAS - UFPI`, etc.
  - `StatusAmostra`: `Disponível`, `Reservada`, `Em uso`, `Perdida`, `Esgotada`.

### 4.5. Exame Laboratorial (`Exame` e Enums)
- **Modelos e DTOs** em `src/models/Exame/`:
  - `Exame`: Entidade contendo `id` (alias `_id`), `amostra_id`, `tipo_exame` (`TipoExame`), `resultado` (`ResultadoExame`, alias `resultado_detalhado`), `data_realizacao`, `material_biologico`, `teste_laboratorial` (`TesteLaboratorial`), `laboratorio_realizador`, `responsavel_exame`, `kit_utilizado`, `protocolo_exame` e `exame_observacoes`.
  - `ExameCreate`: DTO estrito para novos cadastros com validação de campos obrigatórios e vínculo à amostra.
  - `ExameUpdate`: DTO para atualização de exames laboratoriais.
  - `ExameDetails`: Schema enriquecido para projeção e emissão de laudo laboratorial.
- **Enums de Domínio**:
  - `TesteLaboratorial`: `PCR`, `Sorológico`, `Coproparasitológico`, `Hemoparasito em lâmina`, `Outro`.
  - `TipoExame`: Patógenos e ensaios de vigilância (`Febre do Nilo`, `OrthoFlaviviridae`, `Flavivírus`, `Febre Amarela`, `Mycoplasma`, `Herpesviridae`, `Herpesvírus`, `Trypanosomatidae`, `Resistência Bacteriana`, `Hepatozoon`, `Raiva`, `Chlamydia`, `Sarcocystidae`, `Plasmodium e Haemoproteus`, `AIMES`, `Covid Oral`, `Covid Retal`, `Outro`).
  - `ResultadoExame`: `Positivo`, `Negativo`, `Inconclusivo`, `Aguardando Resultado`, `Não Realizado`.

### 4.6. Reagente e Estoque (`Reagente` e `EstoqueReagente`)
- **Módulo de Lotes Físicos (`src/models/Reagente/`)**:
  - `Reagente`: Entidade representativa de um lote físico de reagente químico ou biológico contendo `id` (alias `_id`), `reagente_codigo` (alias `codigo`), `reagente_nome` (alias `nome`), `numero_lote`, `marca`, `data_validade`, `quantidade_unidade`, `reagente_local_armazenamento` (alias `local_armazenamento`), `reagente_id`, `quantidade_volume`, `unidade_medida` (`UnidadeMedida`), `reagente_etapa` (`EtapaReagente`), `reagente_observacoes`, além dos atributos calculados `esta_vencido: Optional[bool]` e `dias_para_vencer: Optional[int]`.
  - `ReagenteCreate`: DTO de cadastro de lote com flag `confirmar_novo_reagente: bool = False`.
  - `ReagenteUpdate`: DTO de atualização cadastral de lote físico.
  - `ReagenteDetails`: Schema de resposta com projeção de validade em tempo real (`esta_vencido`, `dias_para_vencer`).
  - **Enums**: `EtapaReagente` (`Extração`, `PCR`, `Eletroforese`, `Sequenciamento`, `Geral`), `UnidadeMedida` (`ml`, `L`, `µl`, `g`, `kg`, `mg`, `un`).
- **Módulo de Estoque Agregado (`src/models/EstoqueReagente/`)**:
  - `EstoqueReagente`: Modelo agregado que consolida todos os lotes de um mesmo reagente, contendo `id`, `reagente_nome`, `reagente_codigo`, `lotes: List[Reagente]`, `quantidade_total_unidades` (soma de frascos), `quantidade_total_volume` (volume/massa total unificado na unidade base), `totais_por_unidade: Dict[str, float]` (segregado por unidade declarada), `totais_convertidos_base: Dict[str, float]` (em `ml` ou `g`) e `resumo_estoque` legível.
  - `EstoqueReagenteCreate`: DTO para criação ou inicialização agregada de estoque.
  - `EstoqueReagenteUpdate`: DTO para edição de metadados agregados.
  - `EstoqueReagenteDetails`: Schema com listagem de lotes físicos enriquecidos com indicadores de vencimento.

---

## 5. Camada de Serviços e Regras de Negócio (`src/services/`)

### 5.1. `AnimalService` e Regras de Biometria/Faixa Etária
- **Arquivo**: [src/services/animal_service.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/services/animal_service.py)
- **Funcionalidades**:
  1. **Sanitização de Peso**: Converte strings de gramas para kg (`"400g"` $\rightarrow$ `0.4`), vírgula decimal para ponto (`"12,5"` $\rightarrow$ `12.5`), e sentinelas (`"-"`, `"NI"`, `""`) para `"Não aferido"`. Exige números estritamente positivos ($> 0$).
  2. **Dedução de Faixa Etária**: Infere faixas a partir de termos qualitativos ou idades temporais (`< 1.0` ano $\rightarrow$ Filhote; `< 2.0` anos $\rightarrow$ Juvenil; `< 4.0` anos $\rightarrow$ Sub Adulto; `< 10.0` anos $\rightarrow$ Adulto; $\ge 10.0$ anos $\rightarrow$ Senil).
  3. **Resolução de Espécie**: Delega validação binomial e consistência taxonômica para `EspecieService`.
  4. **Enriquecimento (`AnimalDetails`)**: Preenche campos ausentes com `"Não informado"` e consolida lista de amostras.

### 5.2. `EspecieService` e Taxonomia Zoológica
- **Arquivo**: [src/services/especie_service.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/services/especie_service.py)
- **Funcionalidades**:
  1. **Formatação Binomial**: Garante convenção de nomenclatura zoológica (primeira letra maiúscula, epíteto em minúsculo).
  2. **Resolução Taxonômica (`resolver_especie`)**:
     - Se informado apenas o nome científico, preenche automaticamente nome comum e classe.
     - Se informado apenas o nome comum, preenche nome científico e classe.
     - Se informados ambos, valida a coerência cadastrada.
     - Se inédita, exige preenchimento total e `confirmar_nova_especie=True`.
  3. **Delegação de Ingestão**: O método `importar_tabela_csv` delega a leitura do CSV diretamente para [etl/catalogo.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/etl/catalogo.py).
  4. **Resolução de Schemas Bidirecionais**: Garante `EspecieDetails.model_rebuild(_types_namespace={"Animal": Animal})` e exporta modelos diretamente pelo Service.

### 5.3. `AmostraService` e Normalização de Matrizes
- **Arquivo**: [src/services/amostra_service.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/services/amostra_service.py)
- **Funcionalidades**:
  1. **Normalização de Matrizes Biológicas**: Utiliza `src.utils.normalizacao` para mapeamento por especificidade decrescente (ex: `"swab oral e cloacal"` antes de `"swab oral"`; `"pool de tecidos"` antes de `"tecido"`).
  2. **Integridade com Animal**: Verifica a existência prévia do animal de origem ou exige a flag `confirmar_novo_animal=True`.
  3. **Normalização de Enums e Tipos**: Converte strings para os Enums estritos do domínio via `normalizar_enum` e `normalizar_booleano`.
  4. **Enriquecimento (`AmostraDetails`)**: Agrega a entidade completa do animal de origem e os exames vinculados.

### 5.4. Simplificação dos Services e Eliminação de `carga_legada`
Nas versões anteriores, os Services possuíam branches condicionais controlados pelo parâmetro `carga_legada=True`, preenchendo defaults permissivos e mantendo dezenas de aliases de colunas de planilhas (`_ALIASES_ANIMAL` e `_ALIASES_AMOSTRA`).
- **Arquitetura Atual**:
  - `_ALIASES_ANIMAL` e `_ALIASES_AMOSTRA` foram enxugados, retendo **apenas** os aliases de compatibilidade declarados nos modelos Pydantic da API REST.
  - O parâmetro `carga_legada` foi **completamente descontinuado** de todos os métodos de Services e rotas de Controllers.
  - O processamento de anomalias legadas pertence exclusivamente ao pipeline de **ETL**, garantindo que os Services operem com regras de validação estritas, transparentes e previsíveis.

### 5.5. Regras de Integridade, Bloqueio de Exclusão e Permissões (RBAC)
1. **Bloqueio de Exclusão com Dependentes**:
   - É estritamente proibido excluir um **Animal** que possua amostras biológicas vinculadas.
   - É estritamente proibido excluir uma **Amostra** que possua exames laboratoriais vinculados.
2. **Matriz de Permissões por Perfil (RBAC)**:
   - **Gerenciar Animais, Amostras e Reagentes**: Docente, Mestrando, Doutorando, Bolsista Externo e Bolsista PIBITI.
   - **Gerenciar Exames**: Docente, Bolsista Externo e Bolsista PIBITI.
   - **Visualização e Consulta Geral**: Docente, Mestrando, Doutorando, Bolsista Externo, Bolsista PIBIC e Bolsista PIBITI.

### 5.6. `ReagenteService`, `EstoqueReagenteService` e Sincronização Automática
- **Arquivos**: [src/services/reagente_service.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/services/reagente_service.py) e [src/services/estoque_reagente_service.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/services/estoque_reagente_service.py)
- **Funcionalidades e Regras de Negócio**:
  1. **Validação de Unicidade e Consistência de Lotes**:
     - Impede lotes duplicados para o mesmo fabricante e reagente.
     - Valida `quantidade_unidade >= 1` e `quantidade_volume > 0`.
  2. **Cálculos Temporais de Validade**:
     - Computa dinamicamente `esta_vencido` (`data_validade < date.today()`) e `dias_para_vencer` (`(data_validade - date.today()).days`).
  3. **Consolidação Dimensional de Estoque (`calcular_metricas_estoque`)**:
     - Agrupa lotes pelo nome normalizado do reagente.
     - Converte unidades compatíveis para as bases padrão laboratoriais (`ml` para volume líquido, `g` para massa sólida).
     - Gera dicionários estruturados `totais_por_unidade` e `totais_convertidos_base`.
  4. **Sincronização Automática Bidirecional**:
     - A criação, edição ou exclusão de um lote físico em `ReagenteService` dispara automaticamente a sincronização e atualização de `EstoqueReagente`.
     - `EstoqueReagenteService` disponibiliza rotinas de recálculo global de todo o inventário (`recalcular_todo_estoque`).

---

## 6. Módulo de Utilitários e Normalização de Domínio (`src/utils/`)

O módulo foi estruturado no pacote modular especializado `src/utils/normalizacao/`, substituindo o antigo arquivo monolítico e promovendo alta coesão, testabilidade isolada e separação clara de responsabilidades por domínio laboratorial.

### 6.1. Pacote Modular de Normalização (`src/utils/normalizacao/`)
- **Arquitetura Modular**:
  1. **`comum.py`** — Normalizações Genéricas e Sentinelas:
     - `normalizar_data(val)`: Converte formatos ISO (`AAAA-MM-DD`), brasileiros (`DD/MM/AAAA`), timestamps e objetos `datetime`, convertendo sentinelas (`"-"`, `"NI"`, `"Não informado"`) para `None`.
     - `normalizar_booleano(val)`: Converte variantes afirmativas (`"sim"`, `"+"`, `"positivo"`, `1`) e negativas (`"não"`, `"-"`, `"negativo"`, `0`) de forma tolerante.
     - `normalizar_enum(enum_cls, val)`: Normalização tolerante a variações textuais, maiúsculas/minúsculas e acentos para membros de qualquer Enum Pydantic.
     - `eh_nao_informado(val)`: Identificação padronizada de valores nulos, vazios ou sentinelas laboratoriais.
  2. **`local.py`** — Coordenadas Geográficas e Localidades:
     - `normalizar_coordenada(val)`: Converte strings, floats com vírgula e graus sexagesimais DMS (ex: `05°05'21"S`) para float decimal WGS84 com precisão científica.
     - `decompor_localidade(val)`: Decompõe strings compostas (ex: `"Teresina/PI - Zoobotânico"`) em `municipio`, `uf` (sigla de 2 letras validada) e `localidade_detalhe`.
  3. **`animal.py`** — Biometria e Parâmetros Animais:
     - `sanitizar_peso(val)` / `decompor_peso(val)`: Converte gramas/miligramas para kg (`"400g"` $\rightarrow$ `0.4`), tratando vírgulas e sentinelas.
     - `deduzir_faixa_etaria(idade, faixa_etaria)`: Mapeia idades temporais e descrições qualitativas para o Enum canônico `FaixaEtaria`.
     - `normalizar_sexo(val)` e `normalizar_status_vital(val)`: Converte variações laboratoriais para Enums `Sexo` e `StatusVital`.
  4. **`amostra_exame.py`** — Matrizes Biológicas e Ensaio Laboratorial:
     - `normalizar_material_biologico(val)`: Mapeamento de 29 matrizes biológicas por especificidade decrescente para o Enum `MaterialBiologico`.
     - `normalizar_tipo_exame(val)`, `normalizar_resultado_exame(val)`, `normalizar_teste_laboratorial(val)`.
  5. **`reagente.py`** — Dimensionalidade e Métricas de Estoque:
     - `FATORES_CONVERSAO`: Tabela de conversão volumétrica (`l`, `ml`, `ul`) e mássica (`kg`, `g`, `mg`).
     - `normalizar_unidade_medida(val)` e `normalizar_etapa_reagente(val)`: Padronização de unidades e etapas.
     - `calcular_vencimento(data_validade)`: Retorna tupla `(esta_vencido, dias_para_vencer)`.
     - `calcular_metricas_estoque(lotes)`: Agrega volumes, calcula conversões de base e gera resumo de estoque.
     - `validar_lotes_unicos(lotes)`: Garante integridade e unicidade de lote por fabricante.
  6. **`__init__.py`** — Fachada Canônica:
     - Re-exporta todos os símbolos do ecossistema de normalização para importação centralizada (`from src.utils.normalizacao import ...`), garantindo retrocompatibilidade total.
     - Normaliza de maneira tolerante strings textuais para membros de qualquer Enum de domínio Pydantic, ignorando diferenças de maiúsculas/minúsculas, espaços e pontuações.

---

## 7. Pipeline de ETL e Migração de Planilhas (`etl/`)

### 7.1. Arquitetura do Pipeline de Dados
O pipeline de dados converte planilhas esparsas de vigilância de epizootias em lotes canônicos serializados em JSON Lines (`.jsonl`), prontos para ingestão transacional no banco de dados MongoDB:

```
Planilhas Excel/CSV (../planilhas/)
               │
               ▼
   [Extrator Especializado] (ex: etl/morcegos.py)
   ├── Parsing e higienização linha a linha
   ├── Identificação de anomalias taxonômicas e biológicas
   └── Geração de documentos canônicos em memória
               │
               ├──────────────────────────────┐
               ▼                              ▼
   Arquivos .jsonl (etl/saida/)     Relatório problemas.csv
   ├── animais.jsonl                          │
   ├── amostras.jsonl                         ▼
   └── exames.jsonl                 (Análise e auditoria)
               │
               ▼
   [Carregador Genérico] (etl/carregar.py)
   ├── 1. Leitura dos lotes canônicos
   ├── 2. Validação direta via Pydantic v2 (Animal / Amostra / Exame)
   ├── 3. Verificação de integridade referencial de vínculos em 2 passos
   └── 4. Upsert idempotente no MongoDB (exclusivo para pibit_app_dev)
```

### 7.2. Extrator Base e Dataclasses (`etl/base.py`)
Define o contrato de extração e estruturas de dados de auditoria:
- `ProblemaLinha`: Registra a planilha, número da linha, identificação do animal, coluna e motivo da divergência.
- `Resultado`: Contêiner com as listas de animais, amostras, exames extraídos e problemas acumulados.
- `ExtratorBase`: Classe abstrata com métodos de escrita em JSON Lines e exportação de relatórios CSV.

### 7.3. Extrator de Morcegos (`etl/morcegos.py`)
Mapeia a complexa planilha histórica `Planilha dos morcegos (atualizada 2022)_outubro 2022.xlsx`:
- **Extração Realizada**:
  - **136 animais** catalogados com identificações sem colisão (ex: prefixo de abas homônimas `FL_` para Floriano).
  - **767 amostras** distribuídas entre matrizes de sangue, papel filtro, esfregaço, swab oral e tecidos necropsiados (pulmão, coração, fígado).
  - **303 exames** mapeados (PCR para Herpesviridae e Coronavírus oral/retal).
  - **76 problemas** logados em `problemas.csv` para auditoria laboratorial (ex: óbitos em transporte, espécies ausentes).

### 7.4. Catálogo e Seeding Taxonômico (`etl/catalogo.py`)
- Módulo independente e CLI (`python -m etl.catalogo [caminho.csv]`) para povoar o acervo de espécies a partir de arquivos CSV taxonômicos.
- Realiza normalização de classes (`normalizar_classe_taxonomica`) e formatação binomial de nomes científicos (`formatar_nome_cientifico`).

### 7.5. Carregador e Validador Canônico (`etl/carregar.py`)
- **Validação Direta contra Pydantic**: Valida cada documento canônico diretamente com `Animal(**doc)`, `Amostra(**doc)` e `Exame(**doc)`, sem dependência de lógica ad-hoc de serviços.
- **Verificação de Vínculos em 2 Passos**:
  - Amostras devem apontar para animais presentes no mesmo lote ou já existentes no banco.
  - Exames devem apontar para amostras presentes no lote ou no banco.
  - Vínculos órfãos são descartados e detalhados no relatório de carga.
- **Segurança de Banco**: Restringe a persistência exclusivamente ao banco de dados de desenvolvimento `pibit_app_dev`.
- **Modos de Operação**:
  - `--dry-run` (padrão): Executa parsing, validação completa de schemas e checagem referencial sem persistência.
  - `--aplicar`: Executa operações de upsert idempotente (`update_one({"_id": id}, {"$set": doc}, upsert=True)`).

---

## 8. Camada de Repositórios e Persistência (`src/repositories/`)

### 8.1. Padrão DAO e Indexação em Memória $O(1)$
Os repositórios (`backend/src/repositories/`) implementam o padrão DAO (*Data Access Object*). Para conferir agilidade a testes, scripts de migração e consultas, utilizam estruturas indexadas em memória com chaves normalizadas (`casefold()`, `strip()`), garantindo buscas em tempo constante $O(1)$ para chaves primárias e índices secundários.

### 8.2. Matriz de Repositórios e Métodos Disponíveis

| Repositório | Arquivo | Índices em Memória | Principais Métodos |
| :--- | :--- | :--- | :--- |
| **`EspecieRepository`** | [especie_repository.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/repositories/especie_repository.py) | `_por_id` (int), `_por_comum` (str), `_por_cientifico` (str), `_por_classe` (Classe $\rightarrow$ List) | `create`, `save`, `update`, `delete`, `buscar_por_id`, `buscar_por_nome_comum`, `buscar_por_nome_cientifico`, `buscar_por_classe`, `listar`, `count`, `exists`, `clear` |
| **`AnimalRepository`** | [animal_repository.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/repositories/animal_repository.py) | `_por_animal_id` (str), `_por_id` (int), `_por_projeto_id`, `_por_microchip`, `_por_nome_comum`, `_por_nome_cientifico`, `_por_classe`, `_por_sexo`, `_por_faixa_etaria`, `_por_orgao_origem`, `_por_regime_vida`, `_por_status_vital`, `_por_funcao` | `create`, `save`, `update`, `delete`, `buscar_por_animal_id`, `buscar_por_especie`, `listar` (filtros múltiplos, busca textual e paginação), `count`, `exists`, `clear` |
| **`AmostraRepository`** | [amostra_repository.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/repositories/amostra_repository.py) | `_por_amostra_id` (str), `_por_id` (int), `_por_animal_id` (1:N $\rightarrow$ List), `_por_condicao_armazenamento`, `_por_destino_amostra`, `_por_fase_amostra`, `_por_material_biologico`, `_por_status_amostra` | `create`, `save`, `update`, `delete`, `buscar_por_amostra_id`, `buscar_por_animal_id`, `listar` (filtros analíticos, ordenação e paginação), `count`, `exists`, `clear` |
| **`ExameRepository`** | [exame_repository.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/repositories/exame_repository.py) | `_por_id` (int), `_por_exame_id` (str), `_por_amostra_id` (1:N $\rightarrow$ List), `_por_tipo_exame`, `_por_resultado`, `_por_teste_laboratorial`, `_por_responsavel` | `create`, `save`, `update`, `delete`, `buscar_por_id`, `buscar_por_exame_id`, `buscar_por_amostra_id`, `listar` (filtros analíticos, ordenação e paginação), `count`, `exists`, `clear` |
| **`ReagenteRepository`** | [reagente_repository.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/repositories/reagente_repository.py) | `_por_id` (int), `_por_reagente_id` (str), `_por_codigo` (1:N $\rightarrow$ List), `_por_nome` (1:N $\rightarrow$ List), `_por_lote` (1:N $\rightarrow$ List), `_por_marca`, `_por_local` | `create`, `save`, `update`, `delete`, `buscar_por_id`, `buscar_por_codigo`, `buscar_por_nome`, `buscar_por_lote`, `listar` (filtros de vencimento, busca textual, paginação), `count`, `exists`, `clear` |
| **`EstoqueReagenteRepository`** | [estoque_reagente_repository.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/repositories/estoque_reagente_repository.py) | `_por_id` (int), `_por_nome` (str $\rightarrow$ EstoqueReagente), `_por_codigo` (1:N $\rightarrow$ List) | `create`, `save`, `update`, `delete`, `buscar_por_id`, `buscar_por_nome`, `buscar_por_codigo`, `listar` (busca textual, ordenação, paginação), `count`, `exists`, `clear` |

---

## 9. API HTTP (FastAPI) e Controladores (`src/controllers/`)

### 9.1. Centralização de Respostas HTTP e Tratamento de Erros (`response_controller.py`)
Para evitar a replicação exaustiva de blocos `try/except` em cada endpoint e padronizar os contratos de resposta e documentação OpenAPI/Swagger em toda a API, o backend centraliza a infraestrutura de respostas e exceções em [response_controller.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/controllers/response_controller.py):

#### 1. Mapeamento Canônico de Exceções (`EXCECOES_HTTP`)
A camada de serviços opera lançando exceções semânticas de domínio/Python padrão, que são interceptadas e convertidas de forma transparente para os status codes HTTP correspondentes:
- `NoContentError` / `SemConteudoError` $\rightarrow$ `HTTP 204 No Content` (sem corpo de resposta).
- `ValueError` $\rightarrow$ `HTTP 400 Bad Request` (regras de negócio violadas, IDs duplicados ou flags de confirmação ausentes).
- `PermissionError` $\rightarrow$ `HTTP 403 Forbidden` (ações não permitidas pelo perfil ou regra de segurança).
- `KeyError` / `FileNotFoundError` $\rightarrow$ `HTTP 404 Not Found` (recursos ou arquivos não localizados; a mensagem é extraída diretamente de `args[0]` para evitar aspas extras de formatação).

#### 2. Contrato de Respostas: Códigos de Status HTTP e Mensagens
O protocolo HTTP opera em duas camadas complementares (código de status e corpo da mensagem):
- **Código de Status HTTP (Sempre Presente)**: Toda resposta da API transporta o código de status na linha de status do protocolo (ex.: `200 OK`, `201 Created`, `204 No Content`, `400 Bad Request`, `403 Forbidden`, `404 Not Found`, `500 Internal Server Error`), permitindo que clientes (como Axios, Fetch API ou aplicações mobile) decidam o fluxo antes mesmo de inspecionar o payload.
- **Respostas de Sucesso com Dados (`200 OK` e `201 Created`)**: Retornam diretamente a entidade pura serializada ou a lista/modelo de detalhes (ex.: `Animal`, `Amostra`, `Exame`, `EspecieDetails`), mantendo máxima fidelidade ao contrato de dados tipado pelo Pydantic, sem embrulhos redundantes.
- **Respostas de Sucesso sem Dados (`204 No Content`)**: Aplicadas primariamente a rotas de exclusão (`DELETE`), retornam cabeçalhos HTTP com corpo estritamente vazio (`b""`).
- **Respostas de Erro (`400`, `403`, `404`, `500`)**: Retornam o schema padrão `ErroResposta` serializado em JSON com o detalhamento legível da falha:
  ```json
  {
    "detail": "Animal com identificador 'ANI_999' não encontrado."
  }
  ```

#### 3. Catálogo de Respostas HTTP e Documentação OpenAPI (`RESPOSTAS`)
O módulo define o catálogo mestre `RESPOSTAS` com esquemas, exemplos e descrições técnicas, além da função utilitária `respostas(*codigos)` (que sempre anexa a documentação de `500 Internal Server Error`).

A partir dele, são exportados conjuntos prontos utilizados no parâmetro `responses=` de cada rota para enriquecimento da documentação interativa (`/docs` e `/redoc`):
- `RESPOSTAS_CRIAR`: `HTTP 201 Created`, `400 Bad Request`, `403 Forbidden`, `404 Not Found`, `500 Internal Server Error`.
- `RESPOSTAS_LISTAR`: `HTTP 200 OK`, `400 Bad Request`, `500 Internal Server Error`.
- `RESPOSTAS_BUSCAR`: `HTTP 200 OK`, `400 Bad Request`, `404 Not Found`, `500 Internal Server Error`.
- `RESPOSTAS_OBTER`: `HTTP 200 OK`, `404 Not Found`, `500 Internal Server Error`.
- `RESPOSTAS_ATUALIZAR`: `HTTP 200 OK`, `400 Bad Request`, `403 Forbidden`, `404 Not Found`, `500 Internal Server Error`.
- `RESPOSTAS_DELETAR`: `HTTP 204 No Content`, `403 Forbidden`, `404 Not Found`, `500 Internal Server Error`.
- `RESPOSTAS_CONTAGEM`: `HTTP 200 OK`, `500 Internal Server Error`.
- `RESPOSTAS_PROCESSAMENTO`: `HTTP 200 OK`, `400 Bad Request`, `404 Not Found`, `500 Internal Server Error`.

#### 4. Infraestrutura de Roteamento e Interceptação
- **`TratamentoErrosRoute(APIRoute)`**: Rota customizada do FastAPI que executa o endpoint, captura as exceções mapeadas e aplica o retorno HTTP apropriado. Configura e força automaticamente endpoints `DELETE` para `HTTP 204 No Content` sem corpo de resposta.
- **Fábrica `criar_router(**kwargs) -> APIRouter`**: Instancia routers já vinculados a `TratamentoErrosRoute`. Utilizada por todos os controllers do ecossistema.
- **Decorador `tratar_erros`**: Decorador universal (síncrono/assíncrono) para funções avulsas.
- **Manipulador Global `registrar_tratamento_erros(app)`**: Registrado em [src/main.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/main.py) como rede de segurança ASGI global para exceções não tratadas.

#### 5. Diretriz de Desacoplamento Estrito
Os controladores **não acessam repositórios nem modelos de persistência diretamente**. Todas as chamadas são delegadas aos seus respectivos Services (`animal_service`, `especie_service`, `amostra_service`, `exame_service`, `reagente_service`, `estoque_reagente_service`), que re-exportam entidades, DTOs e tipos necessários.

### 9.2. Endpoints de Animais (`/animal`)
- `POST /animal/`: Cadastro de novo animal com resolução taxonômica e biometria automatizadas (`confirmar_nova_especie: bool`) (Status 201 Created; `responses=RESPOSTAS_CRIAR`).
- `GET /animal/`: Listagem filtrada por `classe`, `sexo`, `status` (regime de vida), `status_vital`, busca textual (`termo_busca`) e paginação (`skip`, `limit`) (Status 200; `responses=RESPOSTAS_LISTAR`).
- `GET /animal/{animal_id}`: Consulta individual por ID único do laboratório (Status 200 / 404; `responses=RESPOSTAS_OBTER`).
- `GET /animal/{animal_id}/detalhes`: Consulta detalhada `AnimalDetails` com espécie e amostras colhidas (Status 200 / 404; `responses=RESPOSTAS_OBTER`).
- `PUT /animal/{animal_id}`: Atualização de animal existente com validação taxonômica (`confirmar_nova_especie: bool`) (Status 200 / 400 / 404; `responses=RESPOSTAS_ATUALIZAR`).
- `DELETE /animal/{animal_id}`: Exclusão de animal cadastrado (bloqueia se houver amostras vinculadas) (Status 204 No Content; `responses=RESPOSTAS_DELETAR`).

### 9.3. Endpoints de Espécies (`/especie`)
- `POST /especie/cadastro`: Cadastro de nova espécie taxonômica com validação binomial (Status 201 Created; `responses=RESPOSTAS_CRIAR`).
- `GET /especie/`: Listagem filtrada por `nome_comum`, `nome_cientifico` e `classe` (Status 200; `responses=RESPOSTAS_BUSCAR`).
- `GET /especie/{id}`: Detalhes taxonômicos acompanhados da lista e contagem de animais associados via `EspecieDetails` (Status 200 / 404; `responses=RESPOSTAS_OBTER`).
- `PUT /especie/{id}`: Atualização de espécie com checagem de duplicidade taxonômica (Status 200 / 400 / 404; `responses=RESPOSTAS_ATUALIZAR`).
- `DELETE /especie/{id}`: Exclusão de espécie (Status 204 No Content; `responses=RESPOSTAS_DELETAR`).
- `POST /especie/importar-catalogo`: Importação em lote de tabela CSV para o catálogo de espécies (Status 200 / 400 / 404; `responses=RESPOSTAS_PROCESSAMENTO`).

### 9.4. Endpoints de Amostras (`/amostra`)
- `POST /amostra/`: Cadastro de nova amostra biológica com validação de animal vinculado (`confirmar_nova_amostra`, `confirmar_novo_animal`) (Status 201 Created; `responses=RESPOSTAS_CRIAR`).
- `GET /amostra/`: Listagem com filtros múltiplos (`animal_id`, `status_amostra`, `fase_amostra`, `condicao_armazenamento`, `destino_amostra`, `material_biologico`), busca textual e paginação (Status 200; `responses=RESPOSTAS_LISTAR`).
- `GET /amostra/contagem`: Quantidade total de amostras no acervo (Status 200; `responses=RESPOSTAS_CONTAGEM`).
- `GET /amostra/animal/{animal_id}`: Todas as amostras colhidas de um determinado animal (Status 200; `responses=RESPOSTAS_LISTAR`).
- `GET /amostra/{amostra_id}`: Consulta individual por ID laboratorial (Status 200 / 404; `responses=RESPOSTAS_OBTER`).
- `GET /amostra/{amostra_id}/detalhes`: Detalhes completos `AmostraDetails` com entidade `Animal` e exames diagnósticos (Status 200 / 404; `responses=RESPOSTAS_OBTER`).
- `PATCH /amostra/{amostra_id}`: Atualização parcial de campos com re-normalização de matriz (Status 200 / 400 / 404; `responses=RESPOSTAS_ATUALIZAR`).
- `DELETE /amostra/{amostra_id}`: Exclusão de amostra (bloqueia se houver exames vinculados) (Status 204 No Content; `responses=RESPOSTAS_DELETAR`).

### 9.5. Endpoints de Exames (`/exame`)
- `POST /exame/`: Cadastrar novo exame laboratorial com validação de vínculo com a amostra (`confirmar_novo_exame`, `confirmar_nova_amostra`) (Status 201 Created; `responses=RESPOSTAS_CRIAR`).
- `GET /exame/`: Listagem com filtros cruzados por `amostra_id`, `tipo_exame`, `resultado`, `teste_laboratorial`, `data_realizacao`, `responsavel_exame`, busca textual e paginação (Status 200; `responses=RESPOSTAS_LISTAR`).
- `GET /exame/contagem`: Quantidade total de exames laboratoriais registrados (Status 200; `responses=RESPOSTAS_CONTAGEM`).
- `GET /exame/amostra/{amostra_id}`: Todos os exames laboratoriais realizados para uma amostra específica (Status 200; `responses=RESPOSTAS_LISTAR`).
- `GET /exame/{identificador}`: Recuperar exame por ID numérico ou código alfanumérico (Status 200 / 404; `responses=RESPOSTAS_OBTER`).
- `GET /exame/{identificador}/detalhes`: Consulta de laudo detalhado `ExameDetails` com saneamento de valores (Status 200 / 404; `responses=RESPOSTAS_OBTER`).
- `PUT /exame/{identificador}` e `PATCH /exame/{identificador}`: Atualização de exame com integridade da amostra (Status 200 / 400 / 404; `responses=RESPOSTAS_ATUALIZAR`).
- `DELETE /exame/{identificador}`: Remoção de exame laboratorial (Status 204 No Content; `responses=RESPOSTAS_DELETAR`).

### 9.6. Endpoints de Reagentes (`/reagente`)
- `POST /reagente/`: Cadastrar novo lote físico de reagente com validação de unicidade, cálculo de validade e gatilho de sincronização de estoque (`confirmar_novo_reagente: bool`) (Status 201 Created; `responses=RESPOSTAS_CRIAR`).
- `GET /reagente/`: Listagem de lotes físicos com filtros por `nome`, `codigo`, `marca`, `local_armazenamento`, `apenas_vencidos`, busca textual, ordenação e paginação (Status 200; `responses=RESPOSTAS_LISTAR`).
- `GET /reagente/contagem`: Total de lotes físicos cadastrados no laboratório (Status 200; `responses=RESPOSTAS_CONTAGEM`).
- `GET /reagente/lote/{numero_lote}`: Listar todos os registros vinculados a um número de lote (Status 200; `responses=RESPOSTAS_LISTAR`).
- `GET /reagente/{identificador}`: Obter lote por ID numérico ou identificador `REA_XXXX` (Status 200 / 404; `responses=RESPOSTAS_OBTER`).
- `GET /reagente/{identificador}/detalhes`: Obter `ReagenteDetails` enriquecido com indicadores de validade (`esta_vencido`, `dias_para_vencer`) (Status 200 / 404; `responses=RESPOSTAS_OBTER`).
- `PUT /reagente/{identificador}`: Atualizar dados do lote físico e recalcular estoque consolidado (Status 200 / 400 / 404; `responses=RESPOSTAS_ATUALIZAR`).
- `DELETE /reagente/{identificador}`: Remover lote físico e sincronizar estoque (Status 204 No Content; `responses=RESPOSTAS_DELETAR`).

### 9.7. Endpoints de Estoque Consolidado (`/estoque_reagente`)
- `POST /estoque_reagente/`: Cadastrar nova visão consolidada de estoque (`confirmar_novo_estoque: bool`) (Status 201 Created; `responses=RESPOSTAS_CRIAR`).
- `GET /estoque_reagente/`: Listar estoques agregados com busca textual, filtro `apenas_com_lotes`, ordenação e paginação (Status 200; `responses=RESPOSTAS_LISTAR`).
- `GET /estoque_reagente/contagem`: Quantidade total de reagentes unificados em estoque (Status 200; `responses=RESPOSTAS_CONTAGEM`).
- `POST /estoque_reagente/recalcular`: Varredura completa e recálculo de todo o inventário a partir dos lotes atuais (Status 200; `responses=RESPOSTAS_CONTAGEM`).
- `POST /estoque_reagente/sincronizar/{nome_reagente}`: Recálculo imediato de estoque para um reagente específico (Status 200 / 404; `responses=RESPOSTAS_OBTER`).
- `GET /estoque_reagente/codigo/{codigo}`: Buscar estoque pelo código do reagente (Status 200; `responses=RESPOSTAS_LISTAR`).
- `GET /estoque_reagente/{identificador}`: Obter visão agregada por ID numérico ou nome do reagente (`sincronizar: bool`) (Status 200 / 404; `responses=RESPOSTAS_OBTER`).
- `GET /estoque_reagente/{identificador}/detalhes`: Obter `EstoqueReagenteDetails` com listagem e indicadores de todos os lotes vinculados (Status 200 / 404; `responses=RESPOSTAS_OBTER`).
- `PUT /estoque_reagente/{identificador}`: Atualizar metadados agregados do estoque (Status 200 / 400 / 404; `responses=RESPOSTAS_ATUALIZAR`).
- `DELETE /estoque_reagente/{identificador}`: Remover registro de estoque com opção de deleção em cascata dos lotes físicos (`deletar_lotes_vinculados: bool`) (Status 204 No Content; `responses=RESPOSTAS_DELETAR`).

---

## 10. Suíte de Testes Automatizados (`tests/`)

O backend conta com **84 testes automatizados** cobrindo todas as camadas arquiteturais:

1. **Testes de Animais ([test_animal_service.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/tests/test_animal_service.py))**:
   - Resolução taxonômica pelo catálogo;
   - Processamento de unidades de peso (gramas para kg, vírgulas, `Não aferido`, rejeição de peso zero ou negativo);
   - Dedução de faixas etárias por critérios biológicos;
   - Bloqueio de IDs duplicados e CRUD completo em memória.
2. **Testes de Espécies ([test_especie_service.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/tests/test_especie_service.py))**:
   - Normalização de classes e formatação binomial;
   - Resolução cruzada e detecção de incoerências taxonômicas;
   - Ingestão de catálogo CSV via delegação para o ETL.
3. **Testes de Amostras ([test_amostra_service.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/tests/test_amostra_service.py))**:
   - Normalização de matriz biológica por especificidade decrescente;
   - Validação referencial com o animal de origem e flag `confirmar_novo_animal`;
   - Geração de schema `AmostraDetails`.
4. **Testes do Extrator Base ([test_etl_base.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/tests/test_etl_base.py))**:
   - Validação das estruturas `ProblemaLinha`, `Resultado` e métodos de auditoria.
5. **Testes do Extrator de Morcegos ([test_etl_morcegos.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/tests/test_etl_morcegos.py))**:
   - Parsing de dados brutos de campo, matrizes múltiplas de tecidos e exames virais.
6. **Testes do Carregador ETL ([test_etl_carregar.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/tests/test_etl_carregar.py))**:
   - Validação canônica de documentos Pydantic v2;
   - Detecção e descarte de vínculos órfãos;
   - Simulação de upsert idempotente no MongoDB com trava de segurança em `pibit_app_dev`.
7. **Testes de Correções de Modelos ([test_model_corrections.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/tests/test_model_corrections.py))**:
   - Verificação de schemas, aliases e serialização limpa de entidades.
8. **Testes de Normalização ([test_utils_normalizacao.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/tests/test_utils_normalizacao.py))**:
   - Validação unitária de todas as funções do pacote modular `src.utils.normalizacao` (datas, coordenadas DMS, pesos, faixas etárias, matrizes e conversões de reagentes).
9. **Testes de Reagentes e Estoque ([test_reagente_controlller.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/tests/test_reagente_controlller.py))**:
   - Teste de integração HTTP ponta a ponta com `TestClient(app)` para os controllers `/reagente` e `/estoque_reagente`, validando cadastro de lotes, cálculo automático de validade, consolidação de estoque e sincronização em tempo real.
10. **Testes de Respostas Padronizadas e Centralização de Erros ([test_controllers_centralized_responses.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/tests/test_controllers_centralized_responses.py))**:
    - Validação de que todas as rotas configuradas com `criar_router` e `responses` interceptam automaticamente `KeyError` (404), `FileNotFoundError` (404), `ValueError` (400), `PermissionError` (403) e `NoContentError` (204), cobrindo o fluxo CRUD completo dos controllers sem blocos try/except redundantes.

---

## 11. Como Executar o Backend e o ETL Localmente

### Pré-requisitos
- Python 3.11+ (ou 3.14) instalado
- Ambiente virtual configurado e ativo

```bash
# 1. Ativar o ambiente virtual (dentro de 'backend')
source .venv/bin/activate  # Linux/macOS
# ou: .venv\Scripts\activate no Windows

# 2. Instalar dependências
pip install -r requirements.txt
```

### Execução dos Testes Automatizados
```bash
python -m unittest discover tests
```

### Execução da API FastAPI
```bash
uvicorn src.main:app --reload --port 8000
```
- **Documentação Interativa Swagger**: `http://localhost:8000/docs`
- **Documentação ReDoc**: `http://localhost:8000/redoc`

### Execução do Pipeline de ETL
```bash
# 1. Carga / Seeding do Catálogo de Espécies
python -m etl.catalogo src/data/especies_catalogo.csv

# 2. Extração da Planilha de Morcegos
python -m etl.morcegos

# 3. Validação Dry-Run (sem gravação)
python -m etl.carregar etl/saida/morcegos --dry-run

# 4. Gravação Efetiva no Banco de Dados MongoDB ('pibit_app_dev')
python -m etl.carregar etl/saida/morcegos --aplicar
```

---

## 12. Diretrizes de Qualidade e Boas Práticas

1. **Validação na Borda e Contratos Estritos**: Nenhuma informação deve ser enviada aos repositórios ou ao banco de dados sem validação prévia de seus modelos Pydantic correspondentes.
2. **Separação de Complexidade**: Anomalias e ruídos de planilhas são tratados exclusivamente pelos extratores ETL. Os Services da API devem permanecer enxutos, previsíveis e livres de parâmetros de exceção (`carga_legada`).
3. **Idempotência**: As operações de carga de dados utilizam operações de upsert baseadas em identificadores laboratoriais únicos, permitindo execuções repetidas sem duplicação de dados.
4. **Isolamento de Segredos e Bancos**: Credenciais e URIs de conexão devem ser mantidas em variáveis de ambiente (`MONGO_URI`). O carregador ETL possui trava de segurança que impede a gravação fora de `pibit_app_dev`.
5. **Integridade Referencial**: Bloqueio ativo de exclusão para entidades com registros dependentes (animais com amostras, amostras com exames).