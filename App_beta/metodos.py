import pandas as pd
import numpy as np
from io import BytesIO
import time
import streamlit as st
from utils import ordenar_labels, ordenar_labels_multipla, ordenar_valores, classificar_nps, funcao_agrupamento, classificar_satis

# Função para converter DataFrame em arquivo Excel para download
def to_excel(df: pd.DataFrame, lista_de_labels: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="BD_CODIGOS")
        lista_de_labels.to_excel(writer, index=False, sheet_name="Lista de Labels")
    output.seek(0)  # volta pro início do buffer
    return output.getvalue()

def mensagem_sucesso():
    sucesso = st.success("Download realizado com sucesso!", icon="✅")
    time.sleep(5)
    sucesso.empty()

COLUNAS_SELECIONADAS = ['SEXO', 'REG_POND']
COL_NAME = 'SEXO_REG'
def criar_bandeira(data, lista_labels, COLUNAS_SELECIONADAS, COL_NAME):
    # Criar a nova coluna de bandeira combinada
    if COL_NAME in data.columns:
        raise ValueError(f"A coluna '{COL_NAME}' já existe no DataFrame.")
    else:
        data[COL_NAME] = data[COLUNAS_SELECIONADAS].astype(str).agg(' - '.join, axis=1)

        # Criar um dicionário para mapear os códigos para labels
        dict_nova_bandeira = {'Coluna': [], 'Codigo': [], 'Label': []}
        for i, valor in enumerate(sorted(data[COL_NAME].unique())):
            dict_nova_bandeira['Coluna'].append(COL_NAME)
            dict_nova_bandeira['Codigo'].append(i + 1)

            # Obter os labels correspondentes para cada parte da combinação
            col_1label = lista_labels.loc[(lista_labels['Coluna'] == COLUNAS_SELECIONADAS[0]) & (lista_labels['Codigo'] == int(valor.split(' - ')[0])), 'Label'].values[0]
            col_2label = lista_labels.loc[(lista_labels['Coluna'] == COLUNAS_SELECIONADAS[1]) & (lista_labels['Codigo'] == int(valor.split(' - ')[1])), 'Label'].values[0]

            combined_label = f"{col_1label} - {col_2label}"
            dict_nova_bandeira['Label'].append(combined_label)

        # Adicionar os novos labels à lista_labels
        lista_labels_nova = pd.DataFrame(dict_nova_bandeira)
        lista_labels = pd.concat([lista_labels, lista_labels_nova], axis=0, ignore_index=True)

        # Mapear os códigos na nova coluna
        codigo_map = {valor: i + 1 for i, valor in enumerate(sorted(data[COL_NAME].unique()))}
        data[COL_NAME] = data[COL_NAME].map(codigo_map)

        return data, lista_labels
    

# Criar uma função para fazer um recode simples baseado em uma coluna e um mapeamento fornecido
def recode_variavel(data, lista_labels, COLUNA_ORIGINAL, NOVA_BANDEIRA, dataframe_recode):
    if NOVA_BANDEIRA in data.columns:
        raise ValueError(f"A coluna '{NOVA_BANDEIRA}' já existe no DataFrame.")
    else:
        data[NOVA_BANDEIRA] = np.nan

    # Criar o mapping (de-para) a partir do dataframe de recode
    mapping_de_para = dict(zip(dataframe_recode['Codigo'], dataframe_recode['Ordem']))
    mapping_de_para

    # Aplicar o mapeamento para criar a nova bandeira
    for codigo_original, codigo_novo in mapping_de_para.items():
        data.loc[data[COLUNA_ORIGINAL] == codigo_original, NOVA_BANDEIRA] = codigo_novo

    # Criar a mini lista de labels para a nova variável
    mapping_lista_labels = dict(zip(dataframe_recode['Ordem'], dataframe_recode['Label nova']))

    novo_recode = {
        'Coluna': [],
        'Codigo': [],
        'Label': []
    }

    for codigo, label in mapping_lista_labels.items():
        novo_recode['Coluna'].append(NOVA_BANDEIRA)
        novo_recode['Codigo'].append(codigo)
        novo_recode['Label'].append(label)

    lista_labels = pd.concat([lista_labels, pd.DataFrame(novo_recode)], axis=0, ignore_index=True)
    return data, lista_labels


