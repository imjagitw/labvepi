"""
Setup do Banco de Dados - LABVEPI (UFPI)
Implementa as regras definidas em 'Regras de Dados e Validação - LABVEPI.txt':
  1. Disponibilidade de Amostra: unificada em `status_amostra` [Disponível, Reservada, Em uso, Perdida, Esgotada].
     Toda amostra nasce "Disponível".
  2. Integridade Referencial: Bloqueio de exclusão caso haja dependentes (amostras vinculadas a animal, exames vinculados a amostra).
     Rotinas de mesclagem/junção de dois animais ou duas amostras em um só registro.
  3. Preenchimento de Campos Obrigatórios: Registros legados sem dados recebem "Não informado" ou "Não aferido" (peso).
  4. Perfis de Usuário: Separação de "Bolsista UFPI" em "Bolsista PIBIC" e "Bolsista PIBIT" e controle de permissões.

Por padrão: aponta para o banco de DESENVOLVIMENTO (pibit_app_dev) e roda em SIMULAÇÃO (dry-run, não grava nada).
Para gravar use --aplicar.
Gravar em PRODUÇÃO (pibit_app) exige, além de --aplicar, a flag explícita --producao.

Uso:
    python scripts/setup_banco.py --verificar-indices                 # índices existentes x esperados (leitura)
    python scripts/setup_banco.py --verificar-integridade             # vínculos órfãos e dependentes (leitura)
    python scripts/setup_banco.py                                     # simula a criação de índices
    python scripts/setup_banco.py --aplicar                           # cria índices no banco configurado
    python scripts/setup_banco.py --corrigir                          # simula saneamento e correções
    python scripts/setup_banco.py --aplicar --corrigir                # aplica correções de dados legados
    python scripts/setup_banco.py --aplicar --migrar-bolsistas-ufpi "Bolsista PIBIT"
    python scripts/setup_banco.py --aplicar --definir-perfil USUARIO "Bolsista PIBIC"
    python scripts/setup_banco.py --mesclar-animais ID1 ID2           # simula junção de animais
    python scripts/setup_banco.py --aplicar --mesclar-animais ID1 ID2 # efetiva junção
    python scripts/setup_banco.py --mesclar-amostras ID1 ID2          # simula junção de amostras
    python scripts/setup_banco.py --aplicar --mesclar-amostras ID1 ID2 # efetiva junção
    python scripts/setup_banco.py --aplicar --seed                    # dados de teste (só em *_dev ou *_test)
"""

import argparse
import re
import sys
from collections import Counter
from pymongo import ASCENDING

from _conexao import conectar, PROD_DB

# ==============================================================================
# REGRAS DE NEGÓCIO E PERMISSÕES (LABVEPI)
# ==============================================================================

STATUS_AMOSTRA_VALIDOS = [
    "Disponível",
    "Reservada",
    "Em uso",
    "Perdida",
    "Esgotada",
]

PERFIS_VALIDOS = [
    "Professor",
    "Mestrando",
    "Doutorando",
    "Bolsista Externo",
    "Bolsista PIBIC",
    "Bolsista PIBIT",
]

# Matriz de permissões segundo o documento de regras
PERMISSOES = {
    "animais": ["Professor", "Mestrando", "Doutorando", "Bolsista Externo", "Bolsista PIBIT"],
    "amostras": ["Professor", "Mestrando", "Doutorando", "Bolsista Externo", "Bolsista PIBIT"],
    "exames": ["Professor", "Bolsista Externo", "Bolsista PIBIT"],
    "reagentes": ["Professor", "Mestrando", "Doutorando", "Bolsista Externo", "Bolsista PIBIT"],
    "visualizar": PERFIS_VALIDOS,
}

# Campos obrigatórios segundo os formulários e regras vigentes
CAMPOS_OBRIGATORIOS = {
    "animais": [
        "classe", "nome_comum", "nome_cientifico", "sexo", "peso",
        "orgao", "status", "funcao", "local_origem", "faixa_etaria"
    ],
    "amostras": [
        "animal_id", "local_coleta_amostra", "data_coleta_amostra", "nome_coletor",
        "metodo_coleta", "condicao_amostra", "fase_amostra", "destino_amostra",
        "kit_utilizado", "caixa", "status_amostra"
    ],
    "exames": [
        "amostra_id", "tipo_exame", "teste_laboratorial", "laboratorio_realizador",
        "data_realizacao", "kit_utilizado", "resultado_detalhado",
        "responsavel_exame", "protocolo_exame"
    ],
    "reagentes": [
        "nome", "codigo", "numero_lote", "marca", "data_validade",
        "quantidade_unidade", "local_armazenamento"
    ],
}

