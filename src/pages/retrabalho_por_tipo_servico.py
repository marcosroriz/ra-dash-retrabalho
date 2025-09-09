#!/usr/bin/env python
# coding: utf-8

# Dashboard que lista o retrabalho de um tipo de serviço

##############################################################################
# IMPORTS ####################################################################
##############################################################################
# Bibliotecas básicas
from datetime import date
import pandas as pd

# Importar bibliotecas do dash básicas e plotly
import dash
from dash import Dash, html, dcc, callback, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go

# Importar bibliotecas do bootstrap e ag-grid
import dash_bootstrap_components as dbc
import dash_ag_grid as dag

# Dash componentes Mantine e icones
import dash_mantine_components as dmc
from dash_iconify import DashIconify

# Importar nossas constantes e funções utilitárias
import tema
import locale_utils

# Banco de Dados
from db import PostgresSingleton

# Imports gerais
from modules.entities_utils import get_mecanicos, get_lista_os, get_oficinas, get_secoes, get_modelos

# Imports específicos
from modules.tipo_servico.tipo_servico_service import TipoServicoService
import modules.tipo_servico.graficos as tipo_servico_graficos
import modules.tipo_servico.tabelas as tipo_servico_tabelas

##############################################################################
# LEITURA DE DADOS ###########################################################
##############################################################################
# Conexão com os bancos
pgDB = PostgresSingleton.get_instance()
pgEngine = pgDB.get_engine()

# Cria o serviço
tipo_servico_service = TipoServicoService(pgEngine)

# Obtem a lista de Oficinas
df_oficinas = get_oficinas(pgEngine)
lista_todas_oficinas = df_oficinas.to_dict(orient="records")
lista_todas_oficinas.insert(0, {"LABEL": "TODAS"})

# Obtem a lista de Seções
df_secoes = get_secoes(pgEngine)
lista_todas_secoes = df_secoes.to_dict(orient="records")
lista_todas_secoes.insert(0, {"LABEL": "TODAS"})

# Colaboradores / Mecânicos
df_mecanicos = get_mecanicos(pgEngine)

# Modelos de veículos
df_modelos_veiculos = get_modelos(pgEngine)
lista_todos_modelos_veiculos = df_modelos_veiculos.to_dict(orient="records")
lista_todos_modelos_veiculos.insert(0, {"MODELO": "TODOS"})

# Obtem a lista de OS
df_lista_os = get_lista_os(pgEngine)
lista_todas_os = df_lista_os.to_dict(orient="records")
# lista_todas_os.insert(0, {"LABEL": "TODAS"})

##############################################################################
# CALLBACKS ##################################################################
##############################################################################

##############################################################################
# Callbacks para os inputs ###################################################
##############################################################################

# Função para formatar valores em R$
# Outra possibilidade é usar locale, porém podemos rodar em um ambiente sem locale pt_BR
def formata_moeda(valor):
    return "{:,.2f}".format(valor).replace(',', 'X').replace('.', ',').replace('X', '.')

# Função para validar o input
def input_valido_tela_tipo_servico(datas, min_dias, lista_modelos, lista_oficinas, lista_os):
    if datas is None or not datas or None in datas or min_dias is None:
        return False

    if lista_modelos is None or not lista_modelos or None in lista_modelos:
        return False

    if lista_oficinas is None or not lista_oficinas or None in lista_oficinas:
        return False

    if lista_os is None or not lista_os or None in lista_os:
        return False

    return True


# Corrige o input para garantir que o termo para todas ("TODAS") não seja selecionado junto com outras opções
def corrrige_input_tipo_servico(lista, termo_all="TODAS"):
    # Caso 1: Nenhuma opcao é selecionada, reseta para "TODAS"
    if not lista:
        return [termo_all]

    # Caso 2: Se "TODAS" foi selecionado após outras opções, reseta para "TODAS"
    if len(lista) > 1 and termo_all in lista[1:]:
        return [termo_all]

    # Caso 3: Se alguma opção foi selecionada após "TODAS", remove "TODAS"
    if termo_all in lista and len(lista) > 1:
        return [value for value in lista if value != termo_all]

    # Por fim, se não caiu em nenhum caso, retorna o valor original
    return lista


@callback(
    Output("input-select-modelo-veiculos-visao-tipo-servico", "value"),
    Input("input-select-modelo-veiculos-visao-tipo-servico", "value"),
)
def corrige_input_modelos_tela_tipo_servico(lista_modelos):
    return corrrige_input_tipo_servico(lista_modelos, "TODOS")


@callback(
    Output("input-select-oficina-visao-tipo-servico", "value"),
    Input("input-select-oficina-visao-tipo-servico", "value"),
)
def corrige_input_oficinas_tela_tipo_servico(lista_oficinas):
    return corrrige_input_tipo_servico(lista_oficinas, "TODAS")


##############################################################################
# Callback para gerar labels dinâmicos
##############################################################################


def gera_labels_inputs(campo):
    # Cria o callback
    @callback(
        [
            Output(component_id=f"{campo}-labels", component_property="children"),
        ],
        [
            Input("input-intervalo-datas-os", "value"),
            Input("input-select-dias-os-retrabalho", "value"),
            Input("input-select-modelo-veiculos-visao-tipo-servico", "value"),
            Input("input-select-oficina-visao-tipo-servico", "value"),
            Input("input-select-ordens-servico-visao-tipo-servico", "value"),
        ],
    )
    def atualiza_labels_inputs_tipo_servico(datas, min_dias, lista_modelos, lista_oficinas, lista_os):
        labels_antes = [
            # DashIconify(icon="material-symbols:filter-arrow-right", width=20),
            dmc.Badge("Filtro", color="gray", variant="outline"),
        ]

        datas_label = []
        if not (datas is None or not datas) and datas[0] is not None and datas[1] is not None:
            # Formata as datas
            data_inicio_str = pd.to_datetime(datas[0]).strftime("%d/%m/%Y")
            data_fim_str = pd.to_datetime(datas[1]).strftime("%d/%m/%Y")

            datas_label = [dmc.Badge(f"{data_inicio_str} a {data_fim_str}", variant="outline")]

        min_dias_label = [dmc.Badge(f"{min_dias} dias", variant="outline")]

        lista_modelos_labels = []
        lista_oficinas_labels = []
        lista_os_labels = []

        if lista_modelos is None or not lista_modelos or "TODOS" in lista_modelos:
            lista_modelos_labels.append(dmc.Badge("Todos os modelos", variant="outline"))
        else:
            for modelo in lista_modelos:
                lista_modelos_labels.append(dmc.Badge(modelo, variant="dot"))

        if lista_oficinas is None or not lista_oficinas or "TODAS" in lista_oficinas:
            lista_oficinas_labels.append(dmc.Badge("Todas as oficinas", variant="outline"))
        else:
            for oficina in lista_oficinas:
                lista_oficinas_labels.append(dmc.Badge(oficina, variant="dot"))

        if not (lista_os is None or not lista_os):
            for os in lista_os:
                lista_os_labels.append(dmc.Badge(f"OS: {os}", variant="dot"))

        return [
            dmc.Group(
                labels_antes
                + datas_label
                + min_dias_label
                + lista_oficinas_labels
                + lista_modelos_labels
                + lista_os_labels
            )
        ]

    # Cria o componente
    return dmc.Group(id=f"{campo}-labels", children=[])


##############################################################################
# Callback para cálculo do estado ############################################
##############################################################################


@callback(
    Output("store-dados-tipo-servico", "data"),
    [
        Input("input-intervalo-datas-os", "value"),
        Input("input-select-dias-os-retrabalho", "value"),
        Input("input-select-modelo-veiculos-visao-tipo-servico", "value"),
        Input("input-select-oficina-visao-tipo-servico", "value"),
        Input("input-select-ordens-servico-visao-tipo-servico", "value"),
    ],
    running=[(Output("loading-overlay-guia-os", "visible"), True, False)],
)
def computa_retrabalho(datas, min_dias, lista_modelos, lista_oficinas, lista_os):
    dados_vazios = {
        "df_os": pd.DataFrame().to_dict("records"),
        "vazio": True,
    }

    # Valida input
    if not input_valido_tela_tipo_servico(datas, min_dias, lista_modelos, lista_oficinas, lista_os):
        return dados_vazios

    # Obtém dados das os
    df_os = tipo_servico_service.obtem_dados_os_sql(datas, min_dias, lista_modelos, lista_oficinas, lista_os)

    # Obtem os dados da LLM
    df_llm_raw = tipo_servico_service.obtem_dados_os_llm_sql(datas, min_dias, lista_modelos, lista_oficinas, lista_os)

    # Faz o merge
    df_os_llm = df_os.merge(df_llm_raw, on="KEY_HASH", how="left")

    # Obtem os dados de custo
    df_custo_raw = tipo_servico_service.obtem_dados_os_custo_sql(datas, min_dias, lista_modelos, lista_oficinas, lista_os)

    # Obtem os dados de custo agregados por OS
    df_custo_por_os_raw = df_custo_raw[["NUMERO DA OS", "VALOR"]].drop_duplicates()
    df_custo_por_os_agg = df_custo_por_os_raw.groupby("NUMERO DA OS")["VALOR"].sum().reset_index()

    # Faz o merge
    df_os_custo_agg = df_os.merge(df_custo_por_os_agg, on="NUMERO DA OS", how="left")

    # Obtem dados dos colaboradores
    df_colaborador = tipo_servico_service.obtem_dados_colaboradores_pandas(df_os, df_llm_raw, df_custo_por_os_agg)

    return {
        "df_os": df_os.to_dict("records"),
        "df_os_llm": df_os_llm.to_dict("records"),
        "df_custo_raw": df_custo_raw.to_dict("records"),
        "df_custo_por_os_agg": df_custo_por_os_agg.to_dict("records"),
        "df_os_custo_agg": df_os_custo_agg.to_dict("records"),
        "df_colaborador": df_colaborador.to_dict("records"),
        "vazio": df_os.empty,
    }


##############################################################################
# Callbacks para os gráficos #################################################
##############################################################################


# Callback para o grafico de síntese do retrabalho
@callback(Output("graph-pizza-sintese-retrabalho-os", "figure"), Input("store-dados-tipo-servico", "data"))
def plota_grafico_pizza_sintese_os(store_payload):
    if store_payload["vazio"]:
        return go.Figure()

    # Obtem os dados
    df_os_raw = pd.DataFrame(store_payload["df_os"])

    # Verifica se há dados
    if df_os_raw.empty:
        return go.Figure()

    # Remove duplicatas
    df = df_os_raw.drop_duplicates(subset=["NUMERO DA OS"])

    # Computa sintese
    estatistica_retrabalho = tipo_servico_service.get_sintese_os(df)

    # Prepara os dados para o gráfico
    labels = ["Correções de Primeira", "Correções Tardias", "Retrabalhos"]
    values = [
        estatistica_retrabalho["total_correcao_primeira"],
        estatistica_retrabalho["total_correcao_tardia"],
        estatistica_retrabalho["total_retrabalho"],
    ]

    # Gera o gráfico
    fig = tipo_servico_graficos.gerar_grafico_pizza_sinteze_os(df, labels, values)

    return fig


# Callback para o grafico cumulativo de retrabalho
@callback(Output("graph-retrabalho-cumulativo-os", "figure"), Input("store-dados-tipo-servico", "data"))
def plota_grafico_cumulativo_retrabalho_os(store_payload):
    if store_payload["vazio"]:
        return go.Figure()

    # Obtem os dados
    df_os_raw = pd.DataFrame(store_payload["df_os"])

    # Verifica se há dados
    if df_os_raw.empty:
        return go.Figure()

    # Computa os dados
    df_os_cumulativo = tipo_servico_service.get_tempo_cumulativo_para_retrabalho(df_os_raw)

    # Gera o gráfico
    fig = tipo_servico_graficos.gerar_grafico_cumulativo_os(df_os_cumulativo)

    return fig


@callback(Output("graph-retrabalho-por-modelo-perc-os", "figure"), Input("store-dados-tipo-servico", "data"))
def plota_grafico_retrabalho_por_modelo_perc_os(store_payload):
    if store_payload["vazio"]:
        return go.Figure()

    # Obtem os dados
    df_os_raw = pd.DataFrame(store_payload["df_os"])

    # Remove duplicatas
    df = df_os_raw.drop_duplicates(subset=["NUMERO DA OS"])

    # Estatística por modelo
    df_modelo = tipo_servico_service.get_retrabalho_por_modelo(df)

    # Gera o gráfico
    fig = tipo_servico_graficos.gerar_grafico_barras_retrabalho_por_modelo_perc(df_modelo)

    return fig


def plota_grafico_evolucao_retrabalho_por_oficina_por_mes_os(store_payload):
    if store_payload["vazio"]:
        return go.Figure()

    # Obtem os dados
    df_os_raw = pd.DataFrame(store_payload["df_os"])

    # Remove duplicatas
    df = df_os_raw.drop_duplicates(subset=["NUMERO DA OS"])

    # Adiciona a coluna de ano-mês
    df["year_month"] = pd.to_datetime(df["DATA DA ABERTURA DA OS"]).dt.strftime("%Y-%m")

    result = (
        df.groupby(["year_month", "DESCRICAO DA OFICINA"])
        .agg(
            PERC_RETRABALHO=("retrabalho", lambda x: 100 * round(x.sum() / len(x), 4)),
            PERC_CORRECAO_PRIMEIRA=("correcao_primeira", lambda x: 100 * round(x.sum() / len(x), 4)),
        )
        .reset_index()
    )

    # Estatística por oficina
    df_oficina = tipo_servico_service.get_retrabalho_por_oficina(df)

    # Gera o gráfico
    fig = tipo_servico_graficos.gerar_grafico_evolucao_retrabalho_por_oficina_por_mes(df_oficina)

    return fig


