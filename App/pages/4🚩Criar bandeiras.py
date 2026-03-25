import pandas as pd
import numpy as np
import streamlit as st
import time
from io import BytesIO
from datetime import datetime, date
from metodos import criar_bandeira

st.set_page_config(layout='wide', page_title='Processamento de dados', 
                   page_icon='images/Logo_Expertise.png')

st.logo(image="images/ExpertiseAI.svg", size="large")

if "bandeiras_criadas" not in st.session_state:
    st.session_state.bandeiras_criadas = []

if "data" not in st.session_state or st.session_state.data is None:
    st.warning("Antes de tudo, carregue o banco de dados com os códigos e lista de labels na página Home.", icon="⚠️")
    st.stop()

st.title('Pré-Processamento de Dados Estatísticos')
st.divider()
st.subheader('Aqui você pode criar novas bandeiras combinando colunas existentes na sua base de dados.')
st.write('')

with st.spinner("Please wait..."):
    with st.expander("📅 Dicionário de variáveis:"):
        st.dataframe(st.session_state.lista_variaveis, hide_index=True, selection_mode=["multi-row", "multi-cell"], use_container_width=True)

st.write('')

colunas = st.session_state.data.columns.tolist()
selected_columns = st.multiselect('Selecione as colunas que serão utilizadas para criar a nova bandeira:', 
                                  colunas, 
                                  key="criar_bandeira_selected_columns")