# Índices estruturais, vínculos, filtros e unicidade
# Nota: O campo '_id' já possui unicidade nativa garantida no MongoDB em todas as coleções.
INDICES = [
    ("amostras", [("animal_id", ASCENDING)], {}),
    ("amostras", [("status_amostra", ASCENDING)], {}),
    ("amostras", [("data_coleta_amostra", ASCENDING)], {}),
    ("amostras", [("metodo_coleta", ASCENDING)], {}),
    ("exames", [("amostra_id", ASCENDING)], {}),
    ("exames", [("tipo_exame", ASCENDING)], {}),
    ("exames", [("teste_laboratorial", ASCENDING)], {}),
    ("animais", [("nome_comum", ASCENDING)], {}),
    ("animais", [("nome_cientifico", ASCENDING)], {}),
    ("animais", [("classe", ASCENDING)], {}),
    ("animais", [("microchip", ASCENDING)], {"sparse": True}),
    ("animais", [("id_hvu", ASCENDING)], {"sparse": True}),
    ("reagentes", [("data_validade", ASCENDING)], {}),
    ("reagentes", [("nome", ASCENDING)], {}),
    ("usuarios", [("username", ASCENDING)], {"unique": True}),
    ("usuarios", [("email", ASCENDING)], {"unique": True}),
    ("usuarios", [("matricula", ASCENDING)], {}),
]

# Campos que devem ser string/texto (códigos, IDs, observações); números reais ficam preservados
CAMPOS_TEXTO = {
    "animais": [
        "microchip", "id_hvu", "observacoes", "animal_id_projeto", "local_origem",
        "classe", "nome_comum", "nome_cientifico", "sexo", "status", "funcao",
        "orgao", "faixa_etaria", "idade", "suspeita_clinica"
    ],
    "amostras": [
        "animal_id", "caixa", "observacoes", "metodo_coleta", "local_coleta_amostra",
        "nome_coletor", "condicao_amostra", "fase_amostra", "destino_amostra",
        "kit_utilizado", "amostra_id_projeto", "status_amostra",
        "sangue_disponivel", "dna_disponivel", "rna_disponivel", "sequenciamento"
    ],
    "exames": [
        "amostra_id", "protocolo_exame", "observacoes", "observacoes_exame",
        "tipo_exame", "teste_laboratorial", "laboratorio_realizador",
        "resultado_detalhado", "responsavel_exame", "kit_utilizado"
    ],
    "reagentes": [
        "codigo", "numero_lote", "observacoes", "marca", "local_armazenamento",
        "etapa", "nome"
    ],
}

# Valores de preenchimento para campos obrigatórios ausentes (Regra 3)
PREENCHER = {
    "animais": {c: ("Não aferido" if c == "peso" else "Não informado")
                for c in CAMPOS_OBRIGATORIOS["animais"]},
    "amostras": {c: "Não informado" for c in CAMPOS_OBRIGATORIOS["amostras"]
                 if c not in ("animal_id", "status_amostra")}
                | {c: "Não informado" for c in
                   ("sangue_disponivel", "dna_disponivel", "rna_disponivel", "sequenciamento")},
    "exames": {c: "Não informado" for c in CAMPOS_OBRIGATORIOS["exames"]
               if c not in ("amostra_id", "tipo_exame", "teste_laboratorial", "resultado_detalhado")},
    "reagentes": {"local_armazenamento": "Não informado"},
}

# ==============================================================================
# FUNÇÕES UTILITÁRIAS
# ==============================================================================