##############################################################################
# Callbacks para os indicadores ##############################################
##############################################################################


@callback(
    [
        Output("indicador-total-problemas", "children"),
        Output("indicador-total-os", "children"),
        Output("indicador-relacao-problema-os", "children"),
        Output("indicador-porcentagem-prob-com-retrabalho", "children"),
        Output("indicador-porcentagem-retrabalho", "children"),
        Output("indicador-num-medio-dias-correcao", "children"),
    ],
    Input("store-dados-tipo-servico", "data"),
)
def atualiza_indicadores_os_gerais(store_payload):
    if store_payload["vazio"]:
        return ["", "", "", "", "", ""]

    # Obtem os dados
    df_os_raw = pd.DataFrame(store_payload["df_os"])

    # Remove duplicatas
    df = df_os_raw.drop_duplicates(subset=["NUMERO DA OS"])

    # Remove NaNs e NaTs
    df = df[df["DATA DO FECHAMENTO DA OS"].notna()].copy()

    # Cálculo
    df_dias_para_correcao, df_num_os_por_problema, df_estatistica = tipo_servico_service.get_indicadores_gerais(df)

    # Valores
    total_de_problemas = int(df_estatistica["TOTAL_DE_PROBLEMAS"].values[0])
    total_de_os = int(df_estatistica["TOTAL_DE_OS"].values[0])
    rel_os_problemas = round(float(df_estatistica["RELACAO_OS_PROBLEMA"].values[0]), 2)

    num_problema_sem_retrabalho = int(len(df_num_os_por_problema[df_num_os_por_problema["TOTAL_DE_OS"] == 1]))
    perc_problema_com_retrabalho = round(100 * (1 - (num_problema_sem_retrabalho / total_de_problemas)), 2)

    num_retrabalho = int(df_estatistica["TOTAL_DE_RETRABALHOS"].values[0])
    perc_retrabalho = round(float(df_estatistica["PERC_RETRABALHO"].values[0]), 2)
    dias_ate_corrigir = round(float(df_dias_para_correcao["dias_correcao"].mean()), 2)
    num_os_ate_corrigir = round(float(df_num_os_por_problema["TOTAL_DE_OS"].mean()), 2)

    return [
        f"{total_de_problemas} problemas",
        f"{total_de_os} OS",
        f"{rel_os_problemas} OS/prob",
        f"{perc_problema_com_retrabalho}%",
        f"{perc_retrabalho}%",
        f"{dias_ate_corrigir} dias",
    ]


@callback(
    [
        Output("indicador-custo-total-os", "children"),
        Output("indicador-custo-retrabalho-os", "children"),
        Output("indicador-custo-percentagem-os", "children"),
    ],
    Input("store-dados-tipo-servico", "data"),
)
def atualiza_indicadores_os_custos(store_payload):
    if store_payload["vazio"]:
        return ["", "", ""]

    # Faz o merge
    df_os_custo_agg = pd.DataFrame(store_payload["df_os_custo_agg"])

    # Remove duplicatas
    df_os_custo_agg_distinct = df_os_custo_agg.drop_duplicates(subset=["NUMERO DA OS"])

    # OS que tem retrabalho
    df_os_custo_agg_distinct_retrabalho = df_os_custo_agg_distinct[df_os_custo_agg_distinct["retrabalho"] == True]

    # Indicadores
    custo_total = round(float(df_os_custo_agg_distinct["VALOR"].sum()), 2)
    custo_retrabalho = round(float(df_os_custo_agg_distinct_retrabalho["VALOR"].sum()), 2)
    perc_custo_retrabalho = round(100 * (custo_retrabalho / custo_total), 2)

    custo_total_str = "R$ " + formata_moeda(custo_total)
    custo_retrabalho_str = "R$ " + formata_moeda(custo_retrabalho)
    perc_custo_retrabalho_str = str(perc_custo_retrabalho) + "%"

    return [custo_total_str, custo_retrabalho_str, perc_custo_retrabalho_str]


@callback(
    [
        Output("indicador-media-os-colaborador", "children"),
        Output("indicador-media-porcentagem-retrabalho", "children"),
        Output("indicador-media-correcoes-primeira-colaborador", "children"),
        Output("indicador-media-correcoes-tardias-colaborador", "children"),
    ],
    Input("store-dados-tipo-servico", "data"),
)
def atualiza_indicadores_os_mecanico(store_payload):
    if store_payload["vazio"]:
        return ["", "", "", ""]

    # Obtem os dados
    df_os_raw = pd.DataFrame(store_payload["df_os"])

    # Obtem indicadores
    df_colaborador = tipo_servico_service.get_indicadores_colaboradores(df_os_raw)

    # Média de OS por mecânico
    media_os_por_mecanico = round(float(df_colaborador["TOTAL_DE_OS"].mean()), 2)

    # Retrabalhos médios
    media_retrabalhos_por_mecanico = round(float(df_colaborador["PERC_RETRABALHO"].mean()), 2)

    # Correções de Primeira
    media_correcoes_primeira = round(float(df_colaborador["PERC_CORRECOES_DE_PRIMEIRA"].mean()), 2)

    # Correções Tardias
    media_correcoes_tardias = round(float(df_colaborador["PERC_CORRECOES_TARDIA"].mean()), 2)

    return [
        f"{media_os_por_mecanico} OS / colaborador",
        f"{media_retrabalhos_por_mecanico}%",
        f"{media_correcoes_primeira}%",
        f"{media_correcoes_tardias}%",
    ]

##############################################################################
# Callbacks para as tabelas ##################################################
##############################################################################

@callback(
    Output("tabela-top-mecanicos", "rowData"),
    Input("store-dados-tipo-servico", "data"),
)
def update_tabela_mecanicos_retrabalho(store_payload):
    if store_payload["vazio"]:
        return []

    df_colaborador = pd.DataFrame(store_payload["df_colaborador"])

    # # Prepara o dataframe para a tabela
    # df_colaborador["REL_OS_PROB"] = round(
    #     df_colaborador["TOTAL_DE_OS"] / df_colaborador["NUM_PROBLEMAS"], 2
    # )
    # df_colaborador["PERC_RETRABALHO"] = df_colaborador["PERC_RETRABALHO"].round(2)
    # df_colaborador["PERC_CORRECOES"] = df_colaborador["PERC_CORRECOES"].round(2)
    # df_colaborador["PERC_CORRECOES_DE_PRIMEIRA"] = df_colaborador[
    #     "PERC_CORRECOES_DE_PRIMEIRA"
    # ].round(2)

    # Ordena por PERC_RETRABALHO
    df_colaborador = df_colaborador.sort_values(by="PERC_RETRABALHO", ascending=False)

    # Retorna tabela
    return df_colaborador.to_dict("records")

##############################################################################
# Layout #####################################################################
##############################################################################
layout = dbc.Container(
    [
        # Loading
        dmc.LoadingOverlay(
            visible=True,
            id="loading-overlay-guia-os",
            loaderProps={"size": "xl"},
            overlayProps={
                "radius": "lg",
                "blur": 2,
                "style": {
                    "top": 0,  # Start from the top of the viewport
                    "left": 0,  # Start from the left of the viewport
                    "width": "100vw",  # Cover the entire width of the viewport
                    "height": "100vh",  # Cover the entire height of the viewport
                },
            },
            zIndex=10,
        ),
        # Alerta
        dbc.Alert(
            [
                dbc.Row(
                    [
                        dbc.Col(DashIconify(icon="ooui:alert", width=45), width="auto"),
                        dbc.Col(
                            html.P(
                                """
                                As Ordens de Serviço serão analisadas em conjunto, ou seja, mesmo que seja OS de categoria diferente, 
                                as OSs serão consideradas como um único grupo para o cálculo de retrabalho.
                                """
                            ),
                            className="mt-2",
                            width=True,
                        ),
                    ],
                    align="center",
                ),
            ],
            dismissable=True,
            color="warning",
        ),
        # Cabeçalho
        dbc.Row(
            [
                dbc.Col(
                    [
                        # Cabeçalho e Inputs
                        dbc.Row(
                            [
                                html.Hr(),
                                dbc.Row(
                                    [
                                        dbc.Col(DashIconify(icon="ic:baseline-category", width=45), width="auto"),
                                        dbc.Col(
                                            html.H1(
                                                [
                                                    "Retrabalho por\u00a0",
                                                    html.Strong("tipo de serviço (OS)"),
                                                ],
                                                className="align-self-center",
                                            ),
                                            width=True,
                                        ),
                                    ],
                                    align="center",
                                ),
                                dmc.Space(h=15),
                                html.Hr(),
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            html.Div(
                                                [
                                                    dbc.Label("Data (intervalo) de análise"),
                                                    dmc.DatePicker(
                                                        id="input-intervalo-datas-os",
                                                        allowSingleDateInRange=True,
                                                        type="range",
                                                        minDate=date(2024, 8, 1),
                                                        maxDate=date.today(),
                                                        value=[date(2024, 8, 1), date.today()],
                                                    ),
                                                ],
                                                className="dash-bootstrap",
                                            ),
                                        ],
                                        body=True,
                                    ),
                                    md=6,
                                ),
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            html.Div(
                                                [
                                                    dbc.Label("Tempo (em dias) entre OS para retrabalho"),
                                                    dcc.Dropdown(
                                                        id="input-select-dias-os-retrabalho",
                                                        options=[
                                                            {"label": "10 dias", "value": 10},
                                                            {"label": "15 dias", "value": 15},
                                                            {"label": "30 dias", "value": 30},
                                                        ],
                                                        placeholder="Período em dias",
                                                        value=10,
                                                    ),
                                                ],
                                                className="dash-bootstrap",
                                            ),
                                        ],
                                        body=True,
                                    ),
                                    md=6,
                                ),
                                dmc.Space(h=10),
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            html.Div(
                                                [
                                                    dbc.Label("Modelos de Veículos"),
                                                    dcc.Dropdown(
                                                        id="input-select-modelo-veiculos-visao-tipo-servico",
                                                        options=[
                                                            {
                                                                "label": os["MODELO"],
                                                                "value": os["MODELO"],
                                                            }
                                                            for os in lista_todos_modelos_veiculos
                                                        ],
                                                        multi=True,
                                                        value=["TODOS"],
                                                        placeholder="Selecione uma ou mais ordens de serviço...",
                                                    ),
                                                ],
                                                className="dash-bootstrap",
                                            ),
                                        ],
                                        body=True,
                                    ),
                                    md=12,
                                ),
                                dmc.Space(h=10),
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            html.Div(
                                                [
                                                    dbc.Label("Oficinas"),
                                                    dcc.Dropdown(
                                                        id="input-select-oficina-visao-tipo-servico",
                                                        options=[
                                                            {"label": os["LABEL"], "value": os["LABEL"]}
                                                            for os in lista_todas_oficinas
                                                        ],
                                                        multi=True,
                                                        value=["TODAS"],
                                                        placeholder="Selecione uma ou mais oficinas...",
                                                    ),
                                                ],
                                                className="dash-bootstrap",
                                            ),
                                        ],
                                        body=True,
                                    ),
                                    md=12,
                                ),
                                dmc.Space(h=10),
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            html.Div(
                                                [
                                                    dbc.Label("Ordens de Serviço"),
                                                    dcc.Dropdown(
                                                        id="input-select-ordens-servico-visao-tipo-servico",
                                                        options=[
                                                            {"label": os["LABEL"], "value": os["LABEL"]}
                                                            for os in lista_todas_os
                                                        ],
                                                        multi=True,
                                                        value=[],
                                                        placeholder="Selecione uma ou mais ordens de serviço...",
                                                    ),
                                                ],
                                                className="dash-bootstrap",
                                            ),
                                        ],
                                        body=True,
                                    ),
                                    md=12,
                                ),
                                dmc.Space(h=10),
                            ]
                        ),
                    ],
                    md=8,
                ),
                dbc.Col(
                    # Resumo
                    dbc.Row(
                        [
                            dbc.Row(
                                [
                                    # Cabeçalho
                                    html.Hr(),
                                    dbc.Col(
                                        DashIconify(icon="wpf:statistics", width=45),
                                        width="auto",
                                    ),
                                    dbc.Col(html.H1("Resumo", className="align-self-center"), width=True),
                                    dmc.Space(h=15),
                                    html.Hr(),
                                ],
                                align="center",
                            ),
                            dcc.Graph(id="graph-pizza-sintese-retrabalho-os"),
                        ]
                    ),
                    md=4,
                ),
            ]
        ),
        # Estado
        dcc.Store(id="store-dados-tipo-servico"),
        # Indicadores
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="icon-park-outline:ranking-list", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Indicadores",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            gera_labels_inputs("labels-indicadores-pag-os"),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        dmc.Space(h=20),
        dbc.Row(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        dmc.Group(
                                            [
                                                dmc.Title(
                                                    id="indicador-total-problemas",
                                                    order=2,
                                                ),
                                                DashIconify(
                                                    icon="mdi:bomb",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("Total de problemas"),
                                ],
                                class_name="card-box",
                            ),
                            md=4,
                        ),
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        dmc.Group(
                                            [
                                                dmc.Title(
                                                    id="indicador-total-os",
                                                    order=2,
                                                ),
                                                DashIconify(
                                                    icon="material-symbols:order-play-outline",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("Total de OS"),
                                ],
                                class_name="card-box",
                            ),
                            md=4,
                        ),
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        dmc.Group(
                                            [
                                                dmc.Title(
                                                    id="indicador-relacao-problema-os",
                                                    order=2,
                                                ),
                                                DashIconify(
                                                    icon="icon-park-solid:division",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("Média de OS / problema"),
                                ],
                                class_name="card-box",
                            ),
                            md=4,
                        ),
                    ]
                ),
                dbc.Row(dmc.Space(h=20)),
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        dmc.Group(
                                            [
                                                dmc.Title(
                                                    id="indicador-porcentagem-prob-com-retrabalho",
                                                    order=2,
                                                ),
                                                DashIconify(
                                                    icon="game-icons:time-bomb",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("% de problemas com retrabalho (> 1 OS)"),
                                ],
                                class_name="card-box",
                            ),
                            md=4,
                        ),
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        dmc.Group(
                                            [
                                                dmc.Title(
                                                    id="indicador-porcentagem-retrabalho",
                                                    order=2,
                                                ),
                                                DashIconify(
                                                    icon="tabler:reorder",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("% das OS são retrabalho"),
                                ],
                                class_name="card-box",
                            ),
                            md=4,
                        ),
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        dmc.Group(
                                            [
                                                dmc.Title(
                                                    id="indicador-num-medio-dias-correcao",
                                                    order=2,
                                                ),
                                                DashIconify(
                                                    icon="lucide:calendar-days",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("Média de dias até correção"),
                                ],
                                class_name="card-box",
                            ),
                            md=4,
                        ),
                    ]
                ),
                dbc.Row(dmc.Space(h=20)),
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        dmc.Group(
                                            [
                                                dmc.Title(
                                                    id="indicador-custo-total-os",
                                                    order=2,
                                                ),
                                                DashIconify(
                                                    icon="hugeicons:search-dollar",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("Total gasto com peças"),
                                ],
                                class_name="card-box",
                            ),
                            md=4,
                        ),
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        dmc.Group(
                                            [
                                                dmc.Title(
                                                    id="indicador-custo-retrabalho-os",
                                                    order=2,
                                                ),
                                                DashIconify(
                                                    icon="emojione-monotone:money-with-wings",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("Total gasto com retrabalho"),
                                ],
                                class_name="card-box",
                            ),
                            md=4,
                        ),
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        dmc.Group(
                                            [
                                                dmc.Title(
                                                    id="indicador-custo-percentagem-os",
                                                    order=2,
                                                ),
                                                DashIconify(
                                                    icon="icon-park-solid:division",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("% do custo em retrabalho"),
                                ],
                                class_name="card-box",
                            ),
                            md=4,
                        ),
                    ]
                ),
            ]
        ),
        dmc.Space(h=10),
        html.Hr(),
        # Gráficos
        # Gráfico cumulativo
        dmc.Space(h=30),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="mdi:chart-bell-curve-cumulative", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Gráfico cumulativo de dias para solução do problema",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            gera_labels_inputs("labels-grafico-cumulativo-pag-os"),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        dcc.Graph(id="graph-retrabalho-cumulativo-os"),
        dmc.Space(h=40),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="mdi:fleet", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Retrabalho por modelo (%)",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            gera_labels_inputs("labels-retrabalho-modelo-pag-os"),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        dcc.Graph(id="graph-retrabalho-por-modelo-perc-os"),
        dmc.Space(h=20),
        # Top Colaboradores Retrabalho
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="mdi:mechanic", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Ranking de colaboradores por retrabalho",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            gera_labels_inputs("labels-retrabalho-colaboradores-pag-os"),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                dmc.Group(
                                    [
                                        dmc.Title(id="indicador-media-os-colaborador", order=2),
                                        DashIconify(
                                            icon="bxs:car-mechanic",
                                            width=48,
                                            color="black",
                                        ),
                                    ],
                                    justify="space-around",
                                    mt="md",
                                    mb="xs",
                                ),
                            ),
                            dbc.CardFooter("Média de OS / Colaborador"),
                        ],
                    ),
                    md=6,
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                dmc.Group(
                                    [
                                        dmc.Title(
                                            id="indicador-media-porcentagem-retrabalho",
                                            order=2,
                                        ),
                                        DashIconify(
                                            icon="pepicons-pop:rewind-time",
                                            width=48,
                                            color="black",
                                        ),
                                    ],
                                    justify="space-around",
                                    mt="md",
                                    mb="xs",
                                ),
                            ),
                            dbc.CardFooter("Média da % de retrabalho dos colaboradores"),
                        ],
                    ),
                    md=6,
                ),
            ]
        ),
        dbc.Row(dmc.Space(h=20)),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                dmc.Group(
                                    [
                                        dmc.Title(
                                            id="indicador-media-correcoes-primeira-colaborador",
                                            order=2,
                                        ),
                                        DashIconify(
                                            icon="gravity-ui:target-dart",
                                            width=48,
                                            color="black",
                                        ),
                                    ],
                                    justify="space-around",
                                    mt="md",
                                    mb="xs",
                                ),
                            ),
                            dbc.CardFooter("Média da % de correções de primeira dos colaboradores"),
                        ],
                    ),
                    md=6,
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                dmc.Group(
                                    [
                                        dmc.Title(
                                            id="indicador-media-correcoes-tardias-colaborador",
                                            order=2,
                                        ),
                                        DashIconify(
                                            icon="game-icons:multiple-targets",
                                            width=48,
                                            color="black",
                                        ),
                                    ],
                                    justify="space-around",
                                    mt="md",
                                    mb="xs",
                                ),
                            ),
                            dbc.CardFooter("Média da % de correções tardias dos colaboradores"),
                        ],
                    ),
                    md=6,
                ),
            ]
        ),
        dbc.Row(dmc.Space(h=20)),
        dbc.Row(
            [
                dag.AgGrid(
                    id="tabela-top-mecanicos",
                    columnDefs=tipo_servico_tabelas.tbl_top_mecanicos,
                    rowData=[],
                    defaultColDef={"filter": True, "floatingFilter": True},
                    columnSize="autoSize",
                    dashGridOptions={
                        "localeText": locale_utils.AG_GRID_LOCALE_BR,
                    },
                    # Permite resize --> https://community.plotly.com/t/anyone-have-better-ag-grid-resizing-scheme/78398/5
                    style={"height": 400, "resize": "vertical", "overflow": "hidden"},
                ),
            ]
        ),
    ]
)

