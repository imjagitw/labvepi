import streamlit as st
from datetime import date
from utils import connect_to_mongo, add_document

def render_form_registro_amostra():
    st.header("Nova Amostra")
    with st.form("form_registro_amostra"):

        amostra_id_input = st.text_input(
            "ID da Amostra (único)", placeholder="Ex: AMS001")

        # Dropdown com animais existentes para vincular a amostra
        db = connect_to_mongo()
        animais_collection = db['animais']
        animais_existentes = list(animais_collection.find(
            {}, {"_id": 1, "nome_comum": 1}))

        animal_options = [
            ""] + [f"{animal.get('nome_comum', 'Animal sem nome')} (ID: {animal['_id']})" for animal in animais_existentes]
        selected_animal_str = st.selectbox(
            "Vincular a qual Animal?", options=animal_options)

        # Extrair o ID do animal selecionado
        linked_animal_id = None
        if selected_animal_str and " (ID: " in selected_animal_str:
            linked_animal_id = selected_animal_str.split(
                " (ID: ")[1][:-1]  # Extrai o ID entre " (ID: " e ")"
        amostra_local_coleta = st.text_input("Local de Coleta da Amostra")
        amostra_data_coleta = st.date_input(
            "Data da Coleta da Amostra", value=date.today())
        amostra_nome_coletor = st.text_input("Nome do Coletor")
        amostra_id_projeto = st.text_input("ID do Projeto (opcional)")
        amostra_metodo_coleta = st.selectbox(
            "Amostra coletada via",
            ["", "Swab nasal", "Swab oral", "Swab cloacal", "Sangue", "Necrópsia", 'Fezes', 'Tecido', 'Pele', 'Pelo', 'Esfregaço sanguíneo', 'Outros']
        )
        amostra_condicao = st.selectbox(
            "Condição de Armazenamento",
            ["", "Temperatura ambiente", "Refrigerada", "Congelada",
                "Sem identificação", "Coagulada", "Hemolisada", 'Nitrogênio líquido', 'Gelo seco']
        )
        amostra_fase = st.selectbox(
            "Fase da Amostra",
            ["", "Extração", "PCR", "ELETRO"]
        )
        amostra_destino = st.selectbox(
            "Destino da Amostra",
            ["", "Biobanco UFPI", "Biobanco UFPA", "Fiofruz AM", "LASAN UFPI", 'LAPATO UFPI', 'LAPATO UFPA', 'LAB VIGILÂNCIA DE EPIZOOTIAS - UFPI', 'Outro']
        )
        amostra_kit = st.text_input("Kit utilizado (opcional)")
        amostra_longitude = st.text_input("Longitude (opcional)")
        amostra_latitude = st.text_input("Latitude (opcional)")
        amostra_resultado_exame = st.text_input(
            "Resultado do Exame (inicial, opcional)")
        amostra_observacoes = st.text_area("Observações (opcional)")
        amostra_caixa = st.text_input("Caixa de amarzenamento/Freezer (opcional)")
        amostra_disponibilidade = st.checkbox("Amostra disponível para uso?")
        amostra_dna = st.checkbox("DNA disponível para uso?")
        amostra_rna = st.checkbox("RNA disponível para uso?")
        amostra_sequenciamento = st.selectbox(
            "Sequenciamento realizado?", ["", "Sim", "Não"]
        )

        submit_amostra = st.form_submit_button("Registrar Amostra")

        if submit_amostra:
            if not amostra_id_input:
                st.error("Por favor, insira um ID único para a amostra.")
            elif not linked_animal_id:
                st.error(
                    "Por favor, selecione um animal para vincular esta amostra.")
            else:
                amostra_data = {
                    "_id": amostra_id_input,
                    "animal_id": linked_animal_id,
                    "local_coleta_amostra": amostra_local_coleta,
                    'amostra_id_projeto': amostra_id_projeto,
                    "data_coleta_amostra": str(amostra_data_coleta),
                    "nome_coletor": amostra_nome_coletor,
                    "metodo_coleta": amostra_metodo_coleta,
                    "condicao_amostra": amostra_condicao,
                    "destino_amostra": amostra_destino,
                    "longitude": amostra_longitude,
                    "resultado_exame": amostra_resultado_exame,
                    "latitude": amostra_latitude,
                    "kit_utilizado": amostra_kit,
                    "observacoes": amostra_observacoes,
                    "caixa": amostra_caixa,
                    "sangue_disponivel": amostra_disponibilidade,
                    "dna_disponivel": amostra_dna,
                    "rna_disponivel": amostra_rna,
                    'sequenciamento': amostra_sequenciamento
                }
                amostra_data = {
                    k: v for k, v in amostra_data.items() if v not in (None, "", [])}

                success, message = add_document('amostras', amostra_data)
                if success:
                    st.success(message)
                else:
                    st.error(message)