def calcular_faixa_etaria(idade_str: str) -> str:
    """Calcula a faixa etária com base na string de idade (anos, meses, dias ou palavras-chave)."""
    if not idade_str or not isinstance(idade_str, str):
        return ""
    idade_clean = idade_str.strip().lower()
    if "filhote" in idade_clean:
        return "Filhote"
    if "juvenil" in idade_clean or "suvenil" in idade_clean:
        return "Juvenil"
    if "sub" in idade_clean:
        return "Sub Adulto"
    if "adulto" in idade_clean:
        return "Adulto"
    if "senil" in idade_clean or "idoso" in idade_clean:
        return "Senil"

    match = re.search(r"(\d+(?:[\.,]\d+)?)", idade_clean)
    if not match:
        return ""

    num_val = float(match.group(1).replace(",", "."))
    if any(unit in idade_clean for unit in ["mês", "mes", "meses", "m"]):
        anos = num_val / 12.0
    elif any(unit in idade_clean for unit in ["dia", "dias", "d"]):
        anos = num_val / 365.0
    elif any(unit in idade_clean for unit in ["semana", "semanas", "sem"]):
        anos = num_val / 52.0
    else:
        anos = num_val

    if anos < 1.0:
        return "Filhote"
    elif anos < 2.0:
        return "Juvenil"
    elif anos < 4.0:
        return "Sub Adulto"
    elif anos < 10.0:
        return "Adulto"
    else:
        return "Senil"


def eh_vazio(valor) -> bool:
    """Verifica se um valor está vazio, nulo ou é string vazia."""
    return valor is None or valor == "" or valor == [] or (isinstance(valor, float) and str(valor) == "nan")


def verificar_bloqueio_exclusao_animal(db, animal_id: str):
    """
    Regra 2: Bloquear exclusão de Animal caso haja amostras vinculadas.
    Retorna (pode_excluir: bool, motivo_ou_sucesso: str, count: int).
    """
    count = db["amostras"].count_documents({"animal_id": str(animal_id)})
    if count > 0:
        return False, f"BLOQUEADO: Animal '{animal_id}' possui {count} amostra(s) vinculada(s). Exclua ou transfira as amostras antes ou utilize a rotina de mesclagem.", count
    return True, f"OK: Animal '{animal_id}' não possui amostras vinculadas.", 0


def verificar_bloqueio_exclusao_amostra(db, amostra_id: str):
    """
    Regra 2: Bloquear exclusão de Amostra caso haja exames vinculados.
    Retorna (pode_excluir: bool, motivo_ou_sucesso: str, count: int).
    """
    count = db["exames"].count_documents({"amostra_id": str(amostra_id)})
    if count > 0:
        return False, f"BLOQUEADO: Amostra '{amostra_id}' possui {count} exame(s) vinculado(s). Exclua ou transfira os exames antes ou utilize a rotina de mesclagem.", count
    return True, f"OK: Amostra '{amostra_id}' não possui exames vinculados.", 0


def mesclar_animais(db, id_origem: str, id_destino: str, aplicar: bool = False):
    """
    Regra 2 (detalhe): Trata junção de dados de dois animais em um só.
    - Transfere todas as amostras vinculadas do animal de origem para o animal de destino.
    - Mescla dados do animal de origem nos campos em branco do animal de destino.
    - Registra a fusão nas observações do animal de destino.
    - Remove com segurança o animal de origem após a desvinculação completa.
    """
    doc_origem = db["animais"].find_one({"_id": str(id_origem)})
    doc_destino = db["animais"].find_one({"_id": str(id_destino)})

    if not doc_origem:
        print(f"  ! Erro na mesclagem: animal de origem '{id_origem}' não existe.")
        return False
    if not doc_destino:
        print(f"  ! Erro na mesclagem: animal de destino '{id_destino}' não existe.")
        return False

    amostras_vinculadas = list(db["amostras"].find({"animal_id": str(id_origem)}))
    print(f"\nMesclando Animal '{id_origem}' -> '{id_destino}':")
    print(f"- Amostras a transferir: {len(amostras_vinculadas)}")

    novos_campos = {}
    for k, v in doc_origem.items():
        if k == "_id":
            continue
        v_dest = doc_destino.get(k)
        if (eh_vazio(v_dest) or v_dest in ["Não informado", "Não aferido"]) and not eh_vazio(v):
            novos_campos[k] = v

    obs_atual = str(doc_destino.get("observacoes", "") or "").strip()
    nota_fusao = f"[Fusão: dados incorporados do animal legado {id_origem}]"
    if nota_fusao not in obs_atual:
        nova_obs = f"{obs_atual} | {nota_fusao}" if obs_atual else nota_fusao
        novos_campos["observacoes"] = nova_obs

    print(f"- Campos a mesclar no destino: {list(novos_campos.keys())}")
    print(f"- Animal de origem '{id_origem}' será removido após transferência das amostras.")

    if aplicar:
        if novos_campos:
            db["animais"].update_one({"_id": str(id_destino)}, {"$set": novos_campos})
        if amostras_vinculadas:
            db["amostras"].update_many({"animal_id": str(id_origem)}, {"$set": {"animal_id": str(id_destino)}})
        db["animais"].delete_one({"_id": str(id_origem)})
        print(f"  ✔ Sucesso: Animal '{id_origem}' mesclado em '{id_destino}' e removido com segurança.")
    else:
        print("  [Simulação] Nenhuma alteração gravada. Use --aplicar para efetivar.")
    return True


