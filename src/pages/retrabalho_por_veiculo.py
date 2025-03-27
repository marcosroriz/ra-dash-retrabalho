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
from modules.veiculos.tabelas import *
from modules.sql_utils import *
from modules.veiculos.inputs import *
from modules.veiculos.graficos import *
from modules.veiculos.veiculo_service import *
from modules.veiculos.helps import HelpsVeiculos

##############################################################################
# LEITURA DE DADOS ###########################################################
##############################################################################
# Conexão com os bancos
pgDB = PostgresSingleton.get_instance()
pgEngine = pgDB.get_engine()

# Cria o serviço
home_service_veiculos = VeiculoService(pgEngine)

# Colaboradores / Mecânicos
df_mecanicos = get_mecanicos(pgEngine)

# Obtem a lista de OS
df_lista_os = get_lista_os(pgEngine)
lista_todas_os = df_lista_os.to_dict(orient="records")
lista_todas_os.insert(0, {"LABEL": "TODAS"})

df_lista_modelos = get_modelos(pgEngine)
lista_todos_modelos = df_lista_modelos.to_dict(orient="records")
lista_todos_modelos.insert(0, {"LABEL": "TODOS", "MODELO": "TODOS"})


        # Input("input-intervalo-datas-por-veiculo", "value"),
        # Input("input-select-dias-geral-retrabalho", "value"),
        # Input("input-select-oficina-visao-geral", "value"),
        # Input("input-select-secao-visao-geral", "value"),
        # Input("input-select-ordens-servico-visao-geral-veiculos", "value"),
        # Input("input-select-veiculos", "value"),




