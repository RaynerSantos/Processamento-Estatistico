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

TipoTabela = 'MULTIPLA'
Colunas = 'ONDA, VSEG_BU, VSEG_1, PF_PJ, VREG'
Ordem_ONDA = 'ONDA_G, Jul24, Nov24, Mar25, Jul25'
Cabecalho = 'Onda, Segmento BU, Segmento, Pessoa, Regional'
Var_linha = 'MOTNEU' # ADER_AG2 | NPS_C
NS_NR = 'NAO'
valores_BTB = ''
valores_TTB = ''
Valores_Agrup = 'MOTNEU_1, MOTNEU_2, MOTNEU_3'
Fecha_100 = 'NAO'
Var_ID = 'ID_EMP'
Var_Pond = 'POND'
Titulo = 'Aderencia Mono e Multi'

# Variáveis para as colunas da tabela (bandeiras)
Colunas = Colunas.split(sep=', ')
Valores_Agrup = Valores_Agrup.split(sep=', ')

def ordenar_labels(df, lista_labels, Variavel):
    print(f"\n#== VARIÁVEL SENDO PROCESSADA: {Variavel} ==#")
    # print(f"df_tratamento[Variavel] (antes de ordenar):\n{df[Variavel].head(10)}")
    print(df[Variavel].value_counts(), '\n')
    print(df[Variavel].value_counts(normalize=True))
    lista_labels = lista_labels.iloc[1:, :].copy()
    lista_labels.columns = ['Coluna', 'Codigo', 'Label']
    lista_labels["Coluna"] = lista_labels["Coluna"].ffill().str.strip()

    # Normalizar "Codigo" para numérico (trocando vírgula por ponto)
    lista_labels["Codigo"] = (lista_labels["Codigo"].astype(str).str.strip().str.replace(',', '.', regex=False))
    lista_labels["Codigo"] = pd.to_numeric(lista_labels["Codigo"], errors="coerce")
    # print(lista_labels.head(6))

    # Filtrar apenas os labels da coluna alvo
    labels_sub = lista_labels.loc[lista_labels["Coluna"] == Variavel, ["Codigo", "Label"]].dropna(subset=["Codigo"])
    labels_sub["Codigo"] = (
        labels_sub["Codigo"]
            .astype(str).str.strip().str.replace(",", ".", regex=False)
    )
    labels_sub["Codigo"] = pd.to_numeric(labels_sub["Codigo"], errors="coerce")
    labels_sub["Codigo"] = labels_sub["Codigo"].round().astype("Int64")
    print("\nLabels filtrados para a coluna alvo:\n", labels_sub)

    # df[Variavel] = df[Variavel].replace('NS/NR', np.nan)
    df[Variavel] = pd.to_numeric(df[Variavel], errors='coerce')  # converter para numérico, tratando erros como NaN
    df[Variavel] = df[Variavel].round().astype("Int64")

    # --- Descobrir a ordem numérica presente nos dados ---
    print(f"\ndf[Variavel] (antes de ordenar):\n{df[Variavel].head(10)}")
    codigos_ordenados = (
        pd.Series(df[Variavel].dropna().unique(), dtype="Int64")
        .sort_values()
        .to_frame(name="Codigo")
    )

    print("\nOrdem numérica encontrada:", codigos_ordenados["Codigo"].tolist())

    # --- Mapear códigos -> labels via merge (evita problemas de tipo) ---
    ordem_mapeada = codigos_ordenados.merge(labels_sub, on="Codigo", how="left")
    print("\nOrdem mapeada com labels:\n", ordem_mapeada)

    # Categorias finais na ordem desejada
    ord_labels = ordem_mapeada["Label"].tolist()
    ord_labels = [label for label in ord_labels if pd.notna(label)]
    print("\nOrdem final com labels:", ord_labels)

    # Merge na base para criar uma coluna label
    Variavel_labels = df.merge(ordem_mapeada.rename(columns={"Label": f"{Variavel}_LABEL"}),
                left_on=Variavel, right_on="Codigo", how="left")[f"{Variavel}_LABEL"]
    # print(f"Coluna de labels adicionada ao DataFrame:\n{df.head(10)}")

    # Define categórica ordenada com as categorias encontradas
    Variavel_labels = pd.Categorical(Variavel_labels,
                                            categories=ord_labels,
                                            ordered=True)
    print(f"\nColuna categórica ordenada criada: {Variavel_labels[0:10]}")
    bd_teste = pd.DataFrame({Variavel: Variavel_labels})
    print(bd_teste[Variavel].value_counts(), '\n')
    print(bd_teste[Variavel].value_counts(normalize=True))

    return Variavel_labels, ord_labels