def mesclar_amostras(db, id_origem: str, id_destino: str, aplicar: bool = False):
    """
    Regra 2 (detalhe): Trata junção de dados de duas amostras em uma só.
    - Transfere todos os exames vinculados da amostra de origem para a amostra de destino.
    - Mescla dados da amostra de origem nos campos em branco da amostra de destino.
    - Registra a fusão nas observações da amostra de destino.
    - Remove com segurança a amostra de origem após a desvinculação completa.
    """
    doc_origem = db["amostras"].find_one({"_id": str(id_origem)})
    doc_destino = db["amostras"].find_one({"_id": str(id_destino)})

    if not doc_origem:
        print(f"  ! Erro na mesclagem: amostra de origem '{id_origem}' não existe.")
        return False
    if not doc_destino:
        print(f"  ! Erro na mesclagem: amostra de destino '{id_destino}' não existe.")
        return False

    exames_vinculados = list(db["exames"].find({"amostra_id": str(id_origem)}))
    print(f"\nMesclando Amostra '{id_origem}' -> '{id_destino}':")
    print(f"- Exames a transferir: {len(exames_vinculados)}")

    novos_campos = {}
    for k, v in doc_origem.items():
        if k in ["_id", "animal_id"]:
            continue
        v_dest = doc_destino.get(k)
        if (eh_vazio(v_dest) or v_dest in ["Não informado", "Não aferido"]) and not eh_vazio(v):
            novos_campos[k] = v

    obs_atual = str(doc_destino.get("observacoes", "") or "").strip()
    nota_fusao = f"[Fusão: dados incorporados da amostra legada {id_origem}]"
    if nota_fusao not in obs_atual:
        nova_obs = f"{obs_atual} | {nota_fusao}" if obs_atual else nota_fusao
        novos_campos["observacoes"] = nova_obs

    print(f"- Campos a mesclar no destino: {list(novos_campos.keys())}")
    print(f"- Amostra de origem '{id_origem}' será removida após transferência dos exames.")

    if aplicar:
        if novos_campos:
            db["amostras"].update_one({"_id": str(id_destino)}, {"$set": novos_campos})
        if exames_vinculados:
            db["exames"].update_many({"amostra_id": str(id_origem)}, {"$set": {"amostra_id": str(id_destino)}})
        db["amostras"].delete_one({"_id": str(id_origem)})
        print(f"  ✔ Sucesso: Amostra '{id_origem}' mesclada em '{id_destino}' e removida com segurança.")
    else:
        print("  [Simulação] Nenhuma alteração gravada. Use --aplicar para efetivar.")
    return True


def auditar_integridade(db):
    """Verifica vínculos órfãos e amostras/animais com registros dependentes."""
    print("\nAuditoria de Integridade Referencial:")
    ids_animais = set(a["_id"] for a in db["animais"].find({}, {"_id": 1}))
    ids_amostras = set(s["_id"] for s in db["amostras"].find({}, {"_id": 1}))

    amostras_orfas = list(db["amostras"].find({"animal_id": {"$nin": list(ids_animais)}}))
    exames_orfãos = list(db["exames"].find({"amostra_id": {"$nin": list(ids_amostras)}}))

    print(f"- Amostras com animal_id inexistente (órfãs): {len(amostras_orfas)}")
    print(f"- Exames com amostra_id inexistente (órfãos): {len(exames_orfãos)}")

    total_animais_com_amostras = len(db["amostras"].distinct("animal_id"))
    total_amostras_com_exames = len(db["exames"].distinct("amostra_id"))
    print(f"- Animais que possuem amostras vinculadas (exclusão bloqueada): {total_animais_com_amostras}")
    print(f"- Amostras que possuem exames vinculados (exclusão bloqueada): {total_amostras_com_exames}")