##############################################################################
# Registro da página #########################################################
##############################################################################
dash.register_page(__name__, name="Tipo de Serviço", path="/retrabalho-por-servico", icon="ic:baseline-category", hide_page=True)


# #!/usr/bin/env python
# # coding: utf-8

# # Dashboard que lista o retrabalho de uma ou mais OS

# ##############################################################################
# # IMPORTS ####################################################################
# ##############################################################################
# # Bibliotecas básicas
# from datetime import date
# import pandas as pd

# # Importar bibliotecas do dash básicas e plotly
# import dash
# from dash import Dash, html, dcc, callback, Input, Output, State
# import plotly.express as px
# import plotly.graph_objects as go

# # Importar bibliotecas do bootstrap e ag-grid
# import dash_bootstrap_components as dbc
# import dash_ag_grid as dag

# # Dash componentes Mantine e icones
# import dash_mantine_components as dmc
# from dash_iconify import DashIconify

# # Importar nossas constantes e funções utilitárias
# import tema
# import locale_utils

# # Banco de Dados
# from db import PostgresSingleton

# # Imports gerais
# from modules.entities_utils import (
#     get_mecanicos,
#     get_lista_os,
#     get_oficinas,
#     get_secoes,
#     get_modelos,
# )

# # Imports específicos

# ##############################################################################
# # LEITURA DE DADOS ###########################################################
# ##############################################################################
# # Conexão com os bancos
# pgDB = PostgresSingleton.get_instance()
# pgEngine = pgDB.get_engine()

# # Obtem a lista de Oficinas
# df_oficinas = get_oficinas(pgEngine)
# lista_todas_oficinas = df_oficinas.to_dict(orient="records")
# lista_todas_oficinas.insert(0, {"LABEL": "TODAS"})

# # Obtem a lista de Seções
# df_secoes = get_secoes(pgEngine)
# lista_todas_secoes = df_secoes.to_dict(orient="records")
# lista_todas_secoes.insert(0, {"LABEL": "TODAS"})

# # Colaboradores / Mecânicos
# df_mecanicos = get_mecanicos(pgEngine)

# # Modelos de veículos
# df_modelos_veiculos = get_modelos(pgEngine)
# lista_todos_modelos_veiculos = df_modelos_veiculos.to_dict(orient="records")
# lista_todos_modelos_veiculos.insert(0, {"MODELO": "TODAS"})

# # Obtem a lista de OS
# df_lista_os = get_lista_os(pgEngine)
# lista_todas_os = df_lista_os.to_dict(orient="records")
# lista_todas_os.insert(0, {"LABEL": "TODAS"})


# # Conexão com os bancos
# pgDB = PostgresSingleton.get_instance()
# pgEngine = pgDB.get_engine()

# # Obtem o quantitativo de OS por categoria
# df_os_categorias_pg = pd.read_sql(
#     """
#     SELECT DISTINCT
#        "DESCRICAO DA SECAO" as "SECAO",
#        "DESCRICAO DO SERVICO" AS "LABEL"
#     FROM
#         mat_view_retrabalho_10_dias mvrd
#     ORDER BY
#         "DESCRICAO DO SERVICO"

#     """,
#     pgEngine,
# )

# # Colaboradores / Mecânicos
# df_mecanicos = pd.read_sql("SELECT * FROM colaboradores_frotas_os", pgEngine)

# # Definir colunas das tabelas de detalhamento

# # Tabela Mecânicos
# tbl_top_mecanicos = [
#     {
#         "field": "LABEL_COLABORADOR",
#         "headerName": "COLABORADOR",
#         "pinned": "left",
#         "minWidth": 200,
#     },
#     {"field": "NUM_PROBLEMAS", "headerName": "# PROBLEMAS"},
#     {"field": "TOTAL_DE_OS", "headerName": "# OS"},
#     {"field": "RETRABALHOS", "headerName": "# RETRABALHOS"},
#     {"field": "CORRECOES", "headerName": "# CORREÇÕES"},
#     {
#         "field": "CORRECOES_DE_PRIMEIRA",
#         "headerName": "# CORREÇÕES DE PRIMEIRA",
#         "maxWidth": 150,
#     },
#     {
#         "field": "PERC_RETRABALHO",
#         "headerName": "% RETRABALHOS",
#         "valueFormatter": {"function": "params.value + '%'"},
#         "type": ["numericColumn"],
#     },
#     {
#         "field": "PERC_CORRECOES",
#         "headerName": "% CORREÇÕES",
#         "valueFormatter": {"function": "params.value + '%'"},
#         "type": ["numericColumn"],
#     },
#     {
#         "field": "PERC_CORRECOES_DE_PRIMEIRA",
#         "headerName": "% CORREÇÕES DE PRIMEIRA",
#         "valueFormatter": {"function": "params.value + '%'"},
#         "type": ["numericColumn"],
#         "maxWidth": 150,
#     },
# ]

# # Tabela veículos mais problemáticos
# tbl_top_veiculos_problematicos = [
#     {"field": "CODIGO DO VEICULO", "headerName": "VEÍCULO", "maxWidth": 150},
#     {"field": "TOTAL_DE_PROBLEMAS", "headerName": "# PROBLEMAS"},
#     {"field": "TOTAL_DE_OS", "headerName": "# OS"},
#     {
#         "field": "TOTAL_DIAS_ATE_CORRIGIR",
#         "headerName": "TOTAL DE DIAS GASTOS ATÉ CORRIGIR",
#     },
#     {"field": "REL_PROBLEMA_OS", "headerName": "REL. PROB/OS"},
# ]


# # Tabela OS
# tbl_top_os = [
#     {"field": "DIA", "headerName:": "DIA"},
#     {"field": "NUMERO DA OS", "headerName": "OS"},
#     {"field": "CODIGO DO VEICULO", "headerName": "VEÍCULO"},
#     {"field": "DESCRICAO DO VEICULO", "headerName": "MODELO"},
#     {"field": "DIAS_ATE_OS_CORRIGIR", "headerName": "DIAS ATÉ ESSA OS"},
# ]

# # Tabel Veículos
# tbl_top_vec = [
#     {"field": "CODIGO DO VEICULO", "headerName": "VEÍCULO", "maxWidth": 150},
#     {
#         "field": "TOTAL_DIAS_ATE_CORRIGIR",
#         "headerName": "TOTAL DE DIAS GASTOS ATÉ CORRIGIR",
#     },
# ]

# # Detalhes das OSs
# # df_os_problematicas
# tbl_detalhes_vec_os = [
#     {"field": "problem_no", "headerName": "PROB", "maxWidth": 150},
#     {"field": "NUMERO DA OS", "headerName": "OS", "maxWidth": 150},
#     {"field": "DESCRICAO DO SERVICO", "headerName": "SERVIÇO", "minWidth": 200},
#     {"field": "CLASSIFICACAO_EMOJI", "headerName": "STATUS", "maxWidth": 150},
#     {"field": "LABEL_COLABORADOR", "headerName": "COLABORADOR"},
#     {"field": "DIA_INICIO", "headerName": "INÍCIO", "minWidth": 150},
#     {"field": "DIA_TERMINO", "headerName": "FECHAMENTO", "minWidth": 150},
#     {"field": "DIAS_ENTRE_OS", "headerName": "DIFF DIAS COM ANT", "maxWidth": 120},
#     {"field": "TOTAL_DE_OS", "headerName": "NUM OS ATÉ CORRIGIR", "maxWidth": 150},
#     {
#         "field": "COMPLEMENTO DO SERVICO",
#         "headerName": "DESCRIÇÃO",
#         "minWidth": 800,
#         "wrapText": True,
#         "autoHeight": True,
#     },
# ]

