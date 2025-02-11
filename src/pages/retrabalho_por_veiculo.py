#!/usr/bin/env python
# coding: utf-8

# Dashboard que lista o retrabalho de uma ou mais OS

##############################################################################
# IMPORTS ####################################################################
##############################################################################
# Bibliotecas básicas
from datetime import date
import numpy as np
import pandas as pd

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
from modules.veiculos.home_service import *
from modules.veiculos.helps import HelpsVeiculos

##############################################################################
# LEITURA DE DADOS ###########################################################
##############################################################################
# Conexão com os bancos
pgDB = PostgresSingleton.get_instance()
pgEngine = pgDB.get_engine()

# Colaboradores / Mecânicos
df_mecanicos = get_mecanicos(pgEngine)

# Obtem a lista de OS
df_lista_os = get_lista_os(pgEngine)
lista_todas_os = df_lista_os.to_dict(orient="records")
lista_todas_os.insert(0, {"LABEL": "TODAS"})

df_lista_modelos = get_modelos(pgEngine)
lista_todos_modelos = df_lista_modelos.to_dict(orient="records")

lista_todos_modelos.insert(0, {"LABEL": "TODAS", "MODELO": "TODAS"})


##############################################################################
# Registro da página #########################################################
##############################################################################
dash.register_page(__name__, name="Retrabalho por veículo", path="/retrabalho-por-veiculo", icon="mdi:bus-alert")

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
                                                        minDate=date(2024, 1, 1),
                                                        maxDate=date.today(),
                                                        value=[date(2024, 1, 1), date.today()],
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
                                                        multi=True,
                                                        value=["TODAS"],
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
                                                        multi=True,
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
                                                            {
                                                                "label": "BORRACHARIA",
                                                                "value": "MANUTENCAO BORRACHARIA",
                                                            },
                                                            {
                                                                "label": "ELETRICA",
                                                                "value": "MANUTENCAO ELETRICA",
                                                            },
                                                            {"label": "GARAGEM", "value": "MANUTENÇÃO GARAGEM"},
                                                            {
                                                                "label": "LANTERNAGEM",
                                                                "value": "MANUTENCAO LANTERNAGEM",
                                                            },
                                                            {"label": "LUBRIFICAÇÃO", "value": "LUBRIFICAÇÃO"},
                                                            {
                                                                "label": "MECANICA",
                                                                "value": "MANUTENCAO MECANICA",
                                                            },
                                                            {"label": "PINTURA", "value": "MANUTENCAO PINTURA"},
                                                            {
                                                                "label": "SERVIÇOS DE TERCEIROS",
                                                                "value": "SERVIÇOS DE TERCEIROS",
                                                            },
                                                            {
                                                                "label": "SETOR DE ALINHAMENTO",
                                                                "value": "SETOR DE ALINHAMENTO",
                                                            },
                                                            {
                                                                "label": "SETOR DE POLIMENTO",
                                                                "value": "SETOR DE POLIMENTO",
                                                            },
                                                        ],
                                                        multi=True,
                                                        value=["TODAS"],
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
            ]
            
        ),
        dbc.Row(dmc.Space(h=40)),
        #dmc.Space(h=40),
        dmc.Space(h=40),
        ##Gráfico de Quantidade de OS / mes
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="fluent:arrow-trending-text-20-filled", width=45), width="auto"),
                dbc.Col(html.H4("Relaçao de OS / mês", className="align-self-center"), width=True),
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
                dbc.Col(html.H4("Relações de retrabalho / mês", className="align-self-center"), width=True),
            ],
            align="center",
        ),
        dcc.Graph(id="graph-evolucao-retrabalho-por-garagem-por-mes-veiculos"),
        dmc.Space(h=40),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="fluent:arrow-trending-text-20-filled", width=45), width="auto"),
                dbc.Col(html.H4("Relações de retrabalho / mês / seção", className="align-self-center"), width=True),
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
                dbc.Col(html.H4("Valor das peças trocadas por mês", className="align-self-center"), width=True),
            ],
            align="center",
        ),
        dcc.Graph(id="graph-pecas-trocadas-por-mes"),
        dag.AgGrid(
            enableEnterpriseModules=True,
            id="tabela-pecas-substituidas",
            columnDefs=[
                {"field": "OS", "minWidth": 100},
                {"field": "EQUIPAMENTO", "minWidth": 100},
                {"field": "MODELO", "minWidth": 300},
                {"field": "PRODUTO", "minWidth": 350},
                {"field": "QUANTIDADE", "minWidth": 100},
                {"field": "VALOR", "minWidth": 100},
                {"field": "DATA", "minWidth": 130}
            ],
            rowData=[],
            defaultColDef={"filter": True, "floatingFilter": True},
            columnSize="autoSize",
        ),
        dmc.Space(h=40),
        dag.AgGrid(
            enableEnterpriseModules=True,
            id="tabela-pecas-substituidas-por-descricao",
            columnDefs=[
                {"field": "DESCRIÇÃO", "minWidth": 300},
                {"field": "PRODUTO", "minWidth": 350},
                {"field": "QUANTIDADE DE OS'S", "minWidth": 100},
                {"field": "QUANTIDADE DE PEÇAS", "minWidth": 100},
                {"field": "MODELO", "minWidth": 300},
                {"field": "VALOR", "minWidth": 100},
            ],
            rowData=[],
            defaultColDef={"filter": True, "floatingFilter": True},
            columnSize="autoSize",
        ),
        dmc.Space(h=40),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="fluent:arrow-trending-wrench-20-filled", width=45), width="auto"),
                dbc.Col(html.H4("Tabela por descrição de serviço", className="align-self-center"), width=True),
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
        ),
        dmc.Space(h=60),
        
