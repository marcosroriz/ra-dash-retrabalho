#!/usr/bin/env python
# coding: utf-8

# Dashboard que lista o retrabalho de um colaborador

##############################################################################
# IMPORTS ####################################################################
##############################################################################
# Bibliotecas básicas
from datetime import date, datetime
import pandas as pd

# Importar bibliotecas para manipulação de URL
import ast
from urllib.parse import urlparse, parse_qs, unquote

# Importar bibliotecas do dash básicas e plotly
import dash
from dash import html, dcc, callback, Input, Output
import plotly.graph_objects as go
import plotly.express as px

# Importar bibliotecas do bootstrap e ag-grid
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
from dash import callback_context

# Dash componentes Mantine e icones
import dash_mantine_components as dmc
from dash_iconify import DashIconify

# Banco de Dados
from db import PostgresSingleton

# Imports gerais
from modules.entities_utils import get_mecanicos, get_oficinas, get_secoes, gerar_excel
import locale_utils

# Imports específicos
from modules.colaborador.colaborador_service import ColaboradorService
import modules.colaborador.graficos as colaborador_graficos
import modules.colaborador.tabelas as colaborador_tabelas


##############################################################################
# LEITURA DE DADOS ###########################################################
##############################################################################
# Conexão com os bancos
pgDB = PostgresSingleton.get_instance()
pgEngine = pgDB.get_engine()

# Cria o serviço
colab_service = ColaboradorService(pgEngine)

# Colaboradores / Mecânicos
df_mecanicos = get_mecanicos(pgEngine)

# Obtem a lista de Oficinas
df_oficinas = get_oficinas(pgEngine)
lista_todas_oficinas = df_oficinas.to_dict(orient="records")
lista_todas_oficinas.insert(0, {"LABEL": "TODAS"})

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

# Função auxiliar para transformar string '[%27A%27,%20%27B%27]' → ['A', 'B']
def parse_list_param(param):
    if param:
        try:
            return ast.literal_eval(param)
        except:
            return []
    return []


# Preenche os dados via URL
@callback(
    Output("input-select-colaborador-colaborador", "value"),
    Output("input-intervalo-datas-colaborador", "value"),
    Output("input-min-dias-colaborador", "value"),
    Output("input-select-secao-colaborador", "value"),
    Output("input-select-ordens-servico-colaborador", "value"),
    Output("input-select-modelos-colaborador", "value"),
    Output("input-select-oficina-colaborador", "value"),
    Input("url", "href"),
)
def callback_receber_campos_via_url(href):
    print("Recebendo os dados via URL")
    print(href)
    print("--------------------------------")

    if not href:
        return (
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
        )

    # Faz o parse dos parâmetros da url
    parsed_url = urlparse(href)
    query_params = parse_qs(parsed_url.query)

    id_colaborador = query_params.get("id_colaborador", [3295])[0]
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    datas = [query_params.get("data_inicio", ["2024-08-01"])[0], query_params.get("data_fim", [data_hoje])[0]]
    min_dias = query_params.get("min_dias", [10])[0]
    lista_secaos = parse_list_param(query_params.get("lista_secaos", [None])[0])
    lista_os = parse_list_param(query_params.get("lista_os", [None])[0])
    lista_modelos = parse_list_param(query_params.get("lista_modelos", [None])[0])
    lista_oficinas = parse_list_param(query_params.get("lista_oficinas", [None])[0])

    # Converte para int, se não for possível, retorna None
    if id_colaborador is not None:
        try:
            id_colaborador = int(id_colaborador)
        except ValueError:
            id_colaborador = None

    if min_dias is not None:
        try:
            min_dias = int(min_dias)
        except ValueError:
            min_dias = None

    return id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelos, lista_oficinas



##############################################################################
# Callbacks para os inputs ###################################################
##############################################################################


# Função para validar o input
def input_valido(id_colaborador, datas, min_dias, lista_secaos, lista_oficinas, lista_modelos, lista_os):
    if id_colaborador is None or not id_colaborador:
        return False

    if datas is None or not datas or None in datas or min_dias is None:
        return False

    if lista_oficinas is None or not lista_oficinas or None in lista_oficinas:
        return False

    if lista_secaos is None or not lista_secaos or None in lista_secaos:
        return False

    if lista_modelos is None or not lista_modelos or None in lista_modelos:
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


def gera_labels_inputs_colaborador(campo):
    # Cria o callback
    @callback(
        [
            Output(component_id=f"{campo}-labels", component_property="children"),
        ],
        [
            Input("input-min-dias-colaborador", "value"),
            Input("input-select-secao-colaborador", "value"),
            Input("input-select-ordens-servico-colaborador", "value"),
            Input("input-select-modelos-colaborador", "value"),
            Input("input-select-oficina-colaborador", "value"),
        ],
    )
    def atualiza_labels_inputs(min_dias, lista_secaos, lista_os, lista_modelo, lista_oficinas):
        labels_antes = [
            # DashIconify(icon="material-symbols:filter-arrow-right", width=20),
            dmc.Badge("Filtro", color="gray", variant="outline"),
        ]
        min_dias_label = [dmc.Badge(f"{min_dias} dias", variant="outline")]
        lista_oficinas_labels = []
        lista_secaos_labels = []
        lista_os_labels = []

        if lista_oficinas is None or not lista_oficinas or "TODAS" in lista_oficinas:
            lista_oficinas_labels.append(dmc.Badge("Todas as oficinas", variant="outline"))
        else:
            for oficina in lista_oficinas:
                lista_oficinas_labels.append(dmc.Badge(oficina, variant="dot"))

        if lista_modelo is None or not lista_modelo or "TODAS" in lista_modelo:
            lista_oficinas_labels.append(dmc.Badge("Todos os modelos", variant="outline"))
        else:
            for oficina in lista_modelo:
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

        return [
            dmc.Group(labels_antes + min_dias_label + lista_oficinas_labels + lista_secaos_labels + lista_os_labels)
        ]

    # Cria o componente
    return dmc.Group(id=f"{campo}-labels", children=[])


