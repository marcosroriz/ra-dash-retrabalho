#!/usr/bin/env python
# coding: utf-8

# Tela para apresentar relatório de uma regra para detecção de retrabalho

##############################################################################
# IMPORTS ####################################################################
##############################################################################
# Bibliotecas básicas
import pandas as pd
from datetime import date, datetime, timedelta
import re

# Importar bibliotecas para manipulação de URL
from urllib.parse import urlparse, parse_qs

# Importar bibliotecas do dash básicas e plotly
import dash
from dash import Dash, html, dcc, callback, Input, Output, State, callback_context
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
from modules.entities_utils import get_regras_monitoramento_os, get_mecanicos, get_lista_os, get_oficinas, get_secoes, get_modelos, gerar_excel

# Imports específicos
from modules.crud_regra.crud_regra_service import CRUDRegraService
from modules.crud_regra.crud_email_test import CRUDEmailTestService
from modules.crud_regra.crud_wpp_test import CRUDWppTestService

import modules.crud_regra.graficos as crud_regra_graficos
import modules.crud_regra.tabelas as crud_regra_tabelas

##############################################################################
# LEITURA DE DADOS ###########################################################
##############################################################################
# Conexão com os bancos
pgDB = PostgresSingleton.get_instance()
pgEngine = pgDB.get_engine()

# Cria o serviço
crud_regra_service = CRUDRegraService(pgEngine)

# Obtem a lista de regras de monitoramento de OS
df_regras_monitoramento_os = get_regras_monitoramento_os(pgEngine)
lista_regras_monitoramento_os = df_regras_monitoramento_os.to_dict(orient="records")

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
# Callbacks para os inputs via URL ###########################################
##############################################################################


##############################################################################
# Callbacks para os inputs ###################################################
##############################################################################

# Converte para int, se não for possível, retorna None
def safe_int(value):
    try:
        return int(value) if value is not None else None
    except (ValueError, TypeError):
        return None


# Preenche os dados via URL
@callback(
    Output("relatorio-input-select-regra-retrabalho", "value"),
    Output("relatorio-input-data-relatorio-regra-retrabalho", "value"),
    Input("url", "href"),
)
def callback_receber_campos_via_url_relatorio_regra(href):
    if not href:
        raise dash.exceptions.PreventUpdate

    # Faz o parse dos parâmetros da url
    parsed_url = urlparse(href)
    query_params = parse_qs(parsed_url.query)

    id_regra = safe_int(query_params.get("id_regra", [None])[0])
    data_relatorio = query_params.get("data_relatorio", [None])[0]

    # Verifica se a regra existe
    lista_id_regras = [regra["value"] for regra in lista_regras_monitoramento_os]
    if id_regra is not None and id_regra not in lista_id_regras:
        id_regra = None
        data_relatorio = None

    if id_regra is not None and data_relatorio is None:
        df_ultima_data_regra = crud_regra_service.get_ultima_data_regra(id_regra)
        if not df_ultima_data_regra.empty:
            data_relatorio = df_ultima_data_regra["ultimo_dia"].iloc[0]

    return id_regra, data_relatorio


# Sincroniza o store com os valores dos inputs
@callback(
    [
        Output("relatorio-card-input-select-regra-retrabalho", "style"),
        Output("relatorio-card-input-data-relatorio-regra-retrabalho", "style"),
        Output("relatorio-input-select-regra-retrabalho-error", "style"),
        Output("relatorio-input-data-relatorio-regra-retrabalho-error", "style"),
    ],
    Input("relatorio-input-select-regra-retrabalho", "value"),
    Input("relatorio-input-data-relatorio-regra-retrabalho", "value"),
)
def callback_sincroniza_input_store_relatorio_regra(regra_value, data_value):
    # Flags para validação
    input_regra_valido = True
    input_data_valido = False

    # Validação muda a borda e também mostra campo de erro
    # Estilos das bordas dos inputs
    style_borda_ok = {
        "border": "2px solid #198754",  # verde bootstrap
    }
    style_borda_erro = {
        "border": "2px solid #dc3545",  # vermelho bootstrap
    }

    # Estilho das bordas dos inputs
    style_borda_input_regra = style_borda_erro
    style_borda_input_data = style_borda_erro

    # Estilos dos erros dos inputs
    style_campo_erro_visivel = {"display": "block"}
    style_campo_erro_oculto = {"display": "none"}
    style_campo_erro_input_regra = style_campo_erro_visivel
    style_campo_erro_input_data = style_campo_erro_visivel

    # Valida primeiro se há regra
    if regra_value:
        style_borda_input_regra = style_borda_ok
        style_campo_erro_input_regra = style_campo_erro_oculto
    else:
        input_regra_valido = False

    # Valida primeiro a data
    if data_value:
        style_borda_input_data = style_borda_ok
        style_campo_erro_input_data = style_campo_erro_oculto
    else:
        input_data_valido = False

    return style_borda_input_regra, style_borda_input_data, style_campo_erro_input_regra, style_campo_erro_input_data



