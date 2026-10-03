# 📦 Guia de Backup e Restauração do Banco de Dados (MongoDB)

Instruções para realizar cópia de segurança (*dump*) e restauração (*restore*) da base de dados **`pibit_app`** utilizando as ferramentas oficiais do MongoDB (`mongodump` e `mongorestore`).

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

## 💾 2. Gerar Backup (*Dump*)

Para exportar todas as coleções do banco `pibit_app` para um arquivo único compactado em formato de arquivo (`.archive`):

```bash
mongodump \
  --uri="URI_DO_BANCO_ORIGEM" \
  --db="pibit_app" \
  --archive="scripts/resultados/pibit_app.archive"
```

> 💡 **Nota:** Se você já estiver executando o comando a partir do diretório `scripts/resultados/`, ajuste o caminho para `--archive="pibit_app.archive"`.

### Gerar com compressão adicional (Gzip)
Recomendado para otimizar o espaço em disco caso a base cresça:
```bash
mongodump \
  --uri="URI_DO_BANCO_ORIGEM" \
  --db="pibit_app" \
  --archive="scripts/resultados/pibit_app.archive" \
  --gzip
```

---

## 🔄 3. Restaurar Backup (*Restore*)

Para restaurar as coleções contidas no arquivo para uma nova instância do MongoDB:

```bash
mongorestore \
  --uri="SUA_NOVA_URI" \
  --archive="scripts/resultados/pibit_app.archive"
```

> ⚠️ Caso tenha utilizado a flag `--gzip` na geração do backup, lembre-se de adicionar `--gzip` também no comando de restauração.

### Substituir coleções existentes (`--drop`)
Por padrão, o `mongorestore` não deleta documentos já existentes na base de destino. Para sobrescrever e recriar as coleções do zero (evitando conflitos de chave duplicada como `_id`):
```bash
mongorestore \
  --uri="SUA_NOVA_URI" \
  --archive="scripts/resultados/pibit_app.archive" \
  --drop
```

### Restaurar para um banco com nome diferente
Caso queira restaurar os dados em um banco de desenvolvimento/teste (ex.: `pibit_app_dev`):
```bash
mongorestore \
  --uri="SUA_NOVA_URI" \
  --archive="scripts/resultados/pibit_app.archive" \
  --nsFrom="pibit_app.*" \
  --nsTo="pibit_app_dev.*"
```

---

## 🔒 4. Boas Práticas e Segurança

1. **Evite senhas no histórico:** Em vez de passar a URI com usuário e senha diretamente no comando (onde fica gravada no histórico do bash), use a variável de ambiente:
   ```bash
   export MONGO_URI="mongodb+srv://<usuario>:<senha>@cluster.mongodb.net"
   
   # Gerar backup
   mongodump --uri="$MONGO_URI" --db="pibit_app" --archive="scripts/resultados/pibit_app.archive"
   
   # Restaurar backup
   mongorestore --uri="$MONGO_URI" --archive="scripts/resultados/pibit_app.archive"
   ```

2. **Atenção aos arquivos gerados:**
   - O arquivo `backup/pibit_app.archive` contém dados sensíveis (usuários, hashes de senhas e registros do sistema) e **já está configurado no `.gitignore`** para não ser versionado no repositório Git.
   - Guarde os arquivos de backup em local seguro e protegido.
  --archive="pibit_app.archive"