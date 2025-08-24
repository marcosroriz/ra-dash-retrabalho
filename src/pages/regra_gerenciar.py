#!/usr/bin/env python
# coding: utf-8

# Tela para gerenciar as regras existentes

##############################################################################
# IMPORTS ####################################################################
##############################################################################
# Bibliotecas básicas
from datetime import date, datetime
import json
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



##############################################################################
# CALLBACKS ##################################################################
##############################################################################

# Callback para carregar as regras existentes
@callback(
    Output("tabela-regras-existentes", "rowData"),
    Input("tabela-regras-existentes", "gridReady"),
)
def cb_carregar_regras_existentes(ready):
    df_todas_regras = crud_regra_service.get_todas_regras()
    lista_todas_regras = []
    if not df_todas_regras.empty:
        df_todas_regras = prepara_dados_tabela(df_todas_regras)
        lista_todas_regras = df_todas_regras.to_dict(orient="records")

    return lista_todas_regras

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


# Callback para o botão de cancelar apagar regra
@callback(
    Output("modal-confirma-apagar-gerenciar-regra", "opened", allow_duplicate=True),
    Input("btn-cancelar-apagar-regra", "n_clicks"),
    prevent_initial_call=True,
)
def cb_botao_cancelar_apagar_regra(n_clicks):
    if n_clicks is None or n_clicks == 0:
        return dash.no_update
    else:
        return False
    
# Callback para o botão de confirmar apagar regra
# Saída: 
# - Fecha o Modal de confirmação de apagar regra
# - Abre o Modal de sucesso de apagar regra
# - Atualiza tabela de regras existentes
@callback(
    [
        Output("modal-confirma-apagar-gerenciar-regra", "opened", allow_duplicate=True),
        Output("modal-sucesso-apagar-gerenciar-regra", "opened", allow_duplicate=True),
        Output("tabela-regras-existentes", "rowData", allow_duplicate=True),
    ],
    Input("btn-confirma-apagar-regra", "n_clicks"),
    Input("nome-regra-apagar-gerenciar-regra", "children"),
    prevent_initial_call=True,
    running=[(Output("loading-overlay-guia-gerenciar-regra", "visible"), True, False)],
)
def cb_botao_confirma_apagar_regra(n_clicks, nome_regra):
    if n_clicks is None or n_clicks == 0:
        return dash.no_update, dash.no_update, dash.no_update
    else:
        match = re.search(r"ID:\s*(\d+)", nome_regra)
        id_regra = int(match.group(1))

        # Apagar a regra
        crud_regra_service.apagar_regra(id_regra)

        # Atualiza a tabela
        df_todas_regras = crud_regra_service.get_todas_regras()
        lista_todas_regras = []
        if not df_todas_regras.empty:
            df_todas_regras = prepara_dados_tabela(df_todas_regras)
            lista_todas_regras = df_todas_regras.to_dict(orient="records")

        return False, True, lista_todas_regras
    
# Callback para fechar o modal de sucesso de apagar regra
@callback(
    Output("modal-sucesso-apagar-gerenciar-regra", "opened", allow_duplicate=True),
    Input("btn-close-modal-sucesso-apagar-gerenciar-regra", "n_clicks"),
    prevent_initial_call=True,
)
def cb_botao_close_modal_sucesso_apagar_regra(n_clicks):
    if n_clicks is None or n_clicks == 0:
        return dash.no_update
    else:
        return False

# Callback para acessar o botão apertado da tabela e guardar no estado
@callback(
    Output("url", "href", allow_duplicate=True),
    Output("modal-confirma-apagar-gerenciar-regra", "opened"),
    Output("nome-regra-apagar-gerenciar-regra", "children"),
    # Output("id-regra-apagar-gerenciar-regra", "children"),
    Input("tabela-regras-existentes", "cellRendererData"),
    Input("tabela-regras-existentes", "virtualRowData"),
    prevent_initial_call=True,
)
def cb_botao_apagar_regra(linha, linha_virtual):
    # Obtém o contexto do callback
    ctx = callback_context
    if not ctx.triggered:
        # Evita execução desnecessária
        return dash.no_update, dash.no_update, dash.no_update

    # Verifica se o callback foi acionado pelo botão de visualização
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[1]

    if triggered_id != "cellRendererData":
        return dash.no_update, dash.no_update, dash.no_update

    # Verifica se a linha é valida
    if linha is None or linha_virtual is None:
        return dash.no_update, dash.no_update, dash.no_update
    
    # Pega os dados da regra clicada
    dados_regra = linha_virtual[linha["rowIndex"]]
    nome_regra = dados_regra["nome"]
    id_regra = dados_regra["id"]

    # Extraí a ação a ser feita
    acao = linha["colId"]

    if acao == "acao_relatorio":
        return f"/regra-relatorio?id_regra={id_regra}", dash.no_update, dash.no_update
    elif acao == "acao_editar":
        return f"/regra-editar?id_regra={id_regra}", dash.no_update, dash.no_update
    elif acao == "acao_apagar":
        nome_regra = f"{nome_regra} (ID: {id_regra})"
        return dash.no_update, True, nome_regra
    else:
        return dash.no_update, dash.no_update, dash.no_update   


##############################################################################
# Layout #####################################################################
##############################################################################
layout = dbc.Container(
    [
    # Loading
        dmc.LoadingOverlay(
            visible=False,
            id="loading-overlay-guia-gerenciar-regra",
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
        dmc.Modal(
            id="modal-confirma-apagar-gerenciar-regra",
            centered=True,
            radius="lg",
            size="md",
            opened=False,
            closeOnClickOutside=False,
            closeOnEscape=True,
            children=dmc.Stack(
                [
                    dmc.ThemeIcon(
                        radius="lg",
                        size=128,
                        color="red",
                        variant="light",
                        children=DashIconify(icon="material-symbols:delete", width=128, height=128),
                    ),
                    dmc.Title("Apagar Regra?", order=1),
                    dmc.Text("Você tem certeza que deseja apagar a regra?"),
                    dmc.List(
                        [
                            dmc.ListItem(id="nome-regra-apagar-gerenciar-regra"),
                            # dmc.ListItem(id="id-regra-apagar-gerenciar-regra"),
                        ],
                    ),
                    dmc.Text("Esta ação não poderá ser desfeita."),
                    dmc.Group(
                        [
                            dmc.Button("Cancelar", id="btn-cancelar-apagar-regra", variant="default"),
                            dmc.Button(
                                "Apagar",
                                color="red",
                                variant="outline",
                                id="btn-confirma-apagar-regra",
                            ),
                        ],
                        justify="flex-end",
                    ),
                    dmc.Space(h=20),
                ],
                align="center",
                gap="md",
            ),
        ),
        dmc.Modal(
            id="modal-sucesso-apagar-gerenciar-regra",
            centered=True,
            radius="lg",
            size="lg",
            opened=False,
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
                    dmc.Text("A regra foi apagada com sucesso."),
                    dmc.Group(
                        [
                            dmc.Button(
                                "Fechar",
                                color="green",
                                variant="outline",
                                id="btn-close-modal-sucesso-apagar-gerenciar-regra",
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
            rowData=[],
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
dash.register_page(__name__, name="Regras", path="/regra-gerenciar", icon="carbon:rule")
