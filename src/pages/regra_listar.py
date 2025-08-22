#!/usr/bin/env python
# coding: utf-8

# Tela para listar as regras existentes

##############################################################################
# IMPORTS ####################################################################
##############################################################################
# Bibliotecas básicas
from datetime import date, datetime
import pandas as pd
import re

# Importar bibliotecas do dash básicas e plotly
import dash
from dash import Dash, html, dcc, callback, Input, Output, State, callback_context
import plotly.express as px
import plotly.graph_objects as go

# Importar bibliotecas do bootstrap e ag-grid
import dash_bootstrap_components as dbc
import dash_ag_grid as dag

# Dash componentes Mantine e icones
import dash_mantine_components as dmc
from dash_iconify import DashIconify

# Importar nossas constantes e funções utilitárias
import locale_utils

# Banco de Dados
from db import PostgresSingleton

# Imports gerais
from modules.entities_utils import get_mecanicos, get_lista_os, get_oficinas, get_secoes, get_modelos, gerar_excel

# Imports específicos
from modules.crud_regra.crud_regra_service import CRUDRegraService
from modules.crud_regra.crud_email_test import CRUDEmailTestService
from modules.crud_regra.crud_wpp_test import CRUDWppTestService
from modules.home.home_service import HomeService

import modules.crud_regra.graficos as crud_regra_graficos
import modules.crud_regra.tabelas as crud_regra_tabelas
import tema

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
crud_regra_service = CRUDRegraService(pgEngine)

