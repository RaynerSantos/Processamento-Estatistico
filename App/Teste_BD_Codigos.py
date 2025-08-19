import pandas as pd
import numpy as np
# from statsmodels.stats.proportion import proportions_ztest
from collections import Counter
from databases.utils import ordenar_labels, ordenar_labels_multipla, ordenar_valores, classificar_nps, funcao_agrupamento, classificar_satis


TipoTabela = 'SIMPLES'
Colunas = 'ONDA, VSEG_BU, VSEG_1, PF_PJ, VREG'
Ordem_ONDA = 'ONDA_G, Jul24, Nov24, Mar25, Jul25'
Cabecalho = 'Onda, Segmento BU, Segmento, Pessoa, Regional'
Var_linha = 'VSEG_BU' # ADER_AG2 | NPS_C
NS_NR = 'NAO'
valores_BTB = ''
valores_TTB = ''
Valores_Agrup = 'MOTNEU_1, MOTNEU_2, MOTNEU_3'
Fecha_100 = 'NAO'
Var_ID = 'ID_EMP'
Var_Pond = 'POND'
Titulo = 'Aderencia Mono e Multi'

data = pd.read_excel(r'C:\PROJETOS\Processamento-Estatistico\BASES PARA PROCESSAMENTO\Cielo NPS 2025\OB\BD_Cielo_NPS_Fev25_2025.03.14_completo.xlsx', sheet_name='BD_CODIGOS')
df = data.copy()

lista_labels = pd.read_excel(r'C:\PROJETOS\Processamento-Estatistico\BASES PARA PROCESSAMENTO\Cielo NPS 2025\OB\BD_Cielo_NPS_Fev25_2025.03.14_completo.xlsx', sheet_name='Lista de Labels')

# Variáveis para as colunas da tabela (bandeiras)
Colunas = Colunas.split(sep=', ')
Ordem_ONDA = Ordem_ONDA.split(sep=', ')
dict_ord_labels = {}

for col in Colunas:
    if col not in df.columns:
        raise ValueError(f"Coluna '{col}' não encontrada no DataFrame.")        
    else:
        df[col], ord_labels = ordenar_labels(df=data, lista_labels=lista_labels, Variavel=col)
        dict_ord_labels[col] = ord_labels
        print(f"\nColuna ordenada (unique): {df[col].unique()}")
 
# Transformação na variável para a linha da tabela
if TipoTabela == 'SIMPLES':
    if NS_NR == 'NAO':
        df[Var_linha] = df[Var_linha].replace('NS/NR', np.nan)
        df[Var_linha], ord_labels = ordenar_labels(df=data, lista_labels=lista_labels, Variavel=Var_linha)
        # df[Var_linha] = pd.Categorical(df[Var_linha], categories=df[Var_linha][pd.notna(df[Var_linha])].unique(), ordered=True)
    else:
        df[Var_linha], ord_labels = ordenar_labels(df=data, lista_labels=lista_labels, Variavel=Var_linha)
        # df[Var_linha] = pd.Categorical(df[Var_linha], categories=df[Var_linha][pd.notna(df[Var_linha])].unique(), ordered=True)
    