# ##############################################################################
# # Registro da página #########################################################
# ##############################################################################
# dash.register_page(
#     __name__,
#     name="Retrabalho por OS",
#     path="/retrabalho-por-os",
#     icon="fluent-mdl2:timeline",
# )

# ##############################################################################
# layout = dbc.Container(
#     [
#         # Loading
#         dmc.LoadingOverlay(
#             visible=True,
#             id="loading-overlay",
#             loaderProps={"size": "xl"},
#             overlayProps={
#                 "radius": "lg",
#                 "blur": 2,
#                 "style": {
#                     "top": 0,  # Start from the top of the viewport
#                     "left": 0,  # Start from the left of the viewport
#                     "width": "100vw",  # Cover the entire width of the viewport
#                     "height": "100vh",  # Cover the entire height of the viewport
#                 },
#             },
#             zIndex=10,
#         ),
#         # Cabeçalho
#         dbc.Row(
#             [
#                 dbc.Col(
#                     [
#                         # Cabeçalho e Inputs
#                         dbc.Row(
#                             [
#                                 html.Hr(),
#                                 dbc.Row(
#                                     [
#                                         dbc.Col(
#                                             DashIconify(
#                                                 icon="vaadin:lines-list", width=45
#                                             ),
#                                             width="auto",
#                                         ),
#                                         dbc.Col(
#                                             html.H1(
#                                                 [
#                                                     "Retrabalho por\u00a0",
#                                                     html.Strong("tipo de serviço (OS)"),
#                                                 ],
#                                                 className="align-self-center",
#                                             ),
#                                             width=True,
#                                         ),
#                                     ],
#                                     align="center",
#                                 ),
#                                 dmc.Space(h=15),
#                                 html.Hr(),
#                                 dbc.Col(
#                                     dbc.Card(
#                                         [
#                                             html.Div(
#                                                 [
#                                                     dbc.Label(
#                                                         "Data (intervalo) de análise"
#                                                     ),
#                                                     dmc.DatePicker(
#                                                         id="input-intervalo-datas-os",
#                                                         allowSingleDateInRange=True,
#                                                         type="range",
#                                                         minDate=date(2024, 8, 1),
#                                                         maxDate=date.today(),
#                                                         value=[
#                                                             date(2024, 8, 1),
#                                                             date.today(),
#                                                         ],
#                                                     ),
#                                                 ],
#                                                 className="dash-bootstrap",
#                                             ),
#                                         ],
#                                         body=True,
#                                     ),
#                                     md=6,
#                                 ),
#                                 dbc.Col(
#                                     dbc.Card(
#                                         [
#                                             html.Div(
#                                                 [
#                                                     dbc.Label(
#                                                         "Tempo (em dias) entre OS para retrabalho"
#                                                     ),
#                                                     dcc.Dropdown(
#                                                         id="input-select-dias-os-retrabalho",
#                                                         options=[
#                                                             {
#                                                                 "label": "10 dias",
#                                                                 "value": 10,
#                                                             },
#                                                             {
#                                                                 "label": "15 dias",
#                                                                 "value": 15,
#                                                             },
#                                                             {
#                                                                 "label": "30 dias",
#                                                                 "value": 30,
#                                                             },
#                                                         ],
#                                                         placeholder="Período em dias",
#                                                         value=10,
#                                                     ),
#                                                 ],
#                                                 className="dash-bootstrap",
#                                             ),
#                                         ],
#                                         body=True,
#                                     ),
#                                     md=6,
#                                 ),
#                                 dmc.Space(h=10),
#                                 dbc.Col(
#                                     dbc.Card(
#                                         [
#                                             html.Div(
#                                                 [
#                                                     dbc.Label("Oficinas"),
#                                                     dcc.Dropdown(
#                                                         id="input-select-oficina-os",
#                                                         options=[
#                                                             # {"label": os["LABEL"], "value": os["LABEL"]}
#                                                             # for os in lista_todas_oficinas
#                                                         ],
#                                                         multi=True,
#                                                         value=["TODAS"],
#                                                         placeholder="Selecione uma ou mais oficinas...",
#                                                     ),
#                                                 ],
#                                                 className="dash-bootstrap",
#                                             ),
#                                         ],
#                                         body=True,
#                                     ),
#                                     md=6,
#                                 ),
#                                 dbc.Col(
#                                     dbc.Card(
#                                         [
#                                             html.Div(
#                                                 [
#                                                     dbc.Label(
#                                                         "Seções (categorias) de manutenção"
#                                                     ),
#                                                     dcc.Dropdown(
#                                                         id="input-select-secao-os",
#                                                         options=[
#                                                             # {"label": "TODAS", "value": "TODAS"},
#                                                             # {
#                                                             #     "label": "BORRACHARIA",
#                                                             #     "value": "MANUTENCAO BORRACHARIA",
#                                                             # },
#                                                             {
#                                                                 "label": "ELETRICA",
#                                                                 "value": "MANUTENCAO ELETRICA",
#                                                             },
#                                                             # {"label": "GARAGEM", "value": "MANUTENÇÃO GARAGEM"},
#                                                             # {
#                                                             #     "label": "LANTERNAGEM",
#                                                             #     "value": "MANUTENCAO LANTERNAGEM",
#                                                             # },
#                                                             # {"label": "LUBRIFICAÇÃO", "value": "LUBRIFICAÇÃO"},
#                                                             {
#                                                                 "label": "MECANICA",
#                                                                 "value": "MANUTENCAO MECANICA",
#                                                             },
#                                                             # {"label": "PINTURA", "value": "MANUTENCAO PINTURA"},
#                                                             # {
#                                                             #     "label": "SERVIÇOS DE TERCEIROS",
#                                                             #     "value": "SERVIÇOS DE TERCEIROS",
#                                                             # },
#                                                             # {
#                                                             #     "label": "SETOR DE ALINHAMENTO",
#                                                             #     "value": "SETOR DE ALINHAMENTO",
#                                                             # },
#                                                             # {
#                                                             #     "label": "SETOR DE POLIMENTO",
#                                                             #     "value": "SETOR DE POLIMENTO",
#                                                             # },
#                                                         ],
#                                                         multi=True,
#                                                         value=[
#                                                             "MANUTENCAO ELETRICA",
#                                                             "MANUTENCAO MECANICA",
#                                                         ],
#                                                         placeholder="Selecione uma ou mais seções...",
#                                                     ),
#                                                 ],
#                                                 className="dash-bootstrap",
#                                             ),
#                                         ],
#                                         body=True,
#                                     ),
#                                     md=6,
#                                 ),
#                                 dmc.Space(h=10),
#                                 dbc.Col(
#                                     dbc.Card(
#                                         [
#                                             html.Div(
#                                                 [
#                                                     dbc.Label("Modelos de Veículos"),
#                                                     dcc.Dropdown(
#                                                         id="input-select-modelo-veiculos-visao-tipo-servico",
#                                                         options=[
#                                                             {
#                                                                 "label": os["MODELO"],
#                                                                 "value": os["MODELO"],
#                                                             }
#                                                             for os in lista_todos_modelos_veiculos
#                                                         ],
#                                                         multi=True,
#                                                         value=["TODAS"],
#                                                         placeholder="Selecione uma ou mais ordens de serviço...",
#                                                     ),
#                                                 ],
#                                                 className="dash-bootstrap",
#                                             ),
#                                         ],
#                                         body=True,
#                                     ),
#                                     md=12,
#                                 ),
#                                 dmc.Space(h=10),
#                                 dbc.Col(
#                                     dbc.Card(
#                                         [
#                                             html.Div(
#                                                 [
#                                                     dbc.Label("Ordens de Serviço"),
#                                                     dcc.Dropdown(
#                                                         id="input-select-ordens-servico-visao-tipo-servico",
#                                                         options=[
#                                                             {
#                                                                 "label": os["LABEL"],
#                                                                 "value": os["LABEL"],
#                                                             }
#                                                             for os in lista_todas_os
#                                                         ],
#                                                         multi=True,
#                                                         value=["TODAS"],
#                                                         placeholder="Selecione uma ou mais ordens de serviço...",
#                                                     ),
#                                                 ],
#                                                 className="dash-bootstrap",
#                                             ),
#                                         ],
#                                         body=True,
#                                     ),
#                                     md=12,
#                                 ),
#                             ]
#                         ),
#                     ],
#                     md=8,
#                 ),
#                 dbc.Col(
#                     # Resumo
#                     dbc.Row(
#                         [
#                             dbc.Row(
#                                 [
#                                     # Cabeçalho
#                                     html.Hr(),
#                                     dbc.Col(
#                                         DashIconify(icon="wpf:statistics", width=45),
#                                         width="auto",
#                                     ),
#                                     dbc.Col(
#                                         html.H1(
#                                             "Resumo", className="align-self-center"
#                                         ),
#                                         width=True,
#                                     ),
#                                     dmc.Space(h=15),
#                                     html.Hr(),
#                                 ],
#                                 align="center",
#                             ),
#                             dcc.Graph(id="graph-pizza-sintese-retrabalho-geral"),
#                         ]
#                     ),
#                     md=4,
#                 ),
#             ]
#         ),
#         html.Hr(),
#         # Filtros
#         dbc.Row(
#             [
#                 dbc.Col(
#                     dbc.Card(
#                         [
#                             html.Div(
#                                 [
#                                     dbc.Label("Ordem de Serviço:"),
#                                     dcc.Dropdown(
#                                         id="input-lista-os",
#                                         options=[
#                                             {
#                                                 "label": f"{linha['SECAO']} ({linha['LABEL']})",
#                                                 "value": linha["LABEL"],
#                                             }
#                                             for ix, linha in df_os_categorias_pg.iterrows()
#                                         ],
#                                         multi=True,
#                                         placeholder="Selecione uma ou mais OS",
#                                     ),
#                                 ],
#                                 className="dash-bootstrap",
#                             ),
#                         ],
#                         body=True,
#                     ),
#                     md=12,
#                 ),
#             ],
#         ),
#         dbc.Row(dmc.Space(h=20)),
#         dbc.Row(
#             [
#                 dbc.Col(
#                     dbc.Card(
#                         [
#                             html.Div(
#                                 [
#                                     dbc.Label("Data (Intervalo)"),
#                                     dmc.DatePicker(
#                                         id="input-intervalo-datas",
#                                         allowSingleDateInRange=True,
#                                         type="range",
#                                         minDate=date(2024, 8, 1),
#                                         maxDate=date.today(),
#                                         value=[date(2024, 8, 1), date.today()],
#                                     ),
#                                 ],
#                                 className="dash-bootstrap",
#                             ),
#                         ],
#                         body=True,
#                     ),
#                     md=6,
#                 ),
#                 dbc.Col(
#                     dbc.Card(
#                         [
#                             html.Div(
#                                 [
#                                     dbc.Label("Min. dias para Retrabalho"),
#                                     dmc.NumberInput(
#                                         id="input-dias", value=30, min=1, step=1
#                                     ),
#                                 ],
#                                 className="dash-bootstrap",
#                             ),
#                         ],
#                         body=True,
#                     ),
#                     md=6,
#                 ),
#             ]
#         ),
#         # Estado
#         dcc.Store(id="store-dados-tipo-servico"),
#         # Inicio dos gráficos
#         dbc.Row(dmc.Space(h=20)),
#         # Graficos gerais
#         html.Hr(),
#         # Indicadores
#         dbc.Row(
#             [
#                 html.H4("Indicadores"),
#                 dbc.Row(
#                     [
#                         dbc.Col(
#                             dbc.Card(
#                                 [
#                                     dbc.CardBody(
#                                         dmc.Group(
#                                             [
#                                                 dmc.Title(
#                                                     id="indicador-total-problemas",
#                                                     order=2,
#                                                 ),
#                                                 DashIconify(
#                                                     icon="mdi:bomb",
#                                                     width=48,
#                                                     color="black",
#                                                 ),
#                                             ],
#                                             justify="space-around",
#                                             mt="md",
#                                             mb="xs",
#                                         ),
#                                     ),
#                                     dbc.CardFooter("Total de problemas"),
#                                 ],
#                                 class_name="card-box",
#                             ),
#                             md=4,
#                         ),
#                         dbc.Col(
#                             dbc.Card(
#                                 [
#                                     dbc.CardBody(
#                                         dmc.Group(
#                                             [
#                                                 dmc.Title(
#                                                     id="indicador-total-os",
#                                                     order=2,
#                                                 ),
#                                                 DashIconify(
#                                                     icon="material-symbols:order-play-outline",
#                                                     width=48,
#                                                     color="black",
#                                                 ),
#                                             ],
#                                             justify="space-around",
#                                             mt="md",
#                                             mb="xs",
#                                         ),
#                                     ),
#                                     dbc.CardFooter("Total de OS"),
#                                 ],
#                                 class_name="card-box",
#                             ),
#                             md=4,
#                         ),
#                         dbc.Col(
#                             dbc.Card(
#                                 [
#                                     dbc.CardBody(
#                                         dmc.Group(
#                                             [
#                                                 dmc.Title(
#                                                     id="indicador-relacao-problema-os",
#                                                     order=2,
#                                                 ),
#                                                 DashIconify(
#                                                     icon="icon-park-solid:division",
#                                                     width=48,
#                                                     color="black",
#                                                 ),
#                                             ],
#                                             justify="space-around",
#                                             mt="md",
#                                             mb="xs",
#                                         ),
#                                     ),
#                                     dbc.CardFooter("Média de OS / problema"),
#                                 ],
#                                 class_name="card-box",
#                             ),
#                             md=4,
#                         ),
#                     ]
#                 ),
#                 dbc.Row(dmc.Space(h=20)),
#                 dbc.Row(
#                     [
#                         dbc.Col(
#                             dbc.Card(
#                                 [
#                                     dbc.CardBody(
#                                         dmc.Group(
#                                             [
#                                                 dmc.Title(
#                                                     id="indicador-porcentagem-prob-com-retrabalho",
#                                                     order=2,
#                                                 ),
#                                                 DashIconify(
#                                                     icon="game-icons:time-bomb",
#                                                     width=48,
#                                                     color="black",
#                                                 ),
#                                             ],
#                                             justify="space-around",
#                                             mt="md",
#                                             mb="xs",
#                                         ),
#                                     ),
#                                     dbc.CardFooter(
#                                         "% de problemas com retrabalho (> 1 OS)"
#                                     ),
#                                 ],
#                                 class_name="card-box",
#                             ),
#                             md=4,
#                         ),
#                         dbc.Col(
#                             dbc.Card(
#                                 [
#                                     dbc.CardBody(
#                                         dmc.Group(
#                                             [
#                                                 dmc.Title(
#                                                     id="indicador-porcentagem-retrabalho",
#                                                     order=2,
#                                                 ),
#                                                 DashIconify(
#                                                     icon="tabler:reorder",
#                                                     width=48,
#                                                     color="black",
#                                                 ),
#                                             ],
#                                             justify="space-around",
#                                             mt="md",
#                                             mb="xs",
#                                         ),
#                                     ),
#                                     dbc.CardFooter("% das OS são retrabalho"),
#                                 ],
#                                 class_name="card-box",
#                             ),
#                             md=4,
#                         ),
#                         dbc.Col(
#                             dbc.Card(
#                                 [
#                                     dbc.CardBody(
#                                         dmc.Group(
#                                             [
#                                                 dmc.Title(
#                                                     id="indicador-num-medio-dias-correcao",
#                                                     order=2,
#                                                 ),
#                                                 DashIconify(
#                                                     icon="lucide:calendar-days",
#                                                     width=48,
#                                                     color="black",
#                                                 ),
#                                             ],
#                                             justify="space-around",
#                                             mt="md",
#                                             mb="xs",
#                                         ),
#                                     ),
#                                     dbc.CardFooter("Média de dias até correção"),
#                                 ],
#                                 class_name="card-box",
#                             ),
#                             md=4,
#                         ),
#                     ]
#                 ),
#             ]
#         ),
#         dbc.Row(dmc.Space(h=40)),
#         # Gráfico de Pizza com a relação entre Retrabalho e Correções
#         dbc.Row(
#             [
#                 html.H4("Total de OS: Correções x Retrabalho"),
#                 dcc.Graph(id="graph-retrabalho-correcoes"),
#             ]
#         ),
#         # dbc.Row(dmc.Space(h=20)),
#         dbc.Row(
#             [
#                 html.H4("Grafículo Cumulativo Dias para Correção"),
#                 dcc.Graph(id="graph-retrabalho-cumulativo"),
#             ]
#         ),
#         # dbc.Row(dmc.Space(h=20)),
#         dbc.Row(
#             [
#                 html.H4("Retrabalho por Modelo (%)"),
#                 dcc.Graph(id="graph-retrabalho-por-modelo-perc"),
#             ]
#         ),
#         # Top Colaboradores Retrabalho
#         html.Hr(),
#         dbc.Row(
#             [
#                 dbc.Col(DashIconify(icon="mdi:mechanic", width=45), width="auto"),
#                 dbc.Col(
#                     html.H3(
#                         "Ranking de Colaboradores por Retrabalho",
#                         className="align-self-center",
#                     ),
#                     width=True,
#                 ),
#             ],
#             align="center",
#         ),
#         html.Hr(),
#         dbc.Row(
#             [
#                 dbc.Col(
#                     dbc.Card(
#                         [
#                             dbc.CardBody(
#                                 dmc.Group(
#                                     [
#                                         dmc.Title(
#                                             id="indicador-media-os-colaborador", order=2
#                                         ),
#                                         DashIconify(
#                                             icon="bxs:car-mechanic",
#                                             width=48,
#                                             color="black",
#                                         ),
#                                     ],
#                                     justify="space-around",
#                                     mt="md",
#                                     mb="xs",
#                                 ),
#                             ),
#                             dbc.CardFooter("Média de OS / Colaborador"),
#                         ],
#                         class_name="card-box-shadow",
#                     ),
#                     md=6,
#                 ),
#                 dbc.Col(
#                     dbc.Card(
#                         [
#                             dbc.CardBody(
#                                 dmc.Group(
#                                     [
#                                         dmc.Title(
#                                             id="indicador-media-porcentagem-retrabalho",
#                                             order=2,
#                                         ),
#                                         DashIconify(
#                                             icon="pepicons-pop:rewind-time",
#                                             width=48,
#                                             color="black",
#                                         ),
#                                     ],
#                                     justify="space-around",
#                                     mt="md",
#                                     mb="xs",
#                                 ),
#                             ),
#                             dbc.CardFooter(
#                                 "Média da % de retrabalho dos colaboradores"
#                             ),
#                         ],
#                         class_name="card-box-shadow",
#                     ),
#                     md=6,
#                 ),
#             ]
#         ),
#         dbc.Row(dmc.Space(h=20)),
#         dbc.Row(
#             [
#                 dbc.Col(
#                     dbc.Card(
#                         [
#                             dbc.CardBody(
#                                 dmc.Group(
#                                     [
#                                         dmc.Title(
#                                             id="indicador-media-correcoes-primeira-colaborador",
#                                             order=2,
#                                         ),
#                                         DashIconify(
#                                             icon="gravity-ui:target-dart",
#                                             width=48,
#                                             color="black",
#                                         ),
#                                     ],
#                                     justify="space-around",
#                                     mt="md",
#                                     mb="xs",
#                                 ),
#                             ),
#                             dbc.CardFooter(
#                                 "Média da % de correções de primeira dos colaboradores"
#                             ),
#                         ],
#                         class_name="card-box-shadow",
#                     ),
#                     md=6,
#                 ),
#                 dbc.Col(
#                     dbc.Card(
#                         [
#                             dbc.CardBody(
#                                 dmc.Group(
#                                     [
#                                         dmc.Title(
#                                             id="indicador-media-correcoes-tardias-colaborador",
#                                             order=2,
#                                         ),
#                                         DashIconify(
#                                             icon="game-icons:multiple-targets",
#                                             width=48,
#                                             color="black",
#                                         ),
#                                     ],
#                                     justify="space-around",
#                                     mt="md",
#                                     mb="xs",
#                                 ),
#                             ),
#                             dbc.CardFooter(
#                                 "Média da % de correções tardias dos colaboradores"
#                             ),
#                         ],
#                         class_name="card-box-shadow",
#                     ),
#                     md=6,
#                 ),
#             ]
#         ),
#         dbc.Row(dmc.Space(h=20)),
#         dbc.Row(
#             [
#                 dag.AgGrid(
#                     id="tabela-top-mecanicos",
#                     columnDefs=tbl_top_mecanicos,
#                     rowData=[],
#                     defaultColDef={
#                         "filter": True,
#                         "floatingFilter": True,
#                         "wrapHeaderText": True,
#                         "initialWidth": 200,
#                         "autoHeaderHeight": True,
#                     },
#                     columnSize="autoSize",
#                     dashGridOptions={
#                         # "pagination": True,
#                         "animateRows": False,
#                         "localeText": locale_utils.AG_GRID_LOCALE_BR,
#                     },
#                 ),
#             ]
#         ),
#         # dbc.Row(
#         #     dbc.Col(
#         #         dbc.Button("Download dados mecânico", color="primary", className="me-2"),
#         #         width="auto",  # Button takes its natural width
#         #         className="d-flex justify-content-center",  # Centers the button in the row
#         #     ),
#         #     className="mt-4",  # Adds some margin at the top
#         # ),
#         html.Hr(),
#         # TOP OS e Veículos
#         dbc.Row(
#             [
#                 dbc.Col(
#                     DashIconify(icon="icon-park-outline:ranking-list", width=45),
#                     width="auto",
#                 ),
#                 dbc.Col(
#                     html.H3(
#                         "Ranking de OS e Veículos por Dias até Correção",
#                         className="align-self-center",
#                     ),
#                     width=True,
#                 ),
#             ],
#             align="center",
#         ),
#         html.Hr(),
#         dbc.Row(
#             [
#                 dag.AgGrid(
#                     id="tabela-top-veiculos-problematicos",
#                     columnDefs=tbl_top_veiculos_problematicos,
#                     rowData=[],
#                     defaultColDef={"filter": True, "floatingFilter": True},
#                     columnSize="responsiveSizeToFit",
#                     dashGridOptions={
#                         "localeText": locale_utils.AG_GRID_LOCALE_BR,
#                         # "pagination": True,
#                         # "animateRows": False
#                     },
#                 ),
#             ]
#         ),
#         # dbc.Row(
#         #     [
#         #         dbc.Col(
#         #             dbc.Row(
#         #                 [
#         #                     html.H5("Ordem de Serviço"),
#         #                     dag.AgGrid(
#         #                         id="tabela-top-os-problematicas",
#         #                         columnDefs=tbl_top_os,
#         #                         rowData=[],
#         #                         defaultColDef={"filter": True, "floatingFilter": True},
#         #                         columnSize="responsiveSizeToFit",
#         #                         # columnSize="sizeToFit",
#         #                         dashGridOptions={
#         #                             "localeText": locale_utils.AG_GRID_LOCALE_BR,
#         #                             # "pagination": True,
#         #                             # "animateRows": False
#         #                         },
#         #                     ),
#         #                 ]
#         #             ),
#         #             md=8,
#         #         ),
#         #         dbc.Col(
#         #             dbc.Row(
#         #                 [
#         #                     html.H4("Veículos (Soma de Dias)"),
#         #                     dag.AgGrid(
#         #                         id="tabela-top-veiculos",
#         #                         columnDefs=tbl_top_vec,
#         #                         rowData=[],
#         #                         defaultColDef={"filter": True, "floatingFilter": True},
#         #                         columnSize="responsiveSizeToFit",
#         #                         dashGridOptions={
#         #                             "localeText": locale_utils.AG_GRID_LOCALE_BR,
#         #                             # "pagination": True,
#         #                             # "animateRows": False
#         #                         },
#         #                     ),
#         #                 ]
#         #             ),
#         #             md=4,
#         #         ),
#         #     ]
#         # ),
#         html.Hr(),
#         dbc.Row(
#             [
#                 dbc.Col(
#                     DashIconify(icon="hugeicons:search-list-02", width=45), width="auto"
#                 ),
#                 dbc.Col(
#                     html.H3(
#                         "Detalhar Ordens de Serviço de um Veículo",
#                         className="align-self-center",
#                     ),
#                     width=True,
#                 ),
#             ],
#             align="center",
#         ),
#         html.Hr(),
#         dbc.Row(
#             [
#                 dbc.Col(
#                     dbc.Card(
#                         [
#                             html.Div(
#                                 [
#                                     dbc.Label("Veículos a Detalhar:"),
#                                     dcc.Dropdown(
#                                         id="input-lista-vec-detalhar",
#                                         options=[],
#                                         placeholder="Selecione o veículo",
#                                     ),
#                                 ],
#                                 className="dash-bootstrap",
#                             ),
#                         ],
#                         body=True,
#                     ),
#                     md=12,
#                 ),
#             ],
#         ),
#         dbc.Row(dmc.Space(h=20)),
#         dbc.Row(
#             [
#                 dag.AgGrid(
#                     id="tabela-detalhes-vec-os",
#                     columnDefs=tbl_detalhes_vec_os,
#                     rowData=[],
#                     defaultColDef={
#                         "filter": True,
#                         "floatingFilter": True,
#                         "wrapHeaderText": True,
#                         "initialWidth": 200,
#                         "autoHeaderHeight": True,
#                     },
#                     columnSize="autoSize",
#                     # columnSize="sizeToFit",
#                     dashGridOptions={
#                         "pagination": True,
#                         "animateRows": False,
#                         "localeText": locale_utils.AG_GRID_LOCALE_BR,
#                     },
#                 ),
#             ]
#         ),
#     ]
# )