@callback(
    Output("input-select-oficina-colaborador", "value", allow_duplicate=True),
    Input("input-select-oficina-colaborador", "value"),
    prevent_initial_call=True,
)
def corrige_input_oficina(lista_oficinas):
    print("--- corrigindo input oficina")
    print(lista_oficinas)
    print("--------------------------------")
    return corrige_input(lista_oficinas)


@callback(
    Output("input-select-secao-colaborador", "value", allow_duplicate=True),
    Input("input-select-secao-colaborador", "value"),
    prevent_initial_call=True,
)
def corrige_input_secao(lista_secaos):
    print("--- corrigindo input secao")
    print(lista_secaos)
    print("--------------------------------")
    return corrige_input(lista_secaos)


@callback(
    [
        Output("input-select-modelos-colaborador", "options", allow_duplicate=True),
        Output("input-select-modelos-colaborador", "value", allow_duplicate=True),
    ],
    [
        Input("input-select-modelos-colaborador", "value"),
        Input("input-select-colaborador-colaborador", "value"),
    ],
    prevent_initial_call=True,
)
def corrige_input_modelo(lista_modelos, id_colaborador):
    print("--- corrigindo input modelo")
    print(lista_modelos)
    print(id_colaborador)
    print("--------------------------------")

    # Verifica se há colaborador selecionado
    if id_colaborador is None or not id_colaborador:
        # Retorna a opção padrão (TODAS)
        return [{"label": "TODAS", "value": "TODAS"}], ["TODAS"]

    # Obtém os modelos possíveis
    df_modelos_possiveis = colab_service.get_modelos_veiculos_colaborador(id_colaborador)

    # Transforma em lista e insere TODAS
    lista_modelos_possiveis = df_modelos_possiveis.to_dict(orient="records")
    lista_modelos_possiveis.insert(0, {"LABEL": "TODAS"})
    lista_options = [{"label": os["LABEL"], "value": os["LABEL"]} for os in lista_modelos_possiveis]

    return lista_options, corrige_input(lista_modelos)


@callback(
    [
        Output("input-select-ordens-servico-colaborador", "options", allow_duplicate=True),
        Output("input-select-ordens-servico-colaborador", "value", allow_duplicate=True),
    ],
    [
        Input("input-select-ordens-servico-colaborador", "value"),
        Input("input-select-colaborador-colaborador", "value"),
    ],
    prevent_initial_call=True,
)
def corrige_input_ordem_servico(lista_os, id_colaborador):
    print("--- corrigindo input ordem servico")
    print(lista_os)
    print(id_colaborador)
    print("--------------------------------")

    # Verifica se há colaborador selecionado
    if id_colaborador is None or not id_colaborador:
        # Retorna a opção padrão (TODAS)
        return [{"label": "TODAS", "value": "TODAS"}], ["TODAS"]

    # Obtém as OS possíveis
    df_os_possiveis = colab_service.get_os_possiveis_colaborador(id_colaborador)

    # Transforma em lista e insere TODAS
    lista_os_possiveis = df_os_possiveis.to_dict(orient="records")
    lista_os_possiveis.insert(0, {"LABEL": "TODAS"})
    lista_options = [{"label": os["LABEL"], "value": os["LABEL"]} for os in lista_os_possiveis]

    return lista_options, corrige_input(lista_os)


##############################################################################
# Callbacks para o estado ####################################################
##############################################################################


@callback(
    Output("store-input-dados-retrabalho-colaborador", "data"),
    [
        Input("input-select-colaborador-colaborador", "value"),
        Input("input-intervalo-datas-colaborador", "value"),
        Input("input-min-dias-colaborador", "value"),
        Input("input-select-secao-colaborador", "value"),
        Input("input-select-ordens-servico-colaborador", "value"),
        Input("input-select-modelos-colaborador", "value"),
        Input("input-select-oficina-colaborador", "value"),
    ],
)
def callback_sincroniza_input_colaborador_store(
    id_colaborador=3295,
    datas=None,
    min_dias=None,
    lista_secaos=None,
    lista_os=None,
    lista_modelo=None,
    lista_oficina=None,
):
    # Input padrão
    input_dict = {
        "valido": False,
        "id_colaborador": id_colaborador,
        "datas": datas,
        "min_dias": min_dias,
        "lista_secaos": lista_secaos,
        "lista_os": lista_os,
        "lista_modelo": lista_modelo,
        "lista_oficina": lista_oficina,
    }

    # Validação dos inputs
    # id_colaborador, datas, min_dias, lista_oficinas, lista_secaos, lista_os):
    if input_valido(id_colaborador, datas, min_dias, lista_secaos, lista_oficina, lista_modelo, lista_os):
        input_dict["valido"] = True
    else:
        input_dict["valido"] = False

    return input_dict


