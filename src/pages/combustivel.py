#!/usr/bin/env python
# coding: utf-8

# Dashboard que lista o retrabalho de uma ou mais OS

##############################################################################
# IMPORTS ####################################################################
##############################################################################
# Bibliotecas básicas
from datetime import datetime
import numpy as np
import pandas as pd
import time


# Importar bibliotecas do dash básicas e plotly
import dash
from dash import Dash, html, dcc, callback, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.subplots as sp


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

# Import de arquivos
from modules.entities_utils import *
from modules.combustivel.tabela import *
from modules.sql_utils import *
from modules.veiculos.inputs import *
from modules.veiculos.graficos import *
from modules.veiculos.veiculo_service import *
from modules.veiculos.helps import HelpsVeiculos
from modules.combustivel.combustivel_service import CombustivelService

##############################################################################
# LEITURA DE DADOS ###########################################################
##############################################################################
# Conexão com os bancos
pgDB = PostgresSingleton.get_instance()
pgEngine = pgDB.get_engine()


# Cria o serviço
# home_service_veiculos = VeiculoService(pgEngine)
combus = CombustivelService(pgEngine)

# Colaboradores / Mecânicos
df_mecanicos = get_mecanicos(pgEngine)


# df_lista_modelos = get_modelos(pgEngine)
# lista_todos_modelos = df_lista_modelos.to_dict(orient="records")
# lista_todos_modelos.insert(0, {"MODELO": "TODOS"})

# print(df_lista_modelos)


def gera_labels_inputs_veiculos(campo):
    """Gera labels de filtros baseados nos inputs do usuário para veículos."""

    @callback(
        Output(f"{campo}-labels", "children"),
        [
            Input("input-select-modelos-combustivel", "value"),
            Input("input-select-linhas-combustivel", "value"),
            Input("input-select-sentido-da-linha", "value"),
            Input("input-select-dia", "value"),
        ],
    )
    def atualiza_labels_inputs(lista_modelo, lista_linhas, sentido_linha, dia):
        """Atualiza os labels de acordo com os filtros selecionados."""

        labels_iniciais = [dmc.Badge("Filtro", color="gray", variant="outline")]

        def gerar_badges(lista, texto_todos, prefixo=""):
            """Gera badges com base na lista de filtros."""
            if not lista or "TODOS" in lista:
                return [dmc.Badge(texto_todos, variant="outline")]
            return [dmc.Badge(f"{prefixo}{item}", variant="dot") for item in lista]

        # Gera badges para cada filtro
        lista_modelo_labels = gerar_badges(lista_modelo, "Todos os modelos")
        lista_linhas_labels = gerar_badges(lista_linhas, "Todas as linhas")
        lista_sentido_labels = gerar_badges(sentido_linha, "Ida e volta", "OS: ")
        lista_dia_labels = gerar_badges(dia, "Todos os dias", "DIA: ")

        return [
            dmc.Group(
                labels_iniciais + lista_modelo_labels +
                lista_linhas_labels + lista_sentido_labels + lista_dia_labels
            )
        ]

    return dmc.Group(id=f"{campo}-labels", children=[])


@callback(
    [
        Output("input-select-modelos-combustivel", "options"),
    ],
    [
        Input("input-intervalo-datas-combustivel", "date"),
    ],
)
def corrige_input_modelo(datas):
    # Vamos pegar as OS possíveis para as seções selecionadas
    df_lista_modelo = combus.df_lista_combustivel_modelo(datas)

    # Essa rotina garante que, ao alterar a seleção de oficinas ou seções, a lista de ordens de serviço seja coerente
    lista_modelos_possiveis = df_lista_modelo.to_dict(orient="records")
    lista_modelos_possiveis.insert(0, {"LABEL": "TODOS"})

    lista_options = [{"label": os["LABEL"], "value": os["LABEL"]} for os in lista_modelos_possiveis]

    return [lista_options]


@callback(
    [
        Output("input-select-linhas-combustivel", "options"),
        Output("input-select-linhas-combustivel", "value"),
    ],
    [
        Input("input-intervalo-datas-combustivel", "date"),
        Input("input-select-linhas-combustivel", "value"),
        Input("input-select-modelos-combustivel", "value")
    ],
)
def corrige_input_linha(datas, lista_linhas, lista_modelos):
    # Vamos pegar as OS possíveis para as seções selecionadas
    df_lista_linhas = combus.df_lista_linha_rmtc(datas, lista_modelos)

    # Essa rotina garante que, ao alterar a seleção de oficinas ou seções, a lista de ordens de serviço seja coerente
    lista_modelos_possiveis = df_lista_linhas.to_dict(orient="records")
    lista_modelos_possiveis.insert(0, {"LABEL": "TODAS"})

    lista_options = [{"label": os["LABEL"], "value": os["LABEL"]} for os in lista_modelos_possiveis]

    # OK, algor vamos remover as OS que não são possíveis para as seções selecionadas
    if "TODAS" not in lista_linhas:
        df_lista_os_atual = df_lista_linhas[df_lista_linhas["LABEL"].isin(lista_linhas)]
        lista_linhas = df_lista_os_atual["LABEL"].tolist()

    return lista_options, corrige_input(lista_linhas)

