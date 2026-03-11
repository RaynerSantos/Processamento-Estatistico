import pandas as pd
import numpy as np

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
    ord_labels = list(dict.fromkeys(ord_labels))  # Remove duplicates while preserving order
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

def ordenar_labels_multipla(df, lista_labels, Variavel, Var_Valores_Agrup):
    print(f"\n#== VARIÁVEL SENDO PROCESSADA: {Variavel} ==#")
    lista_labels = lista_labels.iloc[1:, :].copy()
    lista_labels.columns = ['Coluna', 'Codigo', 'Label']
    lista_labels["Coluna"] = lista_labels["Coluna"].ffill().str.strip()

    # Normalizar "Codigo" para numérico (trocando vírgula por ponto)
    lista_labels["Codigo"] = (lista_labels["Codigo"].astype(str).str.strip().str.replace(',', '.', regex=False))
    lista_labels['Codigo'] = pd.to_numeric(lista_labels["Codigo"], errors='coerce')
    # print(lista_labels.head(6))

    # Filtrar apenas os labels da coluna alvo
    labels_sub = lista_labels.loc[lista_labels["Coluna"] == f'{Var_Valores_Agrup}', ["Codigo", "Label"]].dropna(subset=["Codigo"])
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
    ord_labels = list(dict.fromkeys(ord_labels))  # Remove duplicates while preserving order
    print("Ordem final com labels:", ord_labels)

    # (2) Faça o merge na base para criar uma coluna label
    df = df.merge(ordem_mapeada.rename(columns={"Label": f"{Variavel}_LABEL"}),
                left_on=Variavel, right_on="Codigo", how="left")
    print(f"Coluna de labels adicionada ao DataFrame:\n{df}")

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


# ord_labels = [np.nan, np.nan, np.nan, 'NS/NR']
# # Removendo os valores NaN da lista
# ord_labels = [label for label in ord_labels if pd.notna(label)]
# print("Ordem de labels:", ord_labels)

# dict_ord_labels = {}
# ord_labels = ['Empreendedores', 'Varejo', 'Alto Varejo Cielo', 'Alto Varejo Bancos', 'GC']
# Colunas = 'ONDA, VSEG_BU, VSEG_1, PF_PJ, VREG'
# Colunas = Colunas.split(sep=', ')

# dict_ord_labels[Colunas[1]] = ord_labels
# print("Dicionário de labels:", dict_ord_labels[Colunas[1]])