elif (TipoTabela == 'NPS') | (TipoTabela == 'IPA_10'):
    if NS_NR == 'NAO':
        df[Var_linha] = df[Var_linha].replace('NS/NR', np.nan)
        df[Var_linha] = df[Var_linha].replace('ns/nr', np.nan)
        df[Var_linha] = df[Var_linha].replace('90', np.nan)
        df[Var_linha] = df[Var_linha].replace('99', np.nan)
        df[Var_linha] = df[Var_linha].replace('999', np.nan)
        df[Var_linha] = df[Var_linha].replace('9999', np.nan)
        df[Var_linha] = pd.to_numeric(df[Var_linha], errors='coerce', downcast='integer')
        # df[Var_linha], ord_labels = ordenar_labels(df=df, lista_labels=lista_labels, Variavel=Var_linha)
        df[Var_linha] = pd.Categorical(df[Var_linha], categories=ordenar_valores(df[Var_linha]), ordered=True)

        if TipoTabela == 'NPS':
            df['var_agrupada'] = df[Var_linha].apply(classificar_nps)

        elif TipoTabela == 'IPA_10':
            valores_BTB = [int(v) for v in valores_BTB.split(sep=', ')]
            valores_TTB = [int(v) for v in valores_TTB.split(sep=', ')]
            df['var_agrupada'] = funcao_agrupamento(df[Var_linha], valores_BTB, valores_TTB)

    else:
        df[Var_linha] = df[Var_linha].replace('90', np.nan)
        df[Var_linha] = df[Var_linha].replace('99', np.nan)
        df[Var_linha] = df[Var_linha].replace('999', np.nan)
        df[Var_linha] = df[Var_linha].replace('9999', np.nan)
        df[Var_linha], ord_labels = ordenar_labels(df=data, lista_labels=lista_labels, Variavel=Var_linha)
        # df[Var_linha] = pd.Categorical(df[Var_linha], categories=ordenar_valores(df[Var_linha]), ordered=True)

        if TipoTabela == 'NPS':
            df['var_agrupada'] = df[Var_linha].apply(classificar_nps)

        elif TipoTabela == 'IPA_10':
            valores_BTB = [int(v) for v in valores_BTB.split(sep=', ')]
            valores_TTB = [int(v) for v in valores_TTB.split(sep=', ')]
            df['var_agrupada'] = funcao_agrupamento(df[Var_linha], valores_BTB, valores_TTB)

elif TipoTabela == 'IPA_5':
    if NS_NR == 'NAO':
        df[Var_linha] = df[Var_linha].replace('NS/NR', np.nan)
        Valores_Agrup = Valores_Agrup.split(sep=', ')
        df['var_agrupada'] = df[Var_linha].replace(Valores_Agrup[-5], 'BTB').replace(Valores_Agrup[-4], 'BTB').replace(Valores_Agrup[-3], 'Neutro')\
                                                .replace(Valores_Agrup[-2], 'TTB').replace(Valores_Agrup[-1], 'TTB')
        df['var_agrupada'] = pd.Categorical(df['var_agrupada'], categories=['BTB', 'Neutro', 'TTB'], ordered=True)
        df[Var_linha], ord_labels = ordenar_labels(df=data, lista_labels=lista_labels, Variavel=Var_linha)
        # df[Var_linha] = pd.Categorical(df[Var_linha], categories=Valores_Agrup, ordered=True)
    else:
        Valores_Agrup = Valores_Agrup.split(sep=', ')
        df['var_agrupada'] = df[Var_linha].replace(Valores_Agrup[-5], 'BTB').replace(Valores_Agrup[-4], 'BTB').replace(Valores_Agrup[-3], 'Neutro')\
                                            .replace(Valores_Agrup[-2], 'TTB').replace(Valores_Agrup[-1], 'TTB')
        df['var_agrupada'] = pd.Categorical(df['var_agrupada'], categories=['BTB', 'Neutro', 'TTB'], ordered=True)
        df[Var_linha], ord_labels = ordenar_labels(df=data, lista_labels=lista_labels, Variavel=Var_linha)
        # df[Var_linha] = pd.Categorical(df[Var_linha], categories=Valores_Agrup, ordered=True)