# Função para criar a ponderação
def criar_pond(df_universo: pd.DataFrame, df_coletado: pd.DataFrame, 
               bd_codigo: pd.DataFrame, lista_labels: pd.DataFrame, cabecalho: str, coluna: str, linha: str):
    """
    Função para calcular a coluna de ponderação (máximo de 3 categorias: Cabeçalho, coluna e linha - MultiIndex):
    1) A partir do universo, a quantidade total de entrevistas e o coletado é criado o valor da ponderação
    2) Com o banco de dados e a lista de labels cria-se a coluna POND no banco de dados
    """

    # Soma do universo
    total = int(df_universo.sum().sum().round())

    # df_universo em percentual
    df_universo_perc = df_universo.divide(total)

    # Calcular a quantidade total de entrevistas
    qtd_total_entrevistas = int(df_coletado.sum().sum())

    # Valor ideal que deve ter de entrevistas para cada categoria
    df_ideal = df_universo_perc.multiply(qtd_total_entrevistas)

    # DataFrame com a ponderação criada de acordo com a combinação de categorias
    df_pond = pd.DataFrame(
        df_ideal.to_numpy() / df_coletado.astype(float).to_numpy(),
        index=df_ideal.index,
        columns=df_ideal.columns
    )

    # Criar um mapeamento para cada label das categorias necessárias
    lista_labels_cabecalho = lista_labels[lista_labels["Coluna"] == cabecalho]
    lista_labels_cabecalho_mapping = dict(zip(lista_labels_cabecalho['Codigo'], lista_labels_cabecalho['Label']))

    lista_labels_coluna = lista_labels[lista_labels["Coluna"] == coluna]
    lista_labels_coluna_mapping = dict(zip(lista_labels_coluna['Codigo'], lista_labels_coluna['Label']))

    lista_labels_linha = lista_labels[lista_labels["Coluna"] == linha]
    lista_labels_linha_mapping = dict(zip(lista_labels_linha['Codigo'], lista_labels_linha['Label']))

    # Criar a nova coluna de PONDERAÇÃO de acordo com o df_pond
    bd_codigo["POND_nova"] = np.nan
    label_to_codigo = lista_labels.set_index("Label")["Codigo"].astype(int).to_dict()

    for label_cabecalho in pd.Series(sorted(bd_codigo[cabecalho].astype(int).unique())).map(lista_labels_cabecalho_mapping):
        s = lista_labels.loc[lista_labels["Label"] == label_cabecalho, "Codigo"]
        if s.empty:
            raise KeyError(f"Label não encontrado: {label_cabecalho}")
        codigo_cabecalho = label_to_codigo[label_cabecalho]

        for label_coluna in pd.Series(sorted(bd_codigo[coluna].astype(int).unique())).map(lista_labels_coluna_mapping):
            s = lista_labels.loc[lista_labels["Label"] == label_coluna, "Codigo"]
            if s.empty:
                raise KeyError(f"Label não encontrado: {label_coluna}")
            codigo_coluna = label_to_codigo[label_coluna]

            for label_linha in pd.Series(sorted(bd_codigo[linha].astype(int).unique())).map(lista_labels_linha_mapping):
                s = lista_labels.loc[lista_labels["Label"] == label_linha, "Codigo"]
                if s.empty:
                    raise KeyError(f"Label não encontrado: {label_linha}")
                codigo_linha = label_to_codigo[label_linha]

                pond = df_pond[label_cabecalho][label_coluna][label_linha]
                bd_codigo.loc[((bd_codigo[cabecalho] == codigo_cabecalho) & (bd_codigo[coluna] == codigo_coluna) & (bd_codigo[linha] == codigo_linha)), "POND_nova"] = pond
    
    return bd_codigo



