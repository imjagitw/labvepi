import streamlit as st
from datetime import date
from utils import connect_to_mongo, add_document

@st.dialog("Informações da Amostra")
def modal_confirmar_amostra(amostra_data):

    rotulos = {
        "_id": "ID da Amostra",
        "animal_id": "ID do Animal Vinculado",
        "amostra_id_projeto": "ID do Projeto",
        "local_coleta_amostra": "Local de Coleta",
        "data_coleta_amostra": "Data de Coleta",
        "nome_coletor": "Nome do Coletor",
        "metodo_coleta": "Método de Coleta",
        "condicao_amostra": "Condição de Armazenamento",
        "fase_amostra": "Fase da Amostra",
        "destino_amostra": "Destino da Amostra",
        "kit_utilizado": "Kit Utilizado",
        "longitude": "Longitude",
        "latitude": "Latitude",
        #"resultado_exame": "Resultado do Exame",
        "observacoes": "Observações",
        "caixa": "Caixa de Armazenamento/Freezer",
        "sangue_disponivel": "Amostra Disponível",
        "dna_disponivel": "DNA Disponível",
        "rna_disponivel": "RNA Disponível",
        "sequenciamento": "Sequenciamento Realizado"
    }

    for k, v in amostra_data.items():
        lbl = rotulos.get(k, k)
        st.markdown(f"**{lbl}:** {v}")

    c_canc, c_edit, c_conf = st.columns([1, 1, 1])

    with c_canc:
        if st.button("Cancelar", type="secondary", icon=":material/close:", use_container_width=True):
            st.session_state['show_confirm_amostra'] = False
            st.session_state['pending_amostra_data'] = None
            st.rerun()

    with c_edit:
        if st.button("Editar", type="secondary", icon=":material/edit:", use_container_width=True):
            st.session_state['show_confirm_amostra'] = False
            st.session_state['pending_amostra_data'] = None
            st.rerun()

    with c_conf:
        if st.button("Confirmar", type="primary", icon=":material/check:", use_container_width=True):
            success, message = add_document('amostras', amostra_data)
            if success:
                st.session_state['show_confirm_amostra'] = False
                st.session_state['pending_amostra_data'] = None
                st.success(message)
                st.rerun()
            else:
                st.error(message)

