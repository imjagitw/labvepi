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
6. [Módulo de Utilitários e Normalização de Domínio (`src/utils/`)](#6-módulo-de-utilitários-e-normalização-de-domínio-srcutils)
   - [6.1. Utilitários Disponíveis (`normalizacao.py`)](#61-utilitários-disponíveis-normalizacaopy)
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
   - [9.1. Mapeamento de Status HTTP e Exceções](#91-mapeamento-de-status-http-e-exceções)
   - [9.2. Endpoints de Animais (`/animais`)](#92-endpoints-de-animais-animais)
   - [9.3. Endpoints de Espécies (`/especies`)](#93-endpoints-de-espécies-especies)
   - [9.4. Endpoints de Amostras (`/amostras`)](#94-endpoints-de-amostras-amostras)
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
│   │   FastAPI APIRouter · Validação de Request/Response · Erros         │   │
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
├── tests/                            # Suíte de testes automatizados (67 testes)
│   ├── test_animal_service.py        # Testes de unidade e regras de negócio de Animais
│   ├── test_especie_service.py       # Testes de taxonomia, classes e importação CSV
│   ├── test_amostra_service.py       # Testes de Amostras e integração HTTP com TestClient
│   ├── test_etl_morcegos.py          # Testes de extração, tolerâncias e parsing de morcegos
│   ├── test_etl_carregar.py          # Testes do carregador, validação de schemas e integridade
│   └── test_utils_normalizacao.py    # Testes unitários das funções de normalização canônica
└── src/
    ├── main.py                       # Ponto de entrada da aplicação FastAPI
    ├── config/                       # Configurações globais e variáveis de ambiente
    ├── controllers/                  # Controladores e rotas HTTP (endpoints RESTful)
    │   ├── animal_controller.py      # Endpoints RESTful de Animais (/animais)
    │   ├── especie_controller.py     # Endpoints RESTful de Espécies (/especies)
    │   ├── amostra_controller.py     # Endpoints RESTful de Amostras (/amostras)
    │   ├── exame_controller.py       # Endpoints RESTful de Exames (/exames)
    │   └── reagente_controller.py    # Endpoints RESTful de Reagentes (/reagentes)
    ├── data/                         # Dados de referência estáticos
    │   └── especies_catalogo.csv     # Catálogo taxonômico padrão de espécies
    ├── errors/                       # Tratamento centralizado de exceções
    ├── models/                       # Modelos Pydantic v2 e DTOs (Diretriz de Entidade Pura)
    │   ├── Animal/                   # Entidade, DTOs (Create, Update, Details) e Enums
    │   ├── Especie/                  # Entidade, DTOs (Create, Update, Details) e Enum Classe
    │   ├── Amostra/                  # Entidade, DTOs (Create, Update, Details) e Enums
    │   ├── Exame/                    # Modelo Exame e Enums
    │   ├── Reagente/                 # Modelo Reagente e Estoque
    │   └── Usuario/                  # Modelo Usuario e Enum Perfil
    ├── repositories/                 # Repositórios de dados e índices em memória (DAO)
    │   ├── animal_repository.py      # Repositório de Animais
    │   ├── especie_repository.py     # Repositório de Espécies
    │   └── amostra_repository.py     # Repositório de Amostras
    ├── services/                     # Serviços de domínio e regras de negócio
    │   ├── animal_service.py         # Regras de biometria, idade e ciclo de vida de Animal
    │   ├── especie_service.py        # Resolução taxonômica e integração com catálogo
    │   └── amostra_service.py        # Normalização de matriz biológica e ciclo de vida de Amostra
    └── utils/                        # Utilitários e formatadores auxiliares
        ├── __init__.py               # Exportação do ecossistema de utilitários
        └── normalizacao.py           # Funções canônicas de normalização (data, coordenada, enum, booleano)
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
- **Campos**: `id` (alias `_id`), `amostra_id`, `tipo_teste` (alias `teste_laboratorial`), `patogeno` (alias `tipo_exame`), `resultado`, `data_exame`, `responsavel_tecnico`, `kit_utilizado`, `observacoes`.
- **Enums**: `TesteLaboratorial`, `TipoExame` (patógenos de vigilância viral/bacteriana/parasitária) e `ResultadoExame` (`Positivo`, `Negativo`, `Inconclusivo`, `Aguardando Resultado`, `Não Realizado`).

### 4.6. Reagente e Estoque (`Reagente` e `EstoqueReagente`)
- **Campos**: `id`, `nome_reagente`, `fabricante`, `lote`, `quantidade_frascos`, `volume_por_frasco`, `unidade_medida`, `data_validade`, `localizacao_armazenamento`.
- **Modelo Agregado `EstoqueReagente`**: Totalização com conversão de unidades compatíveis (ex.: ml/L, g/kg).

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

---

## 6. Módulo de Utilitários e Normalização de Domínio (`src/utils/`)

Centraliza rotinas reutilizáveis de conversão e saneamento de dados biológicos e laboratoriais.

### 6.1. Utilitários Disponíveis (`normalizacao.py`)
- **Arquivo**: [src/utils/normalizacao.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/utils/normalizacao.py)
- **Funções Exportadas**:
  1. `normalizar_data(val)`:
     - Aceita objetos `date` ou `datetime`, strings no padrão ISO (`AAAA-MM-DD`), formato brasileiro (`DD/MM/AAAA`) e timestamps.
     - Trata sentinelas (`"-"`, `"NI"`, `"Não informado"`, `""`) convertendo para `None`.
  2. `normalizar_coordenada(val)`:
     - Converte valores numéricos, strings com vírgula decimal (`"-5,089"`) e coordenadas em graus sexagesimais DMS (ex: `05°05'21"S` $\rightarrow$ `-5.089167`) para float decimal WGS84.
  3. `normalizar_material_biologico(val)`:
     - Normalização heurística com 29 regras ordenadas por especificidade decrescente para o Enum [MaterialBiologico](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/models/Amostra/enums/MaterialBiologico.py).
  4. `normalizar_booleano(val)`:
     - Converte `True`/`False`, `1`/`0`, strings afirmativas (`"sim"`, `"+"`, `"positivo"`, `"true"`) para `True`, e negativas (`"não"`, `"-"`, `"negativo"`, `"false"`) para `False`.
  5. `normalizar_enum(enum_cls, val)`:
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

---

## 9. API HTTP (FastAPI) e Controladores (`src/controllers/`)

### 9.1. Mapeamento de Status HTTP e Exceções
- `ValueError` $\rightarrow$ `HTTP 400 Bad Request`
- `PermissionError` $\rightarrow$ `HTTP 403 Forbidden`
- `KeyError` $\rightarrow$ `HTTP 404 Not Found`
- Criações bem-sucedidas $\rightarrow$ `HTTP 201 Created`
- Deleções sem corpo $\rightarrow$ `HTTP 204 No Content`

### 9.2. Endpoints de Animais (`/animais`)
- `POST /animais/`: Cadastro de novos animais com taxonomia e biometria automatizadas (Status 201).
- `GET /animais/`: Listagem filtrada por `classe`, `sexo`, `status` (regime de vida), `status_vital`, busca textual ampla (`termo_busca`) e paginação (`skip`, `limit`) (Status 200).
- `GET /animais/{animal_id}`: Consulta por ID único do laboratório (Status 200 / 404).
- `GET /animais/{animal_id}/detalhes`: Consulta detalhada `AnimalDetails` com espécie e amostras colhidas (Status 200 / 404).
- `PUT /animais/{animal_id}`: Atualização de animal existente com reprocessamento de peso/espécie (Status 200 / 400 / 404).
- `DELETE /animais/{animal_id}`: Exclusão de animal cadastrado (bloqueia se houver amostras vinculadas) (Status 200 / 404).

### 9.3. Endpoints de Espécies (`/especies`)
- `POST /especies/cadastro`: Cadastro de nova espécie taxonômica com validação de binômio (Status 201).
- `GET /especies/`: Listagem filtrada por `nome_comum`, `nome_cientifico` e `classe` (Status 200).
- `GET /especies/{id}`: Detalhes taxonômicos acompanhados da lista e contagem de animais associados via `EspecieDetails` (Status 200 / 404).
- `PUT /especies/{id}`: Atualização de espécie com validação taxonômica e checagem de duplicidade (Status 200 / 400 / 404).
- `DELETE /especies/{id}`: Exclusão de espécie (Status 200 / 404).
- `POST /especies/importar-catalogo`: Importação em lote de tabela CSV para o catálogo padrão (Status 200 / 400).

### 9.4. Endpoints de Amostras (`/amostras`)
- `POST /amostras/`: Cadastro de nova amostra biológica vinculada a animal (Status 201).
- `GET /amostras/`: Listagem com filtros múltiplos (`animal_id`, `status_amostra`, `fase_amostra`, `condicao_armazenamento`, `destino_amostra`, `material_biologico`), busca textual e paginação (Status 200).
- `GET /amostras/contagem`: Quantidade total de amostras no acervo (Status 200).
- `GET /amostras/animal/{animal_id}`: Todas as amostras colhidas de um determinado animal (Status 200).
- `GET /amostras/{amostra_id}`: Consulta individual por ID laboratorial (Status 200 / 404).
- `GET /amostras/{amostra_id}/detalhes`: Detalhes completos `AmostraDetails` com entidade `Animal` e exames diagnósticos (Status 200 / 404).
- `PATCH /amostras/{amostra_id}`: Atualização parcial de campos da amostra com re-normalização de matriz (Status 200 / 400 / 404).
- `DELETE /amostras/{amostra_id}`: Exclusão de amostra (bloqueia se houver exames vinculados) (Status 204 No Content).

---

## 10. Suíte de Testes Automatizados (`tests/`)

O backend conta com **67 testes automatizados** cobrindo todas as camadas arquiteturais:

1. **Testes de Animais ([test_animal_service.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/tests/test_animal_service.py))**:
   - Resolução taxonômica pelo catálogo;
   - Processamento de unidades de peso (gramas para kg, vírgulas, `Não aferido`, rejeição de peso zero ou negativo);
   - Dedução de faixas etárias;
   - Bloqueio de IDs duplicados e CRUD completo em memória.
2. **Testes de Espécies ([test_especie_service.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/tests/test_especie_service.py))**:
   - Normalização de classes e formatação binomial;
   - Resolução cruzada e detecção de incoerências taxonômicas;
   - Ingestão de catálogo CSV via delegação para o ETL.
3. **Testes de Amostras ([test_amostra_service.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/tests/test_amostra_service.py))**:
   - Normalização de matriz biológica;
   - Validação referencial com o animal de origem e flag `confirmar_novo_animal`;
   - Geração de schema `AmostraDetails`;
   - Teste de integração HTTP ponta a ponta com `TestClient(app)` em `/amostras/`.
4. **Testes do Extrator de Morcegos ([test_etl_morcegos.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/tests/test_etl_morcegos.py))**:
   - Função utilitária de parsing booleano `eh_sim`;
   - Extração completa de linha representativa (animais, 7 amostras derivadas, 2 exames virais);
   - Registro estruturado de problemas para auditoria em caso de inconsistências.
5. **Testes do Carregador ETL ([test_etl_carregar.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/tests/test_etl_carregar.py))**:
   - Validação canônica de documentos Pydantic;
   - Detecção e descarte de vínculos órfãos;
   - Validação de segurança bloqueando bancos não autorizados;
   - Simulação de upsert idempotente no MongoDB;
   - Validação de documentos gerados a partir de planilhas com valores sentinela.
6. **Testes de Normalização ([test_utils_normalizacao.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/tests/test_utils_normalizacao.py))**:
   - Parsing de datas brasileiras e ISO;
   - Conversão de coordenadas DMS para float decimal;
   - Normalização tolerante de Enums e booleanos.

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