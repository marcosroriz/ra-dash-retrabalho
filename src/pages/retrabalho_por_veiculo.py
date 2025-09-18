#!/usr/bin/env python
# coding: utf-8

# Dashboard que lista o retrabalho de uma ou mais OS

##############################################################################
# IMPORTS ####################################################################
##############################################################################
# Bibliotecas básicas
from datetime import datetime
import pandas as pd
import time

# Importar bibliotecas para manipulação de URL
import ast
from urllib.parse import urlparse, parse_qs

# Importar bibliotecas do dash básicas e plotly
import dash
from dash import html, dcc, callback, Input, Output
import plotly.graph_objects as go

# Importar bibliotecas do bootstrap e ag-grid
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
from dash import callback_context

# Dash componentes Mantine e icones
import dash_mantine_components as dmc
from dash_iconify import DashIconify

# Importar nossas constantes e funções utilitárias
import locale_utils

# Banco de Dados
from db import PostgresSingleton

# Import de arquivos
import modules.veiculos.graficos as veiculos_graficos
from modules.entities_utils import get_modelos, get_lista_os, get_veiculos, get_oficinas, get_secoes
from modules.veiculos.tabelas import *
from modules.sql_utils import *
from modules.veiculos.inputs import input_valido4
from modules.veiculos.graficos import *
from modules.veiculos.veiculo_service import *
from modules.veiculos.helps import HelpsVeiculos


##############################################################################
# LEITURA DE DADOS ###########################################################
##############################################################################
# Conexão com os bancos
pgDB = PostgresSingleton.get_instance()
pgEngine = pgDB.get_engine()

# Cria o serviço
veiculos_service = VeiculoService(pgEngine)

# Obtém a lista de veículos
df_veiculos = get_veiculos(pgEngine)
df_veiculos.sort_values("VEICULO", inplace=True)

# Obtém a lista de oficinas
df_oficinas = get_oficinas(pgEngine)
lista_todas_oficinas = df_oficinas.to_dict(orient="records")
lista_todas_oficinas.insert(0, {"LABEL": "TODAS"})

# Obtem a lista de OS
df_lista_os = get_lista_os(pgEngine)
lista_todas_os = df_lista_os.to_dict(orient="records")
lista_todas_os.insert(0, {"LABEL": "TODAS"})

# Modelos
df_lista_modelos = get_modelos(pgEngine)
df_lista_modelos.sort_values("MODELO", inplace=True)
lista_todos_modelos = df_lista_modelos.to_dict(orient="records")
lista_todos_modelos.insert(0, {"LABEL": "TODOS", "MODELO": "TODOS"})

# Obtem a lista de Seções
df_secoes = get_secoes(pgEngine)
lista_todas_secoes = df_secoes.to_dict(orient="records")
lista_todas_secoes.insert(0, {"LABEL": "TODAS"})


##############################################################################
# CALLBACKS ##################################################################
##############################################################################


##############################################################################
# Callbacks para os inputs via URL ###########################################
##############################################################################

# # Função auxiliar para transformar string '[%27A%27,%20%27B%27]' → ['A', 'B']
# def parse_list_param(param):
#     if param:
#         try:
#             return ast.literal_eval(param)
#         except:
#             return []
#     return []


# # Preenche os dados via URL
# @callback(
#     Output("input-select-veiculos-veiculo", "value"),
#     Output("input-intervalo-datas-veiculo", "value"),
#     Output("input-min-dias-veiculo", "value"),
#     Output("input-select-secao-veiculo", "value"),
#     Output("input-select-ordens-servico-veiculos", "value"),
#     Output("input-select-modelos-veiculo", "value"),
#     Output("input-select-oficina-veiculo", "value"),
#     Input("url", "href"),
# )
# def callback_receber_campos_via_url(href):
#     if not href:
#         return (
#             dash.no_update,
#             dash.no_update,
#             dash.no_update,
#             dash.no_update,
#             dash.no_update,
#             dash.no_update,
#             dash.no_update,
#         )

#     # Faz o parse dos parâmetros da url
#     parsed_url = urlparse(href)
#     query_params = parse_qs(parsed_url.query)

#     print("================================================")
#     print("RECEBI OS PARAMETROS DA URL")
#     print(query_params)
#     print("================================================")

#     id_veiculo = query_params.get("id_veiculo", [1202])[0]
#     data_hoje = datetime.now().strftime("%Y-%m-%d")
#     datas = [query_params.get("data_inicio", ["2024-08-01"])[0], query_params.get("data_fim", [data_hoje])[0]]
#     min_dias = query_params.get("min_dias", [10])[0]
#     lista_secaos = parse_list_param(query_params.get("lista_secaos", [None])[0])
#     lista_os = parse_list_param(query_params.get("lista_os", [None])[0])
#     lista_modelos = parse_list_param(query_params.get("lista_modelos", [None])[0])
#     lista_oficinas = parse_list_param(query_params.get("lista_oficinas", [None])[0])

#     # Converte para int, se não for possível, retorna None
#     if id_veiculo is not None:
#         try:
#             id_veiculo = int(id_veiculo)
#         except ValueError:
#             id_veiculo = None

#     if min_dias is not None:
#         try:
#             min_dias = int(min_dias)
#         except ValueError:
#             min_dias = None

#     print("================================================")
#     print("RETORNEI OS PARAMETROS DA URL")
#     print(id_veiculo, datas, min_dias, lista_secaos, lista_os, lista_modelos, lista_oficinas)
#     print("================================================")
#     return str(id_veiculo), datas, min_dias, lista_secaos, lista_os, lista_modelos, lista_oficinas


##############################################################################
# Callbacks para os inputs ###################################################
##############################################################################


# Função para validar o input
def input_valido(id_veiculo, datas, min_dias, modelo_escolhido, lista_oficinas, lista_secaos, lista_os):
    if id_veiculo is None or not id_veiculo:
        return False

    if datas is None or not datas or None in datas or min_dias is None:
        return False

    if modelo_escolhido is None or not modelo_escolhido:
        return False

    if lista_oficinas is None or not lista_oficinas or None in lista_oficinas:
        return False

    if lista_secaos is None or not lista_secaos or None in lista_secaos:
        return False

    if lista_os is None or not lista_os or None in lista_os:
        return False

    return True


# Corrige o input para garantir que "TODAS" não seja selecionado junto com outras opções
def corrige_input(lista):
    # Caso 1: Nenhuma opcao é selecionada, reseta para "TODAS"
    if not lista:
        return ["TODAS"]

    # Caso 2: Se "TODAS" foi selecionado após outras opções, reseta para "TODAS"
    if len(lista) > 1 and "TODAS" in lista[1:]:
        return ["TODAS"]

    # Caso 3: Se alguma opção foi selecionada após "TODAS", remove "TODAS"
    if "TODAS" in lista and len(lista) > 1:
        return [value for value in lista if value != "TODAS"]

    # Por fim, se não caiu em nenhum caso, retorna o valor original
    return lista


@callback(
    Output("input-select-oficina-veiculo", "value", allow_duplicate=True),
    Input("input-select-oficina-veiculo", "value"),
    prevent_initial_call=True,
)
def corrige_input_oficina(lista_oficinas):
    return corrige_input(lista_oficinas)


@callback(
    Output("input-select-secao-veiculo", "value", allow_duplicate=True),
    Input("input-select-secao-veiculo", "value"),
    prevent_initial_call=True,
)
def corrige_input_secao(lista_secaos):
    return corrige_input(lista_secaos)