##############################################################################
# Callbacks para indicadores #################################################
##############################################################################


@callback(
    [
        Output("indicador-total-os-trabalho", "children"),
        Output("indicador-quantidade-servico", "children"),
        Output("indicador-correcao-de-primeira", "children"),
        Output("indicador-retrabalho", "children"),
        Output("indicador-rank-servico", "children"),
        Output("indicador-rank-os", "children"),
        Output("indicador-nota-colaborador", "children"),
        Output("indicador-rank-posicao-nota", "children"),
        Output("indicador-gasto-total-colaborador", "children"),
        Output("indicador-gasto-retrabalho-total-colaborador", "children"),
    ],
    [
        Input("store-input-dados-retrabalho-colaborador", "data"),
    ],
    running=[(Output("loading-overlay", "visible"), True, False)],
)
def calcular_indicadores_colaborador(data):
    # Valida se os dados do estado estão OK, caso contrário retorna os dados padrão
    if not data or not data["valido"]:
        return "", "", "", "", "", "", "", "", "", ""

    # Obtem os dados do estado
    id_colaborador = data["id_colaborador"]
    datas = data["datas"]
    min_dias = data["min_dias"]
    lista_secaos = data["lista_secaos"]
    lista_os = data["lista_os"]
    lista_modelo = data["lista_modelo"]
    lista_oficina = data["lista_oficina"]

    # Define resposta padrão vazia para caso colaborador nao tenha executado nenhuma OS no período
    resposta_padrao_vazia = (
        "Nenhuma OS realizada no período selecionado.",
        "Nenhuma OS realizada no período selecionado.",
        "Nenhuma OS realizada no período selecionado.",
        "Nenhuma OS realizada no período selecionado.",
        "Nenhuma OS realizada no período selecionado.",
        "Nenhuma OS realizada no período selecionado.",
        "Nenhuma OS realizada no período selecionado.",
        "Nenhuma OS realizada no período selecionado.",
        "Nenhuma OS realizada no período selecionado.",
        "Nenhuma OS realizada no período selecionado.",
    )

    # Obtém análise estatística
    df_os_analise = colab_service.get_indicadores_gerais_retrabalho_colaborador(
        id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina
    )

    if df_os_analise.empty:
        return resposta_padrao_vazia

    # Indicador 1: Total de OSs trabalhadas
    total_os = f"{df_os_analise['TOTAL_OS'].iloc[0]}"
    # Indicador 2: Quantidade de serviços únicos realizados
    servicos_diferentes = df_os_analise["QTD_SERVICOS_DIFERENTES"].iloc[0]
    quantidade_servicos = f"{servicos_diferentes}"

    # Indicadores de correção de primeira e retrabalho
    if not df_os_analise.empty and all(
        col in df_os_analise.columns for col in ["PERC_CORRECAO_PRIMEIRA", "PERC_RETRABALHO"]
    ):
        correcao_primeira = f"{df_os_analise['PERC_CORRECAO_PRIMEIRA'].iloc[0]}%"
        retrabalho = f"{df_os_analise['PERC_RETRABALHO'].iloc[0] if not df_os_analise['PERC_RETRABALHO'].iloc[0] == None else 0}%"
    else:
        correcao_primeira = "Dados insuficientes para calcular correções de primeira"
        retrabalho = "Dados insuficientes para calcular retrabalho"

    df_rank_servico = colab_service.get_indicador_rank_servico_colaborador(
        id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina
    )

    if df_rank_servico.empty:
        return resposta_padrao_vazia

    df_rank_os = colab_service.get_indicador_rank_total_os_colaborador(
        id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina
    )
    if df_rank_os.empty:
        return resposta_padrao_vazia

    # Indicadores Rank
    rank_servico = f"{df_rank_servico['rank_colaborador'].iloc[0]}"
    rank_os_absoluta = f"{df_rank_os['rank_colaborador'].iloc[0]}"

    df_nota_media = colab_service.get_indicador_nota_media_colaborador(
        id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina
    )

    if df_nota_media.empty:
        return resposta_padrao_vazia

    nota_media = f"{df_nota_media['nota_media_colaborador'].iloc[0] if not df_nota_media['nota_media_colaborador'].iloc[0]  is None else 0}"

    df_nota_posicao = colab_service.get_indicador_posicao_rank_nota_media(
        id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina
    )

    if df_nota_posicao.empty:
        return resposta_padrao_vazia

    rank_nota_posicao = f"{df_nota_posicao['rank_colaborador'].iloc[0]}"

    df_gasto = colab_service.get_indicador_gasto_colaborador(
        id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina
    )
    gasto_colaborador = f"{df_gasto['TOTAL_GASTO'].iloc[0]}"
    gasto_retrabalho = f"{df_gasto['TOTAL_GASTO_RETRABALHO'].iloc[0]}"

    return (
        total_os,
        quantidade_servicos,
        correcao_primeira,
        retrabalho,
        rank_servico,
        rank_os_absoluta,
        nota_media,
        rank_nota_posicao,
        gasto_colaborador,
        gasto_retrabalho,
    )


