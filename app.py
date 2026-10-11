import streamlit as st
from datetime import datetime, timedelta
from pymongo import MongoClient
from widgets import __login__
from utils import connect_to_mongo, get_reagente_quantidade

# ---------------------------------------------------------
# 1. Configurações Globais
# ---------------------------------------------------------
st.set_page_config(page_title="LABVEPI - UFPI", layout="wide", page_icon="🐾")
st.logo("logo.png")

# Inicialização segura do estado da sessão
st.session_state.setdefault('LOGGED_IN', False)
st.session_state.setdefault('username', None)
st.session_state.setdefault('matricula', None)

# Instância do gerenciador de login
__login__obj = __login__(
    company_name="UFPI",
    width=200, height=250,
    logout_button_name='Logout'
)

# ---------------------------------------------------------
# 2. Definição da Página Inicial (Cabeçalho no Topo + Abas Abaixo)
# ---------------------------------------------------------
def pagina_inicio():
    # Logo e cabeçalho sempre no topo da área principal
    col1, col2 = st.columns([1, 4], vertical_alignment="center")
    with col1:
        st.image("logo.png", width=150)
    with col2:
        st.markdown(
            """
            <h1 style='font-size: 28px; margin: 0; padding: 0;'>
                LABVEPI - Laboratório de Vigilância de Epizootias - UFPI
            </h1>
            """,
            unsafe_allow_html=True
        )
    st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)

    # Conteúdo condicional abaixo do cabeçalho
    if not st.session_state['LOGGED_IN']:
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            tab_login, tab_cadastro = st.tabs([":material/login: Fazer Login", ":material/person_add: Criar uma Conta"])
            with tab_login:
                st.markdown("##### Acesso ao Sistema")
                __login__obj.login_widget()
            with tab_cadastro:
                st.markdown("##### Solicitar Novo Acesso")
                __login__obj.sign_up_widget()
    else:
        st.success(f"Sessão ativa: **{st.session_state['username']}** ({st.session_state.get('matricula', 'Colaborador')})")
        
        tab_painel, tab_users, tab_novo_user = st.tabs([":material/info: Informações", ":material/group: Listar Usuários", ":material/add: Cadastrar Usuário"])
        with tab_painel:
            st.markdown(
                """
                ### Sistema de Rastreabilidade Biológica
                Utilize o menu lateral para navegar entre os módulos cadastrados:
                - **Novo Registro:** Inserção de espécimes, tecidos e amostras primárias.
                - **Editar Amostra:** Gestão volumétrica, fracionamento de alíquotas e descarte.
                - **Registros:** Painel geral de reagentes, espécimes e armazenamento.
                - **Relatórios:** Emissão e auditoria de laudos laboratoriais.
                """
            )
        with tab_users:
            __login__obj.show_users_widget()
        with tab_novo_user:
            __login__obj.sign_up_widget()

# ---------------------------------------------------------
# 3. Roteamento de Páginas com st.navigation
# ---------------------------------------------------------
p_inicio = st.Page(pagina_inicio, title="Início", icon=":material/home:", default=True)
p_novo = st.Page("pages/Novo_Registro.py", title="Novo Registro", icon=":material/add:")
p_novo_animal = st.Page("forms/registro_animal.py", title="Novo Registro Animal", icon=":material/add:")
p_editar = st.Page("pages/Editar_Amostra.py", title="Editar Amostra", icon=":material/edit:")
p_importar = st.Page("pages/Importar.py", title="Importar", icon=":material/upload:")
p_registros = st.Page("pages/Registros.py", title="Registros", icon=":material/table_view:")
p_relatorios = st.Page("pages/Relatorios.py", title="Relatórios", icon=":material/analytics:")

if st.session_state['LOGGED_IN']:
    pg = st.navigation({
        "Geral": [p_inicio],
        "Operacional": [
            p_novo, 
            p_editar, 
            p_importar
        ],
        "Consultas & Dados": [p_registros, p_relatorios]
    })
