#!/usr/bin/env python
# coding: utf-8

# Tela para criar uma regra para detecção de retrabalho

##############################################################################
# IMPORTS ####################################################################
##############################################################################
# Bibliotecas básicas
from datetime import date, datetime
import pandas as pd

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
import locale_utils

# Banco de Dados
from db import PostgresSingleton

# Imports gerais
from modules.entities_utils import get_mecanicos, get_lista_os, get_oficinas, get_secoes, get_modelos, gerar_excel

# Imports específicos
from modules.crud_regra.crud_regra_service import CRUDRegraService
from modules.home.home_service import HomeService

import modules.crud_regra.graficos as crud_regra_graficos
import modules.crud_regra.tabelas as crud_regra_tabelas
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
# Callbacks para os inputs ###################################################
##############################################################################


# Função para validar o input
def input_valido(data_periodo_regra, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os):
    if data_periodo_regra is None or not data_periodo_regra or data_periodo_regra == 0 or min_dias is None:
        return False

    if lista_modelos is None or not lista_modelos or None in lista_modelos:
        return False

    if lista_oficinas is None or not lista_oficinas or None in lista_oficinas:
        return False

    if lista_secaos is None or not lista_secaos or None in lista_secaos:
        return False

    if lista_os is None or not lista_os or None in lista_os:
        return False

    return True


# Corrige o input para garantir que o termo para todas ("TODAS") não seja selecionado junto com outras opções
def corrige_input(lista, termo_all="TODAS"):
    # Caso 1: Nenhuma opcao é selecionada, reseta para "TODAS"
    if not lista:
        return [termo_all]

    # Caso 2: Se "TODAS" foi selecionado após outras opções, reseta para "TODAS"
    if len(lista) > 1 and termo_all in lista[1:]:
        return [termo_all]

    # Caso 3: Se alguma opção foi selecionada após "TODAS", remove "TODAS"
    if termo_all in lista and len(lista) > 1:
        return [value for value in lista if value != termo_all]

    # Por fim, se não caiu em nenhum caso, retorna o valor original
    return lista


@callback(
    Output("input-select-modelo-veiculos-regra-criar-retrabalho", "value"),
    Input("input-select-modelo-veiculos-regra-criar-retrabalho", "value"),
)
def corrige_input_modelos(lista_modelos):
    return corrige_input(lista_modelos, "TODOS")


@callback(
    Output("input-select-oficina-regra-criar-retrabalho", "value"),
    Input("input-select-oficina-regra-criar-retrabalho", "value"),
)
def corrige_input_oficina(lista_oficinas):
    return corrige_input(lista_oficinas)


@callback(
    Output("input-select-secao-regra-criar-retrabalho", "value"),
    Input("input-select-secao-regra-criar-retrabalho", "value"),
)
def corrige_input_secao(lista_secaos):
    return corrige_input(lista_secaos)


@callback(
    [
        Output("input-select-ordens-servico-regra-criar-retrabalho", "options"),
        Output("input-select-ordens-servico-regra-criar-retrabalho", "value"),
    ],
    [
        Input("input-select-ordens-servico-regra-criar-retrabalho", "value"),
        Input("input-select-secao-regra-criar-retrabalho", "value"),
    ],
)
def corrige_input_ordem_servico(lista_os, lista_secaos):
    # Vamos pegar as OS possíveis para as seções selecionadas
    df_lista_os_secao = df_lista_os

    if "TODAS" not in lista_secaos:
        df_lista_os_secao = df_lista_os_secao[df_lista_os_secao["SECAO"].isin(lista_secaos)]

    # Essa rotina garante que, ao alterar a seleção de oficinas ou seções, a lista de ordens de serviço seja coerente
    lista_os_possiveis = df_lista_os_secao.to_dict(orient="records")
    lista_os_possiveis.insert(0, {"LABEL": "TODAS"})

    lista_options = [{"label": os["LABEL"], "value": os["LABEL"]} for os in lista_os_possiveis]

    # OK, algor vamos remover as OS que não são possíveis para as seções selecionadas
    if "TODAS" not in lista_os:
        df_lista_os_atual = df_lista_os_secao[df_lista_os_secao["LABEL"].isin(lista_os)]
        lista_os = df_lista_os_atual["LABEL"].tolist()

    return lista_options, corrige_input(lista_os)


##############################################################################
# Callbacks para os gráficos #################################################
##############################################################################


# Callback para o grafico de síntese do retrabalho
@callback(
    Output("graph-pizza-sintese-retrabalho-regra-criar", "figure"),
    [
        Input("input-periodo-dias-monitoramento-regra-criar-retrabalho", "value"),
        Input("input-select-dias-regra-criar-retrabalho", "value"),
        Input("input-select-modelo-veiculos-regra-criar-retrabalho", "value"),
        Input("input-select-oficina-regra-criar-retrabalho", "value"),
        Input("input-select-secao-regra-criar-retrabalho", "value"),
        Input("input-select-ordens-servico-regra-criar-retrabalho", "value"),
    ],
)
def plota_grafico_pizza_sintese_criar_regra(
    data_periodo_regra, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os
):
    # Valida input
    if not input_valido(data_periodo_regra, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os):
        return go.Figure()

    # Obtem os dados
    df = crud_regra_service.get_sintese_geral(
        data_periodo_regra, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os
    )

    # Prepara os dados para o gráfico
    labels = ["Nova OS, sem retrabalho prévio", "Nova OS, com retrabalho prévio", "Retrabalho"]
    values = [
        df["TOTAL_NOVA_OS_SEM_RETRABALHO_ANTERIOR"].values[0],
        df["TOTAL_NOVA_OS_COM_RETRABALHO_ANTERIOR"].values[0],
        df["TOTAL_RETRABALHO"].values[0],
    ]

    # Gera o gráfico
    fig = crud_regra_graficos.gerar_grafico_pizza_sinteze_geral(df, labels, values)
    return fig


# Callback para o grafico de síntese do retrabalho
@callback(
    Output("tabela-previa-os-regra-criar", "rowData"),
    [
        Input("input-periodo-dias-monitoramento-regra-criar-retrabalho", "value"),
        Input("input-select-dias-regra-criar-retrabalho", "value"),
        Input("input-select-modelo-veiculos-regra-criar-retrabalho", "value"),
        Input("input-select-oficina-regra-criar-retrabalho", "value"),
        Input("input-select-secao-regra-criar-retrabalho", "value"),
        Input("input-select-ordens-servico-regra-criar-retrabalho", "value"),
    ],
)
def testa_regra_sendo_criada(data_periodo_regra, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os):
    # Valida input
    if not input_valido(data_periodo_regra, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os):
        return []

    # Obtem os dados
    df = crud_regra_service.get_previa_os_regra_detalhada(
        data_periodo_regra, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os
    )

    return df.to_dict(orient="records")


##############################################################################
# Layout #####################################################################
##############################################################################
layout = dbc.Container(
    [
        # Loading
        # dmc.LoadingOverlay(
        #     visible=True,
        #     id="loading-overlay-regra-criar",
        #     loaderProps={"size": "xl"},
        #     overlayProps={
        #         "radius": "lg",
        #         "blur": 2,
        #         "style": {
        #             "top": 0,  # Start from the top of the viewport
        #             "left": 0,  # Start from the left of the viewport
        #             "width": "100vw",  # Cover the entire width of the viewport
        #             "height": "100vh",  # Cover the entire height of the viewport
        #         },
        #     },
        #     zIndex=10,
        # ),
        # Informações / Ajuda
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
                # dbc.Col(
                #     [
                #         dbc.Alert(
                #             [
                #                 dbc.Row(
                #                     [
                #                         dbc.Col(DashIconify(icon="pepicons-pop:rewind-time", width=45), width="auto"),
                #                         dbc.Col(
                #                             html.P(
                #                                 [
                #                                     html.Strong("Período de retrabalho:"),
                #                                     """
                #                                 intervalo mínimo de dias entre OS para que uma nova ordem não seja considerada retrabalho
                #                                 """,
                #                                 ]
                #                             ),
                #                             className="mt-2",
                #                             width=True,
                #                         ),
                #                     ],
                #                     align="center",
                #                 ),
                #             ],
                #             dismissable=True,
                #             color="secondary",
                #         ),
                #     ],
                #     md=6,
                # ),
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
                                                    html.Strong("Nova OS, sem trabalho prévio:"),
                                                    """
                                                não possui OS anterior no período de retrabalho
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
                            color="success",
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
                                                    html.Strong("Nova OS, com trabalho prévio:"),
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
        # Cabeçalho
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
                                        dbc.Col(DashIconify(icon="carbon:rule-draft", width=45), width="auto"),
                                        dbc.Col(
                                            html.H1(
                                                [
                                                    "Criar \u00a0",
                                                    html.Strong("regra"),
                                                    "\u00a0 para monitoramento do retrabalho",
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
                                        html.Div(
                                            [
                                                dbc.Label("Nome da Regra de Monitoramento"),
                                                dbc.Input(
                                                    id="input-nome-regra-monitoramento-retrabalho",
                                                    type="text",
                                                    placeholder="Ex: Retrabalho OS 'Motor Esquentando' nos últimos 5 dias...",
                                                    value="",
                                                ),
                                            ],
                                            className="dash-bootstrap",
                                        ),
                                        body=True,
                                    ),
                                    md=12,
                                ),
                                dmc.Space(h=10),
                                dbc.Col(
                                    dbc.Card(
                                        html.Div(
                                            [
                                                dbc.Label("Período de Monitoramento (últimos X dias)"),
                                                dbc.InputGroup(
                                                    [
                                                        dbc.Input(
                                                            id="input-periodo-dias-monitoramento-regra-criar-retrabalho",
                                                            type="number",
                                                            placeholder="Dias",
                                                            value=5,
                                                            step=1,
                                                            min=1,
                                                        ),
                                                        dbc.InputGroupText("dias"),
                                                    ]
                                                ),
                                                dmc.Space(h=5),
                                                dbc.FormText(
                                                    html.Em(
                                                        "Período em que as OSs estarão ativas para os filtros da regra de monitoramento contínuo"
                                                    ),
                                                    color="secondary",
                                                ),
                                            ],
                                            className="dash-bootstrap",
                                        ),
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
                                                        id="input-select-dias-regra-criar-retrabalho",
                                                        options=[
                                                            {"label": "10 dias", "value": 10},
                                                            {"label": "15 dias", "value": 15},
                                                            {"label": "30 dias", "value": 30},
                                                        ],
                                                        placeholder="Período em dias",
                                                        value=10,
                                                    ),
                                                    dmc.Space(h=5),
                                                    dbc.FormText(
                                                        html.Em(
                                                            "Período mínimo de dias entre OS para que uma nova OS não seja considerada retrabalho"
                                                        ),
                                                        color="secondary",
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
                                                    dbc.Label("Modelos de Veículos"),
                                                    dcc.Dropdown(
                                                        id="input-select-modelo-veiculos-regra-criar-retrabalho",
                                                        options=[
                                                            {
                                                                "label": os["MODELO"],
                                                                "value": os["MODELO"],
                                                            }
                                                            for os in lista_todos_modelos_veiculos
                                                        ],
                                                        multi=True,
                                                        value=["TODOS"],
                                                        placeholder="Selecione um ou mais modelos...",
                                                    ),
                                                ],
                                                className="dash-bootstrap",
                                            ),
                                        ],
                                        body=True,
                                    ),
                                    md=12,
                                ),
                                dmc.Space(h=10),
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            html.Div(
                                                [
                                                    dbc.Label("Oficinas"),
                                                    dcc.Dropdown(
                                                        id="input-select-oficina-regra-criar-retrabalho",
                                                        options=[
                                                            {"label": os["LABEL"], "value": os["LABEL"]}
                                                            for os in lista_todas_oficinas
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
                                                        id="input-select-secao-regra-criar-retrabalho",
                                                        options=[
                                                            {"label": sec["LABEL"], "value": sec["LABEL"]}
                                                            for sec in lista_todas_secoes
                                                        ],
                                                        multi=True,
                                                        value=["MANUTENCAO ELETRICA", "MANUTENCAO MECANICA"],
                                                        placeholder="Selecione uma ou mais seções...",
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
                                                    dbc.Label("Ordens de Serviço"),
                                                    dcc.Dropdown(
                                                        id="input-select-ordens-servico-regra-criar-retrabalho",
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
                                    md=6,
                                ),
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            html.Div(
                                                [
                                                    dbc.Label("Alertar:"),
                                                    dbc.Checklist(
                                                        options=[
                                                            {
                                                                "label": "Nova OS, com retrabalho prévio",
                                                                "value": "nova_os_com_retrabalho_anterior",
                                                            },
                                                            {
                                                                "label": "Nova OS, sem retrabalho prévio",
                                                                "value": "nova_os_sem_retrabalho_anterior",
                                                            },
                                                            {"label": "Retrabalho", "value": "retrabalho"},
                                                            {
                                                                "label": "Correção de Primeira",
                                                                "value": "correcao_primeira",
                                                            },
                                                            {
                                                                "label": "Correção tardia",
                                                                "value": "correcao_tardia",
                                                            },
                                                        ],
                                                        value=[],
                                                        id="checklist-alertar-alvo-regra-criar-retrabalho",
                                                        inline=True,
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
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dmc.Switch(
                                                        id="switch-enviar-email-regra-criar-retrabalho",
                                                        label="Enviar email",
                                                        checked=False,
                                                        size="md",
                                                    ),
                                                    width="auto",
                                                ),
                                                dbc.Col(width=2),
                                                dbc.Col(
                                                    dbc.Input(
                                                        id="input-email-regra-criar-retrabalho",
                                                        type="email",
                                                        placeholder="fulano@odilonsantos.com",
                                                        value="",
                                                        # style={"display": "block"},
                                                    ),
                                                    width=6,
                                                ),
                                            ],
                                            align="center",
                                        ),
                                        body=True,
                                    ),
                                    md=6,
                                ),
                                dbc.Col(
                                    dbc.Card(
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dmc.Switch(
                                                        id="switch-enviar-whatsapp-regra-criar-retrabalho",
                                                        label="Enviar WhatsApp",
                                                        checked=False,
                                                        size="md",
                                                    ),
                                                    width="auto",
                                                ),
                                                dbc.Col(width=2),
                                                dbc.Col(
                                                    dmc.TextInput(
                                                        w=200,
                                                        placeholder="(62) 99999-9999",
                                                        rightSection=DashIconify(icon="logos:whatsapp-icon"),
                                                    ),
                                                    width="auto",
                                                ),
                                            ],
                                            align="center",
                                        ),
                                        body=True,
                                    ),
                                    md=6,
                                ),
                            ]
                        ),
                    ],
                    md=12,
                ),
            ]
        ),
        dmc.Space(h=30),
        # Botão Criar Regra
        dbc.Row(
            [
                dbc.Col(
                    dbc.Button(
                        "Pré-visualizar Regra",
                        id="btn-pre-visualizar-regra-monitoramento-criar-retrabalho",
                        color="primary",
                        className="me-1",
                        style={"padding": "1em", "width": "100%"},
                    ),
                    md=6,
                ),
                dbc.Col(
                    dbc.Button(
                        "Criar Regra",
                        id="btn-criar-regra-monitoramento-criar-retrabalho",
                        color="success",
                        disabled=True,
                        className="me-1",
                        style={"padding": "1em", "width": "100%"},
                    ),
                    md=6,
                ),
            ]
        ),
        dmc.Space(h=40),
        # Resumo
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
        dbc.Row(
            [
                dbc.Col(
                    dbc.Row(dcc.Graph(id="graph-pizza-sintese-retrabalho-regra-criar")),
                    md=8,
                ),
                dbc.Col(
                    html.Div(id="mensagem-sucesso", style={"marginTop": "10px", "fontWeight": "bold"}),
                ),
            ]
        ),
        dmc.Space(h=15),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="mdi:car-search-outline", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Pré-visualização das OSs que serão monitoradas pela regra criada",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        html.Div(
                                            [
                                                html.Button(
                                                    "Exportar para Excel",
                                                    id="btn-exportar-detalhamento-pag-colaborador",
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
                                                dcc.Download(id="download-excel-previa-os-regra-criar"),
                                            ],
                                            style={"text-align": "right"},
                                        ),
                                        width="auto",
                                    ),
                                ],
                                align="center",
                                justify="between",  # Deixa os itens espaçados
                            ),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        dmc.Space(h=40),
        dag.AgGrid(
            id="tabela-previa-os-regra-criar",
            columnDefs=crud_regra_tabelas.tbl_detalhamento_problema_regra,
            rowData=[],
            defaultColDef={"filter": True, "floatingFilter": True},
            columnSize="autoSize",
            dashGridOptions={
                "localeText": locale_utils.AG_GRID_LOCALE_BR,
            },
            style={"height": 400, "resize": "vertical", "overflow": "hidden"},  # -> permite resize
        ),
    ]
)


##############################################################################
# Registro da página #########################################################
##############################################################################
dash.register_page(__name__, name="Criar Regra", path="/criar-regra", icon="carbon:rule-draft", hide_page=True)