elif TipoTabela == 'MULTIPLA':
    if NS_NR == 'NAO':
        df_NS_NR = df.copy()
        
        Valores_Agrup = Valores_Agrup.split(sep=', ')
        # Converte as colunas de motivos para string, preservando NaN
        # for c in Valores_Agrup:
        #     df[c] = df[c].astype("object").where(df[c].isna(), df[c].astype(str))
        #     df_NS_NR[c] = df_NS_NR[c].astype("object").where(df_NS_NR[c].isna(), df_NS_NR[c].astype(str))

        bd_motivo = pd.melt(df, 
                    id_vars=Colunas + [Var_Pond] + [Var_ID],
                    value_vars=Valores_Agrup, 
                    var_name='Valores', 
                    value_name=Var_linha)
        bd_motivo[Var_linha] = bd_motivo[Var_linha].replace('90', np.nan)
        bd_motivo[Var_linha] = bd_motivo[Var_linha].replace('99', np.nan)
        bd_motivo[Var_linha] = bd_motivo[Var_linha].replace('999', np.nan)
        bd_motivo[Var_linha] = bd_motivo[Var_linha].replace('9999', np.nan)
        bd_motivo = bd_motivo.dropna(subset=[Var_linha])
        print(f'\n\n{Var_linha}_1\n')
        bd_motivo = ordenar_labels_multipla(df=bd_motivo, lista_labels=lista_labels, Variavel=Var_linha)
        bd_motivo[Var_linha] = bd_motivo[Var_linha].replace('NS/NR', np.nan)
        # bd_motivo[Var_linha] = pd.Categorical(bd_motivo[Var_linha], categories=ordenar_valores(bd_motivo[Var_linha]), ordered=True)  

        df_limpo = bd_motivo.dropna(subset=[Var_linha])
        print(f'bd_motivo finalizado:\n{df_limpo}')
        df_unico = df_limpo.drop_duplicates(subset=Var_ID, keep='first')
                
        # Bancos para realizar o cálculo do Índice de Multiplicidade (incluir NS/NR)
        bd_motivo_NS_NR = pd.melt(df_NS_NR, 
                    id_vars=Colunas + [Var_Pond] + [Var_ID],
                    value_vars=Valores_Agrup, 
                    var_name='Valores', 
                    value_name=Var_linha)
        bd_motivo_NS_NR = bd_motivo_NS_NR.dropna(subset=[Var_linha])
        bd_motivo_NS_NR = ordenar_labels_multipla(df=bd_motivo_NS_NR, lista_labels=lista_labels, Variavel=Var_linha)
        # bd_motivo_NS_NR[Var_linha] = pd.Categorical(bd_motivo_NS_NR[Var_linha], 
        #                                     categories=ordenar_valores(bd_motivo_NS_NR[Var_linha]), ordered=True)
        
        df_NS_NR_limpo = bd_motivo_NS_NR.dropna(subset=[Var_linha])
        print(f'bd_motivo_NS_NR finalizado:\n{df_limpo}')
        df_NS_NR_unico = df_NS_NR_limpo.drop_duplicates(subset=Var_ID, keep='first')    
        
    else:
        Valores_Agrup = Valores_Agrup.split(sep=', ')
        bd_motivo = pd.melt(df, 
                    id_vars=Colunas + [Var_Pond] + [Var_ID],
                    value_vars=Valores_Agrup, 
                    var_name='Valores', 
                    value_name=Var_linha)
        bd_motivo = bd_motivo.dropna(subset=[Var_linha])
        bd_motivo = ordenar_labels_multipla(df=bd_motivo, lista_labels=lista_labels, Variavel=Var_linha)
        # bd_motivo[Var_linha] = pd.Categorical(bd_motivo[Var_linha], 
        #                                     categories=ordenar_valores(bd_motivo[Var_linha]), ordered=True)
        
        df_limpo = bd_motivo.dropna(subset=[Var_linha])
        df_unico = df_limpo.drop_duplicates(subset=Var_ID, keep='first')

#======= Criação da Tabela Geral =======#
tabela_geral = []
tabelas_pond = []
tabelas_pond_freq_abs = []
tabelas_sem_pond = []
aux_tabelas_pond = []
aux_tabelas_sem_pond = []

tbl_pond_freq_abs_respondentes = []
tbl_sem_pond_respondentes = []

tbl_pond_freq_abs_respostas_NS_NR = []
tbl_pond_freq_abs_respondentes_NS_NR = []

