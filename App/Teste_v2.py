import pandas as pd
import numpy as np
import io
from io import BytesIO
# from statsmodels.stats.proportion import proportions_ztest
from collections import Counter
from databases.metodos import processamento, salvar_excel_aba_unica, salvar_excel_com_formatacao

# df = pd.read_excel(r'C:\PROJETOS\Processamento-Estatistico\BASES PARA PROCESSAMENTO\Cielo NPS 2025\Jul25\EMP_Cielo Satisfacao_2onda_JUL25_v02.xlsx', sheet_name='bdlabels')

# sintaxe = pd.read_excel(r'C:\PROJETOS\Processamento-Estatistico\BASES PARA PROCESSAMENTO\Cielo NPS 2025\Jul25\Sintaxe_Cielo_Satisfacao_Jul25_v03.xlsx')

# todas_tabelas_gerais = processamento(df, sintaxe)

TipoTabela = 'SIMPLES'
Colunas = 'TOTX, ONDA_G, EMP_G, VAR_G, GC_G, PJ_G, PF_G, GER_COL, TIPO_CIELO, COL_EMPX, COL_EMP, COL_VARX, COL_VAR'
Ordem_ONDA = 'ONDA_G, Jul24, Nov24, Mar25, Jul25'

ONDA_G = 'Jul25, Mar25, Jul24, Nov24'

ONDA_G = ONDA_G.split(', ')
print(ONDA_G)
Ordem_ONDA = Ordem_ONDA.split(', ')
print(Ordem_ONDA[1:])

# Ordenar usando a ordem definida em Ordem_ONDA
pos = {valor: i for i, valor in enumerate(Ordem_ONDA[1:])}
ONDA_G_ordenada = sorted(ONDA_G, key=lambda x: pos.get(x, float('inf')))
# ONDA_G_ordenada = sorted(ONDA_G, key=lambda x: Ordem_ONDA[1:].index(x))
print(ONDA_G_ordenada)
# ONDA_G_ord = pd.Categorical(df[col], categories=df[col][pd.notna(df[col])].unique(), ordered=True)