@callback(
    [
        Output("input-select-veiculos-veiculo", "options", allow_duplicate=True),
        Output("input-select-veiculos-veiculo", "value", allow_duplicate=True),
    ],
    Input("input-select-modelos-veiculo", "value"),
    prevent_initial_call=True,
)
def corrige_input_veiculos_ao_mudar_modelo(modelo_escolhido):
    if modelo_escolhido is None or modelo_escolhido == "":
        # Retorna a opção padrão (TODOS OS VEICULOS)
        lista_padrao_veiculos = [
            {
                "label": veiculo["VEICULO"],
                "value": veiculo["VEICULO"],
            }
            for _, veiculo in df_veiculos.iterrows()
        ]
        veiculo_padrao = lista_padrao_veiculos[0]["value"]
        return lista_padrao_veiculos, veiculo_padrao

    # Obtém os veículos possíveis nos modelos selecionados
    lista_todos_veiculos = veiculos_service.get_veiculos_possiveis_nos_modelos([modelo_escolhido])

    # Transforma em lista
    lista_veiculos_possiveis = lista_todos_veiculos.to_dict(orient="records")

    # Formata para o Dropdown
    lista_veiculos_options = [
        {"label": veiculo["VEICULO"], "value": veiculo["VEICULO"]} for veiculo in lista_veiculos_possiveis
    ]

    valor_padrao = lista_veiculos_options[0]["value"]

    return lista_veiculos_options, valor_padrao


# SERVIÇOS DO VEÍCULO SELECIONADO
@callback(
    Output("input-select-ordens-servico-veiculos", "options", allow_duplicate=True),
    Input("input-select-veiculos-veiculo", "value"),
    prevent_initial_call=True,
)
def corrige_input_os_ao_mudar_veiculo(id_veiculo):
    if id_veiculo is None or not id_veiculo:
        return [{"label": "TODAS", "value": "TODAS"}]

    lista_os = veiculos_service.get_os_possiveis_do_veiculo(id_veiculo)

    # Formatar para o formato de opções do dropdown
    options_servicos = [{"label": servico, "value": servico} for servico in lista_os["SERVICO"]]

    # Adicionar opção "TODAS" no início
    options_servicos.insert(0, {"label": "TODAS", "value": "TODAS"})

    return options_servicos


def gera_labels_inputs_veiculos(campo):
    # Cria o callback
    @callback(
        [
            Output(component_id=f"{campo}-labels", component_property="children"),
        ],
        [
            Input("input-min-dias-veiculo", "value"),
            Input(component_id="input-select-oficina-veiculo", component_property="value"),
            Input(component_id="input-select-secao-veiculo", component_property="value"),
            Input(component_id="input-select-ordens-servico-veiculos", component_property="value"),
            Input(component_id="input-select-veiculos-veiculo", component_property="value"),
        ],
    )
    def atualiza_labels_inputs(min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
        lista_veiculos = [lista_veiculos]
        labels_antes = [
            # DashIconify(icon="material-symbols:filter-arrow-right", width=20),
            dmc.Badge("Filtro", color="gray", variant="outline"),
        ]
        min_dias_label = [dmc.Badge(f"{min_dias} dias", variant="outline")]
        lista_oficinas_labels = []
        lista_secaos_labels = []
        lista_os_labels = []
        lista_veiculos_labels = []

        if lista_oficinas is None or not lista_oficinas or "TODAS" in lista_oficinas:
            lista_oficinas_labels.append(dmc.Badge("Todas as oficinas", variant="outline"))
        else:
            for oficina in lista_oficinas:
                lista_oficinas_labels.append(dmc.Badge(oficina, variant="dot"))

        if lista_secaos is None or not lista_secaos or "TODAS" in lista_secaos:
            lista_secaos_labels.append(dmc.Badge("Todas as seções", variant="outline"))
        else:
            for secao in lista_secaos:
                lista_secaos_labels.append(dmc.Badge(secao, variant="dot"))

        if lista_os is None or not lista_os or "TODAS" in lista_os:
            lista_os_labels.append(dmc.Badge("Todas as ordens de serviço", variant="outline"))
        else:
            for os in lista_os:
                lista_os_labels.append(dmc.Badge(f"OS: {os}", variant="dot"))

        if lista_veiculos is None or not lista_veiculos or "TODAS" in lista_veiculos:
            lista_veiculos_labels.append(dmc.Badge("Todas os veículos", variant="outline"))
        else:
            for os in lista_veiculos:
                lista_veiculos_labels.append(dmc.Badge(f"VEICULO: {os}", variant="dot"))
        return [
            dmc.Group(
                labels_antes
                + min_dias_label
                + lista_oficinas_labels
                + lista_secaos_labels
                + lista_os_labels
                + lista_veiculos_labels
            )
        ]

    # Cria o componente
    return dmc.Group(id=f"{campo}-labels", children=[])


##############################################################################
# Callbacks para o estado ####################################################
##############################################################################


@callback(
    Output("store-input-dados-retrabalho-veiculo", "data"),
    [
        Input("input-select-veiculos-veiculo", "value"),
        Input("input-intervalo-datas-veiculo", "value"),
        Input("input-min-dias-veiculo", "value"),
        Input("input-select-modelos-veiculo", "value"),
        Input("input-select-oficina-veiculo", "value"),
        Input("input-select-secao-veiculo", "value"),
        Input("input-select-ordens-servico-veiculos", "value"),
    ],
)
def callback_sincroniza_input_veiculo_store(
    id_veiculo=1202,
    datas=None,
    min_dias=None,
    modelo_escolhido=None,
    lista_oficinas=None,
    lista_secaos=None,
    lista_os=None,
):
    # Input padrão
    input_dict = {
        "valido": False,
        "id_veiculo": id_veiculo,
        "datas": datas,
        "min_dias": min_dias,
        "modelo_escolhido": modelo_escolhido,
        "lista_oficinas": lista_oficinas,
        "lista_secaos": lista_secaos,
        "lista_os": lista_os,
    }

    # Validação dos inputs
    if input_valido(id_veiculo, datas, min_dias, modelo_escolhido, lista_oficinas, lista_secaos, lista_os):
        input_dict["valido"] = True
    else:
        input_dict["valido"] = False

    print("ESTADO --------------------------------")
    print(input_dict)
    print("ESTADO --------------------------------")

    return input_dict


##############################################################################
# Callbacks para os indicadores ##############################################
##############################################################################


@callback(
    Output("indicador-rank-retrabalho-veiculo", "children"),
    Input("store-input-dados-retrabalho-veiculo", "data"),
)
def cb_rank_retrabalho_veiculo_modelo(data):
    # Valida se os dados do estado estão OK, caso contrário retorna os dados padrão
    if not data or not data["valido"]:
        return ""

    # Obtem os dados do estado
    id_veiculo = data["id_veiculo"]
    datas = data["datas"]
    min_dias = data["min_dias"]
    modelo_escolhido = data["modelo_escolhido"]
    lista_oficinas = data["lista_oficinas"]
    lista_secaos = data["lista_secaos"]
    lista_os = data["lista_os"]

    # Obtém os dados
    df = veiculos_service.get_indicador_rank_retrabalho_modelo_veiculo(
        id_veiculo, datas, min_dias, [modelo_escolhido], lista_oficinas, lista_secaos, lista_os
    )

    if df.empty:
        return ""

    return df["rank_veiculo"].values[0]



@callback(
    Output("indicador-rank-correcao-de-primeira-veiculo", "children"),
    Input("store-input-dados-retrabalho-veiculo", "data"),
)
def cb_rank_correcao_primeira_veiculo_modelo(data):
    # Valida se os dados do estado estão OK, caso contrário retorna os dados padrão
    if not data or not data["valido"]:
        return ""

    # Obtem os dados do estado
    id_veiculo = data["id_veiculo"]
    datas = data["datas"]
    min_dias = data["min_dias"]
    modelo_escolhido = data["modelo_escolhido"]
    lista_oficinas = data["lista_oficinas"]
    lista_secaos = data["lista_secaos"]
    lista_os = data["lista_os"]

    # Obtém os dados
    df = veiculos_service.get_indicador_rank_correcao_primeira_modelo_veiculo(
        id_veiculo, datas, min_dias, [modelo_escolhido], lista_oficinas, lista_secaos, lista_os
    )

    if df.empty:
        return ""

    return df["rank_veiculo"].values[0]

##############################################################################
# Callbacks para os gráficos #################################################
##############################################################################


@callback(
    Output("graph-pizza-sintese-veiculo", "figure"),
    Input("store-input-dados-retrabalho-veiculo", "data"),
    Input("store-window-size", "data"),
)
def plota_grafico_pizza_sintese_veiculo(data, metadata_browser):
    # Valida se os dados do estado estão OK, caso contrário retorna os dados padrão
    if not data or not data["valido"]:
        return go.Figure()

    # Obtem os dados do estado
    id_veiculo = data["id_veiculo"]
    datas = data["datas"]
    min_dias = data["min_dias"]
    modelo_escolhido = data["modelo_escolhido"]
    lista_oficinas = data["lista_oficinas"]
    lista_secaos = data["lista_secaos"]
    lista_os = data["lista_os"]

    # Obtém os dados
    df = veiculos_service.get_sinteze_retrabalho_veiculo_para_grafico_pizza(
        id_veiculo, datas, min_dias, [modelo_escolhido], lista_oficinas, lista_secaos, lista_os
    )

    if df.empty:
        return go.Figure()

    # Gera o gráfico
    fig = veiculos_graficos.grafico_pizza_veiculo(df, metadata_browser)

    return fig


@callback(
    Output("graph-evolucao-os-mes-veiculo", "figure"),
    Input("store-input-dados-retrabalho-veiculo", "data"),
)
def plota_grafico_evolucao_quantidade_os_por_mes_v2(data):
    # Valida se os dados do estado estão OK, caso contrário retorna os dados padrão
    if not data or not data["valido"]:
        return go.Figure()

    # Obtem os dados do estado
    id_veiculo = data["id_veiculo"]
    datas = data["datas"]
    min_dias = data["min_dias"]
    modelo_escolhido = data["modelo_escolhido"]
    lista_oficinas = data["lista_oficinas"]
    lista_secaos = data["lista_secaos"]
    lista_os = data["lista_os"]

    # Obtém os dados
    df = veiculos_service.get_evolucao_quantidade_os_por_mes(
        id_veiculo, datas, min_dias, [modelo_escolhido], lista_oficinas, lista_secaos, lista_os
    )

    # Plota o gráfico
    fig = veiculos_graficos.grafico_evolucao_quantidade_os_por_mes(df)

    return fig


@callback(
    Output("graph-evolucao-retrabalho-mes-por-veiculo", "figure"),
    Input("store-input-dados-retrabalho-veiculo", "data"),
)
def plota_grafico_evolucao_retrabalho_por_veiculo_por_mes(data):
    # Valida se os dados do estado estão OK, caso contrário retorna os dados padrão
    if not data or not data["valido"]:
        return go.Figure()

    # Obtem os dados do estado
    id_veiculo = data["id_veiculo"]
    datas = data["datas"]
    min_dias = data["min_dias"]
    modelo_escolhido = data["modelo_escolhido"]
    lista_oficinas = data["lista_oficinas"]
    lista_secaos = data["lista_secaos"]
    lista_os = data["lista_os"]

    # Obtém os dados
    df = veiculos_service.get_evolucao_retrabalho_por_veiculo_por_mes(
        id_veiculo, datas, min_dias, [modelo_escolhido], lista_oficinas, lista_secaos, lista_os
    )

    # Plota o gráfico
    fig = veiculos_graficos.grafico_evolucao_retrabalho_por_veiculo_por_mes(df)

    return fig


@callback(
    Output("graph-evolucao-retrabalho-por-secao-por-mes-veiculos-v2", "figure"),
    Input("store-input-dados-retrabalho-veiculo", "data"),
)
def plota_grafico_evolucao_retrabalho_por_secao_por_mes(data):
    # Valida se os dados do estado estão OK, caso contrário retorna os dados padrão
    if not data or not data["valido"]:
        return go.Figure()

    # Obtem os dados do estado
    id_veiculo = data["id_veiculo"]
    datas = data["datas"]
    min_dias = data["min_dias"]
    modelo_escolhido = data["modelo_escolhido"]
    lista_oficinas = data["lista_oficinas"]
    lista_secaos = data["lista_secaos"]
    lista_os = data["lista_os"]

    # Obtém os dados
    df = veiculos_service.get_evolucao_retrabalho_por_secao_por_mes(
        id_veiculo, datas, min_dias, [modelo_escolhido], lista_oficinas, lista_secaos, lista_os
    )

    # Plota o gráfico
    fig = veiculos_graficos.grafico_evolucao_retrabalho_por_secao_por_mes(df)

    return fig


@callback(
    Output("graph-evolucao-custo-por-mes-veiculo", "figure"),
    Input("store-input-dados-retrabalho-veiculo", "data"),
)
def plota_grafico_evolucao_retrabalho_por_secao_por_mes(data):
    # Valida se os dados do estado estão OK, caso contrário retorna os dados padrão
    if not data or not data["valido"]:
        return go.Figure()

    # Obtem os dados do estado
    id_veiculo = data["id_veiculo"]
    datas = data["datas"]
    min_dias = data["min_dias"]
    modelo_escolhido = data["modelo_escolhido"]
    lista_oficinas = data["lista_oficinas"]
    lista_secaos = data["lista_secaos"]
    lista_os = data["lista_os"]

    # Obtém os dados
    df = veiculos_service.get_evolucao_custo_por_mes(
        id_veiculo, datas, min_dias, [modelo_escolhido], lista_oficinas, lista_secaos, lista_os
    )

    # Plota o gráfico
    fig = veiculos_graficos.grafico_evolucao_custo_por_mes(df)

    return fig

    # return fig


##############################################################################
# Layout #####################################################################
##############################################################################
layout = dbc.Container(
    [
        # Estado
        dcc.Store(id="store-input-dados-retrabalho-veiculo"),
        # Loading
        # dmc.LoadingOverlay(
        #     visible=True,
        #     id="loading-overlay-guia-por-veiculo",
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
                                        dbc.Col(DashIconify(icon="mdi:bus", width=45), width="auto"),
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
                                                    dbc.Label("Data (intervalo) de análise"),
                                                    dmc.DatePicker(
                                                        id="input-intervalo-datas-veiculo",
                                                        allowSingleDateInRange=True,
                                                        type="range",
                                                        minDate=date(2024, 8, 1),
                                                        maxDate=date.today(),
                                                        value=[date(2024, 8, 1), date.today()],
                                                    ),
                                                ],
                                                className="dash-bootstrap",
                                            ),
                                        ],
                                        body=True,
                                    ),
                                    md=6,
                                    className="mb-3 mb-md-0",
                                ),
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            html.Div(
                                                [
                                                    dbc.Label("Tempo (em dias) entre OS para retrabalho"),
                                                    dcc.Dropdown(
                                                        id="input-min-dias-veiculo",
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
                                dmc.Space(h=10),
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            html.Div(
                                                [
                                                    dbc.Label("Modelos"),
                                                    dcc.Dropdown(
                                                        id="input-select-modelos-veiculo",
                                                        options=[
                                                            {"label": os["MODELO"], "value": os["MODELO"]}
                                                            for os in lista_todos_modelos
                                                        ],
                                                        value="TODOS",
                                                        placeholder="Selecione o modelo do veículo",
                                                    ),
                                                ],
                                                className="dash-bootstrap",
                                            ),
                                        ],
                                        body=True,
                                    ),
                                    md=6,
                                    className="mb-3 mb-md-0",
                                ),
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            html.Div(
                                                [
                                                    dbc.Label("Veículos"),
                                                    dcc.Dropdown(
                                                        id="input-select-veiculos-veiculo",
                                                        multi=False,
                                                        options=[
                                                            {
                                                                "label": veiculo["VEICULO"],
                                                                "value": veiculo["VEICULO"],
                                                            }
                                                            for _, veiculo in df_veiculos.iterrows()
                                                        ],
                                                        value=df_veiculos.iloc[0]["VEICULO"],
                                                        placeholder="Selecione o veículo",
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
                                                    dbc.Label("Oficinas"),
                                                    dcc.Dropdown(
                                                        id="input-select-oficina-veiculo",
                                                        options=[
                                                            {"label": oficina["LABEL"], "value": oficina["LABEL"]}
                                                            for oficina in lista_todas_oficinas
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
                                    className="mb-3 mb-md-0",
                                ),
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            html.Div(
                                                [
                                                    dbc.Label("Seções (categorias) de manutenção"),
                                                    dcc.Dropdown(
                                                        id="input-select-secao-veiculo",
                                                        options=[
                                                            {"label": sec["LABEL"], "value": sec["LABEL"]}
                                                            for sec in lista_todas_secoes
                                                        ],
                                                        multi=True,
                                                        value=["TODAS"],
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
                                                        id="input-select-ordens-servico-veiculos",
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
                                    md=12,
                                    className="mb-3 mb-md-0",
                                ),
                            ]
                        ),
                    ],
                    md=8,
                    className="mb-3 mb-md-0",
                ),
                dbc.Col(
                    # Resumo
                    dbc.Row(
                        [
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
                            dmc.Space(h=30),
                            # Gráfico de pizza com a relação entre Retrabalho e Correção
                            dcc.Graph(id="graph-pizza-sintese-veiculo"),
                        ]
                    ),
                    md=4,
                ),
            ]
        ),
        dmc.Space(h=30),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="icon-park-outline:ranking-list", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4("Indicadores", className="align-self-center"),
                            dmc.Space(h=5),
                            gera_labels_inputs_veiculos("labels-indicadores-pag-veiculo"),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        dmc.Space(h=20),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                dmc.Group(
                                    [
                                        dmc.Title(id="indicador-rank-retrabalho-veiculo", order=2),
                                        DashIconify(
                                            icon="tabler:reorder",
                                            width=48,
                                            color="black",
                                        ),
                                    ],
                                    justify="center",
                                    mt="md",
                                    mb="xs",
                                ),
                            ),
                            dbc.CardFooter("Rank Retrabalho / Modelo (menor = melhor)"),
                        ],
                        class_name="card-box-shadow",
                    ),
                    md=3,
                    className="mb-3 mb-md-0",
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                dmc.Group(
                                    [
                                        dmc.Title(id="indicador-rank-correcao-de-primeira-veiculo", order=2),
                                        DashIconify(
                                            icon="gravity-ui:target-dart",
                                            width=48,
                                            color="black",
                                        ),
                                    ],
                                    justify="center",
                                    mt="md",
                                    mb="xs",
                                ),
                            ),
                            dbc.CardFooter("Rank Correção Primeira / Modelo (maior = melhor)"),
                        ],
                        class_name="card-box-shadow",
                    ),
                    md=3,
                    className="mb-3 mb-md-0",
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                dmc.Group(
                                    [
                                        dmc.Title(id="indicador-total-os-veiculo", order=2),
                                        DashIconify(
                                            icon="pajamas:task-done",
                                            width=48,
                                            color="black",
                                        ),
                                    ],
                                    justify="center",
                                    mt="md",
                                    mb="xs",
                                ),
                            ),
                            dbc.CardFooter("Total de OSs executadas"),
                        ],
                        className="card-box",
                    ),
                    md=3,
                    className="mb-3 mb-md-0",
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                dmc.Group(
                                    [
                                        dmc.Title(id="indicador-rank-os-veiculo", order=2),
                                        DashIconify(
                                            icon="solar:ranking-linear",
                                            width=48,
                                            color="black",
                                        ),
                                    ],
                                    justify="center",
                                    mt="md",
                                    mb="xs",
                                ),
                            ),
                            dbc.CardFooter("Rank de OSs / Modelo"),
                        ],
                        className="card-box",
                    ),
                    md=3,
                    className="mb-3 mb-md-0",
                ),
            ],
            justify="center",
        ),
        dmc.Space(h=20),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                dmc.Group(
                                    [
                                        dmc.Title(id="indicador-gasto-total-veiculo", order=2),
                                        DashIconify(
                                            icon="hugeicons:search-dollar",
                                            width=48,
                                            color="black",
                                        ),
                                    ],
                                    justify="center",
                                    mt="md",
                                    mb="xs",
                                ),
                            ),
                            dbc.CardFooter("Total gasto com peças"),
                        ],
                        class_name="card-box-shadow",
                    ),
                    md=3,
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                dmc.Group(
                                    [
                                        dmc.Title(id="indicador-rank-gasto-total-veiculo", order=2),
                                        DashIconify(
                                            icon="ion:analytics-sharp",
                                            width=48,
                                            color="black",
                                        ),
                                    ],
                                    justify="center",
                                    mt="md",
                                    mb="xs",
                                ),
                            ),
                            dbc.CardFooter("Rank Gasto Total Peças / Modelo"),
                        ],
                        class_name="card-box-shadow",
                    ),
                    md=3,
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                dmc.Group(
                                    [
                                        dmc.Title(id="indicador-gasto-retrabalho-total-veiculo", order=2),
                                        DashIconify(
                                            icon="emojione-monotone:money-with-wings",
                                            width=48,
                                            color="black",
                                        ),
                                    ],
                                    justify="center",
                                    mt="md",
                                    mb="xs",
                                ),
                            ),
                            dbc.CardFooter("Total gasto com peças em retrabalho"),
                        ],
                        class_name="card-box-shadow",
                    ),
                    md=3,
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                dmc.Group(
                                    [
                                        dmc.Title(id="indicador-rank-gasto-retrabalho-veiculo", order=2),
                                        DashIconify(
                                            icon="ion:analytics-sharp",
                                            width=48,
                                            color="black",
                                        ),
                                    ],
                                    justify="center",
                                    mt="md",
                                    mb="xs",
                                ),
                            ),
                            dbc.CardFooter("Rank Gasto Retrabalho / Modelo"),
                        ],
                        class_name="card-box-shadow",
                    ),
                    md=3,
                ),
            ],
            justify="center",
        ),
        # dbc.Row(
        #         [
        #             dbc.Col(
        #                 dbc.Card(
        #                     [
        #                         dbc.CardBody(
        #                             dmc.Group(
        #                                 [
        #                                     dmc.Title(id="indicador-porcentagem-retrabalho-veiculo", order=2),
        #                                     DashIconify(
        #                                         icon="mdi:bus-alert",
        #                                         width=48,
        #                                         color="black",
        #                                     ),
        #                                 ],
        #                                 justify="space-around",
        #                                 mt="md",
        #                                 mb="xs",
        #                             ),
        #                         ),
        #                         dbc.CardFooter("% retrabalho"),
        #                     ],
        #                     class_name="card-box-shadow",
        #                 ),
        #                 md=4,
        #             ),
        #             dbc.Col(
        #                 dbc.Card(
        #                     [
        #                         dbc.CardBody(
        #                             dmc.Group(
        #                                 [
        #                                     dmc.Title(
        #                                         id="indicador-porcentagem-correcao-primeira",
        #                                         order=2,
        #                                     ),
        #                                     DashIconify(
        #                                         icon="ic:round-gps-fixed",
        #                                         width=48,
        #                                         color="black",
        #                                     ),
        #                                 ],
        #                                 justify="space-around",
        #                                 mt="md",
        #                                 mb="xs",
        #                             ),
        #                         ),
        #                         dbc.CardFooter("% correção de primeira"),
        #                     ],
        #                     class_name="card-box-shadow",
        #                 ),
        #                 md=4,
        #             ),
        #             dbc.Col(
        #                 dbc.Card(
        #                     [
        #                         dbc.CardBody(
        #                             dmc.Group(
        #                                 [
        #                                     dmc.Title(id="indicador-relacao-os-problema", order=2),
        #                                     DashIconify(
        #                                         icon="icon-park-solid:division",
        #                                         width=48,
        #                                         color="black",
        #                                     ),
        #                                 ],
        #                                 justify="space-around",
        #                                 mt="md",
        #                                 mb="xs",
        #                             ),
        #                         ),
        #                         dbc.CardFooter("Relaçao OS/problema"),
        #                     ],
        #                     class_name="card-box-shadow",
        #                 ),
        #                 md=4,
        #             ),
        #         ]
        #     ),
        #     dbc.Row(dmc.Space(h=20)),
        #     dbc.Row(
        #         [
        #             dbc.Col(
        #                 dbc.Card(
        #                     [
        #                         dbc.CardBody(
        #                             dmc.Group(
        #                                 [
        #                                     dmc.Title(
        #                                         id="indicador-posicao-relaçao-retrabalho",
        #                                         order=2,
        #                                     ),
        #                                     DashIconify(
        #                                         icon="ic:round-sort",
        #                                         width=48,
        #                                         color="black",
        #                                     ),
        #                                 ],
        #                                 justify="space-around",
        #                                 mt="md",
        #                                 mb="xs",
        #                             ),
        #                         ),
        #                         dbc.CardFooter("Ranking do veículo % retrabalho/geral"),
        #                     ],
        #                     class_name="card-box-shadow",
        #                 ),
        #                 md=4,
        #             ),
        #             dbc.Col(
        #                 dbc.Card(
        #                     [
        #                         dbc.CardBody(
        #                             dmc.Group(
        #                                 [
        #                                     dmc.Title(
        #                                         id="indicador-posição-veiculo-correção-primeira",
        #                                         order=2,
        #                                     ),
        #                                     DashIconify(
        #                                         icon="ic:round-sort",
        #                                         width=48,
        #                                         color="black",
        #                                     ),
        #                                 ],
        #                                 justify="space-around",
        #                                 mt="md",
        #                                 mb="xs",
        #                             ),
        #                         ),
        #                         dbc.CardFooter("Ranking do veiculo % correção de primeira/geral"),
        #                     ],
        #                     class_name="card-box-shadow",
        #                 ),
        #                 md=4,
        #             ),
        #             dbc.Col(
        #                 dbc.Card(
        #                     [
        #                         dbc.CardBody(
        #                             dmc.Group(
        #                                 [
        #                                     dmc.Title(id="indicador-posição-veiculo-relaçao-osproblema", order=2),
        #                                     DashIconify(
        #                                         icon="ic:round-sort",
        #                                         width=48,
        #                                         color="black",
        #                                     ),
        #                                 ],
        #                                 justify="space-around",
        #                                 mt="md",
        #                                 mb="xs",
        #                             ),
        #                         ),
        #                         dbc.CardFooter("Posição veiculo relaçao OS/Problema"),
        #                     ],
        #                     class_name="card-box-shadow",
        #                 ),
        #                 md=4,
        #             ),
        #         ]
        #     ),
        #     dbc.Row(dmc.Space(h=20)),
        #     dbc.Row(
        #         [
        #             dbc.Col(
        #                 dbc.Card(
        #                     [
        #                         dbc.CardBody(
        #                             dmc.Group(
        #                                 [
        #                                     dmc.Title(
        #                                         id="indicador-posicao-relaçao-retrabalho-modelo",
        #                                         order=2,
        #                                     ),
        #                                     DashIconify(
        #                                         icon="ic:round-sort",
        #                                         width=48,
        #                                         color="black",
        #                                     ),
        #                                 ],
        #                                 justify="space-around",
        #                                 mt="md",
        #                                 mb="xs",
        #                             ),
        #                         ),
        #                         dbc.CardFooter("Ranking do veículo % retrabalho/modelo"),
        #                     ],
        #                     class_name="card-box-shadow",
        #                 ),
        #                 md=4,
        #             ),
        #             dbc.Col(
        #                 dbc.Card(
        #                     [
        #                         dbc.CardBody(
        #                             dmc.Group(
        #                                 [
        #                                     dmc.Title(
        #                                         id="indicador-posição-veiculo-correção-primeira-modelo",
        #                                         order=2,
        #                                     ),
        #                                     DashIconify(
        #                                         icon="ic:round-sort",
        #                                         width=48,
        #                                         color="black",
        #                                     ),
        #                                 ],
        #                                 justify="space-around",
        #                                 mt="md",
        #                                 mb="xs",
        #                             ),
        #                         ),
        #                         dbc.CardFooter("Ranking do veiculo % correção de primeira/modelo"),
        #                     ],
        #                     class_name="card-box-shadow",
        #                 ),
        #                 md=4,
        #             ),
        #             dbc.Col(
        #                 dbc.Card(
        #                     [
        #                         dbc.CardBody(
        #                             dmc.Group(
        #                                 [
        #                                     dmc.Title(
        #                                         id="indicador-posição-veiculo-relaçao-osproblema-modelo", order=2
        #                                     ),
        #                                     DashIconify(
        #                                         icon="ic:round-sort",
        #                                         width=48,
        #                                         color="black",
        #                                     ),
        #                                 ],
        #                                 justify="space-around",
        #                                 mt="md",
        #                                 mb="xs",
        #                             ),
        #                         ),
        #                         dbc.CardFooter("Posição veiculo OS/Problema modelo"),
        #                     ],
        #                     class_name="card-box-shadow",
        #                 ),
        #                 md=4,
        #             ),
        #         ]
        #     ),
        #     dbc.Row(dmc.Space(h=20)),
        #     dbc.Row(
        #         [
        #             dbc.Col(
        #                 dbc.Card(
        #                     [
        #                         dbc.CardBody(
        #                             dmc.Group(
        #                                 [
        #                                     dmc.Title(
        #                                         id="indicador-pecas-totais",
        #                                         order=2,
        #                                     ),
        #                                     DashIconify(
        #                                         icon="mdi:cog",
        #                                         width=48,
        #                                         color="black",
        #                                     ),
        #                                 ],
        #                                 justify="space-around",
        #                                 mt="md",
        #                                 mb="xs",
        #                             ),
        #                         ),
        #                         dbc.CardFooter("Valor total de peças"),
        #                     ],
        #                     class_name="card-box-shadow",
        #                 ),
        #                 md=4,
        #             ),
        #             dbc.Col(
        #                 dbc.Card(
        #                     [
        #                         dbc.CardBody(
        #                             dmc.Group(
        #                                 [
        #                                     dmc.Title(
        #                                         id="indicador-pecas-mes",
        #                                         order=2,
        #                                     ),
        #                                     DashIconify(
        #                                         icon="mdi:wrench",
        #                                         width=48,
        #                                         color="black",
        #                                     ),
        #                                 ],
        #                                 justify="space-around",
        #                                 mt="md",
        #                                 mb="xs",
        #                             ),
        #                         ),
        #                         dbc.CardFooter("Valor total de peças/mês"),
        #                     ],
        #                     class_name="card-box-shadow",
        #                 ),
        #                 md=4,
        #             ),
        #             dbc.Col(
        #                 dbc.Card(
        #                     [
        #                         dbc.CardBody(
        #                             dmc.Group(
        #                                 [
        #                                     dmc.Title(id="indicador-ranking-pecas", order=2),
        #                                     DashIconify(
        #                                         icon="mdi:podium",
        #                                         width=48,
        #                                         color="black",
        #                                     ),
        #                                 ],
        #                                 justify="space-around",
        #                                 mt="md",
        #                                 mb="xs",
        #                             ),
        #                         ),
        #                         dbc.CardFooter("Ranking do valor das peças dentro do período"),
        #                     ],
        #                     class_name="card-box-shadow",
        #                 ),
        #                 md=4,
        #             ),
        #         ]
        #     ),
        #     dbc.Row(dmc.Space(h=20)),
        #     dbc.Row(
        #         [
        #             dbc.Col(
        #                 dbc.Card(
        #                     [
        #                         dbc.CardBody(
        #                             dmc.Group(
        #                                 [
        #                                     dmc.Title(
        #                                         id="indicador-oss-diferentes",
        #                                         order=2,
        #                                     ),
        #                                     DashIconify(
        #                                         icon="game-icons:time-bomb",
        #                                         width=48,
        #                                         color="black",
        #                                     ),
        #                                 ],
        #                                 justify="space-around",
        #                                 mt="md",
        #                                 mb="xs",
        #                             ),
        #                         ),
        #                         dbc.CardFooter("Números de OSs"),
        #                     ],
        #                     class_name="card-box-shadow",
        #                 ),
        #                 md=4,
        #             ),
        #             dbc.Col(
        #                 dbc.Card(
        #                     [
        #                         dbc.CardBody(
        #                             dmc.Group(
        #                                 [
        #                                     dmc.Title(
        #                                         id="indicador-problemas-diferentes",
        #                                         order=2,
        #                                     ),
        #                                     DashIconify(
        #                                         icon="mdi:tools",
        #                                         width=48,
        #                                         color="black",
        #                                     ),
        #                                 ],
        #                                 justify="space-around",
        #                                 mt="md",
        #                                 mb="xs",
        #                             ),
        #                         ),
        #                         dbc.CardFooter("Serviços diferentes"),
        #                     ],
        #                     class_name="card-box-shadow",
        #                 ),
        #                 md=4,
        #             ),
        #             dbc.Col(
        #                 dbc.Card(
        #                     [
        #                         dbc.CardBody(
        #                             dmc.Group(
        #                                 [
        #                                     dmc.Title(id="indicador-mecanicos-diferentes", order=2),
        #                                     DashIconify(
        #                                         icon="mdi:account-wrench",
        #                                         width=48,
        #                                         color="black",
        #                                     ),
        #                                 ],
        #                                 justify="space-around",
        #                                 mt="md",
        #                                 mb="xs",
        #                             ),
        #                         ),
        #                         dbc.CardFooter("Mecânicos diferentes"),
        #                     ],
        #                     class_name="card-box-shadow",
        #                 ),
        #                 md=4,
        #             ),
        #         ]
        #     ),
        #     dbc.Row(dmc.Space(h=20)),
        #     dbc.Row(
        #         [
        #             dbc.Col(
        #                 dbc.Card(
        #                     [
        #                         dbc.CardBody(
        #                             dmc.Group(
        #                                 [
        #                                     dmc.Title(
        #                                         id="indicador-valor-geral-retrabalho",
        #                                         order=2,
        #                                     ),
        #                                     DashIconify(
        #                                         icon="mdi:reload",
        #                                         width=48,
        #                                         color="black",
        #                                     ),
        #                                 ],
        #                                 justify="space-around",
        #                                 mt="md",
        #                                 mb="xs",
        #                             ),
        #                         ),
        #                         dbc.CardFooter("Valor de retrabalho"),
        #                     ],
        #                     class_name="card-box-shadow",
        #                 ),
        #                 md=4,
        #             ),
        #             dbc.Col(
        #                 dbc.Card(
        #                     [
        #                         dbc.CardBody(
        #                             dmc.Group(
        #                                 [
        #                                     dmc.Title(
        #                                         id="indicador-qtd-pecas",
        #                                         order=2,
        #                                     ),
        #                                     DashIconify(
        #                                         icon="mdi:reload-alert",
        #                                         width=48,
        #                                         color="black",
        #                                     ),
        #                                 ],
        #                                 justify="space-around",
        #                                 mt="md",
        #                                 mb="xs",
        #                             ),
        #                         ),
        #                         dbc.CardFooter("Quantidade de peças trocadas"),
        #                     ],
        #                     class_name="card-box-shadow",
        #                 ),
        #                 md=4,
        #             ),
        #             dbc.Col(
        #                 dbc.Card(
        #                     [
        #                         dbc.CardBody(
        #                             dmc.Group(
        #                                 [
        #                                     dmc.Title(id="indicador-ranking-valor-pecas-modelo", order=2),
        #                                     DashIconify(
        #                                         icon="mdi:podium",
        #                                         width=48,
        #                                         color="black",
        #                                     ),
        #                                 ],
        #                                 justify="space-around",
        #                                 mt="md",
        #                                 mb="xs",
        #                             ),
        #                         ),
        #                         dbc.CardFooter("Ranking valor de peça por modelo"),
        #                     ],
        #                     class_name="card-box-shadow",
        #                 ),
        #                 md=4,
        #             ),
        #         ]
        #     ),
        # ),
        dbc.Row(dmc.Space(h=40)),
        # dmc.Space(h=40),
        dmc.Space(h=40),
        ##Gráfico de Quantidade de OS / mes
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="fluent:arrow-trending-text-20-filled", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Evolução do número de OS por mês",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            gera_labels_inputs_veiculos("evolucao-os-mes-veiculo"),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        dcc.Graph(id="graph-evolucao-os-mes-veiculo"),
        dmc.Space(h=40),
        # Graficos de Evolução do Retrabalho por Garagem e Seção
        dmc.Space(h=30),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="fluent:arrow-trending-wrench-20-filled", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Evolução do retrabalho por veículo",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            gera_labels_inputs_veiculos("evolucao-retrabalho-por-garagem-por-mes-veiculos"),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        dcc.Graph(id="graph-evolucao-retrabalho-mes-por-veiculo"),
        dmc.Space(h=40),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="fluent:arrow-trending-text-20-filled", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Evolução do retrabalho por seção",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            gera_labels_inputs_veiculos("evolucao-retrabalho-por-secao-por-mes-veiculos"),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        dcc.Graph(id="graph-evolucao-retrabalho-por-secao-por-mes-veiculos-v2"),
        dmc.Space(h=40),
        # Grafico geral de peças
        dmc.Space(h=30),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="fluent:arrow-trending-wrench-20-filled", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Evolução do custo de peças trocadas por mês",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            gera_labels_inputs_veiculos("evolucao-custo-por-mes-veiculos"),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        dcc.Graph(id="graph-evolucao-custo-por-mes-veiculo"),
        dmc.Space(h=40),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="mdi:cog-outline", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Tabela de peças por OS",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            dbc.Col(gera_labels_inputs_veiculos("pecas-substituidas-por-os-filtro"), width=True),
                            dbc.Col(
                                html.Div(
                                    [
                                        html.Button(
                                            "Exportar para Excel",
                                            id="btn-exportar-pecas",
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
                                        dcc.Download(id="download-excel-tabela-pecas"),
                                    ],
                                    style={"text-align": "right"},
                                ),
                                width="auto",
                            ),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        dmc.Space(h=20),
        dag.AgGrid(
            enableEnterpriseModules=True,
            id="tabela-pecas-substituidas",
            columnDefs=[
                {"field": "OS", "minWidth": 100},
                {"field": "EQUIPAMENTO", "minWidth": 100},
                {"field": "DESCRICAO DO SERVICO", "headerName": "DESCRIÇÃO DO SERVICO", "minWidth": 100},
                {"field": "MODELO", "minWidth": 300},
                {"field": "PRODUTO", "minWidth": 350},
                {"field": "QUANTIDADE", "minWidth": 100},
                {
                    "field": "VALOR",
                    "minWidth": 100,
                    "type": ["numericColumn"],
                    "valueFormatter": {"function": "'R$' + Number(params.value).toFixed(2).toLocaleString()"},
                    "sort": "desc",
                },
                {"field": "DATA", "minWidth": 130},
                {"field": "retrabalho", "headerName": "RETRABALHO", "minWidth": 130},
            ],
            rowData=[],
            defaultColDef={"filter": True, "floatingFilter": True},
            columnSize="autoSize",
            style={"height": 400, "resize": "vertical", "overflow": "hidden"},
        ),
        dmc.Space(h=40),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="mdi:tools", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Tabela de peças por descrição de seviço",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            dbc.Col(gera_labels_inputs_veiculos("tabela-de-pecas-por-descricao-filtros"), width=True),
                            dbc.Col(
                                html.Div(
                                    [
                                        html.Button(
                                            "Exportar para Excel",
                                            id="btn-exportar-descricao-retrabalho",
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
                                        dcc.Download(id="download-excel-tabela-retrabalho-por-descrição-servico"),
                                    ],
                                    style={"text-align": "right"},
                                ),
                                width="auto",
                            ),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        dmc.Space(h=20),
        dag.AgGrid(
            enableEnterpriseModules=True,
            id="tabela-descricao-de-servico",
            columnDefs=tbl_top_os_geral_retrabalho,
            rowData=[],
            defaultColDef={"filter": True, "floatingFilter": True},
            columnSize="autoSize",
            dashGridOptions={
                "localeText": locale_utils.AG_GRID_LOCALE_BR,
            },
            style={"height": 400, "resize": "vertical", "overflow": "hidden"},
        ),
        dmc.Space(h=40),
        dmc.Space(h=60),
        # Indicadores
    ]
)