if TipoTabela == 'MULTIPLA':
    if NS_NR == 'NAO':
        banco = df_NS_NR_unico
    else:
        banco = df_unico

    if NS_NR == 'NAO':
        banco_pivotado = bd_motivo_NS_NR
    else:
        banco_pivotado = bd_motivo

    i = 0    
    for col in Colunas:

        # Gerar Tabelas Ponderadas de Frequência Absoluta com o banco empilhado
        tabela = pd.pivot_table(bd_motivo, values=Var_Pond, index=Var_linha, columns=col, aggfunc='sum')
        if Fecha_100 == 'SIM':
            tabela = tabela.div(tabela.sum())
            tabelas_pond.append(tabela)
        else:
            tabelas_pond.append(tabela)

        tabela = pd.pivot_table(banco_pivotado, values=Var_Pond, index=Var_linha, columns=col, aggfunc='sum')
        tbl_pond_freq_abs_respostas_NS_NR.append(tabela)

        tabela = pd.pivot_table(df_unico, values=Var_Pond, index=Var_linha, columns=col, aggfunc='sum')
        tbl_pond_freq_abs_respondentes.append(tabela)

        tabela = pd.pivot_table(banco, values=Var_Pond, index=Var_ID, columns=col, aggfunc='sum')
        tbl_pond_freq_abs_respondentes_NS_NR.append(tabela)

        tabela = pd.crosstab(df_unico[Var_linha], df_unico[col], dropna=False)
        tabela = tabela.fillna(0)
        if len(tabela) == 0:
            tabela = pd.DataFrame(0, index=df_unico[Var_linha][pd.notna(df_unico[Var_linha])].unique(), 
                                columns=df_unico[Colunas[i-1]][pd.notna(df_unico[Colunas[i-1]])].unique())
            print(f'{df_unico[Var_linha][pd.notna(df_unico[Var_linha])].unique()}\n')
            print(f'{df_unico[Colunas[i-1]][pd.notna(df_unico[Colunas[i-1]])].unique()}\n')
        print(f'tabela:\n{tabela}')
        tbl_sem_pond_respondentes.append(tabela)
        i += 1

    tabela_geral = pd.concat(tabelas_pond, axis=1)
    tbl_pond_freq_abs_respondentes = pd.concat(tbl_pond_freq_abs_respondentes, axis=1)
    tbl_sem_pond_respondentes = pd.concat(tbl_sem_pond_respondentes, axis=1)
    tbl_pond_freq_abs_respostas_NS_NR = pd.concat(tbl_pond_freq_abs_respostas_NS_NR, axis=1)
    tbl_pond_freq_abs_respondentes_NS_NR = pd.concat(tbl_pond_freq_abs_respondentes_NS_NR, axis=1)
    
    if Fecha_100 != 'SIM':
        soma_base_ponderada = tbl_pond_freq_abs_respondentes.sum()
        tabela_geral = tabela_geral.div(soma_base_ponderada)
    
    print(f'{tabela_geral}\n')


    # Trazendo a coluna de valores gerais
    soma_colunas = tbl_pond_freq_abs_respondentes.sum()
    soma_colunas = pd.Series(soma_colunas)
    base_ponderada = pd.pivot_table(df_unico, values=Var_Pond, index=Var_ID, aggfunc='sum')
    base_ponderada = pd.Series(base_ponderada.sum())
    base_ponderada = pd.concat([base_ponderada, soma_colunas])
    valores_gerais = pd.pivot_table(bd_motivo, values=Var_Pond, index=Var_linha, aggfunc='sum')
    if Fecha_100 == 'SIM':
        percentual_geral = valores_gerais.div(valores_gerais.sum()).sort_index()
        print(f'\npercentual_geral:\n{percentual_geral}')
        print(f'\nsoma de percentual_geral:\t{percentual_geral.sum()}')
    else:
        percentual_geral = valores_gerais.div(base_ponderada[0]).sort_index()
        print(f'\npercentual_geral:\n{percentual_geral}')
        print(f'\nsoma de percentual_geral:\t{percentual_geral.sum()}')

    # tabela_geral = tabela_geral.div(base_ponderada[1:])
    tabela_geral = pd.concat([percentual_geral, tabela_geral], axis=1)
    print(f'{tabela_geral}\n')

    # Valores para Base Ponderada
    soma_colunas = tbl_pond_freq_abs_respondentes.sum()
    soma_colunas = pd.Series(soma_colunas)
    base_ponderada = pd.pivot_table(df_unico, values=Var_Pond, index=Var_ID, aggfunc='sum')
    base_ponderada = pd.Series(base_ponderada.sum())
    base_ponderada = pd.concat([base_ponderada, soma_colunas])
    tabela_geral.loc['Base Ponderada'] = base_ponderada

    # Valores para Base Sem Ponderar
    valores_gerais_respondentes = df_unico[Var_ID].value_counts()
    soma_colunas = pd.Series(tbl_sem_pond_respondentes.sum())
    print(f'\n{soma_colunas}\n')
    base_sem_ponderar = pd.Series(valores_gerais_respondentes.sum())
    base_sem_ponderar = pd.concat([base_sem_ponderar, soma_colunas])
    print(f'base sem ponderar:\n{base_sem_ponderar.index}\n')
    print(f'{len(base_sem_ponderar.index)}\n')
    print(f'tabela geral:\n{tabela_geral.columns}\n')
    print(f'{len(tabela_geral.columns)}\n')
    base_sem_ponderar.index = tabela_geral.columns
    tabela_geral.loc['Base Sem Ponderar'] = base_sem_ponderar

    # Valores para Base Ponderada - Respostas
    soma_colunas_respostas = tbl_pond_freq_abs_respostas_NS_NR.sum()
    soma_colunas_respostas = pd.Series(soma_colunas_respostas)
    base_ponderada_respostas = pd.pivot_table(banco_pivotado, values=Var_Pond, index=Var_linha, aggfunc='sum')
    base_ponderada_respostas = pd.Series(base_ponderada_respostas.sum())
    base_ponderada_respostas = pd.concat([base_ponderada_respostas, soma_colunas_respostas])

    # Valores para Base Ponderada - Respondentes
    soma_colunas = tbl_pond_freq_abs_respondentes_NS_NR.sum()
    soma_colunas = pd.Series(soma_colunas)
    base_ponderada = pd.pivot_table(banco, values=Var_Pond, index=Var_ID, aggfunc='sum')
    base_ponderada = pd.Series(base_ponderada.sum())
    base_ponderada = pd.concat([base_ponderada, soma_colunas])

    # Índice de Multiplicidade (Total de respostas / Total de respondentes)
    indice_multiplicidade = base_ponderada_respostas / base_ponderada
    tabela_geral.loc['Índice de Multiplicidade'] = indice_multiplicidade

    tabela_geral.rename(columns={tabela_geral.columns[0]: 'Geral'}, inplace=True)
    print(f'{tabela_geral}\n')