# FUNÇÃO PARA PROCESSAR UMA ÚNICA TABELA
def processar_tabela(bd_dados: pd.DataFrame, lista_labels: pd.DataFrame, 
                     TipoTabela: str, Var_linha: str, Colunas: list, Cabecalho: str, NS_NR: str, Var_ID: str, Var_Pond: str, Titulo: str,
                     valores_BTB: str = '1, 2, 3', valores_TTB: str = '8, 9, 10', Valores_Agrup: str = 'Q8_1, Q8_2, Q8_3', Fecha_100: str = 'SIM'):
    
    df = bd_dados.copy()
    dict_ord_labels = {}

    for col in Colunas:
        if col not in df.columns:
            raise ValueError(f"Coluna '{col}' não encontrada no DataFrame.")        
        else:
            df[col], ord_labels = ordenar_labels(df=bd_dados, lista_labels=lista_labels, Variavel=col)
            dict_ord_labels[col] = ord_labels
            print(f"\nColuna ordenada (unique): {df[col].unique()}")

    # Etapas de ETL para as colunas principais a serem utilizadas
    # Transformação na variável para a linha da tabela
    if TipoTabela == 'SIMPLES':
        if NS_NR == 'NAO':
            df[Var_linha] = df[Var_linha].replace('NS/NR', np.nan)
            df[Var_linha], ord_labels = ordenar_labels(df=bd_dados, lista_labels=lista_labels, Variavel=Var_linha)
            # df[Var_linha] = pd.Categorical(df[Var_linha], categories=df[Var_linha][pd.notna(df[Var_linha])].unique(), ordered=True)
        else:
            df[Var_linha], ord_labels = ordenar_labels(df=bd_dados, lista_labels=lista_labels, Variavel=Var_linha)
            # df[Var_linha] = pd.Categorical(df[Var_linha], categories=df[Var_linha][pd.notna(df[Var_linha])].unique(), ordered=True)
        
    elif (TipoTabela == 'NPS') | (TipoTabela == 'IPA_10'):
        if NS_NR == 'NAO':
            df[Var_linha] = df[Var_linha].replace('NS/NR', np.nan)
            df[Var_linha] = df[Var_linha].replace('ns/nr', np.nan)
            df[Var_linha] = df[Var_linha].replace('90', np.nan)
            df[Var_linha] = df[Var_linha].replace('99', np.nan)
            df[Var_linha] = df[Var_linha].replace('999', np.nan)
            df[Var_linha] = df[Var_linha].replace('9999', np.nan)
            df[Var_linha] = df[Var_linha].replace(90, np.nan)
            df[Var_linha] = df[Var_linha].replace(99, np.nan)
            df[Var_linha] = df[Var_linha].replace(999, np.nan)
            df[Var_linha] = df[Var_linha].replace(9999, np.nan)
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
            # df[Var_linha] = df[Var_linha].replace('90', np.nan)
            # df[Var_linha] = df[Var_linha].replace('99', np.nan)
            # df[Var_linha] = df[Var_linha].replace('999', np.nan)
            # df[Var_linha] = df[Var_linha].replace('9999', np.nan)
            # df[Var_linha], ord_labels = ordenar_labels(df=data, lista_labels=lista_labels, Variavel=Var_linha)
            df[Var_linha] = pd.Categorical(df[Var_linha], categories=ordenar_valores(df[Var_linha]), ordered=True)

            if TipoTabela == 'NPS':
                df['var_agrupada'] = df[Var_linha].apply(classificar_nps)

            elif TipoTabela == 'IPA_10':
                valores_BTB = [int(v) for v in valores_BTB.split(sep=', ')]
                valores_TTB = [int(v) for v in valores_TTB.split(sep=', ')]
                df['var_agrupada'] = funcao_agrupamento(df[Var_linha], valores_BTB, valores_TTB)

    elif TipoTabela == 'IPA_5':
        if NS_NR == 'NAO':
            df[Var_linha] = df[Var_linha].replace('NS/NR', np.nan)
            df[Var_linha] = df[Var_linha].replace('90', np.nan)
            df[Var_linha] = df[Var_linha].replace('99', np.nan)
            df[Var_linha] = df[Var_linha].replace('999', np.nan)
            df[Var_linha] = df[Var_linha].replace(90, np.nan)
            df[Var_linha] = df[Var_linha].replace(99, np.nan)
            df[Var_linha] = df[Var_linha].replace(999, np.nan)
            valores_BTB = [int(v) for v in valores_BTB.split(sep=', ')]
            valores_TTB = [int(v) for v in valores_TTB.split(sep=', ')]
            df['var_agrupada'] = funcao_agrupamento(df[Var_linha], valores_BTB, valores_TTB)
            df['var_agrupada'] = pd.Categorical(df['var_agrupada'], categories=['BTB', 'Neutro', 'TTB'], ordered=True)
            df[Var_linha], ord_labels = ordenar_labels(df=bd_dados, lista_labels=lista_labels, Variavel=Var_linha)
            # df[Var_linha] = pd.Categorical(df[Var_linha], categories=Valores_Agrup, ordered=True)
        else:
            valores_BTB = [int(v) for v in valores_BTB.split(sep=', ')]
            valores_TTB = [int(v) for v in valores_TTB.split(sep=', ')]
            df['var_agrupada'] = funcao_agrupamento(df[Var_linha], valores_BTB, valores_TTB)
            df['var_agrupada'] = pd.Categorical(df['var_agrupada'], categories=['BTB', 'Neutro', 'TTB'], ordered=True)
            df[Var_linha], ord_labels = ordenar_labels(df=bd_dados, lista_labels=lista_labels, Variavel=Var_linha)
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
            bd_motivo[Var_linha] = bd_motivo[Var_linha].replace(90, np.nan)
            bd_motivo[Var_linha] = bd_motivo[Var_linha].replace(99, np.nan)
            bd_motivo[Var_linha] = bd_motivo[Var_linha].replace(999, np.nan)
            bd_motivo[Var_linha] = bd_motivo[Var_linha].replace(9999, np.nan)
            bd_motivo = bd_motivo.dropna(subset=[Var_linha])
            print(f'\nbd_motivo em formato de código:\n{bd_motivo}')
            bd_motivo = ordenar_labels_multipla(df=bd_motivo, lista_labels=lista_labels, Variavel=Var_linha, Var_Valores_Agrup=Valores_Agrup[0])
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
            bd_motivo_NS_NR = ordenar_labels_multipla(df=bd_motivo_NS_NR, lista_labels=lista_labels, Variavel=Var_linha, 
                                                    Var_Valores_Agrup=Valores_Agrup[0])
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
            bd_motivo = ordenar_labels_multipla(df=bd_motivo, lista_labels=lista_labels, Variavel=Var_linha, Var_Valores_Agrup=Valores_Agrup[0])
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

        tabela_geral_front = tabela_geral.multiply(100)
        tabela_geral_front = tabela_geral_front.applymap(lambda x: f"{x:.1f}%".replace(".", ","))

        # Valores para Base Ponderada
        soma_colunas = tbl_pond_freq_abs_respondentes.sum()
        soma_colunas = pd.Series(soma_colunas)
        base_ponderada = pd.pivot_table(df_unico, values=Var_Pond, index=Var_ID, aggfunc='sum')
        base_ponderada = pd.Series(base_ponderada.sum())
        base_ponderada = pd.concat([base_ponderada, soma_colunas])
        tabela_geral.loc['Base Ponderada'] = base_ponderada
        tabela_geral_front.loc['Base Ponderada'] = base_ponderada.round().astype(int)

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
        tabela_geral_front.loc['Base Sem Ponderar'] = base_sem_ponderar

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
        tabela_geral_front.loc['Índice de Multiplicidade'] = indice_multiplicidade

        tabela_geral.rename(columns={tabela_geral.columns[0]: 'Geral'}, inplace=True)
        print(f'{tabela_geral}\n')
        tabela_geral_front.rename(columns={tabela_geral.columns[0]: 'Geral'}, inplace=True)

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

            tabela_geral_front = tabela_geral.multiply(100)
            tabela_geral_front = tabela_geral_front.applymap(lambda x: f"{x:.1f}%".replace(".", ","))

        else:
            tabela_geral = pd.concat([percentual_geral, tabela_geral], axis=1)

            tabela_geral_front = tabela_geral.multiply(100)
            tabela_geral_front = tabela_geral_front.applymap(lambda x: f"{x:.1f}%".replace(".", ","))

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

            tabela_geral_front = tabela_geral.multiply(100)
            tabela_geral_front = tabela_geral_front.applymap(lambda x: f"{x:.1f}%".replace(".", ","))
            tabela_geral_front.loc['Media'] = media_tabela

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

            tabela_geral_front = tabela_geral.multiply(100)
            tabela_geral_front = tabela_geral_front.applymap(lambda x: f"{x:.1f}%".replace(".", ","))
            tabela_geral_front.loc['Media'] = media_tabela

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
        tabela_geral_front.loc['Base Ponderada'] = base_ponderada.round().astype(int)

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
        tabela_geral_front.loc['Base Sem Ponderar'] = base_sem_ponderar

        tabela_geral.rename(columns={tabela_geral.columns[0]: 'Geral'}, inplace=True)
        tabela_geral_front.rename(columns={tabela_geral.columns[0]: 'Geral'}, inplace=True)
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
    tabela_geral_front.columns = header
    print(f"Tabela processada:\n{tabela_geral}")
    
    return tabela_geral, tabela_geral_front