def verificar_indices(db):
    """Compara os índices existentes com os recomendados (somente leitura)."""
    print("\nConferência de índices (esperado x existente):")
    faltando = 0
    for col in sorted({c for c, _, _ in INDICES}):
        try:
            existentes = {tuple(i["key"].items()): i for i in db[col].list_indexes()}
        except Exception:
            existentes = {}
        for c, chave, opt in INDICES:
            if c != col:
                continue
            ex = existentes.get(tuple(chave))
            nome = f"{col}.{'+'.join(k for k, _ in chave)}"
            if ex is None:
                print(f"  ✗ FALTA        {nome} {opt or ''}")
                faltando += 1
            elif bool(ex.get("unique", False)) != bool(opt.get("unique", False)):
                print(f"  ! DIVERGENTE   {nome}: unique existente={ex.get('unique', False)} esperado={opt.get('unique', False)}")
                faltando += 1
            else:
                print(f"  ✔ ok           {nome}")
    print(f"  -> {faltando} índice(s) a criar/corrigir. (_id já é único por padrão no MongoDB.)")


def _contar_e_aplicar(db, col, filtro, update, descricao, aplicar):
    qtd = db[col].count_documents(filtro)
    print(f"• {descricao}: {qtd}")
    if aplicar and qtd:
        db[col].update_many(filtro, update)
    return qtd


def migrar_campo(db, col, origem, destino, aplicar):
    """
    Copia 'origem' -> 'destino' onde o destino não existe e remove 'origem' somente quando
    o valor é igual ao do destino. Conflitos (ambos existem e diferem) são mantidos para revisão.
    """
    q_mig = {origem: {"$exists": True}, destino: {"$exists": False}}
    n_mig = db[col].count_documents(q_mig)
    q_conf = {origem: {"$exists": True}, destino: {"$exists": True},
              "$expr": {"$ne": [f"${origem}", f"${destino}"]}}
    n_conf = db[col].count_documents(q_conf)
    extra = f" | conflitos mantidos p/ revisão: {n_conf}" if n_conf else ""
    print(f"• {col}: '{origem}' -> '{destino}': {n_mig} a migrar{extra}")
    if aplicar:
        if n_mig:
            db[col].update_many(q_mig, [{"$set": {destino: f"${origem}"}}])
        db[col].update_many(
            {origem: {"$exists": True}, destino: {"$exists": True},
             "$expr": {"$eq": [f"${origem}", f"${destino}"]}},
            {"$unset": {origem: ""}},
        )


def normalizar_status(db, aplicar):
    """Regra 1: 'Consumida' (legado) -> 'Esgotada'; reporta valores fora da lista oficial."""
    _contar_e_aplicar(db, "amostras", {"status_amostra": "Consumida"},
                      {"$set": {"status_amostra": "Esgotada"}},
                      "amostras com status 'Consumida' -> 'Esgotada'", aplicar)
    fora = db["amostras"].count_documents(
        {"status_amostra": {"$exists": True, "$nin": STATUS_AMOSTRA_VALIDOS + [None, ""]}})
    print(f"• amostras com status_amostra fora da lista oficial (revisar manualmente): {fora}")


def auditar_perfis(db, aplicar):
    """Regra 4: perfis oficiais e separação de 'Bolsista UFPI'."""
    print("\n--- Perfis de Usuário (Separação Bolsista PIBIC / Bolsista PIBIT) ---")
    legados = list(db["usuarios"].find({"matricula": "Bolsista UFPI"}, {"username": 1, "email": 1}))
    if legados:
        print(f"⚠️ {len(legados)} usuário(s) com 'Bolsista UFPI' (reclassificar em PIBIC ou PIBIT):")
        for u in legados:
            print(f"   - {u.get('username')} ({u.get('email', 'sem email')})")
        print("   Use --definir-perfil USUARIO PERFIL ou --migrar-bolsistas-ufpi PERFIL.")
    else:
        print("✔ Nenhum 'Bolsista UFPI' pendente.")
    _contar_e_aplicar(db, "usuarios", {"perfil": {"$exists": False}},
                      [{"$set": {"perfil": "$matricula"}}],
                      "usuários sem campo 'perfil' (copiado de 'matricula')", aplicar)