else:
    if df[Var_linha].isna().all():
        # df[Var_linha] = df[Var_linha].astype('float').fillna(0)
        df[Var_linha] = df[Var_linha].cat.add_categories(['Não possui categoria']).fillna('Não possui categoria')
        print(f'Variável em branco\n{df[Var_linha]}\n')

    for col in Colunas:
        # Gerar Tabelas Ponderadas de frequência absoluta
        tabela = pd.crosstab(df[Var_linha], df[col], values=df[Var_Pond], aggfunc='sum')
        tabelas_pond_freq_abs.append(tabela)

        # Gerar Tabelas Ponderadas de frequência relativa 
        tabela = tabela.div(tabela.sum())
        tabela = tabela.fillna(0)
        tabelas_pond.append(tabela)
        print(f'Tabela Ponderada Freq Rel: \n{tabela}\n')

        # Gerar Tabelas Sem Ponderação
        tabela = pd.crosstab(df[Var_linha], df[col], dropna=False)
        tabela = tabela.fillna(0)
        print(f'Tabela Sem Ponderação: \n{tabela}\n')
        if len(tabela) == 0:
            tabela = pd.DataFrame(0, index=df[Var_linha][pd.notna(df[Var_linha])].unique(), 
                                columns=df[col][pd.notna(df[col])].unique())
            print(f'Tabela Sem Ponderação: \n{tabela}\n')
        tabelas_sem_pond.append(tabela)

        # Gerar Tabelas para valores agrupados
        if 'var_agrupada' in df.columns:
            tabela = pd.crosstab(df['var_agrupada'], df[col], values=df[Var_Pond], aggfunc='sum')
            tabela = tabela.div(tabela.sum())
            print(f'Tabela Valores Agrupados: \n{tabela}\n')
            aux_tabelas_pond.append(tabela)

            # Tabelas sem ponderação
            tabela = pd.crosstab(df['var_agrupada'], df[col], dropna=False)
            print(f'Tabela Valores Agrupados Sem Ponderação: \n{tabela}\n')
            aux_tabelas_sem_pond.append(tabela)

    tabela_geral = pd.concat(tabelas_pond, axis=1)
    tabelas_pond_freq_abs = pd.concat(tabelas_pond_freq_abs, axis=1)
    tabelas_sem_pond = pd.concat(tabelas_sem_pond, axis=1)

    # Trazendo a coluna de valores gerais
    valores_gerais_pond = pd.pivot_table(df, values=Var_Pond, index=Var_linha, aggfunc='sum', observed=False)
    print(f'\nValores GERAL:\n{valores_gerais_pond}')
    percentual_geral = valores_gerais_pond.div(valores_gerais_pond.sum()).sort_index()
    print(f'\PERCENTUAL GERAL:\n{percentual_geral}')

    if 'var_agrupada' in df.columns:
        aux_tabelas_pond = pd.concat(aux_tabelas_pond, axis=1)
        aux_tabelas_sem_pond = pd.concat(aux_tabelas_sem_pond, axis=1)

        # Percentual para os valores gerais da variável agrupada
        valores_gerais_aux = pd.pivot_table(df, values=Var_Pond, index='var_agrupada', aggfunc='sum')
        percentual_geral_aux = valores_gerais_aux.div(valores_gerais_aux.sum()).sort_index()
        tabela_geral = pd.concat([tabela_geral, aux_tabelas_pond], axis=0)
        percentual_geral = pd.concat([percentual_geral, percentual_geral_aux], axis=0)
        tabela_geral = pd.concat([percentual_geral, tabela_geral], axis=1)
    else:
        tabela_geral = pd.concat([percentual_geral, tabela_geral], axis=1)

    # Multiplicando cada linha pelo seu índice+1
    if TipoTabela == 'NPS':
        # Gerar o NPS
        nps = tabela_geral.loc['Promotor'] - tabela_geral.loc['Detrator']
        tabela_geral.loc['NPS'] = nps
        # Gerar as médias
        media_tabela = tabelas_pond_freq_abs.copy()
        for i in range(len(tabelas_pond_freq_abs)):
            media_tabela.iloc[i] = tabelas_pond_freq_abs.iloc[i] * (i + 1)
        media_tabela = media_tabela.sum().div(tabelas_pond_freq_abs.sum())

        # Cálculo da média geral
        df_limpo = df.dropna(subset=[Var_linha])
        media_geral = sum(np.array(df_limpo[Var_linha]) * np.array(df_limpo[Var_Pond])) / sum(np.array(df_limpo[Var_Pond]))
        media_geral = pd.Series(media_geral)
        media_tabela = pd.concat([media_geral, media_tabela], axis=0)
        media_tabela.index = tabela_geral.columns
        tabela_geral.loc['Media'] = media_tabela

    elif (TipoTabela == 'SATISFACAO') | (TipoTabela == 'IPA_10') :
        media_tabela = tabelas_pond_freq_abs.copy()
        for i in range(len(tabelas_pond_freq_abs)):
            media_tabela.iloc[i] = tabelas_pond_freq_abs.iloc[i] * (i + 1)
        media_tabela = media_tabela.sum().div(tabelas_pond_freq_abs.sum())

        # Cálculo da média geral
        df_limpo = df.dropna(subset=[Var_linha])
        media_geral = sum(np.array(df_limpo[Var_linha]) * np.array(df_limpo[Var_Pond])) / sum(np.array(df_limpo[Var_Pond]))
        media_geral = pd.Series(media_geral)
        media_tabela = pd.concat([media_geral, media_tabela], axis=0)

        media_tabela.index = tabela_geral.columns
        tabela_geral.loc['Media'] = media_tabela

    else:
        tabela_geral

    tabela_geral = tabela_geral.fillna(0)

    # Valores para Base Ponderada
    tabelas_pond_freq_abs = tabelas_pond_freq_abs.fillna(0)
    soma_colunas = tabelas_pond_freq_abs.sum()
    soma_colunas = pd.Series(soma_colunas)
    base_ponderada = pd.pivot_table(df, values=Var_Pond, index=Var_linha, aggfunc='sum', observed=False)
    base_ponderada = pd.Series(base_ponderada.sum())
    base_ponderada = pd.concat([base_ponderada, soma_colunas])
    # base_ponderada.index = tabela_geral.columns
    tabela_geral.loc['Base Ponderada'] = base_ponderada

    # Valores para Base Sem Ponderar
    tabelas_sem_pond = tabelas_sem_pond.fillna(0)
    soma_colunas = pd.Series(tabelas_sem_pond.sum())
    print(f'{soma_colunas}\n')
    valores_gerais = df[Var_linha].value_counts().sort_index()
    base_sem_ponderar = pd.Series(valores_gerais.sum())
    base_sem_ponderar = pd.concat([base_sem_ponderar, soma_colunas])
    print(f'{base_sem_ponderar.index}\n')
    print(f'{tabela_geral.columns}\n')
    base_sem_ponderar.index = tabela_geral.columns
    tabela_geral.loc['Base Sem Ponderar'] = base_sem_ponderar

    tabela_geral.rename(columns={tabela_geral.columns[0]: 'Geral'}, inplace=True)
    print(f'TABELA GERAL:\n{tabela_geral.iloc[:, 0:10]}\n')


