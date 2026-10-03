import streamlit as st
import os
import pandas as pd
from datetime import datetime
from utils import check_usr_pass
from streamlit_option_menu import option_menu
from utils import (
    check_valid_name,
    check_valid_email,
    check_unique_email,
    check_unique_usr,
    register_new_usr,
    change_password,
)
from pymongo import MongoClient
from utils import connect_to_mongo

class __login__:
    def __init__(
        self,
        company_name: str,
        width,
        height,
        logout_button_name: str = 'Logout',
        hide_menu_bool: bool = False,
        hide_footer_bool: bool = False
    ):
        self.company_name = company_name
        self.width = width
        self.height = height
        self.logout_button_name = logout_button_name
        self.hide_menu_bool = hide_menu_bool
        self.hide_footer_bool = hide_footer_bool

    def get_username(self):
        return st.session_state.get('username', None)

    def check_auth_json_file_exists(self, auth_filename: str) -> bool:
        files = [
            f for f in os.listdir('./')
            if os.path.isfile(os.path.join('./', f))
        ]
        return any(auth_filename in f for f in files)

    def login_widget(self) -> None:
        if not st.session_state['LOGGED_IN']:
            with st.form("login_form"):
                username = st.text_input("Usuário")
                password = st.text_input("Senha", type="password")
                submitted = st.form_submit_button("Login")

                if submitted:
                    authenticated = check_usr_pass(username, password)
                    if not authenticated:
                        st.error("Usuário ou senha inválida")
                    else:
                        # Atualiza último login
                        db = connect_to_mongo()
                        last_login = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        db["usuarios"].update_one(
                            {"username": username},
                            {"$set": {"last_login": last_login}}
                        )

                        st.session_state['LOGGED_IN'] = True
                        st.session_state['username'] = username
                        # Armazena a role (matricula) do usuário na sessão
                        user_doc = db["usuarios"].find_one({"username": username})
                        st.session_state['matricula'] = user_doc.get('matricula', '') if user_doc else ''
                        st.rerun()

    def sign_up_widget(self) -> None:
        with st.form("register_form"):
            username_sign_up = st.text_input(
                "Usuário/Nome *", placeholder='Digite um usuário')
            unique_username_check = check_unique_usr(username_sign_up)

            email_sign_up = st.text_input(
                "Email *", placeholder='Digite seu email')
            valid_email_check = check_valid_email(email_sign_up)
            unique_email_check = check_unique_email(email_sign_up)

            password_sign_up = st.text_input("Senha *", type='password')
            matricula_sign_up = st.selectbox(
                "Tipo de Usuário *",
                ["Bolsista UFPI", "Bolsista Externo",
                    "Mestrando", "Doutorando", "Professor"]
            )

            submitted = st.form_submit_button("Registrar")
            if submitted:
                if not valid_email_check:
                    st.error("Digite um email válido")
                elif not unique_email_check:
                    st.error("Já existe uma conta com esse email")
                elif not unique_username_check:
                    st.error(f'O usuário {username_sign_up} já existe')
                else:
                    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    register_new_usr(
                        email_sign_up,
                        username_sign_up,
                        password_sign_up,
                        matricula_sign_up,
                        created_at
                    )
                    st.success("Registro realizado com sucesso!")

    def show_users_widget(self) -> None:
        db = connect_to_mongo()
        users = list(db["usuarios"].find({}, {"_id": 0}))
        for u in users:
            u['matricula'] = u.get('matricula', 'N/A')
            u['created_at'] = u.get('created_at', 'N/A')
            u['last_login'] = u.get('last_login', 'Nunca')

        df = pd.DataFrame(users)
        if not df.empty:
            st.title("Usuários Registrados")
            st.table(
                df[['username', 'name', 'email', 'matricula', 'created_at', 'last_login']])
        else:
            st.info("Nenhum usuário encontrado.")

    def logout_widget(self) -> None:
        if st.session_state['LOGGED_IN']:
            if st.sidebar.button(self.logout_button_name):
                st.session_state['LOGGED_IN'] = False
                st.session_state['username'] = None
                st.session_state['matricula'] = None
                st.rerun()

    def nav_sidebar(self):
        menu = st.sidebar.empty()
        with menu:
            selected = option_menu(
                menu_title='Navegação',
                menu_icon='list-columns-reverse',
                icons=[
                    'box-arrow-in-right',
                    'person-plus',
                    'x-circle',
                    'arrow-counterclockwise',
                    'file-plus'
                ],
                options=[
                    'Autenticação',
                    'Criar uma conta',
                    'Usuários'
                ],
                styles={
                    "container": {"padding": "5px"},
                    "nav-link": {
                        "font-size": "14px",
                        "text-align": "left",
                        "margin": "0px"
                    }
                }
            )
        return menu, selected

    def hide_menu(self) -> None:
        st.markdown(
            """<style>#MainMenu{visibility:hidden;}</style>""", unsafe_allow_html=True)

    def hide_footer(self) -> None:
        st.markdown(
            """<style>footer{visibility:hidden;}</style>""", unsafe_allow_html=True)

    def build_login_ui(self):
        # inicializa chaves de sessão
        st.session_state.setdefault('LOGGED_IN', False)
        st.session_state.setdefault('username', None)
        st.session_state.setdefault('matricula', None)

        if self.hide_menu_bool:
            self.hide_menu()
        if self.hide_footer_bool:
            self.hide_footer()

        return st.session_state['LOGGED_IN']