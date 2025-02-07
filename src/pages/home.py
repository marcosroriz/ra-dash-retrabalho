#!/usr/bin/env python
# coding: utf-8

# Dashboard que lista o retrabalho de uma ou mais OS

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
from modules.entities_utils import get_mecanicos, get_lista_os, get_oficinas, get_secoes

# Imports específicos
from modules.home.home_service import HomeService
import modules.home.graficos as home_graficos
import modules.home.tabelas as home_tabelas

##############################################################################
# LEITURA DE DADOS ###########################################################
##############################################################################
# Conexão com os bancos
pgDB = PostgresSingleton.get_instance()
pgEngine = pgDB.get_engine()

# Cria o serviço
home_service = HomeService(pgEngine)

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

# Obtem a lista de OS
df_lista_os = get_lista_os(pgEngine)
lista_todas_os = df_lista_os.to_dict(orient="records")
lista_todas_os.insert(0, {"LABEL": "TODAS"})


##############################################################################
# CALLBACKS ##################################################################
##############################################################################

##############################################################################
# Callbacks para os inputs ###################################################
##############################################################################


# Função para validar o input
def input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os):
    if datas is None or not datas or None in datas or min_dias is None:
        return False

    if lista_oficinas is None or not lista_oficinas or None in lista_oficinas:
        return False

    if lista_secaos is None or not lista_secaos or None in lista_secaos:
        return False

    if lista_os is None or not lista_os or None in lista_os:
        return False

    return True


# Corrige o input para garantir que "TODAS" não seja selecionado junto com outras opções
def corrige_input(lista):
    # Caso 1: Nenhuma opcao é selecionada, reseta para "TODAS"
    if not lista:
        return ["TODAS"]

    # Caso 2: Se "TODAS" foi selecionado após outras opções, reseta para "TODAS"
    if len(lista) > 1 and "TODAS" in lista[1:]:
        return ["TODAS"]

    # Caso 3: Se alguma opção foi selecionada após "TODAS", remove "TODAS"
    if "TODAS" in lista and len(lista) > 1:
        return [value for value in lista if value != "TODAS"]

    # Por fim, se não caiu em nenhum caso, retorna o valor original
    return lista


@callback(
    Output("input-select-oficina-visao-geral", "value"),
    Input("input-select-oficina-visao-geral", "value"),
)
def corrige_input_oficina(lista_oficinas):
    return corrige_input(lista_oficinas)


@callback(
    Output("input-select-secao-visao-geral", "value"),
    Input("input-select-secao-visao-geral", "value"),
)
def corrige_input_secao(lista_secaos):
    return corrige_input(lista_secaos)


@callback(
    [
        Output("input-select-ordens-servico-visao-geral", "options"),
        Output("input-select-ordens-servico-visao-geral", "value"),
    ],
    [
        Input("input-select-ordens-servico-visao-geral", "value"),
        Input("input-select-secao-visao-geral", "value"),
    ],
)
def corrige_input_ordem_servico(lista_os, lista_secaos):
    # Vamos pegar as OS possíveis para as seções selecionadas
    df_lista_os_secao = df_lista_os

    if "TODAS" not in lista_secaos:
        df_lista_os_secao = df_lista_os_secao[df_lista_os_secao["SECAO"].isin(lista_secaos)]

    # Essa rotina garante que, ao alterar a seleção de oficinas ou seções, a lista de ordens de serviço seja coerente
    lista_os_possiveis = df_lista_os_secao.to_dict(orient="records")
    lista_os_possiveis.insert(0, {"LABEL": "TODAS"})

    lista_options = [{"label": os["LABEL"], "value": os["LABEL"]} for os in lista_os_possiveis]

    # OK, algor vamos remover as OS que não são possíveis para as seções selecionadas
    if "TODAS" not in lista_os:
        df_lista_os_atual = df_lista_os_secao[df_lista_os_secao["LABEL"].isin(lista_os)]
        lista_os = df_lista_os_atual["LABEL"].tolist()

    return lista_options, corrige_input(lista_os)


##############################################################################
# Callbacks para os gráficos #################################################
##############################################################################


