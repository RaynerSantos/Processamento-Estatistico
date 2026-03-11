import pandas as pd
import numpy as np
import streamlit as st
import time
from io import BytesIO
from datetime import datetime, date
from metodos import criar_bandeira, to_excel


st.set_page_config(layout='wide', page_title='Processamento de dados', page_icon='📊')



st.title('Processamento de Dados Estatísticos')

st.sidebar.title('Navegação')
select_box = st.sidebar.selectbox(label='Selecione a opção desejada:', options=('Criar bandeiras', 'Recode', 'Ponderação', 'Processamento'))

if select_box == 'Criar bandeiras':
    st.write('')
    st.write('')
    st.write('Suba a base de dados e selecione as colunas para criar a nova bandeira.')
    with st.form('sheet_name_data'):
        nome_sheet_DATA = st.text_input(label="📝 Insira o nome da sheet (aba) no qual contém o banco de dados com os CODIGOS", value="BD_CODIGOS")
        nome_sheet_lista_labels = st.text_input(label="📝 Insira o nome da sheet (aba) no qual contém a Lista de Labels", value="Lista de Labels")
        input_buttom_submit_DATA = st.form_submit_button("Enviar")
    st.session_state.nome_sheet_DATA = nome_sheet_DATA
    st.session_state.nome_sheet_lista_labels = nome_sheet_lista_labels
    if input_buttom_submit_DATA:
        st.success("✅ Nome da sheet (aba) da planilha enviado com sucesso")

    st.write('')
    data_file = st.file_uploader("📂 Selecione o banco de dados (em xlsx)", type=["xlsx"])

    if data_file:
        # Guarde os "UploadedFile" em variáveis distintas
        nome_sheet_DATA = st.session_state.nome_sheet_DATA
        nome_sheet_lista_labels = st.session_state.nome_sheet_lista_labels
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
        st.success("✅ Planilhas carregadas com sucesso!")

        st.write('')
        st.write('')
        if st.checkbox('Visualizar base de dados'):
            with st.expander("Colunas"):
                colunas = st.multiselect('Selecione as colunas que deseja visualizar:', st.session_state.data.columns.tolist(), default=[col for col in st.session_state.data.columns if col != 'POND'])
            dados_filtrados = st.session_state.data[colunas]
            st.dataframe(dados_filtrados, hide_index=True)

        st.write('')
        st.write('')
        if st.checkbox('Selecione as colunas que serão utilizadas para criar a nova bandeira'):
            colunas = data.columns.tolist()
            selected_columns = st.multiselect('Selecione as colunas:', colunas)

            if selected_columns:
                coluna1, coluna2 = st.columns(2)
                for i, col in enumerate(selected_columns):
                    if i % 2 == 0:
                        with coluna1:
                            st.write(f'Labels da coluna {col}:')
                            labels_col = lista_labels[lista_labels['Coluna'] == col][['Codigo', 'Label']]
                            st.dataframe(labels_col, hide_index=True)
                    else:
                        with coluna2:
                            st.write(f'Labels da coluna {col}:')
                            labels_col = lista_labels[lista_labels['Coluna'] == col][['Codigo', 'Label']]
                            st.dataframe(labels_col, hide_index=True)

                # with st.form('name_bandeira'):
                nome_bandeira = st.text_input(label="📝 Insira o nome da nova bandeira", value="nome da nova bandeira")
                # input_buttom_submit_DATA = st.form_submit_button("Enviar")
                st.session_state.nome_bandeira = nome_bandeira
                if st.session_state.nome_bandeira in data.columns:
                    st.error(f"❌ A coluna '{st.session_state.nome_bandeira}' já existe no DataFrame. Por favor, escolha outro nome.")
                # if input_buttom_submit_DATA:
                #     st.write("Nome da nova bandeira enviado com sucesso ✅")
                #     st.write('')

                # lógica para criar a nova bandeira com base nas colunas selecionadas
                if st.button('Criar bandeira'):
                    # Criação de uma nova coluna "Bandeira" com base nas colunas selecionadas
                    data, lista_labels = criar_bandeira(data, lista_labels, selected_columns, st.session_state.nome_bandeira)
                    st.session_state.data = data
                    st.session_state.lista_labels = lista_labels
                    st.success('✅ Bandeira criada com sucesso!')
                    st.dataframe(lista_labels[lista_labels['Coluna'] == st.session_state.nome_bandeira], hide_index=True)
                    st.write('')
                    st.write('Frequência da nova bandeira:')
                    freq_bandeira = pd.DataFrame(st.session_state.data[st.session_state.nome_bandeira].value_counts())
                    freq_bandeira['%'] = round(freq_bandeira['count'] / freq_bandeira['count'].sum() * 100, 2)
                    total_line = round(pd.DataFrame(freq_bandeira.sum()).T)
                    total_line.index = ['Total']
                    freq_bandeira = pd.concat([freq_bandeira, total_line], ignore_index=False)
                    freq_bandeira['Código'] = freq_bandeira.index
                    freq_bandeira = freq_bandeira[['Código', 'count', '%']]
                    freq_bandeira.columns = ['Código', 'Frequência', '%']
                    st.dataframe(freq_bandeira, hide_index=True)

                    # st.write('')
                    # if st.button('Deseja criar outra bandeira?'):
                    #     if st.checkbox('Selecione as colunas que serão utilizadas para criar a nova bandeira'):
                    #         colunas = st.session_state.data.columns.tolist()
                    #         selected_columns = st.multiselect('Selecione as colunas:', colunas)
                    #         nome_bandeira = st.text_input(label="📝 Insira o nome da nova bandeira", value="nome da nova bandeira")
                    #         st.session_state.nome_bandeira = nome_bandeira
                    #         if st.session_state.nome_bandeira in st.session_state.data.columns:
                    #             st.error(f"❌ A coluna '{st.session_state.nome_bandeira}' já existe no DataFrame. Por favor, escolha outro nome.")
                    #         # st.experimental_rerun()

                    #         # Criação de uma nova coluna "Bandeira" com base nas colunas selecionadas
                    #         if st.button('Criar bandeira'):
                    #             data, lista_labels = criar_bandeira(data, lista_labels, selected_columns, st.session_state.nome_bandeira)
                    #             st.session_state.data = data
                    #             st.session_state.lista_labels = lista_labels
                    #             st.success('✅ Bandeira criada com sucesso!')
                    #             st.dataframe(lista_labels[lista_labels['Coluna'] == st.session_state.nome_bandeira], hide_index=True)
                    #             st.write('')
                    #             st.write('Frequência da nova bandeira:')
                    #             st.dataframe(data[st.session_state.nome_bandeira].value_counts(), hide_index=False)

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
                        

    
elif select_box == 'Recode':
    st.write('')
    st.write('')
    st.subheader('Recode de variáveis')




elif select_box == 'Processamento':
    st.subheader('Processamento de tabelas estatísticas')


st.write("")
st.write("")
st.write("")
if st.button("🔄 Recarregar página"):
    st.rerun()