##############################################################################
# Layout #####################################################################
##############################################################################
layout = dbc.Container(
    [
        # Estado
        dcc.Store(id="store-relatorio-input-id-relatorio-regra"),
        # Loading
        dmc.LoadingOverlay(
            # visible=True,
            id="loading-overlay-guia-relatorio-regra",
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
        # Modais
        dmc.Modal(
            id="relatorio-modal-carregar-dados-relatorio-regra",
            centered=True,
            radius="lg",
            size="md",
            closeOnClickOutside=False,
            closeOnEscape=False,
            children=dmc.Stack(
                [
                    dmc.ThemeIcon(
                        radius="lg",
                        size=128,
                        color="red",
                        variant="light",
                        children=DashIconify(icon="material-symbols:error-rounded", width=128, height=128),
                    ),
                    dmc.Title("Erro ao carregar dados!", order=1),
                    dmc.Text("Ocorreu um erro ao carregar os dados da regra."),
                    dmc.Group(
                        [
                            dmc.Button(
                                "Fechar",
                                color="red",
                                variant="outline",
                                id="btn-close-relatorio-modal-carregar-dados-relatorio-regra",
                            ),
                        ],
                    ),
                    dmc.Space(h=20),
                ],
                align="center",
                gap="md",
            ),
        ),
        dmc.Modal(
            id="relatorio-modal-teste-relatorio-regra",
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
                                id="btn-close-relatorio-modal-teste-relatorio-regra",
                            ),
                        ],
                    ),
                ],
                align="center",
                gap="md",
            ),
        ),
        dmc.Modal(
            id="relatorio-modal-teste-relatorio-regra",
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
                                id="btn-close-relatorio-modal-teste-relatorio-regra",
                            ),
                        ],
                    ),
                ],
                align="center",
                gap="md",
            ),
        ),
        dmc.Modal(
            id="relatorio-modal-atualizar-relatorio-regra",
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
                    dmc.Text("Ocorreu um erro ao salvar a regra. Verifique se a regra possui:"),
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
                                id="btn-close-relatorio-modal-atualizar-relatorio-regra",
                            ),
                        ],
                    ),
                ],
                align="center",
                gap="md",
            ),
        ),
        dmc.Modal(
            id="relatorio-modal-atualizar-relatorio-regra",
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
                    dmc.Text("A regra foi salva com sucesso."),
                    dmc.Group(
                        [
                            dmc.Button(
                                "Fechar",
                                color="green",
                                variant="outline",
                                id="btn-close-relatorio-modal-atualizar-relatorio-regra",
                            ),
                        ],
                    ),
                ],
                align="center",
                gap="md",
            ),
        ),
        # Cabeçalho e Inputs
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="carbon:rule-data-quality", width=45), width="auto"),
                dbc.Col(
                    html.H1(
                        [
                            "Relatório de \u00a0",
                            html.Strong("regra"),
                            "\u00a0 de monitoramento do retrabalho",
                        ],
                        className="align-self-center",
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        # dmc.Space(h=15),
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        html.Div(
                            [
                                dbc.Label("Nome da Regra de Monitoramento"),
                                dcc.Dropdown(
                                    id="relatorio-input-select-regra-retrabalho",
                                    options=[regra for regra in lista_regras_monitoramento_os],
                                    placeholder="Selecione uma regra...",
                                ),
                                dmc.Space(h=5),
                                dbc.FormText(
                                    html.Em(
                                        "Regra não encontrada",
                                        id="relatorio-input-select-regra-retrabalho-error",
                                    ),
                                    color="secondary",
                                ),
                            ],
                            className="dash-bootstrap",
                        ),
                        id="relatorio-card-input-select-regra-retrabalho",
                        body=True,
                    ),
                    md=6,
                ),
                dbc.Col(
                    dbc.Card(
                        html.Div(
                            [
                                dbc.Label("Data do relatório"),
                                dmc.DateInput(
                                    id="relatorio-input-data-relatorio-regra-retrabalho",
                                    minDate=date(2020, 8, 5),
                                    valueFormat="DD/MM/YYYY",
                                    value=(datetime.now() - timedelta(days=10)).date()

                                ),
                                dmc.Space(h=5),
                                dbc.FormText(
                                    html.Em(
                                        "Período inválido",
                                        id="relatorio-input-data-relatorio-regra-retrabalho-error",
                                    ),
                                    color="secondary",
                                ),
                            ],
                            className="dash-bootstrap",
                        ),
                        id="relatorio-card-input-data-relatorio-regra-retrabalho",
                        body=True,
                    ),
                    md=6,
                ),
            ]
        ),
        dmc.Space(h=10),
        dmc.Space(h=40),
    ]
)


##############################################################################
# Registro da página #########################################################
##############################################################################
dash.register_page(__name__, name="Relatório de Regra", path="/regra-relatorio", icon="carbon:rule-data-quality", hide_page=True)
