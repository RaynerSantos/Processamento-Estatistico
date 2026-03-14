import pandas as pd
import numpy as np
import streamlit as st
import time
from io import BytesIO
from datetime import datetime, date
from metodos import criar_bandeira, to_excel, mensagem_sucesso

st.set_page_config(layout='wide', page_title='Processamento de Dados', 
                   page_icon='images/Logo_Expertise.png')

st.logo(image="images/ExpertiseAI.svg", size="large") # Expertise_Marca_OffWhite_mini.jpg


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


st.write("")
st.write("")
# Upload das planilhas
data_file = st.file_uploader("📂 Selecione o banco de dados (em xlsx)", 
                             type=["xlsx"], 
                             help="Selecione o arquivo Excel contendo o **BANCO DE DADOS**, a **LISTA DE LABELS** e a **LISTA DE VARIÁVEIS**", 
                             key="home_uploader")

if data_file is not None:
    # Lista as abas disponíveis (ajuda muito a evitar erro)
    xls = pd.ExcelFile(data_file)
    st.caption(f"Abas encontradas no arquivo: {',  '.join(xls.sheet_names)}")
    st.success("Planilha carregada com sucesso!", icon="✅")
    st.write("")
    st.write("")

    coluna1, coluna2, coluna3 = st.columns(3, vertical_alignment="center", gap="small")
    with st.form('sheet_name_data'):
        with coluna1:
            with st.container(border=True):
                # nome_sheet_DATA = st.text_input(
                #     label="📝 Informe o nome da aba (sheet) que contém o banco de dados com os **CÓDIGOS**.", 
                #     value="BD_CODIGOS"
                #     )
                nome_sheet_DATA = st.selectbox(
                    label="📝 Informe o nome da aba (sheet) que contém o banco de dados com os **CÓDIGOS**.",
                    options=xls.sheet_names,
                    key="home_nome_sheet_DATA"
                )
                with st.status("🔍 A seguir, veja uma imagem de exemplo do **banco de dados**:"):
                    st.image(image="images/BD_CODIGOS.png")

        with coluna2:
            with st.container(border=True):
                # nome_sheet_lista_labels = st.text_input(
                #     label="📝 Informe o nome da aba (sheet) que contém a **Lista de Labels**.", 
                #     value="LISTA_LABELS"
                #     )
                nome_sheet_lista_labels = st.selectbox(
                    label="📝 Informe o nome da aba (sheet) que contém a **Lista de Labels**.",
                    options=xls.sheet_names,
                    key="home_nome_sheet_lista_labels"
                )
                with st.status("🔍 A seguir, veja uma imagem de exemplo com a **Lista de Labels**:"):
                    st.image(image="images/Lista de Labels.png")

        with coluna3:
            with st.container(border=True):
                # nome_sheet_lista_variaveis = st.text_input(
                #     label="📝 Informe o nome da aba (sheet) que contém a **Lista de variáveis**.", 
                #     value="LISTA_VARIAVEIS"
                #     )
                nome_sheet_lista_variaveis = st.selectbox(
                    label="📝 Informe o nome da aba (sheet) que contém a **Lista de variáveis**.",
                    options=xls.sheet_names,
                    key="home_nome_sheet_lista_variaveis"
                )
                with st.status("🔍 A seguir, veja uma imagem de exemplo com a **Lista de variáveis**:"):
                    st.image(image="images/Lista de variaveis.png")
        input_buttom_submit_DATA = st.form_submit_button("Enviar", icon=":material/done_outline:")

    if input_buttom_submit_DATA:
        # Salvar os nomes das abas
        st.session_state.nome_sheet_DATA = nome_sheet_DATA
        st.session_state.nome_sheet_lista_labels = nome_sheet_lista_labels
        st.session_state.nome_sheet_lista_variaveis = nome_sheet_lista_variaveis

        if not st.session_state.nome_sheet_DATA or not st.session_state.nome_sheet_lista_labels or not st.session_state.nome_sheet_lista_variaveis:
            st.error("Preencha os três nomes de abas antes de continuar.", icon="❌")
        else:
            st.success("Nome das abas (sheets) enviado com sucesso", icon="✅")

        nome_sheet_DATA = st.session_state.get("nome_sheet_DATA", "")
        nome_sheet_lista_labels = st.session_state.get("nome_sheet_lista_labels", "")
        nome_sheet_lista_variaveis = st.session_state.get("nome_sheet_lista_variaveis", "")

        # Validações antes de ler
        if not nome_sheet_DATA or not nome_sheet_lista_labels or not nome_sheet_lista_variaveis:
            st.warning("Envie (submit) os nomes das abas acima antes de carregar as tabelas.", icon="⚠️")
            st.stop()

        if nome_sheet_DATA not in xls.sheet_names:
            st.error(f"A aba do banco de dados com os **CÓDIGOS** '{nome_sheet_DATA}' não existe no arquivo.", icon="❌")
            st.stop()

        if nome_sheet_lista_labels not in xls.sheet_names:
            st.error(f"A aba com a **Lista de Labels** '{nome_sheet_lista_labels}' não existe no arquivo.", icon="❌")
            st.stop()

        if nome_sheet_lista_variaveis not in xls.sheet_names:
            st.error(f"A aba com a **Lista de Variáveis** '{nome_sheet_lista_variaveis}' não existe no arquivo.", icon="❌")
            st.stop()

        data = pd.read_excel(data_file, sheet_name=st.session_state.nome_sheet_DATA)
        lista_labels = pd.read_excel(data_file, sheet_name=st.session_state.nome_sheet_lista_labels)
        lista_variaveis = pd.read_excel(data_file, sheet_name=st.session_state.nome_sheet_lista_variaveis, header=1)

        lista_labels = lista_labels.iloc[1:, :].copy()
        lista_labels.columns = ['Coluna', 'Codigo', 'Label']
        lista_labels["Coluna"] = lista_labels["Coluna"].ffill().str.strip()

        lista_variaveis.columns = ["Coluna", "Rotulo"]

        st.session_state.data = data
        st.session_state.lista_labels = lista_labels
        st.session_state.lista_variaveis = lista_variaveis

        # Normalizar "Codigo" para numérico (trocando vírgula por ponto)
        lista_labels["Codigo"] = (lista_labels["Codigo"].astype(str).str.strip().str.replace(',', '.', regex=False))
        lista_labels['Codigo'] = pd.to_numeric(lista_labels["Codigo"], errors='coerce')