##############################################################################
# Callbacks para os gráficos #################################################
##############################################################################


@callback(
    Output("graph-pizza-sintese-colaborador", "figure"),
    Input("store-input-dados-retrabalho-colaborador", "data"),
)
def plota_grafico_pizza_sintese_colaborador(data):
    # Valida se os dados do estado estão OK, caso contrário retorna os dados padrão
    if not data or not data["valido"]:
        return go.Figure()

    # Obtem os dados do estado
    id_colaborador = data["id_colaborador"]
    datas = data["datas"]
    min_dias = data["min_dias"]
    lista_secaos = data["lista_secaos"]
    lista_os = data["lista_os"]
    lista_modelo = data["lista_modelo"]
    lista_oficina = data["lista_oficina"]

    # Obtém análise estatística
    df_os_analise = colab_service.get_sinteze_retrabalho_colaborador_para_grafico_pizza(
        id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina
    )

    if df_os_analise.empty:
        return go.Figure()

    fig = colaborador_graficos.grafico_pizza_colaborador(df_os_analise)
    return fig


@callback(
    Output("graph-evolucao-retrabalho-por-mes", "figure"),
    Input("store-input-dados-retrabalho-colaborador", "data"),
)
def plota_grafico_retrabalho_colaborador_por_mes(data):
    # Valida se os dados do estado estão OK, caso contrário retorna os dados padrão
    if not data or not data["valido"]:
        return go.Figure()

    # Obtem os dados do estado
    id_colaborador = data["id_colaborador"]
    datas = data["datas"]
    min_dias = data["min_dias"]
    lista_secaos = data["lista_secaos"]
    lista_os = data["lista_os"]
    lista_modelo = data["lista_modelo"]
    lista_oficina = data["lista_oficina"]

    # Obtém análise estatística
    df = colab_service.get_evolucao_retrabalho_por_mes(
        id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina
    )

    # Caso não haja dados, retorna um gráfico vazio
    if df.empty:
        return go.Figure()

    # Plota o gráfico
    fig = colaborador_graficos.gerar_grafico_evolucao_retrabalho_colaborador_por_mes(df)

    return fig


@callback(
    Output("graph-evolucao-nota-por-mes", "figure"),
    Input("store-input-dados-retrabalho-colaborador", "data"),
)
def plota_grafico_nota_media_colaborador_por_mes(data):
    # Valida se os dados do estado estão OK, caso contrário retorna os dados padrão
    if not data or not data["valido"]:
        return go.Figure()

    # Obtem os dados do estado
    id_colaborador = data["id_colaborador"]
    datas = data["datas"]
    min_dias = data["min_dias"]
    lista_secaos = data["lista_secaos"]
    lista_os = data["lista_os"]
    lista_modelo = data["lista_modelo"]
    lista_oficina = data["lista_oficina"]

    # Obtém análise estatística
    df_os_analise = colab_service.get_evolucao_nota_media_colaborador_por_mes(
        id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina
    )

    # Caso não haja dados, retorna um gráfico vazio
    if df_os_analise.empty:
        return go.Figure()

    # Plota o gráfico
    fig = colaborador_graficos.gerar_grafico_evolucao_nota_media_colaborador_por_mes(df_os_analise)

    return fig


@callback(
    Output("graph-evolucao-gasto-colaborador", "figure"),
    Input("store-input-dados-retrabalho-colaborador", "data"),
)
def plota_grafico_gasto_colaborador_por_mes(data):
    # Valida se os dados do estado estão OK, caso contrário retorna os dados padrão
    if not data or not data["valido"]:
        return go.Figure()

    # Obtem os dados do estado
    id_colaborador = data["id_colaborador"]
    datas = data["datas"]
    min_dias = data["min_dias"]
    lista_secaos = data["lista_secaos"]
    lista_os = data["lista_os"]
    lista_modelo = data["lista_modelo"]
    lista_oficina = data["lista_oficina"]

    # Obtém análise estatística
    df = colab_service.get_evolucao_gasto_colaborador_por_mes(
        id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina
    )

    # Caso não haja dados, retorna um gráfico vazio
    if df.empty:
        return go.Figure()

    # Plota o gráfico
    fig = colaborador_graficos.gerar_grafico_evolucao_gasto_colaborador_por_mes(df)

    return fig


@callback(
    Output("graph-pizza-atuacao-geral", "figure"),
    Input("store-input-dados-retrabalho-colaborador", "data"),
)
def plota_grafico_pizza_atuacao_colaborador(data):
    # Valida se os dados do estado estão OK, caso contrário retorna os dados padrão
    if not data or not data["valido"]:
        return go.Figure()

    # Obtem os dados do estado
    id_colaborador = data["id_colaborador"]
    datas = data["datas"]
    min_dias = data["min_dias"]
    lista_secaos = data["lista_secaos"]
    lista_os = data["lista_os"]
    lista_modelo = data["lista_modelo"]
    lista_oficina = data["lista_oficina"]

    # Obtem dados
    df = colab_service.get_atuacao_colaborador(
        id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina
    )

    # Caso não haja dados, retorna um gráfico vazio
    if df.empty:
        return go.Figure()

    # Prepara os dados para o gráfico
    df["PERCENTAGE"] = (df["QUANTIDADE"] / df["QUANTIDADE"].sum()) * 100

    # Plota o gráfico
    fig = colaborador_graficos.gerar_grafico_pizza_atuacao_colaborador(df)

    return fig


