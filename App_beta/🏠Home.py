import pandas as pd
import numpy as np
import streamlit as st
import time
from io import BytesIO
from datetime import datetime, date
from metodos import criar_bandeira, to_excel, mensagem_sucesso

st.set_page_config(layout='wide', page_title='Processamento de Dados', 
                   page_icon='images/LOGO_Expertise_Marca_VerdeEscuro.jpg')

st.logo(image="images/Expertise_Marca_OffWhite_mini.jpg", size="large")


st.title('Processamento de Dados Estatísticos')

st.write("")
st.divider()

st.markdown(
    """
    <h5 style="color: "#20541B"; text-align: center;">
        Faça o upload do banco de dados na versão CODIGOS e com a Lista de Labels, <u><span style="font-weight: 900;">ambas em Excel</span></u> para realizar o Processamento.
    </h5>
    """,
    unsafe_allow_html=True
)


st.write("")
st.write("")
# Upload das planilhas
coluna1, coluna2 = st.columns(2)
with st.form('sheet_name_data'):
    with coluna1:
        nome_sheet_DATA = st.text_input(label="📝 Insira o nome da sheet (aba) no qual contém o banco de dados com os CODIGOS", value="BD_CODIGOS")
    with coluna2:
        nome_sheet_lista_labels = st.text_input(label="📝 Insira o nome da sheet (aba) no qual contém a Lista de Labels", value="Lista de Labels")
    input_buttom_submit_DATA = st.form_submit_button("Enviar")
# Guardar os "UploadedFile" em variáveis distintas
st.session_state.nome_sheet_DATA = nome_sheet_DATA
st.session_state.nome_sheet_lista_labels = nome_sheet_lista_labels
if input_buttom_submit_DATA:
    st.success("Nome das sheets (abas) da planilha enviado com sucesso", icon="✅")

st.write('')
data_file = st.file_uploader("📂 Selecione o banco de dados (em xlsx)", 
                             type=["xlsx"], 
                             help="Selecione o arquivo Excel contendo os dados e a lista de labels", 
                             key="home_uploader")

if data_file is not None:
    data = pd.read_excel(data_file, sheet_name=nome_sheet_DATA)
    lista_labels = pd.read_excel(data_file, sheet_name=nome_sheet_lista_labels)

    lista_labels = lista_labels.iloc[1:, :].copy()
    lista_labels.columns = ['Coluna', 'Codigo', 'Label']
    lista_labels["Coluna"] = lista_labels["Coluna"].ffill().str.strip()

    st.session_state.data = data
    st.session_state.lista_labels = lista_labels

    # Normalizar "Codigo" para numérico (trocando vírgula por ponto)
    lista_labels["Codigo"] = (lista_labels["Codigo"].astype(str).str.strip().str.replace(',', '.', regex=False))
    lista_labels['Codigo'] = pd.to_numeric(lista_labels["Codigo"], errors='coerce')
    st.success("Planilha carregada com sucesso!", icon="✅")

if "data" in st.session_state and "lista_labels" in st.session_state:
    st.write('')
    st.write('')
    with st.spinner("Please wait..."):
        with st.expander("Colunas"):
            default_cols = [c for c in st.session_state.data.columns if c != 'POND']
            colunas = st.multiselect('Selecione as colunas que deseja visualizar:', 
                                    st.session_state.data.columns.tolist(), 
                                    default=default_cols,
                                    key="home_colunas")
        dados_filtrados = st.session_state.data[colunas]
        st.dataframe(dados_filtrados, hide_index=True, selection_mode=["multi-row", "multi-cell"])

        excel_data = to_excel(st.session_state.data, st.session_state.lista_labels)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.download_button(
            label="📥 Baixar arquivo Excel",
            data=excel_data,
            file_name=f'Base de dados atualizada - {now}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            on_click=mensagem_sucesso
        )
else:
    st.info("Faça o upload do Excel na Home para começar.")

st.write('')
st.divider()
if st.button("Recarregar página", icon="🔄"):
    st.rerun()

st.image(image="images/Expertise_Marca_VerdeEscuro_mini.jpg")