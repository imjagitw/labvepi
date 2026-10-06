# 📦 Guia de Backup, Restauração, Auditoria e Organização do Banco de Dados (MongoDB)

Instruções completas para realizar cópia de segurança (*dump*), restauração (*restore*) para ambiente de testes, auditoria de dados, criação de índices, rotinas de correção e plano de recuperação para a base de dados do projeto **`pibit_app`**.

---

## 📋 1. Pré-requisitos

Certifique-se de ter o utilitário **MongoDB Database Tools** instalado em seu sistema operacional:

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
  Baixe o instalador no site oficial do [MongoDB Database Tools](https://www.mongodb.com/try/download/database-tools) e adicione o diretório `bin` às variáveis de ambiente (`PATH`).

Para validar a instalação:
```bash
mongodump --version
mongorestore --version
```

---

## 💾 Issue 1: Backup e Auditoria do Banco

> ⚠️ **Importante:** Todos os comandos neste guia devem ser executados a partir da **raiz do projeto** (`pibitapp/`).

### Passo 1. Gerar Backup (*Dump* da Produção)

Para exportar todas as coleções do banco de produção `pibit_app` para o arquivo de backup na pasta `backup/` a partir da raiz do projeto:

```bash
export MONGO_URI="mongodb+srv://USUARIO:SENHA@cluster.mongodb.net"

mongodump \
  --uri="$MONGO_URI" \
  --db="pibit_app" \
  --archive="scripts/resultados/pibit_app.archive" \
  --gzip
```

> 🔒 **Nota de Segurança:** O arquivo `scripts/resultados/pibit_app.archive` contém dados sensíveis e já está configurado no `.gitignore` para nunca ser enviado ao repositório Git.

---

### Passo 2. Restaurar o Backup em um Banco de Teste (`pibit_app_dev`)

Restaurar a base de produção em um banco de teste/desenvolvimento (`pibit_app_dev`) para auditar sem mexer na produção:

```bash
mongorestore \
  --uri="$MONGO_URI" \
  --gzip \
  --archive="scripts/resultados/pibit_app.archive" \
  --nsFrom="pibit_app.*" \
  --nsTo="pibit_app_dev.*"
```

---

### Passo 3. Rodar a Auditoria de Dados

Execute o script de auditoria no banco de desenvolvimento (idealmente com um usuário Atlas somente leitura):

```bash
export MONGO_URI="$MONGO_URI"
export MONGO_DB="pibit_app_dev"
python scripts/auditar_banco.py
```

#### O que o script de auditoria analisa:
O script mostra apenas nomes de campos, tipos e contagens, **nunca** exibindo valores pessoais. Ele cobre cada item:

1. **Coleções:** Contagem de documentos, índices e tipos de `_id` (`string` ou `ObjectId`).
2. **Vínculos Quebrados:** 
   - `amostras.animal_id` que não aponta para um animal.
   - `exames.amostra_id` que não aponta para uma amostra.
   - Separação entre "quebrado" (órfão) e "só bate como texto" (incompatibilidade de `ObjectId` contra `string`).
3. **Divergências do Código:**
   - `hvu` contra `id_hvu`;
   - `quantidade_unidade` contra `quantidade` (com contagem de reagentes que nunca aparecem nos alertas de baixo estoque);
   - `status` contra `status_amostra`;
   - `sangue_disponivel` contra `disponivel`;
   - Amostras com campo `exames` embutido;
   - Exames criados pelo `Editar_Amostra` com nome e sem `amostra_id`.
4. **Campos Obrigatórios:** Mapeamento dos campos obrigatórios realmente preenchidos em cada coleção.
5. **IDs Vazios:** Identificação de formulários de reagente e exame que removem o `_id` em branco, fazendo com que o MongoDB gere um `ObjectId` automático (contagem de quantos foram criados assim).
6. **Duplicidade de Usuários:** Checagem prévia de e-mails e usernames duplicados em `usuarios`, necessária antes da aplicação do índice único.

---

### Passo 4. Gerar o Resumo de Auditoria

Após executar o script de auditoria:

1. Abra o arquivo gerado em `scripts/resultados/relatorio_auditoria.json`.
2. Monte um resumo de 1 página contendo coleções, contagens, vínculos quebrados e divergências (o "retrato" necessário para a reunião).
3. ⚠️ **Atenção:** **Não versione** o arquivo `relatorio_auditoria.json` no Git, pois ele contém IDs de registros do banco.

---

### Passo 5. Reunião de Decisão com o Laboratório

Agende uma reunião com a equipe do laboratório e leve as seguintes pautas para deliberação e fechamento:

1. **Campos Obrigatórios:** Quais campos são obrigatórios em cada entidade. Hoje *exame* e *reagente* exigem quase tudo, mas o ID é opcional.
2. **Nomes Oficiais de Campos:** Confirmar a padronização (`hvu`, `quantidade` e `status_amostra` são as sugestões do script de correção).
3. **Permissões de Edição e Exclusão:** Quem pode editar e excluir exames e reagentes (hoje qualquer usuário logado exclui exame e reagente, e só o perfil *Professor* edita animal e amostra. Até decidirem, mantenha as restrições atuais).
4. **Tratamento de Vínculos Quebrados:** O que fazer com cada vínculo incorreto (corrigir o ID, apagar o registro ou aceitar como órfão).

> 📝 **Registro:** Registre todas as decisões formalmente no arquivo `docs/regras_dados.md`.

---

## 🛠️ Issue 2: Preparar e Organizar o Banco de Dados

### Passo 1. Ambientes Separados

Separe os ambientes garantindo que a aplicação saiba para qual banco apontar sem alterar código:

- **Produção (`pibit_app`):** Configurado na variável/Secrets do Streamlit Cloud.
- **Desenvolvimento (`pibit_app_dev`):** Pode ser o mesmo cluster ou um cluster gratuito à parte. Configurado em `.streamlit/secrets.toml` (que já está no `.gitignore`).

#### Configuração do `secrets.toml.example`:
Crie um modelo sem credenciais reais na raiz:

```toml
[mongo]
uri = "mongodb+srv://USUARIO:SENHA@cluster/..."
db  = "pibit_app_dev"
```

#### Alteração no código (`utils.py`):
Em `utils.connect_to_mongo()`, certifique-se de utilizar:

```python
def connect_to_mongo():
    client = get_mongo_client()
    nome_db = st.secrets["mongo"].get("db", "pibit_app")
    return client[nome_db]
```
Dessa forma, cada ambiente aponta para o seu banco sem qualquer alteração no código.

---

### Passo 2. Análise dos Índices Existentes

Verifique os índices existentes no relatório emitido pela auditoria. Como o `_id` de cada documento já possui índice único padrão do MongoDB, não é necessário criar índice extra para ele.

---

### Passo 3. Criação de Índices

Execute a rotina de criação de índices primeiramente como simulação e, em seguida, aplique no banco de desenvolvimento:

```bash
export MONGO_DB="pibit_app_dev"

# 1. Simulação (lista o que faria)
python scripts/setup_banco.py

# 2. Criação real dos índices
python scripts/setup_banco.py --aplicar
```

O script criará os seguintes índices:
- `amostras.animal_id`
- `exames.amostra_id`
- `animais.nome_comum`
- `animais.microchip`
- `animais.hvu`
- `reagentes.data_validade`
- Índices únicos em `usuarios.username` e `usuarios.email`

> 💡 **Nota:** Se a criação do índice único falhar devido a usuários duplicados, utilize a lista emitida no relatório de auditoria para sanar as duplicidades antes de aplicar novamente.

---

### Passo 4. Rotina de Correção de Dados Antigos

Execute o script de correção de dados legados no ambiente `_dev`:

```bash
python scripts/setup_banco.py --aplicar --corrigir
```

- Copia `quantidade_unidade` para `quantidade`, `id_hvu` para `hvu` e `status` para `status_amostra`, **apenas onde faltar o campo novo**.
- Esta rotina é **idempotente** (pode ser repetida sem efeitos colaterais).
- Teste sempre primeiro no `pibit_app_dev`. Vínculos quebrados ficam de fora nesta etapa de propósito, pois dependem das decisões da reunião com o laboratório.

---

### Passo 5. Dados de Exemplo e Teste (`--seed`)

Popule o banco de desenvolvimento com massa de testes:

```bash
python scripts/setup_banco.py --aplicar --seed
python scripts/auditar_banco.py
```

- O parâmetro `--seed` só roda em bancos cujos nomes terminam em `_dev` ou `_test`.
- Ele cria registros fictícios com o prefixo `TESTE-*`, incluindo intencionalmente uma amostra com vínculo quebrado para confirmar que a auditoria consegue detectá-la.

---

## 🚑 3. Restauração e Recuperação em Produção (Disaster Recovery)

Instruções para restaurar a produção em caso de problema ou necessidade de rollback:

```bash
export MONGO_URI="mongodb+srv://USUARIO:SENHA@cluster.mongodb.net"

mongorestore \
  --uri="$MONGO_URI" \
  --gzip \
  --archive="backup/pibit_app.archive" \
  --drop
```

> ⚠️ **ATENÇÃO:** O uso da flag `--drop` remove as coleções atuais no banco antes de restaurar o backup. Utilize com extrema cautela apenas quando necessário restaurar o estado limpo de produção.

---

## ✅ Critério de Pronto

O procedimento estará 100% pronto quando outra pessoa da equipe conseguir:
1. Subir o ambiente de testes (`pibit_app_dev`) executando o restore com `--nsFrom` e `--nsTo`;
2. Executar a auditoria e o setup do banco de testes;
3. Consultar coleções, schemas e vínculos quebrados **sem nunca tocar ou afetar o banco de produção**.