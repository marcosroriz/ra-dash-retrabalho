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
from modules.entities_utils import get_mecanicos, get_lista_os, get_oficinas, get_secoes, get_modelos

# Imports específicos
from modules.os.os_service import OSService
import modules.os.graficos as os_graficos
import modules.os.tabelas as os_tabelas

##############################################################################
# LEITURA DE DADOS ###########################################################
##############################################################################
# Conexão com os bancos
pgDB = PostgresSingleton.get_instance()
pgEngine = pgDB.get_engine()

# Cria o serviço
os_service = OSService(pgEngine)

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


# Função para validar o input
def input_valido_tela_os(datas, min_dias, lista_modelos, lista_oficinas, lista_os):
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
def corrrige_input(lista, termo_all="TODAS"):
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
    Output("input-select-modelo-veiculos-visao-os", "value"),
    Input("input-select-modelo-veiculos-visao-os", "value"),
)
def corrige_input_modelos_tela_os(lista_modelos):
    return corrrige_input(lista_modelos, "TODOS")


@callback(
    Output("input-select-oficina-visao-os", "value"),
    Input("input-select-oficina-visao-os", "value"),
)
def corrige_input_oficinas_tela_os(lista_oficinas):
    return corrrige_input(lista_oficinas, "TODAS")


# @callback(
#     Output("input-select-ordens-servico-visao-os", "value"),
#     Input("input-select-ordens-servico-visao-os", "value"),
# )
# def corrige_input_ordem_servico_tela_os(lista_os):
#     return corrrige_input(lista_os, "TODAS")

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
            Input("input-select-modelo-veiculos-visao-os", "value"),
            Input("input-select-oficina-visao-os", "value"),
            Input("input-select-ordens-servico-visao-os", "value"),
        ],
    )
    def atualiza_labels_inputs(datas, min_dias, lista_modelos, lista_oficinas, lista_os):
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

        return [dmc.Group(labels_antes + datas_label + min_dias_label + lista_oficinas_labels + lista_modelos_labels + lista_os_labels)]

    # Cria o componente
    return dmc.Group(id=f"{campo}-labels", children=[])


##############################################################################
# Callback para cálculo do estado ############################################
##############################################################################


@callback(
    Output("store-dados-os", "data"),
    [
        Input("input-intervalo-datas-os", "value"),
        Input("input-select-dias-os-retrabalho", "value"),
        Input("input-select-modelo-veiculos-visao-os", "value"),
        Input("input-select-oficina-visao-os", "value"),
        Input("input-select-ordens-servico-visao-os", "value"),
    ],
    running=[(Output("loading-overlay-guia-os", "visible"), True, False)],
)
def computa_retrabalho(datas, min_dias, lista_modelos, lista_oficinas, lista_os):
    dados_vazios = {
        "df_os": pd.DataFrame().to_dict("records"),
        "vazio": True,
    }

    # Valida input
    if not input_valido_tela_os(datas, min_dias, lista_modelos, lista_oficinas, lista_os):
        return dados_vazios

    # Obtém dados das os
    df_os = os_service.obtem_dados_os_sql(datas, min_dias, lista_modelos, lista_oficinas, lista_os)

    return {
        "df_os": df_os.to_dict("records"),
        "vazio": df_os.empty,
    }


##############################################################################
# Callbacks para os gráficos #################################################
##############################################################################


# Callback para o grafico de síntese do retrabalho
@callback(Output("graph-pizza-sintese-retrabalho-os", "figure"), Input("store-dados-os", "data"))
def plota_grafico_pizza_sintese_os(store_payload):
    if store_payload["vazio"]:
        return go.Figure()

    # Obtem os dados
    df_os_raw = pd.DataFrame(store_payload["df_os"])

    # Computa sintese
    estatistica_retrabalho = os_service.get_sintese_os(df_os_raw)

    # Prepara os dados para o gráfico
    labels = ["Correções de Primeira", "Correções Tardias", "Retrabalhos"]
    values = [
        estatistica_retrabalho["total_correcao_primeira"],
        estatistica_retrabalho["total_correcao_tardia"],
        estatistica_retrabalho["total_retrabalho"],
    ]

    # Gera o gráfico
    fig = os_graficos.gerar_grafico_pizza_sinteze_os(df_os_raw, labels, values)

    return fig


# Callback para o grafico cumulativo de retrabalho
@callback(Output("graph-retrabalho-cumulativo-os", "figure"), Input("store-dados-os", "data"))
def plota_grafico_cumulativo_retrabalho_os(store_payload):
    if store_payload["vazio"]:
        return go.Figure()

    # Obtem os dados
    df_os_raw = pd.DataFrame(store_payload["df_os"])

    # Computa os dados
    df_os_cumulativo = os_service.get_tempo_cumulativo_para_retrabalho(df_os_raw)

    # Gera o gráfico
    fig = os_graficos.gerar_grafico_cumulativo_os(df_os_cumulativo)

    return fig


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
                                        dbc.Col(DashIconify(icon="vaadin:lines-list", width=45), width="auto"),
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
                                                        id="input-select-modelo-veiculos-visao-os",
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
                                                        id="input-select-oficina-visao-os",
                                                        options=[{"label": os["LABEL"], "value": os["LABEL"]} for os in lista_todas_oficinas],
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
                                                        id="input-select-ordens-servico-visao-os",
                                                        options=[{"label": os["LABEL"], "value": os["LABEL"]} for os in lista_todas_os],
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
        dcc.Store(id="store-dados-os"),
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
    ]
)

##############################################################################
# Registro da página #########################################################
##############################################################################
dash.register_page(__name__, name="OS", path="/retrabalho-por-os", icon="vaadin:lines-list")
