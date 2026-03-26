from __future__ import annotations
import pandas as pd
import numpy as np
import streamlit as st
import time
from io import BytesIO
from datetime import datetime, date
from metodos import Criar_Pond
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple, Union, Optional

st.set_page_config(layout='wide', page_title='Processamento de dados', 
                   page_icon='images/Logo_Expertise.png')

st.logo(image="images/ExpertiseAI.svg", size="large")

if "data" not in st.session_state or st.session_state.data is None:
    st.warning("Antes de tudo, carregue o banco de dados com os códigos e lista de labels na página Home.", icon="⚠️")
    st.stop()

if "button_gerar_pond_bool" not in st.session_state:
    st.session_state.button_gerar_pond_bool = False

st.title('Pré-Processamento de Dados Estatísticos')
st.divider()
st.subheader('Aqui você pode criar a coluna de Ponderação')
st.write('')

tab1, tab2 = st.tabs(["Ponderação", "RAKE (IPF)"])

with tab1:
    c1, c2 = st.columns(2, vertical_alignment="bottom")

    with st.form('sheet_name_DFuniverso_DFcoletado'):
        with c1:
            st.write('')
            st.write('')
            st.write('')
            with st.container(border=True):
                nome_sheet_df_universo = st.text_input(
                    label="📝 Digite o nome da aba (sheet) que contém a tabela com a **quantidade real do universo do projeto**.", 
                    value="FONTE",
                    help="A tabela deverá conter duas categorias (Coluna, Linha).",
                    key="pond_nome_sheet_df_universo"
                    )
        with c2:
            with st.container(border=True):
                qtd_dimensao = st.number_input(
                    label="📝 Digite a quantidade de **dimensões** da sua tabela, ou seja, quantas variáveis serão combinadas para criar a ponderação.",
                    value=3,
                    min_value=2,
                    max_value=5,
                    key="pond_qtd_dimensao",
                    # help="Informe a quantidade de **dimensões** da sua tabela, ou seja, quantas variáveis serão combinadas para criar a ponderação."
                )            


        with st.status("🔍 A seguir, veja uma imagem de exemplo da tabela:"):
            if qtd_dimensao == 2:
                st.write("2 dimensões:")
                st.image(image="images/Tabela fonte universo_2dim.png")
            elif qtd_dimensao == 3:
                st.write("3 dimensões:")
                st.image(image="images/Tabela fonte universo.png")
            elif qtd_dimensao == 4:
                st.write("4 dimensões:")
                st.image(image="images/Tabela fonte universo_4dim.png")
            elif qtd_dimensao == 5:
                st.write("5 dimensões:")
                st.image(image="images/Tabela fonte universo_5dim.png")

        with st.container(border=True):
                nome_pond = st.text_input(
                    label="📝 Digite o nome da coluna de **Ponderação** desejado.",
                    value="POND",
                    key="pond_nome_pond",
                    help="Nome da coluna de Ponderação a ser construída com os dados da FONTE."
                )

        input_buttom_submit_DATA = st.form_submit_button("Enviar", icon=":material/done_outline:")

    if input_buttom_submit_DATA:
        st.session_state.nome_sheet_df_universo = nome_sheet_df_universo
        st.session_state.qtd_dimensao = qtd_dimensao
        st.session_state.nome_pond = nome_pond

        if not st.session_state.nome_sheet_df_universo:
            st.error("Preencha o nome da aba antes de continuar.", icon="❌")
        else:
            st.success("Nome da aba (sheet) enviado com sucesso", icon="✅")

    st.write('')
    st.write('')
    data_file_pond = st.file_uploader(
        "📂 Selecione o banco de dados (em xlsx)", 
        type=["xlsx"], 
        help="Selecione o arquivo Excel contendo as tabelas **quantidade real do universo do projeto** e **quantidade coletada do projeto**.", 
        key="ponderacao_uploader"
        )

    if data_file_pond is not None:
        # Lista as abas disponíveis (ajuda muito a evitar erro)
        xls = pd.ExcelFile(data_file_pond)
        st.caption(f"Abas encontradas no arquivo: {',  '.join(xls.sheet_names)}")

        sheet_univ = st.session_state.get("nome_sheet_df_universo", "")

        # Validações antes de ler
        if sheet_univ not in xls.sheet_names:
            st.error(f"A aba do universo '{sheet_univ}' não existe no arquivo.", icon="❌")
            st.stop()


        if st.session_state.qtd_dimensao == 2:
            df_universo = pd.read_excel(
                data_file_pond, 
                sheet_name=nome_sheet_df_universo,
                index_col=0
            )
            
        elif st.session_state.qtd_dimensao == 3:
            df_universo = pd.read_excel(
                data_file_pond, 
                sheet_name=nome_sheet_df_universo,
                header=[0, 1],
                index_col=0 
            )
        
        elif st.session_state.qtd_dimensao == 4:
            df_universo = pd.read_excel(
                data_file_pond, 
                sheet_name=nome_sheet_df_universo,
                header=[0, 1, 2],
                index_col=0 
            )
            
        elif st.session_state.qtd_dimensao == 5:
            df_universo = pd.read_excel(
                data_file_pond, 
                sheet_name=nome_sheet_df_universo,
                header=[0, 1, 2, 3],
                index_col=0 
            )

        st.session_state.df_universo = df_universo
        # st.session_state.df_coletado = df_coletado
        
        st.success("Planilha carregada com sucesso!", icon="✅")


        Criar_ponderacao = Criar_Pond(
            df_universo=st.session_state.df_universo, 
            bd_codigo=st.session_state.data, 
            lista_labels=st.session_state.lista_labels,
            nome_pond=st.session_state.nome_pond
        )
        Criar_ponderacao.n_niveis_colunas()
        result = Criar_ponderacao.verificar_cols_multiindex()
        if isinstance(result, str):
            st.error(result, icon="❌")
        else:
            df_coletado = Criar_ponderacao.criar_df_coletado()
            st.divider()
            st.write("Visualização da amostra coletada para cada dimensão: ")
            st.dataframe(df_coletado, hide_index=False, selection_mode=["multi-row", "multi-cell"], width='stretch')
            total_coletado = df_coletado.sum().sum()
            st.write(f"Total da amostra coletada: ", total_coletado)

            st.write("")
            st.write("")
            if st.button(label="Gerar Ponderação", key="button_gerar_pond", icon=":material/done_outline:"):
                st.session_state.button_gerar_pond_bool = True

            if st.session_state.button_gerar_pond_bool:
                st.session_state.data, lista_de_colunas_indice = Criar_ponderacao.criar_pond()
                st.write("")

                with st.spinner("Please wait..."):
                    with st.expander("📋 Colunas"):
                        # default_cols = st.session_state.data.columns.tolist()
                        colunas = st.multiselect('Selecione as colunas que deseja visualizar:', 
                                                    st.session_state.data.columns.tolist(), 
                                                    default=lista_de_colunas_indice + [st.session_state.nome_pond],
                                                    key="pond_colunas")
                    dados_filtrados = st.session_state.data[colunas]
                    st.dataframe(dados_filtrados, hide_index=True, selection_mode=["multi-row", "multi-cell"], width='stretch')
                    st.success("Ponderação realizada com sucesso!", icon="✅")



