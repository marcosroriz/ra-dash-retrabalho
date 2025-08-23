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
from dash import html, callback, Input, Output, callback_context

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

# Imports específicos
from modules.crud_regra.crud_regra_service import CRUDRegraService
import modules.crud_regra.tabelas as crud_regra_tabelas


##############################################################################
# LEITURA DE DADOS ###########################################################
##############################################################################
# Conexão com os bancos
pgDB = PostgresSingleton.get_instance()
pgEngine = pgDB.get_engine()

# Cria o serviço
crud_regra_service = CRUDRegraService(pgEngine)

# Função para preparar os dados para a tabela
def prepara_dados_tabela(df_regras):
    df_regras["acao_relatorio"] = "📋 Relatório"
    df_regras["acao_editar"] = "✏️ Editar"
    df_regras["acao_apagar"] = "❌ Apagar"
    return df_regras

# Obtem todas as regras e prepara os dados para a tabela
df_todas_regras = crud_regra_service.get_todas_regras()
df_todas_regras = prepara_dados_tabela(df_todas_regras)
lista_todas_regras = df_todas_regras.to_dict(orient="records")

##############################################################################
# CALLBACKS ##################################################################
##############################################################################

# Callback botão criar regra
@callback(
    Output("url", "href", allow_duplicate=True),
    Input("btn-criar-regra", "n_clicks"),
    prevent_initial_call=True,
)
def cb_botao_criar_regra(n_clicks):
    if n_clicks is None:
        return dash.no_update

    return "/regra-criar"

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
                    ),
                ],
                align="center",
                gap="xl",
            ),
        ),
        # Cabeçalho e Inputs
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="carbon:rule", width=45), width="auto"),
                dbc.Col(
                    html.H1(
                        [
                            html.Strong("Regras"),
                            "\u00a0 de Monitoramento",
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
        dmc.Space(h=20),
        dag.AgGrid(
            id="tabela-regras-existentes",
            columnDefs=crud_regra_tabelas.tbl_regras_existentes,
            rowData=lista_todas_regras,
            defaultColDef={"filter": True, "floatingFilter": True},
            columnSize="responsiveSizeToFit",
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
