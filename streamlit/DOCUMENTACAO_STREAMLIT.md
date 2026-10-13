# 🖥️ LABVEPI — Documentação da Interface Streamlit
> **Laboratório de Vigilância de Epizootias — Universidade Federal do Piauí (UFPI)**  
> *Aplicação Web Interativa, Formulários Modulares, Dashboards e Governança*

---

## 📋 Sumário
1. [Visão Geral da Aplicação Frontend](#1-visão-geral-da-aplicação-frontend)
2. [Estrutura de Arquivos e Diretórios](#2-estrutura-de-arquivos-e-diretórios)
3. [Tecnologias Utilizadas](#3-tecnologias-utilizadas)
4. [Navegação, Layout e Central de Alertas](#4-navegação-layout-e-central-de-alertas)
   - [4.1. Roteamento Multipágina (`st.navigation`)](#41-roteamento-multipágina-stnavigation)
   - [4.2. Cabeçalho Institucional e Identidade Visual](#42-cabeçalho-institucional-e-identidade-visual)
   - [4.3. Central de Alertas em Tempo Real (Sidebar)](#43-central-de-alertas-em-tempo-real-sidebar)
5. [Autenticação, Sessão e Controle de Acesso (RBAC)](#5-autenticação-sessão-e-controle-de-acesso-rbac)
   - [5.1. Fluxo de Sessão e Criptografia com Bcrypt](#51-fluxo-de-sessão-e-criptografia-com-bcrypt)
   - [5.2. Matriz de Níveis de Permissão](#52-matriz-de-níveis-de-permissão)
   - [5.3. Gestão e Cadastro de Contas](#53-gestão-e-cadastro-de-contas)
6. [Formulários Modulares de Cadastro (`forms/`)](#6-formulários-modulares-de-cadastro-forms)
   - [6.1. Cadastro de Animais (`registro_animal.py`)](#61-cadastro-de-animais-registro_animalpy)
   - [6.2. Cadastro de Amostras (`registro_amostra.py`)](#62-cadastro-de-amostras-registro_amostrapy)
   - [6.3. Cadastro de Exames (`registro_exame.py`)](#63-cadastro-de-exames-registro_examepy)
   - [6.4. Cadastro de Reagentes (`registro_reagente.py`)](#64-cadastro-de-reagentes-registro_reagentepy)
7. [Páginas Operacionais e Analíticas (`pages/`)](#7-páginas-operacionais-e-analíticas-pages)
   - [7.1. Novo Registro (`Novo_Registro.py`)](#71-novo-registro-novo_registropy)
   - [7.2. Editar Amostra (`Editar_Amostra.py`)](#72-editar-amostra-editar_amostrapy)
   - [7.3. Importação em Lote (`Importar.py`)](#73-importação-em-lote-importarpy)
   - [7.4. Painel de Registros (`Registros.py`)](#74-painel-de-registros-registrospy)
   - [7.5. Relatórios e Indicadores Epidemiológicos (`Relatorios.py`)](#75-relatórios-e-indicadores-epidemiológicos-relatoriospy)
8. [Scripts de Governança e Auditoria (`scripts/`)](#8-scripts-de-governança-e-auditoria-scripts)
9. [Rotinas de Backup e Restauração (MongoDB Tools)](#9-rotinas-de-backup-e-restauração-mongodb-tools)
10. [Ambiente Dev Container](#10-ambiente-dev-container)
11. [Como Executar o Frontend Localmente](#11-como-executar-o-frontend-localmente)
12. [Configuração de Segredos e Segurança](#12-configuração-de-segredos-e-segurança)

---

## 1. Visão Geral da Aplicação Frontend

O frontend do **LABVEPI** é uma plataforma web científica construída sobre **Streamlit 1.36+**. Ela atende às rotinas laboratoriais de pesquisadores, docentes e discentes da UFPI, proporcionando:
- Interface reativa multipágina moderna baseada em `st.navigation` e `st.Page`;
- Entrada de dados com validações interativas e modais de confirmação (`@st.dialog`);
- Alertas proativos de estoque e validade de reagentes;
- Importação automatizada de lotes legados em planilhas Excel e CSV com modo *dry-run*;
- Catálogo geral com busca textual global, paginação (`st.pagination`) e filtros avançados;
- Dashboards estatísticos e epidemiológicos interativos com **Plotly Express**.

---

## 2. Estrutura de Arquivos e Diretórios

```
streamlit/
├── app.py                            # Ponto de entrada (Roteamento st.navigation, Header & Alertas)
├── utils.py                          # Conexão MongoDB, verificação Bcrypt e normalizações
├── widgets.py                        # Componentes reutilizáveis (Login, Cadastro, Gestão de Acessos)
├── logo.png                          # Logomarca oficial do LABVEPI - UFPI
├── requirements.txt                  # Dependências do frontend
├── secrets.toml.example              # Modelo para segredos (.streamlit/secrets.toml)
├── .devcontainer/                    # Ambiente Docker pré-configurado
│   └── devcontainer.json
├── forms/                            # Formulários modulares de inserção
│   ├── __init__.py
│   ├── registro_animal.py            # Cadastro de animais com diálogo modal e taxonomia
│   ├── registro_amostra.py           # Inserção de amostras biológicas vinculadas
│   ├── registro_exame.py             # Registro de ensaios e testes laboratoriais
│   └── registro_reagente.py          # Cadastro de lotes de reagentes e insumos
├── pages/                            # Páginas da aplicação
│   ├── Novo_Registro.py              # Hub unificado de abas de cadastro
│   ├── Editar_Amostra.py             # Gestão de alíquotas e status (Restrito a Docentes)
│   ├── Importar.py                   # Processamento em lote de planilhas com simulação
│   ├── Registros.py                  # Catálogo completo, busca, paginação e CRUD
│   └── Relatorios.py                 # Painel de KPIs e gráficos estatísticos Plotly
└── scripts/                          # Scripts de governança, banco e backups
    ├── auditar_banco.py              # Auditoria de integridade referencial (Read-Only)
    ├── setup_banco.py                # Criação de índices e sanitização de coleções
    ├── instrucoes_backup.md          # Passo a passo de mongodump e mongorestore
    └── resultados/                   # Arquivos de saída de auditoria e dumps (.archive)
```

---

## 3. Tecnologias Utilizadas

| Tecnologia | Finalidade |
| :--- | :--- |
| **Streamlit 1.36+** | Framework de UI reativa multipágina (`st.navigation`, `st.Page`, `@st.dialog`, `st.pagination`). |
| **Streamlit Material Symbols** | Ícones modernos nativos no formato `:material/<icon>:`. |
| **PyMongo & Certifi** | Driver oficial do MongoDB com conexão segura TLS/SSL para o MongoDB Atlas. |
| **Bcrypt** | Hashing criptográfico seguro e validação de senhas de colaboradores. |
| **Pandas** | Manipulação e transformação de dados tabulares. |
| **Plotly Express** | Renderização de gráficos dinâmicos de alta qualidade. |
| **OpenPyXL** | Processamento de planilhas nos formatos Excel (`.xlsx`, `.xls`). |

---

## 4. Navegação, Layout e Central de Alertas

### 4.1. Roteamento Multipágina (`st.navigation`)
A aplicação utiliza a API nativa `st.navigation`, agrupando as páginas em categorias lógicas:

```python
nav = st.navigation({
    "Geral": [
        st.Page("pages/Novo_Registro.py", title="Novo Registro", icon=":material/add_circle:"),
        st.Page("pages/Editar_Amostra.py", title="Editar Amostra", icon=":material/edit:"),
        st.Page("pages/Importar.py", title="Importar Planilha", icon=":material/upload_file:"),
    ],
    "Consultas & Dados": [
        st.Page("pages/Registros.py", title="Registros", icon=":material/database:"),
        st.Page("pages/Relatorios.py", title="Relatórios e Indicadores", icon=":material/bar_chart:"),
    ]
})
```

### 4.2. Cabeçalho Institucional e Identidade Visual
Em todas as execuções, `app.py` renderiza o cabeçalho oficial do laboratório, incluindo a logomarca oficial (`logo.png`), o título institucional, a identificação do usuário logado e o botão de encerramento de sessão (*Logout*).

### 4.3. Central de Alertas em Tempo Real (Sidebar)
Um componente permanente na barra lateral (`Sistema de Alertas`) realiza varreduras em tempo de execução no estoque de reagentes:
- ⚠️ **Baixo Estoque**: Alerta lotes com saldo $\le 2$ unidades;
- ⚠️ **Vencendo em Breve**: Identifica produtos que expiram nos próximos 30 dias;
- 🚨 **Vencidos**: Destaca lotes com validade ultrapassada;
- Botão de atalho para redirecionamento imediato para a página `Registros.py` com filtros correspondentes aplicados.

---

## 5. Autenticação, Sessão e Controle de Acesso (RBAC)

### 5.1. Fluxo de Sessão e Criptografia com Bcrypt
- As senhas são armazenadas no MongoDB exclusivamente como hashes Bcrypt gerados com salt.
- Ao autenticar, os dados de sessão do usuário (`usuario_id`, `username`, `matricula`/`perfil`) são guardados em `st.session_state`.
- Caso o usuário não esteja autenticado, a interface restringe o acesso, exibindo as telas de login e cadastro em `widgets.py`.

### 5.2. Matriz de Níveis de Permissão
O sistema implementa regras baseadas na categoria do colaborador (`matricula`/perfil):

| Funcionalidade / Operação | Bolsistas / Pós-Graduandos | Docente (Professor) |
| :--- | :---: | :---: |
| Visualizar Alertas e Painéis | ✅ | ✅ |
| Cadastrar Animais, Amostras, Exames, Reagentes | ✅ | ✅ |
| Importação em Lote de Planilhas | ✅ | ✅ |
| Consultar Registros com Busca e Paginação | ✅ | ✅ |
| Visualizar Gráficos e Relatórios | ✅ | ✅ |
| **Editar Amostras (`Editar_Amostra.py`)** | ❌ (Bloqueado) | ✅ |
| **Editar Animais Cadastrados (`Registros.py`)** | ❌ (Bloqueado) | ✅ |
| **Exclusão de Registros** | ❌ (Bloqueado) | ✅ |

### 5.3. Gestão e Cadastro de Contas
- **Solicitação de Acesso**: Permite novos membros do laboratório solicitarem conta indicando nome, usuário, e-mail institucional e vínculo.
- **Painel de Usuários**: Visualização administrativa dos colaboradores com status de acesso.

---

## 6. Formulários Modulares de Cadastro (`forms/`)

Cada formulário reside em seu próprio módulo, garantindo separação clara de responsabilidades:

### 6.1. Cadastro de Animais (`registro_animal.py`)
- **Resolução Taxonômica Integrada**: Busca prévia por espécies catalogadas. Caso uma espécie inédita seja informada, aciona solicitação de confirmação para cadastro taxonômico.
- **Campos Obrigatórios**: Nome comum, nome científico, classe, sexo, peso (com opção *"Não aferido"*), órgão de origem, procedência geográfica, regime de vida e status vital (`Vivo` / `Morto`).
- **Cálculo de Faixa Etária**: Conversor inteligente que deduz automaticamente a categoria etária (`Filhote`, `Juvenil`, `Sub Adulto`, `Adulto`, `Senil`) com base no tempo de vida inserido.
- **Revisão Modal (`@st.dialog`)**: Apresenta sumário estruturado em duas colunas para confirmação dos dados antes da inserção definitiva no MongoDB.

### 6.2. Cadastro de Amostras (`registro_amostra.py`)
- Seleção reativa do animal previamente cadastrado no banco;
- Definição do método de coleta (`Swab oral`, `Sangue`, `Fezes`, `Tecido`, etc.) e condição de armazenamento;
- Indicação de disponibilidade de alíquotas de DNA, RNA e material para sequenciamento genético;
- Registro da caixa física / freezer de armazenamento e status inicial da amostra.

### 6.3. Cadastro de Exames (`registro_exame.py`)
- Associação direta à amostra biológica correspondente;
- Seleção de ensaio (`PCR`, `Sorológico`, etc.) e patógeno investigado (`Febre Amarela`, `Orthoflaviridae`, `Raiva`, etc.);
- Registro do laboratório executor, responsável técnico, kit diagnóstico e protocolo.

### 6.4. Cadastro de Reagentes (`registro_reagente.py`)
- Registro de lotes individuais com código interno, descrição comercial, fabricante e número de lote;
- Validação impeditiva contra datas de validade expiradas;
- Definição de quantidades em frascos/unidades e volume nominal.

---

## 7. Páginas Operacionais e Analíticas (`pages/`)

### 7.1. Novo Registro (`Novo_Registro.py`)
Hub que reúne os quatro formulários modulares em abas interativas (*Animais*, *Amostras*, *Exames*, *Reagentes*), permitindo fluxos contínuos de cadastro no laboratório.

### 7.2. Editar Amostra (`Editar_Amostra.py`)
Página restrita ao perfil **Docente**:
- Busca ágil por identificador de amostra (`amostra_id`);
- Atualização em tempo real de status (`Disponível`, `Reservada`, `Em uso`, `Esgotada`, `Perdida`);
- Atualização de caixas de freezer e inclusão de novos ensaios diagnósticos.

### 7.3. Importação em Lote (`Importar.py`)
Módulo avançado de ingestão de dados:
- Suporte a arquivos **CSV** e **Excel (`.xlsx`, `.xls`)**;
- Encadeamento mestre: processamento em cascata criando animais, suas amostras associadas e respectivos exames;
- **Modo Simulação (*Dry-run*)**: Executa todas as checagens e mapeamentos sem persistir nada no banco, exibindo relatório detalhado de inconsistências;
- **Resolução de Conflitos**: Estratégias configuráveis de ignorar existentes (*skip*), atualizar dados (*upsert*) ou sobrescrever (*replace*).

### 7.4. Painel de Registros (`Registros.py`)
Central de consulta e governança de dados:
- Abas segregadas para cada coleção (*Animais*, *Amostras*, *Exames*, *Reagentes*);
- **Busca Global**: Filtro de texto livre pesquisando por ID de laboratório, código HVU, microchip, nomes populares ou científicos;
- **Paginação Reativa (`st.pagination`)**: Configuração de registros por página (5, 10, 20, 50, 100) com ordenação temporal;
- **Ações CRUD**: Edição e exclusão de animais com bloqueio de segurança para perfis sem permissão docente.

### 7.5. Relatórios e Indicadores Epidemiológicos (`Relatorios.py`)
Dashboard analítico executivo:
- **Cards de KPIs**: Totalizador de animais, amostras preservadas, ensaios realizados e reagentes cadastrados;
- **Gráficos Plotly Express**:
  - Distribuição taxonômica por classe biológica e sexo;
  - Prevalência de métodos de coleta e frações genéticas;
  - Positividade por patógeno em ensaios laboratoriais;
  - Cronograma de vencimento de lotes de insumos.

---

## 8. Scripts de Governança e Auditoria (`scripts/`)

Utilitários localizados em `streamlit/scripts/`:

1. **`auditar_banco.py` (Auditoria Somente Leitura)**:
   - Executa varredura profunda no MongoDB Atlas sem alterar documentos;
   - Avalia a integridade referencial dos vínculos (`amostras.animal_id -> animais._id` e `exames.amostra_id -> amostras._id`);
   - Detecta divergências legadas de tipos primitivos (como microchips gravados como inteiros em vez de strings);
   - Gera relatórios em formato JSON (`relatorio_auditoria.json`) e Markdown executivo (`resumo_auditoria_banco.md`).

2. **`setup_banco.py` (Sanitização e Índices)**:
   - Cria índices únicos obrigatórios (`username` e `email` na coleção `usuarios`);
   - Corrige divergências legadas de tipagem quando acionado com `--corrigir`;
   - Permite geração de massa de dados simulados (*seed*) em bancos de homologação.

---

## 9. Rotinas de Backup e Restauração (MongoDB Tools)

O ecossistema utiliza as ferramentas oficiais **MongoDB Database Tools**:

### 9.1. Exportação de Backup (*Dump*)
```bash
mongodump \
  --uri="$MONGO_URI" \
  --db="pibit_app" \
  --archive="streamlit/scripts/resultados/pibit_app.archive" \
  --gzip
```

### 9.2. Restauração de Backup (*Restore*)
```bash
mongorestore \
  --uri="$MONGO_URI" \
  --archive="streamlit/scripts/resultados/pibit_app.archive" \
  --gzip \
  --drop
```

---

## 10. Ambiente Dev Container

O diretório `streamlit/.devcontainer/devcontainer.json` oferece um ambiente conteinerizado pronto para desenvolvimento em **VS Code** ou **GitHub Codespaces**:
- Imagem: `mcr.microsoft.com/devcontainers/python:1-3.11-bookworm`
- Portas mapeadas: `8501` (Streamlit) e `8000` (FastAPI)
- Instalação automática de dependências e extensões de linters.

---

## 11. Como Executar o Frontend Localmente

### Pré-requisitos
- Python 3.11+ instalado
- Ambiente virtual ativo

```bash
# 1. Ativar o ambiente virtual (na raiz do projeto)
source .venv/bin/activate  # Linux/macOS
# ou: .venv\Scripts\activate no Windows

# 2. Instalar dependências da interface Streamlit
pip install -r streamlit/requirements.txt

# 3. Executar o servidor Streamlit
streamlit run streamlit/app.py
```

A interface abrirá automaticamente no navegador no endereço `http://localhost:8501`.

---

## 12. Configuração de Segredos e Segurança

As credenciais do MongoDB Atlas devem ser fornecidas de forma segura:

1. **Arquivo de Segredos (`streamlit/.streamlit/secrets.toml`)**:
   ```toml
   [mongo]
   uri = "mongodb+srv://<usuario>:<senha>@cluster.mongodb.net/?retryWrites=true&w=majority"
   ```
2. **Variável de Ambiente (`MONGO_URI`)**:
   ```bash
   export MONGO_URI="mongodb+srv://<usuario>:<senha>@cluster.mongodb.net/?retryWrites=true&w=majority"
   ```

> ⚠️ **Atenção**: Nunca versione arquivos `secrets.toml` contendo senhas reais. O arquivo `secrets.toml.example` serve como referência pública de formato.
