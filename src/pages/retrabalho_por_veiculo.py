#!/usr/bin/env python
# coding: utf-8

# Dashboard que lista o retrabalho de um veículo específico

##############################################################################
# IMPORTS ####################################################################
##############################################################################
# Bibliotecas básicas
from datetime import date
import math
import numpy as np
import pandas as pd
import os
import re

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

##############################################################################
# LEITURA DE DADOS ###########################################################
##############################################################################
# Conexão com os bancos
pgDB = PostgresSingleton.get_instance()
pgEngine = pgDB.get_engine()

# Veículos
df_veiculos = pd.read_sql(
    """
    SELECT  
        "Description", "RegistrationNumber", "Model"
    FROM 
        veiculos_api
""",
    pgEngine,
)

# Colaboradores / Mecânicos
df_mecanicos = pd.read_sql("SELECT * FROM colaboradores_frotas_os", pgEngine)


##############################################################################
# CALLBACKS ##################################################################
##############################################################################

##############################################################################
# Callbacks para os inputs ##################################################
##############################################################################


# Callback para o grafico por modelo
@callback(
    Output("graph-retrabalho-por-secao-analise-por-veiculo", "figure"),
    [
        Input("input-intervalo-datas-analise-por-veiculo", "value"),
        Input("input-select-dias-geral-analise-por-veiculo", "value"),
        Input("input-select-veiculo-analise-por-veiculo", "value"),
    ],
)
def plota_grafico_por_modelo(datas, min_dias, veiculo_escolhido):
    # Valida input
    if not veiculo_escolhido:
        return go.Figure()

    # Datas
    data_inicio_str = datas[0]

    # Remove min_dias antes para evitar que a última OS não seja retrabalho
    data_fim = pd.to_datetime(datas[1])
    data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
    data_fim_str = data_fim.strftime("%Y-%m-%d")

    query = f"""
    SELECT
        "DESCRICAO DA SECAO",
        "CODIGO DO VEICULO",
        100 * ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
        100 * ROUND(SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA"
    FROM 
        mat_view_retrabalho_{min_dias}_dias
    WHERE
        "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
        AND "CODIGO DO VEICULO" = '{veiculo_escolhido}'
    GROUP BY
        "DESCRICAO DA SECAO", "CODIGO DO VEICULO"
    """

    print(query)


##############################################################################
# Registro da página #########################################################
##############################################################################
dash.register_page(
    __name__,
    name="Análise por Veículo",
    path="/analise-por-veiculo",
    icon="mdi:bus-alert",
)


##############################################################################
# Layout #####################################################################
##############################################################################
layout = dbc.Container(
    [
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
                                        dbc.Col(
                                            DashIconify(
                                                icon="mdi:bus-wrench", width=45
                                            ),
                                            width="auto",
                                        ),
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
                                                    dbc.Label(
                                                        "Data (intervalo) de análise"
                                                    ),
                                                    dmc.DatePicker(
                                                        id="input-intervalo-datas-analise-por-veiculo",
                                                        allowSingleDateInRange=True,
                                                        type="range",
                                                        minDate=date(2024, 1, 1),
                                                        maxDate=date.today(),
                                                        value=[
                                                            date(2024, 1, 1),
                                                            date.today(),
                                                        ],
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
                                                    dbc.Label(
                                                        "Tempo (em dias) entre OS para retrabalho"
                                                    ),
                                                    dcc.Dropdown(
                                                        id="input-select-dias-geral-analise-por-veiculo",
                                                        options=[
                                                            {
                                                                "label": "10 dias",
                                                                "value": 10,
                                                            },
                                                            {
                                                                "label": "15 dias",
                                                                "value": 15,
                                                            },
                                                            {
                                                                "label": "30 dias",
                                                                "value": 30,
                                                            },
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
                                                    dbc.Label("Veículo"),
                                                    dcc.Dropdown(
                                                        id="input-select-veiculo-analise-por-veiculo",
                                                        options=[
                                                            {
                                                                "label": f'{vec["Description"]} ({vec["RegistrationNumber"]} - {vec["Model"]})',
                                                                "value": vec[
                                                                    "Description"
                                                                ],
                                                            }
                                                            for _, vec in df_veiculos.iterrows()
                                                        ],
                                                        placeholder="Selecione o veículo...",
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
                    md=12,
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
                                "Retrabalho por seção",
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
        dcc.Graph(id="graph-retrabalho-por-secao-analise-por-veiculo"),
        dmc.Space(h=40),
    ]
)
