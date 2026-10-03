# 📋 Regras de Dados e Validação - LABVEPI

**Data da Reunião:** DD/MM/AAAA
**Participantes:** [Preencher com os nomes]

Este documento define as regras de negócio, padronização de nomenclatura, permissões de acesso e tratamento de dados legados do sistema LABVEPI.

## 1. Padronização de Nomenclatura (Campos Oficiais)
Define qual nome de campo será adotado no banco de dados e no código para evitar duplicidade e bugs (como o problema dos alertas de estoque).

| Coleção | Conflito Encontrado | Sugestão do Script | Decisão Final (A preencher) |
| :--- | :--- | :--- | :--- |
| **Animais** | `id_hvu` vs `hvu` | Adotar **`hvu`** | [ ] Adotar `hvu` <br> [ ] Adotar `id_hvu` |
| **Amostras** | `status` vs `status_amostra` | Adotar **`status_amostra`** | [ ] Adotar `status_amostra`<br> [ ] Adotar `status` |
| **Amostras** | `sangue_disponivel` vs `disponivel` | Adotar **`sangue_disponivel`** | [ ] Adotar `sangue_disponivel`<br> [ ] Adotar `disponivel` |
| **Reagentes** | `quantidade_unidade` vs `quantidade` | Adotar **`quantidade`** | [ ] Adotar `quantidade`<br> [ ] Adotar `quantidade_unidade` |

*Nota pós-reunião: O script de correção (Issue 2) usará as decisões acima para migrar os dados antigos.*

---

## 2. Campos Obrigatórios (Validação de Formulários)
Define quais dados não podem, sob nenhuma hipótese, ficar em branco no momento do cadastro.

| Coleção | Situação Atual / Problema | Opções de Decisão | Decisão Final |
| :--- | :--- | :--- | :--- |
| **Reagentes** | Exige quase tudo, mas o ID interno/código é opcional. Quando em branco, o Mongo gera um `ObjectId` aleatório. | [ ] Tornar o ID obrigatório (usuário digita).<br> [ ] Manter opcional (sistema gera automático). | _________________ |
| **Exames** | O ID do exame é opcional. Quando em branco, o Mongo gera um `ObjectId` aleatório. | [ ] Tornar o ID obrigatório (usuário digita).<br> [ ] Manter opcional (sistema gera automático). | _________________ |
| **Animais** | (Revisão geral) Quais campos *podem* ficar vazios se o animal chegar em emergência? | [ ] Manter obrigatoriedade estrita atual.<br> [ ] Flexibilizar campos: _______ | _________________ |

---

## 3. Controle de Acesso e Permissões (Edição e Exclusão)
Atualmente, apenas usuários com perfil de **Professor** podem editar e excluir **Animais** e **Amostras**. Contudo, não há restrição para Exames e Reagentes.

| Módulo / Ação | Situação Atual | Opções de Decisão (Perfis) | Decisão Final |
| :--- | :--- | :--- | :--- |
| **Editar/Excluir Exames** | Qualquer usuário logado pode editar/excluir. | [ ] Restringir apenas a **Professor**.<br> [ ] Permitir para Professor, Mestrando e Doutorando.<br> [ ] Manter liberado para todos (Bolsistas inclusos). | _________________ |
| **Editar/Excluir Reagentes** | Qualquer usuário logado altera quantidade e exclui. | [ ] Restringir apenas a **Professor**.<br> [ ] Permitir para Professor, Mestrando e Doutorando.<br> [ ] Manter liberado para todos. | _________________ |
| **Editar Amostra** | Restrito a **Professor**. | [ ] Manter restrito a Professor.<br> [ ] Expandir para outros níveis (Ex: Pós-graduandos). | _________________ |

*(Perfis disponíveis no sistema: Professor, Mestrando, Doutorando, Bolsista UFPI, Bolsista Externo)*.

---

## 4. Tratamento de Vínculos Quebrados (Dados Órfãos)
Como lidar com inconsistências históricas no banco de dados (ex: registros que perderam a referência de origem).

| Tipo de Inconsistência | Origem do Problema | Opções de Tratamento | Decisão Final |
| :--- | :--- | :--- | :--- |
| **Exames sem Amostra** (`amostra_id` quebrado) | Exames criados pela tela *Editar_Amostra* foram salvos apenas com o nome, sem associar o ID da amostra. | [ ] **Corrigir:** Pesquisar em prontuários e vincular manualmente.<br> [ ] **Aceitar:** Manter no banco como órfão (com uma flag de "inconsistente").<br> [ ] **Apagar:** Excluir do banco se não puder ser rastreado. | _________________ |
| **Amostras sem Animal** (`animal_id` quebrado) | Erros de digitação antigos ou exclusão do registro do animal sem apagar a amostra. | [ ] **Corrigir:** Tentar localizar o animal correto no HVU.<br> [ ] **Aceitar:** Manter no estoque, mas sem vínculo biológico.<br> [ ] **Apagar:** Descartar o registro virtual. | _________________ |
| **Amostras com Exames embutidos** | Código antigo gravava exames dentro do documento da amostra em vez de criar na coleção separada. | [ ] **Migrar:** Script deve extrair e criar na coleção de Exames.<br> [ ] **Ignorar:** Deixar como texto morto no documento antigo. | _________________ |