if selected_columns:
    qtd_colunas = len(selected_columns)
    if qtd_colunas > 2:
        st.warning("Você pode selecionar no máximo 2 colunas para criar a nova bandeira.", icon="⚠️")
    elif qtd_colunas == 1:
        # st.info("Por favor, selecione 2 colunas para criar uma bandeira combinada.", icon="ℹ️")
        rotulo = st.session_state.lista_variaveis.loc[st.session_state.lista_variaveis["Coluna"] == selected_columns[0], "Rotulo"].iloc[0]
        st.write(f'**{selected_columns[0]}**: {rotulo}')
        st.success("Uma coluna selecionada com sucesso!", icon="✅")
        st.write('')
        
    elif qtd_colunas == 2:
        rotulo = st.session_state.lista_variaveis.loc[st.session_state.lista_variaveis["Coluna"] == selected_columns[0], "Rotulo"].iloc[0]
        st.write(f'**{selected_columns[0]}**: {rotulo}')
        rotulo = st.session_state.lista_variaveis.loc[st.session_state.lista_variaveis["Coluna"] == selected_columns[1], "Rotulo"].iloc[0]
        st.write(f'**{selected_columns[1]}**: {rotulo}')
        st.success("Duas colunas selecionadas com sucesso!", icon="✅")
        st.write("")
        st.write("")
        coluna1, coluna2 = st.columns(2)
        for i, col in enumerate(selected_columns):
            if i % 2 == 0:
                with coluna1:
                    st.write(f'Labels da coluna **{col}**:')
                    labels_col = st.session_state.lista_labels[st.session_state.lista_labels['Coluna'] == col][['Codigo', 'Label']]
                    st.dataframe(labels_col, hide_index=True, use_container_width=True)
            else:
                with coluna2:
                    st.write(f'Labels da coluna **{col}**:')
                    labels_col = st.session_state.lista_labels[st.session_state.lista_labels['Coluna'] == col][['Codigo', 'Label']]
                    st.dataframe(labels_col, hide_index=True, use_container_width=True)

    nome_bandeira = st.text_input(label="📝 Digite o nome da nova bandeira", 
                                  placeholder="nome da nova bandeira", 
                                  key="criar_nome_bandeira")
    st.write("")
    st.write("")
    ROTULO_BANDEIRA = st.text_input(label="📝 Digite a informação sobre o que se trata a nova bandeira", 
                                  placeholder="Informação da nova bandeira", 
                                  key="rotulo_nome_bandeira")

    if nome_bandeira in st.session_state.data.columns:
        st.error(f"A coluna '{nome_bandeira}' já existe no DataFrame. Por favor, escolha outro nome.", icon="❌")
    else:
        if qtd_colunas == 2:
            # lógica para criar a nova bandeira com base nas colunas selecionadas
            if st.button('Criar bandeira', key="btn_criar_bandeira", icon=":material/done_outline:") and selected_columns and nome_bandeira:
                # Criação de uma nova coluna "Bandeira" com base nas colunas selecionadas
                data, lista_labels = criar_bandeira(st.session_state.data, 
                                                    st.session_state.lista_labels,
                                                    st.session_state.lista_variaveis, 
                                                    selected_columns, nome_bandeira, ROTULO_BANDEIRA)
                st.session_state.data = data
                st.session_state.lista_labels = lista_labels
                st.session_state.ultima_bandeira = nome_bandeira
                st.write('')
                st.success('Bandeira criada com sucesso!', icon="✅")
                st.session_state.bandeiras_criadas.append(st.session_state.ultima_bandeira)
                st.write('')

                coluna1, coluna2 = st.columns(2)
                with coluna1:
                    # Se já existe uma última bandeira criada, reexibe sempre que voltar pra página
                    ultima = st.session_state.get("ultima_bandeira")
                    if ultima:
                        st.dataframe(
                            st.session_state.lista_labels[st.session_state.lista_labels["Coluna"] == ultima][["Codigo", "Label"]],
                            hide_index=True,
                            use_container_width=True
                        )
                with coluna2:
                    freq = st.session_state.data[ultima].value_counts(dropna=False).rename("Frequência").to_frame()
                    freq["%"] = ( freq["Frequência"] / freq["Frequência"].sum() ).round(4)
                    total_line = round(pd.DataFrame(freq.sum()).T)
                    total_line.index = ['Total']
                    freq = pd.concat([freq, total_line], ignore_index=False)
                    freq["Código"] = freq.index
                    st.dataframe(freq[["Código", "Frequência", "%"]], hide_index=True,
                                 column_config={"%": st.column_config.NumberColumn("%", format="percent")},
                                 use_container_width=True)

        elif qtd_colunas == 1:
            if st.button('Criar bandeira', key="btn_criar_bandeira_uma_bandeira") and selected_columns and nome_bandeira:
                st.session_state.ultima_bandeira = nome_bandeira
                st.session_state.data[nome_bandeira] = st.session_state.data[selected_columns[0]]
                st.session_state.bandeiras_criadas.append(st.session_state.ultima_bandeira)
                freq = st.session_state.data[nome_bandeira].value_counts(dropna=False).rename("Frequência").to_frame()
                freq["%"] = ( freq["Frequência"] / freq["Frequência"].sum() ).round(4)
                total_line = round(pd.DataFrame(freq.sum()).T)
                total_line.index = ['Total']
                freq = pd.concat([freq, total_line], ignore_index=False)
                freq["Código"] = freq.index

                df_bandeira_unica = st.session_state.lista_labels.loc[st.session_state.lista_labels["Coluna"]==selected_columns[0]].copy()
                df_bandeira_unica["Coluna"] = st.session_state.ultima_bandeira
                st.session_state.lista_labels = pd.concat([st.session_state.lista_labels, df_bandeira_unica], axis=0)
                st.session_state.lista_variaveis.loc[len(st.session_state.lista_variaveis)] = [
                    st.session_state.ultima_bandeira, 
                    ROTULO_BANDEIRA
                ]

                dict_codigo_label = st.session_state.lista_labels.loc[st.session_state.lista_labels["Coluna"]==st.session_state.ultima_bandeira].set_index("Codigo")["Label"]
                freq["Código"] = freq.index
                freq["Label"] = freq["Código"].map(dict_codigo_label)
                freq.loc["Total", "Label"] = "Total"

                st.dataframe(freq[["Código", "Label", "Frequência", "%"]], hide_index=True, 
                            column_config={"%": st.column_config.NumberColumn("%", format="percent")},
                            use_container_width=True)

st.write('')
st.divider()
if st.button("Recarregar página", icon="🔄"):
    st.rerun()
st.write('')
st.write('')
st.write('')
st.image(image="images/Expertise_Marca_VerdeEscuro_mini.jpg")