# Indicadores

    ]
)



##############################################################################
# CALLBACKS ##################################################################
##############################################################################


# Callback para atualizar o dropdown de veículos
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
    lista_todos_veiculos = HomeServiceVeiculo.atualizar_veiculos_func(modelos_selecionados)
    # Formatar corretamente para o Dropdown
    options = [
        {"label": f'{veiculo["VEICULO"]} ({veiculo["MODELO"]})', "value": veiculo["VEICULO"]}
        for veiculo in lista_todos_veiculos
    ]
    # Selecionar o segundo item como padrão, se existir
    value = [options[1]["value"]] if len(options) > 1 else []
    return options, value

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
        Input("input-select-ordens-servico-visao-geral", "value"),
        Input("input-select-veiculos", "value"),
    ],
)
def plota_grafico_pizza_sintese_geral(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
    # Valida input
    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
        return go.Figure(), "", ""
    total_retrabalho, total_correcao_primeira, labels, values = HomeServiceVeiculo.sintese_geral_fun(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos)
    fig = grafico_pizza_sintese_geral(labels, values)
    return fig, total_retrabalho, total_correcao_primeira,

# GRÁFICO DE RETRABALHOS POR VEÍCULOS
@callback(
    Output("graph-evolucao-retrabalho-por-garagem-por-mes-veiculos", "figure"),
    [
        Input("input-intervalo-datas-por-veiculo", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
        Input("input-select-oficina-visao-geral", "value"),
        Input("input-select-secao-visao-geral", "value"),
        Input("input-select-ordens-servico-visao-geral", "value"),
        Input("input-select-veiculos", "value"),
    ],
)
def plota_grafico_evolucao_retrabalho_por_veiculo_por_mes(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
    # Valida input
    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
        return go.Figure()
    df = HomeServiceVeiculo.evolucao_retrabalho_por_veiculo_por_mes_fun(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos)
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
        Input("input-select-ordens-servico-visao-geral", "value"),
        Input("input-select-veiculos", "value"),
    ],
)
def plota_grafico_evolucao_retrabalho_por_secao_por_mes(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
    # Valida input
    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
        return go.Figure()
    df = HomeServiceVeiculo.retrabalho_por_secao_por_mes()
    fig = grafico_evolucao_retrabalho_por_secao_por_mes(df)
    # Exibe o gráfico
    return fig

######### RASCUNHO
@callback(
    [
        #Output("indicador-porcentagem-retrabalho-veiculo", "children"),
        #Output("indicador-porcentagem-correcao-primeira", "children"),
        #Output("indicador-relacao-os-problema", "children"),
        #Output("indicador-posicao-relaçao-retrabalho", "children"),
        #Output("indicador-posição-veiculo-correção-primeira", "children"),
        Output("indicador-posição-veiculo-relaçao-osproblema", "children"),
        #Output("indicador-pecas-totais", "children"),
        #Output("indicador-pecas-mes", "children"),
        #Output("indicador-ranking-pecas", "children"),
        #Output("indicador-oss-diferentes", "children"),
        #Output("indicador-problemas-diferentes", "children"),
        #Output("indicador-mecanicos-diferentes", "children"),
    ],
    Input("store-dados-os", "data"),
)
def atualiza_indicadores(data):
    # if data["vazio"]:
    #     return ["", "", "", "", "", "", "", "", "", "", "", ""]

    porcentagem_retrabalho_veiculo = '0'
    porcentagem_correcao_primeira = '0'
    rel_os_problemas = '0'
    posicao_relaçao_retrabalho = '0'


    return [
        f"{porcentagem_retrabalho_veiculo} %",
        f"{porcentagem_correcao_primeira} %",
        f"{rel_os_problemas} OS/prob",
        f"{posicao_relaçao_retrabalho}º",
        f"{posicao_veiculo_correção_primeira}º",
        f"{posicao_relaçao_relaçao-osproblema}º",
        f"{pecas_mes} peças por mês",
        f"{ranking_pecas} º",
        f"{oss_diferentes} Os's",
        f"{problemas_diferentess} diferentes",
        f"{mecanicos_diferentes} diferentes",
    ]
######### RASCUNHO

# GRAFICO DA QUANTIDADE DE OSs, INDICADORES DE : PROBLEMAS DIFERENTES, MECANICOS DIFERENTES, OS DIFERENTES
@callback(
    [Output('graph-evolucao-os-mes-veiculo', 'figure'),
     Output("indicador-problemas-diferentes", "children"),
     Output("indicador-mecanicos-diferentes", "children"),
     Output("indicador-oss-diferentes", "children"),
     Output("indicador-relacao-os-problema", "children")],
    [
        Input("input-intervalo-datas-por-veiculo", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
        Input("input-select-oficina-visao-geral", "value"),
        Input("input-select-secao-visao-geral", "value"),
        Input("input-select-ordens-servico-visao-geral", "value"),
        Input("input-select-veiculos", "value"),
    ],
)
def plota_grafico_evolucao_quantidade_os_por_mes(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
    # Valida input
    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
        return go.Figure(), "", "", "", ""
    (os_diferentes, mecanicos_diferentes,os_totais_veiculo, 
     os_problema,  df_soma_mes, df_os_unicas) = HomeServiceVeiculo.evolucao_quantidade_os_por_mes_fun(datas, min_dias, lista_oficinas, 
                                                                                      lista_secaos, lista_os, lista_veiculos)
    fig = grafico_qtd_os_e_soma_de_os_mes(df_soma_mes, df_os_unicas)
    return fig, os_diferentes, mecanicos_diferentes, os_totais_veiculo, os_problema

# GRAFICO DA TABELA DE PEÇAS
@callback(
    Output("graph-pecas-trocadas-por-mes", "figure"),
    [
        Input("input-intervalo-datas-por-veiculo", "value"),
        Input("input-select-veiculos", "value"),
    ],
)
def plota_grafico_pecas_trocadas_por_mes(datas, equipamentos):
    # Valida input
    if not datas or not equipamentos:
        return go.Figure().update_layout(title_text="Parâmetros inválidos")
    # Garante que equipamentos seja uma lista
    if isinstance(equipamentos, str):
        equipamentos = [equipamentos]
        df_veiculos, df_media_geral = HomeServiceVeiculo.pecas_trocadas_por_mes_fun(datas, equipamentos)
        fig = grafico_tabela_pecas(df_veiculos, df_media_geral)
        return fig

# TABELA DE PEÇAS, INDICADORES DE: VALORES DE PECAS, VALOR DE PECAS/MES, RANKING DO VALOR DE PECAS
@callback(
   [Output("tabela-pecas-substituidas", "rowData"),
    Output("indicador-pecas-totais", "children"),
    Output("indicador-pecas-mes", "children"),
    Output("indicador-ranking-pecas", "children"),
    ],
    #Input("graph-pecas-trocadas-por-mes", "clickData"),
    [
        Input("input-intervalo-datas-por-veiculo", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
        Input("input-select-veiculos", "value"),
    ],
    
)
def atualiza_tabela_pecas(datas, min_dias, lista_veiculos):
    # Valida input
    if not input_valido3(datas, min_dias, lista_veiculos):
        return [], 0, 0, 0

    # Datas
    data_inicio_str = datas[0]
    
    # Remove min_dias antes para evitar que a última OS não seja retrabalho
    data_fim = pd.to_datetime(datas[1])
    data_fim = data_fim - pd.DateOffset(days=min_dias + 1)

    data_inicio_dt = pd.to_datetime(data_inicio_str)
    data_inicio_str = data_inicio_dt.strftime("%d/%m/%Y")
    data_fim_str = data_fim.strftime("%d/%m/%Y")

    print(data_inicio_str)

    subquery_veiculos_str = subquery_equipamentos(lista_veiculos)

    query_detalhes = f"""
    SELECT "OS", 
        "EQUIPAMENTO", 
        "MODELO", 
        "PRODUTO", 
        "QUANTIDADE", 
        "VALOR", 
        "DATA"
    FROM pecas_gerais 
        WHERE 
            TO_DATE("DATA", 'DD/MM/YY') 
                BETWEEN TO_DATE('{data_inicio_str}', 'DD/MM/YYYY') 
                    AND TO_DATE('{data_fim_str}', 'DD/MM/YYYY')
            AND "GRUPO" NOT IN ('COMBUSTIVEIS E LUBRIFICANTES', 'Lubrificantes e Combustiveis Especiais')
            {subquery_veiculos_str}
    """

    print(query_detalhes)


    query_ranking_veiculo = f"""
    WITH ranking_veiculos AS (
        SELECT 
            ROW_NUMBER() OVER (ORDER BY SUM("VALOR") ASC) AS ranking,
            "EQUIPAMENTO",  -- Veículo
            SUM("VALOR") AS total_pecas
        FROM pecas_gerais 
        WHERE 
            TO_DATE("DATA", 'DD/MM/YY') 
            BETWEEN TO_DATE('{data_inicio_str}', 'DD/MM/YYYY') 
                    AND TO_DATE('{data_fim_str}', 'DD/MM/YYYY')
            AND "GRUPO" NOT IN ('COMBUSTIVEIS E LUBRIFICANTES', 'Lubrificantes e Combustiveis Especiais')
        GROUP BY "EQUIPAMENTO"
        )
        SELECT * 
        FROM ranking_veiculos
            WHERE "EQUIPAMENTO" = '{lista_veiculos[0]}'
        ORDER BY ranking;
"""
    try:
        df_detalhes = pd.read_sql(query_detalhes, pgEngine)

        df_detalhes["DT"] = pd.to_datetime(df_detalhes["DATA"], dayfirst=True)

        # Formatar a coluna "VALOR"
        df_detalhes["VALOR"] = df_detalhes["VALOR"].astype(float) 

        num_meses = df_detalhes['DT'].dt.to_period('M').nunique()

        numero_pecas_veiculos_total = int(df_detalhes['QUANTIDADE'].sum())
        valor_total_veiculos = df_detalhes['VALOR'].replace('[R$,]', '', regex=True).astype(float).sum().round(2)

        valor_total_veiculos_str = f"R${valor_total_veiculos:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        if len(lista_veiculos) <= 1:
            df_rk = pd.read_sql(query_ranking_veiculo, pgEngine)
            rk_n = df_rk.iloc[0]["ranking"]
            rk = f'{rk_n}°'
        else:
            rk = f'0°'

        pecas_mes = round((numero_pecas_veiculos_total / num_meses), 2)
        valor_mes = round((valor_total_veiculos / num_meses), 2)
        valor_mes_str = f"R$ {valor_mes:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        return df_detalhes.to_dict("records"), valor_total_veiculos_str, valor_mes_str, rk

    except Exception as e:
        print(f"Erro ao executar a consulta da tabela: {e}")
        return [], 0, 0, 0

# TABELA DE DESCRIÇÃO DE SERVIÇOS
@callback(
    Output("tabela-descricao-de-servico", "rowData"),
    [
        Input("input-intervalo-datas-por-veiculo", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
        Input("input-select-oficina-visao-geral", "value"),
        Input("input-select-secao-visao-geral", "value"),
        Input("input-select-ordens-servico-visao-geral", "value"),
        Input("input-select-veiculos", "value"),
    ],
    running=[(Output("loading-overlay-guia-por-veiculo", "visible"), True, False)],
)
def atualiza_tabela_top_os_geral_retrabalho(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculo):
    # Valida input
    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculo):
        return []

    # Datas
    data_inicio_str = datas[0]

    # Remove min_dias antes para evitar que a última OS não seja retrabalho
    data_fim = pd.to_datetime(datas[1])
    data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
    data_fim_str = data_fim.strftime("%Y-%m-%d")

    # Subqueries
    subquery_oficinas_str = subquery_oficinas(lista_oficinas)
    subquery_secoes_str = subquery_secoes(lista_secaos)
    subquery_os_str = subquery_os(lista_os)
    subquery_veiculos_str = subquery_veiculos(lista_veiculo)

    inner_subquery_oficinas_str = subquery_oficinas(lista_oficinas, "main.")
    inner_subquery_secoes_str = subquery_secoes(lista_secaos, "main.")
    inner_subquery_os_str = subquery_os(lista_os, "main.")
    inner_subquery_veiculos_str = subquery_veiculos(lista_veiculo, "main.")

    query = f"""
    WITH normaliza_problema AS (
        SELECT
            "DESCRICAO DA OFICINA",
            "DESCRICAO DA SECAO",
            "DESCRICAO DO SERVICO" as servico,
            "CODIGO DO VEICULO",
            "problem_no"
        FROM
            mat_view_retrabalho_{min_dias}_dias
        WHERE
            "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            {subquery_oficinas_str}
            {subquery_secoes_str}
            {subquery_os_str}
            {subquery_veiculos_str}
        GROUP BY
            "DESCRICAO DA OFICINA",
            "DESCRICAO DA SECAO",
            "DESCRICAO DO SERVICO",
            "CODIGO DO VEICULO",
            "problem_no"
    ),
    os_problema AS (
        SELECT
            "DESCRICAO DA OFICINA",
            "DESCRICAO DA SECAO",
            servico,
            COUNT(*) AS num_problema
        FROM
            normaliza_problema
        GROUP BY
            "DESCRICAO DA OFICINA",
            "DESCRICAO DA SECAO",
            servico
    )
    SELECT
        main."DESCRICAO DA OFICINA",
        main."DESCRICAO DA SECAO",
        main."DESCRICAO DO SERVICO",
        COUNT(*) AS "TOTAL_OS",
        SUM(CASE WHEN main.retrabalho THEN 1 ELSE 0 END) AS "TOTAL_RETRABALHO",
        SUM(CASE WHEN main.correcao THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO",
        SUM(CASE WHEN main.correcao_primeira THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO_PRIMEIRA",
        100 * ROUND(SUM(CASE WHEN main.retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
        100 * ROUND(SUM(CASE WHEN main.correcao THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO",
        100 * ROUND(SUM(CASE WHEN main.correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA",
        COALESCE(op.num_problema, 0) AS "TOTAL_PROBLEMA",
        SUM(pg."QUANTIDADE") as "QUANTIDADE DE PECAS" ,
        COUNT(main."COLABORADOR QUE EXECUTOU O SERVICO") as "QUANTIDADE DE COLABORADORES" 
    FROM
        mat_view_retrabalho_{min_dias}_dias main
    LEFT JOIN
        os_problema op
    ON
        main."DESCRICAO DA OFICINA" = op."DESCRICAO DA OFICINA"
        AND main."DESCRICAO DA SECAO" = op."DESCRICAO DA SECAO"
        AND main."DESCRICAO DO SERVICO" = op.servico
    LEFT JOIN
    	PECAS_GERAIS pg
    ON 
    	main."NUMERO DA OS" = pg."OS"
    WHERE
        main."DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
        {inner_subquery_oficinas_str}
        {inner_subquery_secoes_str}
        {inner_subquery_os_str}
        {inner_subquery_veiculos_str}
    GROUP BY
        main."DESCRICAO DA OFICINA",
        main."DESCRICAO DA SECAO",
        main."DESCRICAO DO SERVICO",
        op.num_problema
    ORDER BY
        "PERC_RETRABALHO" DESC;
    """

    # Executa a query
    df = pd.read_sql(query, pgEngine)

    df["REL_OS_PROBLEMA"] = round(df["TOTAL_OS"] / df["TOTAL_PROBLEMA"], 2)

    return df.to_dict("records")

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
        Input("input-select-ordens-servico-visao-geral", "value"),
        Input("input-select-veiculos", "value"),
    ],
)
def ranking_retrabalho_veiculos(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
    # Valida input
    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
        return "", "", "", ""

    # Datas
    data_inicio_str = datas[0]

    # Remove min_dias antes para evitar que a última OS não seja retrabalho
    data_fim = pd.to_datetime(datas[1])
    data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
    data_fim_str = data_fim.strftime("%Y-%m-%d")

    # Subqueries
    subquery_oficinas_str = subquery_oficinas(lista_oficinas)
    subquery_secoes_str = subquery_secoes(lista_secaos)
    subquery_os_str = subquery_os(lista_os)
    subquery_veiculos_str = subquery_veiculos(lista_veiculos)
    

    query_ranking_retrabalho_correcao = f"""
            SELECT
                "CODIGO DO VEICULO",
                "DESCRICAO DO MODELO",
                "TOTAL_RETRABALHO",
                "TOTAL_CORRECAO",
                "TOTAL_CORRECAO_PRIMEIRA",
                "PERC_RETRABALHO",
                "PERC_CORRECAO",
                "PERC_CORRECAO_PRIMEIRA",
                ranking_retrabalho,
                ranking_correcao,
                ranking_correcao_primeira
            FROM (
                SELECT
                    "CODIGO DO VEICULO",
                    "DESCRICAO DO MODELO",
                    SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END) AS "TOTAL_RETRABALHO",
                    SUM(CASE WHEN correcao THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO",
                    SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO_PRIMEIRA",
                    100 * ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
                    100 * ROUND(SUM(CASE WHEN correcao THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO",
                    100 * ROUND(SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA",
                    DENSE_RANK() OVER (ORDER BY 100 * ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) ASC) AS ranking_retrabalho,
                    DENSE_RANK() OVER (ORDER BY 100 * ROUND(SUM(CASE WHEN correcao THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) ASC) AS ranking_correcao,
                    DENSE_RANK() OVER (ORDER BY 100 * ROUND(SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) desc)  ranking_correcao_primeira
                FROM
                    mat_view_retrabalho_{min_dias}_dias
                WHERE
                    "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                    {subquery_oficinas_str}
                    {subquery_secoes_str}
                    {subquery_os_str}
                    
                GROUP BY
                    "CODIGO DO VEICULO", "DESCRICAO DO MODELO"
            ) subquery
            WHERE
                ranking_retrabalho >= 1  -- Exemplo de filtro pelo ranking
                --{subquery_veiculos_str}
            ORDER BY 
                ranking_retrabalho, ranking_correcao, ranking_correcao_primeira;                
"""
    
    rk_retrabalho_geral = f'0°'
    rk_correcao_primeira_geral = f'0°'
    
    rk_retrabalho_modelo = f'0°'
    rk_correcao_primeira_modelo = f'0°'

    if len(lista_veiculos) <= 1:
        df = pd.read_sql(query_ranking_retrabalho_correcao, pgEngine)
        df = df.rename(columns={
            "PERC_RETRABALHO": "RETRABALHO",
            "PERC_CORRECAO_PRIMEIRA": "CORRECAO_PRIMEIRA"
        })
        df_veiculo = df.loc[df["CODIGO DO VEICULO"] == lista_veiculos[0]]

        if len(df_veiculo) >= 1:
            contagem_ranking_geral = len(df)

            rk_n_retrabalho = df_veiculo.iloc[0]["ranking_retrabalho"]
            retra = df_veiculo.iloc[0]["RETRABALHO"]
            rk_retrabalho_geral = f'{rk_n_retrabalho}°/{contagem_ranking_geral}'

            rk_n_correcao_primeira = df_veiculo.iloc[0]["ranking_correcao_primeira"]
            rk_correcao_primeira_geral = f'{rk_n_correcao_primeira}°/{contagem_ranking_geral}'

        ########################################################### POR MODELO AGORA
            lista_modelos = df_veiculo["DESCRICAO DO MODELO"].dropna().unique().tolist()
            sub_query_modelos_str = subquery_modelos_veiculos(lista_modelos)

            query_ranking_retrabalho_correcao_modelos = f"""
                SELECT
                    "CODIGO DO VEICULO",
                    "DESCRICAO DO MODELO",
                    "TOTAL_RETRABALHO",
                    "TOTAL_CORRECAO",
                    "TOTAL_CORRECAO_PRIMEIRA",
                    "PERC_RETRABALHO",
                    "PERC_CORRECAO",
                    "PERC_CORRECAO_PRIMEIRA",
                    ranking_retrabalho,
                    ranking_correcao,
                    ranking_correcao_primeira
                FROM (
                    SELECT
                        "CODIGO DO VEICULO",
                        "DESCRICAO DO MODELO",
                        SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END) AS "TOTAL_RETRABALHO",
                        SUM(CASE WHEN correcao THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO",
                        SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO_PRIMEIRA",
                        100 * ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
                        100 * ROUND(SUM(CASE WHEN correcao THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO",
                        100 * ROUND(SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA",
                        DENSE_RANK() OVER (ORDER BY 100 * ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) ASC) AS ranking_retrabalho,
                        DENSE_RANK() OVER (ORDER BY 100 * ROUND(SUM(CASE WHEN correcao THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) ASC) AS ranking_correcao,
                        DENSE_RANK() OVER (ORDER BY 100 * ROUND(SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) desc)  ranking_correcao_primeira
                    FROM
                        mat_view_retrabalho_{min_dias}_dias
                    WHERE
                        "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                        {subquery_oficinas_str}
                        {subquery_secoes_str}
                        {subquery_os_str}
                        {sub_query_modelos_str}
                    GROUP BY
                        "CODIGO DO VEICULO", "DESCRICAO DO MODELO"
                ) subquery
                WHERE
                    ranking_retrabalho >= 1  -- Exemplo de filtro pelo ranking
                ORDER BY 
                    ranking_retrabalho, ranking_correcao, ranking_correcao_primeira;                
                """

            df_modelos = pd.read_sql(query_ranking_retrabalho_correcao_modelos, pgEngine)
            df_modelos = df_modelos.rename(columns={
                "PERC_RETRABALHO": "RETRABALHO",
                "PERC_CORRECAO_PRIMEIRA": "CORRECAO_PRIMEIRA"
            })
            contagem_ranking_modelos = len(df_modelos)
            df_veiculo_modelo = df_modelos.loc[df_modelos["CODIGO DO VEICULO"] == lista_veiculos[0]]

            rk_n_retrabalho_modelo = df_veiculo_modelo.iloc[0]["ranking_retrabalho"]
            rk_retrabalho_modelo = f'{rk_n_retrabalho_modelo}°/{contagem_ranking_modelos}'

            rk_n_correcao_primeira_modelos = df_veiculo_modelo.iloc[0]["ranking_correcao_primeira"]
            rk_correcao_primeira_modelo = f'{rk_n_correcao_primeira_modelos}°/{contagem_ranking_modelos}'

    return rk_retrabalho_geral, rk_correcao_primeira_geral, rk_retrabalho_modelo, rk_correcao_primeira_modelo