# ##############################################################################
# # CALLBACKS ##################################################################
# ##############################################################################


# def obtem_dados_os_sql(lista_os, data_inicio, data_fim, min_dias):
#     # Extraí a data final
#     # Remove min_dias antes para evitar que a última OS não seja retrabalho
#     data_fim_dt = pd.to_datetime(data_fim)
#     data_fim_corrigida_dt = data_fim_dt - pd.DateOffset(days=min_dias + 1)
#     data_fim_corrigida_str = data_fim_corrigida_dt.strftime("%Y-%m-%d")

#     # Query
#     query = f"""
#     WITH os_diff_days AS (
#         SELECT
#             od."KEY_HASH",
#             od."PRIORIDADE SERVICO",
#             od."DESCRICAO DA SECAO",
#             od."DESCRICAO DA OFICINA",
#             od."OBSERVACAO DA OS",
#             od."COMPLEMENTO DO SERVICO",
#             od."NUMERO DA OS",
#             od."CODIGO DO VEICULO",
#             od."DESCRICAO DO SERVICO",
#             od."DATA DA ABERTURA DA OS",
#             od."DATA DO FECHAMENTO DA OS",
#             od."DESCRICAO DO MODELO",
#             od."DATA INICIO SERVIÇO",
#             od."DATA DE FECHAMENTO DO SERVICO",
#             od."COLABORADOR QUE EXECUTOU O SERVICO",
#             lag(od."DATA DE FECHAMENTO DO SERVICO") OVER (PARTITION BY od."CODIGO DO VEICULO" ORDER BY od."DATA DA ABERTURA DA OS") AS "PREV_DATA_FECHAMENTO",
#             lead(od."DATA DA ABERTURA DA OS") OVER (PARTITION BY od."CODIGO DO VEICULO" ORDER BY od."DATA DE FECHAMENTO DO SERVICO") AS "NEXT_DATA_ABERTURA",
#                 CASE
#                     WHEN lag(od."DATA DE FECHAMENTO DO SERVICO") OVER (PARTITION BY od."CODIGO DO VEICULO" ORDER BY od."DATA DA ABERTURA DA OS") IS NOT NULL AND od."DATA DA ABERTURA DA OS" IS NOT NULL THEN date_part('day'::text, od."DATA DA ABERTURA DA OS"::timestamp without time zone - lag(od."DATA DE FECHAMENTO DO SERVICO") OVER (PARTITION BY od."CODIGO DO VEICULO" ORDER BY od."DATA DA ABERTURA DA OS")::timestamp without time zone)
#                     ELSE NULL::double precision
#                 END AS prev_days,
#                 CASE
#                     WHEN od."DATA DE FECHAMENTO DO SERVICO" IS NOT NULL AND lead(od."DATA DA ABERTURA DA OS") OVER (PARTITION BY od."CODIGO DO VEICULO" ORDER BY od."DATA DE FECHAMENTO DO SERVICO") IS NOT NULL THEN date_part('day'::text, lead(od."DATA DA ABERTURA DA OS") OVER (PARTITION BY od."CODIGO DO VEICULO" ORDER BY od."DATA DE FECHAMENTO DO SERVICO")::timestamp without time zone - od."DATA DE FECHAMENTO DO SERVICO"::timestamp without time zone)
#                     ELSE NULL::double precision
#                 END AS next_days
#         FROM
#             os_dados od
#         WHERE
#             od."DATA INICIO SERVIÇO" IS NOT NULL
#             AND od."DATA DE FECHAMENTO DO SERVICO" IS NOT NULL
#             AND od."DATA INICIO SERVIÇO" ~ '^\\d{{4}}-\\d{{2}}-\\d{{2}}T\\d{{2}}:\\d{{2}}:\\d{{2}}$'::text
#             AND od."DATA DE FECHAMENTO DO SERVICO" ~ '^\\d{{4}}-\\d{{2}}-\\d{{2}}T\\d{{2}}:\\d{{2}}:\\d{{2}}$'::text
#             AND od."DESCRICAO DO TIPO DA OS" = 'OFICINA'::text
#         ),
#     os_with_flags AS (
#         SELECT
#             os_diff_days."NUMERO DA OS",
#             os_diff_days."CODIGO DO VEICULO",
#             os_diff_days."DESCRICAO DO SERVICO",
#             os_diff_days."DESCRICAO DO MODELO",
#             os_diff_days."DATA INICIO SERVIÇO",
#             os_diff_days."DATA DE FECHAMENTO DO SERVICO",
#             os_diff_days."COLABORADOR QUE EXECUTOU O SERVICO",
#             os_diff_days."COMPLEMENTO DO SERVICO",
#             os_diff_days.prev_days,
#             os_diff_days.next_days,
#             CASE
#                 WHEN os_diff_days.next_days <= {min_dias}::numeric THEN true
#                 ELSE false
#             END AS retrabalho,
#             CASE
#                 WHEN os_diff_days.next_days > {min_dias}::numeric OR os_diff_days.next_days IS NULL THEN true
#                 ELSE false
#             END AS correcao,
#             CASE
#                 WHEN
#                     (os_diff_days.next_days > {min_dias}::numeric OR os_diff_days.next_days IS NULL)
#                     AND
#                     (os_diff_days.prev_days > {min_dias}::numeric OR os_diff_days.prev_days IS NULL)
#                     THEN true
#                 ELSE false
#             END AS correcao_primeira
#         FROM
#             os_diff_days
#         ),
#     problem_grouping AS (
#         SELECT
#             SUM(
#                 CASE
#                     WHEN os_with_flags.correcao THEN 1
#                     ELSE 0
#                 END) OVER (PARTITION BY os_with_flags."CODIGO DO VEICULO" ORDER BY os_with_flags."DATA INICIO SERVIÇO") AS problem_no,
#             os_with_flags."NUMERO DA OS",
#             os_with_flags."CODIGO DO VEICULO",
#             os_with_flags."DESCRICAO DO SERVICO",
#             os_with_flags."DESCRICAO DO MODELO",
#             os_with_flags."DATA INICIO SERVIÇO",
#             os_with_flags."DATA DE FECHAMENTO DO SERVICO",
#             os_with_flags."COLABORADOR QUE EXECUTOU O SERVICO",
#             os_with_flags."COMPLEMENTO DO SERVICO",
#             os_with_flags.prev_days,
#             os_with_flags.next_days,
#             os_with_flags.retrabalho,
#             os_with_flags.correcao,
#             os_with_flags.correcao_primeira
#         FROM
#             os_with_flags
#         )

