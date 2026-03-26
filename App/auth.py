import hashlib
import hmac
import pyodbc
import streamlit as st
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
import pandas as pd
import secrets
from datetime import datetime
from metodos import mensagem_login_sucesso, mensagem_senha_sucesso

@st.cache_resource
def get_connection():
    cfg = st.secrets["sqlserver"]

    conn_str = (
        f"DRIVER={{{cfg['driver']}}};"
        f"SERVER={cfg['server']};"
        f"DATABASE={cfg['database']};"
        f"UID={cfg['username']};"
        f"PWD={cfg['password']};"
        f"Encrypt={cfg.get('encrypt', 'yes')};"
        f"TrustServerCertificate={cfg.get('trust_server_certificate', 'no')};"
    )

    conn_url = "mssql+pyodbc:///?odbc_connect=" + quote_plus(conn_str)
    engine = create_engine(conn_url, pool_pre_ping=True)
    return engine



def authenticate_user(login: str, password: str):
    engine = get_connection()

    query = text("""
        SELECT *
        FROM dbo.usuarios_processamento
        WHERE LOGIN = :login
    """)

    with engine.connect() as connection:
        df_usuarios_processamento = pd.read_sql_query(
            query,
            connection,
            params={"login": login}
        )
    
    senha_correta = df_usuarios_processamento.loc[df_usuarios_processamento["LOGIN"]==login, "SENHA"].iloc[0]
    
    if password == senha_correta:
        return {
            "ID": df_usuarios_processamento.loc[df_usuarios_processamento["LOGIN"]==login, "ID"].iloc[0],
            "LOGIN": login,
            "NOME": df_usuarios_processamento.loc[df_usuarios_processamento["LOGIN"]==login, "NOME"].iloc[0],
            "PERFIL": df_usuarios_processamento.loc[df_usuarios_processamento["LOGIN"]==login, "PERFIL"].iloc[0]
        }
    else:
        return None


def init_auth_state():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if "user" not in st.session_state:
        st.session_state.user = None


def atualizar_senha_usuario(login: str, nova_senha: str) -> bool:
    engine = get_connection()

    query = text("""
        UPDATE dbo.usuarios_processamento
        SET SENHA = :nova_senha
        WHERE LOGIN = :login
    """)

    with engine.begin() as connection:
        result = connection.execute(
            query,
            {
                "login": login,
                "nova_senha": nova_senha
            }
        )

    # print("result.rowcount: ", result.rowcount)
    return result.rowcount > 0



def open_change_password():
    st.session_state.change_password_mode = True
    st.rerun()


def change_password_gate():
    if not st.session_state.get("change_password_mode", False):
        return

    st.title("Alterar senha")
    st.write("")

    with st.form("form_alterar_senha", clear_on_submit=False):
        nova_senha = st.text_input("Digite a nova senha", type="password")
        confirmar_senha = st.text_input("Digite a nova senha novamente", type="password")
        submitted_alterar_senha = st.form_submit_button(
            "Alterar senha", 
            icon=":material/done_outline:", 
            on_click=mensagem_senha_sucesso
        )

    col1, col2 = st.columns([2, 8])
    with col1:
        if st.button("Voltar", icon=":material/arrow_back:"):
            st.session_state.change_password_mode = False
            st.rerun()

    if submitted_alterar_senha:
        if nova_senha != confirmar_senha:
            st.error("❌ As senhas não coincidem.")
        elif nova_senha.strip() == "":
            st.warning("⚠️ A nova senha não pode estar em branco.")
        else:
            sucesso = atualizar_senha_usuario(st.session_state.user["LOGIN"], nova_senha)

            if sucesso:
                st.success("✅ Senha alterada com sucesso.")
                st.session_state.change_password_mode = False
                st.rerun()
            else:
                st.error("❌ Usuário não encontrado ou senha não alterada.")
                  
    st.stop()


def save_user_access(user: str, now: datetime):
    engine = get_connection()

    query = text("""
            INSERT INTO [dbo].[acessos_comandos]
                 ([USUARIO], [DATA], [PROJETO])
            VALUES 
                 (:user, :datetime, :project)
    """)

    try: 
        with engine.begin() as connection:
            result = connection.execute(
                query,
                {
                    "user": user,
                    "datetime": now,
                    'project': 'Processamento de Dados'
                }
            )
        return result.rowcount > 0
    except Exception as e:
        st.error(f"Erro ao salvar acesso: {e}")
        return False


def logout():
    st.session_state.authenticated = False
    st.session_state.user = None
    st.rerun()


def login_gate():
    init_auth_state()

    if st.session_state.authenticated:
        return

    st.title("Acesso à plataforma")

    with st.form("form_login", clear_on_submit=False):
        login = st.text_input("Login")
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar", on_click=mensagem_login_sucesso)

    if submitted:
        login = login.strip()

        if not login or not password:
            st.error("Informe login e senha.")
            st.stop()

        user = authenticate_user(login, password)

        if user is None:
            st.error("Login ou senha inválidos.")
            st.stop()

        st.session_state.authenticated = True
        st.session_state.user = user

        now = datetime.now()
        save_user_access(user=st.session_state.user['LOGIN'], now=now)
        st.rerun()


    st.stop()