else:
    if "data" not in st.session_state and "lista_labels" not in st.session_state and "lista_variaveis" not in st.session_state:
        st.info("Faça o upload do Excel na Home para começar.")

st.write('') 
with st.spinner("Please wait..."):
    if "data" in st.session_state and "lista_labels" in st.session_state and "lista_variaveis" in st.session_state:
        st.write('')
        with st.expander("📅 Dicionário de variáveis:"):
            st.dataframe(
                st.session_state.lista_variaveis, 
                hide_index=True, 
                selection_mode=["multi-row", "multi-cell"], 
                use_container_width=True
                )
        with st.expander("📋 Colunas"):
            # default_cols = [c for c in st.session_state.data.columns if c != 'POND']
            colunas = st.multiselect('Selecione as colunas que deseja visualizar:', 
                                    st.session_state.data.columns.tolist(), 
                                    default=st.session_state.data.columns.tolist(),
                                    key="home_colunas")
        dados_filtrados = st.session_state.data[colunas]
        st.dataframe(dados_filtrados, hide_index=True, selection_mode=["multi-row", "multi-cell"], use_container_width=True)

        excel_data = to_excel(st.session_state.data, st.session_state.lista_labels, st.session_state.lista_variaveis)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.download_button(
            label="📥 Baixar arquivo Excel",
            data=excel_data,
            file_name=f'Base de dados atualizada - {now}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            on_click=mensagem_sucesso
        )


st.write('')
st.divider()
if st.button("Recarregar página", icon="🔄"):
    st.rerun()
st.write('')
st.write('')
st.write('')
st.image(image="images/Expertise_Marca_VerdeEscuro_mini.jpg") # Expertise_Marca_VerdeEscuro_mini.jpg