@dataclass
class RakeResult:
    weights: pd.Series
    targets_abs: Dict[str, Dict[Union[int, str], float]]
    iterations: int
    converged: bool
    max_rel_change: float
    checks: Dict[str, pd.DataFrame]


def _parse_w_vars(
    w_vars: Iterable[Tuple[str, Union[int, str], float]]
) -> Dict[str, Dict[Union[int, str], float]]:
    """
    Converte lista de triplas (var, code, quota) em:
    {var: {code: quota, ...}, ...}
    """
    out: Dict[str, Dict[Union[int, str], float]] = {}
    for var, code, quota in w_vars:
        if var not in out:
            out[var] = {}
        if code in out[var]:
            raise ValueError(f"Categoria duplicada: var='{var}', code='{code}'.")
        if quota is None or not np.isfinite(quota):
            raise ValueError(f"Quota inválida para var='{var}', code='{code}': {quota}")
        if quota < 0:
            raise ValueError(f"Quota negativa para var='{var}', code='{code}': {quota}")
        out[var][code] = float(quota)
    if not out:
        raise ValueError("w_vars vazio. Informe ao menos uma variável/categoria/quota.")
    return out


def _normalize_quotas(quotas_by_var: Dict[str, Dict[Union[int, str], float]]) -> Dict[str, Dict[Union[int, str], float]]:
    """
    Normaliza as quotas de cada variável para somarem 1.
    (Replicando o comentário da macro SPSS: se quotas não somarem 1, ela reescala.)
    """
    normed: Dict[str, Dict[Union[int, str], float]] = {}
    for var, qdict in quotas_by_var.items():
        s = sum(qdict.values())
        if s <= 0:
            raise ValueError(f"Soma das quotas da variável '{var}' é <= 0. Não é possível normalizar.")
        normed[var] = {code: q / s for code, q in qdict.items()}
    return normed


def _make_targets_abs(
    N: float,
    quotas_normed: Dict[str, Dict[Union[int, str], float]]
) -> Dict[str, Dict[Union[int, str], float]]:
    """
    Converte quota -> total-alvo absoluto: target = N * quota
    """
    return {var: {code: N * q for code, q in qdict.items()} for var, qdict in quotas_normed.items()}


