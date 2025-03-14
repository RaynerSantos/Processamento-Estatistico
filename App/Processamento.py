import pandas as pd
import numpy as np
import os
from collections import Counter
import io
from io import BytesIO
from databases.metodos import processamento
import streamlit as st

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
        color: #20541B; /* Branco */
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
# st.write("Faça o upload do banco de dados na ***versão Labels*** e da planilha de sintaxe ambas em Excel para realizar o Processamento.")
st.markdown("Faça o upload do banco de dados na <u>***versão Labels***</u> e da planilha de sintaxe, ambas em Excel para realizar o Processamento.", 
            unsafe_allow_html=True)

st.markdown(
    """
    📄 [Documentação do App em PDF](https://github.com/RaynerSantos/Processamento-Estatistico/blob/main/Documentacao_Processamento.pdf)
    """,
    unsafe_allow_html=True
)

st.write("")

# Upload das planilhas
with st.form(key='sheet_name_data'):
    nome_sheet_DATA = st.text_input(label="📝 Insira o nome da sheet (aba) no qual contém o banco de dados com os LABELS")
    input_buttom_submit_DATA = st.form_submit_button("Enviar")
st.session_state.nome_sheet_DATA = nome_sheet_DATA

data = st.file_uploader("📂 Selecione o banco de dados", type=["xlsx"])
bd_processamento = st.file_uploader("📂 Selecione a planilha com a Sintaxe para a criação das tabelas", type=["xlsx"])

if data and bd_processamento:
    st.write("✅ Planilhas carregadas com sucesso!")
    nome_sheet_DATA = st.session_state.nome_sheet_DATA
    data = pd.read_excel(data, sheet_name=nome_sheet_DATA)
    bd_processamento = pd.read_excel(bd_processamento)
    
    # Botão para processar os dados
    if st.button("Processar Dados"):
        # Processar os dados e obter as tabelas
        todas_tabelas_gerais = processamento(data, bd_processamento)
        
        # Salvar em Excel com formatação
        excel_data = salvar_excel_com_formatacao(todas_tabelas_gerais, bd_processamento=bd_processamento)
        
        # Link para download
        st.download_button(
            label="Baixar Excel Processado",
            data=excel_data,
            file_name="Processamento.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )