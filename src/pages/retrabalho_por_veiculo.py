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

# Banco de Dados
from db import PostgresSingleton

# Import de arquivos
import modules.veiculos.graficos as veiculos_graficos
import modules.veiculos.tabelas as veiculos_tabelas

# Improts gerais
from modules.entities_utils import get_modelos, get_lista_os, get_veiculos, get_oficinas, get_secoes, gerar_excel
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


def formata_float_para_real(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


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


@callback(
    Output("indicador-total-os-veiculo", "children"),
    Input("store-input-dados-retrabalho-veiculo", "data"),
)
def cb_total_os_veiculo_modelo(data):
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
    df = veiculos_service.get_indicador_total_os_modelo_veiculo(
        id_veiculo, datas, min_dias, [modelo_escolhido], lista_oficinas, lista_secaos, lista_os
    )

    if df.empty:
        return ""

    return df["quantidade_de_os"].values[0]


@callback(
    Output("indicador-rank-os-veiculo", "children"),
    Input("store-input-dados-retrabalho-veiculo", "data"),
)
def cb_rank_total_os_veiculo_modelo(data):
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
    df = veiculos_service.get_indicador_rank_total_os_modelo_veiculo(
        id_veiculo, datas, min_dias, [modelo_escolhido], lista_oficinas, lista_secaos, lista_os
    )

    if df.empty:
        return ""

    return df["rank_veiculo"].values[0]


@callback(
    Output("indicador-gasto-total-veiculo", "children"),
    Input("store-input-dados-retrabalho-veiculo", "data"),
)
def cb_total_gasto_pecas_veiculo_modelo(data):
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
    df = veiculos_service.get_indicador_total_gasto_pecas_modelo_veiculo(
        id_veiculo, datas, min_dias, [modelo_escolhido], lista_oficinas, lista_secaos, lista_os
    )

    if df.empty:
        return ""

    total_gasto = df["TOTAL_GASTO"].values[0]
    total_gasto_fmt = formata_float_para_real(total_gasto)

    return total_gasto_fmt


@callback(
    Output("indicador-rank-gasto-total-veiculo", "children"),
    Input("store-input-dados-retrabalho-veiculo", "data"),
)
def cb_rank_gasto_total_pecas_veiculo_modelo(data):
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
    df = veiculos_service.get_indicador_rank_gasto_total_pecas_modelo_veiculo(
        id_veiculo, datas, min_dias, [modelo_escolhido], lista_oficinas, lista_secaos, lista_os
    )

    if df.empty:
        return ""

    return df["rank_veiculo"].values[0]


@callback(
    Output("indicador-gasto-retrabalho-total-veiculo", "children"),
    Input("store-input-dados-retrabalho-veiculo", "data"),
)
def cb_total_gasto_retrabalho_pecas_veiculo_modelo(data):
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
    df = veiculos_service.get_indicador_total_gasto_retrabalho_pecas_modelo_veiculo(
        id_veiculo, datas, min_dias, [modelo_escolhido], lista_oficinas, lista_secaos, lista_os
    )

    if df.empty:
        return ""

    total_gasto = df["TOTAL_GASTO"].values[0]
    total_gasto_fmt = formata_float_para_real(total_gasto)

    return total_gasto_fmt


@callback(
    Output("indicador-rank-gasto-retrabalho-veiculo", "children"),
    Input("store-input-dados-retrabalho-veiculo", "data"),
)
def cb_rank_gasto_retrabalho_pecas_veiculo_modelo(data):
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
    df = veiculos_service.get_indicador_rank_gasto_retrabalho_pecas_modelo_veiculo(
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
    running=[(Output("loading-overlay-guia-por-veiculo", "visible"), True, False)],
)
def plota_grafico_evolucao_quantidade_os_por_mes(data):
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


##############################################################################
# Callbacks para as tabelas ##################################################
##############################################################################


@callback(
    Output("tabela-top-servicos-categorizados-veiculo", "rowData"),
    Input("store-input-dados-retrabalho-veiculo", "data"),
)
def cb_tabela_top_servicos_veiculo(data):
    # Valida se os dados do estado estão OK, caso contrário retorna os dados padrão
    if not data or not data["valido"]:
        return []

    # Obtem os dados do estado
    id_veiculo = data["id_veiculo"]
    datas = data["datas"]
    min_dias = data["min_dias"]
    modelo_escolhido = data["modelo_escolhido"]
    lista_oficinas = data["lista_oficinas"]
    lista_secaos = data["lista_secaos"]
    lista_os = data["lista_os"]

    df = veiculos_service.get_dados_tabela_top_servicos_veiculo(
        id_veiculo, datas, min_dias, [modelo_escolhido], lista_oficinas, lista_secaos, lista_os
    )

    return df.to_dict(orient="records")


@callback(
    Output("tabela-lista-os-pecas-veiculo", "rowData"),
    Input("store-input-dados-retrabalho-veiculo", "data"),
)
def cb_tabela_detalhamento_os_pecas_veiculo(data):
    # Valida se os dados do estado estão OK, caso contrário retorna os dados padrão
    if not data or not data["valido"]:
        return []

    # Obtem os dados do estado
    id_veiculo = data["id_veiculo"]
    datas = data["datas"]
    min_dias = data["min_dias"]
    modelo_escolhido = data["modelo_escolhido"]
    lista_oficinas = data["lista_oficinas"]
    lista_secaos = data["lista_secaos"]
    lista_os = data["lista_os"]

    df = veiculos_service.get_dados_tabela_lista_os_pecas_veiculo(
        id_veiculo, datas, min_dias, [modelo_escolhido], lista_oficinas, lista_secaos, lista_os
    )

    # Ação de visualização
    df["acao"] = "🔍 Detalhar"

    return df.to_dict(orient="records")


##############################################################################
# Callbacks Excel ############################################################
##############################################################################


# Callback para realizar o download quando o botão da categoria de OS do veículo for clicado
@callback(
    Output("download-excel-top-servicos-veiculo", "data"),
    [
        Input("btn-exportar-excel-top-servicos-veiculo", "n_clicks"),
        Input("store-input-dados-retrabalho-veiculo", "data"),
    ],
    prevent_initial_call=True,
)
def cb_excel_tabela_top_servicos_veiculo(n_clicks, data):
    ctx = callback_context  # Obtém o contexto do callback
    if not ctx.triggered:
        return dash.no_update  # Evita execução desnecessária

    # Verifica se o callback foi acionado pelo botão de download
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if triggered_id != "btn-exportar-excel-top-servicos-veiculo":
        return dash.no_update  # Ignora mudanças nos outros inputs

    if not n_clicks or n_clicks <= 0:
        return dash.no_update

    # Valida se os dados do estado estão OK, caso contrário retorna os dados padrão
    if not data or not data["valido"]:
        return dash.no_update

    # Obtem os dados do estado
    id_veiculo = data["id_veiculo"]
    datas = data["datas"]
    min_dias = data["min_dias"]
    modelo_escolhido = data["modelo_escolhido"]
    lista_oficinas = data["lista_oficinas"]
    lista_secaos = data["lista_secaos"]
    lista_os = data["lista_os"]

    df = veiculos_service.get_dados_tabela_top_servicos_veiculo(
        id_veiculo, datas, min_dias, [modelo_escolhido], lista_oficinas, lista_secaos, lista_os
    )

    excel_data = gerar_excel(df=df)

    date_now = datetime.now().strftime("%d-%m-%Y")
    return dcc.send_bytes(excel_data, f"tabela_servicos_veiculo_categorizados_{date_now}.xlsx")


# Callback para realizar o download quando o botão da tabela de os e peças do veículo for clicado
@callback(
    Output("download-excel-tabela-os-pecas-veiculo", "data"),
    [
        Input("btn-exportar-excel-tabela-os-pecas-veiculo", "n_clicks"),
        Input("store-input-dados-retrabalho-veiculo", "data"),
    ],
    prevent_initial_call=True,
)
def cb_excel_tabela_os_pecas_veiculo(n_clicks, data):
    ctx = callback_context  # Obtém o contexto do callback
    if not ctx.triggered:
        return dash.no_update  # Evita execução desnecessária

    # Verifica se o callback foi acionado pelo botão de download
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if triggered_id != "btn-exportar-excel-tabela-os-pecas-veiculo":
        return dash.no_update  # Ignora mudanças nos outros inputs

    if not n_clicks or n_clicks <= 0:
        return dash.no_update

    # Valida se os dados do estado estão OK, caso contrário retorna os dados padrão
    if not data or not data["valido"]:
        return dash.no_update

    # Obtem os dados do estado
    id_veiculo = data["id_veiculo"]
    datas = data["datas"]
    min_dias = data["min_dias"]
    modelo_escolhido = data["modelo_escolhido"]
    lista_oficinas = data["lista_oficinas"]
    lista_secaos = data["lista_secaos"]
    lista_os = data["lista_os"]

    df = veiculos_service.get_dados_tabela_lista_os_pecas_veiculo(
        id_veiculo, datas, min_dias, [modelo_escolhido], lista_oficinas, lista_secaos, lista_os
    )

    excel_data = gerar_excel(df=df)

    date_now = datetime.now().strftime("%d-%m-%Y")
    return dcc.send_bytes(excel_data, f"tabela_os_pecas_veiculo_{date_now}.xlsx")


##############################################################################
# Botão detalhar #############################################################
##############################################################################


@callback(
    Output("url", "href", allow_duplicate=True),
    Input("tabela-lista-os-pecas-veiculo", "cellRendererData"),
    Input("tabela-lista-os-pecas-veiculo", "virtualRowData"),
    Input("store-input-dados-retrabalho-veiculo", "data"),
    prevent_initial_call=True,
)
def cb_pag_veiculo_botao_detalhar_os_tabela_os(linha, linha_virtual, data):
    ctx = callback_context  # Obtém o contexto do callback
    if not ctx.triggered:
        return dash.no_update  # Evita execução desnecessária

    # Verifica se o callback foi acionado pelo botão de visualização
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[1]

    if triggered_id != "cellRendererData":
        return dash.no_update

    # Acessa os demais dados da linha
    linha_alvo = linha_virtual[linha["rowIndex"]]

    # Pega o parâmetro final (# da os)
    numero_da_os = linha_alvo["NUMERO DA OS"]
    # Min Dias
    min_dias = data["min_dias"]

    url_params = [
        f"os={numero_da_os}",
        f"mindiasretrabalho={min_dias}",
    ]
    url_params_str = "&".join(url_params)

    return f"/retrabalho-por-os?{url_params_str}"


##############################################################################
# Layout #####################################################################
##############################################################################
layout = dbc.Container(
    [
        # Estado
        dcc.Store(id="store-input-dados-retrabalho-veiculo"),
        # Loading
        dmc.LoadingOverlay(
            visible=True,
            id="loading-overlay-guia-por-veiculo",
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
                            dbc.CardFooter(["Rank Retrabalho / Modelo", html.Br(), "(menor = melhor)"]),
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
                            dbc.CardFooter(["Rank Correção Primeira / Modelo", html.Br(), "(maior = melhor)"]),
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
                            dbc.CardFooter(["Total de OSs executadas", html.Br(), "(no período selecionado)"]),
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
                            dbc.CardFooter(["Rank de OSs / Modelo", html.Br(), "(menor = melhor)"]),
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
                            dbc.CardFooter(["Total gasto com peças", html.Br(), "(no período)"]),
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
                            dbc.CardFooter(["Rank Gasto Total Peças / Modelo", html.Br(), "(menor = melhor)"]),
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
                            dbc.CardFooter(["Total gasto com retrabalho", html.Br(), "(no período selecionado)"]),
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
                            dbc.CardFooter(["Rank Gasto Retrabalho / Modelo", html.Br(), "(menor = melhor)"]),
                        ],
                        class_name="card-box-shadow",
                    ),
                    md=3,
                ),
            ],
            justify="center",
        ),
        dbc.Row(dmc.Space(h=40)),
        dmc.Space(h=40),
        # Gráfico de Quantidade de OS / mes
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
        # Graficos de Evolução do Retrabalho por Mês
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
        # Graficos de Evolução do Retrabalho por Seção
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
        # Grafico de Evolução do Custo
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
                dbc.Col(DashIconify(icon="mdi:account-wrench", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Detalhamento dos Serviços",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        gera_labels_inputs_veiculos("labels-tabela-top-servicos-categorizados-veiculo"),
                                        width=True,
                                    ),
                                    dbc.Col(
                                        html.Div(
                                            [
                                                html.Button(
                                                    "Exportar para Excel",
                                                    id="btn-exportar-excel-top-servicos-veiculo",
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
                                                dcc.Download(id="download-excel-top-servicos-veiculo"),
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
            id="tabela-top-servicos-categorizados-veiculo",
            columnDefs=veiculos_tabelas.tbl_top_servicos_categorizados_veiculo,
            rowData=[],
            defaultColDef={"filter": True, "floatingFilter": True},
            columnSize="autoSize",
            dashGridOptions={
                "localeText": locale_utils.AG_GRID_LOCALE_BR,
            },
            style={"height": 400, "resize": "vertical", "overflow": "hidden"},  # -> permite resize
        ),
        dmc.Space(h=40),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="mdi:cog-outline", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Lista de OS e Peças do Veículo",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            dbc.Col(gera_labels_inputs_veiculos("labels-tabela-lista-os-pecas-do-veiculo"), width=True),
                            dbc.Col(
                                html.Div(
                                    [
                                        html.Button(
                                            "Exportar para Excel",
                                            id="btn-exportar-excel-tabela-os-pecas-veiculo",
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
                                        dcc.Download(id="download-excel-tabela-os-pecas-veiculo"),
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
        dmc.Space(h=40),
        dag.AgGrid(
            id="tabela-lista-os-pecas-veiculo",
            columnDefs=veiculos_tabelas.tbl_detalhamento_os_pecas_veiculo,
            rowData=[],
            defaultColDef={"filter": True, "floatingFilter": True},
            columnSize="autoSize",
            dashGridOptions={
                "localeText": locale_utils.AG_GRID_LOCALE_BR,
            },
            style={"height": 600, "resize": "vertical", "overflow": "hidden"},  # -> permite resize
        ),
        dmc.Space(h=40),
    ]
)


##############################################################################
# Registro da página #########################################################
##############################################################################
dash.register_page(__name__, name="Veículo", path="/retrabalho-por-veiculo", icon="mdi:bus")