# Modelos de veículos
df_modelos_veiculos = get_modelos(pgEngine)
lista_todos_modelos_veiculos = df_modelos_veiculos.to_dict(orient="records")
lista_todos_modelos_veiculos.insert(0, {"MODELO": "TODOS"})

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
# Layout #####################################################################
##############################################################################
layout = dbc.Container(
    [
        # Informações / Ajuda
        dmc.Modal(
            # title="Erro ao carregar os dados",
            id="modal-erro-apagar-regra",
            centered=True,
            radius="lg",
            size="md",
            children=dmc.Stack(
                [
                    dmc.ThemeIcon(
                        radius="lg",
                        size=128,
                        color="red",
                        variant="light",
                        children=DashIconify(icon="material-symbols:error-rounded", width=128, height=128),
                    ),
                    dmc.Title("Erro!", order=1),
                    dmc.Text("Ocorreu um erro ao testar a regra. Verifique se a regra possui:"),
                    dmc.List(
                        [
                            dmc.ListItem("Nome da regra;"),
                            dmc.ListItem("Pelo menos um alerta alvo (nova OS, retrabalho, etc);"),
                            dmc.ListItem("Pelo menos um destino de email ou WhatsApp ativo."),
                        ],
                    ),
                    dmc.Group(
                        [
                            dmc.Button(
                                "Fechar",
                                color="red",
                                variant="outline",
                                id="btn-close-modal-erro-teste-regra",
                            ),
                        ],
                        # justify="flex-end",
                    ),
                ],
                align="center",
                gap="xl",
            ),
        ),
        dmc.Modal(
            # title="Erro ao carregar os dados",
            id="modal-sucesso-apagar-regra",
            centered=True,
            radius="lg",
            size="lg",
            children=dmc.Stack(
                [
                    dmc.ThemeIcon(
                        radius="xl",
                        size=128,
                        color="green",
                        variant="light",
                        children=DashIconify(icon="material-symbols:check-circle-rounded", width=128, height=128),
                    ),
                    dmc.Title("Sucesso!", order=1),
                    dmc.Text("A regra foi testada com sucesso."),
                    dmc.Group(
                        [
                            dmc.Button(
                                "Fechar",
                                color="green",
                                variant="outline",
                                id="btn-close-modal-sucesso-teste-regra",
                            ),
                        ],
                        # justify="flex-end",
                    ),
                ],
                align="center",
                gap="xl",
            ),
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Alert(
                            [
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            DashIconify(icon="material-symbols:date-range", width=45), width="auto"
                                        ),
                                        dbc.Col(
                                            html.P(
                                                [
                                                    html.Strong("Período de monitoramento:"),
                                                    #     """
                                                    # período em que as OSs estarão ativas para os filtros da regra de monitoramento contínuo.
                                                    # """,
                                                    """
                                                intervalo em que as OSs serão analisadas pelos filtros da regra de 
                                                monitoramento contínuo. Esse valor é diferente do período de retrabalho,
                                                que define o número mínimo de dias entre OS para que uma nova OS não 
                                                seja considerada retrabalho. Exemplo: um monitoramento de 2 dias com
                                                período de retrabalho de 30 dias irá avaliar continuamente 
                                                as OSs dos dois últimos dias para identificar retrabalhos.
                                                """,
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
                            color="secondary",
                        ),
                    ],
                    md=12,
                ),
                dbc.Col(
                    [
                        dbc.Alert(
                            [
                                dbc.Row(
                                    [
                                        dbc.Col(DashIconify(icon="mdi:new-box", width=45), width="auto"),
                                        dbc.Col(
                                            html.P(
                                                [
                                                    html.Strong("Nova OS, sem retrabalho prévio:"),
                                                    """
                                                não há OS anterior no período de retrabalho
                                                """,
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
                            color="info",
                        ),
                    ],
                    md=4,
                ),
                dbc.Col(
                    [
                        dbc.Alert(
                            [
                                dbc.Row(
                                    [
                                        dbc.Col(DashIconify(icon="mdi:alert-decagram-outline", width=45), width="auto"),
                                        dbc.Col(
                                            html.P(
                                                [
                                                    html.Strong("Nova OS, com retrabalho prévio:"),
                                                    """
                                                possui OS dentro do intervalo de retrabalho
                                                """,
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
                            color="warning",
                        ),
                    ],
                    md=4,
                ),
                dbc.Col(
                    [
                        dbc.Alert(
                            [
                                dbc.Row(
                                    [
                                        dbc.Col(DashIconify(icon="pepicons-pop:rewind-time", width=45), width="auto"),
                                        dbc.Col(
                                            html.P(
                                                [
                                                    html.Strong("Retrabalho:"),
                                                    """
                                                OS de retrabalho confirmada dentro do período de monitoramento
                                                """,
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
                            color="danger",
                        ),
                    ],
                    md=4,
                ),
            ]
        ),
        # Cabeçalho e Inputs
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="carbon:rule", width=45), width="auto"),
                dbc.Col(
                    html.H1(
                        [
                            html.Strong("Regras de Monitoramento"),
                        ],
                        className="align-self-center",
                    ),
                    width=True,
                ),
                dbc.Col(
                    dbc.Button(
                        [DashIconify(icon="mdi:plus", className="me-1"), "Criar Regra"],
                        id="btn-criar-regra",
                        color="success",
                        className="me-1",
                        style={"padding": "1em"},
                    ),
                    width="auto",
                ),
            ],
            align="center",
        ),
        # dmc.Space(h=15),
        html.Hr(),
        dmc.Space(h=40),
        dag.AgGrid(
            id="tabela-regras-existentes",
            columnDefs=crud_regra_tabelas.tbl_regras_existentes,
            rowData=[
                {
                    "id": 1,
                    "relatorio": "📋 Relatório",
                    "editar": "✏️ Editar",
                    "apagar": "❌ Apagar",
                    "nome_regra": "Regra 1",
                    "data_surgimento": "2021-01-01",
                    "data_criacao": "2021-01-01",
                    "data_atualizacao": "2021-01-01",
                    "periodo_monitoramento": "10 dias",
                    "tempo_retrabalho": "30 dias",
                }
            ],
            defaultColDef={"filter": True, "floatingFilter": True},
            columnSize="autoSize",
            dashGridOptions={
                "localeText": locale_utils.AG_GRID_LOCALE_BR,
                "enableCellTextSelection": True,
                "ensureDomOrder": True,
            },
            style={"height": 500, "resize": "vertical", "overflow": "hidden"},  # -> permite resize
        ),
        dmc.Space(h=40),
    ]
)


##############################################################################
# Registro da página #########################################################
##############################################################################
dash.register_page(__name__, name="Regras", path="/regra-listar", icon="carbon:rule")
