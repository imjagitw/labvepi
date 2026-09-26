import streamlit as st
from datetime import date
from utils import add_document


def render_form_registro_reagente():
    st.header("Novo Reagente")
    with st.form("form_registro_reagente"):
        reagente_id_input = st.text_input(
            "ID do Reagente (único)", placeholder="Ex: REG001")
        reagente_nome = st.text_input("Nome do Reagente")
        reagente_codigo = st.text_input("Código")
        reagente_lote = st.text_input("Número do Lote")
        reagente_marca = st.text_input("Marca")
        reagente_validade = st.date_input(
            "Data de Validade", value=date.today())
        reagente_quantidade = st.number_input(
            "Quantidade (e.g., ml, g, unidades)", min_value=0.0, format="%.2f", step=0.01)
        reagente_local_armazenamento = st.text_input("Local de Armazenamento")
        reagente_observacoes = st.text_area(
            "Observações do Reagente (opcional)")
        reagente_etapa = st.text_input("Etapa do Processo (opcional)")

        submit_reagente = st.form_submit_button("Registrar Reagente")

        if submit_reagente:
            if not reagente_id_input:
                st.error("Por favor, insira um ID único para o reagente.")
            else:
                reagente_data = {
                    "_id": reagente_id_input,
                    "nome": reagente_nome,
                    "codigo": reagente_codigo,
                    "numero_lote": reagente_lote,
                    "marca": reagente_marca,
                    "data_validade": str(reagente_validade),
                    "quantidade": reagente_quantidade,
                    "local_armazenamento": reagente_local_armazenamento,
                    'etapa': reagente_etapa,
                    "observacoes": reagente_observacoes
                }
                reagente_data = {
                    k: v for k, v in reagente_data.items() if v not in (None, "", [])}

                success, message = add_document('reagentes', reagente_data)
                if success:
                    st.success(message)
                else:
                    st.error(message)