# Callback para o grafico de síntese do retrabalho
@callback(
    Output("graph-pizza-sintese-retrabalho-geral", "figure"),
    [
        Input("input-intervalo-datas-geral", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
        Input("input-select-oficina-visao-geral", "value"),
        Input("input-select-secao-visao-geral", "value"),
        Input("input-select-ordens-servico-visao-geral", "value"),
    ],
)
def plota_grafico_pizza_sintese_geral(datas, min_dias, lista_oficinas, lista_secaos, lista_os):
    # Valida input
    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os):
        return go.Figure()

    # Obtem os dados
    df = home_service.get_sintese_geral(datas, min_dias, lista_oficinas, lista_secaos, lista_os)

    # Prepara os dados para o gráfico
    labels = ["Correções de Primeira", "Correções Tardias", "Retrabalhos"]
    values = [
        df["TOTAL_CORRECAO_PRIMEIRA"].values[0],
        df["TOTAL_CORRECAO_TARDIA"].values[0],
        df["TOTAL_RETRABALHO"].values[0],
    ]

    # Gera o gráfico
    fig = home_graficos.gerar_grafico_pizza_sinteze_geral(df, labels, values)
    return fig


# Callback para o grafico por modelo
@callback(
    Output("graph-visao-geral-por-modelo", "figure"),
    [
        Input("input-intervalo-datas-geral", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
        Input("input-select-oficina-visao-geral", "value"),
        Input("input-select-secao-visao-geral", "value"),
        Input("input-select-ordens-servico-visao-geral", "value"),
    ],
)
def plota_grafico_por_modelo(datas, min_dias, lista_oficinas, lista_secaos, lista_os):
    # Valida input
    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os):
        return go.Figure()

    # Obtem os dados
    df = home_service.get_retrabalho_por_modelo(datas, min_dias, lista_oficinas, lista_secaos, lista_os)

    # Gera o gráfico
    fig = home_graficos.gerar_grafico_retrabalho_por_modelo(df)

    return fig


# Callbacks para o grafico de evolução do retrabalho por oficina
@callback(
    Output("graph-evolucao-retrabalho-por-garagem-por-mes", "figure"),
    [
        Input("input-intervalo-datas-geral", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
        Input("input-select-oficina-visao-geral", "value"),
        Input("input-select-secao-visao-geral", "value"),
        Input("input-select-ordens-servico-visao-geral", "value"),
    ],
)
def plota_grafico_evolucao_retrabalho_por_oficina_por_mes(datas, min_dias, lista_oficinas, lista_secaos, lista_os):
    # Valida input
    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os):
        return go.Figure()

    # Obtem os dados
    df = home_service.get_evolucao_retrabalho_por_oficina_por_mes(
        datas, min_dias, lista_oficinas, lista_secaos, lista_os
    )

    # Gera o gráfico
    fig = home_graficos.gerar_grafico_evolucao_retrabalho_por_oficina_por_mes(df)

    return fig


# Callbacks para o grafico de evolução do retrabalho por seção
@callback(
    Output("graph-evolucao-retrabalho-por-secao-por-mes", "figure"),
    [
        Input("input-intervalo-datas-geral", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
        Input("input-select-oficina-visao-geral", "value"),
        Input("input-select-secao-visao-geral", "value"),
        Input("input-select-ordens-servico-visao-geral", "value"),
    ],
)
def plota_grafico_evolucao_retrabalho_por_secao_por_mes(datas, min_dias, lista_oficinas, lista_secaos, lista_os):
    # Valida input
    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os):
        return go.Figure()

    # Obtem os dados
    df = home_service.get_evolucao_retrabalho_por_secao_por_mes(datas, min_dias, lista_oficinas, lista_secaos, lista_os)

    # Gera o gráfico
    fig = home_graficos.gerar_grafico_evolucao_retrabalho_por_secao_por_mes(df)

    return fig


# Callbacks para o grafico de evolução do retrabalho por nota
@callback(
    Output("graph-evolucao-retrabalho-por-nota-por-mes", "figure"),
    [
        Input("input-intervalo-datas-geral", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
        Input("input-select-oficina-visao-geral", "value"),
        Input("input-select-secao-visao-geral", "value"),
        Input("input-select-ordens-servico-visao-geral", "value"),
    ],
)
def plota_grafico_evolucao_retrabalho_por_nota_por_mes(datas, min_dias, lista_oficinas, lista_secaos, lista_os):
    # Valida input
    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os):
        return go.Figure()

    # Obtem os dados
    df = home_service.get_evolucao_retrabalho_por_nota_por_mes(datas, min_dias, lista_oficinas, lista_secaos, lista_os)

    # Gera o gráfico
    fig = home_graficos.gerar_grafico_evolucao_retrabalho_por_nota_por_mes(df)

    return fig