##############################################################################
# CALLBACKS ##################################################################
##############################################################################


# GRÁFICO DE PIZZA GERAL
# @callback(
#     [
#         Output("graph-pizza-sintese-retrabalho-geral_veiculo", "figure"),
#         Output("indicador-porcentagem-retrabalho-veiculo", "children"),
#         Output("indicador-porcentagem-correcao-primeira", "children"),
#     ],
#     [
#         Input("input-intervalo-datas-veiculo", "value"),
#         Input("input-min-dias-veiculo", "value"),
#         Input("input-select-oficina-veiculo", "value"),
#         Input("input-select-secao-veiculo", "value"),
#         Input("input-select-ordens-servico-veiculos", "value"),
#         Input("input-select-veiculos-veiculo", "value"),
#     ],
# )
# def plota_grafico_pizza_sintese_geral(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
#     lista_veiculos = [lista_veiculos]
#     # Valida input
#     if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
#         return go.Figure(), "", ""
#     total_retrabalho, total_correcao_primeira, labels, values = veiculos_service.sintese_geral_fun(
#         datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos
#     )
#     fig = grafico_pizza_sintese_geral(labels, values)
#     return fig, total_retrabalho, total_correcao_primeira


# GRÁFICO DE RETRABALHOS POR VEÍCULOS
@callback(
    Output("graph-evolucao-retrabalho-por-garagem-por-mes-veiculos", "figure"),
    [
        Input("input-intervalo-datas-veiculo", "value"),
        Input("input-min-dias-veiculo", "value"),
        Input("input-select-oficina-veiculo", "value"),
        Input("input-select-secao-veiculo", "value"),
        Input("input-select-ordens-servico-veiculos", "value"),
        Input("input-select-veiculos-veiculo", "value"),
    ],
)
def plota_grafico_evolucao_retrabalho_por_veiculo_por_mes(
    datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos
):
    # Valida input
    lista_veiculos = [lista_veiculos]
    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
        return go.Figure()
    df = veiculos_service.evolucao_retrabalho_por_veiculo_por_mes_fun(
        datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos
    )
    fig = gerar_grafico_evolucao_retrabalho_por_veiculo_por_mes(df)
    return fig


# GRÁFICO DO RETRABALHO POR SECAO POR UM ÚNICO VEICULO
@callback(
    Output("graph-evolucao-retrabalho-por-secao-por-mes-veiculos", "figure"),
    [
        Input("input-intervalo-datas-veiculo", "value"),
        Input("input-min-dias-veiculo", "value"),
        Input("input-select-oficina-veiculo", "value"),
        Input("input-select-secao-veiculo", "value"),
        Input("input-select-ordens-servico-veiculos", "value"),
        Input("input-select-veiculos-veiculo", "value"),
    ],
)
def plota_grafico_evolucao_retrabalho_por_secao_por_mes(
    datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos
):
    lista_veiculos = [lista_veiculos]
    # Valida input
    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
        return go.Figure()
    df = veiculos_service.retrabalho_por_secao_por_mes_fun(
        datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos
    )
    fig = grafico_evolucao_retrabalho_por_secao_por_mes(df)
    # Exibe o gráfico
    return fig


# # GRAFICO DA QUANTIDADE DE OSs, INDICADORES DE : PROBLEMAS DIFERENTES, MECANICOS DIFERENTES, OS DIFERENTES, OS/PROBL, RANKING OS/PROBL
# @callback(
#     [
#         Output("graph-evolucao-os-mes-veiculo-v2", "figure"),
#         Output("indicador-problemas-diferentes", "children"),
#         Output("indicador-mecanicos-diferentes", "children"),
#         Output("indicador-oss-diferentes", "children"),
#         Output("indicador-relacao-os-problema", "children"),
#         Output("indicador-posição-veiculo-relaçao-osproblema", "children"),
#         Output("indicador-posição-veiculo-relaçao-osproblema-modelo", "children"),
#     ],
#     [
#         Input("input-intervalo-datas-veiculo", "value"),
#         Input("input-min-dias-veiculo", "value"),
#         Input("input-select-oficina-veiculo", "value"),
#         Input("input-select-secao-veiculo", "value"),
#         Input("input-select-ordens-servico-veiculos", "value"),
#         Input("input-select-veiculos-veiculo", "value"),
#     ],
# )
# def plota_grafico_evolucao_quantidade_os_por_mes(
#     datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos
# ):
#     lista_veiculos = [lista_veiculos]
#     # Valida input
#     if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
#         return go.Figure(), "", "", "", "", "", ""
#     (
#         os_diferentes,
#         mecanicos_diferentes,
#         os_veiculo_filtradas,
#         os_problema,
#         df_soma_mes,
#         df_os_unicas,
#         rk_os_problema_geral,
#         rk_os_problema_modelos,
#     ) = veiculos_service.evolucao_quantidade_os_por_mes_fun(
#         datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos
#     )
#     fig = grafico_qtd_os_e_soma_de_os_mes(df_soma_mes, df_os_unicas)
#     return (
#         fig,
#         os_diferentes,
#         mecanicos_diferentes,
#         os_veiculo_filtradas,
#         os_problema,
#         rk_os_problema_geral,
#         rk_os_problema_modelos,
#     )


# # GRAFICO DA TABELA DE PEÇAS
# @callback(
#     Output("graph-pecas-trocadas-por-mes", "figure"),
#     [
#         Input("input-intervalo-datas-veiculo", "value"),
#         Input("input-min-dias-veiculo", "value"),
#         Input("input-select-oficina-veiculo", "value"),
#         Input("input-select-secao-veiculo", "value"),
#         Input("input-select-ordens-servico-veiculos", "value"),
#         Input("input-select-veiculos-veiculo", "value"),
#     ],
# )
# def plota_grafico_pecas_trocadas_por_mes(datas, min_dias, lista_oficinas, lista_secaos, lista_os, equipamentos):
#     equipamentos = [equipamentos]
#     # Valida input
#     if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os, equipamentos):
#         return go.Figure()

#     data_inicio_str = datas[0]
#     data_fim_str = datas[1]

#     if data_inicio_str is None:
#         return go.Figure()  # Ou algum valor padrão válido
#     if data_fim_str is None:
#         return go.Figure()  # Ou algum valor padrão válido

#     # Garante que equipamentos seja uma lista
#     if isinstance(equipamentos, str):
#         equipamentos = [equipamentos]
#     df_veiculos, df_media_geral, df_media_modelo = veiculos_service.pecas_trocadas_por_mes_fun(
#         datas, min_dias, lista_oficinas, lista_secaos, lista_os, equipamentos
#     )
#     fig = grafico_tabela_pecas(df_veiculos, df_media_geral, df_media_modelo)
#     return fig


# # TABELA DE PEÇAS, INDICADORES DE: VALORES DE PECAS, VALOR DE PECAS/MES, RANKING DO VALOR DE PECAS, TOTAL DE PEÇAS
# @callback(
#     [
#         Output("tabela-pecas-substituidas", "rowData"),
#         Output("indicador-pecas-totais", "children"),
#         Output("indicador-pecas-mes", "children"),
#         Output("indicador-ranking-pecas", "children"),
#         Output("indicador-qtd-pecas", "children"),
#     ],
#     # Input("graph-pecas-trocadas-por-mes", "clickData"),
#     [
#         Input("input-intervalo-datas-veiculo", "value"),
#         Input("input-min-dias-veiculo", "value"),
#         Input("input-select-oficina-veiculo", "value"),
#         Input("input-select-secao-veiculo", "value"),
#         Input("input-select-ordens-servico-veiculos", "value"),
#         Input("input-select-veiculos-veiculo", "value"),
#     ],
# )
# def atualiza_tabela_pecas(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
#     lista_veiculos = [lista_veiculos]
#     # Valida input
#     if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
#         return [], " ", " ", " ", " "
#     df_detalhes_dict, valor_total_veiculos_str, valor_mes_str, rk, numero_pecas_veiculos_total = (
#         veiculos_service.tabela_pecas_fun(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos)
#     )
#     return df_detalhes_dict, valor_total_veiculos_str, valor_mes_str, rk, numero_pecas_veiculos_total


