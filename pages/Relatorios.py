import streamlit as st
from pymongo import MongoClient
import os
import pandas as pd
import plotly.express as px
import unicodedata

# --- Conexão ao MongoDB ---
from utils import connect_to_mongo

db = connect_to_mongo()
animais_col = db['animais']
amostras_col = db['amostras']
exames_col = db['exames']
reagentes_col = db['reagentes']

st.title("Relatórios e Estatísticas do Sistema")

# --- normalização do campo sexo ---
def normalize_sexo_raw(val):
    if val is None:
        return "indeterminado"
    s = str(val).strip().lower()
    # remover acentos
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    # mapear variantes comuns
    if s in ("femea", "femea.", "f", "f.", "fem", "fêmea", "female", "feminino", "feminino."):
        return "femea"
    if s in ("macho", "m", "m.", "male", "masculino", "masculino."):
        return "macho"
    # valores que indicam desconhecido/indeterminado
    if s in ("", "nao informado", "nao", "n/a", "none", "indeterminado", "desconhecido", "unknown"):
        return "indeterminado"
    # fallback simples: tenta detectar por prefixo
    if s.startswith("f"):
        return "femea"
    if s.startswith("m"):
        return "macho"
    return "indeterminado"

# --- Coleta de Dados ---
animais = list(animais_col.find())
amostras = list(amostras_col.find())
exames = list(exames_col.find())
reagentes = list(reagentes_col.find())

# normalizar antes de criar DataFrame/relatórios
df_animais = pd.DataFrame(animais)
if not df_animais.empty:
    if "sexo" in df_animais.columns:
        df_animais["sexo_normalizado"] = df_animais["sexo"].apply(
            normalize_sexo_raw)
    else:
        df_animais["sexo_normalizado"] = "indeterminado"

# --- KPIs ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Animais cadastrados", len(animais))
col2.metric("Amostras cadastradas", len(amostras))
col3.metric("Exames cadastrados", len(exames))
col4.metric("Reagentes cadastrados", len(reagentes))

st.markdown("---")

# --- Gráfico: Animais por Sexo (usar coluna normalizada) ---
if not df_animais.empty and "sexo_normalizado" in df_animais.columns:
    fig = px.histogram(df_animais, x="sexo_normalizado",
                       category_orders={"sexo_normalizado": [
                           "femea", "macho", "indeterminado"]},
                       title="Distribuição dos Animais por Sexo")
    st.plotly_chart(fig, use_container_width=True)

# --- Gráfico: Amostras por Método de Coleta e Status ---
df_amostras = pd.DataFrame(amostras)
if not df_amostras.empty:
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        if "metodo_coleta" in df_amostras.columns:
            fig2 = px.histogram(df_amostras, x="metodo_coleta",
                                title="Amostras por Método de Coleta")
            st.plotly_chart(fig2, use_container_width=True)
    with col_g2:
        col_status = "status_amostra" if "status_amostra" in df_amostras.columns else ("status" if "status" in df_amostras.columns else None)
        if col_status:
            fig_st = px.histogram(df_amostras, x=col_status,
                                  title="Amostras por Status (status_amostra)")
            st.plotly_chart(fig_st, use_container_width=True)

# --- Gráfico: Exames por Tipo ---
df_exames = pd.DataFrame(exames)
if not df_exames.empty and "tipo_exame" in df_exames.columns:
    fig3 = px.histogram(df_exames, x="tipo_exame", title="Exames por Tipo")
    st.plotly_chart(fig3, use_container_width=True)

# --- Gráfico: Reagentes (Estoque em Unidades) ---
df_reagentes = pd.DataFrame(reagentes)
if not df_reagentes.empty:
    if "quantidade_unidade" in df_reagentes.columns or "quantidade" in df_reagentes.columns:
        df_reagentes["qtd_unidade"] = df_reagentes.apply(
            lambda r: r.get("quantidade_unidade") if pd.notna(r.get("quantidade_unidade")) else r.get("quantidade", 0),
            axis=1
        )
        if "nome" in df_reagentes.columns:
            fig4 = px.bar(df_reagentes, x="nome", y="qtd_unidade", title="Estoque de Reagentes (Unidades)")
            st.plotly_chart(fig4, use_container_width=True)

# --- Tabelas detalhadas (opcional) ---
with st.expander("Ver tabelas detalhadas"):
    st.subheader("Animais")
    # mostrar coluna original e a normalizada
    if not df_animais.empty:
        display_df = df_animais.copy()
        # garantir ordenação de colunas com a normalizada ao final
        if "sexo_normalizado" in display_df.columns:
            cols = [c for c in display_df.columns if c !=
                    "sexo_normalizado"] + ["sexo_normalizado"]
            display_df = display_df[cols]
        st.dataframe(display_df)
    else:
        st.info("Nenhum animal cadastrado.")
    st.subheader("Amostras")
    st.dataframe(df_amostras)
    st.subheader("Exames")
    st.dataframe(df_exames)
    st.subheader("Reagentes")
    st.dataframe(df_reagentes)