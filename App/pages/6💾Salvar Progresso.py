import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime
from metodos import to_excel, mensagem_sucesso


st.set_page_config(layout='wide', page_title='Processamento de Dados', 
                   page_icon='images/Logo_Expertise.png')

st.logo(image="images/ExpertiseAI.svg", size="large") # Expertise_Marca_OffWhite_mini.jpg

if "data" not in st.session_state or st.session_state.data is None:
    st.warning("Antes de tudo, carregue o banco de dados com os códigos e lista de labels na página Home.", icon="⚠️")
    st.stop()


st.title('Processamento de Dados Estatísticos')
st.divider()
st.subheader('Aqui você pode fazer o download de seu Banco de Dados atualizado')
st.write('')


@st.cache_data(show_spinner="Preparando arquivo Excel para download...")
def gerar_excel_download(data, lista_labels, lista_variaveis):
    # to_excel deve retornar bytes ou BytesIO
    return to_excel(data, lista_labels, lista_variaveis)


@st.fragment
def render_download_button(excel_data, file_name):
    st.download_button(
        label="📥 Baixar arquivo Excel",
        data=excel_data,
        file_name=file_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        on_click=mensagem_sucesso,
        key="download_excel_btn",
        use_container_width=False,
    )


if all(k in st.session_state for k in ["data", "lista_labels", "lista_variaveis"]):
    data = st.session_state.data
    lista_labels = st.session_state.lista_labels
    lista_variaveis = st.session_state.lista_variaveis

    # Gera o nome do arquivo uma única vez por sessão desta página
    if "download_file_timestamp" not in st.session_state:
        st.session_state.download_file_timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")

    file_name = f"Base de dados atualizada - {st.session_state.download_file_timestamp}.xlsx"

    # 1) Gera/cacheia o Excel primeiro
    excel_data = gerar_excel_download(data, lista_labels, lista_variaveis)

    # 2) Mostra o botão logo no topo
    render_download_button(excel_data, file_name)

    st.write("")
    st.write("")

    # 3) Pré-visualizações leves e opcionais
    with st.expander("📅 Dicionário de variáveis"):
        st.dataframe(
            lista_variaveis,
            hide_index=True,
            width="stretch"
        )

    with st.expander("👀 Pré-visualizar base de dados"):
        with st.form("preview_form"):
            colunas_disponiveis = data.columns.tolist()
            default_cols = colunas_disponiveis[:10]  # evita carregar tudo de cara

            colunas = st.multiselect(
                "Selecione as colunas que deseja visualizar:",
                colunas_disponiveis,
                default=default_cols,
                key="download_preview_cols"
            )

            qtd_linhas = st.number_input(
                "Quantidade de linhas para pré-visualizar:",
                min_value=10,
                max_value=5000,
                value=200,
                step=50,
                key="download_preview_rows"
            )

            ver_preview = st.form_submit_button("Atualizar visualização")

        # mostra preview mesmo após reruns, sem precisar clicar toda hora
        cols_escolhidas = st.session_state.get("download_preview_cols", default_cols)
        linhas_escolhidas = st.session_state.get("download_preview_rows", 200)

        if cols_escolhidas:
            st.dataframe(
                data[cols_escolhidas].head(linhas_escolhidas),
                hide_index=True,
                width="stretch"
            )


st.write('')
st.divider()
st.write('')
st.write('')
st.image(image="images/Expertise_Marca_VerdeEscuro_mini.jpg") # Expertise_Marca_VerdeEscuro_mini.jpg