def gera_labels_inputs_veiculos(campo):
    # Cria o callback
    @callback(
        [
            Output(component_id=f"{campo}-labels", component_property="children"),
        ],
        [
            Input("input-select-dias-geral-retrabalho", "value"),
            Input(component_id="input-select-oficina-visao-geral", component_property="value"),
            Input(component_id="input-select-secao-visao-geral", component_property="value"),
            Input(component_id="input-select-ordens-servico-visao-geral-veiculos", component_property="value"),
            Input(component_id="input-select-veiculos", component_property="value"),
        ],
    )
    def atualiza_labels_inputs(min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
        lista_veiculos = [lista_veiculos]
        labels_antes = [
            # DashIconify(icon="material-symbols:filter-arrow-right", width=20),
            dmc.Badge("Filtro", color="gray", variant="outline"),
        ]
        min_dias_label = [dmc.Badge(f"{min_dias} dias", variant="outline")]
        lista_oficinas_labels = []
        lista_secaos_labels = []
        lista_os_labels = []
        lista_veiculos_labels = []

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
            
        if lista_veiculos is None or not lista_veiculos or "TODAS" in lista_veiculos:
            lista_veiculos_labels.append(dmc.Badge("Todas os veículos", variant="outline"))
        else:
            for os in lista_veiculos:
                lista_veiculos_labels.append(dmc.Badge(f"VEICULO: {os}", variant="dot"))
        return [
            dmc.Group(labels_antes + min_dias_label + lista_oficinas_labels + lista_secaos_labels + lista_os_labels + lista_veiculos_labels)
        ]

    # Cria o componente
    return dmc.Group(id=f"{campo}-labels", children=[])

##############################################################################
# Registro da página #########################################################
##############################################################################
dash.register_page(__name__, name="Veículo", path="/retrabalho-por-veiculo", icon="mdi:bus-alert")

##############################################################################
# Layout #####################################################################
##############################################################################
layout = dbc.Container(
    [
        # Loading
        dmc.LoadingOverlay(
            visible=True,
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
                                        dbc.Col(DashIconify(icon="mdi:bus-alert", width=45), width="auto"),
                                        dbc.Col(
                                            html.H1(
                                                [
                                                    "Retrabalho por\u00a0",
                                                    html.Strong("veículo"),
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
                                                        id="input-intervalo-datas-por-veiculo",
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
                                                    dbc.Label("Modelos"),
                                                    dcc.Dropdown(
                                                        id="input-select-modelos",
                                                        options=[
                                                            {
                                                                "label": os["MODELO"], 
                                                                "value": os["MODELO"]
                                                            }
                                                            for os in lista_todos_modelos
                                                        ],
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
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            html.Div(
                                                [
                                                    dbc.Label("Veículos"),
                                                    dcc.Dropdown(
                                                        id="input-select-veiculos",
                                                        multi=False,
                                                        placeholder="Selecione um ou mais veículos...",
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
                                                    dbc.Label("Oficinas"),
                                                    dcc.Dropdown(
                                                        id="input-select-oficina-visao-geral",
                                                        options=[
                                                            {"label": "TODAS", "value": "TODAS"},
                                                            {
                                                                "label": "GARAGEM CENTRAL",
                                                                "value": "GARAGEM CENTRAL - RAL",
                                                            },
                                                            {
                                                                "label": "GARAGEM NOROESTE",
                                                                "value": "GARAGEM NOROESTE - RAL",
                                                            },
                                                            {
                                                                "label": "GARAGEM SUL",
                                                                "value": "GARAGEM SUL - RAL",
                                                            },
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
                                                            {"label": "TODAS", "value": "TODAS"},
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
                                                        id="input-select-ordens-servico-visao-geral-veiculos",
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
                            dmc.Space(h=30),
                            # Gráfico de pizza com a relação entre Retrabalho e Correção
                            dcc.Graph(id="graph-pizza-sintese-retrabalho-geral_veiculo"),
                        ]
                    ),
                    md=4,
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
                                                dmc.Title(id="indicador-porcentagem-retrabalho-veiculo", order=2),
                                                DashIconify(
                                                    icon="mdi:bus-alert",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("% retrabalho"),
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
                                                    id="indicador-porcentagem-correcao-primeira",
                                                    order=2,
                                                ),
                                                DashIconify(
                                                    icon="ic:round-gps-fixed",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("% correção de primeira"),
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
                                                dmc.Title(id="indicador-relacao-os-problema", order=2),
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
                                    dbc.CardFooter("Relaçao OS/problema"),
                                ],
                                class_name="card-box-shadow",
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
                                                    id="indicador-posicao-relaçao-retrabalho",
                                                    order=2,
                                                ),
                                                DashIconify(
                                                    icon="ic:round-sort",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("Ranking do veículo % retrabalho/geral"),
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
                                                    id="indicador-posição-veiculo-correção-primeira",
                                                    order=2,
                                                ),
                                                DashIconify(
                                                    icon="ic:round-sort",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("Ranking do veiculo % correção de primeira/geral"),
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
                                                dmc.Title(id="indicador-posição-veiculo-relaçao-osproblema", order=2),
                                                DashIconify(
                                                    icon="ic:round-sort",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("Posição veiculo relaçao OS/Problema"),
                                ],
                                class_name="card-box-shadow",
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
                                                    id="indicador-posicao-relaçao-retrabalho-modelo",
                                                    order=2,
                                                ),
                                                DashIconify(
                                                    icon="ic:round-sort",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("Ranking do veículo % retrabalho/modelo"),
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
                                                    id="indicador-posição-veiculo-correção-primeira-modelo",
                                                    order=2,
                                                ),
                                                DashIconify(
                                                    icon="ic:round-sort",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("Ranking do veiculo % correção de primeira/modelo"),
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
                                                dmc.Title(id="indicador-posição-veiculo-relaçao-osproblema-modelo", order=2),
                                                DashIconify(
                                                    icon="ic:round-sort",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("Posição veiculo OS/Problema modelo"),
                                ],
                                class_name="card-box-shadow",
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
                                                    id="indicador-pecas-totais",
                                                    order=2,
                                                ),
                                                DashIconify(
                                                    icon="mdi:cog",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("Valor total de peças"),
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
                                                    id="indicador-pecas-mes",
                                                    order=2,
                                                ),
                                                DashIconify(
                                                    icon="mdi:wrench",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("Valor total de peças/mês"),
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
                                                dmc.Title(id="indicador-ranking-pecas", order=2),
                                                DashIconify(
                                                    icon="mdi:podium",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("Ranking do valor das peças dentro do período"),
                                ],
                                class_name="card-box-shadow",
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
                                                    id="indicador-oss-diferentes",
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
                                    dbc.CardFooter("Números de OSs"),
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
                                                    id="indicador-problemas-diferentes",
                                                    order=2,
                                                ),
                                                DashIconify(
                                                    icon="mdi:tools",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("Serviços diferentes"),
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
                                                dmc.Title(id="indicador-mecanicos-diferentes", order=2),
                                                DashIconify(
                                                    icon="mdi:account-wrench",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("Mecânicos diferentes"),
                                ],
                                class_name="card-box-shadow",
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
                                                    id="indicador-valor-geral-retrabalho",
                                                    order=2,
                                                ),
                                                DashIconify(
                                                    icon="mdi:reload",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("Valor de retrabalho"),
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
                                                    id="indicador-qtd-pecas",
                                                    order=2,
                                                ),
                                                DashIconify(
                                                    icon="mdi:reload-alert",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("Quantidade de peças trocadas"),
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
                                                dmc.Title(id="indicador-ranking-valor-pecas-modelo", order=2),
                                                DashIconify(
                                                    icon="mdi:podium",
                                                    width=48,
                                                    color="black",
                                                ),
                                            ],
                                            justify="space-around",
                                            mt="md",
                                            mb="xs",
                                        ),
                                    ),
                                    dbc.CardFooter("Ranking valor de peça por modelo"),
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
        #dmc.Space(h=40),
        dmc.Space(h=40),
        ##Gráfico de Quantidade de OS / mes
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="fluent:arrow-trending-text-20-filled", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Relaçao de OS / mês",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            gera_labels_inputs_veiculos("evolucao-os-mes-veiculo"),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        dcc.Graph(id="graph-evolucao-os-mes-veiculo"),
        dmc.Space(h=40),
        # Graficos de Evolução do Retrabalho por Garagem e Seção
        dmc.Space(h=30),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="fluent:arrow-trending-wrench-20-filled", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Relações de retrabalho",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            gera_labels_inputs_veiculos("evolucao-retrabalho-por-garagem-por-mes-veiculos"),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        dcc.Graph(id="graph-evolucao-retrabalho-por-garagem-por-mes-veiculos"),
        dmc.Space(h=40),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="fluent:arrow-trending-text-20-filled", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Relações de retrabalho / mês / seção",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            gera_labels_inputs_veiculos("evolucao-retrabalho-por-secao-por-mes-veiculos"),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        dcc.Graph(id="graph-evolucao-retrabalho-por-secao-por-mes-veiculos"),
        dmc.Space(h=40),
        #Grafico geral de peças
        dmc.Space(h=30),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="fluent:arrow-trending-wrench-20-filled", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Valor das peças trocadas por mês",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            gera_labels_inputs_veiculos("pecas-trocadas-por-mes"),
                        ]
                    ),
                    width=True,
                ),
                
            ],
            align="center",
        ),
        dcc.Graph(id="graph-pecas-trocadas-por-mes"),
        dmc.Space(h=20),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="mdi:cog-outline", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Tabela de peças por OS",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            dbc.Col(gera_labels_inputs_veiculos("pecas-substituidas-por-os-filtro"), width=True),
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
            id="tabela-pecas-substituidas",
            columnDefs=[
                {"field": "OS", "minWidth": 100},
                {"field": "EQUIPAMENTO", "minWidth": 100},
                {"field": "DESCRICAO DO SERVICO","headerName": "DESCRIÇÃO DO SERVICO", "minWidth": 100},
                {"field": "MODELO", "minWidth": 300},
                {"field": "PRODUTO", "minWidth": 350},
                {"field": "QUANTIDADE", "minWidth": 100},
                {"field": "VALOR", "minWidth": 100,
                     "type": ["numericColumn"],
                     "valueFormatter": {"function": "'R$' + Number(params.value).toFixed(2).toLocaleString()"},
                     "sort": "desc"
                },
                {"field": "DATA", "minWidth": 130},
                {"field": "retrabalho","headerName": "RETRABALHO", "minWidth": 130}
            ],
            rowData=[],
            defaultColDef={"filter": True, "floatingFilter": True},
            columnSize="autoSize",
            style={"height": 400, "resize": "vertical", "overflow": "hidden"},
        ),
        dmc.Space(h=40),   
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="mdi:tools", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Tabela de peças por descrição de seviço",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            dbc.Col(gera_labels_inputs_veiculos("tabela-de-pecas-por-descricao-filtros"), width=True),
                            dbc.Col(
                            html.Div(
                                    [
                                        html.Button(
                                            "Exportar para Excel",
                                            id="btn-exportar-descricao-retrabalho",
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
                                        dcc.Download(id="download-excel-tabela-retrabalho-por-descrição-servico"),
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
            id="tabela-descricao-de-servico",
            columnDefs=tbl_top_os_geral_retrabalho,
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
        
# Indicadores

    ]
)


##############################################################################
# CALLBACKS ##################################################################
##############################################################################

# VEÍCULOS DO MODELO SELECIONADO
@callback(
    [
        Output("input-select-veiculos", "options"),
        Output("input-select-veiculos", "value"),
    ],
    Input("input-select-modelos", "value")
)
def atualizar_veiculos(modelos_selecionados):
    if modelos_selecionados is None:
        return [], []  # Retorna uma lista vazia de opções e sem valor padrão
    lista_todos_veiculos = home_service_veiculos.atualizar_veiculos_func([modelos_selecionados])
    # Formatar corretamente para o Dropdown
    options = [
        {"label": f'{veiculo["VEICULO"]} ({veiculo["MODELO"]})', "value": veiculo["VEICULO"]}
        for veiculo in lista_todos_veiculos
    ]
    
    #DESCOMENTAR CASO USE A OPÇÃO MULTIPLA DO DROPDOWN
    # Selecionar o segundo item como padrão, se existir
    #value = [options[1]["value"]] if len(options) > 1 else []

    #COMENTAR CASO USE A OPÇÃO MULTIPLA DO DROPDOWN
    # Selecionar o segundo item como padrão, se existir
    value = options[1]["value"] if len(options) > 1 else None  # None para evitar erro
    return options, value

# SERVIÇOS DO VEÍCULO SELECIONADO
@callback(
    Output("input-select-ordens-servico-visao-geral-veiculos", "options"),
    [
        Input("input-intervalo-datas-por-veiculo", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
        Input("input-select-oficina-visao-geral", "value"),
        Input("input-select-secao-visao-geral", "value"),
        Input("input-select-veiculos", "value"),
    ]
)
def atualizar_servicos(datas, min_dias, lista_oficinas, lista_secaos, lista_veiculos):
    lista_veiculos = [lista_veiculos]
    if not input_valido4(datas, min_dias, lista_oficinas, lista_secaos, lista_veiculos):
        return []  # Retorna uma lista vazia de opções se lista_veiculos for None  
    # Chama a função atualizar_servicos_func para obter a lista de serviços
    lista_servicos = home_service_veiculos.atualizar_servicos_func(
        datas, min_dias, lista_oficinas, lista_secaos, lista_veiculos
    )
    
    # Formatar para o formato de opções do dropdown
    options_servicos = [{"label": servico, "value": servico} for servico in lista_servicos]
    
    # Adicionar opção "TODAS" no início
    options_servicos.insert(0, {"label": "TODAS", "value": "TODAS"})  

    return options_servicos

# GRÁFICO DE PIZZA GERAL
@callback(
    [Output("graph-pizza-sintese-retrabalho-geral_veiculo", "figure"),
    Output("indicador-porcentagem-retrabalho-veiculo", "children"),
    Output("indicador-porcentagem-correcao-primeira", "children")],

    [
        Input("input-intervalo-datas-por-veiculo", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
        Input("input-select-oficina-visao-geral", "value"),
        Input("input-select-secao-visao-geral", "value"),
        Input("input-select-ordens-servico-visao-geral-veiculos", "value"),
        Input("input-select-veiculos", "value"),
    ],
)
def plota_grafico_pizza_sintese_geral(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
    lista_veiculos = [lista_veiculos]
    # Valida input
    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
        return go.Figure(), "", ""
    total_retrabalho, total_correcao_primeira, labels, values = home_service_veiculos.sintese_geral_fun(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos)
    fig = grafico_pizza_sintese_geral(labels, values)
    return fig, total_retrabalho, total_correcao_primeira

# GRÁFICO DE RETRABALHOS POR VEÍCULOS
@callback(
    Output("graph-evolucao-retrabalho-por-garagem-por-mes-veiculos", "figure"),
    [
        Input("input-intervalo-datas-por-veiculo", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
        Input("input-select-oficina-visao-geral", "value"),
        Input("input-select-secao-visao-geral", "value"),
        Input("input-select-ordens-servico-visao-geral-veiculos", "value"),
        Input("input-select-veiculos", "value"),
    ],
)
def plota_grafico_evolucao_retrabalho_por_veiculo_por_mes(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
    # Valida input
    lista_veiculos = [lista_veiculos]
    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
        return go.Figure()
    df = home_service_veiculos.evolucao_retrabalho_por_veiculo_por_mes_fun(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos)
    fig = gerar_grafico_evolucao_retrabalho_por_veiculo_por_mes(df)
    return fig

# GRÁFICO DO RETRABALHO POR SECAO POR UM ÚNICO VEICULO
@callback(
    Output("graph-evolucao-retrabalho-por-secao-por-mes-veiculos", "figure"),
    [
        Input("input-intervalo-datas-por-veiculo", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
        Input("input-select-oficina-visao-geral", "value"),
        Input("input-select-secao-visao-geral", "value"),
        Input("input-select-ordens-servico-visao-geral-veiculos", "value"),
        Input("input-select-veiculos", "value"),
    ],
)
def plota_grafico_evolucao_retrabalho_por_secao_por_mes(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
    lista_veiculos = [lista_veiculos]
    # Valida input
    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
        return go.Figure()
    df = home_service_veiculos.retrabalho_por_secao_por_mes_fun(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos)
    fig = grafico_evolucao_retrabalho_por_secao_por_mes(df)
    # Exibe o gráfico
    return fig

# GRAFICO DA QUANTIDADE DE OSs, INDICADORES DE : PROBLEMAS DIFERENTES, MECANICOS DIFERENTES, OS DIFERENTES, OS/PROBL, RANKING OS/PROBL
@callback(
    [Output('graph-evolucao-os-mes-veiculo', 'figure'),
     Output("indicador-problemas-diferentes", "children"),
     Output("indicador-mecanicos-diferentes", "children"),
     Output("indicador-oss-diferentes", "children"),
     Output("indicador-relacao-os-problema", "children"),
     Output("indicador-posição-veiculo-relaçao-osproblema", "children"),
     Output("indicador-posição-veiculo-relaçao-osproblema-modelo", "children"),],
    [
        Input("input-intervalo-datas-por-veiculo", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
        Input("input-select-oficina-visao-geral", "value"),
        Input("input-select-secao-visao-geral", "value"),
        Input("input-select-ordens-servico-visao-geral-veiculos", "value"),
        Input("input-select-veiculos", "value"),
    ],
)
def plota_grafico_evolucao_quantidade_os_por_mes(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
    lista_veiculos = [lista_veiculos]
    # Valida input
    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
        return go.Figure(), "", "", "", "", "", ""
    (os_diferentes, mecanicos_diferentes,os_veiculo_filtradas, 
     os_problema, df_soma_mes, df_os_unicas, rk_os_problema_geral,
     rk_os_problema_modelos) = home_service_veiculos.evolucao_quantidade_os_por_mes_fun(datas, min_dias, lista_oficinas, 
                                                                                      lista_secaos, lista_os, lista_veiculos)
    fig = grafico_qtd_os_e_soma_de_os_mes(df_soma_mes, df_os_unicas)
    return fig, os_diferentes, mecanicos_diferentes, os_veiculo_filtradas, os_problema, rk_os_problema_geral, rk_os_problema_modelos

# GRAFICO DA TABELA DE PEÇAS
@callback(
    Output("graph-pecas-trocadas-por-mes", "figure"),
    [
        Input("input-intervalo-datas-por-veiculo", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
        Input("input-select-oficina-visao-geral", "value"),
        Input("input-select-secao-visao-geral", "value"),
        Input("input-select-ordens-servico-visao-geral-veiculos", "value"),
        Input("input-select-veiculos", "value"),
    ],
)
def plota_grafico_pecas_trocadas_por_mes(datas, min_dias, lista_oficinas, lista_secaos, lista_os, equipamentos):
    equipamentos = [equipamentos]
    # Valida input
    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os, equipamentos):
        return go.Figure()
    
    data_inicio_str = datas[0]
    data_fim_str = datas[1]

    if data_inicio_str is None:
            return go.Figure()  # Ou algum valor padrão válido
    if data_fim_str is None:
            return go.Figure()  # Ou algum valor padrão válido
    
    # Garante que equipamentos seja uma lista
    if isinstance(equipamentos, str):
        equipamentos = [equipamentos]
    df_veiculos, df_media_geral, df_media_modelo = home_service_veiculos.pecas_trocadas_por_mes_fun(datas, min_dias, lista_oficinas, lista_secaos, lista_os, equipamentos)
    fig = grafico_tabela_pecas(df_veiculos, df_media_geral, df_media_modelo)
    return fig

# TABELA DE PEÇAS, INDICADORES DE: VALORES DE PECAS, VALOR DE PECAS/MES, RANKING DO VALOR DE PECAS, TOTAL DE PEÇAS
@callback(
   [Output("tabela-pecas-substituidas", "rowData"),
    Output("indicador-pecas-totais", "children"),
    Output("indicador-pecas-mes", "children"),
    Output("indicador-ranking-pecas", "children"),
    Output("indicador-qtd-pecas", "children"),
    ],
    #Input("graph-pecas-trocadas-por-mes", "clickData"),
    [
        Input("input-intervalo-datas-por-veiculo", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
        Input("input-select-oficina-visao-geral", "value"),
        Input("input-select-secao-visao-geral", "value"),
        Input("input-select-ordens-servico-visao-geral-veiculos", "value"),
        Input("input-select-veiculos", "value"),
    ],
    
)
def atualiza_tabela_pecas(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
    lista_veiculos = [lista_veiculos]
    # Valida input
    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
        return [], " ", " ", " ", " "
    df_detalhes_dict, valor_total_veiculos_str, valor_mes_str, rk, numero_pecas_veiculos_total = home_service_veiculos.tabela_pecas_fun(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos)
    return df_detalhes_dict, valor_total_veiculos_str, valor_mes_str, rk, numero_pecas_veiculos_total

# DOWLOAD DA TABELA PEÇAS
@callback(
    Output("download-excel-tabela-pecas", "data"),
    [
        Input("btn-exportar-pecas", "n_clicks"),
        Input("input-intervalo-datas-por-veiculo", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
        Input("input-select-oficina-visao-geral", "value"),
        Input("input-select-secao-visao-geral", "value"),
        Input("input-select-ordens-servico-visao-geral-veiculos", "value"),
        Input("input-select-veiculos", "value"),
    ],
    prevent_initial_call=True
)
def dowload_excel_tabela_peças(n_clicks, datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
    lista_veiculos = [lista_veiculos]
    if not n_clicks or n_clicks <= 0: # Garantir que ao iniciar ou carregar a page, o arquivo não seja baixado
        return dash.no_update
    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
        return dash.no_update
    
    date_now = datetime.now().strftime('%d-%m-%Y')
    timestamp = int(time.time())
    df_detalhes_dict, _, _, _, _ = home_service_veiculos.tabela_pecas_fun(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos)
    df = pd.DataFrame(df_detalhes_dict)

    # Converter a coluna "retrabalho" (supondo que seja essa a coluna correta)
    if "retrabalho" in df.columns:
        df["retrabalho"] = df["retrabalho"].map({True: "SIM", False: "NÃO"})

    excel_data = gerar_excel(df=df)
    return dcc.send_bytes(excel_data, f"tabela-peças-os-{date_now}-{timestamp}.xlsx")


# TABELA DE DESCRIÇÃO DE SERVIÇOS E INDICADO DE VALOR DE RETRABALHO
@callback(
    [Output("tabela-descricao-de-servico", "rowData"),
     Output("indicador-valor-geral-retrabalho", "children"),],

    [
        Input("input-intervalo-datas-por-veiculo", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
        Input("input-select-oficina-visao-geral", "value"),
        Input("input-select-secao-visao-geral", "value"),
        Input("input-select-ordens-servico-visao-geral-veiculos", "value"),
        Input("input-select-veiculos", "value"),
    ],
    
)
def atualiza_tabela_retrabalho_por_descrição_serviço(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculo):
    lista_veiculo = [lista_veiculo]
    # Valida input
    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculo):
        return [], " "

    df_dict, valor_retrabalho = home_service_veiculos.tabela_top_os_geral_retrabalho_fun(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculo)
    return df_dict, valor_retrabalho

# DOWLOAD DA TABELA RETRABALHO POR DESCRIÇÃO DE SERVIÇO
@callback(
    Output("download-excel-tabela-retrabalho-por-descrição-servico", "data"),
    [
        Input("btn-exportar-descricao-retrabalho", "n_clicks"),
        Input("input-intervalo-datas-por-veiculo", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
        Input("input-select-oficina-visao-geral", "value"),
        Input("input-select-secao-visao-geral", "value"),
        Input("input-select-ordens-servico-visao-geral-veiculos", "value"),
        Input("input-select-veiculos", "value"),
    ],
    prevent_initial_call=True
)
def dowload_excel_tabela_retrabalho_por_descrição_servico(n_clicks, datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
    lista_veiculos = [lista_veiculos]
    if not n_clicks or n_clicks <= 0: 
        return dash.no_update
    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
        return dash.no_update
    
    date_now = datetime.now().strftime('%d-%m-%Y')
    timestamp = int(time.time())
    df_dict, _ = home_service_veiculos.tabela_top_os_geral_retrabalho_fun(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos)
    df = pd.DataFrame(df_dict)
    excel_data = gerar_excel(df=df)
    return dcc.send_bytes(excel_data, f"tabela-retrabalho-por-descrição-serviço-{date_now}-{timestamp}.xlsx")

#INDICADOR RANKING DE VALOR DE PEÇAS POR MODELO
@callback(
    [Output("indicador-ranking-valor-pecas-modelo", "children")],
    [
        Input("input-intervalo-datas-por-veiculo", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
        Input("input-select-oficina-visao-geral", "value"),
        Input("input-select-secao-visao-geral", "value"),
        Input("input-select-ordens-servico-visao-geral-veiculos", "value"),
        Input("input-select-veiculos", "value"),
    ],
)
def atualiza_ranking_pecas(datas, min_dias, lista_oficinas, lista_secoes, lista_os, lista_veiculos):
    lista_veiculos = [lista_veiculos]

    if not input_valido3(datas, min_dias, lista_veiculos):
        return [""]
    
    indicador_ranking_pecas_modelos = home_service_veiculos.tabela_ranking_pecas_fun(
        datas, min_dias, lista_oficinas, lista_secoes, lista_os, lista_veiculos
    )
    
    return [indicador_ranking_pecas_modelos]

# RANKING DOS RETRABALHOS DOS VEÍCULOS. INDICADORES DE: POSIÇÃO DE RELAÇÃO RETRABALHO, CORREÇÃO DE PRIMEIRA 
@callback(
    [Output("indicador-posicao-relaçao-retrabalho", "children"),
     Output("indicador-posição-veiculo-correção-primeira","children"),
     Output("indicador-posicao-relaçao-retrabalho-modelo","children"),
     Output("indicador-posição-veiculo-correção-primeira-modelo","children"),],
    [
        Input("input-intervalo-datas-por-veiculo", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
        Input("input-select-oficina-visao-geral", "value"),
        Input("input-select-secao-visao-geral", "value"),
        Input("input-select-ordens-servico-visao-geral-veiculos", "value"),
        Input("input-select-veiculos", "value"),
    ],
    running=[(Output("loading-overlay-guia-por-veiculo", "visible"), True, False)],
)
def ranking_retrabalho_veiculos(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
    lista_veiculos = [lista_veiculos]
    # Valida input
    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
        return "", "", "", ""
    rk_retrabalho_geral, rk_correcao_primeira_geral, rk_retrabalho_modelo, rk_correcao_primeira_modelo = home_service_veiculos.ranking_retrabalho_veiculos_fun(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos)
    return rk_retrabalho_geral, rk_correcao_primeira_geral, rk_retrabalho_modelo, rk_correcao_primeira_modelo