else:
    pg = st.navigation([p_inicio])

# RENDERIZA A PÁGINA ESCOLHIDA PRIMEIRO
pg.run()

# ---------------------------------------------------------
# 4. Sidebar Global (Renderizada DEPOIS de pg.run())
# ---------------------------------------------------------
if st.session_state['LOGGED_IN']:
    with st.sidebar:
        st.markdown(f":material/person: **{st.session_state['username']}**")
        st.caption(f"Perfil: {st.session_state.get('matricula', 'Colaborador')}")
        
        if st.button("Sair", icon=":material/logout:", key="btn_logout_global", use_container_width=True):
            st.session_state['LOGGED_IN'] = False
            st.session_state['username'] = None
            st.session_state['matricula'] = None
            st.rerun()

        with st.expander(":material/notifications: Sistema de Alertas", expanded=False):
            try:
                db = connect_to_mongo()
                reagentes_col = db['reagentes']

                # Consulta de baixo estoque (prioriza 'quantidade_unidade' e aceita 'quantidade' legado)
                todos_reagentes = list(reagentes_col.find())
                reagentes_baixo_estoque = [
                    r for r in todos_reagentes
                    if get_reagente_quantidade(r) <= 2
                ]

                # Consulta de validade (próximos 30 dias)
                data_hoje = datetime.now().strftime('%Y-%m-%d')
                data_limite = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
                reagentes_vencendo = list(reagentes_col.find({
                    "data_validade": {
                        "$lte": data_limite,
                        "$gte": data_hoje
                    }
                }))

                # Consulta de já vencidos (validade menor que hoje)
                reagentes_vencidos = list(reagentes_col.find({
                    "data_validade": {
                        "$lt": data_hoje
                    }
                }))

                if not reagentes_baixo_estoque and not reagentes_vencendo and not reagentes_vencidos:
                    st.info("Nenhum alerta pendente! :material/thumb_up:")
                else:
                    if reagentes_baixo_estoque:
                        st.markdown(
                            f"""
                            <div style='background-color: #fff3cd; padding: 8px; border-radius: 5px; border-left: 5px solid #ffc107; margin-bottom: 8px;'>
                            <strong style='color: #856404;'>⚠️ Baixo Estoque ({len(reagentes_baixo_estoque)})</strong>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        for r in reagentes_baixo_estoque:
                            qtd = get_reagente_quantidade(r)
                            vol_info = f" | {r.get('quantidade_volume')} vol" if r.get('quantidade_volume') else ""
                            st.caption(f"• **{r.get('nome', 'Sem nome')}**: {qtd} un{vol_info} ({r.get('local_armazenamento', 'Local N/D')})")

                    if reagentes_vencendo:
                        st.markdown(
                            f"""
                            <div style='background-color: #fff3cd; padding: 8px; border-radius: 5px; border-left: 5px solid #ffc107; margin-bottom: 8px;'>
                            <strong style='color: #856404;'>⚠️ Vencendo em breve ({len(reagentes_vencendo)})</strong>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        for r in reagentes_vencendo:
                            st.caption(f"• **{r.get('nome', 'Sem nome')}**: Vence {r.get('data_validade', 'Data N/D')}")

                    if reagentes_vencidos:
                        st.markdown(
                            f"""
                            <div style='background-color: #f8d7da; padding: 8px; border-radius: 5px; border-left: 5px solid #dc3545; margin-bottom: 8px;'>
                            <strong style='color: #721c24;'>🚨 Vencidos ({len(reagentes_vencidos)})</strong>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        for r in reagentes_vencidos:
                            st.caption(f"• **{r.get('nome', 'Sem nome')}**: Venceu em {r.get('data_validade', 'Data N/D')}")

                    # Redirecionamento seguro passando o objeto de página
                    if st.button("Ver Todos os Reagentes", key="btn_ver_reagentes", use_container_width=True):
                        st.switch_page(p_registros)

            except Exception as e:
                st.error(f"Falha na conexão de alertas: {e}")