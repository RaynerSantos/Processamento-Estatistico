import pandas as pd
import numpy as np
import os
from collections import Counter
import io
from io import BytesIO
from databases.metodos import processamento
import streamlit as st
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

# CSS personalizado
st.markdown(
    """
    <style>
    /* Cor de fundo da página */
    [data-testid="stAppViewContainer"] {
        background-color: #000000;
    }
    
    /* Cor de fundo do cabeçalho */
    [data-testid="stHeader"] {
        background-color: #000000;
    }

    /* Cor de fundo da barra lateral */
    [data-testid="stSidebar"] {
        background-color: #333333;
    }

    /* Cor do título */
    h1 {
        color: #20541B; /* white */
        text-align: center;
    }

    /* Cor do subtítulo */
    h2 {
        color: #FFD700; /* Dourado */
    }

    /* Cor do texto normal */
    p, span {
        color: #FFFFFF; /* Branco */
    }

    /* Cor dos botões */
    button {
        background-color: #20541B !important;
        color: white !important;
    }

    /* Muda a cor do texto no menu de configurações */
    div[data-testid="stDropdownMenu"] * {
        color: black !important;
    }

    /* Opcional: ajusta a cor do fundo para contraste */
    div[data-testid="stDropdownMenu"] {
        background-color: white !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Função para salvar as tabelas em um único Excel com única aba
def salvar_excel_aba_unica(todas_tabelas_gerais, bd_processamento):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        worksheet = workbook.add_worksheet("Processamento_Estatistico")
        writer.sheets["Processamento_Estatistico"] = worksheet

        linha_atual = 0  # Controle da linha onde cada tabela será escrita
        percent_format = workbook.add_format({'num_format': '0.0%'})
        int_format = workbook.add_format({'num_format': '0'})
        float_format = workbook.add_format({'num_format': '0.0'})

        for i, tabela in enumerate(todas_tabelas_gerais):
            # Escreve o nome da tabela antes dela
            worksheet.write(linha_atual, 0, f'Tabela{i} - {bd_processamento["Var_Linha"][i]}')
            linha_atual += 1

            # Salva a tabela na linha atual
            tabela.to_excel(writer, sheet_name="Processamento_Estatistico", startrow=linha_atual, startcol=0)

            # Formatação personalizada (igual à função original, mas ajustando para a aba única)
            tipo = bd_processamento['TipoTabela'][i]
            tamanho = len(tabela)

            if tipo in ['NPS', 'IPA_10']:
                for row in range(linha_atual + 4, linha_atual + tamanho + 3): 
                    worksheet.set_row(row, None, percent_format)
                for row in range(linha_atual + len(tabela[:-2]) + 3, linha_atual + tamanho + 2):  
                    worksheet.set_row(row, None, float_format) 
                for row in range(linha_atual + len(tabela[:-2]) + 4, linha_atual + tamanho + 4): 
                    worksheet.set_row(row, None, int_format)

            elif tipo == 'MULTIPLA':
                for row in range(linha_atual + 4, linha_atual + tamanho + 4):
                    worksheet.set_row(row, None, percent_format)
                for row in range(linha_atual + len(tabela[:-2]) + 3, linha_atual + tamanho + 6): ###
                    worksheet.set_row(row, None, int_format) ###
                worksheet.set_row(linha_atual + tamanho + 3, None, float_format)

            else:
                for row in range(linha_atual + 3, linha_atual + tamanho + 4):
                    worksheet.set_row(row, None, percent_format)
                for row in range(linha_atual + len(tabela[:-2]) + 4, linha_atual + tamanho + 4):
                    worksheet.set_row(row, None, int_format)

            linha_atual += tamanho + 3 + 4  # Adiciona +4 para considerar o cabeçalho e +3 de espaçamento

    return output.getvalue()



# Função para salvar as tabelas em um único Excel com várias abas e formatação
def salvar_excel_com_formatacao(todas_tabelas_gerais, bd_processamento):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for i, tabela in enumerate(bd_processamento['Var_Linha']):
            nome_aba = f'Tabela{i} {tabela}'
            todas_tabelas_gerais[i].to_excel(writer, sheet_name=nome_aba, index=True)
            workbook = writer.book
            worksheet = writer.sheets[nome_aba]

            # Formatar as linhas que deverão estar com formatação de percentual
            percent_format = workbook.add_format({'num_format': '0.0%'})
            if (bd_processamento['TipoTabela'][i] == 'NPS') | (bd_processamento['TipoTabela'][i] == 'IPA_10'):
                tamanho = len(todas_tabelas_gerais[i])
                for row in range(4, tamanho+1):
                    worksheet.set_row(row, None, percent_format)
                # Formatar as linhas que não terão casas decimais
                num_format = workbook.add_format({'num_format': '0'})
                for row in range((len(todas_tabelas_gerais[i][:-2])+4), (len(todas_tabelas_gerais[i])+4)):
                    worksheet.set_row(row, None, num_format)

            elif (bd_processamento['TipoTabela'][i] == 'MULTIPLA'):
                tamanho = len(todas_tabelas_gerais[i])
                # Formatar as linhas que deverão estar com formatação de percentual
                for row in range(4, tamanho+1):
                    worksheet.set_row(row, None, percent_format)
                # Formatar as linhas que não terão casas decimais
                num_format = workbook.add_format({'num_format': '0'})
                for row in range((len(todas_tabelas_gerais[i])+1), (len(todas_tabelas_gerais[i])+2)):
                    worksheet.set_row(row, None, num_format)
                # Formatar o Índice de Multiplicidade que terá somente 1 casa decimal
                num_format = workbook.add_format({'num_format': '0.0'})
                for row in range((len(todas_tabelas_gerais[i])+3), (len(todas_tabelas_gerais[i])+4)):
                    worksheet.set_row(row, None, num_format)

            else:
                tamanho = len(todas_tabelas_gerais[i]) + 4
                # Formatar as linhas que deverão estar com formatação de percentual
                for row in range(3, tamanho+1):
                    worksheet.set_row(row, None, percent_format)
                # Formatar as linhas que não terão casas decimais
                num_format = workbook.add_format({'num_format': '0'})
                for row in range((len(todas_tabelas_gerais[i][:-2])+4), (len(todas_tabelas_gerais[i])+4)):
                    worksheet.set_row(row, None, num_format)

    return output.getvalue()

# # Configurações da página
# st.set_page_config(layout="centered")  # "wide"

#=== Título ===#
st.title("Processamento do Estatístico")
st.write("")
st.write("")
st.markdown(
    """
    <h5 style="color: white; text-align: center;">
        Faça o upload do banco de dados na versão CODIGOS e com a Lista de Labels e da planilha de sintaxe, <u><span style="font-weight: 900;">ambas em Excel</span></u> para realizar o Processamento.
    </h5>
    """,
    unsafe_allow_html=True
)

st.write("")
st.write("")

st.markdown(
    """
    📄 [Documentação do App em PDF](https://github.com/RaynerSantos/Processamento-Estatistico/blob/main/Documenta%C3%A7%C3%A3o%20-%20Processamento%20do%20Estat%C3%ADstico.pdf)
    
    📥 [Exemplo da Sintaxe](https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fraw.githubusercontent.com%2FRaynerSantos%2FProcessamento-Estatistico%2Frefs%2Fheads%2Fupdate-solicitado-sintaxe%2FSintaxe_Exemplo.xlsx&wdOrigin=BROWSELINK)
    """,
    unsafe_allow_html=True
)

st.write("")
st.write("")


# Upload das planilhas
with st.form(key='sheet_name_data'):
    nome_sheet_DATA = st.text_input(label="📝 Insira o nome da sheet (aba) no qual contém o banco de dados com os CODIGOS", value="BD_CODIGOS")
    nome_sheet_lista_labels = st.text_input(label="📝 Insira o nome da sheet (aba) no qual contém a Lista de Labels", value="Lista de Labels")
    input_buttom_submit_DATA = st.form_submit_button("Enviar")
st.session_state.nome_sheet_DATA = nome_sheet_DATA
st.session_state.nome_sheet_lista_labels = nome_sheet_lista_labels
if input_buttom_submit_DATA:
    st.write("Nome da sheet (aba) da planilha enviado com sucesso ✅")

data_file = st.file_uploader("📂 Selecione o banco de dados (em xlsx)", type=["xlsx"])
sintaxe_file = st.file_uploader("📂 Selecione a planilha com a Sintaxe para a criação das tabelas (em xlsx)", type=["xlsx"])

if data_file and sintaxe_file:
    # Guarde os "UploadedFile" em variáveis distintas
    nome_sheet_DATA = st.session_state.nome_sheet_DATA
    nome_sheet_lista_labels = st.session_state.nome_sheet_lista_labels
    data = pd.read_excel(data_file, sheet_name=nome_sheet_DATA)
    bd_processamento = pd.read_excel(sintaxe_file)
    lista_labels = pd.read_excel(data_file, sheet_name=nome_sheet_lista_labels)
    st.write("✅ Planilhas carregadas com sucesso!")

st.write("")
st.write("")

# Formato do output (uma única aba ou para cada tabela processada gerar uma nova aba)
with st.form(key='output_excel'):
    tipo_output = st.selectbox(label='Informe a opção do formato para o output desejado', options=['Única aba', 'Várias abas'])
    excel_name = st.text_input(label='Informe o nome desejado para a planilha com o output do Processamento  Estatístico')
    processar_dados = st.form_submit_button("Processar Dados")
    st.session_state.tipo_output = tipo_output
    st.session_state.excel_name = excel_name

# Botão para processar os dados
if processar_dados:
    # Processar os dados e obter as tabelas
    todas_tabelas_gerais = processamento(data=data, bd_processamento=bd_processamento, lista_labels=lista_labels)
    
    if tipo_output == 'Várias abas':
        # Salvar em Excel com formatação
        excel_data = salvar_excel_com_formatacao(todas_tabelas_gerais, bd_processamento=bd_processamento)
    elif tipo_output == 'Única aba':
        # Salvar em Excel com formatação
        excel_data = salvar_excel_aba_unica(todas_tabelas_gerais, bd_processamento=bd_processamento)
    
    # Link para download
    st.download_button(
        label="Baixar Excel Processado",
        data=excel_data,
        file_name=st.session_state.excel_name + ".xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )