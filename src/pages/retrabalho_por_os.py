#!/usr/bin/env python
# coding: utf-8

# Dashboard que lista o retrabalho de uma OS específica

##############################################################################
# IMPORTS ####################################################################
##############################################################################
# Bibliotecas básicas
from datetime import date
import pandas as pd
from collections import defaultdict

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

# Importar bibliotecas para manipulação de URL
from urllib.parse import urlparse, parse_qs


# Importar nossas constantes e funções utilitárias
import tema
import locale_utils

# Banco de Dados
from db import PostgresSingleton

# Imports específicos
from modules.os.os_service import OSService
import modules.os.tabelas as os_tabelas
import modules.os.graficos as os_graficos

##############################################################################
# LEITURA DE DADOS ###########################################################
##############################################################################
# Conexão com os bancos
pgDB = PostgresSingleton.get_instance()
pgEngine = pgDB.get_engine()

# Cria o serviço
os_service = OSService(pgEngine)

##############################################################################
# CALLBACKS ##################################################################
##############################################################################

##############################################################################
# Callbacks para os inputs ###################################################
##############################################################################


# Preenche os dados via URL
@callback(
    Output("input-detalhamento-os-selecionada", "value"),
    Output("input-detalhamento-select-dias-os-retrabalho", "value"),
    Input("url", "href"),
)
def callback_receber_campos_via_url(href):
    if not href:
        return dash.no_update, dash.no_update

    # Faz o parse dos parâmetros da url
    parsed_url = urlparse(href)
    query_params = parse_qs(parsed_url.query)

    os_numero = query_params.get("os", [None])[0]
    dias = query_params.get("mindiasretrabalho", [None])[0]

    # Converte para int dias, se não for possível, retorna None
    if dias is not None:
        try:
            dias = int(dias)
        except ValueError:
            dias = None

    return os_numero, dias


@callback(
    Output("url", "search", allow_duplicate=True),
    Input("input-detalhamento-os-selecionada", "value"),
    Input("input-detalhamento-select-dias-os-retrabalho", "value"),
    prevent_initial_call="initial_duplicate",
)
def callback_sincronizar_campos_para_url(os_numero, min_dias):
    if not os_numero or not min_dias:
        raise dash.exceptions.PreventUpdate

    return f"?os={os_numero}&mindiasretrabalho={min_dias}"


# Sincroniza o store com os valores dos inputs
@callback(
    [
        Output("store-input-dados-detalhamento-os", "data"),
        Output("input-detalhamento-os-selecionada", "error"),
    ],
    Input("input-detalhamento-os-selecionada", "value"),
    Input("input-detalhamento-select-dias-os-retrabalho", "value"),
)
def callback_sincroniza_input_store(os_value, dias_value):
    if not os_value or not dias_value:
        return {}, True

    # Verifica se a OS existe
    os_existe = os_service.os_existe(os_value, dias_value)

    if not os_existe:
        return {}, True

    return {"os_numero": os_value, "min_dias_retrabalho": dias_value}, False


# Recupera as OS escolhidas a partir do input
@callback(
    Output("store-output-dados-detalhamento-os", "data"),
    Input("store-input-dados-detalhamento-os", "data"),
)
def callback_recupera_os_armazena_store_output(data):
    saida = {
        "sucesso": False,
        "df_os": pd.DataFrame(),
        "os_numero": None,
        "min_dias_retrabalho": None,
        "codigo_veiculo": None,
        "modelo_veiculo": None,
        "problema_veiculo": None,
        "num_problema_os": None,
    }

    # Verifica se o input está vazio
    if not data:
        return saida

    # Verifica se os dados estão OK
    os_numero = data["os_numero"]
    min_dias = data["min_dias_retrabalho"]

    if not os_numero or not min_dias:
        return saida

    # Recupera os dados de retrabalho da OS
    df_os = os_service.obtem_detalhamento_os(os_numero, min_dias)

    saida["sucesso"] = True
    saida["df_os"] = df_os.to_dict(orient="records")
    
    # Demais dados
    saida["os_numero"] = os_numero
    saida["min_dias_retrabalho"] = min_dias
    saida["codigo_veiculo"] = df_os[df_os["NUMERO DA OS"] == int(os_numero)]["CODIGO DO VEICULO"].values[0]
    saida["modelo_veiculo"] = df_os[df_os["NUMERO DA OS"] == int(os_numero)]["DESCRICAO DO MODELO"].values[0]
    saida["problema_veiculo"] = df_os[df_os["NUMERO DA OS"] == int(os_numero)]["DESCRICAO DO SERVICO"].values[0]
    saida["num_problema_os"] = df_os[df_os["NUMERO DA OS"] == int(os_numero)]["problem_no"].values[0]

    return saida


##############################################################################
### Callbacks para os labels #################################################
##############################################################################


def gera_labels_inputs_detalhamento_os(campo):
    # Cria o callback
    @callback(
        Output(component_id=f"{campo}-labels-detalhamento-os", component_property="children"),
        Input("store-output-dados-detalhamento-os", "data"),
    )
    def atualiza_labels_inputs_detalhamento_os(data):
        labels = [
            dmc.Badge("Filtro", color="gray", variant="outline"),
            dmc.Badge("Escolha a OS primeiro", variant="outline"),
        ]

        if not data["sucesso"]:
            return dmc.Group(labels)
        
        # Obtem os dados
        numero_os = data["os_numero"]
        codigo_veiculo = data["codigo_veiculo"]
        modelo_veiculo = data["modelo_veiculo"]
        problema_veiculo = data["problema_veiculo"]
        num_problema_os = data["num_problema_os"]

        labels = [
            dmc.Badge(f"OS: {numero_os}", variant="dot"),
            dmc.Badge(f"Veículo: {codigo_veiculo} - {modelo_veiculo}", variant="dot"),
            dmc.Badge(f"{problema_veiculo}", variant="dot"),
            dmc.Badge(f"Problema # {num_problema_os}", variant="dot"),
        ]

        return labels

    # Cria o componente
    return dmc.Group(id=f"{campo}-labels-detalhamento-os", children=[])


##############################################################################
# Callbacks para os indicadores ##############################################
##############################################################################


@callback(
    [
        Output("card-detalhamento-os-classificacao", "children"),
        Output("card-detalhamento-os-num-problema-os", "children"),
        Output("card-detalhamento-os-colaborador", "children"),
        Output("card-detalhamento-os-data-inicio-os", "children"),
        Output("card-detalhamento-os-data-fim-os", "children"),
        Output("card-detalhamento-os-sintoma-os", "children"),
        Output("card-detalhamento-os-correcao-os", "children"),
        Output("card-detalhamento-os-pecas-os", "children"),
    ],
    Input("store-output-dados-detalhamento-os", "data"),
)
def atualiza_dados_card_detalhamento_os(data):
    if not data["sucesso"]:
        return [
            "❓ OS: Não Informada",
            "💣 Número do Problema: Não Informado",
            "🧑‍🔧 Colaborador: Não Informado",
            "🚩 Data de abertura da OS: Não Informado",
            "📌 Data de fechamento da OS: Não Informado",
            "💡 Sintoma: Não Informado",
            "🔧 Correção: Não Informado",
            "🧰 Peças trocadas: Não Informado",
        ]

    # Obtem os dados
    os_numero = data["os_numero"]
    min_dias = data["min_dias_retrabalho"]
    num_problema_os = data["num_problema_os"]   
    df_os = pd.DataFrame(data["df_os"]).copy()

    # Pega o status da OS
    txt_status_label = df_os[df_os["NUMERO DA OS"] == int(os_numero)]["status_os_label"].values[0]
    txt_status_emoji = df_os[df_os["NUMERO DA OS"] == int(os_numero)]["status_os_emoji"].values[0]
    txt_os_classificacao = f"{txt_status_emoji} OS {os_numero} ({txt_status_label})"

    # Pega os demais dados
    txt_colaborador = df_os[df_os["NUMERO DA OS"] == int(os_numero)]["nome_colaborador"].values[0]
    txt_data_inicio_os = df_os[df_os["NUMERO DA OS"] == int(os_numero)]["DATA DA ABERTURA LABEL"].values[0]
    txt_data_fim_os = df_os[df_os["NUMERO DA OS"] == int(os_numero)]["DATA DO FECHAMENTO LABEL"].values[0]
    txt_sintoma_os = df_os[df_os["NUMERO DA OS"] == int(os_numero)]["SINTOMA"].values[0]
    txt_correcao_os = df_os[df_os["NUMERO DA OS"] == int(os_numero)]["CORRECAO"].values[0]

    # Pega as peças trocadas
    txt_pecas_os_raw = df_os[df_os["NUMERO DA OS"] == int(os_numero)]["pecas_trocadas_str"].values[0]
    lista_pecas_os = txt_pecas_os_raw.split("__SEP__")
    lista_pecas_os.sort()

    html_pecas_os = html.Div([html.Span("🧰 Peças trocadas:"), html.Ul([html.Li(p) for p in lista_pecas_os])])

    return [
        txt_os_classificacao,
        "💣 Número do Problema: " + str(df_os[df_os["NUMERO DA OS"] == int(os_numero)]["problem_no"].values[0]),
        "🧑‍🔧 Colaborador: " + txt_colaborador,
        "🚩 Data de abertura da OS: " + txt_data_inicio_os,
        "📌 Data de fechamento da OS: " + txt_data_fim_os,
        "💡 Sintoma: " + txt_sintoma_os,
        "🔧 Correção: " + txt_correcao_os,
        html_pecas_os,
    ]


@callback(
    [
        Output("card-detalhamento-os-codigo-veiculo", "children"),
        Output("card-detalhamento-os-modelo-veiculo", "children"),
        Output("card-detalhamento-os-problema-veiculo", "children"),
        Output("card-detalhamento-os-total-os-no-problema", "children"),
        Output("card-detalhamento-os-data-inicio-problema", "children"),
        Output("card-detalhamento-os-data-fim-problema", "children"),
        Output("card-detalhamento-os-diff-dias-problema", "children"),
        Output("card-detalhamento-os-pecas-problema", "children"),
    ],
    Input("store-output-dados-detalhamento-os", "data"),
)
def atualiza_dados_card_detalhamento_problema(data):
    if not data["sucesso"]:
        return [
            "🚍 Código do veículo: Não Informado",
            "⚙️ Modelo do veículo: Não Informado",
            "💣 Problema da OS: Não Informado",
            "📋 Total de OS no problema: Não Informado",
            "🚩 Data de abertura do problema: Não Informado",
            "📌 Data de fechamento do problema: Não Informado",
            "📅 Diferença de dias desde o início do problema: Não Informado",
            "🧰 Peças trocadas até agora: Não Informado",
        ]

    # Obtem os dados
    os_numero = data["os_numero"]
    min_dias = data["min_dias_retrabalho"]
    df_os = pd.DataFrame(data["df_os"]).copy()

    # Pega o problema da OS alvo
    problem_no = df_os[df_os["NUMERO DA OS"] == int(os_numero)]["problem_no"].values[0]

    # Pega o status da OS
    txt_status_label = df_os[df_os["NUMERO DA OS"] == int(os_numero)]["status_os_label"].values[0]
    txt_status_emoji = df_os[df_os["NUMERO DA OS"] == int(os_numero)]["status_os_emoji"].values[0]

    # Descobre o serviço, modelo e codigo do veículo
    txt_codigo_veiculo = df_os[df_os["NUMERO DA OS"] == int(os_numero)]["CODIGO DO VEICULO"].values[0]
    txt_modelo_veiculo = df_os[df_os["NUMERO DA OS"] == int(os_numero)]["DESCRICAO DO MODELO"].values[0]
    txt_problema_veiculo = df_os[df_os["NUMERO DA OS"] == int(os_numero)]["DESCRICAO DO SERVICO"].values[0]

    # Filtra OS no mesmo problema
    df_problema_os_alvo = df_os[(df_os["problem_no"] == problem_no)]

    # Total de OS no problema
    txt_total_os_no_problema = df_problema_os_alvo.shape[0]

    # Data do início e fim do problema, primeiro arruma datas
    df_problema_os_alvo["DATA DA ABERTURA DA OS DT"] = pd.to_datetime(
        df_problema_os_alvo["DATA DA ABERTURA DA OS DT"], errors="coerce"
    )
    df_problema_os_alvo["DATA DO FECHAMENTO DA OS DT"] = pd.to_datetime(
        df_problema_os_alvo["DATA DO FECHAMENTO DA OS DT"], errors="coerce"
    )

    # Calcula a data de início e fim do problema
    data_inicio_problema = df_problema_os_alvo["DATA DA ABERTURA DA OS DT"].min()
    data_fim_problema = df_problema_os_alvo["DATA DO FECHAMENTO DA OS DT"].max()
    txt_data_inicio_problema = data_inicio_problema.strftime("%d/%m/%Y")
    txt_data_fim_problema = data_fim_problema.strftime("%d/%m/%Y")

    txt_diff_dias_problema = (data_fim_problema - data_inicio_problema).days

    # Pega as peças trocadas
    hashmap_pecas_problema = defaultdict(set)

    for index, row in df_problema_os_alvo.iterrows():
        numero_os = row["NUMERO DA OS"]
        pecas_os = hashmap_pecas_problema[numero_os]
        pecas_os.update(row["pecas_trocadas_str"].split("__SEP__"))
        hashmap_pecas_problema[numero_os] = pecas_os

    lista_pecas_problema = []
    for pecas_os in hashmap_pecas_problema.values():
        lista_pecas_problema.extend(pecas_os)

    # Remove "Nenhuma" from lista_pecas_problema se houver alguma peca diferente de "Nenhuma"
    lista_pecas_problema_final = []
    lista_pecas_problema_sem_nenhuma = [p for p in lista_pecas_problema if p != "Nenhuma"]

    if len(lista_pecas_problema_sem_nenhuma) > 0:
        lista_pecas_problema_final = lista_pecas_problema_sem_nenhuma
    else:
        lista_pecas_problema_final = ["Nenhuma"]

    # Ordena a lista de peças
    lista_pecas_problema_final.sort()

    html_pecas_problema = html.Div(
        [html.Span("🧰 Peças trocadas até agora:"), html.Ul([html.Li(p) for p in lista_pecas_problema_final])]
    )

    return [
        "🚍 Código do veículo: " + txt_codigo_veiculo,
        "⚙️ Modelo do veículo: " + txt_modelo_veiculo,
        "💣 Problema da OS: " + txt_problema_veiculo,
        "📋 Total de OSs no problema: " + str(txt_total_os_no_problema),
        "🚩 Data de abertura do problema: " + txt_data_inicio_problema,
        "📌 Data de fechamento do problema: " + txt_data_fim_problema,
        "📅 Diferença de dias desde o início do problema: " + str(txt_diff_dias_problema),
        html_pecas_problema,
    ]


##############################################################################
# Callbacks para a linha do tempo ############################################
##############################################################################


# Preenche a linha do tempo com os dados do store
@callback(
    Output("timeline-detalhamento-os", "children"),
    Input("store-output-dados-detalhamento-os", "data"),
)
def preencher_timeline(data):
    if not data["sucesso"]:
        return []

    os_numero = data["os_numero"]
    min_dias = data["min_dias_retrabalho"]
    df_os = pd.DataFrame(data["df_os"]).copy()

    # Preenche a linha do tempo somente com o problema da OS atual
    problem_no = df_os[df_os["NUMERO DA OS"] == int(os_numero)]["problem_no"].values[0]
    df_problema_os_alvo = df_os[(df_os["problem_no"] == problem_no)]
    # df_problema_os_alvo_anterior = df_os[(df_os["problem_no"] == problem_no - 1)]

    problemas_ativos = df_problema_os_alvo.shape[0]

    # Problema atual (vem com line solid)
    timeline_items = []
    for index, row in df_problema_os_alvo.iterrows():
        titulo_item = dmc.Text(f"OS {row['NUMERO DA OS']}", size="lg")
        item_body = dbc.Row(
            [
                # dmc.Text(row["status_os"], size="sm", className="text-muted"),
                dmc.Text("🧑‍🔧 Colaborador: " + row["nome_colaborador"], size="sm", className="text-muted"),
                dmc.Text("🚩 Início: " + row["DATA DA ABERTURA LABEL"], size="sm", className="text-muted"),
                dmc.Text("📌 Fim: " + row["DATA DO FECHAMENTO LABEL"], size="sm", className="text-muted"),
                dmc.Text("💬 Correção: " + row["CORRECAO"], size="sm", className="text-muted"),
            ]
        )

        dmc_timeline_item = dmc.TimelineItem(
            bullet=row["status_os_emoji"],
            title=titulo_item,
            lineVariant="solid",
            children=item_body,
        )

        # Se for a OS atual, adiciona um highlight especial
        if row["NUMERO DA OS"] == int(os_numero):
            dmc_timeline_item = dmc.TimelineItem(
                bullet=row["status_os_emoji"],
                title=titulo_item,
                lineVariant="solid",
                children=dmc.Paper(
                    withBorder=True, radius="lg", p="md", style={"backgroundColor": "#fff8e1"}, children=item_body
                ),
            )

        timeline_items.append(dmc_timeline_item)

    # Problema anterior (vem com line)
    # for index, row in df_problema_os_alvo_anterior.iterrows():
    #     titulo_item = dmc.Text(f"OS {row['NUMERO DA OS']}", size="lg")
    #     item_body = dbc.Row(
    #         [
    #             # dmc.Text(row["status_os"], size="sm", className="text-muted"),
    #             dmc.Text("🧑‍🔧 Colaborador: " + row["nome_colaborador"], size="sm", className="text-muted"),
    #             dmc.Text("🚩 Início: " + row["DATA DA ABERTURA LABEL"], size="sm", className="text-muted"),
    #             dmc.Text("📌 Fim: " + row["DATA DO FECHAMENTO LABEL"], size="sm", className="text-muted"),
    #         ]
    #     )
    #     dmc_timeline_item = dmc.TimelineItem(
    #         bullet=row["status_os_emoji"],
    #         title=titulo_item,
    #         children=item_body,
    #         lineVariant="dashed",
    #     )
    #     timeline_items.append(dmc_timeline_item)

    return dmc.Timeline(
        active=problemas_ativos, lineWidth=2, color="lightgray", radius="lg", bulletSize=30, children=timeline_items
    )


##############################################################################
# Callbacks para as tabelas ##################################################
##############################################################################


# Preenche a tabela com os dados do store
@callback(
    Output("tabela-detalhamento-previa-os-retrabalho", "rowData"),
    Input("store-output-dados-detalhamento-os", "data"),
)
def preencher_tabela(data):
    if not data["sucesso"]:
        return []

    df_os = pd.DataFrame(data["df_os"])

    return df_os.to_dict(orient="records")


##############################################################################
# Callbacks para o gantt #####################################################
##############################################################################


# Preenche o gantt com os dados do store
@callback(
    Output("graph-gantt-historico-problema-detalhamento-os", "figure"),
    Input("store-output-dados-detalhamento-os", "data"),
)
def preencher_gantt(data):
    if not data["sucesso"]:
        return go.Figure()

    # Obtem os dados
    df_os = pd.DataFrame(data["df_os"])
    problem_no = data["num_problema_os"]
    
    # Gera o gráfico
    fig = os_graficos.gerar_grafico_gantt_historico_problema_detalhamento_os(df_os, problem_no)

    return fig


##############################################################################
# Layout #####################################################################
##############################################################################
layout = dbc.Container(
    [
        # Estado
        dcc.Store(id="store-input-dados-detalhamento-os"),
        dcc.Store(id="store-output-dados-detalhamento-os"),
        # Alerta
        dbc.Alert(
            [
                dbc.Row(
                    [
                        dbc.Col(DashIconify(icon="ooui:alert", width=45), width="auto"),
                        dbc.Col(
                            html.P(
                                """
                                A tela permite analisar o retrabalho de uma OS específica, detalhando o histórico do que foi feito.
                                """
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
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="vaadin:lines-list", width=45), width="auto"),
                dbc.Col(
                    html.H1(
                        [
                            "Retrabalho por\u00a0",
                            html.Strong("Ordem de Serviço (OS)"),
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
                        [
                            html.Div(
                                [
                                    dbc.Label("Ordem de Serviço"),
                                    dmc.TextInput(
                                        id="input-detalhamento-os-selecionada",
                                        placeholder="Digite o número da OS",
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
                                        id="input-detalhamento-select-dias-os-retrabalho",
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
            ]
        ),
        dmc.Space(h=40),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Row(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(DashIconify(icon="wpf:statistics", width=45), width="auto"),
                                    dbc.Col(
                                        dbc.Row(
                                            [
                                                html.H4(
                                                    "Resumo da OS",
                                                    className="align-self-center",
                                                ),
                                            ]
                                        ),
                                        width=True,
                                    ),
                                ],
                            ),
                            dmc.Space(h=40),
                            dbc.Row(
                                [
                                    dbc.ListGroup(
                                        [
                                            dbc.ListGroupItem("", id="card-detalhamento-os-classificacao", active=True),
                                            dbc.ListGroupItem("", id="card-detalhamento-os-num-problema-os"),
                                            dbc.ListGroupItem("", id="card-detalhamento-os-colaborador"),
                                            dbc.ListGroupItem("", id="card-detalhamento-os-data-inicio-os"),
                                            dbc.ListGroupItem("", id="card-detalhamento-os-data-fim-os"),
                                            dbc.ListGroupItem("", id="card-detalhamento-os-sintoma-os"),
                                            dbc.ListGroupItem("", id="card-detalhamento-os-correcao-os"),
                                            dbc.ListGroupItem("", id="card-detalhamento-os-pecas-os"),
                                        ]
                                    )
                                ]
                            ),
                        ],
                        className="m-1",
                    ),
                    md=6,
                ),
                dbc.Col(
                    dbc.Row(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(DashIconify(icon="mdi:bomb", width=45), width="auto"),
                                    dbc.Col(
                                        dbc.Row(
                                            [
                                                html.H4(
                                                    "Resumo do problema",
                                                    className="align-self-center",
                                                ),
                                            ]
                                        ),
                                        width=True,
                                    ),
                                ],
                            ),
                            dmc.Space(h=40),
                            dbc.Row(
                                [
                                    dbc.ListGroup(
                                        [
                                            dbc.ListGroupItem(
                                                "", id="card-detalhamento-os-codigo-veiculo", active=True
                                            ),
                                            dbc.ListGroupItem("", id="card-detalhamento-os-modelo-veiculo"),
                                            dbc.ListGroupItem("", id="card-detalhamento-os-problema-veiculo"),
                                            dbc.ListGroupItem("", id="card-detalhamento-os-total-os-no-problema"),
                                            dbc.ListGroupItem("", id="card-detalhamento-os-data-inicio-problema"),
                                            dbc.ListGroupItem("", id="card-detalhamento-os-data-fim-problema"),
                                            dbc.ListGroupItem("", id="card-detalhamento-os-diff-dias-problema"),
                                            dbc.ListGroupItem("", id="card-detalhamento-os-pecas-problema"),
                                        ]
                                    ),
                                ]
                            ),
                        ],
                        className="m-1",
                    ),
                    md=6,
                ),
            ],
        ),
        dmc.Space(h=40),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="clarity:timeline-line", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Linha do tempo do retrabalho da OS selecionada",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            gera_labels_inputs_detalhamento_os("detalhamento-os-timeline"),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        dmc.Space(h=40),
        html.Div(id="timeline-detalhamento-os"),
        dmc.Space(h=20),
        dmc.Group(
            [
                dmc.Text("Legenda:"),
                dmc.Badge(
                    "🟦 Nova OS, sem retrabalho prévio",
                    color="blue",
                    variant="outline",
                ),
                dmc.Badge(
                    "🟨 Nova OS, com retrabalho prévio",
                    color="yellow",
                    variant="outline",
                ),
                dmc.Badge(
                    "🟥 Retrabalho",
                    color="red",
                    variant="outline",
                ),
                dmc.Badge(
                    "🟩 Correção Primeira",
                    color="green",
                    variant="outline",
                ),
                dmc.Badge(
                    "🟪 Correção Tardia",
                    color="purple",
                    variant="outline",
                ),
            ]
        ),
        dmc.Space(h=60),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="fa6-solid:chart-gantt", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Histórico (diagrama de Gantt) do problema selecionado ",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            gera_labels_inputs_detalhamento_os("detalhamento-os-gantt"),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        dcc.Graph(id="graph-gantt-historico-problema-detalhamento-os"),
        dmc.Space(h=20),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="mdi:car-search-outline", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Detalhamento e histórico da OS e do problema selecionado",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            gera_labels_inputs_detalhamento_os("detalhamento-os-tabela"),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        dmc.Space(h=40),
        dag.AgGrid(
            id="tabela-detalhamento-previa-os-retrabalho",
            columnDefs=os_tabelas.tbl_detalhamento_problema_os,
            rowData=[],
            defaultColDef={"filter": True, "floatingFilter": True},
            columnSize="autoSize",
            dashGridOptions={
                "localeText": locale_utils.AG_GRID_LOCALE_BR,
                "enableCellTextSelection": True,
                "ensureDomOrder": True,
            },
            style={"height": 600, "resize": "vertical", "overflow": "hidden"},  # -> permite resize
        ),
        dmc.Space(h=80),
    ]
)

##############################################################################
# Registro da página #########################################################
##############################################################################
dash.register_page(__name__, name="OS", path="/retrabalho-por-os", icon="vaadin:lines-list")