# Callbacks para o grafico de evolução do retrabalho por nota
@callback(
    Output("graph-evolucao-retrabalho-por-custo-por-mes", "figure"),
    [
        Input("input-intervalo-datas-geral", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
        Input("input-select-oficina-visao-geral", "value"),
        Input("input-select-secao-visao-geral", "value"),
        Input("input-select-ordens-servico-visao-geral", "value"),
    ],
)
def plota_grafico_evolucao_retrabalho_por_nota_por_mes(datas, min_dias, lista_oficinas, lista_secaos, lista_os):
    # Valida input
    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os):
        return go.Figure()

    # Obtem os dados
    df = home_service.get_evolucao_retrabalho_por_custo_por_mes(datas, min_dias, lista_oficinas, lista_secaos, lista_os)

    # Gera o gráfico
    fig = home_graficos.gerar_grafico_evolucao_retrabalho_por_custo_por_mes(df)

    return fig


##############################################################################
# Callbacks para as tabelas ##################################################
##############################################################################


@callback(
    Output("tabela-top-os-retrabalho-geral", "rowData"),
    [
        Input("input-intervalo-datas-geral", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
        Input("input-select-oficina-visao-geral", "value"),
        Input("input-select-secao-visao-geral", "value"),
        Input("input-select-ordens-servico-visao-geral", "value"),
    ],
    running=[(Output("loading-overlay-guia-geral", "visible"), True, False)],
)
def atualiza_tabela_top_os_geral_retrabalho(datas, min_dias, lista_oficinas, lista_secaos, lista_os):
    # Valida input
    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os):
        return []

    # Obtem os dados
    df = home_service.get_top_os_geral_retrabalho(datas, min_dias, lista_oficinas, lista_secaos, lista_os)

    return df.to_dict("records")


@callback(
    Output("tabela-top-os-colaborador-geral", "rowData"),
    [
        Input("input-intervalo-datas-geral", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
        Input("input-select-oficina-visao-geral", "value"),
        Input("input-select-secao-visao-geral", "value"),
        Input("input-select-ordens-servico-visao-geral", "value"),
    ],
)
def atualiza_tabela_top_colaboradores_geral_retrabalho(datas, min_dias, lista_oficinas, lista_secaos, lista_os):
    # Valida input
    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os):
        return []

    # Obtem dados
    df = home_service.get_top_os_colaboradores(datas, min_dias, lista_oficinas, lista_secaos, lista_os)

    return df.to_dict("records")


@callback(
    Output("tabela-top-veiculos-geral", "rowData"),
    [
        Input("input-intervalo-datas-geral", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
        Input("input-select-oficina-visao-geral", "value"),
        Input("input-select-secao-visao-geral", "value"),
        Input("input-select-ordens-servico-visao-geral", "value"),
    ],
)
def atualiza_tabela_top_veiculos_geral_retrabalho(datas, min_dias, lista_oficinas, lista_secaos, lista_os):
    # Valida input
    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os):
        return []

    # Obtem dados
    df = home_service.get_top_veiculos(datas, min_dias, lista_oficinas, lista_secaos, lista_os)

    return df.to_dict("records")


##############################################################################
### Callbacks para os labels #################################################
##############################################################################


