#!/usr/bin/env python
# coding: utf-8

# Tela para gerenciar os relatórios existentes

##############################################################################
# IMPORTS ####################################################################
##############################################################################
# Bibliotecas básicas
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
from modules.crud_relatorio.crud_relatorio_service import CRUDRelatorioService
import modules.crud_relatorio.tabelas as crud_relatorio_tabelas
from modules.crud_regra.crud_regra_service import CRUDRegraService
import modules.crud_regra.tabelas as crud_regra_tabelas


##############################################################################
# LEITURA DE DADOS ###########################################################
##############################################################################
# Conexão com os bancos
pgDB = PostgresSingleton.get_instance()
pgEngine = pgDB.get_engine()

# Cria o serviço
crud_relatorio_service = CRUDRelatorioService(pgEngine)


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
    Output("tabela-relatorios-existentes", "rowData"),
    Input("tabela-relatorios-existentes", "gridReady"),
)
def cb_pag_relatorio_carregar_regras_existentes(ready):
    df_todas_regras = crud_relatorio_service.get_todas_regras_relatorios()
    lista_todas_regras = []
    if not df_todas_regras.empty:
        df_todas_regras = prepara_dados_tabela(df_todas_regras)
        lista_todas_regras = df_todas_regras.to_dict(orient="records")

    return lista_todas_regras




# Callback para acessar o botão apertado da tabela e guardar no estado
@callback(
    Output("url", "href", allow_duplicate=True),
    Output("relatorio-modal-confirma-apagar-regra", "opened"),
    Output("relatorio-nome-regra-apagar", "children"),
    # Output("id-regra-apagar-gerenciar-regra", "children"),
    Input("tabela-relatorios-existentes", "cellRendererData"),
    Input("tabela-relatorios-existentes", "virtualRowData"),
    prevent_initial_call=True,
)
def cb_pag_relatorio_botao_acao_tabela(linha, linha_virtual):
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
    dia_ultimo_relatorio = dados_regra["dia_ultimo_relatorio"]

    # Extraí a ação a ser feita
    acao = linha["colId"]

    if acao == "acao_relatorio":
        return (
            f"/relatorio-ler?id_regra={id_regra}&data_relatorio={dia_ultimo_relatorio}",
            dash.no_update,
            dash.no_update,
        )
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
        dmc.Modal(
            id="relatorio-modal-confirma-apagar-regra",
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
                            dmc.ListItem(id="relatorio-nome-regra-apagar"),
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
            id="relatorio-modal-sucesso-apagar-regra",
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
                    dbc.Row(
                        [
                            # Título desktop
                            dmc.Box(
                                html.H1(
                                    [
                                        html.Strong("Relatórios"),
                                        "\u00a0 de OS",
                                    ],
                                    className="align-self-center",
                                ),
                                visibleFrom="sm",
                            ),
                            # Título mobile
                            dmc.Box(
                                html.H1(
                                    [
                                        html.Strong("Regras"),
                                    ],
                                    className="align-self-center",
                                ),
                                hiddenFrom="sm",
                            ),
                        ],
                    ),
                    width=True,
                ),
                dbc.Col(
                    dbc.Button(
                        [DashIconify(icon="mdi:plus", className="me-1"), "Criar Novo Relatório"],
                        id="btn-criar-relatorio",
                        color="success",
                        className="me-1",
                        style={"padding": "1em"},
                    ),
                    className="mt-3 mt-md-0",
                    width="auto",
                ),
            ],
            align="center",
        ),
        # dmc.Space(h=15),
        html.Hr(),
        dmc.Space(h=20),
        dag.AgGrid(
            id="tabela-relatorios-existentes",
            columnDefs=crud_relatorio_tabelas.tbl_relatorios_existentes,
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
dash.register_page(__name__, name="Relatórios", path="/relatorio-gerenciar", icon="carbon:rule")
