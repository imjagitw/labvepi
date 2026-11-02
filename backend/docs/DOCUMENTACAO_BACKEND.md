# ⚙️ LABVEPI — Documentação Técnica do Backend
> **Laboratório de Vigilância de Epizootias — Universidade Federal do Piauí (UFPI)**  
> *API RESTful, Modelos de Domínio Pydantic v2, Pipeline de ETL Desacoplado, Regras de Negócio, Repositórios e Testes*

---

## 📋 Sumário
1. [Visão Geral e Arquitetura em Camadas](#1-visão-geral-e-arquitetura-em-camadas)
2. [Estrutura de Diretórios](#2-estrutura-de-diretórios)
3. [Tecnologias e Dependências](#3-tecnologias-e-dependências)
4. [Modelos de Domínio e Entidades (Pydantic v2)](#4-modelos-de-domínio-e-entidades-pydantic-v2)
   - [4.1. Módulo de Usuário (`Usuario`, DTOs e Enums `Perfil` e `StatusUsuario`)](#41-módulo-de-usuário-usuario-dtos-e-enums-perfil-e-statususuario)
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
   - [5.7. `UsuarioService`, Autenticação, Ciclo de Vida de Contas e Segurança (Bcrypt)](#57-usuarioservice-autenticação-ciclo-de-vida-de-contas-e-segurança-bcrypt)
6. [Módulo de Utilitários e Normalização de Domínio (`src/utils/`)](#6-módulo-de-utilitários-e-normalização-de-domínio-srcutils)
   - [6.1. Pacote Modular de Normalização (`src/utils/normalizacao/`)](#61-pacote-modular-de-normalização-srcutilsnormalizacao)
   - [6.2. Utilitários de Persistência/Repositório e Exceções de Domínio (`repositorio.py`, `persistencia.py`, `excecoes.py`)](#62-utilitários-de-persistênciarepositório-e-exceções-de-domínio-repositoriopy-persistenciapy-excecoespy)
7. [Pipeline de ETL e Migração de Planilhas (`etl/`)](#7-pipeline-de-etl-e-migração-de-planilhas-etl)
   - [7.1. Arquitetura do Pipeline de Dados](#71-arquitetura-do-pipeline-de-dados)
   - [7.2. Extrator Base e Dataclasses (`etl/base.py`)](#72-extrator-base-e-dataclasses-etlbasepy)
   - [7.3. Extrator de Morcegos (`etl/morcegos.py`)](#73-extrator-de-morcegos-etlmorcegospy)
   - [7.4. Catálogo e Seeding Taxonômico (`etl/catalogo.py`)](#74-catálogo-e-seeding-taxonômico-etlcatalogopy)
   - [7.5. Carregador e Validador Canônico (`etl/carregar.py`)](#75-carregador-e-validador-canônico-etlcarregarpy)
8. [Camada de Repositórios e Persistência (`src/repositories/`)](#8-camada-de-repositórios-e-persistência-srcrepositories)
   - [8.1. Padrão DAO, Modo Dual e Persistência no MongoDB](#81-padrão-dao-modo-dual-e-persistência-no-mongodb)
   - [8.2. Gerenciador de Conexão e Configuração (`src/data/connection.py` e `src/config/`)](#82-gerenciador-de-conexão-e-configuração-srcdataconnectionpy-e-srcconfig)
   - [8.3. Matriz de Repositórios e Coleções MongoDB](#83-matriz-de-repositórios-e-coleções-mongodb)
9. [API HTTP (FastAPI) e Controladores (`src/controllers/`)](#9-api-http-fastapi-e-controladores-srccontrollers)
   - [9.1. Centralização de Respostas HTTP e Tratamento de Erros (`response_controller.py`)](#91-centralização-de-respostas-http-e-tratamento-de-erros-response_controllerpy)
   - [9.2. Endpoints de Animais (`/animal`)](#92-endpoints-de-animais-animal)
   - [9.3. Endpoints de Espécies (`/especie`)](#93-endpoints-de-espécies-especie)
   - [9.4. Endpoints de Amostras (`/amostra`)](#94-endpoints-de-amostras-amostra)
   - [9.5. Endpoints de Exames (`/exame`)](#95-endpoints-de-exames-exame)
   - [9.6. Endpoints de Reagentes (`/reagente`)](#96-endpoints-de-reagentes-reagente)
   - [9.7. Endpoints de Estoque Consolidado (`/estoque`)](#97-endpoints-de-estoque-consolidado-estoque)
   - [9.8. Endpoints de Usuários e Gestão de Contas (`/usuario`)](#98-endpoints-de-usuários-e-gestão-de-contas-usuario)
   - [9.9. Configuração de CORS e Conectividade Multiplataforma](#99-configuração-de-cors-e-conectividade-multiplataforma)
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
├── requirements.txt                  # Dependências do backend (fastapi, uvicorn, pydantic-settings, pymongo, bcrypt, etc.)
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
├── tests/                            # Suíte de testes automatizados (165 testes organizados por domínio)
│   ├── base_test_client.py           # Classe base ControllerTestCase com TestClient(app) e isolamento O(1) dos 7 repositórios em memória
│   ├── animal/                       # Entidade Animal (test_animal_service.py e test_animal_controller.py)
│   ├── amostra/                      # Entidade Amostra (test_amostra_service.py e test_amostra_controller.py)
│   ├── especie/                      # Entidade Espécie (test_especie_service.py e test_especie_controller.py)
│   ├── exame/                        # Entidade Exame (test_exame_controller.py)
│   ├── usuario/                      # Entidade Usuário (test_usuario_service.py e test_usuario_controller.py)
│   ├── reagente_estoque/             # Domínio Reagentes e Estoque (test_reagente_status_rules.py, test_estoque_alertas_endpoint.py, test_reagente_controller.py)
│   ├── utilitarios/                  # Testes transversais (test_utils_normalizacao.py, test_model_corrections.py, test_response_controller.py, test_partial_updates.py)
│   └── etl/                          # Pipeline de Dados (test_etl_base.py, test_etl_morcegos.py, test_etl_carregar.py)
└── src/
    ├── main.py                       # Ponto de entrada FastAPI com lifespan MongoDB e registro global de handlers de erro
    ├── config/                       # Configurações globais e variáveis de ambiente (pydantic-settings)
    │   └── config.py                 # Classe Settings / settings (.env)
    ├── controllers/                  # Controladores e rotas HTTP (endpoints RESTful sem try/except)
    │   ├── response_controller.py    # Respostas HTTP padronizadas e tratamento centralizado de erros: TratamentoErrosRoute, criar_router e catálogo RESPOSTAS
    │   ├── usuario_controller.py     # Endpoints RESTful de Usuários, Autenticação e Gestão de Contas (/usuario)
    │   ├── animal_controller.py      # Endpoints RESTful de Animais (/animal)
    │   ├── especie_controller.py     # Endpoints RESTful de Espécies (/especie)
    │   ├── amostra_controller.py     # Endpoints RESTful de Amostras (/amostra)
    │   ├── exame_controller.py       # Endpoints RESTful de Exames (/exame)
    │   ├── reagente_controller.py    # Endpoints RESTful de Lotes de Reagentes (/reagente)
    │   └── estoque_reagente_controller.py # Endpoints de Estoque Consolidado (/estoque)
    ├── data/                         # Conexão de banco de dados e dados de referência estáticos
    │   ├── connection.py             # DatabaseManager e pool de conexão com o MongoDB
    │   └── especies_catalogo.csv     # Catálogo taxonômico padrão de espécies
    ├── models/                       # Modelos Pydantic v2 e DTOs (Diretriz de Entidade Pura e Imutabilidade de _id)
    │   ├── Animal/                   # Entidade, DTOs (Create, Update, Details) e Enums (Sexo, FaixaEtaria, Orgao, RegimeVida, Funcao, StatusVital, UnidadePeso, UnidadeIdade)
    │   ├── Especie/                  # Entidade, DTOs (Create, Update, Details) e Enum Classe
    │   ├── Amostra/                  # Entidade, DTOs (Create, Update, Details) e Enums
    │   ├── Exame/                    # Entidade, DTOs (Create, Update, Details) e Enums
    │   ├── Reagente/                 # Entidade Reagente (lotes), DTOs (Create, Update, Details) e Enums
    │   ├── EstoqueReagente/          # Modelo Agregado EstoqueReagente e DTOs (Create, Update, Details)
    │   └── Usuario/                  # Entidade Usuario, DTOs (Create, Update, Details, TrocaSenha, PerfilUpdate, StatusUpdate) e Enums (Perfil, StatusUsuario)
    ├── repositories/                 # Repositórios de dados modo dual (MongoDB + índices em memória DAO O(1))
    │   ├── __init__.py               # Exportador centralizado de todos os repositórios e instâncias singleton
    │   ├── usuario_repository.py     # Repositório de Usuários
    │   ├── animal_repository.py      # Repositório de Animais
    │   ├── especie_repository.py     # Repositório de Espécies
    │   ├── amostra_repository.py     # Repositório de Amostras
    │   ├── exame_repository.py       # Repositório de Exames Laboratoriais
    │   ├── reagente_repository.py    # Repositório de Lotes Físicos de Reagentes
    │   └── estoque_reagente_repository.py # Repositório de Estoque Consolidado
    ├── services/                     # Serviços de domínio e regras de negócio
    │   ├── usuario_service.py        # Gestão de contas, solicitação/aprovação, hashing Bcrypt, login e troca de senha
    │   ├── animal_service.py         # Regras de biometria, idade, localidade e ciclo de vida de Animal
    │   ├── especie_service.py        # Resolução taxonômica, reconstrução de schemas e catálogo
    │   ├── amostra_service.py        # Normalização de matriz biológica e integridade com Animal
    │   ├── exame_service.py          # Ciclo de vida de Exames e integridade referencial com Amostras
    │   ├── reagente_service.py       # Validação de lotes, datas de validade e gatilho de estoque
    │   └── estoque_reagente_service.py # Agregação dimensional, conversões de unidade e inventário
    └── utils/                        # Utilitários, persistência, exceções de domínio e formatadores auxiliares
        ├── __init__.py               # Fachada de re-exportação canônica e retrocompatibilidade
        ├── excecoes.py               # Exceções semânticas de domínio (ConfirmacaoNecessariaError -> HTTP 409)
        ├── repositorio.py            # Utilitários de persistência BSON/MongoDB, geração de _id e bloqueio de PK na entrada
        ├── persistencia.py           # Fachada de compatibilidade para utilitários de repositório
        └── normalizacao/             # Pacote modular especializado de normalização
            ├── comum.py              # Tratamento de sentinelas, booleanos tolerantes, datas e Enums
            ├── local.py              # Coordenadas decimais/DMS e composição/decomposição de localidade
            ├── animal.py             # Sanitização de peso, dedução de faixa etária, sexo e status vital
            ├── amostra_exame.py      # Matrizes biológicas, metodologias e resultados de ensaios
            ├── reagente.py           # Conversões de unidade, unicidade de lotes, validade e métricas
            ├── usuario.py            # Normalização de perfis legados, status de conta, matrícula e último acesso
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
| **Pydantic-Settings** | `>=2.0.0` | Carregamento tipado de variáveis de ambiente e arquivos `.env` (`src/config/config.py`). |
| **PyMongo** | `>=4.6.0` | Driver oficial do MongoDB para persistência atômica e upserts idempotentes. |
| **Bcrypt** | `>=4.0.0` | Hashing criptográfico seguro de senhas com geração automática de salt (com fallback SHA-256). |
| **Openpyxl** | `>=3.1.0` | Leitura de alta performance de planilhas Excel estruturadas para o ETL. |
| **Email-Validator** | `>=2.0.0` | Validação formal de formato de e-mail (`EmailStr`). |

---

## 4. Modelos de Domínio e Entidades (Pydantic v2)

Todos os modelos utilizam `ConfigDict(populate_by_name=True)`, permitindo instanciação tanto via atributos padrão do Python quanto via aliases correspondentes aos documentos salvos no MongoDB (ex.: `_id` $\leftrightarrow$ `id`/`animal_id`/`amostra_id`).

- **Diretrizes Globais dos DTOs (`*Create` e `*Update`)**:
  1. **Geração Automática e Imutabilidade de Chave Primária (`id`/`_id`)**: Nenhum DTO de criação (`*Create`) ou atualização (`*Update`) aceita `id` ou `_id` na entrada (`extra="ignore"` + remoção explícita via `_CAMPOS_PROIBIDOS_ENTRADA`). A chave primária sequencial é gerada exclusivamente pelo repositório/banco no momento da criação e permanece estritamente imutável durante todo o ciclo de vida do registro.
  2. **Suporte Uniforme a Atualizações Parciais (`PUT` e `PATCH`)**: Todos os schemas `*Update` declaram seus campos como opcionais (`Optional[...] = None`) e são processados com `model_dump(by_alias=True, exclude_unset=True)`, permitindo atualizar apenas um único campo ou subconjunto de campos sem sobrescrever os demais.

### 4.1. Módulo de Usuário (`Usuario`, DTOs e Enums `Perfil` e `StatusUsuario`)
- **Modelos e DTOs** em `src/models/Usuario/`:
  - `Usuario` ([usuario.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/models/Usuario/usuario.py)): Entidade contendo `id` (alias `_id`), `username` (alias `usuario`), `name` (alias `nome`), `email` (`EmailStr`), `password` (alias `senha`, hash Bcrypt), `created_at`, `last_login`, `perfil` (`Perfil`), `matricula` e `status` (`StatusUsuario`, default `Pendente`).
  - `UsuarioCreate` ([usuario_create.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/models/Usuario/usuario_create.py)): DTO estrito para novos cadastros e solicitações de acesso (`username`, `email`, `password` com mínimo de 6 caracteres, `perfil`, além dos opcionais `name`, `matricula`, `status` e `confirmar_novo_usuario`).
  - `UsuarioUpdate` ([usuario_update.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/models/Usuario/usuario_update.py)): DTO para atualização parcial de dados cadastrais (`username`, `name`, `email`, `password`, `perfil`, `matricula`, `last_login`, `status`).
  - `UsuarioDetails` ([usuario_details.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/models/Usuario/usuario_details.py)): Projeção pública e segura de resposta que **exclui estritamente** credenciais sensíveis (`password`/`senha`) e preenche campos opcionais ausentes com `"Não informado"` (`name`, `matricula`) e `"Nunca"` (`last_login`).
  - `UsuarioTrocaSenha` / `TrocaSenhaRequest` ([usuario_troca_senha.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/models/Usuario/usuario_troca_senha.py)): DTO dedicado para troca autenticada de senha (`senha_atual` / alias `senha_antiga`, `nova_senha` mín. 6 caracteres e `confirmar_nova_senha`).
  - `UsuarioPerfilUpdate` / `AtualizarPerfilRequest` ([usuario_perfil_update.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/models/Usuario/usuario_perfil_update.py)): DTO dedicado para alteração semântica do `perfil` institucional.
  - `UsuarioStatusUpdate` / `AtualizarStatusRequest` ([usuario_status_update.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/models/Usuario/usuario_status_update.py)): DTO dedicado para alteração formal do `status` da conta.
- **Enums de Domínio**:
  - `Perfil` ([Perfil.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/models/Usuario/enums/Perfil.py)): `DOCENTE` (`"docente"`), `POS_GRADUANDO` (`"pos_graduando"`), `BOLSISTA_PIBITI` (`"bolsista_pibiti"`), `BOLSISTA_PIBIC` (`"bolsista_pibic"`), `BOLSISTA_EXTERNO` (`"bolsista_externo"`).
  - `StatusUsuario` ([StatusUsuario.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/models/Usuario/enums/StatusUsuario.py)): `ATIVO` (`"Ativo"`), `INATIVO` (`"Inativo"`), `PENDENTE` (`"Pendente"`), `BLOQUEADO` (`"Bloqueado"`).

### 4.2. Módulo de Espécie (`Especie`, DTOs e Enum `Classe`)
- **Modelos e DTOs** em `src/models/Especie/`:
  - `Especie`: Entidade contendo `id`, `nome_comum`, `nome_cientifico` e `classe`.
  - `EspecieCreate`: DTO com flag `confirmar_nova_especie: bool = False`.
  - `EspecieUpdate`: DTO de atualização parcial com flag `confirmar_atualizacao_especie: bool = False`.
  - `EspecieDetails`: Schema de resposta agregando contagem e lista de animais associados.
- **Enum `Classe`**: `AVES` (`"Ave"`), `MAMIFERO` (`"Mamífero"`), `REPTIL` (`"Réptil"`), `ANFIBIO` (`"Anfíbio"`), `PEIXE` (`"Peixe"`).

### 4.3. Módulo de Animal (`Animal`, DTOs e Enums de Domínio)
- **Modelos e DTOs** em `src/models/Animal/`:
  - `Animal`: Entidade central contendo `id` (alias `_id`), `animal_id`, `classe`, `nome_comum`, `nome_cientifico`, `sexo`, `peso`, `peso_valor`, `peso_unidade`, `faixa_etaria`, `orgao_origem`, `local_origem`, `municipio`, `uf`, `localidade_detalhe`, `regime_vida`, `status_vital`, além dos opcionais `animal_id_projeto`, `microchip`, `funcao`, `idade`, `idade_valor`, `idade_unidade`, `suspeita_clinica` e `animal_observacoes`.
  - `AnimalCreate`: DTO estrito para novos cadastros com suporte a peso e idade estruturados ou textuais, localidade composta ou decomposta e flag `confirmar_nova_especie`.
  - `AnimalUpdate`: DTO para atualização parcial de dados cadastrais (com flag `confirmar_nova_especie`).
  - `AnimalDetails`: Schema enriquecido que substitui campos nulos por `"Não informado"`, aninha o modelo `Especie` e agrega `quantidade_amostras` e a lista `amostras: List[Amostra]`.
- **Enums de Domínio**:
  - `Sexo`: `Macho`, `Fêmea`, `Indeterminado`, `Não informado`.
  - `FaixaEtaria`: `Filhote`, `Juvenil`, `Jovem`, `Sub Adulto`, `Adulto`, `Senil`, `Idoso`, `Potro`, `Ninhego`, `Não informado`.
  - `Orgao`: Órgãos de custódia e origem (`UFPI`, `HVU`, `CCZ`, CETAS, `NAO INFORMADO`, etc.).
  - `RegimeVida`: `Vida livre`, `Cativeiro`, `Domiciliado`, `Não informado`.
  - `Funcao`: `Pet`, `Trabalho`, `Lazer`, `Reprodução`, `Conservação / Zoológico`, `Outro`, `Não aplicável`.
  - `StatusVital`: `Vivo`, `Morto`, `Eutanasiado`, `Não informado`.
  - `UnidadePeso`: `kg`, `g`, `mg`.
  - `UnidadeIdade`: `anos`, `meses`, `semanas`, `dias`.

### 4.4. Módulo de Amostra Biológica (`Amostra`, DTOs e Enums)
- **Modelos e DTOs** em `src/models/Amostra/`:
  - `Amostra`: `id` (alias `_id`), `amostra_id`, `animal_id`, `data_coleta_amostra`, `data_entrega`, `material_biologico`, `status_amostra`, `laudo_liberado`, `local_coleta_amostra`, `nome_coletor`, `condicao_armazenamento`, `fase_amostra`, `destino_amostra`, `kit_utilizado`, `caixa_armazenamento`, frações disponíveis (`dna_disponivel`, `rna_disponivel`, `sequenciamento_disponivel`), latitude, longitude e observações.
  - `AmostraCreate`: DTO estrito de criação com flag de regra de negócio `confirmar_novo_animal` (confirmação genérica de interface pertence ao frontend).
  - `AmostraUpdate`: DTO de atualização parcial com flag de regra de negócio `confirmar_novo_animal`.
  - `AmostraDetails`: Schema com objeto `Animal` agregado e lista/contagem de exames laboratoriais.
- **Enums de Domínio**:
  - `MaterialBiologico`: 29 matrizes biológicas normalizadas (Swabs, Sangue, Órgãos, Tecidos, Fezes, etc.).
  - `CondicaoArmazenamento`: `Temperatura ambiente`, `Refrigerada`, `Congelada`, `Sem identificação`, `Coagulada`, `Hemolisada`, `Nitrogênio líquido`, `Gelo seco`.
  - `FaseAmostra`: `Extração`, `PCR`, `ELETRO`.
  - `DestinoAmostra`: `Biobanco UFPI`, `Biobanco UFPA`, `Fiofruz AM`, `LAB VIGILÂNCIA DE EPIZOOTIAS - UFPI`, etc.
  - `StatusAmostra`: `Disponível`, `Reservada`, `Em uso`, `Perdida`, `Esgotada`.

### 4.5. Exame Laboratorial (`Exame` e Enums)
- **Modelos e DTOs** em `src/models/Exame/`:
  - `Exame`: Entidade contendo `id` (alias `_id`), `exame_id`, `amostra_id`, `tipo_exame` (`TipoExame`), `resultado` (`ResultadoExame`, alias `resultado_detalhado`), `data_realizacao`, `material_biologico`, `teste_laboratorial` (`TesteLaboratorial`), `laboratorio_realizador`, `responsavel_exame`, `kit_utilizado`, `protocolo_exame` e `exame_observacoes`.
  - `ExameCreate`: DTO estrito para novos cadastros com validação de campos obrigatórios e vínculo à amostra.
  - `ExameUpdate`: DTO para atualização parcial de exames laboratoriais.
  - `ExameDetails`: Schema enriquecido para projeção e emissão de laudo laboratorial.
- **Enums de Domínio**:
  - `TesteLaboratorial`: `PCR`, `Sorológico`, `Coproparasitológico`, `Hemoparasito em lâmina`, `Outro`.
  - `TipoExame`: Patógenos e ensaios de vigilância (`Febre do Nilo`, `OrthoFlaviviridae`, `Flavivírus`, `Febre Amarela`, `Mycoplasma`, `Herpesviridae`, `Herpesvírus`, `Trypanosomatidae`, `Resistência Bacteriana`, `Hepatozoon`, `Raiva`, `Chlamydia`, `Sarcocystidae`, `Plasmodium e Haemoproteus`, `AIMES`, `Covid Oral`, `Covid Retal`, `Outro`).
  - `ResultadoExame`: `Positivo`, `Negativo`, `Inconclusivo`, `Aguardando Resultado`, `Não Realizado`.

### 4.6. Reagente e Estoque (`Reagente` e `EstoqueReagente`)
- **Módulo de Lotes Físicos (`src/models/Reagente/`)**:
  - `Reagente`: Entidade representativa de um lote físico de reagente químico ou biológico contendo `id` (alias `_id`), `reagente_codigo` (alias `codigo`), `reagente_nome` (alias `nome`), `numero_lote`, `marca`, `data_validade`, `quantidade_unidade`, `reagente_local_armazenamento` (alias `local_armazenamento`), `status_reagente` (alias `status`, tipo `StatusReagente`), `reagente_id`, `quantidade_volume`, `unidade_medida` (`UnidadeMedida`), `reagente_etapa` (`EtapaReagente`), `reagente_observacoes`, além dos atributos calculados `esta_vencido: Optional[bool]` e `dias_para_vencer: Optional[int]`.
  - `ReagenteCreate`: DTO de cadastro de lote com `status_reagente: StatusReagente = StatusReagente.DISPONIVEL` (alias `status`) e flag `confirmar_novo_reagente: bool = False`.
  - `ReagenteUpdate`: DTO de atualização parcial de lote físico suportando `status_reagente: Optional[StatusReagente] = None` (alias `status`).
  - `ReagenteDetails`: Schema de resposta com projeção de validade em tempo real (`esta_vencido`, `dias_para_vencer`) e `status_reagente: StatusReagente`.
  - **Enums**:
    - `StatusReagente`: Enum canônico estrito com quatro valores: `Disponível` (`DISPONIVEL`), `Vencido` (`VENCIDO`), `Reservado` (`RESERVADO`) e `Esgotado` (`ESGOTADO`). Termos como `"usado"` são normalizados automaticamente para `Esgotado`.
    - `EtapaReagente`: `Extração`, `PCR`, `Eletroforese`, `Sequenciamento`, `Geral`.
    - `UnidadeMedida`: `ml`, `L`, `µl`, `g`, `kg`, `mg`, `un`.
- **Módulo de Estoque Agregado (`src/models/EstoqueReagente/`)**:
  - `EstoqueReagente`: Modelo agregado que consolida todos os lotes de um mesmo reagente, contendo `id`, `reagente_nome`, `reagente_codigo`, `lotes: List[Reagente]`, `quantidade_total_unidades` (soma de frascos), `quantidade_total_volume` (volume/massa total unificado na unidade base), `totais_por_unidade: Dict[str, float]` (segregado por unidade declarada), `totais_convertidos_base: Dict[str, float]` (em `ml` ou `g`) e `resumo_estoque` legível.
  - `EstoqueReagenteCreate`: DTO para criação ou inicialização agregada de estoque.
  - `EstoqueReagenteUpdate`: DTO para edição parcial de metadados agregados.
  - `EstoqueReagenteDetails`: Schema com listagem de lotes físicos enriquecidos com indicadores de vencimento.
  - **Modelos de Alertas de Estoque (`src/models/EstoqueReagente/Alertas/`)**:
    - `ParametrosAlertaEstoque`: Parâmetros de corte utilizados no cálculo (`limite_baixo_estoque: int`, `janela_dias_vencimento: int`).
    - `TotaisAlertasEstoque`: Indicadores agregados do inventário (`total_reagentes_monitorados`, `total_reagentes_com_alerta`, `total_reagentes_baixo_estoque`, `total_reagentes_com_lotes_vencidos`, `total_reagentes_com_lotes_vencendo`, `total_lotes_vencidos`, `total_lotes_vencendo`).
    - `ReagenteAlertaItem`: Representação consolidada de um reagente com alerta, contendo indicadores booleanos (`baixo_estoque_global`, `tem_lotes_vencidos`, `tem_lotes_vencendo`, `tem_alerta`) e as listas segregadas de `lotes_vencidos`, `lotes_proximos_vencimento` e `lotes_regulares`.
    - `EstoqueAlertasResponse`: Schema de resposta HTTP padronizado retornado por `GET /estoque/alertas` e alias `GET /reagente/alertas`.

---

## 5. Camada de Serviços e Regras de Negócio (`src/services/`)

### 5.1. `AnimalService` e Regras de Biometria/Faixa Etária
- **Arquivo**: [src/services/animal_service.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/services/animal_service.py)
- **Funcionalidades**:
  1. **Sanitização e Decomposição de Peso**: Converte strings de gramas/miligramas para kg (`"400g"` $\rightarrow$ `0.4`), vírgula decimal para ponto (`"12,5"` $\rightarrow$ `12.5`), e sentinelas (`"-"`, `"NI"`, `""`) para `"Não aferido"`. Decompõe em `(peso_kg, peso_valor, peso_unidade)` e exige números estritamente positivos ($> 0$).
  2. **Dedução de Faixa Etária e Idade Estruturada**: Decompõe idade em `(idade_fmt, idade_valor, idade_unidade)` e infere faixas a partir de termos qualitativos ou idades temporais (`< 1.0` ano $\rightarrow$ Filhote; `< 2.0` anos $\rightarrow$ Juvenil; `< 4.0` anos $\rightarrow$ Sub Adulto; `< 10.0` anos $\rightarrow$ Adulto; $\ge 10.0$ anos $\rightarrow$ Senil).
  3. **Decomposição de Localidade**: Decompõe e sincroniza `local_origem`, `municipio`, `uf` e `localidade_detalhe`.
  4. **Resolução de Espécie**: Delega validação binomial e consistência taxonômica para `EspecieService` (em atualizações parciais onde apenas `nome_comum` ou `nome_cientifico` é alterado, resolve automaticamente os demais campos pelo catálogo).
  5. **Enriquecimento (`AnimalDetails`)**: Preenche campos ausentes com `"Não informado"` e consolida lista de amostras.

### 5.2. `EspecieService` e Taxonomia Zoológica
- **Arquivo**: [src/services/especie_service.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/services/especie_service.py)
- **Funcionalidades**:
  1. **Formatação Binomial**: Garante convenção de nomenclatura zoológica (primeira letra maiúscula, epíteto em minúsculo).
  2. **Resolução Taxonômica (`resolver_especie`)**:
     - Se informado apenas o nome científico, preenche automaticamente nome comum e classe.
     - Se informado apenas o nome comum, preenche nome científico e classe.
     - Se informados ambos, valida a coerência cadastrada.
     - Se inédita, exige preenchimento total e, caso `confirmar_nova_especie=False`, lança `ConfirmacaoNecessariaError` (`codigo="ESPECIE_NAO_ENCONTRADA"`, mapeada para `HTTP 409 Conflict`).
  3. **Delegação de Ingestão**: O método `importar_tabela_csv` delega a leitura do CSV diretamente para [etl/catalogo.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/etl/catalogo.py).
  4. **Resolução de Schemas Bidirecionais**: Garante `EspecieDetails.model_rebuild(_types_namespace={"Animal": Animal})` e exporta modelos diretamente pelo Service.

### 5.3. `AmostraService` e Normalização de Matrizes
- **Arquivo**: [src/services/amostra_service.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/services/amostra_service.py)
- **Funcionalidades**:
  1. **Normalização de Matrizes Biológicas**: Utiliza `src.utils.normalizacao` para mapeamento por especificidade decrescente (ex: `"swab oral e cloacal"` antes de `"swab oral"`; `"pool de tecidos"` antes de `"tecido"`).
  2. **Integridade com Animal (`_verificar_animal_vinculado`)**: Verifica a existência prévia do animal de origem; caso não exista e `confirmar_novo_animal=False`, lança `ConfirmacaoNecessariaError` (`codigo="ANIMAL_NAO_ENCONTRADO"`, mapeada para `HTTP 409 Conflict`).
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
     - Valida `quantidade_unidade >= 1` e `quantidade_volume > 0` (em atualizações parciais, preserva a quantidade e unidade existentes caso não sejam reenviadas).
  2. **Regras Estritas de Ciclo de Vida e Transição de `StatusReagente`**:
     - **Status Canônicos Permitidos**: Apenas `Disponível`, `Vencido`, `Reservado` e `Esgotado`.
     - **Atualização Automática para Vencido**: Lotes cuja data de validade expirou (`data_validade < date.today()`) recebem automaticamente o status `StatusReagente.VENCIDO` em consultas e operações.
     - **Exceção de Lote Esgotado**: Se o lote estiver com status `Esgotado`, ele **NÃO vira `Vencido`** automaticamente mesmo após expirar a data de validade.
     - **Bloqueio de Vencimento Prematuro**: O usuário não pode definir manualmente o status como `Vencido` para um lote cuja validade ainda não expirou (`data_validade >= date.today()`). Qualquer tentativa lança `ValueError`.
     - **Imutabilidade Cruzada Esgotado $\leftrightarrow$ Vencido**:
       - Um lote com status `Vencido` não pode ser alterado para `Esgotado` (`ValueError: Reagente com status Vencido não pode ser alterado para Esgotado.`).
       - Um lote com status `Esgotado` não pode ser alterado para `Vencido` (`ValueError: Reagente com status Esgotado não pode ser alterado para Vencido.`).
     - **Normalização de Sinônimos**: Termos como `"usado"` enviados nos payloads são normalizados automaticamente para `Esgotado`.
     - **Baixo Estoque**: Não é utilizado como status de lote físico; é monitorado na visão agregada de estoque consolidado.
  3. **Cálculos Temporais de Validade**:
     - Computa dinamicamente `esta_vencido` (`data_validade < date.today()`) e `dias_para_vencer` (`(data_validade - date.today()).days`).
  4. **Consolidação Dimensional de Estoque (`calcular_metricas_estoque`)**:
     - Agrupa lotes pelo nome normalizado do reagente.
     - Converte unidades compatíveis para as bases padrão laboratoriais (`ml` para volume líquido, `g` para massa sólida).
     - Gera dicionários estruturados `totais_por_unidade` e `totais_convertidos_base`.
  5. **Serviço de Alertas de Estoque Consolidado (`obter_alertas_estoque`)**:
     - Consolida reagentes com baixo estoque global ($\le 2$ unidades por padrão), lotes vencidos e lotes a vencer nos próximos 30 dias.
     - Ordena os lotes cronologicamente em conformidade com a diretriz laboratorial PEPS/FIFO.
  6. **Sincronização Automática Bidirecional**:
     - A criação, edição ou exclusão de um lote físico em `ReagenteService` dispara automaticamente a sincronização e atualização de `EstoqueReagente`.
     - `EstoqueReagenteService` disponibiliza rotinas de recálculo global de todo o inventário (`recalcular_todo_estoque`).

### 5.7. `UsuarioService`, Autenticação, Ciclo de Vida de Contas e Segurança (Bcrypt)
- **Arquivo**: [src/services/usuario_service.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/services/usuario_service.py)
- **Funcionalidades e Regras de Negócio**:
  1. **Hashing Criptográfico de Senhas (`hash_password` e `verificar_senha`)**:
     - Utiliza `bcrypt` com geração automática de salt (`bcrypt.gensalt()`) antes de persistir qualquer senha no banco, contando com fallback transparente para `SHA-256` caso a biblioteca `bcrypt` não esteja instalada no ambiente.
     - Exige comprimento mínimo de 6 caracteres em cadastros, atualizações e trocas de senha.
  2. **Solicitação de Cadastro e Fluxo de Aprovação**:
     - `solicitar_cadastro` e `criar_usuario` inicializam contas com `status = StatusUsuario.PENDENTE` por padrão, `created_at = datetime.now()` e `last_login = None`.
     - `listar_solicitacoes_pendentes` retorna todas as contas que aguardam homologação por um docente ou administrador.
     - `aprovar_usuario` promove a conta para `StatusUsuario.ATIVO`, liberando imediatamente a autenticação; `inativar_usuario` e `alterar_status_usuario` gerenciam transições para `Inativo`, `Pendente` ou `Bloqueado`.
  3. **Autenticação Estrita e Auditoria de Acesso (`autenticar_usuario`)**:
     - Aceita identificação tanto por `username` quanto por `email`.
     - Bloqueia o login com `PermissionError` (`HTTP 403 Forbidden`) e mensagem contextualizada caso a conta esteja `Pendente`, `Inativo` ou `Bloqueado`.
     - Registra atomicamente o timestamp `last_login` no momento da autenticação bem-sucedida.
  4. **Troca de Senha Autenticada (`trocar_senha`)**:
     - Exige e valida a `senha_atual` contra o hash armazenado (lançando `PermissionError` -> `HTTP 403` se incorreta).
     - Valida `confirmar_nova_senha` (se enviada) e impede que a `nova_senha` seja idêntica à senha atual (`ValueError` -> `HTTP 400`).
  5. **Projeção Pública Segura (`preencher_nao_informados` / `UsuarioDetails`)**:
     - Remove qualquer atributo `password`/`senha` antes de construir a resposta e substitui campos ausentes por `"Não informado"` (`name`, `matricula`) e `"Nunca"` (`last_login`).

---

## 6. Módulo de Utilitários e Normalização de Domínio (`src/utils/`)

O módulo `src/utils/` reúne o pacote modular especializado `src/utils/normalizacao/`, os utilitários de persistência/repositório (`src/utils/repositorio.py` e `src/utils/persistencia.py`) e as exceções semânticas de domínio (`src/utils/excecoes.py`).

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
  5. **`reagente.py`** — Dimensionalidade, Regras de Status e Métricas de Estoque:
     - `FATORES_CONVERSAO`: Tabela de conversão volumétrica (`l`, `ml`, `ul`) e mássica (`kg`, `g`, `mg`).
     - `normalizar_unidade_medida(val)` e `normalizar_etapa_reagente(val)`: Padronização de unidades e etapas.
     - `normalizar_status_reagente(val)`: Converte variações textuais para o Enum canônico `StatusReagente` (`Disponível`, `Vencido`, `Reservado`, `Esgotado`), mapeando automaticamente `"usado"` e variações para `StatusReagente.ESGOTADO`.
     - `calcular_vencimento(data_validade, data_referencia=None)`: Retorna tupla `(esta_vencido, dias_para_vencer)` aceitando data de referência para auditoria e testes.
     - `classificar_lotes_alertas(lotes, janela_dias, data_referencia=None)`: Segrega lotes físicos em `(lotes_vencidos, lotes_proximos_vencimento, lotes_regulares)`, ordenando os lotes a vencer cronologicamente (regra laboratorial PEPS/FIFO).
     - `processar_alerta_reagente(lotes, limite_baixo_estoque, janela_dias, nome_reagente, reagente_codigo, data_referencia=None)`: Consolida indicadores de alerta agregados (`baixo_estoque_global`, `tem_lotes_vencidos`, `tem_lotes_vencendo`, `tem_alerta`).
     - `calcular_metricas_estoque(lotes)`: Agrega volumes, calcula conversões de base e gera resumo de estoque.
     - `validar_lotes_unicos(lotes)`: Garante integridade e unicidade de lote por fabricante.
  6. **`usuario.py`** — Perfis Institucionais, Status de Conta e Credenciais:
     - `normalizar_perfil(perfil)`: Remove acentuação e mapeia termos legados/sinônimos (`"professor"`, `"mestrando"`, `"doutorando"`, `"pibit"`, `"pibic"`, `"externo"`, etc.) para o Enum canônico `Perfil`.
     - `normalizar_status_usuario(status)`: Converte strings em português/inglês (`"ativo"`, `"active"`, `"pendente"`, `"aguardando"`, `"inativo"`, `"bloqueado"`) para `StatusUsuario`.
     - `normalizar_matricula(matricula)`: Preserva zeros à esquerda como texto limpo e converte sentinelas (`"-"`, `"NI"`, `"None"`) para `None`.
     - `normalizar_last_login(last_login)`: Converte `"Nunca"` e sentinelas para `None` e realiza parsing resiliente de datas/horas ISO e brasileiras (`DD/MM/AAAA HH:MM:SS`).
     - `normalizar_chaves_usuario(payload)`: Converte aliases de entrada (`usuario` $\rightarrow$ `username`, `nome` $\rightarrow$ `name`, `senha` $\rightarrow$ `password`).
  7. **`__init__.py`** — Fachada Canônica:
     - Re-exporta todos os símbolos do ecossistema de normalização para importação centralizada (`from src.utils.normalizacao import ...`), garantindo retrocompatibilidade total.

### 6.2. Utilitários de Persistência/Repositório e Exceções de Domínio (`repositorio.py`, `persistencia.py`, `excecoes.py`)
- **`src/utils/repositorio.py` (e fachada `src/utils/persistencia.py`)**:
  - `_CAMPOS_PROIBIDOS_ENTRADA = ("id", "_id")`: Constante compartilhada por todos os Services para remover chaves primárias enviadas nos payloads de entrada.
  - `normalizar_chave_busca(texto)` / `_normalizar`: Padroniza strings (`strip` + `casefold`) para indexação e busca textual $O(1)$ em memória.
  - `extrair_id_numerico(id_val)` e `sanitizar_id_filtro(id_val)`: Convertem identificadores compostos por dígitos para `int`, mantendo compatibilidade entre rotas HTTP e chaves `_id` numéricas no MongoDB.
  - `gerar_proximo_id_mongo(collection, proximo_id_atual)`: Calcula a próxima chave primária sequencial (`max(_id) + 1`) sincronizada entre a coleção MongoDB e o ponteiro em memória.
  - `doc_para_mongo(model)` e `preparar_doc_mongo(doc, fallback_id_campo)`: Garantem serialização BSON-safe (`model_dump(mode="json", by_alias=True, exclude_none=True)`) e desserialização segura de documentos do MongoDB para modelos Pydantic.
- **`src/utils/excecoes.py`**:
  - `ConfirmacaoNecessariaError(ValueError)`: Exceção semântica de domínio lançada quando uma operação é válida mas requer confirmação explícita de regra de negócio pelo usuário. Transporta `codigo`, `mensagem`, `confirmacao` e `contexto`, sendo convertida automaticamente pelo `response_controller.py` em `HTTP 409 Conflict`.

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

### 8.1. Padrão DAO, Modo Dual e Persistência no MongoDB
Os repositórios (`backend/src/repositories/`) implementam o padrão DAO (*Data Access Object*) com arquitetura de **modo dual de operação**:
1. **Modo MongoDB Ativo (Produção / API)**: Conecta-se ao MongoDB (`pibit_app_dev` ou `pibit_app` via pool `DatabaseManager` em `src/data/connection.py`). Todas as operações de escrita (`create`, `update`, `delete`) realizam I/O atômico no banco e sincronizam os caches internos.
2. **Modo Isolado em Memória (Testes Unitários de Services)**: Repositórios instanciados sem `db` ou com `use_mongo=False` operam estritamente em memória com indexação $O(1)$, garantindo isolamento total, velocidade extrema e evitando poluição da base real de pesquisa.
3. **Geração Automática e Imutabilidade de Chave Primária (`_id`)**: Todos os repositórios geram `id`/`_id` automaticamente em `create()` via `gerar_proximo_id_mongo` (`max(_id) + 1`), descartando qualquer valor pré-existente enviado pelo cliente, e preservam o `_id` original como imutável em `update()`.
4. **Serialização BSON-Safe**: Para contornar a incompatibilidade nativa do PyMongo com tipos `datetime.date`, todos os modelos são serializados através de `doc_para_mongo` (`model_dump(mode="json", by_alias=True, exclude_none=True)`) antes de serem gravados nas coleções.
5. **Tratamento de Tipos de Chave Primária**: As operações que aceitam identificadores numéricos ou strings de rotas HTTP convertem dinamicamente identificadores compostos por dígitos para `int` (`sanitizar_id_filtro`), garantindo que queries `{"_id": id}` correspondam com precisão ao tipo BSON armazenado no MongoDB.

### 8.2. Gerenciador de Conexão e Configuração (`src/data/connection.py` e `src/config/`)
- **`Settings` / `settings` (`src/config/config.py`)**: Carrega variáveis do arquivo `.env` via `pydantic-settings` (`MONGODB_URI`, `DATABASE_NAME`, `FASTAPI_HOST`, `FASTAPI_PORT`).
- **`DatabaseManager` (`src/data/connection.py`)**: Gerencia o ciclo de vida do `MongoClient` através de `get_client()`, `get_database()` e `close_connection()`, com suporte a timeouts configuráveis e pool persistente integrado ao `lifespan` do FastAPI em [src/main.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/main.py).

### 8.3. Matriz de Repositórios e Coleções MongoDB

| Repositório | Coleção MongoDB | Arquivo | Chaves e Índices | Principais Métodos |
| :--- | :--- | :--- | :--- | :--- |
| **`EspecieRepository`** | `especies` | [especie_repository.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/repositories/especie_repository.py) | `_id` (int), `nome` (str), `nome_cientifico` (str), `classe` | `create`, `save`, `update`, `delete`, `buscar_por_id`, `buscar_por_nome_comum`, `buscar_por_nome_cientifico`, `buscar_por_classe`, `listar`, `count`, `exists`, `clear` |
| **`AnimalRepository`** | `animais` | [animal_repository.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/repositories/animal_repository.py) | `animal_id` (str), `_id` (int), `animal_id_projeto`, `microchip`, `classe`, `sexo`, `faixa_etaria`, `orgao_origem`, `status_vital` | `create`, `save`, `update`, `delete`, `buscar_por_animal_id`, `buscar_por_id`, `buscar_por_especie`, `listar`, `count`, `exists`, `clear` |
| **`AmostraRepository`** | `amostras` | [amostra_repository.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/repositories/amostra_repository.py) | `amostra_id` (str), `_id` (int), `animal_id`, `material_biologico`, `status_amostra`, `fase_amostra`, `destino_amostra` | `create`, `save`, `update`, `delete`, `buscar_por_amostra_id`, `buscar_por_id`, `buscar_por_animal_id`, `listar`, `count`, `exists`, `clear` |
| **`ExameRepository`** | `exames` | [exame_repository.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/repositories/exame_repository.py) | `exame_id` (str), `_id` (int), `amostra_id`, `tipo_exame`, `resultado`, `teste_laboratorial`, `responsavel_exame` | `create`, `save`, `update`, `delete`, `buscar_por_id`, `buscar_por_exame_id`, `buscar_por_amostra_id`, `listar`, `count`, `exists`, `clear` |
| **`ReagenteRepository`** | `reagentes` | [reagente_repository.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/repositories/reagente_repository.py) | `reagente_id` (str), `_id` (int), `reagente_codigo`, `reagente_nome`, `numero_lote`, `marca`, `local_armazenamento` | `create`, `save`, `update`, `delete`, `buscar_por_id`, `buscar_por_codigo`, `buscar_por_nome`, `buscar_por_lote`, `listar`, `count`, `exists`, `clear` |
| **`EstoqueReagenteRepository`** | `estoque_reagentes` | [estoque_reagente_repository.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/repositories/estoque_reagente_repository.py) | `_id` (int), `reagente_nome` (str), `reagente_codigo` | `create`, `save`, `update`, `delete`, `buscar_por_id`, `buscar_por_nome`, `buscar_por_codigo`, `listar`, `count`, `exists`, `clear` |
| **`UsuarioRepository`** | `usuarios` | [usuario_repository.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/repositories/usuario_repository.py) | `_id` (int), `username` (str), `email` (str), `matricula` (str), `perfil`, `status` | `create`, `save`, `update`, `delete`, `buscar_por_id`, `buscar_por_username`, `buscar_por_email`, `buscar_por_matricula`, `buscar_por_perfil`, `buscar_por_status`, `listar_pendentes`, `listar`, `count`, `exists`, `clear` |

---

## 9. API HTTP (FastAPI) e Controladores (`src/controllers/`)

### 9.1. Centralização de Respostas HTTP e Tratamento de Erros (`response_controller.py`)
Para evitar a replicação exaustiva de blocos `try/except` em cada endpoint e padronizar os contratos de resposta e documentação OpenAPI/Swagger em toda a API, o backend centraliza a infraestrutura de respostas e exceções em [response_controller.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/controllers/response_controller.py):

#### 1. Mapeamento Canônico de Exceções (`EXCECOES_HTTP`)
A camada de serviços opera lançando exceções semânticas de domínio/Python padrão, que são interceptadas e convertidas de forma transparente para os status codes HTTP correspondentes:
- `NoContentError` / `SemConteudoError` $\rightarrow$ `HTTP 204 No Content` (sem corpo de resposta).
- `ConfirmacaoNecessariaError` $\rightarrow$ `HTTP 409 Conflict` (operação válida, porém dependente de confirmação explícita do usuário; retorna payload estruturado com `codigo`, `mensagem`, `confirmacao` e `contexto`).
- `ValueError` $\rightarrow$ `HTTP 400 Bad Request` (regras de negócio violadas ou IDs duplicados).
- `PermissionError` $\rightarrow$ `HTTP 403 Forbidden` (ações não permitidas pelo perfil, credenciais inválidas ou contas pendentes/inativas/bloqueadas).
- `KeyError` / `FileNotFoundError` $\rightarrow$ `HTTP 404 Not Found` (recursos ou arquivos não localizados; a mensagem é extraída diretamente de `args[0]` para evitar aspas extras de formatação).

#### 2. Contrato de Respostas: Códigos de Status HTTP e Mensagens
O protocolo HTTP opera em duas camadas complementares (código de status e corpo da mensagem):
- **Código de Status HTTP (Sempre Presente)**: Toda resposta da API transporta o código de status na linha de status do protocolo (ex.: `200 OK`, `201 Created`, `204 No Content`, `400 Bad Request`, `403 Forbidden`, `404 Not Found`, `409 Conflict`, `500 Internal Server Error`), permitindo que clientes (como Axios, Fetch API ou aplicações mobile) decidam o fluxo antes mesmo de inspecionar o payload.
- **Respostas de Sucesso com Dados (`200 OK` e `201 Created`)**: Retornam diretamente a entidade pura serializada ou a lista/modelo de detalhes (ex.: `Animal`, `Amostra`, `Exame`, `EspecieDetails`, `UsuarioDetails`), mantendo máxima fidelidade ao contrato de dados tipado pelo Pydantic, sem embrulhos redundantes.
- **Respostas de Sucesso sem Dados (`204 No Content`)**: Aplicadas primariamente a rotas de exclusão (`DELETE`), retornam cabeçalhos HTTP com corpo estritamente vazio (`b""`).
- **Respostas de Confirmação de Regra de Negócio (`409 Conflict`)**: Retornam o schema `ErroConfirmacaoResposta` (`DetalheConfirmacao`) permitindo ao frontend identificar o caso por `detail.codigo` e reenviar com o parâmetro indicado em `detail.confirmacao`:
  ```json
  {
    "detail": {
      "codigo": "ESPECIE_NAO_ENCONTRADA",
      "mensagem": "A espécie 'Animal Inédito' (Alienigena ficticius) não está no catálogo...",
      "confirmacao": "confirmar_nova_especie",
      "contexto": {
        "nome_comum": "Animal Inédito",
        "nome_cientifico": "Alienigena ficticius",
        "classe": "Mamífero"
      }
    }
  }
  ```
- **Respostas de Erro (`400`, `403`, `404`, `500`)**: Retornam o schema padrão `ErroResposta` serializado em JSON com o detalhamento legível da falha:
  ```json
  {
    "detail": "Animal com identificador 'ANI_999' não encontrado."
  }
  ```

#### 3. Catálogo de Respostas HTTP e Documentação OpenAPI (`RESPOSTAS`)
O módulo define o catálogo mestre `RESPOSTAS` com esquemas, exemplos e descrições técnicas, além da função utilitária `respostas(*codigos)` (que sempre anexa a documentação de `500 Internal Server Error`).

A partir dele, são exportados conjuntos prontos utilizados no parâmetro `responses=` de cada rota para enriquecimento da documentação interativa (`/docs` e `/redoc`):
- `RESPOSTAS_CRIAR`: `HTTP 201 Created`, `400 Bad Request`, `403 Forbidden`, `404 Not Found`, `409 Conflict`, `500 Internal Server Error`.
- `RESPOSTAS_LISTAR`: `HTTP 200 OK`, `400 Bad Request`, `500 Internal Server Error`.
- `RESPOSTAS_BUSCAR`: `HTTP 200 OK`, `400 Bad Request`, `404 Not Found`, `500 Internal Server Error`.
- `RESPOSTAS_OBTER`: `HTTP 200 OK`, `404 Not Found`, `500 Internal Server Error`.
- `RESPOSTAS_ATUALIZAR`: `HTTP 200 OK`, `400 Bad Request`, `403 Forbidden`, `404 Not Found`, `409 Conflict`, `500 Internal Server Error`.
- `RESPOSTAS_DELETAR`: `HTTP 204 No Content`, `403 Forbidden`, `404 Not Found`, `500 Internal Server Error`.
- `RESPOSTAS_CONTAGEM`: `HTTP 200 OK`, `500 Internal Server Error`.
- `RESPOSTAS_PROCESSAMENTO`: `HTTP 200 OK`, `400 Bad Request`, `404 Not Found`, `500 Internal Server Error`.

#### 4. Infraestrutura de Roteamento e Interceptação
- **`TratamentoErrosRoute(APIRoute)`**: Rota customizada do FastAPI que executa o endpoint, captura as exceções mapeadas e aplica o retorno HTTP apropriado. Configura e força automaticamente endpoints `DELETE` para `HTTP 204 No Content` sem corpo de resposta.
- **Fábrica `criar_router(**kwargs) -> APIRouter`**: Instancia routers já vinculados a `TratamentoErrosRoute`. Utilizada por todos os controllers do ecossistema.
- **Decorador `tratar_erros`**: Decorador universal (síncrono/assíncrono) para funções avulsas.
- **Manipulador Global `registrar_tratamento_erros(app)`**: Registrado em [src/main.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/main.py) como rede de segurança ASGI global para exceções não tratadas.

#### 5. Diretriz de Desacoplamento Estrito
Os controladores **não acessam repositórios nem modelos de persistência diretamente**. Todas as chamadas são delegadas aos seus respectivos Services (`usuario_service`, `animal_service`, `especie_service`, `amostra_service`, `exame_service`, `reagente_service`, `estoque_reagente_service`), que re-exportam entidades, DTOs e tipos necessários.

### 9.2. Endpoints de Animais (`/animal`)
- `POST /animal/`: Cadastro de novo animal com resolução taxonômica e biometria automatizadas (`confirmar_nova_especie: bool`) (Status 201 Created / 409 Conflict; `responses=RESPOSTAS_CRIAR`).
- `GET /animal/`: Listagem filtrada por `classe`, `sexo`, `status` (regime de vida), `status_vital`, busca textual (`termo_busca`) e paginação (`skip`, `limit`) (Status 200; `responses=RESPOSTAS_LISTAR`).
- `GET /animal/{animal_id}`: Consulta individual por ID único do laboratório (Status 200 / 404; `responses=RESPOSTAS_OBTER`).
- `GET /animal/{animal_id}/detalhes`: Consulta detalhada `AnimalDetails` com espécie e amostras colhidas (Status 200 / 404; `responses=RESPOSTAS_OBTER`).
- `PUT /animal/{animal_id}` e `PATCH /animal/{animal_id}`: Atualização parcial ou completa de animal existente com validação taxonômica (`confirmar_nova_especie: bool`) (Status 200 / 400 / 404 / 409; `responses=RESPOSTAS_ATUALIZAR`).
- `DELETE /animal/{animal_id}`: Exclusão de animal cadastrado (bloqueia se houver amostras vinculadas) (Status 204 No Content; `responses=RESPOSTAS_DELETAR`).

### 9.3. Endpoints de Espécies (`/especie`)
- `POST /especie/cadastro`: Cadastro de nova espécie taxonômica com validação binomial (Status 201 Created; `responses=RESPOSTAS_CRIAR`).
- `GET /especie/`: Listagem filtrada por `nome_comum`, `nome_cientifico` e `classe` (Status 200; `responses=RESPOSTAS_BUSCAR`).
- `GET /especie/{id}`: Detalhes taxonômicos acompanhados da lista e contagem de animais associados via `EspecieDetails` (Status 200 / 404; `responses=RESPOSTAS_OBTER`).
- `PUT /especie/{id}` e `PATCH /especie/{id}`: Atualização parcial ou completa de espécie com checagem de duplicidade taxonômica (Status 200 / 400 / 404; `responses=RESPOSTAS_ATUALIZAR`).
- `DELETE /especie/{id}`: Exclusão de espécie (Status 204 No Content; `responses=RESPOSTAS_DELETAR`).
- `POST /especie/importar-catalogo`: Importação em lote de tabela CSV para o catálogo de espécies (Status 200 / 400 / 404; `responses=RESPOSTAS_PROCESSAMENTO`).

### 9.4. Endpoints de Amostras (`/amostra`)
- `POST /amostra/`: Cadastro de nova amostra biológica com validação de animal vinculado (`confirmar_novo_animal`) (Status 201 Created / 409 Conflict; `responses=RESPOSTAS_CRIAR`).
- `GET /amostra/`: Listagem com filtros múltiplos (`animal_id`, `status_amostra`, `fase_amostra`, `condicao_armazenamento`, `destino_amostra`, `material_biologico`), busca textual e paginação (Status 200; `responses=RESPOSTAS_LISTAR`).
- `GET /amostra/contagem`: Quantidade total de amostras no acervo (Status 200; `responses=RESPOSTAS_CONTAGEM`).
- `GET /amostra/animal/{animal_id}`: Todas as amostras colhidas de um determinado animal (Status 200; `responses=RESPOSTAS_LISTAR`).
- `GET /amostra/{amostra_id}`: Consulta individual por ID laboratorial (Status 200 / 404; `responses=RESPOSTAS_OBTER`).
- `GET /amostra/{amostra_id}/detalhes`: Detalhes completos `AmostraDetails` com entidade `Animal` e exames diagnósticos (Status 200 / 404; `responses=RESPOSTAS_OBTER`).
- `PUT /amostra/{amostra_id}` e `PATCH /amostra/{amostra_id}`: Atualização parcial ou completa de campos com re-normalização de matriz (Status 200 / 400 / 404 / 409; `responses=RESPOSTAS_ATUALIZAR`).
- `DELETE /amostra/{amostra_id}`: Exclusão de amostra (bloqueia se houver exames vinculados) (Status 204 No Content; `responses=RESPOSTAS_DELETAR`).

### 9.5. Endpoints de Exames (`/exame`)
- `POST /exame/`: Cadastrar novo exame laboratorial com validação de vínculo com a amostra (`confirmar_novo_exame`, `confirmar_nova_amostra`) (Status 201 Created; `responses=RESPOSTAS_CRIAR`).
- `GET /exame/`: Listagem com filtros cruzados por `amostra_id`, `tipo_exame`, `resultado`, `teste_laboratorial`, `data_realizacao`, `responsavel_exame`, busca textual e paginação (Status 200; `responses=RESPOSTAS_LISTAR`).
- `GET /exame/contagem`: Quantidade total de exames laboratoriais registrados (Status 200; `responses=RESPOSTAS_CONTAGEM`).
- `GET /exame/amostra/{amostra_id}`: Todos os exames laboratoriais realizados para uma amostra específica (Status 200; `responses=RESPOSTAS_LISTAR`).
- `GET /exame/{identificador}`: Recuperar exame por ID numérico ou código alfanumérico (Status 200 / 404; `responses=RESPOSTAS_OBTER`).
- `GET /exame/{identificador}/detalhes`: Consulta de laudo detalhado `ExameDetails` com saneamento de valores (Status 200 / 404; `responses=RESPOSTAS_OBTER`).
- `PUT /exame/{identificador}` e `PATCH /exame/{identificador}`: Atualização parcial ou completa de exame com integridade da amostra (Status 200 / 400 / 404; `responses=RESPOSTAS_ATUALIZAR`).
- `DELETE /exame/{identificador}`: Remoção de exame laboratorial (Status 204 No Content; `responses=RESPOSTAS_DELETAR`).

### 9.6. Endpoints de Reagentes (`/reagente`)
- `POST /reagente/`: Cadastrar novo lote físico de reagente com validação de unicidade, cálculo de validade e gatilho de sincronização de estoque (`confirmar_novo_reagente: bool`) (Status 201 Created; `responses=RESPOSTAS_CRIAR`).
- `GET /reagente/`: Listagem de lotes físicos com filtros por `nome`, `codigo`, `marca`, `local_armazenamento`, `status` (`StatusReagente`: `Disponível`, `Vencido`, `Reservado`, `Esgotado`), `apenas_vencidos`, busca textual, ordenação e paginação (Status 200; `responses=RESPOSTAS_LISTAR`).
- `GET /reagente/contagem`: Total de lotes físicos cadastrados no laboratório (Status 200; `responses=RESPOSTAS_CONTAGEM`).
- `GET /reagente/lote/{numero_lote}`: Listar todos os registros vinculados a um número de lote (Status 200; `responses=RESPOSTAS_LISTAR`).
- `GET /reagente/alertas`: Obter alertas consolidados de reagentes (alias para `GET /estoque/alertas`) calculando baixo estoque global e lotes a vencer por PEPS/FIFO (Status 200; `responses=RESPOSTAS_OBTER`).
- `GET /reagente/{identificador}`: Obter lote por ID numérico ou identificador `REA_XXXX` (Status 200 / 404; `responses=RESPOSTAS_OBTER`).
- `GET /reagente/{identificador}/detalhes`: Obter `ReagenteDetails` enriquecido com indicadores de validade (`esta_vencido`, `dias_para_vencer`) (Status 200 / 404; `responses=RESPOSTAS_OBTER`).
- `PUT /reagente/{identificador}` e `PATCH /reagente/{identificador}`: Atualizar parcial ou completamente dados do lote físico e recalcular estoque consolidado (Status 200 / 400 / 404; `responses=RESPOSTAS_ATUALIZAR`).
- `DELETE /reagente/{identificador}`: Remover lote físico e sincronizar estoque (Status 204 No Content; `responses=RESPOSTAS_DELETAR`).

### 9.7. Endpoints de Estoque Consolidado (`/estoque`)
- `POST /estoque/`: Cadastrar nova visão consolidada de estoque (`confirmar_novo_estoque: bool`) (Status 201 Created; `responses=RESPOSTAS_CRIAR`).
- `GET /estoque/`: Listar estoques agregados com busca textual, filtro `apenas_com_lotes`, ordenação e paginação (Status 200; `responses=RESPOSTAS_LISTAR`).
- `GET /estoque/contagem`: Quantidade total de reagentes unificados em estoque (Status 200; `responses=RESPOSTAS_CONTAGEM`).
- `POST /estoque/recalcular`: Varredura completa e recálculo de todo o inventário a partir dos lotes atuais (Status 200; `responses=RESPOSTAS_CONTAGEM`).
- `POST /estoque/sincronizar/{nome_reagente}`: Recálculo imediato de estoque para um reagente específico (Status 200 / 404; `responses=RESPOSTAS_OBTER`).
- `GET /estoque/alertas`: Endpoint dedicado de monitoramento proativo de alertas do inventário, retornando `EstoqueAlertasResponse` estruturado com parâmetros de corte (`limite_baixo_estoque`, `dias_vencimento`), contadores agregados (`TotaisAlertasEstoque`) e lista consolidada de reagentes com baixo estoque global ($\le 2$ unidades), lotes vencidos e lotes a expirar nos próximos 30 dias ordenados por PEPS/FIFO (Status 200; `responses=RESPOSTAS_OBTER`).
- `GET /estoque/codigo/{codigo}`: Buscar estoque pelo código do reagente (Status 200; `responses=RESPOSTAS_LISTAR`).
- `GET /estoque/{identificador}`: Obter visão agregada por ID numérico ou nome do reagente (`sincronizar: bool`) (Status 200 / 404; `responses=RESPOSTAS_OBTER`).
- `GET /estoque/{identificador}/detalhes`: Obter `EstoqueReagenteDetails` com listagem e indicadores de todos os lotes vinculados (Status 200 / 404; `responses=RESPOSTAS_OBTER`).
- `PUT /estoque/{identificador}` e `PATCH /estoque/{identificador}`: Atualizar parcial ou completamente metadados agregados do estoque (Status 200 / 400 / 404; `responses=RESPOSTAS_ATUALIZAR`).
- `DELETE /estoque/{identificador}`: Remover registro de estoque com opção de deleção em cascata dos lotes físicos (`deletar_lotes_vinculados: bool`) (Status 204 No Content; `responses=RESPOSTAS_DELETAR`).

### 9.8. Endpoints de Usuários e Gestão de Contas (`/usuario`)
- `POST /usuario/`: Cadastrar novo usuário com validação de unicidade, hashing Bcrypt de senha e status default `Pendente` (Status 201 Created; `responses=RESPOSTAS_CRIAR`).
- `POST /usuario/solicitar-cadastro`: Solicitação pública de cadastro com status inicial `Pendente` aguardando homologação por docente ou administrador (Status 201 Created; `responses=RESPOSTAS_CRIAR`).
- `GET /usuario/`: Listar usuários com filtros combinados por `perfil`, `status` (`Ativo`, `Pendente`, `Inativo`, `Bloqueado`), busca textual (`termo_busca`) e paginação (`skip`, `limit`) (Status 200; `responses=RESPOSTAS_LISTAR`).
- `GET /usuario/pendentes`: Listar solicitações de cadastro com status `Pendente` para avaliação administrativa (Status 200; `responses=RESPOSTAS_LISTAR`).
- `GET /usuario/{identificador}`: Buscar usuário por ID numérico ou username (Status 200 / 404; `responses=RESPOSTAS_OBTER`).
- `GET /usuario/{identificador}/detalhes`: Consulta detalhada `UsuarioDetails` com saneamento explícito de campos e exclusão estrita de senhas (Status 200 / 404; `responses=RESPOSTAS_OBTER`).
- `PUT /usuario/{identificador}` e `PATCH /usuario/{identificador}`: Atualização parcial de dados cadastrais (Status 200 / 400 / 404; `responses=RESPOSTAS_ATUALIZAR`).
- `PATCH /usuario/{identificador}/aprovar`: Aprovação e ativação imediata da conta (`status = Ativo`), liberando o login no sistema (Status 200 / 404; `responses=RESPOSTAS_ATUALIZAR`).
- `PATCH /usuario/{identificador}/inativar`: Inativação da conta do usuário (`status = Inativo`) (Status 200 / 404; `responses=RESPOSTAS_ATUALIZAR`).
- `PATCH /usuario/{identificador}/status`: Alteração formal de status da conta via schema `UsuarioStatusUpdate` (Status 200 / 400 / 404; `responses=RESPOSTAS_ATUALIZAR`).
- `PATCH /usuario/{identificador}/perfil`: Atualização semântica do perfil institucional via `UsuarioPerfilUpdate` (Status 200 / 400 / 404; `responses=RESPOSTAS_ATUALIZAR`).
- `POST /usuario/{identificador}/trocar-senha`: Troca autenticada de senha via `UsuarioTrocaSenha`, exigindo e validando a senha atual antes de persistir o novo hash Bcrypt (Status 200 / 400 / 403 / 404; `responses=RESPOSTAS_ATUALIZAR`).
- `POST /usuario/login`: Validação de credenciais (via body JSON `LoginRequest` ou query params) e status da conta (bloqueia contas pendentes, inativas ou bloqueadas com 403 Forbidden) com atualização atômica do `last_login` (Status 200 / 400 / 403; `responses=RESPOSTAS_OBTER`).
- `DELETE /usuario/{identificador}`: Exclusão de usuário cadastrado (Status 204 No Content; `responses=RESPOSTAS_DELETAR`).

### 9.9. Configuração de CORS e Conectividade Multiplataforma
Para suportar o consumo seguro e simultâneo pela aplicação Web (Streamlit/Next.js hospedada na VM da UFPI), pelo aplicativo móvel (Capacitor/Ionic) e em ambientes locais de desenvolvimento, o FastAPI configura o middleware oficial de CORS em [src/main.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/main.py):
- **Origens Locais**: `http://localhost:*`, `http://127.0.0.1:*` (portas `3000`, `5173`, `8000`, `8080`, `8501`);
- **Ambiente Mobile Híbrido**: `capacitor://localhost`, `ionic://localhost`;
- **Regex de Origens Institucionais**: `allow_origin_regex=r"https?://.*\.ufpi\.br(:[0-9]+)?|capacitor://.*|ionic://.*"`, autorizando a VM da UFPI e seus subdomínios;
- **Políticas e Métodos**: `allow_credentials=True`, `allow_methods=["*"]`, `allow_headers=["*"]`, garantindo resposta imediata `HTTP 200` para requisições de preflight `OPTIONS`.

---

## 10. Suíte de Testes Automatizados (`tests/`)

O backend conta com **165 testes automatizados** (100% de aprovação e execução completa em ~13.4 segundos), cobrindo regras de negócio, transformações do pipeline de ETL, validações de schemas Pydantic e todos os contratos RESTful dos endpoints HTTP da API.

### 10.1. Arquitetura e Fatiamento Vertical por Domínio

A suíte adota o padrão de **fatiamento vertical por entidade/domínio**, agrupando testes unitários de regras de negócio (`*_service.py`) e testes de integração HTTP (`*_controller.py`) dentro da pasta correspondente ao módulo:

```text
tests/
├── base_test_client.py               # Infraestrutura base com TestClient(app) e isolamento O(1) em memória
├── animal/                           # Domínio Animal
│   ├── test_animal_service.py        # Unitário: regras de biometria, faixas etárias e taxonomia (20 testes)
│   └── test_animal_controller.py     # HTTP: TestClient para endpoints /animal (8 testes)
├── amostra/                          # Domínio Amostra
│   ├── test_amostra_service.py       # Unitário: integridade, matrizes biológicas e AmostraDetails (8 testes)
│   └── test_amostra_controller.py    # HTTP: TestClient para endpoints /amostra (9 testes)
├── especie/                          # Domínio Espécie
│   ├── test_especie_service.py       # Unitário: nomenclatura binomial e catálogo (8 testes)
│   └── test_especie_controller.py    # HTTP: TestClient para endpoints /especie (6 testes)
├── exame/                            # Domínio Exame
│   └── test_exame_controller.py      # HTTP: TestClient para endpoints /exame (8 testes)
├── usuario/                          # Domínio Usuário
│   ├── test_usuario_service.py       # Unitário: hashing Bcrypt, ciclo de aprovação e login (13 testes)
│   └── test_usuario_controller.py    # HTTP: TestClient para endpoints /usuario (9 testes)
├── reagente_estoque/                 # Domínio Reagente e Estoque
│   ├── test_reagente_status_rules.py # Unitário: ciclo de vida estrito e transições de status (11 testes)
│   ├── test_estoque_alertas_endpoint.py # HTTP: alertas agregados e ordenação FIFO/PEPS (2 testes)
│   └── test_reagente_controller.py   # HTTP: TestClient para rotas /reagente e /estoque (1 teste)
├── utilitarios/                      # Testes Transversais
│   ├── test_utils_normalizacao.py    # Unitário: pacote modular src.utils.normalizacao (24 testes)
│   ├── test_model_corrections.py     # Unitário: conformidade dos schemas Pydantic v2 (4 testes)
│   ├── test_response_controller.py   # HTTP: tratamento centralizado de erros e 409 Conflict (12 testes)
│   └── test_partial_updates.py       # HTTP: validação de PATCH/PUT de campo único em 7 entidades (7 testes)
└── etl/                              # Pipeline de Engenharia de Dados
    ├── test_etl_base.py              # Unitário: ExtratorBase, dataclasses e auditoria (1 teste)
    ├── test_etl_morcegos.py          # Unitário: extração de dados brutos e matrizes de tecidos (2 testes)
    └── test_etl_carregar.py          # Unitário/Integração: carregador canônico e validação MongoDB (1 teste)
```

---

### 10.2. Infraestrutura Base e Isolamento em Memória (`tests/base_test_client.py`)

Para viabilizar a execução ultra-rápida e eliminar dependências externas durante os testes automatizados, foi desenvolvida a classe abstrata `ControllerTestCase(unittest.TestCase)`:

1. **Isolamento Total do Banco de Dados (`setUpClass`)**:
   - Itera sobre todos os 7 repositórios do sistema (`ALL_REPOSITORIES`) e define `repo._use_mongo = False`, `repo._collection = None` e `repo._db = None`.
   - Força os repositórios para o modo DAO em memória RAM $O(1)$, eliminando qualquer I/O de rede com o MongoDB real.
   - Instancia e preserva `cls.client = TestClient(app)`.
2. **Ambiente 100% Limpo entre Testes (`setUp` e `tearDown`)**:
   - Executa `self.limpar_repositorios()` antes e após cada método de teste, invocando `.clear()` em todos os 7 repositórios para garantir total independência entre os testes.
3. **Helpers Semânticos de Preparação (Arrange)**:
   - Injetam dados diretamente nos repositórios em memória sem gerar requisições HTTP redundantes:
     - `self.criar_especie_pre_requisito(**kwargs) -> Especie`
     - `self.criar_animal_pre_requisito(**kwargs) -> Animal`
     - `self.criar_amostra_pre_requisito(**kwargs) -> Amostra`
     - `self.criar_exame_pre_requisito(**kwargs) -> Exame`
     - `self.criar_reagente_pre_requisito(**kwargs) -> Reagente`
     - `self.criar_estoque_pre_requisito(**kwargs) -> EstoqueReagente`
     - `self.criar_usuario_pre_requisito(**kwargs) -> Usuario` (com senha pré-hasheada em Bcrypt).
4. **Helpers de Contrato RESTful e Asserção (Assert)**:
   - `assert_status(response, expected_status)`: Valida código HTTP com enriquecimento de payload em falhas.
   - `assert_created(response)`: Valida `201 Created` e retorna JSON.
   - `assert_ok(response)`: Valida `200 OK` e retorna payload.
   - `assert_no_content(response)`: Valida estritamente `204 No Content` sem corpo (`content == b""`).
   - `assert_not_found(response, expected_detail_substr)`: Valida `404 Not Found` e mensagens de detalhe.
   - `assert_conflict(response, expected_code)`: Valida `409 Conflict` estruturado com o payload `ConfirmacaoNecessariaError`.
   - `assert_primary_key_blocked(response_data)`: Assegura que chaves primárias numéricas ou identificadores arbitrários injetados pelo cliente foram ignorados ou sobrescritos pelo banco.
5. **Verificadores Reutilizáveis de Fluxos CRUD**:
   - `verificar_contrato_post_criacao(...)`: Injeta fake PK, valida `201 Created` e bloqueio de chave.
   - `verificar_contrato_get_detalhes_e_filtros(...)`: Valida consulta detalhada e listagem de arrays.
   - `verificar_contrato_patch_put_atualizacao(...)`: Valida atualização parcial de campos específicos.
   - `verificar_contrato_delete(...)`: Valida `204 No Content` (`b""`) e `404 Not Found` subsequente na mesma rota.

---

### 10.3. Matriz de Cobertura das Entidades e Controladores

| Entidade / Pacote | Arquivo de Teste | Qtd. | Camada | Principais Cenários Validados |
| :--- | :--- | :---: | :---: | :--- |
| **Animal** | `test_animal_service.py` | 20 | Service | Regras biométricas, conversão de gramas/mg para kg, dedução de faixa etária, localidade, taxonomia e bloqueio de duplicações. |
| **Animal** | `test_animal_controller.py` | 8 | Controller | `POST /animal/` com bloqueio de PK, confirmação obrigatória de espécie inédita (`409 Conflict` + `ESPECIE_NAO_ENCONTRADA`), duplicidade, `GET /animal/{id}` e `AnimalDetails`, filtros por sexo/classe, `PUT`/`PATCH` e `DELETE 204`. |
| **Amostra** | `test_amostra_service.py` | 8 | Service | Schema estrito `AmostraCreate`, obrigatoriedade uniforme, mapeamento por especificidade de 29 matrizes biológicas e projeção em `AmostraDetails`. |
| **Amostra** | `test_amostra_controller.py` | 9 | Controller | `POST /amostra/` com validação de animal vinculado (`409 Conflict` + `confirmar_novo_animal`), bloqueio de PK, contagem de acervo, listagem por animal, filtros analíticos, `PUT`/`PATCH` e `DELETE 204`. |
| **Espécie** | `test_especie_service.py` | 8 | Service | Formatação binomial zoológica, resolução taxonômica cruzada e ingestão delegada para o ETL. |
| **Espécie** | `test_especie_controller.py` | 6 | Controller | `POST /especie/cadastro` com bloqueio de PK, `GET /especie/{id}` com `quantidade_animais`, filtros por `Classe`, `PUT`/`PATCH` e `DELETE 204`. |
| **Exame** | `test_exame_controller.py` | 8 | Controller | `POST /exame/` com integridade de amostra (`400 Bad Request` + `confirmar_nova_amostra`), bloqueio de PK, contagem, listagem por patógeno (`TipoExame`), listagem por amostra, `PUT`/`PATCH` e `DELETE 204`. |
| **Usuário** | `test_usuario_service.py` | 13 | Service | Hashing Bcrypt com salt, unicidade de login/e-mail, solicitações com status `Pendente`, aprovação e ativação, inativação, bloqueio de login (`403`), troca de senha autenticada e projeção segura `UsuarioDetails`. |
| **Usuário** | `test_usuario_controller.py` | 9 | Controller | `POST /usuario/` com omissão estrita de senha, solicitação pública de cadastro, listagem de pendências, `POST /usuario/login` (sucesso e rejeição), `PATCH /perfil`, `PATCH /aprovar` e `/inativar`, e `DELETE 204`. |
| **Reagente & Estoque** | `test_reagente_status_rules.py` | 11 | Service/HTTP | Integridade estrita de `StatusReagente`, rejeição de "Baixo Estoque" em lote físico, atualização automática para `Vencido` (preservando `Esgotado`), bloqueio de vencimento prematuro e preflight CORS `OPTIONS`. |
| **Reagente & Estoque** | `test_estoque_alertas_endpoint.py` | 2 | Controller | Endpoints `GET /estoque/alertas` e alias `GET /reagente/alertas`, cálculo de baixo estoque consolidado ($\le 2$ un) e ordenação FIFO/PEPS de lotes a vencer em 30 dias. |
| **Reagente & Estoque** | `test_reagente_controller.py` | 1 | Controller | Fluxo completo ponta a ponta de criação de lote físico, cálculo automático de estoque agregado, conversões dimensionais de volume e recálculo global. |
| **Utilitários** | `test_utils_normalizacao.py` | 24 | Utils | Validação unitária de todas as funções do pacote modular `src.utils.normalizacao` (datas, coordenadas DMS, pesos, faixas etárias, matrizes e conversões). |
| **Utilitários** | `test_model_corrections.py` | 4 | Models | Verificação de conformidade de schemas Pydantic v2, aliases e serialização. |
| **Utilitários** | `test_response_controller.py` | 12 | Controller | Validação de que todas as rotas configuradas com `criar_router` interceptam centralizadamente `ConfirmacaoNecessariaError` (409), `KeyError` (404), `ValueError` (400), `PermissionError` (403) e `NoContentError` (204). |
| **Utilitários** | `test_partial_updates.py` | 7 | Controller | Testes transversais verificando que `PATCH` e `PUT` alteram um único atributo preservando todos os demais campos e a chave primária imutável nas 7 entidades. |
| **ETL** | `test_etl_*.py` | 4 | ETL | ExtratorBase, parsing de planilhas históricas de morcegos e carregador canônico idempotente com trava de segurança em `pibit_app_dev`. |

---

### 10.4. Execução Seletiva Inteligente por Padrão de Arquivos

Como as camadas de teste residem na mesma pasta do domínio, o filtro de padrões (`-p`) do `unittest` permite executar subconjuntos específicos de testes com máxima agilidade:

- **1. Executar TODA a suíte de testes (165 testes):**
  ```bash
  python -m unittest discover -s tests -t . -v
  ```
- **2. Executar APENAS os testes de Integração HTTP (`TestClient`):**
  ```bash
  python -m unittest discover -s tests -p "*_controller.py" -t . -v
  ```
- **3. Executar APENAS os testes Unitários de Regras de Negócio (`Services`):**
  ```bash
  python -m unittest discover -s tests -p "*_service.py" -t . -v
  ```
- **4. Executar TUDO de uma única entidade / domínio (ex.: Amostra):**
  ```bash
  python -m unittest discover -s tests/amostra -t . -v
  ```
- **5. Executar APENAS os testes do Pipeline de ETL:**
  ```bash
  python -m unittest discover -s tests/etl -t . -v
  ```

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
2. **Imutabilidade de Chave Primária e Atualização Parcial**: Chaves primárias (`id`/`_id`) nunca são aceitas na entrada da API; são geradas exclusivamente pelo repositório/banco na criação e mantidas imutáveis em atualizações. Rotas `PUT` e `PATCH` suportam atualização parcial segura (`exclude_unset=True`).
3. **Separação de Complexidade**: Anomalias e ruídos de planilhas são tratados exclusivamente pelos extratores ETL. Os Services da API devem permanecer enxutos, previsíveis e livres de parâmetros de exceção (`carga_legada`).
4. **Idempotência**: As operações de carga de dados utilizam operações de upsert baseadas em identificadores laboratoriais únicos, permitindo execuções repetidas sem duplicação de dados.
5. **Isolamento de Segredos e Bancos**: Credenciais e URIs de conexão devem ser mantidas em variáveis de ambiente (`MONGODB_URI`). O carregador ETL possui trava de segurança que impede a gravação fora de `pibit_app_dev`.
6. **Integridade Referencial e Confirmações Semânticas**: Bloqueio ativo de exclusão para entidades com registros dependentes e emissão de `HTTP 409 Conflict` (`ConfirmacaoNecessariaError`) para operações sensíveis que exigem confirmação explícita do usuário.