def gera_labels_inputs(campo):
    # Cria o callback
    @callback(
        [
            Output(component_id=f"{campo}-labels", component_property="children"),
        ],
        [
            Input("input-select-dias-geral-retrabalho", "value"),
            Input(component_id="input-select-oficina-visao-geral", component_property="value"),
            Input(component_id="input-select-secao-visao-geral", component_property="value"),
            Input(component_id="input-select-ordens-servico-visao-geral", component_property="value"),
        ],
    )
    def atualiza_labels_inputs(min_dias, lista_oficinas, lista_secaos, lista_os):
        labels_antes = [
            # DashIconify(icon="material-symbols:filter-arrow-right", width=20),
            dmc.Badge("Filtro", color="gray", variant="outline"),
        ]
        min_dias_label = [dmc.Badge(f"{min_dias} dias", variant="outline")]
        lista_oficinas_labels = []
        lista_secaos_labels = []
        lista_os_labels = []

        if lista_oficinas is None or not lista_oficinas or "TODAS" in lista_oficinas:
            lista_oficinas_labels.append(dmc.Badge("Todas as oficinas", variant="outline"))
        else:
            for oficina in lista_oficinas:
                lista_oficinas_labels.append(dmc.Badge(oficina, variant="dot"))

        if lista_secaos is None or not lista_secaos or "TODAS" in lista_secaos:
            lista_secaos_labels.append(dmc.Badge("Todas as seções", variant="outline"))
        else:
            for secao in lista_secaos:
                lista_secaos_labels.append(dmc.Badge(secao, variant="dot"))

        if lista_os is None or not lista_os or "TODAS" in lista_os:
            lista_os_labels.append(dmc.Badge("Todas as ordens de serviço", variant="outline"))
        else:
            for os in lista_os:
                lista_os_labels.append(dmc.Badge(f"OS: {os}", variant="dot"))

        return [
            dmc.Group(labels_antes + min_dias_label + lista_oficinas_labels + lista_secaos_labels + lista_os_labels)
        ]

    # Cria o componente
    return dmc.Group(id=f"{campo}-labels", children=[])


##############################################################################
# Registro da página #########################################################
##############################################################################
dash.register_page(__name__, name="Visão Geral", path="/", icon="mdi:bus-alert")