def ordenar_labels_multipla(df, lista_labels, Variavel):
    lista_labels = lista_labels.iloc[1:, :]
    lista_labels.columns = ['Coluna', 'Codigo', 'Label']
    lista_labels["Coluna"] = lista_labels["Coluna"].fillna(method="ffill").str.strip()

    # Normalizar "Codigo" para numérico (trocando vírgula por ponto)
    lista_labels["Codigo"] = (lista_labels["Codigo"].astype(str).str.strip().str.replace(',', '.', regex=False))
    lista_labels['Codigo'] = pd.to_numeric(lista_labels["Codigo"], errors='ignore')
    # print(lista_labels.head(6))

    # Filtrar apenas os labels da coluna alvo
    labels_sub = lista_labels.loc[lista_labels["Coluna"] == f'{Variavel}_1', ["Codigo", "Label"]].dropna(subset=["Codigo"])
    labels_sub["Codigo"] = (
        labels_sub["Codigo"]
            .astype(str).str.strip().str.replace(",", ".", regex=False)
    )
    labels_sub["Codigo"] = pd.to_numeric(labels_sub["Codigo"], errors="coerce")
    labels_sub["Codigo"] = labels_sub["Codigo"].round().astype("Int64")
    print("Labels filtrados para a coluna alvo:\n", labels_sub)

    # df[Variavel] = df[Variavel].replace('NS/NR', np.nan)
    df[Variavel] = pd.to_numeric(df[Variavel], errors='coerce')  # converter para numérico, tratando erros como NaN
    df[Variavel] = df[Variavel].round().astype("Int64")

    # --- Descobrir a ordem numérica presente nos dados ---
    codigos_ordenados = (
        pd.Series(df[Variavel].dropna().unique(), dtype="Int64")
        .sort_values()
        .to_frame(name="Codigo")
    )

    print("Ordem numérica encontrada:", codigos_ordenados["Codigo"].tolist())

    # --- Mapear códigos -> labels via merge (evita problemas de tipo) ---
    ordem_mapeada = codigos_ordenados.merge(labels_sub, on="Codigo", how="left")
    print("Ordem mapeada com labels:\n", ordem_mapeada)

    # Categorias finais na ordem desejada
    ord_labels = ordem_mapeada["Label"].tolist()
    ord_labels = [label for label in ord_labels if pd.notna(label)]
    print("Ordem final com labels:", ord_labels)

    # (2) Faça o merge na base para criar uma coluna label
    df = df.merge(ordem_mapeada.rename(columns={"Label": f"{Variavel}_LABEL"}),
                left_on=Variavel, right_on="Codigo", how="left")
    print(f"Coluna de labels adicionada ao DataFrame:\n{df.head(10)}")

    # (3) Defina categórica ordenada com as categorias encontradas
    df[f"{Variavel}_LABEL"] = pd.Categorical(df[f"{Variavel}_LABEL"],
                                            categories=ord_labels,
                                            ordered=True)

    # (4) Se quiser, substitua a coluna original pela label
    # Variavel_labels = df[f"{Variavel}_LABEL"]
    df[Variavel] = df[f"{Variavel}_LABEL"]
    # print("\nValores únicos finais (ordenados):", df[f"{Variavel}"].head(10))
    df.drop(columns=["Codigo", f"{Variavel}_LABEL"], inplace=True)  # ajuste conforme preferir

    # print("\nValores únicos finais (ordenados):", df[f"{Var_linha}"].unique())

    return df


lista_labels = pd.read_excel(r'C:\PROJETOS\Processamento-Estatistico\BASES PARA PROCESSAMENTO\Cielo NPS 2025\OB\BD_Cielo_NPS_Fev25_2025.03.14_completo.xlsx', sheet_name='Lista de Labels')


# --- carregar base principal ---
df = pd.read_excel(r'C:\PROJETOS\Processamento-Estatistico\BASES PARA PROCESSAMENTO\Cielo NPS 2025\OB\BD_Cielo_NPS_Fev25_2025.03.14_completo.xlsx', sheet_name='BD_CODIGOS')
bd_motivo = pd.melt(df, 
                    id_vars=Colunas + [Var_Pond] + [Var_ID],
                    value_vars=Valores_Agrup, 
                    var_name='Valores', 
                    value_name=Var_linha)
# bd_motivo[Var_linha] = bd_motivo[Var_linha].replace('90', np.nan)
# bd_motivo[Var_linha] = bd_motivo[Var_linha].replace('99', np.nan)
# bd_motivo[Var_linha] = bd_motivo[Var_linha].replace('999', np.nan)
# bd_motivo[Var_linha] = bd_motivo[Var_linha].replace('9999', np.nan)
bd_motivo = bd_motivo.dropna(subset=[Var_linha])
print(f'bd_motivo em formato de código:\n{bd_motivo}')


# Var_linha_labels = ordenar_labels(df, lista_labels, Var_linha)
# print("\nValores únicos finais (ordenados):\n", Var_linha_labels.head(5))  
bd_motivo = ordenar_labels_multipla(bd_motivo, lista_labels, Var_linha)
# print("\nValores únicos finais (ordenados):\n", Var_linha_labels.tail(5))  

# bd_motivo[Var_linha] = ordenar_labels_multipla(bd_motivo, lista_labels, Var_linha)
# bd_motivo[Var_linha] = bd_motivo[Var_linha].replace('NS/NR', np.nan)
bd_motivo = bd_motivo.dropna(subset=[Var_linha])
print(f'bd_motivo finalizado:\n{bd_motivo}')

# for col in Colunas:
#     if col not in df.columns:
#         raise ValueError(f"Coluna '{col}' não encontrada no DataFrame.")        
#     else:
#         df[col] = ordenar_labels(df=df, lista_labels=lista_labels, Variavel=col)
#         print(f"Coluna ordenada: {df[col].unique()}")
#         # df[col] = pd.Categorical(df[col], categories=df[col][pd.notna(df[col])].unique(), ordered=True)