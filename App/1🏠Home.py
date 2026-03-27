import pandas as pd
import numpy as np
import streamlit as st
from io import BytesIO
from auth import login_gate, logout, change_password_gate, open_change_password

st.set_page_config(layout='wide', page_title='Processamento de Dados', 
                   page_icon='images/Logo_Expertise.png')

st.logo(image="images/ExpertiseAI.svg", size="large") # Expertise_Marca_OffWhite_mini.jpg

# Bloqueia a app até o usuário autenticar
login_gate()
change_password_gate()

# Barra simples no topo
col1, col2, col3 = st.columns([15, 3, 2], vertical_alignment='center')
with col1:
    st.caption(f"Usuário logado: {st.session_state.user['NOME']}")
with col2:
    st.button("Alterar Senha", icon="🔒", on_click=open_change_password)
with col3:
    st.button("Sair", on_click=logout)


st.write("")
st.write("")
st.title('Processamento de Dados Estatísticos')

st.write("")
st.divider()

st.markdown(
    """
    <h5 style="color: "#20541B"; text-align: center;">
        Faça o upload do banco de dados na versão CODIGOS, com a Lista de Labels e com a Lista de Variáveis, <u><span style="font-weight: 900;">ambas em Excel</span></u> para realizar o Processamento.
    </h5>
    """,
    unsafe_allow_html=True
)

@st.cache_data(show_spinner="Lendo arquivo Excel...")
def obter_abas_excel(file_bytes: bytes):
    xls = pd.ExcelFile(BytesIO(file_bytes))
    return xls.sheet_names


@st.cache_data(show_spinner="Carregando e tratando planilhas...")
def carregar_planilhas(
    file_bytes: bytes,
    nome_sheet_data: str,
    nome_sheet_lista_labels: str,
    nome_sheet_lista_variaveis: str
):
    xls = pd.ExcelFile(BytesIO(file_bytes))

    data = xls.parse(nome_sheet_data)

    # Lê só as colunas que você usa
    lista_labels = xls.parse(
        nome_sheet_lista_labels
    )

    lista_variaveis = xls.parse(
        nome_sheet_lista_variaveis,
        header=1
    )

    # Tratamentos
    lista_labels = lista_labels.iloc[1:, :].copy()
    lista_labels.columns = ["Coluna", "Codigo", "Label"]
    lista_labels["Coluna"] = lista_labels["Coluna"].ffill().astype(str).str.strip()

    # Normalizar "Codigo" para numérico (trocando vírgula por ponto)
    lista_labels["Codigo"] = (
        lista_labels["Codigo"]
        .astype(str)
        .str.strip()
        .str.replace(",", ".", regex=False)
    )
    lista_labels["Codigo"] = pd.to_numeric(lista_labels["Codigo"], errors="coerce")

    lista_variaveis = lista_variaveis.iloc[:, :2].copy()
    lista_variaveis.columns = ["Coluna", "Rotulo"]

    return data, lista_labels, lista_variaveis


def limpar_home():
    for chave in [
        "home_uploader",
        "home_nome_sheet_DATA",
        "home_nome_sheet_lista_labels",
        "home_nome_sheet_lista_variaveis",
        "home_colunas_preview",
        "nome_sheet_DATA",
        "nome_sheet_lista_labels",
        "nome_sheet_lista_variaveis",
        "data",
        "lista_labels",
        "lista_variaveis",
    ]:
        st.session_state.pop(chave, None)


st.write("")
st.write("")
# Upload das planilhas
data_file = st.file_uploader("📂 Selecione o banco de dados (em xlsx)", 
                             type=["xlsx"], 
                             help="Selecione o arquivo Excel contendo o **BANCO DE DADOS**, a **LISTA DE LABELS** e a **LISTA DE VARIÁVEIS**", 
                             key="home_uploader")