##############################################################################
# Layout #####################################################################
##############################################################################
layout = dbc.Container(
    [
        # Loading
        dmc.LoadingOverlay(
            visible=True,
            id="loading-overlay-guia-geral",
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
                                        dbc.Col(DashIconify(icon="mdi:bus-alert", width=45), width="auto"),
                                        dbc.Col(
                                            html.H1(
                                                [
                                                    "Visão geral do\u00a0",
                                                    html.Strong("retrabalho"),
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
                                                        id="input-intervalo-datas-geral",
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
                                                        id="input-select-dias-geral-retrabalho",
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
                                                    dbc.Label("Oficinas"),
                                                    dcc.Dropdown(
                                                        id="input-select-oficina-visao-geral",
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
                                    md=6,
                                ),
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            html.Div(
                                                [
                                                    dbc.Label("Seções (categorias) de manutenção"),
                                                    dcc.Dropdown(
                                                        id="input-select-secao-visao-geral",
                                                        options=[
                                                            # {"label": "TODAS", "value": "TODAS"},
                                                            # {
                                                            #     "label": "BORRACHARIA",
                                                            #     "value": "MANUTENCAO BORRACHARIA",
                                                            # },
                                                            {
                                                                "label": "ELETRICA",
                                                                "value": "MANUTENCAO ELETRICA",
                                                            },
                                                            # {"label": "GARAGEM", "value": "MANUTENÇÃO GARAGEM"},
                                                            # {
                                                            #     "label": "LANTERNAGEM",
                                                            #     "value": "MANUTENCAO LANTERNAGEM",
                                                            # },
                                                            # {"label": "LUBRIFICAÇÃO", "value": "LUBRIFICAÇÃO"},
                                                            {
                                                                "label": "MECANICA",
                                                                "value": "MANUTENCAO MECANICA",
                                                            },
                                                            # {"label": "PINTURA", "value": "MANUTENCAO PINTURA"},
                                                            # {
                                                            #     "label": "SERVIÇOS DE TERCEIROS",
                                                            #     "value": "SERVIÇOS DE TERCEIROS",
                                                            # },
                                                            # {
                                                            #     "label": "SETOR DE ALINHAMENTO",
                                                            #     "value": "SETOR DE ALINHAMENTO",
                                                            # },
                                                            # {
                                                            #     "label": "SETOR DE POLIMENTO",
                                                            #     "value": "SETOR DE POLIMENTO",
                                                            # },
                                                        ],
                                                        multi=True,
                                                        value=["MANUTENCAO ELETRICA", "MANUTENCAO MECANICA"],
                                                        placeholder="Selecione uma ou mais seções...",
                                                    ),
                                                ],
                                                # className="dash-bootstrap",
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
                                                    dbc.Label("Ordens de Serviço"),
                                                    dcc.Dropdown(
                                                        id="input-select-ordens-servico-visao-geral",
                                                        options=[
                                                            {"label": os["LABEL"], "value": os["LABEL"]}
                                                            for os in lista_todas_os
                                                        ],
                                                        multi=True,
                                                        value=["TODAS"],
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
                            dcc.Graph(id="graph-pizza-sintese-retrabalho-geral"),
                        ]
                    ),
                    md=4,
                ),
            ]
        ),
        # Gráfico de Retrabalho por Modelo
        dmc.Space(h=30),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="mdi:fleet", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Quantitativo da frota que teve problema e retrabalho por modelo",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            gera_labels_inputs("visao-geral-quanti-frota"),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        dcc.Graph(id="graph-visao-geral-por-modelo"),
        dmc.Space(h=40),
        # Graficos de Evolução do Retrabalho por Garagem e Seção
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="fluent:arrow-trending-wrench-20-filled", width=45), width="auto"),
                # dbc.Col(html.H4("Evolução do retrabalho por oficina / mês", className="align-self-center"), width=True),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Evolução do retrabalho por oficina / mês",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            gera_labels_inputs("visao-geral-evolucao-por-oficina"),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        dcc.Graph(id="graph-evolucao-retrabalho-por-garagem-por-mes"),
        dmc.Space(h=40),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="fluent:arrow-trending-text-20-filled", width=45), width="auto"),
                # dbc.Col(html.H4("Evolução do retrabalho por seção / mês", className="align-self-center"), width=True),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Evolução do retrabalho por seção / mês",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            gera_labels_inputs("visao-geral-evolucao-por-secao"),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        dcc.Graph(id="graph-evolucao-retrabalho-por-secao-por-mes"),
        dmc.Space(h=40),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="fluent:arrow-trending-sparkle-20-filled", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Evolução da nota do retrabalho por mês",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            gera_labels_inputs("visao-geral-evolucao-por-nota"),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        dcc.Graph(id="graph-evolucao-retrabalho-por-nota-por-mes"),
        dmc.Space(h=40),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="hugeicons:search-dollar", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Evolução do custo (peças) do retrabalho por mês",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            gera_labels_inputs("visao-geral-evolucao-por-custo"),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        dcc.Graph(id="graph-evolucao-retrabalho-por-custo-por-mes"),
        dmc.Space(h=40),
        # Tabela com as estatísticas gerais de Retrabalho
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="fluent:line-horizontal-4-search-16-filled", width=45), width="auto"),
                # dbc.Col(html.H4("Detalhamento por tipo de OS (serviço)", className="align-self-center"), width=True),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Detalhamento por tipo de OS (serviço)",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            gera_labels_inputs("visao-geral-tabela-tipo-os"),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        dmc.Space(h=20),
        dag.AgGrid(
            # enableEnterpriseModules=True,
            id="tabela-top-os-retrabalho-geral",
            columnDefs=home_tabelas.tbl_top_os_geral_retrabalho,
            rowData=[],
            defaultColDef={"filter": True, "floatingFilter": True},
            columnSize="autoSize",
            dashGridOptions={
                "localeText": locale_utils.AG_GRID_LOCALE_BR,
            },
            style={"height": 600},
        ),
        dmc.Space(h=40),
        # Tabela com as estatísticas gerais por Colaborador
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="mdi:account-wrench", width=45), width="auto"),
                # dbc.Col(
                #     html.H4("Detalhamento por colaborador das OSs escolhidas", className="align-self-center"),
                #     width=True,
                # ),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Detalhamento por colaborador das OSs escolhidas",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            gera_labels_inputs("visao-geral-tabela-colaborador-os"),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        dmc.Space(h=20),
        dag.AgGrid(
            id="tabela-top-os-colaborador-geral",
            columnDefs=home_tabelas.tbl_top_colaborador_geral_retrabalho,
            rowData=[],
            defaultColDef={"filter": True, "floatingFilter": True},
            columnSize="autoSize",
            dashGridOptions={
                "localeText": locale_utils.AG_GRID_LOCALE_BR,
            },
            style={"height": 600},
        ),
        dmc.Space(h=20),
        dag.AgGrid(
            id="tabela-top-veiculos-geral",
            columnDefs=home_tabelas.tbl_top_colaborador_geral_retrabalho,
            rowData=[],
            defaultColDef={"filter": True, "floatingFilter": True},
            columnSize="autoSize",
            dashGridOptions={
                "localeText": locale_utils.AG_GRID_LOCALE_BR,
            },
            style={"height": 600},
        ),
        dmc.Space(h=40),
    ]
)
