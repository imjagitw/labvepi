import streamlit as st
from forms import (
    render_form_registro_animal,
    render_form_registro_amostra,
    render_form_registro_exame,
    render_form_registro_reagente,
)

# --- Configurações Iniciais ---
st.set_page_config(layout="wide")

# --- Verificação de Login ---
if not st.session_state.get("LOGGED_IN"):
    st.warning("Você precisa fazer login para acessar esta página.")
    st.stop()

# --- Título Principal ---
st.title("Novo Registro no Sistema")

# --- Abas para Registro ---
tab_animal, tab_amostra, tab_exame, tab_reagente = st.tabs([
    "Registrar Animal",
    "Registrar Amostra",
    "Registrar Exame",
    "Registrar Reagente"
])

# --- Aba: Registrar Animal ---
with tab_animal:
    render_form_registro_animal()

# --- Aba: Registrar Amostra ---
with tab_amostra:
    render_form_registro_amostra()

# --- Aba: Registrar Exame ---
with tab_exame:
    render_form_registro_exame()

# --- Aba: Registrar Reagente ---
with tab_reagente:
    render_form_registro_reagente()