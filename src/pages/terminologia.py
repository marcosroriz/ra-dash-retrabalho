#!/usr/bin/env python
# coding: utf-8

# Página de ajuda

##############################################################################
# IMPORTS ####################################################################
##############################################################################
# Bibliotecas básicas
from datetime import date, datetime
import pandas as pd

# Importar bibliotecas do dash básicas e plotly
import dash
from dash import html, dcc, callback, Input, Output
import plotly.graph_objects as go
import plotly.express as px

# Importar bibliotecas do bootstrap e ag-grid
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
from dash import callback_context

# Dash componentes Mantine e icones
import dash_mantine_components as dmc
from dash_iconify import DashIconify

# Banco de Dados
from db import PostgresSingleton

# Imports gerais
from modules.entities_utils import gerar_excel, get_lista_os, get_secoes
import locale_utils

# Imports específicos
from modules.colaborador.colaborador_service import ColaboradorService
import modules.colaborador.graficos as colaborador_graficos
import modules.colaborador.tabelas as colaborador_tabelas


##############################################################################
# Registro da página #########################################################
##############################################################################
dash.register_page(__name__, name="Terminologia", path="/terminologia", icon="fluent-mdl2:timeline")


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
                                        dbc.Col(DashIconify(icon="raphael:book", width=45), width="auto"),
                                        dbc.Col(
                                            html.H1(
                                                [
                                                    html.Strong("Terminologia"),
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
                            ]
                        ),
                    ],
                    md=12,
                ),
            ]
        ),
        dmc.Space(h=30),
        # Termos
        dbc.Alert(
            [
                dbc.Row(
                    [
                        dbc.Col(DashIconify(icon="gravity-ui:target-dart", width=45), width="auto"),
                        dbc.Col(
                            html.P(
                                [
                                html.Strong("Correção de primeira:"),
                                """
                                sem nova OS para o mesmo problema no período selecionado.
                                """
                                ]
                            ),
                            className="mt-2",
                            width=True,
                        ),
                    ],
                    align="center",
                ),
            ],
            dismissable=True,
            color="success",
        ),
    ]
)