#     SELECT
#         CASE
#             WHEN problem_grouping.retrabalho THEN problem_grouping.problem_no + 1
#             ELSE problem_grouping.problem_no
#         END AS problem_no,
#         problem_grouping."NUMERO DA OS",
#         problem_grouping."CODIGO DO VEICULO",
#         problem_grouping."DESCRICAO DO MODELO",
#         problem_grouping."DESCRICAO DO SERVICO",
#         problem_grouping."DATA INICIO SERVIÇO",
#         problem_grouping."DATA DE FECHAMENTO DO SERVICO",
#         problem_grouping."COLABORADOR QUE EXECUTOU O SERVICO",
#         problem_grouping."COMPLEMENTO DO SERVICO",
#         problem_grouping.prev_days,
#         problem_grouping.next_days,
#         problem_grouping.retrabalho,
#         problem_grouping.correcao,
#         problem_grouping.correcao_primeira
#     FROM
#         problem_grouping
#     WHERE
#         problem_grouping."DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio}' AND '{data_fim_corrigida_str}'
#         AND problem_grouping."DESCRICAO DO SERVICO" IN ({', '.join([f"'{x}'" for x in lista_os])})
#         AND problem_grouping."DESCRICAO DO MODELO" IN ('M.BENZ O 500/INDUSCAR MILLEN A')
#             -- AND (
#                 --"DESCRICAO DO SERVICO" = 'Motor cortando alimentação'
#                 --OR
#                 --"DESCRICAO DO SERVICO" = 'Motor sem força'
#             --)
#             --AND
#             --(
#             -- AND od."CODIGO DO VEICULO" ='50803'
#             --OR
#             --od."CODIGO DO VEICULO" ='50530'
#             --)
#     ORDER BY
#         problem_grouping."DATA INICIO SERVIÇO";
#     """

#     df_os_query = pd.read_sql_query(query, pgEngine)

#     # Tratamento de datas
#     df_os_query["DATA INICIO SERVICO"] = pd.to_datetime(
#         df_os_query["DATA INICIO SERVIÇO"]
#     )
#     df_os_query["DATA DE FECHAMENTO DO SERVICO"] = pd.to_datetime(
#         df_os_query["DATA DE FECHAMENTO DO SERVICO"]
#     )

#     return df_os_query


# def obtem_estatistica_retrabalho_sql(df_os, min_dias):
#     # Lida com NaNs
#     df_os = df_os.fillna(0)

#     # Extraí os DFs
#     df_retrabalho = df_os[df_os["retrabalho"]]
#     df_correcao = df_os[df_os["correcao"]]
#     df_correcao_primeira = df_os[df_os["correcao_primeira"]]

#     # Estatísticas por modelo
#     df_modelo = (
#         df_os.groupby("DESCRICAO DO MODELO")
#         .agg(
#             {
#                 "NUMERO DA OS": "count",
#                 "retrabalho": "sum",
#                 "correcao": "sum",
#                 "correcao_primeira": "sum",
#                 "problem_no": lambda x: x.nunique(),  # Conta o número de problemas distintos
#             }
#         )
#         .reset_index()
#     )
#     # Renomeia algumas colunas
#     df_modelo = df_modelo.rename(
#         columns={
#             "NUMERO DA OS": "TOTAL_DE_OS",
#             "retrabalho": "RETRABALHOS",
#             "correcao": "CORRECOES",
#             "correcao_primeira": "CORRECOES_DE_PRIMEIRA",
#             "problem_no": "NUM_PROBLEMAS",
#         }
#     )
#     # Correções Tardias
#     df_modelo["CORRECOES_TARDIA"] = (
#         df_modelo["CORRECOES"] - df_modelo["CORRECOES_DE_PRIMEIRA"]
#     )
#     # Calcula as porcentagens
#     df_modelo["PERC_RETRABALHO"] = 100 * (
#         df_modelo["RETRABALHOS"] / df_modelo["TOTAL_DE_OS"]
#     )
#     df_modelo["PERC_CORRECOES"] = 100 * (
#         df_modelo["CORRECOES"] / df_modelo["TOTAL_DE_OS"]
#     )
#     df_modelo["PERC_CORRECOES_DE_PRIMEIRA"] = 100 * (
#         df_modelo["CORRECOES_DE_PRIMEIRA"] / df_modelo["TOTAL_DE_OS"]
#     )
#     df_modelo["PERC_CORRECOES_TARDIA"] = 100 * (
#         df_modelo["CORRECOES_TARDIA"] / df_modelo["TOTAL_DE_OS"]
#     )
#     df_modelo["REL_PROBLEMA_OS"] = df_modelo["NUM_PROBLEMAS"] / df_modelo["TOTAL_DE_OS"]

#     # Estatísticas por colaborador
#     df_colaborador = (
#         df_os.groupby("COLABORADOR QUE EXECUTOU O SERVICO")
#         .agg(
#             {
#                 "NUMERO DA OS": "count",
#                 "retrabalho": "sum",
#                 "correcao": "sum",
#                 "correcao_primeira": "sum",
#                 "problem_no": lambda x: x.nunique(),  # Conta o número de problemas distintos
#             }
#         )
#         .reset_index()
#     )
#     # Renomeia algumas colunas
#     df_colaborador = df_colaborador.rename(
#         columns={
#             "NUMERO DA OS": "TOTAL_DE_OS",
#             "retrabalho": "RETRABALHOS",
#             "correcao": "CORRECOES",
#             "correcao_primeira": "CORRECOES_DE_PRIMEIRA",
#             "problem_no": "NUM_PROBLEMAS",
#         }
#     )
#     # Correções Tardias
#     df_colaborador["CORRECOES_TARDIA"] = (
#         df_colaborador["CORRECOES"] - df_colaborador["CORRECOES_DE_PRIMEIRA"]
#     )
#     # Calcula as porcentagens
#     df_colaborador["PERC_RETRABALHO"] = 100 * (
#         df_colaborador["RETRABALHOS"] / df_colaborador["TOTAL_DE_OS"]
#     )
#     df_colaborador["PERC_CORRECOES"] = 100 * (
#         df_colaborador["CORRECOES"] / df_colaborador["TOTAL_DE_OS"]
#     )
#     df_colaborador["PERC_CORRECOES_DE_PRIMEIRA"] = 100 * (
#         df_colaborador["CORRECOES_DE_PRIMEIRA"] / df_colaborador["TOTAL_DE_OS"]
#     )
#     df_colaborador["PERC_CORRECOES_TARDIA"] = 100 * (
#         df_colaborador["CORRECOES_TARDIA"] / df_colaborador["TOTAL_DE_OS"]
#     )
#     df_colaborador["REL_PROBLEMA_OS"] = (
#         df_colaborador["NUM_PROBLEMAS"] / df_colaborador["TOTAL_DE_OS"]
#     )

#     # Adiciona label de nomes
#     df_colaborador["COLABORADOR QUE EXECUTOU O SERVICO"] = df_colaborador[
#         "COLABORADOR QUE EXECUTOU O SERVICO"
#     ].astype(int)

#     # Encontra o nome do colaborador
#     for ix, linha in df_colaborador.iterrows():
#         colaborador = linha["COLABORADOR QUE EXECUTOU O SERVICO"]
#         nome_colaborador = "Não encontrado"
#         if colaborador in df_mecanicos["cod_colaborador"].values:
#             nome_colaborador = df_mecanicos[
#                 df_mecanicos["cod_colaborador"] == colaborador
#             ]["nome_colaborador"].values[0]
#             nome_colaborador = re.sub(r"(?<!^)([A-Z])", r" \1", nome_colaborador)

#         df_colaborador.at[ix, "LABEL_COLABORADOR"] = (
#             f"{nome_colaborador} - {int(colaborador)}"
#         )
#         df_colaborador.at[ix, "NOME_COLABORADOR"] = f"{nome_colaborador}"
#         df_colaborador.at[ix, "ID_COLABORADOR"] = int(colaborador)

#     # Dias para correção
#     df_dias_para_correcao = (
#         df_os.groupby(["problem_no", "CODIGO DO VEICULO", "DESCRICAO DO MODELO"])
#         .agg(
#             data_inicio=("DATA INICIO SERVIÇO", "min"),
#             data_fim=("DATA INICIO SERVIÇO", "max"),
#         )
#         .reset_index()
#     )
#     df_dias_para_correcao["data_inicio"] = pd.to_datetime(
#         df_dias_para_correcao["data_inicio"]
#     )
#     df_dias_para_correcao["data_fim"] = pd.to_datetime(
#         df_dias_para_correcao["data_fim"]
#     )
#     df_dias_para_correcao["dias_correcao"] = (
#         df_dias_para_correcao["data_fim"] - df_dias_para_correcao["data_inicio"]
#     ).dt.days