# DOWLOAD DA TABELA PEÇAS
@callback(
    Output("download-excel-tabela-pecas", "data"),
    [
        Input("btn-exportar-pecas", "n_clicks"),
        Input("input-intervalo-datas-veiculo", "value"),
        Input("input-min-dias-veiculo", "value"),
        Input("input-select-oficina-veiculo", "value"),
        Input("input-select-secao-veiculo", "value"),
        Input("input-select-ordens-servico-veiculos", "value"),
        Input("input-select-veiculos-veiculo", "value"),
    ],
    prevent_initial_call=True,
)
def dowload_excel_tabela_peças(n_clicks, datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
    lista_veiculos = [lista_veiculos]
    ctx = callback_context  # Obtém o contexto do callback
    if not ctx.triggered:
        return dash.no_update  # Evita execução desnecessária

    # Verifica se o callback foi acionado pelo botão de download
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if triggered_id != "btn-exportar-pecas":
        return dash.no_update  # Ignora mudanças nos outros inputs

    if not n_clicks or n_clicks <= 0:
        return dash.no_update

    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
        return dash.no_update

    date_now = datetime.now().strftime("%d-%m-%Y")
    timestamp = int(time.time())
    df_detalhes_dict, _, _, _, _ = veiculos_service.tabela_pecas_fun(
        datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos
    )
    df = pd.DataFrame(df_detalhes_dict)

    # Converter a coluna "retrabalho" (supondo que seja essa a coluna correta)
    if "retrabalho" in df.columns:
        df["retrabalho"] = df["retrabalho"].map({True: "SIM", False: "NÃO"})

    excel_data = gerar_excel(df=df)
    return dcc.send_bytes(excel_data, f"tabela-peças-os-{date_now}-{timestamp}.xlsx")


# TABELA DE DESCRIÇÃO DE SERVIÇOS E INDICADO DE VALOR DE RETRABALHO
# @callback(
#     [
#         Output("tabela-descricao-de-servico", "rowData"),
#         Output("indicador-valor-geral-retrabalho", "children"),
#     ],
#     [
#         Input("input-intervalo-datas-veiculo", "value"),
#         Input("input-min-dias-veiculo", "value"),
#         Input("input-select-oficina-veiculo", "value"),
#         Input("input-select-secao-veiculo", "value"),
#         Input("input-select-ordens-servico-veiculos", "value"),
#         Input("input-select-veiculos-veiculo", "value"),
#     ],
# )
# def atualiza_tabela_retrabalho_por_descrição_serviço(
#     datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculo
# ):
#     lista_veiculo = [lista_veiculo]
#     # Valida input
#     if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculo):
#         return [], " "

#     df_dict, valor_retrabalho = veiculos_service.tabela_top_os_geral_retrabalho_fun(
#         datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculo
#     )
#     return df_dict, valor_retrabalho


# DOWLOAD DA TABELA RETRABALHO POR DESCRIÇÃO DE SERVIÇO
@callback(
    Output("download-excel-tabela-retrabalho-por-descrição-servico", "data"),
    [
        Input("btn-exportar-descricao-retrabalho", "n_clicks"),
        Input("input-intervalo-datas-veiculo", "value"),
        Input("input-min-dias-veiculo", "value"),
        Input("input-select-oficina-veiculo", "value"),
        Input("input-select-secao-veiculo", "value"),
        Input("input-select-ordens-servico-veiculos", "value"),
        Input("input-select-veiculos-veiculo", "value"),
    ],
    prevent_initial_call=True,
)
def dowload_excel_tabela_retrabalho_por_descrição_servico(
    n_clicks, datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos
):
    lista_veiculos = [lista_veiculos]
    ctx = callback_context  # Obtém o contexto do callback
    if not ctx.triggered:
        return dash.no_update  # Evita execução desnecessária

    # Verifica se o callback foi acionado pelo botão de download
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if triggered_id != "btn-exportar-descricao-retrabalho":
        return dash.no_update  # Ignora mudanças nos outros inputs

    if not n_clicks or n_clicks <= 0:
        return dash.no_update

    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
        return dash.no_update

    date_now = datetime.now().strftime("%d-%m-%Y")
    timestamp = int(time.time())
    df_dict, _ = veiculos_service.tabela_top_os_geral_retrabalho_fun(
        datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos
    )
    df = pd.DataFrame(df_dict)
    excel_data = gerar_excel(df=df)
    return dcc.send_bytes(excel_data, f"tabela-retrabalho-por-descrição-serviço-{date_now}-{timestamp}.xlsx")


# INDICADOR RANKING DE VALOR DE PEÇAS POR MODELO
@callback(
    [Output("indicador-ranking-valor-pecas-modelo", "children")],
    [
        Input("input-intervalo-datas-veiculo", "value"),
        Input("input-min-dias-veiculo", "value"),
        Input("input-select-oficina-veiculo", "value"),
        Input("input-select-secao-veiculo", "value"),
        Input("input-select-ordens-servico-veiculos", "value"),
        Input("input-select-veiculos-veiculo", "value"),
    ],
)
def atualiza_ranking_pecas(datas, min_dias, lista_oficinas, lista_secoes, lista_os, lista_veiculos):
    lista_veiculos = [lista_veiculos]

    if not input_valido3(datas, min_dias, lista_veiculos):
        return [""]

    indicador_ranking_pecas_modelos = veiculos_service.tabela_ranking_pecas_fun(
        datas, min_dias, lista_oficinas, lista_secoes, lista_os, lista_veiculos
    )

    return [indicador_ranking_pecas_modelos]


# RANKING DOS RETRABALHOS DOS VEÍCULOS. INDICADORES DE: POSIÇÃO DE RELAÇÃO RETRABALHO, CORREÇÃO DE PRIMEIRA
@callback(
    [
        Output("indicador-posicao-relaçao-retrabalho", "children"),
        Output("indicador-posição-veiculo-correção-primeira", "children"),
        Output("indicador-posicao-relaçao-retrabalho-modelo", "children"),
        Output("indicador-posição-veiculo-correção-primeira-modelo", "children"),
    ],
    [
        Input("input-intervalo-datas-veiculo", "value"),
        Input("input-min-dias-veiculo", "value"),
        Input("input-select-oficina-veiculo", "value"),
        Input("input-select-secao-veiculo", "value"),
        Input("input-select-ordens-servico-veiculos", "value"),
        Input("input-select-veiculos-veiculo", "value"),
    ],
    # running=[(Output("loading-overlay-guia-por-veiculo", "visible"), True, False)],
)
def ranking_retrabalho_veiculos(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
    lista_veiculos = [lista_veiculos]
    # Valida input
    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
        return "", "", "", ""
    rk_retrabalho_geral, rk_correcao_primeira_geral, rk_retrabalho_modelo, rk_correcao_primeira_modelo = (
        veiculos_service.ranking_retrabalho_veiculos_fun(
            datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos
        )
    )
    return rk_retrabalho_geral, rk_correcao_primeira_geral, rk_retrabalho_modelo, rk_correcao_primeira_modelo


##############################################################################
# Registro da página #########################################################
##############################################################################
dash.register_page(__name__, name="Veículo", path="/retrabalho-por-veiculo", icon="mdi:bus")