########################################
#======= Tratamento das tabelas =======#
########################################

def processamento(data, bd_processamento, lista_labels):
    # Função para aplicar a classificação do nps
    def classificar_nps(valor):
        if np.isnan(valor):
            return np.nan
        elif valor >= 9:
            return 'Promotor'
        elif valor >= 7:
            return 'Neutro'
        else:
            return 'Detrator'
        
    # Função para aplicar a classificação para a variável satisfação
    def classificar_satis(valor):
        if np.isnan(valor):
            return np.nan
        elif valor >= 8:
            return 'Satisfeito'
        elif valor >= 6:
            return 'Neutro'
        else:
            return 'Insatisfeito'
        

    # Função para criar os índices corretos e ordenados das tabelas (esse novo índice entrará na função stat_test())
    def ordenar_valores(variavel):
        valores_unicos = variavel.unique()
        valores_ordenados = pd.Series(valores_unicos).sort_values()

        if valores_ordenados.isna().iloc[-1]:
            return valores_ordenados[0:-1]
        else:
            return valores_ordenados

    # Função para calcular se o valor é estatisticamente significativo (comparar o p-valor)
    def classificar_relevancia(valor):
        if valor <= 0.05:
            return "DIF"
        else:
            return ''
        
    # Função para realizar o agrupamento
    def funcao_agrupamento(variavel, BTB, TTB):
        nova_var = []
        for v in variavel:
            if np.isnan(v):  # Verifica se o valor é NaN
                nova_var.append(np.nan)
            elif int(v) in BTB:  # Converte v para inteiro antes da comparação, se necessário
                nova_var.append('BTB')
            elif int(v) in TTB:  # Converte v para inteiro antes da comparação, se necessário
                nova_var.append('TTB')
            else:
                nova_var.append('Neutro')
        return nova_var

    todas_tabelas_gerais = []
    todos_resultados_teste = []
    for line in range(len(bd_processamento)):
        i = 0
        TipoTabela = bd_processamento.iloc[line, i]
        i+=1
        Colunas = bd_processamento.iloc[line, i]
        i+=1
        Cabecalho = bd_processamento.iloc[line, i]
        i+=1
        Var_linha = bd_processamento.iloc[line, i]
        i+=1
        NS_NR = bd_processamento.iloc[line, i]
        i+=1
        valores_BTB = bd_processamento.iloc[line, i]
        i+=1
        valores_TTB = bd_processamento.iloc[line, i]
        i+=1
        Valores_Agrup = bd_processamento.iloc[line, i]
        i+=1
        Fecha_100 = bd_processamento.iloc[line, i]
        i+=1
        Var_ID = bd_processamento.iloc[line, i]
        i+=1
        Var_Pond = bd_processamento.iloc[line, i]
        i+=1
        Titulo = bd_processamento.iloc[line, i]

        df = data.copy()

        print(f'\n#===== VAR_LINHA =====#\n{Var_linha}\n')
        # Variáveis para as colunas da tabela (bandeiras)
        Colunas = Colunas.split(sep=', ')
        dict_ord_labels = {}
        for col in Colunas:
            if col not in df.columns:
                raise ValueError(f"Coluna '{col}' não encontrada no DataFrame.")        
            else:
                df[col], ord_labels = ordenar_labels(df=data, lista_labels=lista_labels, Variavel=col)
                dict_ord_labels[col] = ord_labels
                print(f"Coluna ordenada: {df[col].unique()}")

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
                df[Var_linha] = df[Var_linha].replace(90, np.nan)
                df[Var_linha] = df[Var_linha].replace(99, np.nan)
                df[Var_linha] = df[Var_linha].replace(999, np.nan)
                df[Var_linha] = df[Var_linha].replace(9999, np.nan)
                df[Var_linha] = pd.to_numeric(df[Var_linha], errors='coerce', downcast='integer')
                df[Var_linha] = pd.Categorical(df[Var_linha], categories=ordenar_valores(df[Var_linha]), ordered=True)

                if TipoTabela == 'NPS':
                    df['var_agrupada'] = df[Var_linha].apply(classificar_nps)

                elif TipoTabela == 'IPA_10':
                    valores_BTB = [int(v) for v in valores_BTB.split(sep=', ')]
                    valores_TTB = [int(v) for v in valores_TTB.split(sep=', ')]
                    df['var_agrupada'] = funcao_agrupamento(df[Var_linha], valores_BTB, valores_TTB)

            else:
                # df[Var_linha] = df[Var_linha].replace('90', np.nan)
                # df[Var_linha] = df[Var_linha].replace('99', np.nan)
                # df[Var_linha] = df[Var_linha].replace('999', np.nan)
                # df[Var_linha] = df[Var_linha].replace('9999', np.nan)
                df[Var_linha] = pd.to_numeric(df[Var_linha], errors='coerce', downcast='integer')
                df[Var_linha] = pd.Categorical(df[Var_linha], categories=ordenar_valores(df[Var_linha]), ordered=True)

                if TipoTabela == 'NPS':
                    df['var_agrupada'] = df[Var_linha].apply(classificar_nps)

                elif TipoTabela == 'IPA_10':
                    valores_BTB = [int(v) for v in valores_BTB.split(sep=', ')]
                    valores_TTB = [int(v) for v in valores_TTB.split(sep=', ')]
                    df['var_agrupada'] = funcao_agrupamento(df[Var_linha], valores_BTB, valores_TTB)
            
        elif TipoTabela == 'IPA_5':
            if NS_NR == 'NAO':
                df[Var_linha] = df[Var_linha].replace('NS/NR', np.nan)
                df[Var_linha] = df[Var_linha].replace('ns/nr', np.nan)
                df[Var_linha] = df[Var_linha].replace('90', np.nan)
                df[Var_linha] = df[Var_linha].replace('99', np.nan)
                df[Var_linha] = df[Var_linha].replace('999', np.nan)
                df[Var_linha] = df[Var_linha].replace('9999', np.nan)
                df[Var_linha] = df[Var_linha].replace(90, np.nan)
                df[Var_linha] = df[Var_linha].replace(99, np.nan)
                df[Var_linha] = df[Var_linha].replace(999, np.nan)
                df[Var_linha] = df[Var_linha].replace(9999, np.nan)
                valores_BTB = [int(v) for v in valores_BTB.split(sep=', ')]
                valores_TTB = [int(v) for v in valores_TTB.split(sep=', ')]
                df['var_agrupada'] = funcao_agrupamento(df[Var_linha], valores_BTB, valores_TTB)
                df['var_agrupada'] = pd.Categorical(df['var_agrupada'], categories=['BTB', 'Neutro', 'TTB'], ordered=True)
                df[Var_linha], ord_labels = ordenar_labels(df=data, lista_labels=lista_labels, Variavel=Var_linha)
                # df[Var_linha] = pd.Categorical(df[Var_linha], categories=Valores_Agrup, ordered=True)
            else:
                valores_BTB = [int(v) for v in valores_BTB.split(sep=', ')]
                valores_TTB = [int(v) for v in valores_TTB.split(sep=', ')]
                df['var_agrupada'] = funcao_agrupamento(df[Var_linha], valores_BTB, valores_TTB)
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
                bd_motivo[Var_linha] = bd_motivo[Var_linha].replace(90, np.nan)
                bd_motivo[Var_linha] = bd_motivo[Var_linha].replace(99, np.nan)
                bd_motivo[Var_linha] = bd_motivo[Var_linha].replace(999, np.nan)
                bd_motivo[Var_linha] = bd_motivo[Var_linha].replace(9999, np.nan)
                bd_motivo = bd_motivo.dropna(subset=[Var_linha])
                bd_motivo = ordenar_labels_multipla(df=bd_motivo, lista_labels=lista_labels, Variavel=Var_linha, 
                                                    Var_Valores_Agrup=Valores_Agrup[0])
                bd_motivo[Var_linha] = bd_motivo[Var_linha].replace('NS/NR', np.nan)
                bd_motivo[Var_linha] = bd_motivo[Var_linha].replace('ns/nr', np.nan)
                # bd_motivo[Var_linha] = pd.Categorical(bd_motivo[Var_linha], 
                #                                     categories=ordenar_valores(bd_motivo[Var_linha]), ordered=True)  
                
                df_limpo = bd_motivo.dropna(subset=[Var_linha])
                df_unico = df_limpo.drop_duplicates(subset=Var_ID, keep='first')
                        
                # Bancos para realizar o cálculo do Índice de Multiplicidade (incluir NS/NR)
                bd_motivo_NS_NR = pd.melt(df_NS_NR, 
                            id_vars=Colunas + [Var_Pond] + [Var_ID],
                            value_vars=Valores_Agrup, 
                            var_name='Valores', 
                            value_name=Var_linha)
                bd_motivo_NS_NR = bd_motivo_NS_NR.dropna(subset=[Var_linha])
                bd_motivo_NS_NR = ordenar_labels_multipla(df=bd_motivo_NS_NR, lista_labels=lista_labels, Variavel=Var_linha, 
                                                          Var_Valores_Agrup=Valores_Agrup[0])
                # bd_motivo_NS_NR[Var_linha] = pd.Categorical(bd_motivo_NS_NR[Var_linha], 
                #                                     categories=ordenar_valores(bd_motivo_NS_NR[Var_linha]), ordered=True)
                
                df_NS_NR_limpo = bd_motivo_NS_NR.dropna(subset=[Var_linha])
                df_NS_NR_unico = df_NS_NR_limpo.drop_duplicates(subset=Var_ID, keep='first')    
                
            else:
                Valores_Agrup = Valores_Agrup.split(sep=', ')
                bd_motivo = pd.melt(df, 
                            id_vars=Colunas + [Var_Pond] + [Var_ID],
                            value_vars=Valores_Agrup, 
                            var_name='Valores', 
                            value_name=Var_linha)
                bd_motivo = bd_motivo.dropna(subset=[Var_linha])
                bd_motivo = ordenar_labels_multipla(df=bd_motivo, lista_labels=lista_labels, Variavel=Var_linha, 
                                                    Var_Valores_Agrup=Valores_Agrup[0])
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
                if col == Var_linha:
                    tabela = pd.crosstab(index=df[Var_linha], columns=df[col], values=df[Var_Pond], aggfunc='sum')
                else:
                    tabela = pd.pivot_table(df, values=Var_Pond, index=Var_linha, columns=col, aggfunc='sum')
                tabelas_pond_freq_abs.append(tabela)

                # Gerar Tabelas Ponderadas de frequência relativa
                tabela = tabela.div(tabela.sum())
                tabela = tabela.fillna(0)
                tabelas_pond.append(tabela)
                print(f'{tabela}\n')

                
                # Gerar Tabelas Sem Ponderação
                tabela = pd.crosstab(df[Var_linha], df[col], dropna=False)
                tabela = tabela.fillna(0)
                if len(tabela) == 0:
                    tabela = pd.DataFrame(0, index=df[Var_linha][pd.notna(df[Var_linha])].unique(), 
                                        columns=df[col][pd.notna(df[col])].unique())
                tabelas_sem_pond.append(tabela)

                # Gerar Tabelas para valores agrupados
                if 'var_agrupada' in df.columns:
                    if col == Var_linha:
                        tabela = pd.crosstab(index=df['var_agrupada'], columns=df[col], values=df[Var_Pond], aggfunc='sum')
                    else:
                        tabela = pd.pivot_table(df, values=Var_Pond, index='var_agrupada', columns=col, aggfunc='sum')
                    tabela = tabela.div(tabela.sum())
                    aux_tabelas_pond.append(tabela)

                    # Tabelas sem ponderação
                    tabela = pd.crosstab(df['var_agrupada'], df[col], dropna=False)
                    aux_tabelas_sem_pond.append(tabela)
                
            tabela_geral = pd.concat(tabelas_pond, axis=1)
            tabelas_pond_freq_abs = pd.concat(tabelas_pond_freq_abs, axis=1)
            tabelas_sem_pond = pd.concat(tabelas_sem_pond, axis=1)

            # Trazendo a coluna de valores gerais
            valores_gerais_pond = pd.pivot_table(df, values=Var_Pond, index=Var_linha, aggfunc='sum')
            percentual_geral = valores_gerais_pond.div(valores_gerais_pond.sum()).sort_index()

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
            base_ponderada = pd.pivot_table(df, values=Var_Pond, index=Var_linha, aggfunc='sum')
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

        #===== Adicionar cabeçalho a tabela =====#
        Cabecalho = Cabecalho.split(sep=',')
        print(f'Cabeçalho:\n{Cabecalho}')
        header_above = []
        print(f'\ntabela_geral.columns:\n{tabela_geral.columns}')
        for col in tabela_geral.columns:
            valor = col.split(sep=' - ')[0]
            print(f'\nvalor: {valor}')
            header_above.append(valor)
        print(f'\nheader_above:\n{header_above}')

        col_series = []
        for i, valor in enumerate(Cabecalho):
            # col_names = df[Colunas[i]][pd.notna(df[Colunas[i]])].unique()
            col_names = dict_ord_labels[Colunas[i]]
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
        print(f'\n\n #===== TABELA GERAL FINAL =====#\n{tabela_geral}\n')
        print(f'#========================================================================#\n')

        todas_tabelas_gerais.append(tabela_geral)

    return todas_tabelas_gerais