def render_form_registro_amostra():
    st.header("Nova Amostra")
    with st.form("form_registro_amostra"):

        # --- 🏷️ IDENTIFICAÇÃO E VINCULAÇÃO ---
        st.subheader(":material/label: Identificação & Vinculação")
        col_id, col_projeto, col_animal = st.columns([2, 2, 2])

        with col_id:
            amostra_id_input = st.text_input(
                "ID da Amostra (único) :red[*]", placeholder="Ex: AMS001")
            err_id = st.empty()

        with col_animal:
            # Dropdown com animais existentes para vincular a amostra
            db = connect_to_mongo()
            animais_collection = db['animais']
            animais_existentes = list(animais_collection.find(
                {}, {"_id": 1, "nome_comum": 1}))

            animal_options = [
                ""] + [f"{animal.get('nome_comum', 'Animal sem nome')} (ID: {animal['_id']})" for animal in animais_existentes]
            selected_animal_str = st.selectbox(
                "Vincular a qual Animal? :red[*]", options=animal_options)
            err_animal = st.empty()

            # Extrair o ID do animal selecionado
            linked_animal_id = None
            if selected_animal_str and " (ID: " in selected_animal_str:
                linked_animal_id = selected_animal_str.split(
                    " (ID: ")[1][:-1]

        with col_projeto:
            amostra_id_projeto = st.text_input("ID do Projeto")

        st.divider()

        # --- 🧪 COLETA, PROCESSAMENTO E ARMAZENAMENTO ---
        st.subheader(":material/science: Coleta, Processamento & Armazenamento")

        # Linha 1: Nome do Coletor, Data da Coleta, Coletada via, Kit utilizado
        col_data, col_metodo, col_kit, col_fase = st.columns([2, 2, 2, 2])
        with col_fase:
            amostra_fase = st.selectbox(
                "Fase da Amostra :red[*]",
                ["", "Extração", "PCR", "ELETRO"]
            )
            err_fase = st.empty()
        with col_data:
            amostra_data_coleta = st.date_input(
                "Data da Coleta :red[*]", value=date.today())
            err_data = st.empty()
        with col_metodo:
            amostra_metodo_coleta = st.selectbox(
                "Coletada via :red[*]",
                ["", "Swab nasal", "Swab oral", "Swab cloacal", "Sangue", "Necrópsia",
                    'Fezes', 'Tecido', 'Pele', 'Pelo', 'Esfregaço sanguíneo', 'Outros']
            )
            err_metodo = st.empty()
        with col_kit:
            amostra_kit = st.text_input(
                "Kit utilizado :red[*]", placeholder="Ex: QIAamp Viral RNA Mini Kit")
            err_kit = st.empty()

        # Linha 2: Fase da amostra, Condição de armazenamento, Caixa de armazenamento
        col_coletor, col_condicao, col_caixa = st.columns([2, 2, 2])
        with col_coletor:
            amostra_nome_coletor = st.text_input("Nome do Coletor :red[*]")
            err_coletor = st.empty()
        with col_condicao:
            amostra_condicao = st.selectbox(
                "Condição de Armazenamento :red[*]",
                ["", "Temperatura ambiente", "Refrigerada", "Congelada",
                    "Sem identificação", "Coagulada", "Hemolisada", 'Nitrogênio líquido', 'Gelo seco']
            )
            err_condicao = st.empty()
        with col_caixa:
            amostra_caixa = st.text_input(
                "Caixa de armazenamento/Freezer :red[*]")
            err_caixa = st.empty()

        # Linha 3: Local de Coleta, Latitude, Longitude, Destino Coleta
        col_local, col_lat, col_long, col_destino = st.columns([2, 2, 2, 2])
        with col_local:
            amostra_local_coleta = st.text_input(
                "Local de Coleta da Amostra :red[*]", placeholder="Ex: Lab. Virologia")
            err_local = st.empty()
        with col_lat:
            amostra_latitude = st.text_input("Latitude")
        with col_long:
            amostra_longitude = st.text_input("Longitude")
        with col_destino:
            amostra_destino = st.selectbox(
                "Destino da Amostra :red[*]",
                ["", "Biobanco UFPI", "Biobanco UFPA", "Fiofruz AM", "LASAN UFPI",
                    'LAPATO UFPI', 'LAPATO UFPA', 'LAB VIGILÂNCIA DE EPIZOOTIAS - UFPI', 'Outro']
            )
            err_destino = st.empty()

        st.divider()

        # --- 📊 DISPONIBILIDADE E ANÁLISES ---
        st.subheader(":material/inventory: Disponibilidade & Análises")
        col_status_ams, col_disp, col_seq, col_dna, col_rna = st.columns([2, 2, 2, 2, 2])

        with col_status_ams:
            amostra_status = st.selectbox(
                "Status da Amostra",
                ["Disponível", "Reservada", "Em uso", "Consumida", "Perdida"]
            )

        with col_disp:
            amostra_disponibilidade = st.selectbox(
                "Amostra disponível? :red[*]", ["", "Sim", "Não"]
            )
            err_disponibilidade = st.empty()

        with col_dna:
            amostra_dna = st.selectbox(
                "DNA disponível? :red[*]", ["", "Sim", "Não"]
            )
            err_dna = st.empty()

        with col_rna:
            amostra_rna = st.selectbox(
                "RNA disponível? :red[*]", ["", "Sim", "Não"]
            )
            err_rna = st.empty()

        with col_seq:
            amostra_sequenciamento = st.selectbox(
                "Sequenciamento realizado? :red[*]", ["", "Sim", "Não"]
            )
            err_sequenciamento = st.empty()

        st.divider()

        # --- 📋 OBSERVAÇÕES ---
        st.subheader(":material/notes: Observações")
        amostra_observacoes = st.text_area('Observações')


        col_space, col_submit = st.columns([3, 1])
        with col_submit:
            submit_amostra = st.form_submit_button(
                "Registrar Amostra", type="primary", use_container_width=True)

        if submit_amostra:
            has_errors = False

            if not amostra_id_input:
                err_id.error("Insira um ID único para a amostra.")
                has_errors = True
            if not linked_animal_id:
                err_animal.error(
                    "Selecione um animal para vincular esta amostra.")
                has_errors = True
            if not amostra_local_coleta:
                err_local.error("Insira o local de coleta da amostra.")
                has_errors = True
            if not amostra_data_coleta:
                err_data.error("Informe a data de coleta da amostra.")
                has_errors = True
            if not amostra_nome_coletor:
                err_coletor.error("Insira o nome do coletor.")
                has_errors = True
            if not amostra_metodo_coleta:
                err_metodo.error("Selecione o método de coleta da amostra.")
                has_errors = True
            if not amostra_condicao:
                err_condicao.error(
                    "Selecione a condição de armazenamento da amostra.")
                has_errors = True
            if not amostra_fase:
                err_fase.error("Selecione a fase da amostra.")
                has_errors = True
            if not amostra_destino:
                err_destino.error("Selecione o destino da amostra.")
                has_errors = True
            if not amostra_kit:
                err_kit.error("Insira o kit utilizado.")
                has_errors = True
            # if not amostra_resultado_exame:
            #     err_resultado.error("Insira o resultado do exame.")
            #     has_errors = True
            if not amostra_caixa:
                err_caixa.error(
                    "Insira a caixa de armazenamento ou freezer.")
                has_errors = True
            if not amostra_disponibilidade:
                err_disponibilidade.error(
                    "Selecione a disponibilidade da amostra.")
                has_errors = True
            if not amostra_dna:
                err_dna.error("Selecione se o DNA está disponível.")
                has_errors = True
            if not amostra_rna:
                err_rna.error("Selecione se o RNA está disponível.")
                has_errors = True
            if not amostra_sequenciamento:
                err_sequenciamento.error(
                    "Selecione se o sequenciamento foi realizado.")
                has_errors = True

            if not has_errors:
                amostra_data = {
                    "_id": amostra_id_input,
                    "animal_id": linked_animal_id,
                    "local_coleta_amostra": amostra_local_coleta,
                    "amostra_id_projeto": amostra_id_projeto,
                    "data_coleta_amostra": str(amostra_data_coleta),
                    "nome_coletor": amostra_nome_coletor,
                    "metodo_coleta": amostra_metodo_coleta,
                    "condicao_amostra": amostra_condicao,
                    "fase_amostra": amostra_fase,
                    "destino_amostra": amostra_destino,
                    "longitude": amostra_longitude,
                    #"resultado_exame": amostra_resultado_exame,
                    "latitude": amostra_latitude,
                    "kit_utilizado": amostra_kit,
                    "caixa": amostra_caixa,
                    "status_amostra": amostra_status,
                    "sangue_disponivel": amostra_disponibilidade,
                    "dna_disponivel": amostra_dna,
                    "rna_disponivel": amostra_rna,
                    "sequenciamento": amostra_sequenciamento,
                    "observacoes": amostra_observacoes,
                }
                amostra_data = {
                    k: v for k, v in amostra_data.items() if v not in (None, "", [])}

                st.session_state['pending_amostra_data'] = amostra_data
                st.session_state['show_confirm_amostra'] = True

    if st.session_state.get('show_confirm_amostra') and st.session_state.get('pending_amostra_data'):
        modal_confirmar_amostra(st.session_state['pending_amostra_data'])