@callback(
    Output("tabela-combustivel", "rowData"), 
    [
        Input("input-intervalo-datas-combustivel", "date"),
        Input("input-select-modelos-combustivel", "value"),
        Input("input-select-linhas-combustivel", "value"),
        Input("input-select-sentido-da-linha", "value"),
        Input("input-select-dia", "value"),
    ],
)
def tabela_visao_geral_combustivel(datas, lista_modelo, lista_linhas, sentido_linha, dia):
    
    if(datas is None):
        return []
    
    return combus.df_tabela_combustivel(
        datas, lista_modelo, lista_linhas, sentido_linha, dia
    ).to_dict("records")

@callback(
    Output("graph-combustivel", "figure"), 
    [
        Input("input-intervalo-datas-combustivel", "date"),
        Input("input-select-modelos-combustivel", "value"),
        Input("input-select-linhas-combustivel", "value"),
        Input("input-select-sentido-da-linha", "value"),
        Input("input-select-dia", "value"),
    ],
)
def grafico_visao_geral_combustivel(datas, lista_modelo, lista_linhas, sentido_linha, dia):
    if(datas is None):
        return []

    grafico = combus.grafico_combustivel(datas, lista_modelo, lista_linhas, sentido_linha, dia)

    return grafico
##############################################################################
# Registro da página #########################################################
##############################################################################
dash.register_page(__name__, name="Combustível", path="/combustivel")