@callback(
    Output("graph-principais-os", "figure"),
    Input("store-input-dados-retrabalho-colaborador", "data"),
)
def plota_grafico_top_10_os_colaborador(data):
    # Valida se os dados do estado estão OK, caso contrário retorna os dados padrão
    if not data or not data["valido"]:
        return go.Figure()

    # Obtem os dados do estado
    id_colaborador = data["id_colaborador"]
    datas = data["datas"]
    min_dias = data["min_dias"]
    lista_secaos = data["lista_secaos"]
    lista_os = data["lista_os"]
    lista_modelo = data["lista_modelo"]
    lista_oficina = data["lista_oficina"]

    # Obtem OS
    df = colab_service.get_top_10_tipo_os_colaborador(
        id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina
    )

    # Caso não haja dados, retorna um gráfico vazio
    if df.empty:
        return go.Figure()

    # Plota o gráfico
    fig = colaborador_graficos.gerar_grafico_pizza_top_10_os_colaborador(df)

    return fig


##############################################################################
# Callbacks para as tabelas ##################################################
##############################################################################


@callback(
    Output("tabela-top-os-colaborador", "rowData"),
    Input("store-input-dados-retrabalho-colaborador", "data"),
)
def tabela_visao_geral_colaborador(data):
    # Valida se os dados do estado estão OK, caso contrário retorna os dados padrão
    if not data or not data["valido"]:
        return []

    # Obtem os dados do estado
    id_colaborador = data["id_colaborador"]
    datas = data["datas"]
    min_dias = data["min_dias"]
    lista_secaos = data["lista_secaos"]
    lista_os = data["lista_os"]
    lista_modelo = data["lista_modelo"]
    lista_oficina = data["lista_oficina"]

    df = colab_service.get_dados_tabela_retrabalho_por_categoria_os_colaborador(
        id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina
    )

    return df.to_dict("records")


@callback(
    [
        Output("tabela-detalhamento-os-colaborador", "rowData"),
        Output("input-lista-vec-detalhar-problema-colaborador", "options"),
    ],
    Input("store-input-dados-retrabalho-colaborador", "data"),
)
def tabela_detalhamento_os_colaborador(data):
    # Valida se os dados do estado estão OK, caso contrário retorna os dados padrão
    if not data or not data["valido"]:
        return [], []

    # Obtem os dados do estado
    id_colaborador = data["id_colaborador"]
    datas = data["datas"]
    min_dias = data["min_dias"]
    lista_secaos = data["lista_secaos"]
    lista_os = data["lista_os"]
    lista_modelo = data["lista_modelo"]
    lista_oficina = data["lista_oficina"]

    df_os_detalhada_colaborador = colab_service.get_dados_tabela_detalhamento_os_colaborador(
        id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina
    )

    # Gera as opções dos problemas, como dict pois o colaborador pode ter o mesmo problema várias vezes
    dict_options = {}
    for _, row in df_os_detalhada_colaborador.iterrows():
        value = f"{row['CODIGO DO VEICULO']},{row['DESCRICAO DO SERVICO']},{row['problem_no']}"
        lbl = f"{row['CODIGO DO VEICULO']} - Serviço: {row['DESCRICAO DO SERVICO']} - Problema: {row['problem_no']} "
        dict_options[value] = lbl

    # Converte para lista de dicionários
    lista_options = [{"label": lbl, "value": value} for value, lbl in dict_options.items()]
    lista_options.sort(key=lambda x: x["label"])

    return df_os_detalhada_colaborador.to_dict("records"), lista_options


@callback(
    Output("tabela-detalhamento-problema-colaborador", "rowData"),
    [
        Input("input-lista-vec-detalhar-problema-colaborador", "value"),
        Input("store-input-dados-retrabalho-colaborador", "data"),
    ],
)
def tabela_detalhamento_problema_colaborador(vec_problema_lbl, data):
    # Valida se os dados do estado estão OK, caso contrário retorna os dados padrão
    if not data or not data["valido"] or vec_problema_lbl is None or vec_problema_lbl == "":
        return []

    # Obtem os dados do estado
    id_colaborador = data["id_colaborador"]
    datas = data["datas"]
    min_dias = data["min_dias"]
    lista_secaos = data["lista_secaos"]
    lista_os = data["lista_os"]
    lista_modelo = data["lista_modelo"]
    lista_oficina = data["lista_oficina"]

    vec_problema_options = vec_problema_lbl.split(",")
    vec_problema = vec_problema_options[0]
    servico = vec_problema_options[1]
    problema = vec_problema_options[2]

    df_os_problema_colaborador = colab_service.get_dados_tabela_detalhamento_problema_colaborador(
        id_colaborador,
        datas,
        min_dias,
        lista_secaos,
        lista_os,
        lista_modelo,
        lista_oficina,
        vec_problema,
        servico,
        problema,
    )

    return df_os_problema_colaborador.to_dict("records")


