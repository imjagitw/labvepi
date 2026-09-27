import streamlit as st
from pymongo import MongoClient
import datetime
import os
import pandas as pd

# Conexão ao MongoDB (usando variável de ambiente)

def connect_to_mongo():
    uri = os.environ.get(
        "MONGO_URI",
        "mongodb+srv://emiliods79:uD5A2J4o38dpk0hX@cluster0.ufpae.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    )
    client = MongoClient(uri)
    db = client['pibit_app']
    return db

db = connect_to_mongo()

st.title("Importação de dados para o Sistema")

# Seleção do tipo de planilha para definir a coleção
tipo_planilha = st.radio(
    "Selecione o tipo de planilha a ser importada:",
    options=["Importação Unificada", "Animais",
             "Amostras", "Exames", "Reagentes"]
)

if tipo_planilha == "Importação Unificada":
    st.info("""
    Para importação unificada, sua planilha deve conter as seguintes colunas:
    - Colunas do Animal: animal_id, nome_comum, nome_cientifico, sexo, peso, hvu, microchip, orgao, status, funcao
    - Colunas da Amostra: amostra_id, metodo_coleta, data_coleta, local_coleta
    - Colunas do Exame: exame_id, tipo_exame, teste_laboratorial, data_realizacao, resultado_detalhado
    """)

    uploaded_file = st.file_uploader(
        "Selecione a planilha unificada (CSV ou Excel)",
        type=["csv", "xlsx"]
    )

    if uploaded_file is not None:
        try:
            # Leitura do arquivo
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            st.subheader("Visualização dos Dados")
            st.dataframe(df.head())

            if st.button("Processar Importação Unificada"):
                # Processar animais
                animais_df = df[[col for col in df.columns if col.startswith(
                    'animal_')]].drop_duplicates()
                animais_df = animais_df.rename(columns={
                    'animal_id': '_id',
                    'animal_nome_comum': 'nome_comum',
                    'animal_nome_cientifico': 'nome_cientifico'
                    # adicione outros campos conforme necessário
                })

                # Processar amostras
                amostras_df = df[[col for col in df.columns if col.startswith(
                    'amostra_')]].drop_duplicates()
                amostras_df = amostras_df.rename(columns={
                    'amostra_id': '_id',
                    'amostra_metodo_coleta': 'metodo_coleta',
                    'amostra_data_coleta': 'data_coleta'
                    # adicione outros campos conforme necessário
                })

                # Processar exames
                exames_df = df[[col for col in df.columns if col.startswith(
                    'exame_')]].drop_duplicates()
                exames_df = exames_df.rename(columns={
                    'exame_id': '_id',
                    'exame_tipo': 'tipo_exame',
                    'exame_resultado': 'resultado_detalhado'
                    # adicione outros campos conforme necessário
                })

                # Converter para dicionários e remover campos vazios
                animais = [
                    {k: v for k, v in record.items() if pd.notnull(v) and v != ""}
                    for record in animais_df.to_dict('records')
                ]
                amostras = [
                    {k: v for k, v in record.items() if pd.notnull(v) and v != ""}
                    for record in amostras_df.to_dict('records')
                ]
                exames = [
                    {k: v for k, v in record.items() if pd.notnull(v) and v != ""}
                    for record in exames_df.to_dict('records')
                ]

                # Inserir no banco de dados
                if animais:
                    db['animais'].insert_many(animais)
                if amostras:
                    db['amostras'].insert_many(amostras)
                if exames:
                    db['exames'].insert_many(exames)

                st.success(f"""
                Importação concluída com sucesso!
                - {len(animais)} animais processados
                - {len(amostras)} amostras processadas
                - {len(exames)} exames processados
                """)

        except Exception as e:
            st.error(f"Erro durante a importação: {str(e)}")

else:
    colecao_map = {
        "Animais": "animais",
        "Amostras": "amostras",
        "Exames": "exames",
        "Reagentes": "reagentes"
    }
    collection = db[colecao_map[tipo_planilha]]

    # Upload do arquivo
    uploaded_file = st.file_uploader(
        "Selecione uma planilha (CSV ou Excel)",
        type=["csv", "xlsx"]
    )

    if uploaded_file is not None:
        try:
            # Leitura com pandas
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            # Padronização dos nomes das colunas
            df.columns = [col.strip().lower().replace(" ", "_")
                          for col in df.columns]

            # Renomeie para os nomes usados no sistema, se necessário
            renomear = {}
            if tipo_planilha == "Amostras":
                renomear = {
                    "data_de_coleta": "data_coleta",
                    "local_de_coleta": "local_coleta",
                    "tipo_de_amostra": "metodo_coleta",
                    "condicao": "condicao_amostra",
                    "destino": "destino_amostra",
                    "resultado_do_exame": "resultado_exame",
                    'amostra_kit': 'kit_utilizado',
                    "observacoes_da_amostra": "observacoes",
                }
            elif tipo_planilha == "Animais":
                renomear = {
                    "nome_comum": "nome_comum",
                    "nome_cientifico": "nome_cientifico",
                    "sexo": "sexo",
                    "peso": "peso",
                    "hvu": "hvu",
                    "microchip": "microchip",
                    "orgao": "orgao",
                    "status": "status",
                    "funcao": "funcao",
                    "local_origem": "local_origem",
                    "data_nascimento": "data_nascimento",
                    "observacoes": "observacoes",
                    'id_projeto': 'animal_id_projeto',
                }
            elif tipo_planilha == "Exames":
                renomear = {
                    'id': '_id',
                    'amostra_id': 'amostra_id',
                    'tipo_exame': 'tipo_exame',
                    'teste_laboratorial': 'teste_laboratorial',
                    'laboratorio_realizador': 'laboratorio_realizador',
                    'data_de_realizacao': 'data_realizacao',
                    'resultado_detalhado': 'resultado_detalhado',
                    'responsavel_exame': 'responsavel_exame',
                    'protocolo_exame': 'protocolo_exame',
                    'observacoes_do_exame': 'observacoes_exame'
                }
            elif tipo_planilha == "Reagentes":
                renomear = {
                    'id': '_id',
                    "nome_do_reagente": "nome",
                    "fabricante": "fabricante",
                    "numero_do_lote": "numero_lote",
                    "data_de_validade": "data_validade",
                    "quantidade": "quantidade",
                    "unidade": "unidade",
                    "local_de_armazenamento": "local_armazenamento",
                    'etapa': 'etapa',
                    "observacoes_do_reagente": "observacoes",
                }
            df.rename(columns=renomear, inplace=True)

            # Adicionar seleção do modo de importação
            modo_importacao = st.radio(
                "Selecione o modo de importação:",
                ["Inserir novos registros",
                    "Atualizar registros existentes", "Inserir e atualizar"]
            )

            st.subheader("Visualização dos Dados")
            st.dataframe(df.head())

            # controles extras
            st.info("Opções de importação")
            modo_importacao = st.radio(
                "Modo de importação:",
                ["Inserir novos registros",
                    "Atualizar registros existentes", "Inserir e atualizar"],
                index=2
            )
            conflito = st.radio(
                "Tratamento de duplicatas (_id):",
                ["Pular duplicatas",
                    "Sobrescrever (replace)", "Manter e atualizar campos (upsert)"],
                index=0
            )
            dry_run = st.checkbox(
                "Simular importação (dry-run) — não grava no banco", value=True)
            chunk_size = st.number_input(
                "Tamanho do lote (chunk) para inserção", min_value=50, max_value=1000, value=200, step=50)

            if st.button("Importar dados"):
                # normaliza e prepara registros
                dados = [
                    {k: (v.strftime('%Y-%m-%d') if isinstance(v, (pd.Timestamp, datetime.date)) else v)
                     for k, v in row.items() if pd.notnull(v) and v != ""}
                    for row in df.to_dict(orient="records")
                ]

                # ids existentes no banco
                ids = [d.get('_id') for d in dados if d.get('_id') is not None]
                existentes_cursor = collection.find(
                    {"_id": {"$in": ids}}, {"_id": 1})
                ids_existentes = set([d["_id"] for d in existentes_cursor])

                registros_novos = [d for d in dados if d.get(
                    '_id') not in ids_existentes]
                registros_existentes = [
                    d for d in dados if d.get('_id') in ids_existentes]

                st.write(
                    f"Total linhas: {len(dados)} — Novos: {len(registros_novos)} — Existentes: {len(registros_existentes)}")

                if dry_run:
                    st.success(
                        "Dry-run ativo — nenhuma alteração será feita no banco.")
                    # mostra amostra de registros novos/existentes
                    if registros_novos:
                        st.write("Exemplo de novos registros (primeiros 5):")
                        st.dataframe(pd.DataFrame(registros_novos[:5]))
                    if registros_existentes:
                        st.write(
                            "Exemplo de registros existentes (primeiros 5):")
                        st.dataframe(pd.DataFrame(registros_existentes[:5]))
                    st.stop()

                # execução real: processa registros de acordo com opções
                inserted = 0
                updated = 0
                errors = []

                from pymongo.errors import DuplicateKeyError, BulkWriteError

                # upsert parcial: atualiza somente campos não-nulos (exceto _id)
                def merge_and_upsert(doc):
                    _id = doc.get('_id')
                    if _id is None:
                        errors.append(
                            {'_id': None, 'errmsg': 'Documento sem _id; não será upsertado', 'op': doc})
                        return
                    update_fields = {k: v for k, v in doc.items(
                    ) if k != '_id' and v is not None and v != ""}
                    if update_fields:
                        try:
                            collection.update_one(
                                {'_id': _id}, {'$set': update_fields}, upsert=True)
                        except Exception as e:
                            errors.append({'_id': _id, 'errmsg': str(e)})

                # validar documentos sem _id antes de inserir/atualizar
                sem_id = [d for d in dados if d.get('_id') is None]
                if sem_id:
                    st.warning(
                        f"{len(sem_id)} linhas sem _id encontradas — serão inseridas com ObjectId automático. Verifique referências.")
                    # opcional: listar exemplos
                    st.dataframe(pd.DataFrame(sem_id[:5]))

                # inserir novos em chunks (ordered=False para prosseguir em erros)
                for i in range(0, len(registros_novos), chunk_size):
                    chunk = registros_novos[i:i+chunk_size]
                    try:
                        res = collection.insert_many(chunk, ordered=False)
                        inserted += len(res.inserted_ids)
                    except BulkWriteError as bwe:
                        write_errors = bwe.details.get("writeErrors", [])
                        inserted += len(chunk) - len(write_errors)
                        for we in write_errors:
                            err = {'index': we.get('index'), 'op': we.get(
                                'op'), 'errmsg': we.get('errmsg')}
                            errors.append(err)
                    except Exception as e:
                        errors.append({'op_chunk': i, 'errmsg': str(e)})

                # tratar existentes conforme escolha do usuário (usar a variável 'conflito' corretamente)
                if conflito == "Pular duplicatas":
                    pass
                elif conflito == "Sobrescrever (replace)":
                    for doc in registros_existentes:
                        _id = doc.get('_id')
                        try:
                            collection.replace_one(
                                {"_id": _id}, doc, upsert=False)
                            updated += 1
                        except Exception as e:
                            errors.append({"_id": _id, "errmsg": str(e)})
                elif conflito == "Manter e atualizar campos (upsert)":
                    for doc in registros_existentes:
                        merge_and_upsert(doc)
                        updated += 1

                # relatório final
                st.write("Relatório da importação:")
                st.success(f"Inseridos: {inserted}  —  Atualizados: {updated}")
                if errors:
                    st.error(
                        f"Ocorreram {len(errors)} erros. Exibir detalhes abaixo.")
                    st.json(errors)
                    df_err = pd.json_normalize(errors)
                    csv_err = df_err.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "Baixar CSV de erros", data=csv_err, file_name="import_errors.csv", mime="text/csv"
                    )
        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {e}")