# ===== __main__ ===== #
if __name__ == "__main__":
    # Teste da função criar_bandeira e fazer recode
    data_file = r'C:\Users\rayner.santos\Downloads\Consistencia e Processamento\BD_CNP_Recall de campanha_v12.xlsx'
    data = pd.read_excel(data_file, sheet_name='Códigos')
    lista_labels = pd.read_excel(data_file, sheet_name='Variáveis Labels')
    lista_labels = lista_labels.iloc[1:, :].copy()
    lista_labels.columns = ['Coluna', 'Codigo', 'Label']
    lista_labels["Coluna"] = lista_labels["Coluna"].ffill().str.strip()

    # data, lista_labels = criar_bandeira(data, lista_labels)

    # print(data[['SEXO', 'REG_POND', 'SEXO_REG']].head(), "\n")
    # print(data['SEXO_REG'].value_counts(), "\n")
    # print(lista_labels[lista_labels['Coluna'] == 'SEXO_REG'], "\n") 

    data, lista_labels = recode_variavel(
        data, lista_labels, 'Q7', 'NOVA_BANDEIRA', {1: 12, 2: 12, 3: 12, 4: 12, 5: 10, 6: 9, 7: 8, 8: 4, 9: 12, 10: 12, 11: 12, 13: 2, 14: 12, 15: 12, 16: 5, 17: 12, 18: 12, 19: 3, 20: 11, 21: 7, 22: 12, 23: 12 , 24: 6, 25: 1, 26: 12, 27: 12})

    print(data[['Q7', 'NOVA_BANDEIRA']], "\n")
    print(data['NOVA_BANDEIRA'].value_counts(), "\n")
    print(lista_labels[lista_labels['Coluna'] == 'NOVA_BANDEIRA'], "\n")
    print("Tamanho lista_labels:", len(lista_labels[lista_labels['Coluna'] == 'NOVA_BANDEIRA']))


