import streamlit as st
from datetime import date
from utils import add_document, connect_to_mongo

@st.dialog("Informações do Reagente")
def modal_confirmar_reagente(reagente_data):
    rotulos = {
        "_id": "ID do Reagente",
        "nome": "Nome do Reagente",
        "codigo": "Código",
        "numero_lote": "Número do Lote",
        "marca": "Marca",
        "data_validade": "Data de Validade",
        "quantidade_unidade": "Quantidade (Unidade)",
        "local_armazenamento": "Local de Armazenamento",
        "observacoes": "Observações",
        "etapa": "Etapa do Processo"
    }
    for k, v in reagente_data.items():
        lbl = rotulos.get(k, k)
        st.markdown(f"**{lbl}:** {v}")

    c_canc, c_edit, c_conf = st.columns([1, 1, 1])
    
    with c_canc:
        if st.button("Cancelar", type="secondary", icon=":material/close:", use_container_width=True):
            st.session_state['show_confirm_reagente'] = False
            st.session_state['pending_reagente_data'] = None
            st.rerun()

    with c_edit:
        if st.button("Editar", type="secondary", icon=":material/edit:", use_container_width=True):
            st.session_state['show_confirm_reagente'] = False
            st.session_state['pending_reagente_data'] = None
            st.rerun()

    with c_conf:
        if st.button("Confirmar", type="primary", icon=":material/check:", use_container_width=True):
            success, message = add_document('reagentes', reagente_data)
            if success:
                st.session_state['show_confirm_reagente'] = False
                st.session_state['pending_reagente_data'] = None
                st.success(message)
                st.rerun()
            else:
                st.error(message)

def render_form_registro_reagente():
    st.header("Novo Reagente")
    with st.form("form_registro_reagente"):
        
        # --- 🏷️ IDENTIFICAÇÃO DO REAGENTE ---
        st.subheader(":material/label: Identificação")
        
        # Linha 1: ID, Nome, Código
        col_id, col_nome = st.columns([3, 3])

        with col_id:
            reagente_id_input = st.text_input(
                "ID do Reagente (único)", placeholder="Ex: REG001")

        with col_nome:
            reagente_nome = st.text_input("Nome do Reagente :red[*]")
            err_nome = st.empty()

        # Linha 2: Número do Lote, Marca
        col_codigo, col_lote, col_marca = st.columns([2, 2, 2])

        with col_codigo:
            reagente_codigo = st.text_input("Código :red[*]")
            err_codigo = st.empty()
        with col_lote:
            reagente_lote = st.text_input("Número do Lote :red[*]")
            err_lote = st.empty()

        with col_marca:
            reagente_marca = st.text_input("Marca :red[*]")
            err_marca = st.empty()

        st.divider()

        # --- 📦 ESTOQUE, VALIDADE E LOCALIZAÇÃO ---
        st.subheader(":material/inventory: Estoque, Validade & Localização")

        # Linha 1: Validade, Qtd Unidade, Qtd Volume
        col_validade, col_qtd_uni, col_qtd_vol = st.columns([2, 2, 2])

        with col_validade:
            reagente_validade = st.date_input(
                "Data de Validade :red[*]", value=date.today())
            err_validade = st.empty()

        with col_qtd_uni:
            reagente_quantidade_unidade = st.number_input(
                "Quantidade (unidade) :red[*]", min_value=0, step=1)
            err_quantidade_unidade = st.empty()

        with col_qtd_vol:
            reagente_quantidade_volume = st.number_input(
                "Quantidade (volume)", min_value=0.0, format="%.2f", step=0.01)

        # Linha 2: Local de Armazenamento, Etapa do Processo
        col_local, col_etapa = st.columns([2, 2])

        with col_local:
            reagente_local_armazenamento = st.text_input(
                "Local de Armazenamento :red[*]")
            err_local_armazenamento = st.empty()

        with col_etapa:
            reagente_etapa = st.text_input("Etapa do Processo")

        st.divider()

        # --- 📋 OBSERVAÇÕES ---
        st.subheader(":material/notes: Observações")
        reagente_observacoes = st.text_area("Observações")

        col_space, col_submit = st.columns([3, 1])
        with col_submit:
            submit_reagente = st.form_submit_button("Registrar Reagente", type="primary", use_container_width=True)

        if submit_reagente:
            has_erros = False
            
            if not reagente_nome:
                err_nome.error("Inserir nome do reagente.")
                has_erros = True
            if not reagente_codigo:
                err_codigo.error("Inserir código do reagente.")
                has_erros = True
            if not reagente_lote:
                err_lote.error("Inserir número do lote.")
                has_erros = True
            if not reagente_marca:
                err_marca.error("Inserir marca do reagente.")
                has_erros = True
            if not reagente_validade:
                err_validade.error("Inserir data de validade.")
                has_erros = True
            if not reagente_quantidade_unidade:
                err_quantidade_unidade.error("Inserir quantidade (unidade).")
                has_erros = True
            if not reagente_local_armazenamento:
                err_local_armazenamento.error("Inserir local de armazenamento.")
                has_erros = True
                
            if not has_erros:
                reagente_data = {
                    "_id": reagente_id_input,
                    "nome": reagente_nome,
                    "codigo": reagente_codigo,
                    "numero_lote": reagente_lote,
                    "marca": reagente_marca,
                    "data_validade": str(reagente_validade),
                    "quantidade_unidade": reagente_quantidade_unidade,
                    "quantidade_volume": reagente_quantidade_volume,
                    "quantidade": reagente_quantidade_unidade,
                    "local_armazenamento": reagente_local_armazenamento,
                    'etapa': reagente_etapa,
                    "observacoes": reagente_observacoes
                }
                reagente_data = {
                    k: v for k, v in reagente_data.items() if v not in (None, "", [])}

                st.session_state['pending_reagente_data'] = reagente_data
                st.session_state['show_confirm_reagente'] = True
    
    if st.session_state.get('show_confirm_reagente') and st.session_state.get('pending_reagente_data'):
        modal_confirmar_reagente(st.session_state['pending_reagente_data'])