if data_file is not None:
    # # Lista as abas disponí­veis (ajuda muito a evitar erro)
    # xls = pd.ExcelFile(data_file)
    file_bytes = data_file.getvalue()
    sheet_names = obter_abas_excel(file_bytes)

    st.caption(f"Abas encontradas no arquivo: {',  '.join(sheet_names)}")
    st.success("Planilha carregada com sucesso!", icon="✅")
    st.write("")
    st.write("")

    coluna1, coluna2, coluna3 = st.columns(3, vertical_alignment="center", gap="small")

    with st.form('sheet_name_data'):
        with coluna1:
            with st.container(border=True):
                nome_sheet_DATA = st.selectbox(
                    label="📝 Informe o nome da aba (sheet) que contém o banco de dados com os **CÓDIGOS**.",
                    options=sheet_names,
                    key="home_nome_sheet_DATA"
                )
                with st.status("🔍 A seguir, veja uma imagem de exemplo do **banco de dados**:"):
                    st.image(image="images/BD_CODIGOS.png")

        with coluna2:
            with st.container(border=True):
                nome_sheet_lista_labels = st.selectbox(
                    label="📝 Informe o nome da aba (sheet) que contém a **Lista de Labels**.",
                    options=sheet_names,
                    key="home_nome_sheet_lista_labels"
                )
                with st.status("🔍 A seguir, veja uma imagem de exemplo com a **Lista de Labels**:"):
                    st.image(image="images/Lista de Labels.png")

        with coluna3:
            with st.container(border=True):
                nome_sheet_lista_variaveis = st.selectbox(
                    label="📝 Informe o nome da aba (sheet) que contém a **Lista de variáveis**.",
                    options=sheet_names,
                    key="home_nome_sheet_lista_variaveis"
                )
                with st.status("🔍 A seguir, veja uma imagem de exemplo com a **Lista de variáveis**:"):
                    st.image(image="images/Lista de variaveis.png")
        input_buttom_submit_DATA = st.form_submit_button("Enviar", icon=":material/done_outline:")

    if input_buttom_submit_DATA:
        # # Salvar os nomes das abas
        # st.session_state.nome_sheet_DATA = nome_sheet_DATA
        # st.session_state.nome_sheet_lista_labels = nome_sheet_lista_labels
        # st.session_state.nome_sheet_lista_variaveis = nome_sheet_lista_variaveis

        # if not st.session_state.nome_sheet_DATA or not st.session_state.nome_sheet_lista_labels or not st.session_state.nome_sheet_lista_variaveis:
        #     st.error("Preencha os três nomes de abas antes de continuar.", icon="❌")
        # else:
        #     st.success("Nome das abas (sheets) enviado com sucesso", icon="✅")

        # nome_sheet_DATA = st.session_state.get("nome_sheet_DATA", "")
        # nome_sheet_lista_labels = st.session_state.get("nome_sheet_lista_labels", "")
        # nome_sheet_lista_variaveis = st.session_state.get("nome_sheet_lista_variaveis", "")

        # # Validação antes de ler
        # if not nome_sheet_DATA or not nome_sheet_lista_labels or not nome_sheet_lista_variaveis:
        #     st.warning("Envie (submit) os nomes das abas acima antes de carregar as tabelas.", icon="⚠️")
        #     st.stop()

        if nome_sheet_DATA not in sheet_names:
            st.error(f"A aba do banco de dados com os **CÓDIGOS** '{nome_sheet_DATA}' não existe no arquivo.", icon="❌")
            st.stop()

        elif nome_sheet_lista_labels not in sheet_names:
            st.error(f"A aba com a **Lista de Labels** '{nome_sheet_lista_labels}' não existe no arquivo.", icon="❌")
            st.stop()

        elif nome_sheet_lista_variaveis not in sheet_names:
            st.error(f"A aba com a **Lista de Variáveis** '{nome_sheet_lista_variaveis}' não existe no arquivo.", icon="❌")
            st.stop()
        
        else:
            data, lista_labels, lista_variaveis = carregar_planilhas(
                file_bytes=file_bytes,
                nome_sheet_data=nome_sheet_DATA,
                nome_sheet_lista_labels=nome_sheet_lista_labels,
                nome_sheet_lista_variaveis=nome_sheet_lista_variaveis
            )

            st.session_state.nome_sheet_DATA = nome_sheet_DATA
            st.session_state.nome_sheet_lista_labels = nome_sheet_lista_labels
            st.session_state.nome_sheet_lista_variaveis = nome_sheet_lista_variaveis
            st.session_state.data = data
            st.session_state.lista_labels = lista_labels
            st.session_state.lista_variaveis = lista_variaveis

            st.success("Abas carregadas com sucesso!", icon="✅")
      
else:
    if not all(k in st.session_state for k in ["data", "lista_labels", "lista_variaveis"]):
        st.info("Faça o upload do Excel na Home para começar.")

st.write('') 
with st.spinner("Please wait..."):
    if all(k in st.session_state for k in ["data", "lista_labels", "lista_variaveis"]):
        st.write("")
        with st.expander("📅 Dicionário de variáveis:"):
            st.dataframe(
                st.session_state.lista_variaveis, 
                hide_index=True, 
                selection_mode=["multi-row", "multi-cell"], 
                width='stretch'
                )
        # with st.expander("📋 Colunas"):
        #     # default_cols = [c for c in st.session_state.data.columns if c != 'POND']
        #     colunas = st.multiselect('Selecione as colunas que deseja visualizar:', 
        #                             st.session_state.data.columns.tolist(), 
        #                             default=st.session_state.data.columns.tolist(),
        #                             key="home_colunas")
        # dados_filtrados = st.session_state.data[colunas]
        # st.dataframe(dados_filtrados, hide_index=True, selection_mode=["multi-row", "multi-cell"], width='stretch')
        # Atualiza visualização só quando o usuário mandar
        with st.form("preview_cols_form"):
            colunas_disponiveis = st.session_state.data.columns.tolist()
            default_cols = colunas_disponiveis[:30]  # evita renderizar tudo de cara
            with st.expander("📋 Colunas"):
                colunas_preview = st.multiselect(
                    "Selecione as colunas que deseja visualizar:",
                    colunas_disponiveis,
                    default=colunas_disponiveis,
                    key="home_colunas_preview"
                )

            qtd_linhas = st.number_input(
                "Quantidade de linhas para pré-visualizar:",
                min_value=10,
                max_value=20000,
                value=200,
                step=50
            )

            atualizar_preview = st.form_submit_button("Atualizar visualização")

        if atualizar_preview or "home_colunas_preview" in st.session_state:
            cols = st.session_state.get("home_colunas_preview", default_cols)
            if cols:
                st.dataframe(
                    st.session_state.data[cols].head(qtd_linhas),
                    hide_index=True,
                    width="stretch"
                )


st.write('')
st.divider()
if st.button("Recarregar página", icon="🔄", on_click=limpar_home):
    st.rerun()
st.write('')
st.write('')
st.write('')
st.image(image="images/Expertise_Marca_VerdeEscuro_mini.jpg") # Expertise_Marca_VerdeEscuro_mini.jpg