#     # Num de OS para correção
#     df_num_os_por_problema = (
#         df_os.groupby(["problem_no", "CODIGO DO VEICULO"])
#         .size()
#         .reset_index(name="TOTAL_DE_OS")
#     )

#     # DF estatística
#     df_estatistica = pd.DataFrame(
#         {
#             "TOTAL_DE_OS": len(df_os),
#             "TOTAL_DE_PROBLEMAS": len(df_os[df_os["correcao"]]),
#             "TOTAL_DE_RETRABALHOS": len(df_os[df_os["retrabalho"]]),
#             "TOTAL_DE_CORRECOES": len(df_os[df_os["correcao"]]),
#             "TOTAL_DE_CORRECOES_DE_PRIMEIRA": len(df_os[df_os["correcao_primeira"]]),
#             "MEDIA_DE_DIAS_PARA_CORRECAO": df_dias_para_correcao[
#                 "dias_correcao"
#             ].mean(),
#             "MEDIANA_DE_DIAS_PARA_CORRECAO": df_dias_para_correcao[
#                 "dias_correcao"
#             ].median(),
#             "MEDIA_DE_OS_PARA_CORRECAO": df_num_os_por_problema["TOTAL_DE_OS"].mean(),
#         },
#         index=[0],
#     )
#     # Correções tardias
#     df_estatistica["TOTAL_DE_CORRECOES_TARDIAS"] = (
#         df_estatistica["TOTAL_DE_CORRECOES"]
#         - df_estatistica["TOTAL_DE_CORRECOES_DE_PRIMEIRA"]
#     )
#     # Rel probl/os
#     df_estatistica["RELACAO_OS_PROBLEMA"] = (
#         df_estatistica["TOTAL_DE_OS"] / df_estatistica["TOTAL_DE_PROBLEMAS"]
#     )

#     # Porcentagens
#     df_estatistica["PERC_RETRABALHO"] = 100 * (
#         df_estatistica["TOTAL_DE_RETRABALHOS"] / df_estatistica["TOTAL_DE_OS"]
#     )
#     df_estatistica["PERC_CORRECOES"] = 100 * (
#         df_estatistica["TOTAL_DE_CORRECOES"] / df_estatistica["TOTAL_DE_OS"]
#     )
#     df_estatistica["PERC_CORRECOES_DE_PRIMEIRA"] = 100 * (
#         df_estatistica["TOTAL_DE_CORRECOES_DE_PRIMEIRA"] / df_estatistica["TOTAL_DE_OS"]
#     )
#     df_estatistica["PERC_CORRECOES_TARDIAS"] = 100 * (
#         df_estatistica["TOTAL_DE_CORRECOES_TARDIAS"] / df_estatistica["TOTAL_DE_OS"]
#     )

#     return {
#         "df_estatistica": df_estatistica.to_dict("records"),
#         "df_retrabalho": df_retrabalho.to_dict("records"),
#         "df_correcao": df_correcao.to_dict("records"),
#         "df_correcao_primeira": df_correcao_primeira.to_dict("records"),
#         "df_modelo": df_modelo.to_dict("records"),
#         "df_colaborador": df_colaborador.to_dict("records"),
#         "df_dias_para_correcao": df_dias_para_correcao.to_dict("records"),
#         "df_num_os_por_problema": df_num_os_por_problema.to_dict("records"),
#     }


# @callback(
#     Output("store-dados-tipo-servico", "data"),
#     [
#         Input("input-lista-os", "value"),
#         Input("input-intervalo-datas", "value"),
#         Input("input-dias", "value"),
#     ],
#     running=[(Output("loading-overlay", "visible"), True, False)],
# )
# def computa_retrabalho(lista_os, datas, min_dias):
#     dados_vazios = {
#         "df_os": pd.DataFrame().to_dict("records"),
#         "df_estatistica": pd.DataFrame().to_dict("records"),
#         "df_retrabalho": pd.DataFrame().to_dict("records"),
#         "df_correcao": pd.DataFrame().to_dict("records"),
#         "df_correcao_primeira": pd.DataFrame().to_dict("records"),
#         "df_modelo": pd.DataFrame().to_dict("records"),
#         "df_colaborador": pd.DataFrame().to_dict("records"),
#         "df_dias_para_correcao": pd.DataFrame().to_dict("records"),
#         "df_num_os_por_problema": pd.DataFrame().to_dict("records"),
#         "vazio": True,
#     }

#     # Verifica se foi preenchido
#     if (lista_os is None or not lista_os) or (datas is None or not datas or None in datas):
#         return dados_vazios

#     # Obtem datas
#     inicio_data = datas[0]
#     fim_data = datas[1]

#     # Realiza consulta
#     df_os_sql = obtem_dados_os_sql(lista_os, inicio_data, fim_data, min_dias)

#     # Verifica se há dados, caso negativo retorna vazio
#     df_filtro_sql = df_os_sql[
#         (df_os_sql["DATA INICIO SERVICO"] >= pd.to_datetime(inicio_data))
#         & (df_os_sql["DATA DE FECHAMENTO DO SERVICO"] <= pd.to_datetime(fim_data))
#     ]
#     if df_filtro_sql.empty:
#         return dados_vazios

#     # Computa retrabalho
#     dict_dfs_retrabalhos = obtem_estatistica_retrabalho_sql(df_os_sql, min_dias)

#     return {
#         "df_os": df_filtro_sql.to_dict("records"),
#         "df_estatistica": dict_dfs_retrabalhos["df_estatistica"],
#         "df_retrabalho": dict_dfs_retrabalhos["df_retrabalho"],
#         "df_correcao": dict_dfs_retrabalhos["df_correcao"],
#         "df_correcao_primeira": dict_dfs_retrabalhos["df_correcao_primeira"],
#         "df_modelo": dict_dfs_retrabalhos["df_modelo"],
#         "df_colaborador": dict_dfs_retrabalhos["df_colaborador"],
#         "df_dias_para_correcao": dict_dfs_retrabalhos["df_dias_para_correcao"],
#         "df_num_os_por_problema": dict_dfs_retrabalhos["df_num_os_por_problema"],
#         "vazio": False,
#     }


# @callback(
#     Output("graph-retrabalho-correcoes", "figure"), Input("store-dados-tipo-servico", "data")
# )
# def plota_grafico_pizza_retrabalho(data):
#     if data["vazio"]:
#         return go.Figure()

#     # Obtém os dados de retrabalho

#     df_estatistica = pd.DataFrame(data["df_estatistica"])

#     # Prepara os dados para o gráfico
#     labels = ["Correções de Primeira", "Correções Tardias", "Retrabalhos"]
#     values = [
#         df_estatistica["TOTAL_DE_CORRECOES_DE_PRIMEIRA"].values[0],
#         df_estatistica["TOTAL_DE_CORRECOES_TARDIAS"].values[0],
#         df_estatistica["TOTAL_DE_RETRABALHOS"].values[0],
#     ]

#     # Gera o gráfico
#     fig = go.Figure(
#         data=[
#             go.Pie(
#                 labels=labels,
#                 values=values,
#                 direction="clockwise",
#                 marker_colors=[tema.COR_SUCESSO, tema.COR_ALERTA, tema.COR_ERRO],
#                 sort=True,
#             )
#         ]
#     )

#     # Arruma legenda e texto
#     fig.update_traces(textinfo="value+percent", sort=False)

#     # Retorna o gráfico
#     return fig


# @callback(
#     Output("graph-retrabalho-cumulativo", "figure"), Input("store-dados-tipo-servico", "data")
# )
# def plota_grafico_cumulativo_retrabalho(data):
#     if data["vazio"]:
#         return go.Figure()

#     # Obtém os dados de dias para correção
#     df_dias_para_correcao = pd.DataFrame(data["df_dias_para_correcao"])

#     # Ordenando os dados e criando a coluna cumulativa em termos percentuais
#     df_dias_para_correcao_ordenado = df_dias_para_correcao.sort_values(
#         by="dias_correcao"
#     ).copy()
#     df_dias_para_correcao_ordenado["cumulative_percentage"] = (
#         df_dias_para_correcao_ordenado["dias_correcao"].expanding().count()
#         / len(df_dias_para_correcao_ordenado)
#         * 100
#     )

#     # Verifica se df não está vazio
#     if df_dias_para_correcao_ordenado.empty:
#         return go.Figure()

#     # Criando o gráfico cumulativo com o eixo y em termos percentuais
#     fig = px.line(
#         df_dias_para_correcao_ordenado,
#         x="dias_correcao",
#         y="cumulative_percentage",
#         labels={
#             "dias_correcao": "Dias",
#             "cumulative_percentage": "Correções Cumulativas (%)",
#         },
#     )

#     # Mostrando os pontos e linhas
#     fig.update_traces(
#         mode="markers+lines",
#     )

#     # Adiciona o Topo
#     df_top = df_dias_para_correcao_ordenado.groupby(
#         "dias_correcao", as_index=False
#     ).agg(
#         cumulative_percentage=("cumulative_percentage", "max"),
#         count=("dias_correcao", "count"),
#     )
#     # Reseta o index para garantir a sequencialidade
#     df_top = df_top.reset_index(drop=True)
#     # Adiciona o rótulo vazio
#     df_top["label"] = ""

#     # Vamos decidir qual a frequência dos labels
#     label_frequency = 1
#     num_records = len(df_top)
#     if num_records >= 30:
#         label_frequency = math.ceil(num_records / 20) + 1
#     elif num_records >= 10:
#         label_frequency = 4
#     elif num_records >= 5:
#         label_frequency = 2

#     # Adiciona o rótulo a cada freq de registros
#     for i in range(len(df_top)):
#         if i % label_frequency == 0:
#             df_top.at[i, "label"] = (
#                 f"{df_top.at[i, 'cumulative_percentage']:.0f}% <br>({df_top.at[i, 'count']})"
#             )

#     fig.add_scatter(
#         x=df_top["dias_correcao"],
#         y=df_top["cumulative_percentage"] + 3,
#         mode="text",
#         text=df_top["label"],
#         textposition="middle right",
#         showlegend=False,
#         marker=dict(color=tema.COR_PADRAO),
#     )

#     fig.update_layout(
#         xaxis=dict(
#             range=[-1, df_dias_para_correcao_ordenado["dias_correcao"].max() + 3]
#         ),
#     )

#     # Retorna o gráfico
#     return fig


# @callback(
#     Output("graph-retrabalho-por-modelo-perc", "figure"),
#     Input("store-dados-tipo-servico", "data"),
# )
# def plota_grafico_barras_retrabalho_por_modelo_perc(data):
#     if data["vazio"]:
#         return go.Figure()

#     # Obtém os dados de retrabalho por modelo
#     df_modelo = pd.DataFrame(data["df_modelo"])

#     # Gera o gráfico
#     bar_chart = px.bar(
#         df_modelo,
#         x="DESCRICAO DO MODELO",
#         y=["PERC_CORRECOES_DE_PRIMEIRA", "PERC_CORRECOES_TARDIA", "PERC_RETRABALHO"],
#         barmode="stack",
#         color_discrete_sequence=[tema.COR_SUCESSO, tema.COR_ALERTA, tema.COR_ERRO],
#         labels={
#             "value": "Percentagem",
#             "DESCRICAO DO SERVICO": "Ordem de Serviço",
#             "variable": "Itens",
#         },
#     )

#     # Atualizando os valores de rótulo para PERC_CORRECOES_DE_PRIMEIRA (percentual e valor absoluto de correções de primeira)
#     bar_chart.update_traces(
#         text=[
#             f"{retrabalho} ({perc_retrab:.2f}%)"
#             for retrabalho, perc_retrab in zip(
#                 df_modelo["CORRECOES_DE_PRIMEIRA"],
#                 df_modelo["PERC_CORRECOES_DE_PRIMEIRA"],
#             )
#         ],
#         selector=dict(name="PERC_CORRECOES_DE_PRIMEIRA"),
#     )

#     # Atualizando os valores de rótulo para PERC_CORRECOES_TARDIA (percentual e valor absoluto de correções tardias)
#     bar_chart.update_traces(
#         text=[
#             f"{correcoes} ({perc_correcoes:.2f}%)"
#             for correcoes, perc_correcoes in zip(
#                 df_modelo["CORRECOES_TARDIA"], df_modelo["PERC_CORRECOES_TARDIA"]
#             )
#         ],
#         selector=dict(name="PERC_CORRECOES_TARDIA"),
#     )

#     # Atualizando os valores de rótulo para PERC_RETRABALHO (percentual e valor absoluto de retrabalhos)
#     bar_chart.update_traces(
#         text=[
#             f"{correcoes} ({perc_correcoes:.2f}%)"
#             for correcoes, perc_correcoes in zip(
#                 df_modelo["RETRABALHOS"], df_modelo["PERC_RETRABALHO"]
#             )
#         ],
#         selector=dict(name="PERC_RETRABALHO"),
#     )

#     # Exibir os rótulos nas barras
#     bar_chart.update_traces(texttemplate="%{text}")

#     # Ajustar a margem inferior para evitar corte de rótulos
#     bar_chart.update_layout(margin=dict(b=200), height=600)

#     # Retorna o gráfico
#     return bar_chart


# @callback(
#     [
#         Output("indicador-total-problemas", "children"),
#         Output("indicador-total-os", "children"),
#         Output("indicador-relacao-problema-os", "children"),
#         Output("indicador-porcentagem-prob-com-retrabalho", "children"),
#         Output("indicador-porcentagem-retrabalho", "children"),
#         Output("indicador-num-medio-dias-correcao", "children"),
#     ],
#     Input("store-dados-tipo-servico", "data"),
# )
# def atualiza_indicadores(data):
#     if data["vazio"]:
#         return ["", "", "", "", "", ""]

