import pandas as pd
import numpy as np
import streamlit as st
import time
from io import BytesIO
from datetime import datetime, date
from metodos import recode_variavel

st.set_page_config(layout='wide', page_title='Processamento de dados',
                   page_icon='images/Logo_Expertise.png')

st.logo(image="images/ExpertiseAI.svg", size="large")

if "data" not in st.session_state or st.session_state.data is None:
    st.warning("Antes de tudo, carregue o banco de dados com os códigos e lista de labels na página Home.")
    st.stop()

st.title('Pré-Processamento de Dados Estatísticos')
st.divider()
st.subheader('Aqui você pode realizar recodes simples em suas variáveis existentes.')
st.write('')

with st.spinner("Please wait..."):
    with st.expander("📅 Dicionário de variáveis:"):
        st.dataframe(st.session_state.lista_variaveis, hide_index=True, selection_mode=["multi-row", "multi-cell"])

st.write('')

colunas = st.session_state.data.columns.tolist()
selected_column = st.selectbox('Selecione a coluna que será recodificada:', colunas, key="recode_selected_column")

if selected_column:
    rotulo = st.session_state.lista_variaveis.loc[st.session_state.lista_variaveis["Coluna"] == selected_column, "Rotulo"].iloc[0]
    st.write(f'**{selected_column}**: {rotulo}')
    st.write('')

    dataframe_recode = st.session_state.lista_labels[st.session_state.lista_labels['Coluna'] == selected_column][['Codigo', 'Label']].copy()
    dataframe_recode = dataframe_recode.rename(columns={'Codigo': 'Codigo', 'Label': 'Label'})
    dataframe_recode['Label nova'] = None
    dataframe_recode['Ordem'] = None
    
    dataframe_recode_edited = st.data_editor(dataframe_recode, 
                                             num_rows="fixed", 
                                            #  use_container_width=True, 
                                             key="dataframe_recode_editor", 
                                             hide_index=True)
    
    nome_bandeira_recode = st.text_input(
        label="📝 Insira o nome da nova bandeira recodificada", 
        placeholder="nome da nova bandeira recodificada", 
        key="recode_nome_bandeira"
    )

    if nome_bandeira_recode in st.session_state.data.columns:
        st.error(f"A coluna '{nome_bandeira_recode}' já existe no DataFrame. Por favor, escolha outro nome.", 
                 icon="⚠️")
        

    if st.button('Realizar recode', key="btn_recode") and nome_bandeira_recode:
        # st.dataframe(dataframe_recode_edited, hide_index=True)

        data, lista_labels = recode_variavel(
            data=st.session_state.data,
            lista_labels=st.session_state.lista_labels,
            COLUNA_ORIGINAL=selected_column,
            NOVA_BANDEIRA=nome_bandeira_recode,
            dataframe_recode=dataframe_recode_edited
        )
        st.session_state.data = data
        st.session_state.lista_labels = lista_labels
        st.session_state.ultima_bandeira = nome_bandeira_recode
        st.success('✅ Recode realizado com sucesso!')

        # Exibir a frequência da nova bandeira criada
        ultima = st.session_state.ultima_bandeira
        st.write(f'Frequência da nova bandeira: {ultima}')

        freq = st.session_state.data[ultima].value_counts(dropna=False).rename("Frequência").to_frame()
        freq["%"] = ( freq["Frequência"] / freq["Frequência"].sum() ).round(4)
        total_line = round(pd.DataFrame(freq.sum()).T)
        total_line.index = ['Total']
        freq = pd.concat([freq, total_line], ignore_index=False)
        freq["Código"] = freq.index

        dict_codigo_label = st.session_state.lista_labels.loc[st.session_state.lista_labels["Coluna"]==st.session_state.ultima_bandeira].set_index("Codigo")["Label"]
        freq["Código"] = freq.index
        freq["Label"] = freq["Código"].map(dict_codigo_label)
        freq.loc["Total", "Label"] = "Total"

        st.dataframe(freq[["Código", "Label", "Frequência", "%"]], hide_index=True,
                        column_config={"%": st.column_config.NumberColumn("%", format="percent")})


st.write('')
st.divider()
if st.button("Recarregar página", icon="🔄"):
    st.rerun()
st.write('')
st.write('')
st.write('')
st.image(image="images/Expertise_Marca_VerdeEscuro_mini.jpg")  