def preencher_ausentes(db, aplicar):
    """Regra 3: obrigatórios sem dado -> 'Não informado' / 'Não aferido'. Regra 1: status padrão."""
    print("\n--- Regras 1 e 3: status e campos obrigatórios ausentes ---")
    q_sem_status = {"$or": [{"status_amostra": {"$exists": False}},
                            {"status_amostra": None}, {"status_amostra": ""}]}
    _contar_e_aplicar(db, "amostras", q_sem_status, {"$set": {"status_amostra": "Disponível"}},
                      "amostras sem status_amostra -> 'Disponível'", aplicar)
    normalizar_status(db, aplicar)
    for col, campos in PREENCHER.items():
        for campo, valor in campos.items():
            q = {"$or": [{campo: {"$exists": False}}, {campo: None}, {campo: ""}]}
            _contar_e_aplicar(db, col, q, {"$set": {campo: valor}},
                              f"{col}.{campo} ausente -> '{valor}'", aplicar)


def corrigir_dados_legados(db, aplicar):
    """Higienização e conformidade com as regras do laboratório. Idempotente."""
    print("\n--- Higienização e Aplicação de Regras de Validação ---")

    # Reagentes: manter quantidade <-> quantidade_unidade sincronizadas
    _contar_e_aplicar(
        db, "reagentes",
        {"quantidade": {"$exists": False}, "quantidade_unidade": {"$exists": True}},
        [{"$set": {"quantidade": "$quantidade_unidade"}}],
        "reagentes sem 'quantidade'", aplicar)
    _contar_e_aplicar(
        db, "reagentes",
        {"quantidade_unidade": {"$exists": False}, "quantidade": {"$exists": True}},
        [{"$set": {"quantidade_unidade": "$quantidade"}}],
        "reagentes sem 'quantidade_unidade'", aplicar)

    # Nomes legados de campos
    for origem, destino in [("hvu", "id_hvu"), ("órgãos", "orgao"),
                            ("funcão", "funcao"), ("observações", "observacoes")]:
        migrar_campo(db, "animais", origem, destino, aplicar)
    for origem, destino in [("status", "status_amostra"), ("data_coleta", "data_coleta_amostra"),
                            ("local_coleta", "local_coleta_amostra")]:
        migrar_campo(db, "amostras", origem, destino, aplicar)

    # Lixo de importação (colunas 'unnamed*')
    for col in ["amostras", "animais", "exames", "reagentes"]:
        afetados = 0
        for doc in db[col].find():
            ruins = {k: "" for k in doc if str(k).lower().startswith("unnamed")}
            if ruins:
                afetados += 1
                if aplicar:
                    db[col].update_one({"_id": doc["_id"]}, {"$unset": ruins})
        print(f"• {col} com colunas 'unnamed*': {afetados}")

    # Tipos primitivos: códigos/textos gravados como int/float/Int64 -> str
    for col, campos in CAMPOS_TEXTO.items():
        corrigidos, detalhes = 0, Counter()
        for doc in db[col].find():
            sets = {}
            for c in campos:
                val = doc.get(c)
                if val is None:
                    continue
                if not isinstance(val, str):
                    sets[c] = str(int(val)) if isinstance(val, float) and val.is_integer() else str(val).strip()
                elif val != val.strip():
                    sets[c] = val.strip()
                else:
                    continue
                detalhes[c] += 1
            if sets:
                corrigidos += 1
                if aplicar:
                    db[col].update_one({"_id": doc["_id"]}, {"$set": sets})
        print(f"• {col}: tipos/espaços corrigidos em {corrigidos} docs {dict(detalhes) or ''}")

    # Faixa etária derivada da idade (só onde falta)
    q = {"idade": {"$exists": True, "$nin": [None, ""]},
         "$or": [{"faixa_etaria": {"$exists": False}}, {"faixa_etaria": {"$in": [None, "", "Não Informado", "Não informado"]}}]}
    calculados = 0
    for doc in db["animais"].find(q):
        faixa = calcular_faixa_etaria(doc.get("idade", ""))
        if faixa:
            calculados += 1
            if aplicar:
                db["animais"].update_one({"_id": doc["_id"]}, {"$set": {"faixa_etaria": faixa}})
    print(f"• animais com faixa_etaria calculada a partir de 'idade': {calculados}")

    preencher_ausentes(db, aplicar)
    auditar_perfis(db, aplicar)