#     # Obtém os dados
#     df_estatistica = pd.DataFrame(data["df_estatistica"])
#     df_dias_para_correcao = pd.DataFrame(data["df_dias_para_correcao"])
#     df_num_os_por_problema = pd.DataFrame(data["df_num_os_por_problema"])

#     # Valores
#     total_de_problemas = int(df_estatistica["TOTAL_DE_PROBLEMAS"].values[0])
#     total_de_os = int(df_estatistica["TOTAL_DE_OS"].values[0])
#     rel_os_problemas = round(float(df_estatistica["RELACAO_OS_PROBLEMA"].values[0]), 2)

#     num_problema_sem_retrabalho = int(
#         len(df_num_os_por_problema[df_num_os_por_problema["TOTAL_DE_OS"] == 1])
#     )
#     perc_problema_com_retrabalho = round(
#         100 * (1 - (num_problema_sem_retrabalho / total_de_problemas)), 2
#     )

#     num_retrabalho = int(df_estatistica["TOTAL_DE_RETRABALHOS"].values[0])
#     perc_retrabalho = round(float(df_estatistica["PERC_RETRABALHO"].values[0]), 2)
#     dias_ate_corrigir = round(float(df_dias_para_correcao["dias_correcao"].mean()), 2)
#     num_os_ate_corrigir = round(float(df_num_os_por_problema["TOTAL_DE_OS"].mean()), 2)

#     return [
#         f"{total_de_problemas} problemas",
#         f"{total_de_os} OS",
#         f"{rel_os_problemas} OS/prob",
#         f"{perc_problema_com_retrabalho}%",
#         f"{perc_retrabalho}%",
#         f"{dias_ate_corrigir} dias",
#     ]


# @callback(
#     [
#         Output("indicador-media-os-colaborador", "children"),
#         Output("indicador-media-porcentagem-retrabalho", "children"),
#         Output("indicador-media-correcoes-primeira-colaborador", "children"),
#         Output("indicador-media-correcoes-tardias-colaborador", "children"),
#     ],
#     Input("store-dados-tipo-servico", "data"),
# )
# def atualiza_indicadores_mecanico(data):
#     if data["vazio"]:
#         return ["", "", "", ""]

#     # Obtém os dados de retrabalho
#     df_colaborador = pd.DataFrame(data["df_colaborador"])

#     # Média de OS por mecânico
#     media_os_por_mecanico = round(float(df_colaborador["TOTAL_DE_OS"].mean()), 2)

#     # Retrabalhos médios
#     media_retrabalhos_por_mecanico = round(
#         float(df_colaborador["PERC_RETRABALHO"].mean()), 2
#     )

#     # Correções de Primeira
#     media_correcoes_primeira = round(
#         float(df_colaborador["PERC_CORRECOES_DE_PRIMEIRA"].mean()), 2
#     )

#     # Correções Tardias
#     media_correcoes_tardias = round(
#         float(df_colaborador["PERC_CORRECOES_TARDIA"].mean()), 2
#     )

#     return [
#         f"{media_os_por_mecanico} OS / colaborador",
#         f"{media_retrabalhos_por_mecanico}%",
#         f"{media_correcoes_primeira}%",
#         f"{media_correcoes_tardias}%",
#     ]


# @callback(
#     Output("tabela-top-mecanicos", "rowData"),
#     Input("store-dados-tipo-servico", "data"),
# )
# def update_tabela_mecanicos_retrabalho(data):
#     if data["vazio"]:
#         return []

#     # Obtém os dados do colaborador
#     df_colaborador = pd.DataFrame(data["df_colaborador"])

#     # Prepara o dataframe para a tabela
#     df_colaborador["REL_OS_PROB"] = round(
#         df_colaborador["TOTAL_DE_OS"] / df_colaborador["NUM_PROBLEMAS"], 2
#     )
#     df_colaborador["PERC_RETRABALHO"] = df_colaborador["PERC_RETRABALHO"].round(2)
#     df_colaborador["PERC_CORRECOES"] = df_colaborador["PERC_CORRECOES"].round(2)
#     df_colaborador["PERC_CORRECOES_DE_PRIMEIRA"] = df_colaborador[
#         "PERC_CORRECOES_DE_PRIMEIRA"
#     ].round(2)

#     # Ordena por PERC_RETRABALHO
#     df_colaborador = df_colaborador.sort_values(by="PERC_RETRABALHO", ascending=False)

#     # Retorna tabela
#     return df_colaborador.to_dict("records")


# @callback(
#     Output("tabela-top-veiculos-problematicos", "rowData"),
#     Input("store-dados-tipo-servico", "data"),
# )
# def update_tabela_veiculos_mais_problematicos(data):
#     if data["vazio"]:
#         return []

#     # Obtém os dados de retrabalho
#     df_dias_para_correcao = pd.DataFrame(data["df_dias_para_correcao"])
#     df_num_os_por_problema = pd.DataFrame(data["df_num_os_por_problema"])

#     # Merge
#     df_os_problematicas = df_dias_para_correcao.merge(df_num_os_por_problema)

#     # Agrega
#     df_os_problematicas = (
#         df_os_problematicas.groupby(["CODIGO DO VEICULO", "DESCRICAO DO MODELO"])
#         .agg({"problem_no": "count", "dias_correcao": "sum", "TOTAL_DE_OS": "sum"})
#         .reset_index()
#     )

#     # Gera campos
#     df_os_problematicas["TOTAL_DE_PROBLEMAS"] = df_os_problematicas["problem_no"]
#     df_os_problematicas["TOTAL_DE_OS"] = df_os_problematicas["TOTAL_DE_OS"]
#     df_os_problematicas["REL_PROBLEMA_OS"] = round(
#         df_os_problematicas["TOTAL_DE_OS"] / df_os_problematicas["TOTAL_DE_PROBLEMAS"],
#         2,
#     )
#     df_os_problematicas["TOTAL_DIAS_ATE_CORRIGIR"] = df_os_problematicas[
#         "dias_correcao"
#     ]

#     df_os_problematicas.sort_values(
#         by="TOTAL_DIAS_ATE_CORRIGIR", ascending=False, inplace=True
#     )

#     return df_os_problematicas.to_dict("records")


# # @callback(
# #     Output("tabela-top-os-problematicas", "rowData"),
# #     Input("store-dados-tipo-servico", "data"),
# # )
# # def update_tabela_os_problematicas(data):
# #     if data["vazio"]:
# #         return []

# #     # Obtém os dados de retrabalho
# #     df_dias_para_correcao = pd.DataFrame(data["df_dias_para_correcao"])
# #     df_num_os_por_problema = pd.DataFrame(data["df_num_os_por_problema"])

# #     df_os_problematicas = df_dias_para_correcao.merge(df_num_os_por_problema)
# #     #####
# #     df_fixes = pd.DataFrame(data["df_fixes"])

# #     df_tabela = df_fixes.sort_values(by=["DIAS_ATE_OS_CORRIGIR"], ascending=False).copy()
# #     df_tabela["DIA"] = pd.to_datetime(df_tabela["DATA_INICIO_SERVICO_DT"]).dt.strftime("%d/%m/%Y")

# #     # Retorna tabela
# #     return df_tabela.to_dict("records")


# # @callback(
# #     Output("tabela-top-veiculos", "rowData"),
# #     Input("store-dados-tipo-servico", "data"),
# # )
# # def update_tabela_veiculos_problematicos(data):
# #     if data["vazio"]:
# #         return []

# #     #####
# #     # Obtém os dados de retrabalho
# #     #####
# #     df_fixes = pd.DataFrame(data["df_fixes"])

# #     df_top_veiculos = (
# #         df_fixes.groupby("CODIGO DO VEICULO")["DIAS_ATE_OS_CORRIGIR"].sum().reset_index(name="TOTAL_DIAS_ATE_CORRIGIR")
# #     )
# #     df_top_veiculos = df_top_veiculos.sort_values(by="TOTAL_DIAS_ATE_CORRIGIR", ascending=False)

# #     # Retorna tabela
# #     return df_top_veiculos.to_dict("records")


# @callback(
#     Output("input-lista-vec-detalhar", "options"),
#     Input("store-dados-tipo-servico", "data"),
# )
# def update_lista_veiculos_detalhar(data):
#     if data["vazio"]:
#         return []

#     # Obtém os dados de os por veiculo
#     df_num_os_por_problema = pd.DataFrame(data["df_num_os_por_problema"])

#     # Faz o total
#     df_total_os_por_veiculo = (
#         df_num_os_por_problema.groupby("CODIGO DO VEICULO")["TOTAL_DE_OS"]
#         .sum()
#         .reset_index()
#     )

#     # Ordena veículos por num de os
#     df_top_veiculos = df_total_os_por_veiculo.sort_values(
#         by="TOTAL_DE_OS", ascending=False
#     )

#     # Gera a lista de opções
#     vec_list = [
#         {
#             "label": f"{linha['CODIGO DO VEICULO']} ({linha['TOTAL_DE_OS']} OS)",
#             "value": linha["CODIGO DO VEICULO"],
#         }
#         for _, linha in df_top_veiculos.iterrows()
#     ]

#     return vec_list


# @callback(
#     Output("tabela-detalhes-vec-os", "rowData"),
#     [
#         Input("store-dados-tipo-servico", "data"),
#         Input("input-lista-vec-detalhar", "value"),
#         Input("input-dias", "value"),
#     ],
# )
# def update_tabela_veiculos_detalhar(data, vec_detalhar, min_dias):
#     if data["vazio"] or vec_detalhar is None or vec_detalhar == "":
#         return []

#     # Obtém os dados de retrabalho
#     df_retrabalho = pd.DataFrame(data["df_retrabalho"])
#     df_correcao = pd.DataFrame(data["df_correcao"])
#     df_correcao_primeira = pd.DataFrame(data["df_correcao_primeira"])

#     # Obtém os dados de os por veiculo
#     df_num_os_por_problema = pd.DataFrame(data["df_num_os_por_problema"])

#     # Filtra as OS do veículo
#     df_retrabalho_vec = pd.DataFrame()
#     if not df_retrabalho.empty:
#         df_retrabalho_vec = df_retrabalho[
#             df_retrabalho["CODIGO DO VEICULO"] == vec_detalhar
#         ].copy()
#         df_retrabalho_vec["CLASSIFICACAO"] = "Retrabalho"
#         df_retrabalho_vec["CLASSIFICACAO_EMOJI"] = "❌"

#     df_correcao_vec = pd.DataFrame()
#     if not df_correcao.empty:
#         df_correcao_vec = df_correcao[
#             df_correcao["CODIGO DO VEICULO"] == vec_detalhar
#         ].copy()
#         df_correcao_vec["CLASSIFICACAO"] = "Correção"
#         df_correcao_vec["CLASSIFICACAO_EMOJI"] = "✅"

#     # Junta total com detalhar
#     df_correcao_vec = pd.merge(
#         df_correcao_vec, df_num_os_por_problema, on=["problem_no", "CODIGO DO VEICULO"]
#     )

#     # Junta os dados
#     df_detalhar = pd.concat([df_retrabalho_vec, df_correcao_vec])
#     df_detalhar = df_detalhar.sort_values(
#         by=["CODIGO DO VEICULO", "DATA INICIO SERVICO"]
#     )

#     # Dias entre OS
#     df_detalhar["DATA_DT"] = pd.to_datetime(
#         df_detalhar["DATA INICIO SERVICO"], errors="coerce"
#     )
#     df_detalhar["DIAS_ENTRE_OS_PROBLEMA"] = (
#         df_detalhar.groupby("problem_no")["DATA_DT"].diff().dt.days
#     )
#     df_detalhar["DIAS_ENTRE_OS_PROBLEMA"] = df_detalhar[
#         "DIAS_ENTRE_OS_PROBLEMA"
#     ].fillna(0)

#     df_detalhar["DIAS_ENTRE_OS"] = df_detalhar["DATA_DT"].diff().dt.days
#     df_detalhar["DIAS_ENTRE_OS"] = df_detalhar["DIAS_ENTRE_OS"].fillna(0)

#     df_detalhar["SOMA_DIAS_MSM_PROB"] = df_detalhar.groupby("problem_no")[
#         "DIAS_ENTRE_OS"
#     ].transform("sum")

#     # Gera NaNs
#     df_detalhar["TOTAL_DE_OS"] = df_detalhar["TOTAL_DE_OS"]
#     df_detalhar = df_detalhar.fillna("-")

#     # Formata datas
#     df_detalhar["DIA_INICIO"] = pd.to_datetime(
#         df_detalhar["DATA INICIO SERVICO"]
#     ).dt.strftime("%d/%m/%Y %H:%M")
#     df_detalhar["DIA_TERMINO"] = pd.to_datetime(
#         df_detalhar["DATA DE FECHAMENTO DO SERVICO"]
#     ).dt.strftime("%d/%m/%Y %H:%M")

#     # Encontra o colaborador
#     # TODO: Join com colaborador e remover esse codigo
#     for ix, linha in df_detalhar.iterrows():
#         colaborador = linha["COLABORADOR QUE EXECUTOU O SERVICO"]
#         nome_colaborador = "Não encontrado"
#         if colaborador in df_mecanicos["cod_colaborador"].values:
#             nome_colaborador = df_mecanicos[
#                 df_mecanicos["cod_colaborador"] == colaborador
#             ]["nome_colaborador"].values[0]
#             nome_colaborador = re.sub(r"(?<!^)([A-Z])", r" \1", nome_colaborador)

#         df_detalhar.at[ix, "LABEL_COLABORADOR"] = f"{colaborador} - {nome_colaborador}"
#         df_detalhar.at[ix, "LABEL"] = f"{colaborador}"

#     return df_detalhar.to_dict("records")
