import pandas as pd
import numpy as np
import streamlit as st
import time
from io import BytesIO
from datetime import datetime, date
from metodos import criar_bandeira, to_excel

st.set_page_config(layout='wide', page_title='Processamento de dados', page_icon='📊')

if "data" not in st.session_state or st.session_state.data is None:
    st.warning("Antes de tudo, carregue o banco de dados com os códigos e lista de labels na página Home.")
    st.stop()

st.title('Pré-Processamento de Dados Estatísticos')
st.divider()
st.subheader('Aqui você pode criar novas bandeiras combinando colunas existentes na sua base de dados.')
st.write('')

colunas = st.session_state.data.columns.tolist()
selected_columns = st.multiselect('Selecione as colunas que serão utilizadas para criar a nova bandeira:', 
                                  colunas, 
                                  key="criar_bandeira_selected_columns")

if selected_columns:
    qtd_colunas = len(selected_columns)
    if qtd_colunas > 2:
        st.warning("❌ Você pode selecionar no máximo 2 colunas para criar a nova bandeira.")
    elif qtd_colunas == 1:
        st.info("ℹ️ Por favor, selecione 2 colunas para criar uma bandeira combinada.")
    else:
        st.success("✅ Duas colunas selecionadas com sucesso!")
        coluna1, coluna2 = st.columns(2)
        for i, col in enumerate(selected_columns):
            if i % 2 == 0:
                with coluna1:
                    st.write(f'Labels da coluna {col}:')
                    labels_col = st.session_state.lista_labels[st.session_state.lista_labels['Coluna'] == col][['Codigo', 'Label']]
                    st.dataframe(labels_col, hide_index=True)
            else:
                with coluna2:
                    st.write(f'Labels da coluna {col}:')
                    labels_col = st.session_state.lista_labels[st.session_state.lista_labels['Coluna'] == col][['Codigo', 'Label']]
                    st.dataframe(labels_col, hide_index=True)

    nome_bandeira = st.text_input(label="📝 Insira o nome da nova bandeira", placeholder="nome da nova bandeira", key="criar_nome_bandeira")

    if nome_bandeira in st.session_state.data.columns:
        st.error(f"❌ A coluna '{nome_bandeira}' já existe no DataFrame. Por favor, escolha outro nome.")
    else:
        # lógica para criar a nova bandeira com base nas colunas selecionadas
        if st.button('Criar bandeira', key="btn_criar_bandeira") and selected_columns and nome_bandeira:
            # Criação de uma nova coluna "Bandeira" com base nas colunas selecionadas
            data, lista_labels = criar_bandeira(st.session_state.data, st.session_state.lista_labels, selected_columns, nome_bandeira)
            st.session_state.data = data
            st.session_state.lista_labels = lista_labels
            st.session_state.ultima_bandeira = nome_bandeira
            st.success('✅ Bandeira criada com sucesso!')

            # Se já existe uma última bandeira criada, reexibe sempre que voltar pra página
            ultima = st.session_state.get("ultima_bandeira")
            if ultima:
                st.dataframe(
                    st.session_state.lista_labels[st.session_state.lista_labels["Coluna"] == ultima][["Codigo", "Label"]],
                    hide_index=True
                )

                freq = st.session_state.data[ultima].value_counts(dropna=False).rename("Frequência").to_frame()
                freq["%"] = (freq["Frequência"] / freq["Frequência"].sum() * 100).round(2)
                total_line = round(pd.DataFrame(freq.sum()).T)
                total_line.index = ['Total']
                freq = pd.concat([freq, total_line], ignore_index=False)
                freq["Código"] = freq.index
                st.dataframe(freq[["Código", "Frequência", "%"]], hide_index=True)

            excel_data = to_excel(st.session_state.data, st.session_state.lista_labels)
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.write('')
            st.write('')
            st.download_button(
                label="📥 Baixar arquivo Excel",
                data=excel_data,
                file_name=f'Base de dados atualizada - {now}.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )

st.write('')
st.divider()
if st.button("🔄 Recarregar página"):
    st.rerun()
