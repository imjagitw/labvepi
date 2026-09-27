import streamlit as st
from datetime import date
from utils import connect_to_mongo, add_document

@st.dialog("Informações do Exame")
def modal_confirmar_exame(exame_data):

    rotulos = {
        "_id": "ID do Exame",
        "amostra_id": "ID da Amostra Vinculada",
        "tipo_exame": "Patógeno Investigado",
        "teste_laboratorial": "Teste Laboratorial",
        "laboratorio_realizador": "Laboratório Realizador",
        "data_realizacao": "Data de Realização",
        "kit_utilizado": "Kit Utilizado",
        "resultado_detalhado": "Resultado do Exame",
        "responsavel_exame": "Responsável pelo Exame",
        "protocolo_exame": "Protocolo Utilizado",
        "observacoes_exame": "Observações"
    }
    
    for k, v in exame_data.items():
        lbl = rotulos.get(k, k)
        st.markdown(f"**{lbl}:** {v}")

    c_canc, c_edit, c_conf = st.columns([1, 1, 1])

    with c_canc:
        if st.button("Cancelar", type="secondary", icon=":material/close:", use_container_width=True):
            st.session_state['show_confirm_exame'] = False
            st.session_state['pending_exame_data'] = None
            st.rerun()

    with c_edit:
        if st.button("Editar", type="secondary", icon=":material/edit:", use_container_width=True):
            st.session_state['show_confirm_exame'] = False
            st.session_state['pending_exame_data'] = None
            st.rerun()

    with c_conf:
        if st.button("Confirmar", type="primary", icon=":material/check:", use_container_width=True):
            success, message = add_document('exames', exame_data)
            if success:
                st.session_state['show_confirm_exame'] = False
                st.session_state['pending_exame_data'] = None
                st.success(message)
                st.rerun()
            else:
                st.error(message)

def render_form_registro_exame():
    st.header("Novo Exame")
    with st.form("form_registro_exame"):
        # --- 🏷️ IDENTIFICAÇÃO E VINCULAÇÃO ---
        st.subheader(":material/label: Identificação & Vinculação")
        col_id, col_amostra = st.columns([3, 3])

        with col_id:
            exame_id_input = st.text_input(
                "ID do Exame (único)", placeholder="Ex: EXM001")

        with col_amostra:
            # Dropdown com amostras existentes para vincular o exame
            db = connect_to_mongo()
            amostras_collection = db['amostras']
            amostras_existentes = list(amostras_collection.find(
                {}, {"_id": 1, "metodo_coleta": 1}))

            amostra_options = [
                ""] + [f"{amostra.get('metodo_coleta', 'Amostra sem tipo')} (ID: {amostra['_id']})" for amostra in amostras_existentes]
            selected_amostra_str = st.selectbox(
                "Vincular a qual Amostra? :red[*]", options=amostra_options)
            err_amostra = st.empty()

            # Extrair o ID da amostra selecionada
            linked_amostra_id = None
            if selected_amostra_str and " (ID: " in selected_amostra_str:
                linked_amostra_id = selected_amostra_str.split(" (ID: ")[1][:-1]
        
        st.divider()

        # --- 🧪 EXECUÇÃO E ANÁLISE ---
        st.subheader(":material/science: Execução & Análise")

        # Linha 1: Laboratório, Teste Laboratorial, Data de Realização, Kit Utilizado
        col_data, col_lab, col_teste, col_tipo = st.columns([2, 2, 2, 2])

        with col_lab:
            exame_laboratorio = st.text_input(
                "Laboratório Realizador :red[*]", placeholder="Ex: Lab. Virologia")
            err_laboratorio = st.empty()

        with col_teste:
            exame_teste = st.selectbox(
                "Teste Laboratorial :red[*]",
                ['', 'PCR', 'Sorológico', 'Coproparasitológico',
                    'Hemoparasito em lâmina', 'Outro']
            )
            err_teste = st.empty()

        with col_data:
            exame_data_realizacao = st.date_input(
                "Data de Realização :red[*]", value=date.today())
            err_data = st.empty()

        with col_tipo:
            exame_tipo = st.selectbox("Patógeno investigado :red[*]", [
                '', 'Febre do Nilo', 'ORTHOFLAVIRIDAE', 'FEBRE AMARELA', 'MYCOPLASMA',
                'HERPESVIRIDAE', 'TRIPANOSTOMATIDAE', 'RESISTÊNCIA BACTERIANA',
                ' HEPATOZOON', 'RAIVA', 'Outro'
            ])
            err_tipo = st.empty()
     
        # Linha 2: Resultado, Responsável, Protocolo
        col_resp, col_kit, col_prot, col_res = st.columns([2, 2, 2, 2])

        with col_res:
            exame_resultado = st.selectbox(
                "Resultado do Exame :red[*]",
                ["", "Positivo", "Negativo", "Inconclusivo", "Aguardando Resultado"]
            )
            err_resultado = st.empty()

        with col_kit:
            exame_kit = st.text_input("Kit Utilizado :red[*]")
            err_kit = st.empty()

        with col_resp:
            exame_responsavel = st.text_input("Responsável pelo Exame :red[*]")
            err_responsavel = st.empty()

        with col_prot:
            exame_procotocolo = st.text_input("Protocolo Utilizado :red[*]")
            err_protocolo = st.empty()

        st.divider()

        # --- 📋 OBSERVAÇÕES ---
        st.subheader(":material/notes: Observações")
        exame_observacoes = st.text_area("Observações")

        col_space, col_submit = st.columns([3, 1])
        with col_submit:
            submit_exame = st.form_submit_button(
                "Registrar Exame", type="primary", use_container_width=True)

        if submit_exame:
            has_errors = False

            if not linked_amostra_id:
                err_amostra.error(
                    "Selecione uma amostra para vincular este exame.")
                has_errors = True
            if not exame_tipo:
                err_tipo.error("Selecione o patógeno investigado.")
                has_errors = True
            if not exame_laboratorio:
                err_laboratorio.error("Insira o laboratório realizador.")
                has_errors = True
            if not exame_teste:
                err_teste.error("Selecione o teste laboratorial.")
                has_errors = True
            if not exame_data_realizacao:
                err_data.error("Informe a data de realização do exame.")
                has_errors = True
            if not exame_kit:
                err_kit.error("Insira o kit utilizado.")
                has_errors = True
            if not exame_resultado:
                err_resultado.error("Selecione o resultado do exame.")
                has_errors = True
            if not exame_responsavel:
                err_responsavel.error("Insira o responsável pelo exame.")
                has_errors = True
            if not exame_procotocolo:
                err_protocolo.error("Insira o protocolo utilizado.")
                has_errors = True

            if not has_errors:
                exame_data = {
                    "_id": exame_id_input,
                    "amostra_id": linked_amostra_id,
                    "tipo_exame": exame_tipo,
                    "teste_laboratorial": exame_teste,
                    "laboratorio_realizador": exame_laboratorio,
                    "data_realizacao": str(exame_data_realizacao),
                    "kit_utilizado": exame_kit,
                    "resultado_detalhado": exame_resultado,
                    "responsavel_exame": exame_responsavel,
                    "protocolo_exame": exame_procotocolo,
                    "observacoes_exame": exame_observacoes
                }
                exame_data = {k: v for k, v in exame_data.items()
                              if v not in (None, "", [])}

                st.session_state['pending_exame_data'] = exame_data
                st.session_state['show_confirm_exame'] = True

    if st.session_state.get('show_confirm_exame') and st.session_state.get('pending_exame_data'):
        modal_confirmar_exame(st.session_state['pending_exame_data'])