def verif_TipoTabela(TipoTabela):
        if TipoTabela not in ["SIMPLES", "IPA_5", "IPA_10", "NPS", "MULTIPLA"]:
            return 1
        return 0

def verif_bandeiras_cabecalho(Bandeiras, Cabecalho):
     Bandeiras = Bandeiras.split(", ")
     Cabecalho = Cabecalho.split(", ")
     qtd_bandeiras = len(Bandeiras)
     qtd_cabecalho = len(Cabecalho)
     if qtd_bandeiras != qtd_cabecalho:
          return 1
     return 0

def verif_bandeiras(df, Bandeiras):
     Bandeiras = Bandeiras.split(", ")
     for col in Bandeiras:
          if col not in df.columns:
            # raise ValueError(f"⚠️ Coluna '{col}' não encontrada no DataFrame.")
            return 1, col
     return 0, col
      
def verif_Var_linha(df, Var_linha, TipoTabela):
     if TipoTabela != "MULTIPLA":
          if Var_linha not in df.columns:
               return 1
     return 0

def verif_NS_NR(NS_NR):
        if NS_NR not in ["NAO", "SIM"]:
            return 1
        return 0

def verif_Fecha_100(TipoTabela, Fecha_100):
     if TipoTabela == "MULTIPLA":
          if Fecha_100 not in ["NAO", "SIM"]:
               return 1
     return 0