# Callback para realizar o download quando o botão de os categorizadasfor clicado
@callback(
    Output("download-excel-categorizadas", "data"),
    [
        Input("btn-exportar-categorizadas-pag-colaborador", "n_clicks"),
        Input("store-input-dados-retrabalho-colaborador", "data"),
    ],
    prevent_initial_call=True,
)
def download_excel_categorizadas(n_clicks, data):
    ctx = callback_context  # Obtém o contexto do callback
    if not ctx.triggered:
        return dash.no_update  # Evita execução desnecessária

    # Verifica se o callback foi acionado pelo botão de download
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if triggered_id != "btn-exportar-categorizadas-pag-colaborador":
        return dash.no_update  # Ignora mudanças nos outros inputs

    if not n_clicks or n_clicks <= 0:
        return dash.no_update

    # Valida se os dados do estado estão OK, caso contrário retorna os dados padrão
    if not data or not data["valido"]:
        return dash.no_update

    # Obtem os dados do estado
    id_colaborador = data["id_colaborador"]
    datas = data["datas"]
    min_dias = data["min_dias"]
    lista_secaos = data["lista_secaos"]
    lista_os = data["lista_os"]
    lista_modelo = data["lista_modelo"]
    lista_oficina = data["lista_oficina"]

    df = colab_service.get_dados_tabela_retrabalho_por_categoria_os_colaborador(
        id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina
    )

    excel_data = gerar_excel(df=df)

    date_now = datetime.now().strftime("%d-%m-%Y")
    return dcc.send_bytes(excel_data, f"tabela_os_retrabalho_categorizadas_{date_now}.xlsx")


# Callback para realizar o download quando o botão de os categorizadasfor clicado
@callback(
    Output("download-excel-detalhamento-os-colaborador", "data"),
    [
        Input("btn-exportar-detalhamento-pag-colaborador", "n_clicks"),
        Input("store-input-dados-retrabalho-colaborador", "data"),
    ],
    prevent_initial_call=True,
)
def download_excel_detalhamento_os(n_clicks, data):
    ctx = callback_context  # Obtém o contexto do callback
    if not ctx.triggered:
        return dash.no_update  # Evita execução desnecessária

    # Verifica se o callback foi acionado pelo botão de download
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if triggered_id != "btn-exportar-detalhamento-pag-colaborador":
        return dash.no_update  # Ignora mudanças nos outros inputs

    if not n_clicks or n_clicks <= 0:
        return dash.no_update

        # Valida se os dados do estado estão OK, caso contrário retorna os dados padrão
    if not data or not data["valido"]:
        return dash.no_update

    # Obtem os dados do estado
    id_colaborador = data["id_colaborador"]
    datas = data["datas"]
    min_dias = data["min_dias"]
    lista_secaos = data["lista_secaos"]
    lista_os = data["lista_os"]
    lista_modelo = data["lista_modelo"]
    lista_oficina = data["lista_oficina"]

    df_os_detalhada_colaborador = colab_service.get_dados_tabela_detalhamento_os_colaborador(
        id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina
    )

    excel_data = gerar_excel(df=df_os_detalhada_colaborador)

    date_now = datetime.now().strftime("%d-%m-%Y")
    return dcc.send_bytes(excel_data, f"tabela_os_retrabalho_detalhamento_{date_now}.xlsx")


# Callback para realizar o download quando o botão de os categorizadasfor clicado
@callback(
    Output("download-excel-detalhamento-veiculo-prob-colaborador", "data"),
    [
        Input("btn-exportar-detalhamento-veiculo-prob-colaborador", "n_clicks"),
        Input("input-lista-vec-detalhar-problema-colaborador", "value"),
        Input("store-input-dados-retrabalho-colaborador", "data"),
    ],
    prevent_initial_call=True,
)
def download_excel_detalhamento_problema(n_clicks, vec_problema_lbl, data):
    ctx = callback_context  # Obtém o contexto do callback
    if not ctx.triggered:
        return dash.no_update  # Evita execução desnecessária

    # Verifica se o callback foi acionado pelo botão de download
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if triggered_id != "btn-exportar-detalhamento-veiculo-prob-colaborador":
        return dash.no_update  # Ignora mudanças nos outros inputs

    if not n_clicks or n_clicks <= 0:
        return dash.no_update

    if vec_problema_lbl is None:
        return dash.no_update

    # Valida se os dados do estado estão OK, caso contrário retorna os dados padrão
    if not data or not data["valido"]:
        return dash.no_update

    # Obtem os dados do estado
    id_colaborador = data["id_colaborador"]
    datas = data["datas"]
    min_dias = data["min_dias"]
    lista_secaos = data["lista_secaos"]
    lista_os = data["lista_os"]
    lista_modelo = data["lista_modelo"]
    lista_oficina = data["lista_oficina"]

    vec_problema_options = vec_problema_lbl.split(",")
    vec_problema = vec_problema_options[0]
    servico = vec_problema_options[1]
    problema = vec_problema_options[2]

    df_os_problema_colaborador = colab_service.get_dados_tabela_detalhamento_problema_colaborador(
        id_colaborador,
        datas,
        min_dias,
        lista_secaos,
        lista_os,
        lista_modelo,
        lista_oficina,
        vec_problema,
        servico,
        problema,
    )

    excel_data = gerar_excel(df=df_os_problema_colaborador)

    date_now = datetime.now().strftime("%d-%m-%Y")
    return dcc.send_bytes(excel_data, f"tabela_os_retrabalho_detalhamento_problema_{date_now}.xlsx")


