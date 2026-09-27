import streamlit as st
from pymongo import MongoClient
import os

# Função utilitária para exibir campos preenchidos
def exibir_campos(campos):
    for campo, valor in campos.items():
        if valor not in ('Não informado', '', None, 'Nenhuma'):
            st.markdown(f"**{campo}:** {valor}")

# Conexão segura com MongoDB
from utils import connect_to_mongo

db = connect_to_mongo()
animais_col = db['animais']
amostras_col = db['amostras']
exames_col = db['exames']
reagentes_col = db['reagentes']

def carregar_animais_mongo():
    try:
        return list(animais_col.find())
    except Exception as e:
        st.error(f"Erro ao carregar animais: {e}")
        return []

def carregar_amostras_mongo():
    try:
        return list(amostras_col.find())
    except Exception as e:
        st.error(f"Erro ao carregar amostras: {e}")
        return []

def carregar_exames_mongo():
    try:
        return list(exames_col.find())
    except Exception as e:
        st.error(f"Erro ao carregar exames: {e}")
        return []

def carregar_reagentes_mongo():
    try:
        return list(reagentes_col.find())
    except Exception as e:
        st.error(f"Erro ao carregar reagentes: {e}")
        return []

st.title("Registros do Sistema")

tab1, tab2, tab3, tab4 = st.tabs(
    ["Animais", "Amostras", "Exames", "Reagentes"])

# helper: transforma chave em rótulo legível
def _prettify(key: str) -> str:
    return key.replace('_', ' ').capitalize()

# helper: exibe todos os campos preenchidos de um documento (somente non-empty)
def display_document(doc: dict, title: str = None):
    if title:
        st.subheader(title)
    if not doc:
        st.info("Registro não encontrado.")
        return
    # exibir _id primeiro
    if '_id' in doc and doc['_id'] not in (None, '', []):
        st.markdown(f"**ID Interno:** `{doc['_id']}`")
    for k, v in doc.items():
        if k == '_id':
            continue
        if v in (None, '', [], {}, 'Não informado', 'Nenhuma'):
            continue
        # formatar listas e dicts
        if isinstance(v, list):
            v = ', '.join(map(str, v)) if v else v
        elif isinstance(v, dict):
            v = ', '.join(f"{_prettify(kk)}: {vv}" for kk,
                          vv in v.items() if vv not in (None, '', []))
        st.markdown(f"**{_prettify(k)}:** {v}")