def rake_by_quota_spss_style(
    df: pd.DataFrame,
    *,
    N: float,
    w_vars: Iterable[Tuple[str, Union[int, str], float]],
    weight_col: str = "weight",
    maxit: int = 200,
    epsilon: float = 1e-10,
    clip: Optional[Tuple[float, float]] = None,
    verbose: bool = False,
) -> RakeResult:
    """
    Replica o comportamento essencial da macro SPSS (rake por quotas):
    - Inicializa peso = 1
    - Normaliza quotas por variável (se não somarem 1)
    - Converte quotas para targets absolutos: N * quota
    - Ajusta iterativamente alternando variáveis
    - (Opcional) aplica corte de pesos (clip) se você quiser evitar extremos

    Parâmetros:
      df: DataFrame com colunas das variáveis (ex.: 'TIPO_NIV', 'TIPO_REG')
      N: total final desejado (soma dos pesos)
      w_vars: lista de triplas (var, code, quota) como no SPSS
      weight_col: nome da coluna de peso a ser criada/atualizada
      maxit: iterações máximas
      epsilon: tolerância de convergência (maior variação relativa do peso)
      clip: (min, max) para truncar pesos se necessário (opcional)
      verbose: imprime progresso

    Retorna:
      RakeResult com pesos, targets e tabelas de checagem.
    """
    if N is None or not np.isfinite(N) or N <= 0:
        raise ValueError(f"N inválido: {N}. Deve ser > 0.")

    quotas_by_var = _parse_w_vars(w_vars)
    quotas_normed = _normalize_quotas(quotas_by_var)
    targets_abs = _make_targets_abs(float(N), quotas_normed)

    # checagens de presença de colunas e categorias
    for var, tdict in targets_abs.items():
        if var not in df.columns:
            raise KeyError(f"Coluna '{var}' não existe no df.")
        # missing
        if df[var].isna().any():
            raise ValueError(f"Há missing (NaN) na coluna '{var}'. Trate antes de ponderar.")
        # categorias alvo precisam existir na amostra (senão divisão por zero)
        present = set(df[var].unique().tolist())
        missing_cats = [c for c in tdict.keys() if c not in present]
        if missing_cats:
            raise ValueError(
                f"Categorias {missing_cats} de '{var}' não aparecem na amostra. "
                "Rake por margens 1D não consegue ajustar quando a categoria está ausente."
            )

    # inicializa pesos = 1 (como a macro)
    w = np.ones(len(df), dtype=float)

    # ordem das variáveis (como a macro percorre cada critério)
    var_order = list(targets_abs.keys())

    converged = False
    max_rel_change = np.inf
    it_done = 0

    for it in range(1, maxit + 1):
        w_old = w.copy()

        for var in var_order:
            # total ponderado atual por categoria
            cur = (
                pd.DataFrame({var: df[var].values, "_w": w})
                .groupby(var)["_w"].sum()
            )

            # aplica fator por categoria: target / current
            for code, target in targets_abs[var].items():
                current = float(cur.loc[code])
                if current <= 0:
                    raise ValueError(
                        f"Total ponderado atual 0 para var='{var}', cat='{code}'. "
                        "Isso não deveria ocorrer se a categoria existe na amostra."
                    )
                factor = target / current
                mask = (df[var].values == code)
                w[mask] *= factor

        # opcional: truncar pesos
        if clip is not None:
            lo, hi = clip
            if lo <= 0 or hi <= 0 or lo > hi:
                raise ValueError(f"clip inválido: {clip}. Use (min>0, max>0, min<=max).")
            w = np.clip(w, lo, hi)

        # convergência: maior mudança relativa do peso
        rel = np.max(np.abs(w - w_old) / (np.abs(w_old) + 1e-12))
        max_rel_change = float(rel)
        it_done = it

        if verbose:
            print(f"it={it:3d}  max_rel_change={max_rel_change:.3e}  sum_w={w.sum():.6f}")

        if max_rel_change < epsilon:
            converged = True
            break

    # resultados e checagens (estilo SPSS "quota vs weighted")
    w_series = pd.Series(w, index=df.index, name=weight_col)

    checks: Dict[str, pd.DataFrame] = {}
    for var in var_order:
        weighted = (
            pd.DataFrame({var: df[var].values, "_w": w})
            .groupby(var)["_w"].sum()
            .reindex(list(targets_abs[var].keys()))
        )
        target = pd.Series(targets_abs[var]).reindex(weighted.index).astype(float)

        # percentuais
        weighted_pct = weighted / w.sum()
        target_pct = target / float(N)  # como target = N * quota, isso volta à quota

        checks[var] = pd.DataFrame({
            "target_abs": target.values,
            "weighted_abs": weighted.values,
            "target_pct": target_pct.values,
            "weighted_pct": weighted_pct.values,
        }, index=weighted.index)

    return RakeResult(
        weights=w_series,
        targets_abs=targets_abs,
        iterations=it_done,
        converged=converged,
        max_rel_change=max_rel_change,
        checks=checks
    )


