import pandas as pd
import numpy as np
import io
from io import BytesIO
# from statsmodels.stats.proportion import proportions_ztest
from collections import Counter
from databases.metodos import processamento, salvar_excel_aba_unica, salvar_excel_com_formatacao

df = pd.read_excel(r'C:\PROJETOS\Processamento-Estatistico\BASES PARA PROCESSAMENTO\Cielo NPS 2025\Jul25\EMP_Cielo Satisfacao_2onda_JUL25_v02.xlsx', sheet_name='bdlabels')

sintaxe = pd.read_excel(r'C:\PROJETOS\Processamento-Estatistico\BASES PARA PROCESSAMENTO\Cielo NPS 2025\Jul25\Sintaxe_Cielo_Satisfacao_Jul25_v03.xlsx')

todas_tabelas_gerais = processamento(df, sintaxe)

# excel_data = salvar_excel_aba_unica(todas_tabelas_gerais, bd_processamento=sintaxe)
# print('\n\nEXCEL_DATA\n')
# print(excel_data)

# excel_data.to_excel(r"C:\PROJETOS\Processamento-Estatistico\BASES PARA PROCESSAMENTO\Cielo NPS 2025\Jul25\output.xlsx")