# ---------------- TAB 1: Animais ----------------
with tab1:
    st.header("Animais Registrados")
    
    col_busca, col_ordem, col_qtd = st.columns([4, 2, 1])
    with col_busca:
        busca = st.text_input(
            "Buscar animal por nome, microchip ou ID HVU:", key="busca_animal_input")
    with col_ordem:
        ordem_animal = st.selectbox(
            "Ordem de exibição",
            ["Últimos adicionados", "Primeiros adicionados"],
            key="ordem_animal"
        )
    with col_qtd:
        por_pagina_animal = st.selectbox(
            "Por página",
            [5, 10, 20, 50, 100],
            index=1,
            key="por_pagina_animal"
        )
    
    animais = carregar_animais_mongo()
    amostras = carregar_amostras_mongo()

    # Filtro de busca incluindo o campo id_hvu
    if busca:
        termo = busca.lower()
        animais = [
            a for a in animais
            if termo in str(a.get('nome_comum', '')).lower()
            or termo in str(a.get('nome_cientifico', '')).lower()
            or termo in str(a.get('microchip', '')).lower()
            or termo in str(a.get('id_hvu', '')).lower()
            or termo in str(a.get('_id', '')).lower()
        ]

    # Ordenação
    if ordem_animal == "Últimos adicionados":
        animais = list(reversed(animais))

    # Paginação
    por_pagina = por_pagina_animal
    total = len(animais)
    max_paginas = max(1, (total + por_pagina - 1) // por_pagina)

    if not animais:
        st.info("Nenhum animal encontrado com este critério.")
    else:
        list_container_animais = st.container()

        col_espaco, col_pag = st.columns([2, 1])
        with col_pag:
            page = st.pagination(num_pages=max_paginas, key="pagina_animal")
            # Ajuste da exibição dos números
            inicio = (page - 1) * por_pagina
            fim = inicio + por_pagina
            st.caption(
                f"Mostrando {inicio + 1} a {min(fim, total)} de {total} animais (Página {page} de {max_paginas})"
            )
        inicio = (page - 1) * por_pagina
        fim = inicio + por_pagina
        animais_pagina = animais[inicio:fim]

        with list_container_animais:
            for animal in animais_pagina:
                # Título do expander exibindo ID HVU para facilitar identificação
                label_hvu = f" | HVU: {animal.get('id_hvu')}" if animal.get('id_hvu') else ""
                with st.expander(f"{animal.get('nome_comum', 'Sem nome')} ({animal.get('_id')}){label_hvu}", expanded=False):
                    display_document(animal, title="Dados do Animal")
                    # Apenas Professores podem editar animais
                    if st.session_state.get('matricula') == 'Professor':
                        if st.button("Editar animal", key=f"editar_animal_{animal.get('_id')}"):
                            flag = f"editando_{animal.get('_id')}"
                            st.session_state[flag] = not st.session_state.get(flag, False)

                        if st.session_state.get(f"editando_{animal.get('_id')}"):
                            st.subheader("Editar Dados do Animal")
                            with st.form(key=f"form_editar_animal_{animal.get('_id')}"):

                                col1, col2 = st.columns(2)
                                with col1:
                                    novo_nome_comum = st.text_input("Nome Comum", value=animal.get("nome_comum", ""))
                                    novo_nome_cientifico = st.text_input("Nome Científico", value=animal.get("nome_cientifico", ""))
                                    novo_id_projeto = st.text_input("ID do Projeto", value=animal.get("animal_id_projeto", ""))
                                    novo_hvu = st.text_input("ID do HVU", value=animal.get("hvu", ""))
                                    novo_microchip = st.text_input("Microchip", value=animal.get("microchip", ""))
                                    novo_local_origem = st.text_input("Local de Origem", value=animal.get("local_origem", ""))
                                    nova_idade = st.text_input("Idade", value=animal.get("idade", ""))
                                    nova_suspeita = st.text_input("Suspeita Clínica", value=animal.get("suspeita_clinica", ""))

                                with col2:
                                    sexo_opts = ["", "Macho", "Fêmea", "Desconhecido"]
                                    sexo_atual = animal.get("sexo", "")
                                    novo_sexo = st.selectbox("Sexo", sexo_opts,
                                        index=sexo_opts.index(sexo_atual) if sexo_atual in sexo_opts else 0)

                                    orgao_opts = ['UFPI', 'NEPPAS', 'IBAMA - CETAS - PI', 'IBAMA - CETAS - CE',
                                                  'IBAMA - CETAS - RN', 'SEMARH - CETAS - PI', 'UFPA', 'UFRR',
                                                  'UFAC', 'UFOB', 'DSEI LESTE - AM', 'ZOOLOGICO -PI', 'PARTICULAR', 'Outro']
                                    orgao_atual = animal.get("orgao", "UFPI")
                                    novo_orgao = st.selectbox("Órgão de Origem", orgao_opts,
                                        index=orgao_opts.index(orgao_atual) if orgao_atual in orgao_opts else 0)

                                    status_opts = ["", "Vida livre", "Cativeiro"]
                                    status_atual = animal.get("status", "")
                                    novo_status = st.selectbox("Status do Animal", status_opts,
                                        index=status_opts.index(status_atual) if status_atual in status_opts else 0)

                                    funcao_opts = ["PET", "Trabalho", "Lazer", "Outros"]
                                    funcao_atual = animal.get("funcao", "Outros")
                                    nova_funcao = st.selectbox("Função", funcao_opts,
                                        index=funcao_opts.index(funcao_atual) if funcao_atual in funcao_opts else 3)

                                    faixa_opts = ["Filhote", "Suvenil", " Sub Adulto", "Adulto", "Senil", "Não Informado"]
                                    faixa_atual = animal.get("faixa_etaria", "Não Informado")
                                    nova_faixa = st.selectbox("Faixa Etária", faixa_opts,
                                        index=faixa_opts.index(faixa_atual) if faixa_atual in faixa_opts else 5)

                                    classe_opts = ["Ave", "Mamífero", "Répteis", " Anfíbios", "Peixes"]
                                    classe_atual = animal.get("classe", "")
                                    nova_classe = st.selectbox("Classe", classe_opts,
                                        index=classe_opts.index(classe_atual) if classe_atual in classe_opts else 0)

                                    novo_peso = st.number_input("Peso (kg)", min_value=0.0, format="%.2f", step=0.01,
                                        value=float(animal.get("peso", 0.0)) if isinstance(animal.get("peso"), (int, float)) else 0.0)

                                novas_obs = st.text_area("Observações", value=animal.get("observacoes", ""))

                                col_s, col_c = st.columns(2)
                                with col_s:
                                    salvar = st.form_submit_button("Salvar alterações")
                                with col_c:
                                    cancelar = st.form_submit_button("Cancelar")

                                if salvar:
                                    update_data = {
                                        "nome_comum": novo_nome_comum,
                                        "nome_cientifico": novo_nome_cientifico,
                                        "animal_id_projeto": novo_id_projeto,
                                        "hvu": novo_hvu,
                                        "microchip": novo_microchip,
                                        "local_origem": novo_local_origem,
                                        "idade": nova_idade,
                                        "suspeita_clinica": nova_suspeita,
                                        "sexo": novo_sexo,
                                        "orgao": novo_orgao,
                                        "status": novo_status,
                                        "funcao": nova_funcao,
                                        "faixa_etaria": nova_faixa,
                                        "classe": nova_classe,
                                        "peso": novo_peso,
                                        "observacoes": novas_obs,
                                    }
                                    update_data = {k: v for k, v in update_data.items() if v not in (None, "", [])}
                                    animais_col.update_one({"_id": animal["_id"]}, {"$set": update_data})
                                    st.success("✅ Animal atualizado com sucesso!")
                                    st.session_state[f"editando_{animal.get('_id')}"] = False
                                    st.rerun()

                                if cancelar:
                                    st.session_state[f"editando_{animal.get('_id')}"] = False
                                    st.rerun()

                    st.write("---")
                    st.subheader("Amostras Coletadas:")
                    amostras_do_animal = [a for a in amostras if a.get(
                        'animal_id') == animal.get('_id')]
                    if amostras_do_animal:
                        for amostra in amostras_do_animal:
                            st.markdown(
                                f"**Amostra:** `{amostra.get('_id')}` — {_prettify('metodo_coleta')}: {amostra.get('metodo_coleta','Não informado')}")
                            if st.button("Ver detalhes da amostra", key=f"ver_am_{amostra.get('_id')}_{animal.get('_id')}"):
                                display_document(
                                    amostra, title=f"Detalhes da Amostra {amostra.get('_id')}")
                    else:
                        st.info("Nenhuma amostra para este animal ainda.")
                    
                    if st.session_state.get('matricula') == 'Professor':
                        st.markdown("---")
                        st.warning("Esta ação é irreversível.")
                        if st.button("Confirmar exclusão", key=f"del_animal_{animal.get('_id')}"):
                            animais_col.delete_one({"_id": animal['_id']})
                            st.success("Animal excluído! Recarregue a página.")
                            st.rerun()  

# ---------------- TAB 2: Amostras ----------------
with tab2:
    st.header("Amostras Cadastradas")
    col_busca, col_ordem, col_qtd = st.columns([4, 2, 1])
    with col_busca:
        busca_amostra = st.text_input(
            "Buscar amostra por ID, tipo ou animal:", key="busca_amostra")
    with col_ordem:
        ordem_amostra = st.selectbox(
            "Ordem de exibição",
            ["Últimos adicionados", "Primeiros adicionados"],
            key="ordem_amostra"
        )
    with col_qtd:
        por_pagina_amostra = st.selectbox(
            "Por página",
            [5, 10, 20, 50, 100],
            index=1,
            key="por_pagina_amostra"
        )

    amostras = carregar_amostras_mongo()
    animais = carregar_animais_mongo()

    if busca_amostra:
        termo_am = busca_amostra.lower()
        amostras = [
            a for a in amostras
            if termo_am in str(a.get('_id', '')).lower()
            or termo_am in str(a.get('metodo_coleta', '')).lower()
            or termo_am in str(a.get('animal_id', '')).lower()
        ]

    if ordem_amostra == "Últimos adicionados":
        amostras = list(reversed(amostras))

    por_pagina = por_pagina_amostra
    total_am = len(amostras)
    max_paginas_am = max(1, (total_am + por_pagina - 1) // por_pagina)

    if not amostras:
        st.info("Nenhuma amostra encontrada.")
    else:
        list_container_amostras = st.container()

        st.markdown("---")
        col_espaco_am, col_pag_am = st.columns([2, 1])
        with col_pag_am:
            page_am = st.pagination(num_pages=max_paginas_am, key="pagina_amostra")
            inicio_am = (page_am - 1) * por_pagina
            fim_am = inicio_am + por_pagina
            st.caption(
                f"Mostrando {inicio_am + 1} a {min(fim_am, total_am)} de {total_am} amostras (Página {page_am} de {max_paginas_am})"
            )
            
        amostras_pagina = amostras[inicio_am:fim_am]

        with list_container_amostras:
            for amostra in amostras_pagina:
                amostra_id = amostra.get('_id', 'Sem ID')
                with st.expander(f"Amostra {amostra_id}"):
                    display_document(amostra, title="Dados da Amostra")

                    animal = next((an for an in animais if an.get(
                        '_id') == amostra.get('animal_id')), None)
                    if animal:
                        st.markdown("---")
                        display_document(
                            animal, title=f"Animal relacionado ({animal.get('nome_comum','Sem nome')})")

                    st.markdown("---")
                    st.subheader("Disponibilidade")
                    
                    current_status = amostra.get('status_amostra') or "Não informado"
                    current_disponivel = bool(amostra.get('disponivel'))
                    current_local = amostra.get('destino_amostra') or ""

                    status_options = ["Disponível", "Reservada", "Em uso", "Consumida", "Perdida", "Não informado"]
                    try:
                        status_index = next(i for i, s in enumerate(status_options) if s.lower() == str(current_status).strip().lower())
                    except:
                        status_index = 5

                    col1, col2 = st.columns(2)
                    with col1:
                        novo_status = st.selectbox("Status", options=status_options, index=status_index, key=f"status_{amostra_id}")
                        disponivel_checkbox = st.checkbox("Disponível", value=current_disponivel, key=f"disp_{amostra_id}")
                    with col2:
                        novo_local = st.text_input("Local / Destino", value=current_local, key=f"local_{amostra_id}")

                    if st.button("Salvar alterações", key=f"salvar_disp_{amostra_id}"):
                        amostras_col.update_one({"_id": amostra_id}, {"$set": {
                            "status_amostra": novo_status,
                            "disponivel": bool(disponivel_checkbox),
                            "destino_amostra": novo_local
                        }})
                        st.success("Atualizado!")
                        st.rerun()

                    if st.button("Excluir amostra", key=f"del_amostra_{amostra_id}"):
                        amostras_col.delete_one({"_id": amostra_id})
                        st.rerun()

# ---------------- TAB 3: Exames ----------------
with tab3:
    st.header("Exames Cadastrados")
    col_busca, col_ordem, col_qtd = st.columns([4, 2, 1])
    with col_busca:
        busca_exame = st.text_input("Buscar exame:", key="busca_exame")
    with col_ordem:
        ordem_exame = st.selectbox(
            "Ordem de exibição",
            ["Últimos adicionados", "Primeiros adicionados"],
            key="ordem_exame"
        )
    with col_qtd:
        por_pagina_exame = st.selectbox(
            "Por página",
            [5, 10, 20, 50, 100],
            index=1,
            key="por_pagina_exame"
        )

    exames = carregar_exames_mongo()

    if busca_exame:
        termo_ex = busca_exame.lower()
        exames = [e for e in exames if termo_ex in str(e.values()).lower()]

    if ordem_exame == "Últimos adicionados":
        exames = list(reversed(exames))

    por_pagina = por_pagina_exame
    total_ex = len(exames)
    max_paginas_ex = max(1, (total_ex + por_pagina - 1) // por_pagina)

    if not exames:
        st.info("Nenhum exame encontrado.")
    else:
        list_container_exames = st.container()

        col_espaco_ex, col_pag_ex = st.columns([3, 1])
        with col_pag_ex:
            page_ex = st.pagination(num_pages=max_paginas_ex, key="pagina_exame")
            inicio_ex = (page_ex - 1) * por_pagina
            fim_ex = inicio_ex + por_pagina
            st.caption(
                f"Mostrando {inicio_ex + 1} a {min(fim_ex, total_ex)} de {total_ex} exames (Página {page_ex} de {max_paginas_ex})"
            )
            
        exames_pagina = exames[inicio_ex:fim_ex]

        with list_container_exames:
            for exame in exames_pagina:
                with st.expander(f"Exame {exame.get('_id')}"):
                    display_document(exame)
                    if st.button("Excluir Exame", key=f"del_ex_{exame.get('_id')}"):
                        exames_col.delete_one({"_id": exame.get('_id')})
                        st.rerun()

# ---------------- TAB 4: Reagentes ----------------
with tab4:
    st.header("Reagentes Cadastrados")
    col_busca, col_ordem, col_qtd = st.columns([4, 2, 1])
    with col_busca:
        busca_reagente = st.text_input("Buscar reagente:", key="busca_reagente")
    with col_ordem:
        ordem_reagente = st.selectbox(
            "Ordem de exibição",
            ["Últimos adicionados", "Primeiros adicionados"],
            key="ordem_reagente"
        )
    with col_qtd:
        por_pagina_reagente = st.selectbox(
            "Por página",
            [5, 10, 20, 50, 100],
            index=1,
            key="por_pagina_reagente"
        )

    reagentes = carregar_reagentes_mongo()

    if busca_reagente:
        termo_re = busca_reagente.lower()
        reagentes = [r for r in reagentes if termo_re in str(r.get('nome', '')).lower()]

    if ordem_reagente == "Últimos adicionados":
        reagentes = list(reversed(reagentes))

    por_pagina = por_pagina_reagente
    total_re = len(reagentes)
    max_paginas_re = max(1, (total_re + por_pagina - 1) // por_pagina)

    if not reagentes:
        st.info("Nenhum reagente encontrado.")
    else:
        list_container_reagentes = st.container()

        st.markdown("---")
        col_espaco_re, col_pag_re = st.columns([3, 1])
        with col_pag_re:
            page_re = st.pagination(num_pages=max_paginas_re, key="pagina_reagente")
            inicio_re = (page_re - 1) * por_pagina
            fim_re = inicio_re + por_pagina
            st.caption(
                f"Mostrando {inicio_re + 1} a {min(fim_re, total_re)} de {total_re} reagentes (Página {page_re} de {max_paginas_re})"
            )
            
        reagentes_pagina = reagentes[inicio_re:fim_re]

        with list_container_reagentes:
            for reagente in reagentes_pagina:
                with st.expander(f"Reagente: {reagente.get('nome')}"):
                    display_document(reagente)
                    nova_qtd = st.number_input("Qtd", value=int(reagente.get('quantidade', 0)), key=f"q_{reagente['_id']}")
                    if st.button("Atualizar Qtd", key=f"b_{reagente['_id']}"):
                        reagentes_col.update_one({"_id": reagente['_id']}, {"$set": {"quantidade": nova_qtd}})
                        st.success("Ok!")
                    if st.button("Excluir", key=f"d_{reagente['_id']}"):
                        reagentes_col.delete_one({"_id": reagente['_id']})
                        st.rerun()