with tab2:
    st.write('')
    st.write('')
    st.write('')
    with st.form('sheet_name_fonte_rake'):
        with st.container(border=True):
            N_universo = st.number_input(
                label="Digite o total ponderado final desejado (o “universo” do rake)",
                value=1212,
                step=1,
                key="rake_N_universo"
            )
        with st.container(border=True):
            nome_sheet_df_rake = st.text_input(
                label="📝 Digite o nome da aba (sheet) que contém a tabela com os **Totais marginais em percentual** das características demográficas importantes para o estudo.", 
                value="RAKE",
                # help="A tabela deverá conter duas categorias (Coluna, Linha).",
                key="pond_nome_sheet_rake"
            )
            
            with st.status("🔍 A seguir, veja uma imagem de exemplo da tabela:"):
                st.image(image="images/Tabela fonte pond rake.png")
        input_buttom_submit_DATA_rake = st.form_submit_button("Enviar", icon=":material/done_outline:")

    if input_buttom_submit_DATA_rake:
        st.session_state.nome_sheet_df_rake = nome_sheet_df_rake
        st.session_state.N_universo = int(N_universo)

        if not st.session_state.nome_sheet_df_rake:
            st.error("Preencha o nome da aba antes de continuar.", icon="❌")
        else:
            st.success("Nome da aba (sheet) enviado com sucesso", icon="✅")


    st.write('')
    data_file_pond_rake = st.file_uploader(
        "📂 Selecione o banco de dados (em xlsx)", 
        type=["xlsx"], 
        help="Selecione o arquivo Excel contendo a tabela com os **Totais marginais em percentual** das características demográficas.", 
        key="ponderacao_rake_uploader"
    )

    if data_file_pond_rake is not None:
        # Lista as abas disponíveis (ajuda muito a evitar erro)
        xls = pd.ExcelFile(data_file_pond_rake)
        st.caption(f"Abas encontradas no arquivo: {',  '.join(xls.sheet_names)}")

        sheet_rake = st.session_state.get("nome_sheet_df_rake", "")

        # Validações antes de ler
        if st.session_state.nome_sheet_df_rake not in xls.sheet_names:
            st.error(f"A aba dos **Totais marginais** '{sheet_rake}' não existe no arquivo.", icon="❌")
            st.stop()

        df_rake = pd.read_excel(
            data_file_pond_rake, 
            sheet_name=nome_sheet_df_rake
            )
        st.session_state.df_rake = df_rake
        st.success("Planilha carregada com sucesso!", icon="✅")
        st.write("")

        # ========================================================== #
        # Verificar se as colunas existem no df_rake
        def verif_cols(df_rake, colunas=["Colunas", "Codigo", "% marginal"]):
            for col in colunas:
                if col not in df_rake.columns:
                    return f"Coluna **{col}** não se encontra na tabela do arquivo em excel, favor verificar!"
            return 0
        res_verif_cols = verif_cols(st.session_state.df_rake)
        if isinstance(res_verif_cols, str):
            st.error(res_verif_cols, icon="❌")
        else:
            # Criar o conjunto de alvo (percentual/quota) para cada label das colunas
            w_vars = []
            for i, col in enumerate(df_rake["Colunas"]):
                codigo = int(df_rake.loc[i, "Codigo"])
                perc = float(df_rake.loc[i, "% marginal"])
                w_vars.append((col, codigo, perc))

            res = rake_by_quota_spss_style(
                st.session_state.data,
                N=st.session_state.N_universo,
                w_vars=w_vars,
                weight_col="weight",
                maxit=200,
                epsilon=1e-10,
                clip=None,
                verbose=True
            )

            st.session_state.data["POND_RAKE"] = res.weights
            
            COLUNAS = [col for col in st.session_state.data.columns.tolist() if col != "w_base"]
            with st.spinner("Please wait..."):
                st.write("")
                st.write("")
                with st.expander("📋 Colunas"):
                    # default_cols = st.session_state.data.columns.tolist()
                    colunas = st.multiselect('Selecione as colunas que deseja visualizar:', 
                                                COLUNAS, 
                                                default=COLUNAS,
                                                key="pond_rake_colunas"
                                            )
                dados_filtrados = st.session_state.data[colunas]
                st.dataframe(dados_filtrados, hide_index=True, selection_mode=["multi-row", "multi-cell"], width='stretch')
                st.success("Ponderação realizada com sucesso!", icon="✅")


    
st.write("")
st.write("")
st.write("")
st.divider()
st.write('')
st.write('')
st.image(image="images/Expertise_Marca_VerdeEscuro_mini.jpg")





