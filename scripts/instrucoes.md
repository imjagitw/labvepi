# 📦 Guia de Inicialização, Backup, Restauração e Auditoria do Banco de Dados (MongoDB)

Este documento descreve os procedimentos operacionais para:
1. **Subir um ambiente de testes isolado (`pibit_app_dev`)** sem afetar a produção.
2. **Gerar cópia de segurança (*dump*)** e plano de recuperação (*Disaster Recovery*).
3. **Executar auditoria somente-leitura** de dados, contagens e integridade de vínculos.
4. **Conferir e criar índices no MongoDB** (para chaves estrangeiras `animal_id`, `amostra_id`, filtros do sistema e unicidade, considerando a unicidade nativa de `_id`).
5. **Higienizar e corrigir dados legados** antes de exigir vínculos e novos campos obrigatórios.
6. **Testar com dados de exemplo (`--seed`)** e validar detecção de vínculos quebrados.
7. **Aplicar mudanças em produção com salvaguardas explícitas (`--producao`)**.

---

## 📋 1. Pré-requisitos e Ferramentas

- **Python 3.11+** com as dependências instaladas:
  ```bash
  pip install pymongo certifi
  ```
- **MongoDB Database Tools** (`mongodump` e `mongorestore`) e, opcionalmente, `mongosh`:
  - **Linux (Ubuntu/Debian):**
    ```bash
    sudo apt-get install mongodb-database-tools
    ```
  - **macOS (Homebrew):**
    ```bash
    brew tap mongodb/brew
    brew install mongodb-database-tools
    ```
  - **Windows:**
    Baixe no [MongoDB Database Tools](https://www.mongodb.com/try/download/database-tools) e adicione o diretório `bin` ao `PATH`.

Valide a instalação:
```bash
mongodump --version
mongorestore --version
```

---

## 🔒 2. Ambientes e Precedência de Conexão

Para garantir segurança total dos dados, os scripts e o app obedecem a uma ordem rigorosa de precedência de conexão:

| Componente | Ordem de Precedência | Padrão se não informado |
| :--- | :--- | :--- |
| **Scripts** (`auditar_banco.py`, `setup_banco.py`) | 1. `MONGO_URI` e `MONGO_DB` (variáveis de ambiente)<br>2. `.streamlit/secrets.toml` (`[mongo].uri`, `[mongo].db`) | **`pibit_app_dev`** (NUNCA produção por omissão) |
| **App Streamlit** | `.streamlit/secrets.toml` (`[mongo].uri`, `[mongo].db`) | `pibit_app` |

### 🛡️ Boas práticas de segurança:
1. **Nunca grave senhas no histórico do shell:**
   ```bash
   read -rs MONGO_URI && export MONGO_URI      # cole a URI de conexão e tecle Enter
   ```
2. **Salvaguarda de Produção:** O script `setup_banco.py` roda em **simulação** por padrão. Para gravar em `pibit_app` (produção), ele exige **obrigatoriamente** as flags `--aplicar --producao`. Sem `--producao`, o script recusa a execução e protege a base contra alterações acidentais.
3. **Isolamento de Testes:** O comando `--seed` só roda em bancos terminados com `_dev` ou `_test`.

### Configuração Local do Ambiente de Teste (`.streamlit/secrets.toml`):
```toml
[mongo]
uri = "mongodb+srv://USUARIO:SENHA@cluster.mongodb.net/?retryWrites=true&w=majority"
db  = "pibit_app_dev"
```

---

## 💾 3. Backup de Produção (*Dump*)

Execute a partir da raiz do projeto (`pibitapp/`):

```bash
mkdir -p scripts/resultados

# Gerar dump comprimido do banco de produção
mongodump \
  --uri="$MONGO_URI" \
  --db="pibit_app" \
  --archive="scripts/resultados/pibit_app.archive" \
  --gzip
```

> ⚠️ O arquivo `.archive` contém dados sensíveis; o diretório `scripts/resultados` está no `.gitignore` e não deve ser versionado.

---

## 🧪 4. Subir Ambiente de Testes Sem Alterar Produção (*Restore Dev*)

Restaure o dump de produção diretamente no banco `pibit_app_dev`, remapeando os namespaces para garantir que o banco `pibit_app` permaneça intacto:

```bash
# Restaura as coleções no namespace pibit_app_dev.*
mongorestore \
  --uri="$MONGO_URI" \
  --gzip \
  --archive="scripts/resultados/pibit_app.archive" \
  --nsFrom="pibit_app.*" \
  --nsTo="pibit_app_dev.*" \
  --drop
```
*Nota:* A flag `--drop` aqui afeta exclusivamente o destino (`pibit_app_dev`), permitindo recriar o ambiente de testes a qualquer momento.

Pronto: o ambiente de desenvolvimento agora possui uma cópia fiel de produção para auditoria e simulação de regras, com zero risco para a produção.

---

## 🔍 5. Auditoria de Dados (Somente Leitura)

O script `scripts/auditar_banco.py` analisa a estrutura, tipos de campos, divergências de nomenclatura e integridade de vínculos sem expor dados pessoais:

```bash
export MONGO_DB="pibit_app_dev"

python scripts/auditar_banco.py
```

### O que a auditoria avalia:
1. **Coleções e Índices:** Contagens, tipos de `_id` (`string` ou `ObjectId`) e índices ativos.
2. **Integridade de Vínculos:**
   - `amostras.animal_id` $\rightarrow$ `animais._id` (órfãos vs. válidos).
   - `exames.amostra_id` $\rightarrow$ `amostras._id` (órfãos vs. válidos).
3. **Campos Obrigatórios:** Estatística de preenchimento real de cada campo obrigatório.
4. **Divergências de Modelo:** Nomes legados de campos (`hvu`, `status`, `data_coleta`, `local_coleta`, `órgãos`, `funcão`, etc.).
5. **Usuários:** Detecção de duplicidades em `username` e `email` para assegurar que índices únicos possam ser criados.

O relatório detalhado é salvo em `scripts/resultados/relatorio_auditoria_<data_hora>.json`.

---

## 🔬 6. Consultar Vínculos e Agregações

### Com os scripts do projeto:
```bash
python scripts/setup_banco.py --verificar-indices       # índices existentes x esperados
python scripts/setup_banco.py --verificar-integridade   # órfãos e contagem de bloqueios
```

### Consultas diretas via `mongosh` (somente leitura):
```javascript
use pibit_app_dev

// 1. Amostras sem animal correspondente (órfãs)
db.amostras.aggregate([
  { $lookup: { from: "animais", localField: "animal_id", foreignField: "_id", as: "a" } },
  { $match: { a: { $size: 0 } } },
  { $project: { _id: 1, animal_id: 1 } },
  { $limit: 20 }
])

// 2. Exames sem amostra correspondente (órfãos)
db.exames.aggregate([
  { $lookup: { from: "amostras", localField: "amostra_id", foreignField: "_id", as: "a" } },
  { $match: { a: { $size: 0 } } },
  { $project: { _id: 1, amostra_id: 1 } },
  { $limit: 20 }
])

// 3. Animais com maior número de amostras
db.amostras.aggregate([
  { $group: { _id: "$animal_id", n: { $sum: 1 } } },
  { $sort: { n: -1 } },
  { $limit: 10 }
])
```

---

## ⚡ 7. Inicialização, Índices e Saneamento (`setup_banco.py`)

### Passo 7.1. Conferir e Criar Índices

O MongoDB já garante unicidade nativa no campo `_id` de cada documento. O script confere os índices existentes e cria os índices recomendados para filtros e vínculos:

```bash
# 1. Simulação: confere índices existentes e lista o que precisa ser criado
python scripts/setup_banco.py

# 2. Criação real dos índices no banco configurado (dev por padrão)
python scripts/setup_banco.py --aplicar
```

#### Índices gerenciados:
- **Vínculos:** `amostras.animal_id`, `exames.amostra_id`.
- **Filtros e Consultas:**
  - `amostras`: `status_amostra`, `data_coleta_amostra`, `metodo_coleta`.
  - `exames`: `tipo_exame`, `teste_laboratorial`.
  - `animais`: `nome_comum`, `nome_cientifico`, `classe`, `microchip` (sparse), `id_hvu` (sparse).
  - `reagentes`: `data_validade`, `nome`.
  - `usuarios`: `matricula` (perfil).
- **Unicidade:** `usuarios.username` (unique), `usuarios.email` (unique).

---

### Passo 7.2. Rotina de Correção de Dados Antigos (`--corrigir`)

Antes de tornar novos campos e vínculos estritamente obrigatórios no sistema, execute a rotina de saneamento para tratar dados legados:

```bash
# 1. Simulação (mostra exatamente quantos documentos serão alterados)
python scripts/setup_banco.py --corrigir

# 2. Aplicação real das correções no ambiente de teste
python scripts/setup_banco.py --aplicar --corrigir

# 3. Conferência na auditoria
python scripts/auditar_banco.py
```

#### O que a rotina corrige automaticamente (idempotente e segura):
1. **Reagentes:** Sincroniza `quantidade` $\leftrightarrow$ `quantidade_unidade`.
2. **Animais:**
   - Migra `hvu` legado para `id_hvu`.
   - Recupera campos acentuados: `órgãos` $\rightarrow$ `orgao`, `funcão` $\rightarrow$ `funcao`, `observações` $\rightarrow$ `observacoes`.
   - Só remove o campo legado se o valor for idêntico ao destino; divergências são preservadas para revisão.
   - Calcula automaticamente `faixa_etaria` com base em `idade`.
   - Preenche `peso` ausente com `"Não aferido"`.
   - Preenche demais obrigatórios ausentes com `"Não informado"`.
3. **Amostras:**
   - Migra `data_coleta` $\rightarrow$ `data_coleta_amostra` e `local_coleta` $\rightarrow$ `local_coleta_amostra`.
   - **Regra de Disponibilidade:** Inicializa `status_amostra` ausente com `"Disponível"` ("toda amostra nasce Disponível"). Mapeia `"Consumida"` para `"Esgotada"`.
   - Preenche campos obrigatórios legados com `"Não informado"`.
4. **Exames:** Preenche campos obrigatórios legados (`kit_utilizado`, `protocolo_exame`, etc.) com `"Não informado"`.
5. **Reagentes:** Preenche `local_armazenamento` ausente com `"Não informado"`.
6. **Remoção de lixo:** Remove colunas anômalas `unnamed*` resultantes de importações de planilhas.
7. **Normalização de Tipos:** Converte identificadores numéricos (`int`, `float`, `Int64`) para `string` e remove espaços residuais.
8. **Auditoria de Perfis:** Identifica usuários com o perfil legado `"Bolsista UFPI"` para separação entre `"Bolsista PIBIC"` e `"Bolsista PIBIT"`.
   ```bash
   python scripts/setup_banco.py --aplicar --migrar-bolsistas-ufpi "Bolsista PIBIT"
   python scripts/setup_banco.py --aplicar --definir-perfil USUARIO "Bolsista PIBIC"
   ```

---

### Passo 7.3. Integridade Referencial e Junção de Dados

Para cumprir a regra de **bloqueio de exclusão quando há dependentes** e permitir a junção de cadastros duplicados:

```bash
# Mesclar dados de dois animais duplicados em um só (transfere amostras e exclui origem)
python scripts/setup_banco.py --mesclar-animais ID_ANTIGO ID_OFICIAL             # simulação
python scripts/setup_banco.py --aplicar --mesclar-animais ID_ANTIGO ID_OFICIAL   # efetivação

# Mesclar dados de duas amostras duplicadas em uma só (transfere exames e exclui origem)
python scripts/setup_banco.py --mesclar-amostras ID_ANTIGA ID_OFICIAL            # simulação
python scripts/setup_banco.py --aplicar --mesclar-amostras ID_ANTIGA ID_OFICIAL  # efetivação
```

---

## 🧬 8. Teste em Dados de Exemplo (`--seed`)

Popule o banco de desenvolvimento com registros controlados (`TESTE-*`):

```bash
# Popula dados de teste (só executa em bancos com sufixo _dev ou _test)
python scripts/setup_banco.py --aplicar --seed

# Re-executa auditoria para confirmar detecção dos dados e do vínculo quebrado proposital
python scripts/auditar_banco.py
```

- Cria `TESTE-ANM001`, `TESTE-AMS001`, `TESTE-EXM001` e `TESTE-REG001` perfeitamente vinculados.
- Cria intencionalmente `TESTE-AMS002` apontando para um animal inexistente (`NAO-EXISTE`) para comprovar que a auditoria detecta vínculos quebrados.
- Cria `TESTE-ANM002`, `TESTE-AMS003` e `TESTE-REG002` com campos legados para exercitar a rotina `--corrigir`.

---

## 🚀 9. Levar Mudanças para Produção

Depois de validar completamente no ambiente de teste `pibit_app_dev`:

1. **Gere um novo backup da produção** conforme a Seção 3.
2. **Execute a simulação na produção:**
   ```bash
   export MONGO_DB="pibit_app"
   python scripts/setup_banco.py --corrigir
   ```
3. **Aplique na produção com a salvaguarda explícita `--producao`:**
   ```bash
   python scripts/setup_banco.py --aplicar --producao --corrigir
   ```
4. **Rode a auditoria na produção:**
   ```bash
   python scripts/auditar_banco.py
   ```

---

## 🚑 10. Restauração e Recuperação em Produção (Disaster Recovery)

Se for necessário restaurar o banco de produção para um ponto de recuperação anterior:

```bash
# ATENÇÃO: A flag --drop apaga as coleções existentes antes de restaurar!
mongorestore \
  --uri="$MONGO_URI" \
  --gzip \
  --archive="scripts/resultados/pibit_app.archive" \
  --drop
```

> ⚠️ **Cuidado Extremo:** O parâmetro `--drop` deve ser utilizado exclusivamente em situações de desastre, rollback emergencial ou quando houver intenção explícita de sobrepor a base inteira.

---

## ✅ Critério de Pronto (Definition of Done)

O fluxo está aprovado quando qualquer colaborador da equipe consegue:

1. Executar o `mongorestore` com `--nsFrom="pibit_app.*" --nsTo="pibit_app_dev.*"` para subir uma cópia de testes sem encostar em produção.
2. Rodar `python scripts/auditar_banco.py` e obter o relatório sem falhas de conexão.
3. Rodar `python scripts/setup_banco.py --aplicar` para validar a conferência e aplicação de todos os índices.
4. Rodar `python scripts/setup_banco.py --aplicar --corrigir` para sanar todos os dados legados de forma idempotente e segura.
5. Rodar `python scripts/setup_banco.py --aplicar --seed` e comprovar a detecção de vínculos válidos e quebrados na auditoria.
6. Ter certeza de que os scripts **nunca alteram a produção por acidente**, pois exigem `--producao` expressamente.