def criar_seed(db):
    """Dados de exemplo (apenas *_dev / *_test). Inclui casos legados para exercitar --corrigir."""
    def up(col, _id, dados):
        db[col].update_one({"_id": _id}, {"$set": dados}, upsert=True)

    up("animais", "TESTE-ANM001", {
        "nome_comum": "Sagui", "nome_cientifico": "Callithrix jacchus", "classe": "Mamífero",
        "sexo": "Macho", "peso": 0.3, "orgao": "UFPI", "status": "Cativeiro", "funcao": "Outros",
        "local_origem": "Teresina", "faixa_etaria": "Adulto", "id_hvu": "H-1",
        "observacoes": "Exemplo de animal padrão"})
    up("amostras", "TESTE-AMS001", {
        "animal_id": "TESTE-ANM001", "metodo_coleta": "Sangue", "data_coleta_amostra": "2026-01-10",
        "status_amostra": "Disponível", "local_coleta_amostra": "Lab. Virologia",
        "nome_coletor": "Pesquisador Teste", "condicao_amostra": "Refrigerada",
        "fase_amostra": "Extração", "destino_amostra": "LAB VIGILÂNCIA DE EPIZOOTIAS - UFPI",
        "kit_utilizado": "QIAamp Viral RNA Mini Kit", "caixa": "Freezer 1 / Caixa A"})
    up("exames", "TESTE-EXM001", {
        "amostra_id": "TESTE-AMS001", "tipo_exame": "RAIVA", "teste_laboratorial": "PCR",
        "resultado_detalhado": "Negativo", "laboratorio_realizador": "Lab. Virologia UFPI",
        "data_realizacao": "2026-01-12", "kit_utilizado": "Kit Raiva PCR",
        "responsavel_exame": "Dr. Teste", "protocolo_exame": "PROT-001"})
    up("reagentes", "TESTE-REG001", {
        "nome": "Kit teste", "codigo": "REG-TEST-01", "numero_lote": "LOTE-2026", "marca": "Qiagen",
        "quantidade": 5, "quantidade_unidade": 5, "data_validade": "2026-12-20",
        "local_armazenamento": "Freezer 1"})

    # Casos propositalmente legados e com erro para testar --corrigir e integridade
    up("animais", "TESTE-ANM002", {
        "nome_comum": "Cachorro-do-mato", "hvu": 12345, "microchip": 9876543210,
        "órgãos": "UFPI", "funcão": "PET", "observações": 7, "idade": "18 meses",
        "unnamed:_1": "lixo"})
    up("amostras", "TESTE-AMS003", {
        "animal_id": "TESTE-ANM002", "metodo_coleta": "Fezes", "data_coleta": "2025-03-01",
        "local_coleta": "Campo", "status": "Em uso"})
    up("amostras", "TESTE-AMS002", {
        "animal_id": "NAO-EXISTE", "metodo_coleta": "Fezes", "status_amostra": "Disponível"})
    up("reagentes", "TESTE-REG002", {
        "nome": "Reagente legado", "codigo": "REG-TEST-02", "numero_lote": "L-1", "marca": "X",
        "quantidade": 1, "data_validade": "2026-10-30"})
    print("✔ Registros TESTE-* criados (inclui legados e TESTE-AMS002 com vínculo quebrado proposital).")


# ==============================================================================
# FLUXO PRINCIPAL
# ==============================================================================