##############################################################################
# Layout #####################################################################
##############################################################################
layout = dbc.Container(
    [
        # Estado (vem do app.py), mencionando aqui só para relembrarmos
        # dcc.Store(id="store-input-dados-retrabalho-colaborador")
        # Loading
        dmc.LoadingOverlay(
            visible=True,
            id="loading-overlay",
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
                                        dbc.Col(DashIconify(icon="mdi:account-wrench", width=45), width="auto"),
                                        dbc.Col(
                                            html.H1(
                                                [
                                                    "Visão geral do\u00a0",
                                                    html.Strong("Colaborador"),
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
                                                    dbc.Label("Colaborador (Código):"),
                                                    dcc.Dropdown(
                                                        id="input-select-colaborador-colaborador",
                                                        options=[
                                                            {
                                                                "label": f"{linha['LABEL_COLABORADOR']}",
                                                                "value": linha["CODIGO"],
                                                            }
                                                            for _, linha in df_mecanicos.iterrows()
                                                        ],
                                                        placeholder="Selecione um colaborador",
                                                        value=3295,
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
                                                    dbc.Label("Data (intervalo) de análise"),
                                                    dmc.DatePicker(
                                                        id="input-intervalo-datas-colaborador",
                                                        allowSingleDateInRange=True,
                                                        type="range",
                                                        minDate=date(2024, 8, 1),
                                                        maxDate=datetime.now().date(),
                                                        value=[date(2024, 8, 1), datetime.now().date()],
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
                                                    dbc.Label("Tempo (em dias) entre OS para retrabalho"),
                                                    dcc.Dropdown(
                                                        id="input-min-dias-colaborador",
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
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            html.Div(
                                                [
                                                    dbc.Label("Seções (categorias) de manutenção"),
                                                    dcc.Dropdown(
                                                        id="input-select-secao-colaborador",
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
                                                    dbc.Label("Oficinas"),
                                                    dcc.Dropdown(
                                                        id="input-select-oficina-colaborador",
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
                                                    dbc.Label("Modelo"),
                                                    dcc.Dropdown(
                                                        id="input-select-modelos-colaborador",
                                                        multi=True,
                                                        value=["TODAS"],
                                                        placeholder="Selecione um ou mais modelos...",
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
                                                        id="input-select-ordens-servico-colaborador",
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
                                ),
                            ]
                        ),
                    ],
                    md=8,
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
                            # Gráfico de pizza com a relação entre Retrabalho e Correção
                            dcc.Graph(id="graph-pizza-sintese-colaborador"),
                        ]
                    ),
                    md=4,
                ),
            ]
        ),
        dmc.Space(h=30),
        # Indicadores
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="icon-park-outline:ranking-list", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Indicadores",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            gera_labels_inputs_colaborador("labels-indicadores-pag-colaborador"),
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
                                        dmc.Title(id="indicador-quantidade-servico", order=2),
                                        DashIconify(
                                            icon="material-symbols:order-play-outline",
                                            width=48,
                                            color="black",
                                        ),
                                    ],
                                    justify="center",
                                    mt="md",
                                    mb="xs",
                                ),
                            ),
                            dbc.CardFooter("Total de tipo serviços"),
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
                                        dmc.Title(id="indicador-rank-servico", order=2),
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
                            dbc.CardFooter("Rank de serviços diferentes"),
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
                                        dmc.Title(id="indicador-total-os-trabalho", order=2),
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
                                        dmc.Title(id="indicador-rank-os", order=2),
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
                            dbc.CardFooter("Rank de OSs absolutas"),
                        ],
                        class_name="card-box-shadow",
                    ),
                    md=3,
                ),
            ],
            justify="center",
        ),
        dbc.Row(dmc.Space(h=20)),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                dmc.Group(
                                    [
                                        dmc.Title(id="indicador-retrabalho", order=2),
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
                            dbc.CardFooter("% das OS são retrabalho"),
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
                                        dmc.Title(id="indicador-correcao-de-primeira", order=2),
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
                            dbc.CardFooter("% das OSs correção de primeira"),
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
                                        dmc.Title(id="indicador-nota-colaborador", order=2),
                                        DashIconify(
                                            icon="material-symbols-light:bar-chart-4-bars-rounded",
                                            width=48,
                                            color="black",
                                        ),
                                    ],
                                    justify="center",
                                    mt="md",
                                    mb="xs",
                                ),
                            ),
                            dbc.CardFooter("Nota do colaborador"),
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
                                        dmc.Title(id="indicador-rank-posicao-nota", order=2),
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
                            dbc.CardFooter("Posição da nota media"),
                        ],
                        class_name="card-box-shadow",
                    ),
                    md=3,
                ),
            ],
        ),
        dbc.Row(dmc.Space(h=20)),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                dmc.Group(
                                    [
                                        dmc.Title(id="indicador-gasto-total-colaborador", order=2),
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
                    md=6,
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                dmc.Group(
                                    [
                                        dmc.Title(id="indicador-gasto-retrabalho-total-colaborador", order=2),
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
                    md=6,
                ),
            ],
            justify="center",
        ),
        dmc.Space(h=80),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="fluent:arrow-trending-wrench-20-filled", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Evolução da % de retrabalho e correção de primeira por mês",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            gera_labels_inputs_colaborador("labels-colaborador-evolucao-retrabalho-por-mes"),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        dcc.Graph(id="graph-evolucao-retrabalho-por-mes"),
        dmc.Space(h=40),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="fluent:arrow-trending-sparkle-20-filled", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4("Evolução da nota média por mês", className="align-self-center"),
                            dmc.Space(h=5),
                            gera_labels_inputs_colaborador("labels-colaborador-evolucao-nota-por-mes"),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        dcc.Graph(id="graph-evolucao-nota-por-mes"),
        dmc.Space(h=40),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="hugeicons:search-dollar", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4("Evolução do gasto médio com retrabalho por mês", className="align-self-center"),
                            dmc.Space(h=5),
                            gera_labels_inputs_colaborador("labels-colaborador-evolucao-gasto-por-mes"),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        dcc.Graph(id="graph-evolucao-gasto-colaborador"),
        dmc.Space(h=40),
        dbc.Row(
            [
                # Gráfico de Pizza
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4("Atuação Geral"),
                            dcc.Graph(id="graph-pizza-atuacao-geral"),
                        ]
                    ),
                    md=4,
                ),
                # Indicadores
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4("Atuação OS (TOP 10)"),
                            dcc.Graph(id="graph-principais-os"),
                        ]
                    ),
                    md=8,
                ),
            ],
            align="center",
        ),
        dmc.Space(h=40),
        dbc.Alert(
            [
                dbc.Row(
                    [
                        dbc.Col(DashIconify(icon="material-symbols:info-outline-rounded", width=45), width="auto"),
                        dbc.Col(
                            html.P(
                                """
                                As tabelas a seguir mostram a atuação do colaborador nas OS, começando por uma visão 
                                categórica, com todas as OS de um mesmo serviço. Depois, é possível consultar a atuação
                                individual em cada OS. Os textos são avaliados por modelos de Large Language Model 
                                (como ChatGPT e DeepSeek) para medir a qualidade das respostas. Por fim, é possível 
                                acompanhar o desempenho diante de um problema específico de um veículo, entendido como
                                um conjunto de OS relacionadas até a resolução completa da questão.
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
            color="info",
        ),
        dmc.Space(h=40),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="mdi:account-wrench", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Detalhamento do colaborador nas OSs escolhidas (por categoria)",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        gera_labels_inputs_colaborador("labels-tabela-colaborador-categorizadas-os"),
                                        width=True,
                                    ),
                                    dbc.Col(
                                        html.Div(
                                            [
                                                html.Button(
                                                    "Exportar para Excel",
                                                    id="btn-exportar-categorizadas-pag-colaborador",
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
                                                dcc.Download(id="download-excel-categorizadas"),
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
            id="tabela-top-os-colaborador",
            columnDefs=colaborador_tabelas.tbl_top_os_geral_retrabalho,
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
                dbc.Col(DashIconify(icon="mdi:car-search-outline", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Detalhamento do colaborador nas OSs escolhidas (por OS)",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        gera_labels_inputs_colaborador("labels-tabela-colaborador-detalhamento-os"),
                                        width=True,
                                    ),
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
                                                dcc.Download(id="download-excel-detalhamento-os-colaborador"),
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
            id="tabela-detalhamento-os-colaborador",
            columnDefs=colaborador_tabelas.tbl_detalhamento_os_colaborador,
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
                dbc.Col(DashIconify(icon="game-icons:time-bomb", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Detalhamento da atuação do colaborador em um problema de um veículo",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        gera_labels_inputs_colaborador(
                                            "labels-tabela-colaborador-detalhamento-veiculo-prob-colaborador"
                                        ),
                                        width=True,
                                    ),
                                    dbc.Col(
                                        html.Div(
                                            [
                                                html.Button(
                                                    "Exportar para Excel",
                                                    id="btn-exportar-detalhamento-veiculo-prob-colaborador",
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
                                                dcc.Download(id="download-excel-detalhamento-veiculo-prob-colaborador"),
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
        dmc.Space(h=20),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            html.Div(
                                [
                                    dbc.Label("Veículos e problema a detalhar:"),
                                    dcc.Dropdown(
                                        id="input-lista-vec-detalhar-problema-colaborador",
                                        options=[],
                                        placeholder="Selecione o veículo e problema",
                                    ),
                                ],
                                className="dash-bootstrap",
                            ),
                        ],
                        body=True,
                    ),
                    md=12,
                ),
            ],
        ),
        dmc.Space(h=20),
        dag.AgGrid(
            id="tabela-detalhamento-problema-colaborador",
            columnDefs=colaborador_tabelas.tbl_detalhamento_problema_colaborador,
            rowData=[],
            defaultColDef={"filter": True, "floatingFilter": True},
            columnSize="autoSize",
            dashGridOptions={
                "localeText": locale_utils.AG_GRID_LOCALE_BR,
            },
            style={"height": 500, "resize": "vertical", "overflow": "hidden"},  # -> permite resize
        ),
    ]
)


##############################################################################
# Registro da página #########################################################
##############################################################################
dash.register_page(__name__, name="Colaborador", path="/retrabalho-por-colaborador", icon="fluent-mdl2:timeline")


