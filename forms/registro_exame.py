import streamlit as st
from datetime import date
from utils import connect_to_mongo, add_document


def render_form_registro_exame():
    st.header("Registrar Novo Exame")
    with st.form("form_registro_exame"):
        st.markdown("**Informações do Exame**")
        exame_id_input = st.text_input(
            "ID do Exame (único)", placeholder="Ex: EXM001")

        # Dropdown com amostras existentes para vincular o exame
        db = connect_to_mongo()
        amostras_collection = db['amostras']
        amostras_existentes = list(amostras_collection.find(
            {}, {"_id": 1, "metodo_coleta": 1}))

        amostra_options = [
            ""] + [f"{amostra.get('metodo_coleta', 'Amostra sem tipo')} (ID: {amostra['_id']})" for amostra in amostras_existentes]
        selected_amostra_str = st.selectbox(
            "Vincular a qual Amostra?", options=amostra_options)

        # Extrair o ID da amostra selecionada
        linked_amostra_id = None
        if selected_amostra_str and " (ID: " in selected_amostra_str:
            linked_amostra_id = selected_amostra_str.split(" (ID: ")[1][:-1]

        exame_tipo = st.selectbox("Patógeno investigado", [
            'Febre do Nilo', 'ORTHOFLAVIRIDAE', 'FEBRE AMARELA', 'MYCOPLASMA',
            'HERPESVIRIDAE', 'TRIPANOSTOMATIDAE', 'RESISTÊNCIA BACTERIANA',
            ' HEPATOZOON', 'RAIVA', ''
        ])
        exame_laboratorio = st.text_input("Laboratório Realizador")
        exame_teste = st.selectbox(
            "Teste Laboratorial",
            ['PCR', 'Sorológico', 'Coproparasitológico', 'Hemoparasito em lâmina', 'Outro', '']
        )
        exame_data_realizacao = st.date_input(
            "Data de Realização", value=date.today())
        exame_resultado = st.selectbox(
            "Resultado do Exame",
            ["", "Positivo", "Negativo", "Inconclusivo", "Aguardando Resultado"]
        )
        exame_responsavel = st.text_input("Responsável pelo Exame")
        exame_procotocolo = st.text_input("Protocolo Utilizado")
        exame_observacoes = st.text_area("Observações do Exame (opcional)")

        submit_exame = st.form_submit_button("Registrar Exame")

        if submit_exame:
            if not exame_id_input:
                st.error("Por favor, insira um ID único para o exame.")
            elif not linked_amostra_id:
                st.error(
                    "Por favor, selecione uma amostra para vincular este exame.")
            else:
                exame_data = {
                    "_id": exame_id_input,
                    "amostra_id": linked_amostra_id,
                    "tipo_exame": exame_tipo,
                    'teste_laboratorial': exame_teste,
                    "laboratorio_realizador": exame_laboratorio,
                    "data_realizacao": str(exame_data_realizacao),
                    "resultado_detalhado": exame_resultado,
                    "responsavel_exame": exame_responsavel,
                    "observacoes_exame": exame_observacoes,
                    "protocolo_exame": exame_procotocolo
                }
                exame_data = {k: v for k, v in exame_data.items()
                              if v not in (None, "", [])}

                success, message = add_document('exames', exame_data)
                if success:
                    st.success(message)
                else:
                    st.error(message)
