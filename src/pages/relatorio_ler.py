#!/usr/bin/env python
# coding: utf-8

# Tela para apresentar relatório de uma regra para detecção de retrabalho


import plotly.express as px
import plotly.graph_objects as go


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
from modules.entities_utils import get_relatorios_llm_os

# Imports específicos
from modules.crud_relatorio.crud_relatorio_service import CRUDRelatorioService

##############################################################################
# LEITURA DE DADOS ###########################################################
##############################################################################
# Conexão com os bancos
pgDB = PostgresSingleton.get_instance()
pgEngine = pgDB.get_engine()

# Cria o serviço
crud_relatorio_service = CRUDRelatorioService(pgEngine)


# Obtem a lista dos relatórios disponíveis
df_regras = get_relatorios_llm_os(pgEngine)
lista_regras = df_regras.to_dict(orient="records")


##############################################################################
# CALLBACKS ##################################################################
##############################################################################

##############################################################################
# Callbacks para os inputs via URL ###########################################
##############################################################################


# Converte para int, se não for possível, retorna None
def safe_int(value):
    try:
        return int(value) if value is not None else None
    except (ValueError, TypeError):
        return None


# Preenche os dados via URL
@callback(
    Output("ler-relatorio-input-select-regra", "value"),
    Output("ler-relatorio-input-select-data", "value"),
    Input("url", "href"),
)
def cb_ler_relatorio_receber_campos_via_url(href):
    if not href:
        raise dash.exceptions.PreventUpdate

    # Faz o parse dos parâmetros da url
    parsed_url = urlparse(href)
    query_params = parse_qs(parsed_url.query)

    id_regra = safe_int(query_params.get("id_regra", [None])[0])
    data_relatorio = query_params.get("data_relatorio", [None])[0]

    # Verifica se a regra existe
    lista_id_regras = [regra["value"] for regra in lista_regras]
    if id_regra is not None and id_regra not in lista_id_regras:
        id_regra = None
        data_relatorio = None

    if id_regra is not None and data_relatorio is None:
        df_ultima_data_regra = crud_relatorio_service.get_ultima_data_regra(id_regra)
        if not df_ultima_data_regra.empty:
            data_relatorio = df_ultima_data_regra["ultimo_dia"].iloc[0]

    return id_regra, data_relatorio


# Sincroniza o store com os valores dos inputs
@callback(
    [
        Output("store-ler-relatorio", "data"),
        Output("ler-relatorio-card-input-nome", "style"),
        Output("ler-relatorio-card-input-data", "style"),
        Output("ler-relatorio-input-nome-error", "style"),
        Output("ler-relatorio-input-data-error", "style"),
    ],
    Input("ler-relatorio-input-select-regra", "value"),
    Input("ler-relatorio-input-select-data", "value"),
)
def cb_ler_relatorio_sincroniza_input_store(id_regra, dia_execucao):
    # Flags para validação
    input_regra_valido = True
    input_data_valido = True

    # Store padrão
    store_payload = {"valido": False}

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
    if id_regra:
        style_borda_input_regra = style_borda_ok
        style_campo_erro_input_regra = style_campo_erro_oculto
    else:
        input_regra_valido = False

    # Valida a data
    if dia_execucao and crud_relatorio_service.existe_execucao_regra_no_dia(id_regra, dia_execucao):
        style_borda_input_data = style_borda_ok
        style_campo_erro_input_data = style_campo_erro_oculto
    else:
        input_data_valido = False

    if input_regra_valido and input_data_valido:
        # Pega o relatório
        df_relatorio = crud_relatorio_service.get_relatorio_markdown_regra(id_regra, dia_execucao)
        relatorio_md_valido = True if not df_relatorio.empty else False

        store_payload = {
            "valido": input_regra_valido and input_data_valido and relatorio_md_valido,
            "id_regra": id_regra,
            "dia_execucao": dia_execucao,
            "relatorio_md": df_relatorio["relatorio_md"].iloc[0] if relatorio_md_valido else "",
        }

    return (
        store_payload,
        style_borda_input_regra,
        style_borda_input_data,
        style_campo_erro_input_regra,
        style_campo_erro_input_data,
    )


##############################################################################
# Callbacks do relatório #####################################################
##############################################################################


# Renderiza o relatório
@callback(
    Output("conteudo-markdown-relatorio", "children"),
    Input("store-ler-relatorio", "data"),
)
def cb_render_relatorio_markdown(store_payload):
    if not store_payload or not store_payload["valido"]:
        return ""
    else:
        return store_payload["relatorio_md"]


##############################################################################
# Layout #####################################################################
##############################################################################
layout = dbc.Container(
    [
        # Estado
        dcc.Store(id="store-ler-relatorio"),
        # Modais
        # Cabeçalho e Inputs
        html.Hr(),
        # Título Desktop
        dmc.Box(
            dbc.Row(
                [
                    dbc.Col(DashIconify(icon="carbon:rule-data-quality", width=45), width="auto"),
                    dbc.Col(
                        html.H1(
                            [
                                "Relatório de ação de\u00a0",
                                html.Strong("retrabalho"),
                            ],
                            className="align-self-center",
                        ),
                        width=True,
                    ),
                ],
                align="center",
            ),
            visibleFrom="sm",
        ),
        # Titulo Mobile
        dmc.Box(
            dbc.Row(
                [
                    dbc.Col(DashIconify(icon="carbon:rule-data-quality", width=45), width="auto"),
                    dbc.Col(
                        html.H1(
                            "Relatório de retrabalho",
                            className="align-self-center",
                        ),
                        width=True,
                    ),
                ],
                align="center",
            ),
            hiddenFrom="sm",
        ),
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        html.Div(
                            [
                                dbc.Label("Nome do Relatório"),
                                dcc.Dropdown(
                                    id="ler-relatorio-input-select-regra",
                                    options=[regra for regra in lista_regras],
                                    placeholder="Selecione uma regra...",
                                ),
                                dmc.Space(h=5),
                                dbc.FormText(
                                    html.Em(
                                        "Regra não encontrada",
                                        id="ler-relatorio-input-nome-error",
                                    ),
                                    color="secondary",
                                ),
                            ],
                            className="dash-bootstrap",
                        ),
                        id="ler-relatorio-card-input-nome",
                        body=True,
                    ),
                    md=6,
                    className="mb-3 mb-md-0",
                ),
                dbc.Col(
                    dbc.Card(
                        html.Div(
                            [
                                dbc.Label("Data do relatório"),
                                dmc.DateInput(
                                    id="ler-relatorio-input-select-data",
                                    minDate=date(2020, 8, 5),
                                    valueFormat="DD/MM/YYYY",
                                    value=(datetime.now() - timedelta(days=10)).date(),
                                ),
                                dmc.Space(h=5),
                                dbc.FormText(
                                    html.Em(
                                        "Período inválido",
                                        id="ler-relatorio-input-data-error",
                                    ),
                                    color="secondary",
                                ),
                            ],
                            className="dash-bootstrap",
                        ),
                        id="ler-relatorio-card-input-data",
                        body=True,
                    ),
                    md=6,
                    className="mb-3 mb-md-0",
                ),
            ]
        ),
        dmc.Space(h=40),
        # Relatório em MD
        dcc.Markdown(id="conteudo-markdown-relatorio", className="markdown-relatorio"),
    ]
)


##############################################################################
# Registro da página #########################################################
##############################################################################
dash.register_page(
    __name__, name="Ler Relatório", path="/relatorio-ler", icon="carbon:rule-data-quality", hide_page=True
)