def verif_coluna_existe(df, coluna):
    if coluna not in df.columns:
        return 1
    return 0


class verificar_incosistencias_iniciais:
    def __init__(self, data, sintaxe, lista_labels):
        self.data = data
        self.sintaxe = sintaxe
        self.lista_labels = lista_labels
    
    def verificar_incosistencia(self):
        df = self.data.copy()
        for line in range(len(self.sintaxe)):
            i = 0
            TipoTabela = self.sintaxe.iloc[line, i]
            i+=1
            Bandeiras = self.sintaxe.iloc[line, i]
            i+=1
            Cabecalho = self.sintaxe.iloc[line, i]
            i+=1
            Var_linha = self.sintaxe.iloc[line, i]
            i+=1
            NS_NR = self.sintaxe.iloc[line, i]
            i+=1
            valores_BTB = self.sintaxe.iloc[line, i]
            i+=1
            valores_TTB = self.sintaxe.iloc[line, i]
            i+=1
            Valores_Agrup = self.sintaxe.iloc[line, i]
            i+=1
            Fecha_100 = self.sintaxe.iloc[line, i]
            i+=1
            Var_ID = self.sintaxe.iloc[line, i]
            i+=1
            Var_Pond = self.sintaxe.iloc[line, i]
            i+=1
            Titulo = self.sintaxe.iloc[line, i]

            res_TipoTabela = verif_TipoTabela(TipoTabela)
            if res_TipoTabela == 1:
                 return f"⚠️ Verificar incosistência: o **Tipo de Tabela** informado na linha {line+2} não corresponde com as opções válidas: [SIMPLES, IPA_5, IPA_10, NPS, MULTIPLA]"
            
            res_bandeiras_cabecalho = verif_bandeiras_cabecalho(Bandeiras, Cabecalho)
            if res_bandeiras_cabecalho == 1:
                 return f"⚠️ Verificar incosistência: na linha {line+2}, **o nº de Bandeiras não é compatível com o nº de inputs do Cabeçalho**."
            
            res_bandeira, col = verif_bandeiras(df, Bandeiras)
            if res_bandeira == 1:
                 return f"⚠️ Coluna **{col}** que se encontra na coluna **Bandeiras** não foi encontrada no Banco de dados."
            
            res_Var_linha = verif_Var_linha(df, Var_linha, TipoTabela)
            if res_Var_linha == 1:
                 return f"⚠️ Verificar incosistência: na linha {line+2}, a variável/coluna informada que representa o **nível da linha** da tabela não consta no Banco de dados."
            
            res_NS_NR = verif_NS_NR(NS_NR)
            if res_NS_NR == 1:
                 return f"⚠️ Verificar incosistência: o valor informado na linha {line+2} da coluna **Contabiliza_NS/NR** não corresponde com as opções válidas: [NAO, SIM]"
            
            res_Fecha_100 = verif_Fecha_100(TipoTabela, Fecha_100)
            if res_Fecha_100 == 1:
                 return(f"⚠️ Verificar incosistência: o valor informado na linha {line+2} da coluna **Fecha_100** não corresponde com as opções válidas: [NAO, SIM]")
            
            res_Var_ID = verif_coluna_existe(df, Var_ID)
            if res_Var_ID == 1:
                 return f"⚠️ Verificar incosistência: na linha {line+2}, a variável/coluna informada que representa o **Código de identificação da entrevista** não consta no Banco de dados."
            
            res_Var_Pond = verif_coluna_existe(df, Var_Pond)
            if res_Var_Pond == 1:
                 return f"⚠️ Verificar incosistência: na linha {line+2}, a variável/coluna informada que representa a **Ponderação** não consta no Banco de dados."
        return 0   
