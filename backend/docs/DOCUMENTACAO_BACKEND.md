# ⚙️ LABVEPI — Documentação Técnica do Backend
> **Laboratório de Vigilância de Epizootias — Universidade Federal do Piauí (UFPI)**  
> *API RESTful, Modelos de Domínio Pydantic v2, Regras de Negócio, Repositórios e Testes*

---

## 📋 Sumário
1. [Visão Geral e Arquitetura em 4 Camadas](#1-visão-geral-e-arquitetura-em-4-camadas)
2. [Estrutura de Diretórios](#2-estrutura-de-diretórios)
3. [Tecnologias e Dependências](#3-tecnologias-e-dependências)
4. [Modelos de Domínio e Entidades (Pydantic v2)](#4-modelos-de-domínio-e-entidades-pydantic-v2)
   - [4.1. Usuário (`Usuario` e Enum `Perfil`)](#41-usuário-usuario-e-enum-perfil)
   - [4.2. Módulo de Espécie (`Especie`, DTOs e Enum `Classe`)](#42-módulo-de-espécie-especie-dtos-e-enum-classe)
   - [4.3. Módulo de Animal (`Animal`, DTOs e Enums de Domínio)](#43-módulo-de-animal-animal-dtos-e-enums-de-domínio)
   - [4.4. Módulo de Amostra Biológica (`Amostra`, DTOs e Enums)](#44-módulo-de-amostra-biológica-amostra-dtos-e-enums)
   - [4.5. Exame Laboratorial (`Exame` e Enums)](#45-exame-laboratorial-exame-e-enums)
   - [4.6. Reagente e Estoque (`Reagente` e `EstoqueReagente`)](#46-reagente-e-estoque-reagente-e-estoquereagente)
5. [Camada de Serviços e Regras de Negócio (`services/`)](#5-camada-de-serviços-e-regras-de-negócio-services)
   - [5.1. `AnimalService` e Regras de Biometria/Faixa Etária](#51-animalservice-e-regras-de-biometriafaixa-etária)
   - [5.2. `EspecieService` e Taxonomia Zoológica](#52-especieservice-e-taxonomia-zoológica)
   - [5.3. `AmostraService` e Normalização de Matrizes](#53-amostraservice-e-normalização-de-matrizes)
   - [5.4. Regras de Integridade, Bloqueio de Exclusão e Permissões (RBAC)](#54-regras-de-integridade-bloqueio-de-exclusão-e-permissões-rbac)
6. [Camada de Repositórios e Persistência (`repositories/`)](#6-camada-de-repositórios-e-persistência-repositories)
   - [6.1. Padrão DAO e Indexação em Memória $O(1)$](#61-padrão-dao-e-indexação-em-memória-o1)
   - [6.2. Matriz de Repositórios e Métodos Disponíveis](#62-matriz-de-repositórios-e-métodos-disponíveis)
7. [API HTTP (FastAPI) e Controladores (`controllers/`)](#7-api-http-fastapi-e-controladores-controllers)
   - [7.1. Mapeamento de Status HTTP e Exceções](#71-mapeamento-de-status-http-e-exceções)
   - [7.2. Endpoints de Animais (`/animais`)](#72-endpoints-de-animais-animais)
   - [7.3. Endpoints de Espécies (`/especies`)](#73-endpoints-de-espécies-especies)
   - [7.4. Endpoints de Amostras (`/amostras`)](#74-endpoints-de-amostras-amostras)
8. [Suíte de Testes Automatizados (`tests/`)](#8-suíte-de-testes-automatizados-tests)
9. [Como Executar o Backend Localmente](#9-como-executar-o-backend-localmente)
10. [Diretrizes de Qualidade e Boas Práticas](#10-diretrizes-de-qualidade-e-boas-práticas)

---

## 1. Visão Geral e Arquitetura em 4 Camadas

A camada de backend do **LABVEPI** foi projetada para garantir rigor técnico, integridade de dados científicos e desacoplamento absoluto de regras de negócio. Utiliza **Python 3.11+**, **FastAPI** para serviços assíncronos e **Pydantic v2** como núcleo de validação e modelagem de contratos de dados.

### 1.1. Filosofia de Design e Padrão em 4 Camadas

A arquitetura do backend segue o princípio de **separação estrita de responsabilidades**, estruturada em quatro camadas bem delimitadas:

```
┌─────────────────────────────────────────────────────────────────┐
│                      1. CONTROLLERS (API HTTP)                  │
│   FastAPI APIRouter · Validação de Request/Response · Erros     │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      2. SERVICES (REGRAS DE NEGÓCIO)            │
│   Resolução Taxonômica · Conversão de Unidades · Deduções       │
│   Saneamento de "Não informado" · Integridade Referencial       │
└──────────────────┬───────────────────────────────┬──────────────┘
                   │                               │
                   ▼                               ▼
┌──────────────────────────────────────┐  ┌───────────────────────┐
│       3. REPOSITORIES (DAO)          │  │  4. MODELS & DTOs     │
│   Persistência · Índices em Memória  │  │  Pydantic v2 Models   │
│   Busca Textual · Filtros · Paginação│  │  Create / Update / DTO│
└──────────────────┬───────────────────┘  │  Details Agregados    │
                   │                      │  Enums Estritos       │
                   ▼                      └───────────────────────┘
┌──────────────────────────────────────┐
│        BANCO DE DADOS / ATACADO      │
│  MongoDB Atlas · Catálogo CSV Local  │
└──────────────────────────────────────┘
```

1. **Camada de Modelos e DTOs (`src/models/`) — "Diretriz de Entidade Pura"**:
   - Cada domínio é dividido em:
     - `Entidade Canônica`: Estrutura do documento persistido no banco com suporte a aliases (`ConfigDict(populate_by_name=True)`);
     - `*Create (DTO)`: Schema de entrada com campos necessários para cadastro e flags de confirmação;
     - `*Update (DTO)`: Schema de entrada para atualizações parciais com campos opcionais;
     - `*Details (Schema Agregado)`: Schema enriquecido de resposta que padroniza ausência de valores como `"Não informado"`, aninha entidades relacionadas e traz listas/contagens de vínculos.
   - **Isolamento de Negócio**: Os modelos Pydantic **não contêm** validações ativas de regras de negócio, conversões complexas ou chamadas a banco. Toda a inteligência reside nos Serviços.

2. **Camada de Serviços (`src/services/`)**:
   - Contém a totalidade das regras laboratoriais e epidemiológicas;
   - Realiza resolução taxonômica automática, sanitização e conversão de unidades (ex: gramas para kg), inferência de faixa etária e normalização de matrizes biológicas;
   - Garante integridade referencial antes da gravação (ex: validação de animal vinculado antes de criar amostra);
   - Possui ganchos preparados (`_verificar_permissao`) para aplicação de RBAC (*Role-Based Access Control*).

3. **Camada de Repositórios (`src/repositories/`)**:
   - Responsabilidade exclusiva de persistência e acesso a dados (DAO);
   - Implementa indexação multinível em memória utilizando dicionários com chaves normalizadas (`casefold()`, `strip()`) para buscas em tempo constante $O(1)$;
   - Provê consultas filtradas, ordenação dinâmica, buscas textuais compostas e paginação (`skip`, `limit`);
   - Sem regras de negócio ou conversões de domínio.

4. **Camada de Controladores (`src/controllers/`)**:
   - Roteadores FastAPI (`APIRouter`) documentados com OpenAPI/Swagger (`summary`, `description`);
   - Conversão padronizada de exceções em códigos de status HTTP semânticos.

---

## 2. Estrutura de Diretórios

```
backend/
├── requirements.txt                  # Dependências do backend (fastapi, uvicorn, pydantic, email-validator)
├── database/                         # Scripts e conexões de persistência direta
├── docs/                             # Documentações técnicas e notas analíticas
│   ├── DOCUMENTACAO_BACKEND.md       # Documentação técnica consolidada do backend (este arquivo)
│   ├── analise_planilhas_models.TXT  # Levantamento taxonômico e correspondência com planilhas
│   ├── campos_impossiveis.txt        # Especificações de restrições de campos
│   └── regras.txt                    # Regras de negócio, permissões e diretrizes de validação
├── tests/                            # Testes unitários e de integração
│   ├── test_animal_service.py        # Testes de unidade e regras de negócio de Animais
│   ├── test_especie_service.py       # Testes de taxonomia, classes e importação CSV
│   └── test_amostra_service.py       # Testes de Amostras e integração HTTP com TestClient
└── src/
    ├── main.py                       # Ponto de entrada da aplicação FastAPI
    ├── config/                       # Configurações globais e variáveis de ambiente
    ├── controllers/                  # Controladores e rotas HTTP (endpoints)
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
    │   ├── especie_service.py        # Resolução taxonômica e catálogo CSV
    │   └── amostra_service.py        # Normalização de matriz biológica e ciclo de vida de Amostra
    └── utils/                        # Utilitários e formatadores auxiliares
```

---

## 3. Tecnologias e Dependências

| Pacote | Versão Mínima | Finalidade |
| :--- | :--- | :--- |
| **Python** | `3.11+` | Ambiente de execução e tipagem estática moderna. |
| **FastAPI** | `>=0.110.0` | Framework web assíncrono para construção da API RESTful com OpenAPI/Swagger. |
| **Uvicorn** | `>=0.29.0` | Servidor ASGI de alta performance para a aplicação FastAPI. |
| **Pydantic** | `>=2.6.0` | Validação de schemas, serialização e modelos de domínio fortemente tipados. |
| **Email-Validator** | `>=2.0.0` | Validação robusta de endereços de e-mail (`EmailStr`). |

---

## 4. Modelos de Domínio e Entidades (Pydantic v2)

Todos os modelos utilizam `ConfigDict(populate_by_name=True)`, permitindo tanto a instanciação via nomes de atributos padrão do Python quanto via aliases correspondentes aos documentos salvos no MongoDB (ex.: `_id` $\leftrightarrow$ `id`/`animal_id`/`amostra_id`).

---

### 4.1. Usuário (`Usuario` e Enum `Perfil`)
- **Arquivo**: [usuario.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/models/Usuario/usuario.py)
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
  - `password`: `str` (alias `senha`, hash criptográfico Bcrypt)
  - `created_at`: `datetime` (padrão `datetime.now`)
  - `last_login`: `Optional[Union[datetime, str]]` (data/hora do último acesso)
  - `perfil`: `Perfil` (perfil com normalizador inteligente de termos legados)
  - `matricula`: `Optional[Union[int, str]]`

---

### 4.2. Módulo de Espécie (`Especie`, DTOs e Enum `Classe`)
- **Modelos e DTOs** em `backend/src/models/Especie/`:
  - [especie.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/models/Especie/especie.py) (`Especie`): Entidade base contendo `id`, `nome_comum` (alias `nome`), `nome_cientifico` (obrigatório) e `classe`.
  - [especie_create.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/models/Especie/especie_create.py) (`EspecieCreate`): DTO de criação com flag `confirmar_nova_especie: bool = False`.
  - [especie_update.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/models/Especie/especie_update.py) (`EspecieUpdate`): DTO de atualização com flag `confirmar_atualizacao_especie: bool = False`.
  - [especie_details.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/models/Especie/especie_details.py) (`EspecieDetails`): Schema enriquecido de detalhes agregados com `quantidade_animais: int` e lista `animais: List[Animal]`.
- **Enum `Classe`** ([Classe.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/models/Especie/enums/Classe.py)):
  - `AVES` (`"Ave"`)
  - `MAMIFERO` (`"Mamífero"`)
  - `REPTIL` (`"Réptil"`)
  - `ANFIBIO` (`"Anfíbio"`)
  - `PEIXE` (`"Peixe"`)
- **Diretriz de Entidade Pura**: Validação e padronização taxonômica de nomes científicos e normalização de classes delegadas a `EspecieService` e `EspecieRepository`.

---

### 4.3. Módulo de Animal (`Animal`, DTOs e Enums de Domínio)
- **Modelos e DTOs** em `backend/src/models/Animal/`:
  - [animal.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/models/Animal/animal.py) (`Animal`): Entidade central de rastreamento animal.
    - **Campos Obrigatórios**: `animal_id` (alias `_id`), `classe`, `nome_comum`, `nome_cientifico`, `sexo`, `peso`, `faixa_etaria`, `orgao_origem` (alias `orgao`), `local_origem`, `regime_vida` (alias `status`), `status_vital`.
    - **Campos Opcionais**: `animal_id_projeto`, `microchip`, `funcao`, `idade`, `suspeita_clinica`, `animal_observacoes` (alias `observacoes`).
  - [animal_create.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/models/Animal/animal_create.py) (`AnimalCreate`): DTO de criação com flags `confirmar_novo_animal: bool = False` e `confirmar_nova_especie: bool = False`.
  - [animal_update.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/models/Animal/animal_update.py) (`AnimalUpdate`): DTO de atualização com flags de confirmação.
  - [animal_details.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/models/Animal/animal_details.py) (`AnimalDetails`): Schema enriquecido que substitui campos nulos por `"Não informado"`, aninha a entidade `Especie` e agrega `quantidade_amostras` e a lista `amostras: List[Amostra]`.
- **Enums de Domínio** em `backend/src/models/Animal/enums/`:
  - [Sexo](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/models/Animal/enums/Sexo.py): `Macho`, `Fêmea`, `Indeterminado`, `Não informado`.
  - [FaixaEtaria](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/models/Animal/enums/FaixaEtaria.py): `Filhote`, `Juvenil`, `Jovem`, `Sub Adulto`, `Adulto`, `Senil`, `Idoso`, `Potro`, `Ninhego`, `Não informado`.
  - [Orgao](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/models/Animal/enums/Orgao.py): `UFPI`, `HVU`, `CCZ`, `NEPPAS`, CETAS (`IBAMA - CETAS - PI`, `CE`, `RN`, `SEMARH - CETAS - PI`), universidades parceiras (`UFPA`, `UFRR`, `UFAC`, `UFOB`), `DSEI LESTE - AM`, `ZOOLOGICO -PI`, `PARTICULAR`, `OUTRO`, `NAO INFORMADO`.
  - [RegimeVida](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/models/Animal/enums/RegimeVida.py): `Vida livre`, `Cativeiro`, `Domiciliado`, `Não informado` (alias `status`).
  - [Funcao](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/models/Animal/enums/Funcao.py): `Pet`, `Trabalho`, `Lazer`, `Reprodução`, `Conservação / Zoológico`, `Outro`, `Não aplicável`.
  - [StatusVital](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/models/Animal/enums/StatusVital.py): `Vivo`, `Morto`, `Eutanasiado`, `Não informado`.

---

### 4.4. Módulo de Amostra Biológica (`Amostra`, DTOs e Enums)
- **Modelos e DTOs** em `backend/src/models/Amostra/`:
  - [amostra.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/models/Amostra/amostra.py) (`Amostra`):
    - **Campos Centrais**: `amostra_id` (alias `_id`), `animal_id`, `data_coleta_amostra` (alias `data_coleta`), `data_entrega` (alias `data_recebimento`), `material_biologico` (alias `metodo_coleta`), `status_amostra` (default `Disponível`), `laudo_liberado`.
    - **Laboratório e Triagem**: `local_coleta_amostra`, `nome_coletor`, `condicao_armazenamento`, `fase_amostra` (default `Extração`), `destino_amostra` (default `LAB VIGILÂNCIA DE EPIZOOTIAS - UFPI`), `kit_utilizado`, `caixa_armazenamento` (alias `caixa`).
    - **Frações Disponíveis**: `dna_disponivel`, `rna_disponivel`, `sequenciamento_disponivel`.
    - **Geolocalização & Projetos**: `amostra_id_projeto`, `latitude`, `longitude`, `amostra_observacoes` (alias `observacoes`).
  - [amostra_create.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/models/Amostra/amostra_create.py) (`AmostraCreate`): DTO de criação com datas padrão dinâmicas (`date.today`) e flags de confirmação `confirmar_nova_amostra` e `confirmar_novo_animal`.
  - [amostra_update.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/models/Amostra/amostra_update.py) (`AmostraUpdate`): DTO de atualização parcial com flag `confirmar_atualizacao_amostra`.
  - [amostra_details.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/models/Amostra/amostra_details.py) (`AmostraDetails`): Schema enriquecido que substitui campos nulos por `"Não informado"`, aninha o objeto completo [Animal](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/models/Animal/animal.py) de origem e traz `quantidade_exames` e a lista `exames: List[Exame]`.
- **Enums de Domínio** em `backend/src/models/Amostra/enums/`:
  - [MaterialBiologico](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/models/Amostra/enums/MaterialBiologico.py): 29 categorias cobrindo:
    - *Swabs*: `Swab oral`, `Swab nasal`, `Swab cloacal`, `Swab oral e cloacal`, `Swab retal`, `Swab traqueal`, `Swab ocular`;
    - *Sangue e Derivados*: `Sangue`, `Sangue total`, `Sangue (EDTA)`, `Soro`, `Papel filtro`, `Esfregaço sanguíneo`;
    - *Tecidos e Órgãos*: `Tecido`, `Pool de tecidos`, `Órgãos`, `Baço`, `Fígado`, `Pulmão`, `Rim`, `Encéfalo / Cérebro`, `Coração`;
    - *Excretas e Outros*: `Fezes`, `Enema`, `Líquor / LCR`, `Ectoparasita`, `Pele`, `Pelo`, `Necrópsia`, `Outro`.
  - [CondicaoArmazenamento](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/models/Amostra/enums/CondicaoArmazenamento.py): `Temperatura ambiente`, `Refrigerada`, `Congelada`, `Sem identificação`, `Coagulada`, `Hemolisada`, `Nitrogênio líquido`, `Gelo seco`.
  - [FaseAmostra](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/models/Amostra/enums/FaseAmostra.py): `Extração`, `PCR`, `ELETRO`.
  - [DestinoAmostra](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/models/Amostra/enums/DestinoAmostra.py): `Biobanco UFPI`, `Biobanco UFPA`, `Fiofruz AM`, `LASAN UFPI`, `LAPATO UFPI`, `LAPATO UFPA`, `LAB VIGILÂNCIA DE EPIZOOTIAS - UFPI`, `Outro`.
  - [StatusAmostra](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/models/Amostra/enums/StatusAmostra.py): `Disponível`, `Reservada`, `Em uso`, `Perdida`, `Esgotada`.

---

### 4.5. Exame Laboratorial (`Exame` e Enums)
- **Arquivo**: `backend/src/models/Exame/exame.py`
- **Campos**: `id` (alias `_id`), `amostra_id`, `tipo_teste` (alias `teste_laboratorial`), `patogeno` (alias `tipo_exame`), `resultado`, `data_exame`, `responsavel_tecnico`, `kit_utilizado`, `observacoes`.
- **Enums de Domínio**:
  - `TesteLaboratorial`: `PCR`, `Sorológico`, `Coproparasitológico`, `Hemoparasito em lâmina`, `Outro`.
  - `TipoExame`: `Febre Amarela`, `OrthoFlaviviridae`, `Febre do Nilo`, `Mycoplasma`, `Herpesviridae`, `Trypanosomatidae`, `Resistência Bacteriana`, `Hepatozoon`, `Raiva`, `Chlamydia`, `Sarcocystidae`, `Plasmodium e Haemoproteus`, `Outro`.
  - `ResultadoExame`: `Positivo`, `Negativo`, `Inconclusivo`, `Aguardando Resultado`, `Não Realizado`.

---

### 4.6. Reagente e Estoque (`Reagente` e `EstoqueReagente`)
- **Arquivos**: `backend/src/models/Reagente/`
- **Campos de Reagente**: `id`, `nome_reagente`, `fabricante`, `lote`, `quantidade_frascos`, `volume_por_frasco`, `unidade_medida`, `data_validade`, `localizacao_armazenamento`, `observacoes`.
- **Enum `UnidadeMedida`**: `ml`, `L`, `µl`, `g`, `mg`, `kg`, `un`.
- **Modelo Agregado `EstoqueReagente`**: Consolidação inteligente com conversão dimensional de grandezas compatíveis (ex.: ml e L, g e kg) e totalização por reagente.

---

## 5. Camada de Serviços e Regras de Negócio (`services/`)

A camada de serviços (`backend/src/services/`) concentra a totalidade das regras laboratoriais, sanitizações e orquestração de operações.

### 5.1. `AnimalService` e Regras de Biometria/Faixa Etária
- **Arquivo**: [animal_service.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/services/animal_service.py)
- **Operações e Regras**:
  1. **Sanitização e Conversão de Peso (`processar_peso` e `validar_peso`)**:
     - Converte strings com unidade em gramas para kg (`"400g"` $\rightarrow$ `0.4`, `"15g"` $\rightarrow$ `0.015`);
     - Converte vírgula decimal para ponto (`"12,5"` $\rightarrow$ `12.5`);
     - Padroniza termos legados (`"-"`, `"NI"`, `"ni"`, `"Não informado"`, `"N/A"`, `None`, `""`) para `"Não aferido"`;
     - Garante que pesos numéricos sejam estritamente maiores que zero ($peso > 0$).
  2. **Dedução Heurística de Faixa Etária (`deduzir_faixa_etaria`)**:
     - Identifica termos expressos (ex: `"filhote"`, `"ninhego"`, `"potro"`, `"juvenil"`, `"senil"`);
     - Processa idades temporais convertendo para escala em anos:
       - Meses (ex: `"6 meses"`, `"8m"`): $< 1.0\text{ ano} \rightarrow \text{Filhote}$;
       - Anos (ex: `"1.5 anos"`): $< 2.0\text{ anos} \rightarrow \text{Juvenil}$;
       - Anos (ex: `"3 anos"`): $< 4.0\text{ anos} \rightarrow \text{Sub Adulto}$;
       - Anos (ex: `"6 anos"`): $< 10.0\text{ anos} \rightarrow \text{Adulto}$;
       - Anos (ex: `"12 anos"`): $\ge 10.0\text{ anos} \rightarrow \text{Senil}$.
  3. **Resolução Taxonômica Integrada**: Delega a resolução e consistência de espécie e classe para o `EspecieService`.
  4. **Enriquecimento e Saneamento (`obter_animal_detalhes`)**: Constrói `AnimalDetails` garantindo que campos ausentes exibam `"Não informado"` explicitamente e anexa as amostras coletadas.

---

### 5.2. `EspecieService` e Taxonomia Zoológica
- **Arquivo**: [especie_service.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/services/especie_service.py)
- **Operações e Regras**:
  1. **Normalização Flexível de Classes (`normalizar_classe`)**: Mapeia variações como `"mamifero"`, `"mamífero"`, `"mamíferos"`, `"aves"`, `"repteis"`, `"répteis"` para os valores canônicos do Enum `Classe`.
  2. **Formatação Binomial Estrita (`formatar_nome_cientifico`)**: Aplica a convenção internacional de nomenclatura zoológica (primeira letra do gênero maiúscula, epíteto específico ou `"sp."`/`"spp."` em minúsculo — ex: `"panthera onca"` $\rightarrow$ `"Panthera onca"`).
  3. **Resolução Taxonômica Automatizada (`resolver_especie`)**:
     - Se informado apenas o **nome científico**, obtém automaticamente o **nome comum** e a **classe** do catálogo;
     - Se informado apenas o **nome comum**, obtém automaticamente o **nome científico** e a **classe**;
     - Se informados ambos, valida se coincidem na mesma espécie para evitar inconsistências taxonômicas;
     - Se a espécie for **inédita** (ausente no catálogo), exige o fornecimento completo de nome comum, científico e classe, acompanhado da flag `confirmar_nova_especie=True`.
  4. **Carga e Ingestão do Catálogo CSV (`importar_tabela_csv`)**: Inicializa e alimenta o catálogo com o acervo padrão de [especies_catalogo.csv](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/data/especies_catalogo.csv), suportando delimitadores `,` e `;`.

---

### 5.3. `AmostraService` e Normalização de Matrizes
- **Arquivo**: [amostra_service.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/services/amostra_service.py)
- **Operações e Regras**:
  1. **Normalização Heurística de Matrizes Biológicas (`normalizar_material_biologico`)**:
     - Análise por especificidade decrescente para evitar falsos positivos (ex: `"swab oral e cloacal"` é verificado antes de `"swab oral"`; `"pool de tecidos"` antes de `"tecido"`; `"sangue (edta)"` antes de `"sangue"`);
     - Mapeia termos comuns: `"soro"` $\rightarrow$ `MaterialBiologico.SORO`, `"edta"` $\rightarrow$ `MaterialBiologico.SANGUE_EDTA`, `"papel filtro"` $\rightarrow$ `MaterialBiologico.PAPEL_FILTRO`, `"órgãos"` $\rightarrow$ `MaterialBiologico.ORGAOS`.
  2. **Integridade Referencial com Animal de Origem**:
     - Valida via `AnimalService` se o `animal_id` existe antes de persistir a amostra;
     - Se o animal não existir, bloqueia a criação a menos que `confirmar_novo_animal=True` seja explicitado.
  3. **Agregação e Detalhes (`obter_amostra_detalhes`)**: Constrói `AmostraDetails` enriquecido com saneamento de `"Não informado"`, objeto `Animal` vinculado e lista/contagem de `Exame`.

---

### 5.4. Regras de Integridade, Bloqueio de Exclusão e Permissões (RBAC)

De acordo com as diretrizes e regras operacionais do LABVEPI:

1. **Bloqueio de Exclusão com Dependentes**:
   - É estritamente proibido excluir um **Animal** que possua amostras biológicas vinculadas.
   - É estritamente proibido excluir uma **Amostra** que possua exames laboratoriais vinculados.
   - Operações de merge/junção de registros duplicados devem transferir a custódia das amostras/exames antes da exclusão do registro redundante.
2. **Obrigatoriedade e Tolerância a Dados Incompletos**:
   - Segue a paridade com a interface de entrada: campos que não puderam ser aferidos em campo recebem `"Não informado"`, `"Não aferido"` ou `"Indeterminado"` em vez de falhar a validação.
3. **Matriz de Permissões por Perfil (RBAC)**:
   - **Registrar, editar e deletar Animais**: Docente, Mestrando, Doutorando, Bolsista Externo e Bolsista PIBITI.
   - **Registrar, editar e deletar Amostras**: Docente, Mestrando, Doutorando, Bolsista Externo e Bolsista PIBITI.
   - **Registrar, editar e deletar Exames**: Docente, Bolsista Externo e Bolsista PIBITI.
   - **Registrar, editar e deletar Reagentes**: Docente, Mestrando, Doutorando, Bolsista Externo e Bolsista PIBITI.
   - **Visualizar Registros / Consulta Geral**: Docente, Mestrando, Doutorando, Bolsista Externo, Bolsista PIBIC e Bolsista PIBITI.

---

## 6. Camada de Repositórios e Persistência (`repositories/`)

### 6.1. Padrão DAO e Indexação em Memória $O(1)$
Os repositórios (`backend/src/repositories/`) implementam o padrão DAO (*Data Access Object*). Para conferir máxima velocidade em testes, importações massivas e consultas, utilizam estruturas indexadas em memória com chaves normalizadas (`casefold()`, `strip()`), assegurando tempo de consulta constante $O(1)$ para chaves primárias e índices secundários.

### 6.2. Matriz de Repositórios e Métodos Disponíveis

| Repositório | Arquivo | Índices em Memória | Principais Métodos |
| :--- | :--- | :--- | :--- |
| **`EspecieRepository`** | [especie_repository.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/repositories/especie_repository.py) | `_por_id` (int), `_por_comum` (str), `_por_cientifico` (str), `_por_classe` (Classe $\rightarrow$ List) | `create`, `save`, `update`, `delete`, `buscar_por_id`, `buscar_por_nome_comum`, `buscar_por_nome_cientifico`, `buscar_por_classe`, `listar`, `count`, `exists`, `clear` |
| **`AnimalRepository`** | [animal_repository.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/repositories/animal_repository.py) | `_por_animal_id` (str), `_por_id` (int), `_por_projeto_id`, `_por_microchip`, `_por_nome_comum`, `_por_nome_cientifico`, `_por_classe`, `_por_sexo`, `_por_faixa_etaria`, `_por_orgao_origem`, `_por_regime_vida`, `_por_status_vital`, `_por_funcao` | `create`, `save`, `update`, `delete`, `buscar_por_animal_id`, `buscar_por_especie`, `listar` (com filtros múltiplos, busca textual ampla e paginação), `count`, `exists`, `clear` |
| **`AmostraRepository`** | [amostra_repository.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/repositories/amostra_repository.py) | `_por_amostra_id` (str), `_por_id` (int), `_por_animal_id` (1:N $\rightarrow$ List), `_por_condicao_armazenamento`, `_por_destino_amostra`, `_por_fase_amostra`, `_por_material_biologico`, `_por_status_amostra` | `create`, `save`, `update`, `delete`, `buscar_por_amostra_id`, `buscar_por_animal_id`, `listar` (filtros analíticos cruzados, ordenação dinâmica e paginação), `count`, `exists`, `clear` |

---

## 7. API HTTP (FastAPI) e Controladores (`controllers/`)

### 7.1. Mapeamento de Status HTTP e Exceções
Os controladores FastAPI (`backend/src/controllers/`) mapeiam erros de domínio para códigos HTTP semânticos:
- `ValueError` $\rightarrow$ `HTTP 400 Bad Request` (validação de entrada ou regra violada)
- `PermissionError` $\rightarrow$ `HTTP 403 Forbidden` (operação não permitida ao perfil)
- `KeyError` $\rightarrow$ `HTTP 404 Not Found` (recurso inexistente no acervo)
- Criações bem-sucedidas $\rightarrow$ `HTTP 201 Created`
- Deleções sem retorno $\rightarrow$ `HTTP 204 No Content`

### 7.2. Endpoints de Animais (`/animais`)
Arquivo: [animal_controller.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/controllers/animal_controller.py)
- `POST /animais/`: Cadastro de novos animais com taxonomia e biometria automatizadas (Status 201).
- `GET /animais/`: Listagem filtrada por `classe`, `sexo`, `status` (regime de vida), `status_vital`, busca textual ampla (`termo_busca`) e paginação (`skip`, `limit`) (Status 200).
- `GET /animais/{animal_id}`: Consulta por ID único do laboratório (Status 200 / 404).
- `GET /animais/{animal_id}/detalhes`: Consulta detalhada `AnimalDetails` com espécie e amostras colhidas (Status 200 / 404).
- `PUT /animais/{animal_id}`: Atualização de animal existente com reprocessamento de peso/espécie (Status 200 / 400 / 404).
- `DELETE /animais/{animal_id}`: Exclusão de animal cadastrado (bloqueia se houver amostras vinculadas) (Status 200 / 404).

### 7.3. Endpoints de Espécies (`/especies`)
Arquivo: [especie_controller.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/controllers/especie_controller.py)
- `POST /especies/cadastro`: Cadastro de nova espécie taxonômica com validação de binômio (Status 201).
- `GET /especies/`: Listagem filtrada por `nome_comum`, `nome_cientifico` e `classe` (Status 200).
- `GET /especies/{id}`: Detalhes taxonômicos acompanhados da lista e contagem de animais associados via `EspecieDetails` (Status 200 / 404).
- `PUT /especies/{id}`: Atualização de espécie com validação taxonômica e checagem de duplicidade (Status 200 / 400 / 404).
- `DELETE /especies/{id}`: Exclusão de espécie (Status 200 / 404).
- `POST /especies/importar-catalogo`: Importação em lote de tabela CSV para o catálogo padrão (Status 200 / 400).

### 7.4. Endpoints de Amostras (`/amostras`)
Arquivo: [amostra_controller.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/src/controllers/amostra_controller.py)
- `POST /amostras/`: Cadastro de nova amostra biológica vinculada a animal (Status 201).
- `GET /amostras/`: Listagem com filtros múltiplos (`animal_id`, `status_amostra`, `fase_amostra`, `condicao_armazenamento`, `destino_amostra`, `material_biologico`), busca textual e paginação (Status 200).
- `GET /amostras/contagem`: Quantidade total de amostras no acervo (Status 200).
- `GET /amostras/animal/{animal_id}`: Todas as amostras colhidas de um determinado animal (Status 200).
- `GET /amostras/{amostra_id}`: Consulta individual por ID laboratorial (Status 200 / 404).
- `GET /amostras/{amostra_id}/detalhes`: Detalhes completos `AmostraDetails` com entidade `Animal` e exames diagnósticos (Status 200 / 404).
- `PATCH /amostras/{amostra_id}`: Atualização parcial de campos da amostra com re-normalização de matriz (Status 200 / 400 / 404).
- `DELETE /amostras/{amostra_id}`: Exclusão de amostra (bloqueia se houver exames vinculados) (Status 204 No Content).

---

## 8. Suíte de Testes Automatizados (`tests/`)

O backend conta com suíte de testes automatizados em [backend/tests/](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/tests) que asseguram a integridade das regras de negócio e contratos de API:

1. **Testes de Animais ([test_animal_service.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/tests/test_animal_service.py))**:
   - Resolução automática de espécies pelo catálogo (nome comum e científico);
   - Processamento de unidades de peso (gramas para kg, vírgulas, `Não aferido`, rejeição de peso negativo ou zero);
   - Dedução de faixas etárias a partir de idades temporais;
   - Bloqueio de IDs duplicados e exigência de confirmação para espécies inéditas;
   - Ciclo CRUD completo em memória.
2. **Testes de Espécies ([test_especie_service.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/tests/test_especie_service.py))**:
   - Normalização de classes e formatação binomial de nomes científicos;
   - Resolução cruzada e detecção de incoerências taxonômicas;
   - Ingestão de arquivos CSV com persistência no catálogo.
3. **Testes de Amostras ([test_amostra_service.py](file:///home/gio/Documents/UNIVERSIDADE/Pesquisa/PIBIT%202026-2027/pibitapp/backend/tests/test_amostra_service.py))**:
   - Normalização heurística de termos livres para `MaterialBiologico`;
   - Validação referencial com o animal de origem e flag `confirmar_novo_animal`;
   - Geração de schema `AmostraDetails` com agregação de entidades;
   - Teste de integração HTTP ponta a ponta com `TestClient(app)` em `/amostras/`.

### Executando os Testes:
```bash
# Estando dentro do diretório 'backend'
python3 -m unittest discover -s tests
```

---

## 9. Como Executar o Backend Localmente

### Pré-requisitos
- Python 3.11+ instalado
- Ambiente virtual configurado e ativo

```bash
# 1. Entrar na pasta do backend (se estiver na raiz)
cd backend

# 2. Ativar o ambiente virtual
source .venv/bin/activate  # Linux/macOS
# ou: .venv\Scripts\activate no Windows

# 3. Instalar dependências do backend
pip install -r requirements.txt

# 4. Iniciar o servidor Uvicorn com hot-reload
uvicorn src.main:app --reload --port 8000
```

- **API Health Check**: `http://localhost:8000/`
- **Documentação Interativa Swagger**: `http://localhost:8000/docs`
- **Documentação ReDoc**: `http://localhost:8000/redoc`

---

## 10. Diretrizes de Qualidade e Boas Práticas

1. **Validação na Borda**: Nenhuma informação deve ser enviada ao banco de dados sem antes passar pela validação de seu modelo Pydantic correspondente.
2. **Imutabilidade e Consistência**: Utilizar Enums estritos para categorias fechadas e delegar normalizações de strings legadas para os Services.
3. **Isolamento de Segredos**: Nunca gravar credenciais ou URIs de banco diretamente nos arquivos do backend; utilizar `src/config/` e variáveis de ambiente (`MONGO_URI`).
4. **Integridade Referencial**: Sempre checar a existência de dependentes antes de exclusões ou migrações de dados biológicos.
