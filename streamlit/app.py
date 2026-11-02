import os
import requests
import streamlit as st
from widgets import __login__

@st.cache_data(ttl=60)
def carregar_alertas_estoque() -> dict:
    """Busca os alertas consolidados de reagentes na API FastAPI com cache de 60s."""
    backend_url = (
        st.secrets.get("api", {}).get("url")
        or st.secrets.get("BACKEND_URL")
        or os.environ.get("BACKEND_URL")
        or "http://localhost:8000"
    ).rstrip("/")

    rotas = [
        f"{backend_url}/estoque/alertas",
        f"{backend_url}/reagente/alertas",
    ]
    ultimo_erro = None
    for rota in rotas:
        try:
            resp = requests.get(rota, timeout=4)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code != 404:
                ultimo_erro = f"HTTP {resp.status_code}: {resp.text}"
        except Exception as e:
            ultimo_erro = str(e)
    if ultimo_erro:
        raise RuntimeError(ultimo_erro)
    return {}


# ---------------------------------------------------------
# 1. Configurações Globais
# ---------------------------------------------------------
from pathlib import Path

LOGO_PATH = str(Path(__file__).parent / "logo.png")

st.set_page_config(page_title="LABVEPI - UFPI", layout="wide", page_icon="🐾")
st.logo(LOGO_PATH)

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
        st.image(LOGO_PATH, width=150)
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
                dados_alertas = carregar_alertas_estoque()
                reagentes_alerta = dados_alertas.get("reagentes_com_alerta", [])
                totais = dados_alertas.get("totais", {})

                if not reagentes_alerta:
                    st.info("Todos os reagentes e lotes estão em conformidade! :material/thumb_up:")
                else:
                    n_reag = totais.get("total_reagentes_com_alerta", len(reagentes_alerta))
                    st.caption(f"**{n_reag}** reagente(s) requerem atenção:")

                    for r in reagentes_alerta:
                        nome = r.get("reagente_nome") or r.get("nome", "Sem nome")
                        qtd_tot = r.get("quantidade_total_unidades", 0)
                        resumo = r.get("resumo_estoque")
                        detalhe_qtd = f"{qtd_tot} un" + (f" ({resumo})" if resumo else "")
                        
                        baixo_estoque = r.get("baixo_estoque_global", False)
                        lotes_vencidos = r.get("lotes_vencidos", [])
                        lotes_vencendo = r.get("lotes_proximos_vencimento", [])

                        # Indicador de destaque visual do reagente
                        if lotes_vencidos:
                            bg_color = "#f8d7da"
                            border_color = "#dc3545"
                            title_color = "#721c24"
                        elif baixo_estoque:
                            bg_color = "#fff3cd"
                            border_color = "#ffc107"
                            title_color = "#856404"
                        else:
                            bg_color = "#fff3cd"
                            border_color = "#fd7e14"
                            title_color = "#664d03"

                        status_extra = " | ⚠️ Baixo Estoque" if baixo_estoque else ""
                        st.markdown(
                            f"""
                            <div style='background-color: {bg_color}; padding: 8px; border-radius: 6px; border-left: 5px solid {border_color}; margin-bottom: 8px;'>
                                <div style='font-size: 14px; font-weight: bold; color: {title_color};'>
                                    {nome}
                                </div>
                                <div style='font-size: 12px; color: {title_color};'>
                                    Estoque Total: <strong>{detalhe_qtd}</strong>{status_extra}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                        # Detalhamento de Lotes Vencidos
                        if lotes_vencidos:
                            for lv in lotes_vencidos:
                                num = lv.get("numero_lote", "S/L")
                                dt = lv.get("data_validade", "N/D")
                                dias = lv.get("dias_para_vencer")
                                qtd_lote = lv.get("quantidade_unidade", 1)
                                local = lv.get("local_armazenamento") or lv.get("reagente_local_armazenamento", "Local N/D")
                                info_dias = f" ({abs(dias)} dias atrás)" if dias is not None else ""
                                st.caption(f"• 🚨 Lote **{num}**: Venceu em {dt}{info_dias} | {qtd_lote} un ({local})")

                        # Detalhamento de Lotes Próximos do Vencimento
                        if lotes_vencendo:
                            for lp in lotes_vencendo:
                                num = lp.get("numero_lote", "S/L")
                                dt = lp.get("data_validade", "N/D")
                                dias = lp.get("dias_para_vencer")
                                qtd_lote = lp.get("quantidade_unidade", 1)
                                local = lp.get("local_armazenamento") or lp.get("reagente_local_armazenamento", "Local N/D")
                                info_dias = f" (restam {dias} dias)" if dias is not None else ""
                                st.caption(f"• ⚠️ Lote **{num}**: Vence {dt}{info_dias} | {qtd_lote} un ({local})")

                    # Redirecionamento seguro passando o objeto de página
                    if st.button("Ver Todos os Reagentes", key="btn_ver_reagentes", use_container_width=True):
                        st.switch_page(p_registros)

            except Exception as e:
                st.warning(f"⚠️ Não foi possível sincronizar alertas com o servidor backend: {e}")
                if st.button("Ver Todos os Reagentes", key="btn_ver_reagentes_fallback", use_container_width=True):
                    st.switch_page(p_registros)