def main():
    p = argparse.ArgumentParser(description="Configuração e Manutenção do Banco LABVEPI")
    p.add_argument("--aplicar", action="store_true", help="Grava alterações no banco (padrão: simulação)")
    p.add_argument("--producao", action="store_true", help="Permite --aplicar no banco de PRODUÇÃO (pibit_app)")
    p.add_argument("--seed", action="store_true", help="Insere dados de exemplo (apenas bancos _dev ou _test)")
    p.add_argument("--corrigir", action="store_true", help="Executa rotinas de higienização e conformidade com as regras")
    p.add_argument("--migrar-bolsistas-ufpi", metavar="NOVO_PERFIL", help="Migra perfis legados 'Bolsista UFPI' para 'Bolsista PIBIC' ou 'Bolsista PIBIT'")
    p.add_argument("--definir-perfil", nargs=2, metavar=("USERNAME", "PERFIL"), help="Atualiza perfil/matrícula de um usuário específico")
    p.add_argument("--verificar-indices", action="store_true", help="Compara índices existentes x esperados (somente leitura)")
    p.add_argument("--verificar-integridade", action="store_true", help="Audita chaves estrangeiras e registros dependentes (somente leitura)")
    p.add_argument("--mesclar-animais", nargs=2, metavar=("ORIGEM", "DESTINO"), help="Une dois animais em um registro só")
    p.add_argument("--mesclar-amostras", nargs=2, metavar=("ORIGEM", "DESTINO"), help="Une duas amostras em um registro só")
    args = p.parse_args()

    db, nome_db = conectar()

    # Trava de segurança para produção
    if args.aplicar and nome_db == PROD_DB and not args.producao:
        sys.exit(f"Recusado: '{nome_db}' é o banco de PRODUÇÃO. Valide antes em pibit_app_dev, "
                 "faça backup e só então repita com --aplicar --producao.")

    modo = "APLICAR (GRAVAÇÃO)" if args.aplicar else "SIMULAÇÃO (DRY-RUN)"
    print("=" * 60)
    print(f" Banco: {nome_db} | Modo: {modo}")
    print("=" * 60)

    # 1. Operações Pontuais: Mesclagem
    if args.mesclar_animais:
        mesclar_animais(db, *args.mesclar_animais, aplicar=args.aplicar)
        return
    if args.mesclar_amostras:
        mesclar_amostras(db, *args.mesclar_amostras, aplicar=args.aplicar)
        return

    # 2. Gestão de Perfis de Usuário
    if args.definir_perfil:
        user, perfil = args.definir_perfil
        if perfil not in PERFIS_VALIDOS:
            sys.exit(f"Perfil inválido. Use um de: {PERFIS_VALIDOS}")
        if not db["usuarios"].find_one({"username": user}):
            sys.exit(f"Usuário '{user}' não encontrado.")
        print(f"Perfil de '{user}' -> '{perfil}'" + ("" if args.aplicar else " [simulação]"))
        if args.aplicar:
            db["usuarios"].update_one({"username": user}, {"$set": {"matricula": perfil, "perfil": perfil}})
            print("  ✔ Perfil atualizado com sucesso.")
        return

    if args.migrar_bolsistas_ufpi:
        perfil = args.migrar_bolsistas_ufpi
        if perfil not in ("Bolsista PIBIC", "Bolsista PIBIT"):
            sys.exit("Perfil inválido. Escolha entre 'Bolsista PIBIC' e 'Bolsista PIBIT'.")
        _contar_e_aplicar(db, "usuarios", {"matricula": "Bolsista UFPI"},
                          {"$set": {"matricula": perfil, "perfil": perfil}},
                          f"usuários 'Bolsista UFPI' -> '{perfil}'", args.aplicar)
        return

    # 3. Auditorias Somente-Leitura
    if args.verificar_indices:
        verificar_indices(db)
    if args.verificar_integridade:
        auditar_integridade(db)
    if (args.verificar_indices or args.verificar_integridade) and not (
            args.aplicar or args.corrigir or args.seed):
        return

    # 4. Criação de Índices
    print("\n--- Criação / Conferência de Índices ---")
    for col, chave, opt in INDICES:
        print(f"- {col}: {chave} {opt or ''}")
        if args.aplicar:
            try:
                db[col].create_index(chave, **opt)
            except Exception as e:
                print(f"  ! Falhou ao criar índice: {e}")

    # 5. Higienização e Correção de Dados Legados
    if args.corrigir:
        corrigir_dados_legados(db, args.aplicar)

    # 6. Seed de Dados de Exemplo
    if args.seed:
        if not (nome_db.endswith("_dev") or nome_db.endswith("_test")):
            sys.exit("Recusado: --seed só pode ser executado em bancos com sufixo _dev ou _test.")
        if not args.aplicar:
            print("\n[Simulação] --seed só grava se acompanhado de --aplicar.")
        else:
            print("\n--- Dados de Exemplo (--seed) ---")
            criar_seed(db)

    print("\nExecução concluída." + ("" if args.aplicar else " Nada foi gravado (simulação)."))


if __name__ == "__main__":
    main()