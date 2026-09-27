import streamlit as st
from pymongo import MongoClient
from bson import ObjectId
import os
import pandas as pd

# Conexão ao MongoDB Atlas
from utils import connect_to_mongo

# Conecta ao banco e seleciona a coleção de amostras
db = connect_to_mongo()
samples_col = db['amostras']
exams_col   = db['exames']

st.title("Editar Amostra")

# Somente Professores podem editar amostras
if st.session_state.get('matricula') != 'Professor':
    st.warning("⚠️ Acesso restrito. Você não tem permissão para editar amostras.")
    st.stop()

# Carrega amostras
samples = list(samples_col.find())
# Mapeia ID (string) → documento
sample_dict = { str(s['_id']): s for s in samples }
sample_ids  = list(sample_dict.keys())

if not sample_ids:
    st.info("Nenhuma amostra cadastrada para editar.")
    st.stop()

# Carrega exames e debuga
exams = list(exams_col.find())
st.write("⚙️ Exames carregados do Banco:", exams)

# Mapeia nome do exame → ID (string)
# ajuste o campo 'nome' se seu documento usar outro
exam_map = { e['nome']: str(e['_id']) for e in exams if 'nome' in e }

# Se não houver exames no banco, avisar
if not exam_map:
    st.warning("Não há exames cadastrados — você poderá adicionar novos abaixo.")

# Seleção de amostra
sample_id = st.selectbox("Selecione a amostra para editar:", options=sample_ids)
sample = sample_dict[sample_id]

st.subheader("Dados atuais da Amostra")
st.json(sample)

st.subheader("Editar dados da Amostra")
with st.form("form_editar_amostra"):
    update_data = {}

    # Exemplo de edição de status
    status_atual = sample.get("status", "Pendente")
    opcoes_status = ["Pendente", "Transferida", "Recebida"]
    idx = opcoes_status.index(status_atual) if status_atual in opcoes_status else 0
    novo_status = st.selectbox("Status", options=opcoes_status, index=idx)
    update_data["status"] = novo_status

    # Exemplo de edição de laboratório
    lab_atual = sample.get("laboratorio", "")
    if pd.notna(lab_atual):
        novo_lab = st.text_input("Laboratório", value=lab_atual)
        update_data["laboratorio"] = novo_lab

    # Exemplo de edição de observações
    obs_atual = sample.get("observacoes", "")
    if pd.notna(obs_atual):
        nova_obs = st.text_area("Observações", value=obs_atual)
        update_data["observacoes"] = nova_obs

    # --- Multiselect para exames já existentes ---
    # converte lista de ObjectId ou strings para nomes
    atuais = sample.get("exames", [])
    atuais_nomes = [
        nome for nome, _id in exam_map.items()
        if str(_id) in [str(x) for x in atuais]
    ]
    selecionados = st.multiselect(
        "Exames associados (existentes)",
        options=list(exam_map.keys()),
        default=atuais_nomes
    )

    # --- Text input para criar novo exame ---
    novo_exame = st.text_input("Adicionar novo exame (opcional)")
    if novo_exame:
        # insere no Mongo e atualiza o map
        novo_id = exams_col.insert_one({"nome": novo_exame}).inserted_id
        exam_map[novo_exame] = str(novo_id)
        selecionados.append(novo_exame)
        st.success(f"Exame '{novo_exame}' criado e adicionado à lista.")

    # Converte nomes selecionados de volta para ObjectId
    update_data["exames"] = [ ObjectId(exam_map[n]) for n in selecionados ]

    submit = st.form_submit_button("Salvar alterações")
    if submit:
        result = samples_col.update_one(
            { "_id": ObjectId(sample_id) },
            { "$set": update_data }
        )
        if result.modified_count:
            st.success("Amostra atualizada com sucesso!")
        else:
            st.warning("Nenhuma alteração detectada ou erro na atualização.")