##############################################################################
# Layout #####################################################################
##############################################################################
layout = dbc.Container(
    [
        # Loading
        dmc.LoadingOverlay(
            visible=False,
            id="loading-overlay-guia-por-veiculo",
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
                                        dbc.Col(DashIconify(icon="mdi:gas-station", width=45), width="auto"),
                                        dbc.Col(
                                            html.H1(
                                                [
                                                    html.Strong("Combustível"),
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
                                                    dbc.Label("Data",    style={"display": "block", "margin-bottom": "10px"} ), # Adiciona espaço abaixo do Label),),
                                                    dcc.DatePickerSingle(
                                                        id="input-intervalo-datas-combustivel",
                                                        min_date_allowed=date(2024, 12, 29),  # Data mínima permitida
                                                        max_date_allowed=date.today(),        # Data máxima permitida
                                                        initial_visible_month=date(2024, 12, 29),  # Mês visível por padrão
                                                        date=date(2024, 12, 29),              # Data inicial
                                                        display_format="DD/MM/YYYY",          # Formato de exibição
                                                    ),
                                                    # dcc.DatePickerSingle(
                                                    #     id='input-intervalo-datas-combustivel',
                                                    #     min_date_allowed=date(2024, 12, 29),
                                                    #     max_date_allowed=date.today(),
                                                    #     initial_visible_month=date(2024, 12, 29),
                                                    #     date=date(2024, 12, 29)
                                                    # ),
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
                                                    dbc.Label("Modelos"),
                                                    dcc.Dropdown(
                                                        id="input-select-modelos-combustivel",
                                                        #multi=True,
                                                        value="TODOS", #ANTES ERA ["TODAS"], AGORA COMO É UMA VARIAVEL SÓ NO DROP, ENTÃO SE CONSIDERA APENAS UMA STRIN.
                                                        placeholder="Selecione um ou mais modelos...",
                                                    )
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
                                                    dbc.Label("Linha"),
                                                    dcc.Dropdown(
                                                        id="input-select-linhas-combustivel",
                                                        multi=True,
                                                        value=["TODAS"],
                                                        placeholder="Selecione uma ou mais linhas...",
                                                    )
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
                                                    dbc.Label("Sentido"),
                                                    dcc.Dropdown(
                                                        id="input-select-sentido-da-linha",
                                                        options=[
                                                            {"label": "IDA/VOLTA", "value": "IDA_VOLTA"},
                                                            {
                                                                "label": "IDA",
                                                                "value": "IDA",
                                                            },
                                                            {
                                                                "label": "VOLTA",
                                                                "value": "VOLTA",
                                                            },
                                                        ],
                                                        multi=True,
                                                        value=["IDA_VOLTA"],
                                                        placeholder="Selecione o sentido...",
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
                                                    dbc.Label("Dias"),
                                                    dcc.Checklist(
                                                        id="input-select-dia",
                                                        options=[
                                                            {"label": "Sabado", "value": "SABADO"},
                                                            {"label": "Domingo", "value": "DOMINGO"},
                                                            {"label": "Feriado", "value": "FERIADO"},
                                                            {"label": "Todos", "value": "TODOS"},
                                                        ],
                                                        value=["TODOS"],
                                                        inputStyle={"margin-right": "6px"},
                                                        labelStyle={
                                                            "display": "inline-block",
                                                            "margin-right": "20px",
                                                            "font-weight": "500",
                                                            "cursor": "pointer",
                                                        },
                                                        style={"padding": "10px"},
                                                    ),
                                                ],
                                                className="dash-bootstrap",
                                            ),
                                        ],
                                        body=True,
                                        style={"box-shadow": "0 2px 6px rgba(0, 0, 0, 0.1)", "border-radius": "8px"},
                                    ),
                                    md=12,
                                )
                            ]
                        ),
                    ],
                    md=12,
                ),
            ]
        ),
        dmc.Space(h=30),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="material-symbols:insights", width=45), width="auto"),
                dbc.Col(
                    html.H4("Indicadores", className="align-self-center"),
                ),
                dmc.Space(h=20),
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        dmc.Group(
                                            [
                                                dmc.Title(id="indicador-quantidade-de-viagens", order=2),
                                                DashIconify(
                                                    icon="tabler:road",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("Viagens"),
                                ],
                                class_name="card-box-shadow",
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
                                                    id="indicador-quantidade-de-veiculos-diferentes",
                                                    order=2,
                                                ),
                                                DashIconify(
                                                    icon="mdi:bus",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("Veículos diferentes"),
                                ],
                                class_name="card-box-shadow",
                            ),
                            md=4,
                        ),
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        dmc.Group(
                                            [
                                                dmc.Title(id="indicador-quantidade-de-veiculos", order=2),
                                                DashIconify(
                                                    icon="mdi:car-multiple",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("Quantidade de veículos"),
                                ],
                                class_name="card-box-shadow",
                            ),
                            md=4,
                        ),
                    ]
                ),
            ]
        ),
        dbc.Row(dmc.Space(h=40)),
        #Grafico geral de peças
        dmc.Space(h=30),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="mdi:trending-down", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Gráfico: Consumo de combustível por linha",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                        ]
                    ),
                    width=True,
                ),
                
            ],
            align="center",
        ),
        dcc.Graph(id="graph-combustivel"), #Trocar ID aqui quando o grafico estiver pronto
        dmc.Space(h=40),   
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="mdi:cog-outline", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Tabela de linhas",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            dbc.Col(gera_labels_inputs_veiculos("input-geral-combustivel-1"), width=True),
                            dbc.Col(
                                        html.Div(
                                            [
                                                html.Button(
                                                    "Exportar para Excel",
                                                    id="btn-exportar-pecas",
                                                    n_clicks=0,
                                                    style={
                                                        "background-color": "#007bff",  # Azul
                                                        "color": "white",
                                                        "border": "none",
                                                        "padding": "10px 20px",
                                                        "border-radius": "8px",
                                                        "cursor": "pointer",
                                                        "font-size": "16px",
                                                        "font-weight": "bold",
                                                    },
                                                ),
                                                dcc.Download(id="download-excel-tabela-pecas"),
                                            ],
                                            style={"text-align": "right"},
                                        ),
                                        width="auto",
                                    ),
                        ]
                    ),
                    width=True,
                ),
                
            ],
            align="center",
        ),
        dmc.Space(h=20),
        dag.AgGrid(
            enableEnterpriseModules=True,
            id="tabela-combustivel",
            columnDefs=tbl_dados_das_linhas,
            rowData=[],
            defaultColDef={"filter": True, "floatingFilter": True},
            columnSize="autoSize",
            dashGridOptions={
                "localeText": locale_utils.AG_GRID_LOCALE_BR,
            },
            style={"height": 400, "resize": "vertical", "overflow": "hidden"},
        ),
        dmc.Space(h=40),
        dmc.Space(h=60),

    ]
)


##############################################################################
# CALLBACKS ##################################################################
##############################################################################

# # VEÍCULOS DO MODELO SELECIONADO
# @callback(
#     [
#         Output("input-linha-selecionada", "options"),
#         Output("input-linha-selecionada", "value"),
#     ],
#     Input("input-linha-selecionada", "value")
# )
# def atualizar_veiculos(modelos_selecionados):
#     if modelos_selecionados is None:
#         return [], []  # Retorna uma lista vazia de opções e sem valor padrão
#     lista_todos_veiculos = home_service_veiculos.atualizar_veiculos_func([modelos_selecionados])
#     # Formatar corretamente para o Dropdown
#     options = [
#         {"label": f'{veiculo["VEICULO"]} ({veiculo["MODELO"]})', "value": veiculo["VEICULO"]}
#         for veiculo in lista_todos_veiculos
#     ]
    
#     #DESCOMENTAR CASO USE A OPÇÃO MULTIPLA DO DROPDOWN
#     # Selecionar o segundo item como padrão, se existir
#     #value = [options[1]["value"]] if len(options) > 1 else []

#     #COMENTAR CASO USE A OPÇÃO MULTIPLA DO DROPDOWN
#     # Selecionar o segundo item como padrão, se existir
#     value = options[1]["value"] if len(options) > 1 else None  # None para evitar erro
#     return options, value