Cabecalho = Cabecalho.split(sep=', ')
print(f'Cabeçalho:\n{Cabecalho}')
header_above = []
print(f'\ntabela_geral.columns:\n{tabela_geral.columns}')
for col in tabela_geral.columns:
    valor = col.split(sep=' - ')[0]
    print(f'valor: {valor}')
    header_above.append(valor)
print(f'\nheader_above:\n{header_above}')

col_series = []
for i, valor in enumerate(Cabecalho):
    # col_names = df[Colunas[i]][pd.notna(df[Colunas[i]])].unique()
    col_names = dict_ord_labels[Colunas[i]]
    print(f'\ncol_names:\n{col_names}')
    for col in col_names:
        col_series.append((Titulo, valor, col))

header = [(Titulo, '', 'GERAL')]
print(f'\ncol_series:\n{col_series}')
header = header + col_series
print(f'\nheader:\n{header}')
print(f'\ntamanho header:\t{len(header)}')
    
header = pd.MultiIndex.from_tuples(header)
print(f'\ntabela_geral.columns:\n{tabela_geral.columns}')
print(f'\ntamanho tabela_geral.columns:\t{len(tabela_geral.columns)}')
tabela_geral.columns = header
tabela_geral
print(f'\n\n #===== TABELA GERAL FINAL =====#\n{tabela_geral}\n')
print(f'#===================================================================================#\n')


