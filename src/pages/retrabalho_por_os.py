#!/usr/bin/env python
# coding: utf-8

# Dashboard que lista o retrabalho de uma OS específica

##############################################################################
# IMPORTS ####################################################################
##############################################################################
# Bibliotecas básicas
import os
import pandas as pd
from datetime import date
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

# Imports gerais
from modules.entities_utils import get_tipos_eventos_telemetria_mix_com_data, get_tipos_eventos_telemetria_mix_com_gps

# Imports específicos
from modules.os.os_service import OSService
import modules.os.tabelas as os_tabelas
import modules.os.graficos as os_graficos

# Imports de mapa
import dash_leaflet as dl

##############################################################################
# LEITURA DE DADOS ###########################################################
##############################################################################
# Conexão com os bancos
pgDB = PostgresSingleton.get_instance()
pgEngine = pgDB.get_engine()

# Cria o serviço
os_service = OSService(pgEngine)

# Eventos da mix com data
df_eventos_mix_data = get_tipos_eventos_telemetria_mix_com_data(pgEngine)
df_eventos_mix_data = df_eventos_mix_data.sort_values(by="label")
lista_todos_eventos_com_data = df_eventos_mix_data.to_dict(orient="records")

# Eventos da mix com GPS
df_eventos_mix_gps = get_tipos_eventos_telemetria_mix_com_gps(pgEngine)
df_eventos_mix_gps = df_eventos_mix_gps.sort_values(by="label")
lista_todos_eventos_com_gps = df_eventos_mix_gps.to_dict(orient="records")

# MapBox
MAPBOX_KEY = os.getenv("MAPBOX_KEY", None)

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
        Output("card-input-detalhamento-os-selecionada", "style"),
        Output("card-input-detalhamento-select-dias-os-retrabalho", "style"),
        Output("input-detalhamento-os-selecionada-error", "style"),
        Output("input-detalhamento-select-dias-os-retrabalho-error", "style"),
    ],
    Input("input-detalhamento-os-selecionada", "value"),
    Input("input-detalhamento-select-dias-os-retrabalho", "value"),
)
def callback_sincroniza_input_store(os_value, dias_value):
    # Input padrão
    input_dict = {
        "valido": False,
        "os_numero": None,
        "min_dias_retrabalho": None,
    }

    # Flags para validação
    input_os_valido = True
    input_dias_valido = True

    # Validação muda a borda e também mostra campo de erro
    # Estilos das bordas dos inputs
    style_borda_ok = {
        "border": "2px solid #198754",  # verde bootstrap
    }
    style_borda_erro = {
        "border": "2px solid #dc3545",  # vermelho bootstrap
    }

    # Estilho das bordas dos inputs
    style_borda_input_os = style_borda_erro
    style_borda_input_dias = style_borda_erro

    # Estilos dos erros dos inputs
    style_campo_erro_visivel = {"display": "block"}
    style_campo_erro_oculto = {"display": "none"}
    style_campo_erro_input_os = style_campo_erro_visivel
    style_campo_erro_input_dias = style_campo_erro_visivel

    # Valida primeiro o min dias
    if dias_value and dias_value in [10, 15, 30]:
        input_dict["min_dias_retrabalho"] = dias_value
        style_borda_input_dias = style_borda_ok
        style_campo_erro_input_dias = style_campo_erro_oculto
    else:
        input_dias_valido = False

    # Valida se há algum número da OS (os_value)
    try:
        # Trim o input
        os_value = os_value.strip()
        if os_value and os_service.os_existe(os_value, dias_value):
            input_dict["os_numero"] = os_value
            style_borda_input_os = style_borda_ok
            style_campo_erro_input_os = style_campo_erro_oculto
        else:
            input_os_valido = False
    except Exception:
        input_os_valido = False

    input_dict["valido"] = input_os_valido and input_dias_valido

    return (
        input_dict,
        style_borda_input_os,
        style_borda_input_dias,
        style_campo_erro_input_os,
        style_campo_erro_input_dias,
    )


# Recupera as OS escolhidas a partir do input
@callback(
    Output("store-output-dados-detalhamento-os", "data"),
    Input("store-input-dados-detalhamento-os", "data"),
)
def callback_recupera_os_armazena_store_output(data):
    saida = {
        "sucesso": False,
        "df_os": {},
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

    # Asset ID (útil para acelerar as queries)
    saida["vec_asset_id"] = str(os_service.obtem_asset_id_veiculo(saida["codigo_veiculo"]))

    return saida


@callback(
    Output("input-select-data-eventos-mix-detalhamento-os", "value"),
    Output("input-select-data-eventos-mix-detalhamento-os-error", "style"),
    Input("input-select-data-eventos-mix-detalhamento-os", "value"),
    prevent_initial_call=True,
)
def cb_limita_dropdown_eventos_mix(selected):
    estilo_sem_erro = {"display": "none"}
    estilo_com_erro = {"display": "block"}
    if selected is None:
        return [], estilo_sem_erro
    if len(selected) > 3:
        return selected[:3], estilo_com_erro
    return selected, estilo_sem_erro


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

        # Valida se os dados do estado estão OK, caso contrário retorna os dados padrão
        if not data or not data["sucesso"]:
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
    # Valida se os dados do estado estão OK, caso contrário retorna os dados padrão
    if not data or not data["sucesso"]:
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

    # Obtem os dados do estado
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
    # Valida se os dados do estado estão OK, caso contrário retorna os dados padrão
    if not data or not data["sucesso"]:
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
    txt_total_os_no_problema = df_problema_os_alvo["NUMERO DA OS"].nunique()

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
    # Valida se os dados do estado estão OK, caso contrário retorna os dados padrão
    if not data or not data["sucesso"]:
        return []

    os_numero = data["os_numero"]
    df_os = pd.DataFrame(data["df_os"]).copy()

    # Preenche a linha do tempo somente com o problema da OS atual
    problem_no = df_os[df_os["NUMERO DA OS"] == int(os_numero)]["problem_no"].values[0]
    df_problema_os_alvo = df_os[(df_os["problem_no"] == problem_no)]

    problemas_ativos = df_problema_os_alvo.shape[0]

    # Problema atual (vem com line solid)
    timeline_items = []
    lista_os_problema_alvo = df_problema_os_alvo["NUMERO DA OS"].unique()

    for os in lista_os_problema_alvo:
        df_os_do_problema = df_os[df_os["NUMERO DA OS"] == os]

        os_status_os_emoji = df_os_do_problema["status_os_emoji"].values[0]
        os_colaborador = ", ".join(df_os_do_problema["nome_colaborador"].unique())
        os_total_colaboradores = len(df_os_do_problema["nome_colaborador"].unique())
        os_data_inicio = df_os_do_problema["DATA DA ABERTURA LABEL"].values[0]

        # Remove "Ainda não foi fechada" de lista_data_fim_problema
        lista_os_data_fim_problema = df_os_do_problema["DATA DO FECHAMENTO LABEL"].unique()
        lista_os_data_fim_problema = [d for d in lista_os_data_fim_problema if d != "Ainda não foi fechada"]
        os_data_fim = "Ainda não foi fechada"
        if len(lista_os_data_fim_problema) > 0:
            os_data_fim = lista_os_data_fim_problema[0]

        # Mesma lógica para o sintoma
        lista_os_sintoma_problema = df_os_do_problema["SINTOMA"].unique()
        lista_os_sintoma_valida = [s for s in lista_os_sintoma_problema if s != "Não Informado"]
        os_sintoma = "Não Informado"
        if len(lista_os_sintoma_valida) > 0:
            os_sintoma = ", ".join(lista_os_sintoma_valida)

        # Mesma lógica para a correção
        lista_os_correcao_problema = df_os_do_problema["CORRECAO"].unique()
        lista_os_correcao_valida = [c for c in lista_os_correcao_problema if c != "Não Informado"]
        os_correcao = "Não Informado"
        if len(lista_os_correcao_valida) > 0:
            os_correcao = ", ".join(lista_os_correcao_valida)

        titulo_item = dmc.Text(f"OS {os_numero}", size="lg")
        item_body = dbc.Row(
            [
                dmc.Text("🧑‍🔧 Colaborador: " + os_colaborador, size="sm", className="text-muted"),
                dmc.Text(
                    "👥 Total de colaboradores: " + str(os_total_colaboradores), size="sm", className="text-muted"
                ),
                dmc.Text("🚩 Início: " + os_data_inicio, size="sm", className="text-muted"),
                dmc.Text("📌 Fim: " + os_data_fim, size="sm", className="text-muted"),
                dmc.Text("💡 Sintoma: " + os_sintoma, size="sm", className="text-muted"),
                dmc.Text("💬 Correção: " + os_correcao, size="sm", className="text-muted"),
            ]
        )

        dmc_timeline_item = dmc.TimelineItem(
            bullet=os_status_os_emoji,
            title=titulo_item,
            lineVariant="solid",
            children=item_body,
        )

        # Se for a OS atual, adiciona um highlight especial
        if int(os_numero) == int(os):
            dmc_timeline_item = dmc.TimelineItem(
                bullet=os_status_os_emoji,
                title=titulo_item,
                lineVariant="solid",
                children=dmc.Paper(
                    withBorder=True, radius="lg", p="md", style={"backgroundColor": "#fff8e1"}, children=item_body
                ),
            )

        timeline_items.append(dmc_timeline_item)

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
    # Valida se os dados do estado estão OK, caso contrário retorna os dados padrão
    if not data or not data["sucesso"]:
        return []

    # Obtem os dados do estado
    df_os = pd.DataFrame(data["df_os"])

    return df_os.to_dict(orient="records")


##############################################################################
# Callbacks para os gráficos #################################################
##############################################################################


# Preenche o gantt com os dados do store
@callback(
    Output("graph-gantt-historico-problema-detalhamento-os", "figure"),
    Input("store-output-dados-detalhamento-os", "data"),
)
def plota_grafico_gantt_retrabalho_os(data):
    # Valida se os dados do estado estão OK, caso contrário retorna os dados padrão
    if not data or not data["sucesso"]:
        return go.Figure()

    # Obtem os dados do estado
    df_os = pd.DataFrame(data["df_os"])
    os_numero = data["os_numero"]
    problem_no = data["num_problema_os"]

    # Gera o gráfico
    fig = os_graficos.gerar_grafico_gantt_historico_problema_detalhamento_os(df_os, os_numero, problem_no)

    return fig


def preenche_dias_sem_eventos(df, data_inicio_problema, data_fim_problema, vec_asset_id, clazz):
    lista_dias_evt = df["travel_date"].astype(str).unique()
    for dia in pd.date_range(data_inicio_problema, data_fim_problema, freq="D"):
        dia_str = dia.strftime("%Y-%m-%d")
        if dia_str not in lista_dias_evt:
            # Adiciona linha com zero
            df_linha = pd.DataFrame(
                {
                    "AssetId": [vec_asset_id],
                    "travel_date": [dia_str],
                    "total_evts": [0],
                    "target_value": [0],
                    "target_label": ["0"],
                    "CLASSE": [clazz],
                }
            )
            df = pd.concat([df, df_linha], ignore_index=True)

    return df


# Preenche o gráfico de eventos com os dados do store
@callback(
    Output("graph-historico-eventos-detalhamento-os", "figure"),
    Input("store-output-dados-detalhamento-os", "data"),
    Input("input-select-data-eventos-mix-detalhamento-os", "value"),
)
def plota_grafico_eventos_retrabalho_os(data, lista_dropdown_eventos_mix):
    # Valida se os dados do estado estão OK, caso contrário retorna os dados padrão
    if not data or not data["sucesso"]:
        return go.Figure()

    # Obtem os dados do estado
    df_os = pd.DataFrame(data["df_os"])
    codigo_veiculo = data["codigo_veiculo"]
    os_numero = data["os_numero"]
    problem_no = data["num_problema_os"]
    vec_asset_id = data["vec_asset_id"]

    # Pega as OS do problema atual
    df_problema_os_alvo = os_service.obtem_os_problema_atual(df_os, problem_no)

    # Pega o início e fim do problema
    data_inicio_problema = df_problema_os_alvo["DATA DA ABERTURA DA OS DT"].min()
    data_fim_problema = df_problema_os_alvo["DATA DO FECHAMENTO DA OS DT"].max()
    data_inicio_problema_str = data_inicio_problema.strftime("%Y-%m-%d %H:%M:%S")
    data_fim_problema_str = data_fim_problema.strftime("%Y-%m-%d %H:%M:%S")

    # Obtem os dados do odômetro e consumo de combustível
    df_odometro = os_service.obtem_odometro_veiculo(vec_asset_id, data_inicio_problema_str, data_fim_problema_str)
    df_consumo = os_service.obtem_consumo_veiculo(vec_asset_id, data_inicio_problema_str, data_fim_problema_str)

    lista_df_evts = [df_odometro, df_consumo]

    # Obtem os demais eventos mix através do input / select
    if lista_dropdown_eventos_mix is not None and len(lista_dropdown_eventos_mix) > 0:
        for evento in lista_dropdown_eventos_mix:
            df_evt_raw = os_service.obtem_historico_evento_veiculo(
                vec_asset_id, evento, data_inicio_problema_str, data_fim_problema_str
            )
            df_evt = preenche_dias_sem_eventos(
                df_evt_raw, data_inicio_problema, data_fim_problema, vec_asset_id, evento
            )

            # Encontra o label descritivo do evento
            label_row = df_eventos_mix_data[df_eventos_mix_data["value"] == evento]
            if not label_row.empty:
                label_evento_str = label_row["label"].values[0]
            else:
                label_evento_str = evento  # fallback

            df_evt["CLASSE"] = label_evento_str
            lista_df_evts.append(df_evt)

    # Gera o gráfico
    fig = os_graficos.gerar_grafico_historico_eventos_detalhamento_os(os_numero, df_problema_os_alvo, lista_df_evts)

    return fig


##############################################################################
# Callback para o mapa #######################################################
##############################################################################


def get_label_com_icone(i, label_str):
    icone = "⬜ "
    if i == 2:
        icone = "🟩 "
    elif i == 3:
        icone = "🟥 "
    elif i == 4:
        icone = "🟪 "

    return icone + label_str


def gera_layer_evento_mix(vec_asset_id, evt, data_inicio_problema_str, data_fim_problema_str, cor_icone):
    lista_marcadores = []
    lista_lat = []
    lista_lon = []

    # Retorne se o evento possui dados e os marcadores (quando houver), bem como a lista de lat e long
    if evt not in df_eventos_mix_gps["value"].unique():
        return False, lista_marcadores, lista_lat, lista_lon

    df_eventos_mix = os_service.obtem_detalhamento_evento_os(
        vec_asset_id, evt, data_inicio_problema_str, data_fim_problema_str
    )

    # Caso não tenha eventos para a data, retorne falso
    if df_eventos_mix.empty:
        return False, lista_marcadores, lista_lat, lista_lon

    for jx, row in df_eventos_mix.iterrows():
        evt_lon = row["StartPosition_Longitude"]
        evt_lat = row["StartPosition_Latitude"]
        evt_driver_name = row["Name"]
        evt_timestamp = pd.to_datetime(row["StartDateTime"]).strftime("%H:%M:%S - %Y-%m-%d")

        # Encontra o label descritivo do evento
        label_row = df_eventos_mix_data[df_eventos_mix_data["value"] == evt]
        label_evento_str = evt
        if not label_row.empty:
            label_evento_str = label_row["label"].values[0]

        marcador = dl.CircleMarker(
            center=[evt_lat, evt_lon],
            radius=10,
            color="black",
            fillColor=cor_icone,
            fillOpacity=0.75,
            children=dl.Popup(
                html.Div(
                    [
                        html.H6(label_evento_str),
                        html.Ul([html.Li(f"Motorista: {evt_driver_name}"), html.Li(f"Hora: {evt_timestamp}")]),
                    ]
                )
            ),
        )

        # Adiciona o marcador e guarda lat e lon para dar zoom
        lista_marcadores.append(marcador)
        lista_lat.append(evt_lat)
        lista_lon.append(evt_lon)

    return True, lista_marcadores, lista_lat, lista_lon


@callback(
    Output("layer-control-eventos-detalhe-os", "children"),
    Output("mapa-eventos-detalhe-os", "bounds"),
    Input("store-output-dados-detalhamento-os", "data"),
    Input("input-select-data-eventos-mix-detalhamento-os", "value"),
    Input("graph-historico-eventos-detalhamento-os", "relayoutData"),
)
def cb_mapa_eventos_mix_retrabalho_os(data, eventos_selecionados, relayoutData):
    # Valida se os dados do estado estão OK, caso contrário retorna os dados padrão
    if not data or not data["sucesso"]:
        return dash.no_update, dash.no_update

    if not eventos_selecionados:
        return dash.no_update, dash.no_update

    # Obtem os dados do estado
    df_os = pd.DataFrame(data["df_os"])
    problem_no = data["num_problema_os"]
    vec_asset_id = data["vec_asset_id"]

    # Pega as OS do problema atual
    df_problema_os_alvo = os_service.obtem_os_problema_atual(df_os, problem_no)

    # Pega o início e fim do problema
    data_inicio_problema = df_problema_os_alvo["DATA DA ABERTURA DA OS DT"].min()
    data_fim_problema = df_problema_os_alvo["DATA DO FECHAMENTO DA OS DT"].max()
    data_inicio_problema_str = data_inicio_problema.strftime("%Y-%m-%d %H:%M:%S")
    data_fim_problema_str = data_fim_problema.strftime("%Y-%m-%d %H:%M:%S")

    # Verifica se houve seleção, caso tenha, atualiza data_inicio e data_fim para os valores selecionados
    if relayoutData and "xaxis.range[0]" in relayoutData and "xaxis.range[1]" in relayoutData:
        data_inicio_problema_str = pd.to_datetime(relayoutData["xaxis.range[0]"]).strftime("%Y-%m-%d %H:%M:%S")
        data_fim_problema_str = pd.to_datetime(relayoutData["xaxis.range[1]"]).strftime("%Y-%m-%d %H:%M:%S")

    # Lista de overlays
    lista_overlays = []
    lista_lat = []
    lista_lon = []

    # Define as cores
    for i, evt in enumerate(eventos_selecionados):
        # i + 2 pq as duas primerias cores ficam com o odômetro e combustível, daí vem as cores dos eventos
        cor_icone = tema.PALETA_CORES_DISCRETA[i + 2 % len(tema.PALETA_CORES_DISCRETA)]

        layer_possui_marcador, layer_lista_marcadores, layer_lista_lat, layer_lista_lon = gera_layer_evento_mix(
            vec_asset_id, evt, data_inicio_problema_str, data_fim_problema_str, cor_icone
        )

        if layer_possui_marcador:
            # Encontra o label descritivo do evento
            label_row = df_eventos_mix_data[df_eventos_mix_data["value"] == evt]
            label_evento_str = evt
            if not label_row.empty:
                label_evento_str = label_row["label"].values[0]

            label_evento_str = get_label_com_icone(i + 2, label_evento_str)

            # Adiciona o overlay
            lista_overlays.append(
                dl.Overlay(dl.LayerGroup(layer_lista_marcadores), name=label_evento_str, checked=True)
            )
            # Salva lat e lon para zoom
            lista_lat.extend(layer_lista_lat)
            lista_lon.extend(layer_lista_lon)

    # Zoom para os marcadores
    # bound south east canto inferior esquerdo
    # bound north east canto superior direito
    bounds = dash.no_update
    if lista_lat and lista_lon and len(lista_lat) > 0:
        bound_south_west = [min(lista_lat), min(lista_lon)]
        bound_north_east = [max(lista_lat), max(lista_lon)]
        bounds = [bound_south_west, bound_north_east]

    return getMapaFundo() + lista_overlays, bounds


##############################################################################
# Layout #####################################################################
##############################################################################


def getMapaFundo():
    if MAPBOX_KEY and MAPBOX_KEY != "":
        return [
            # 🛰️ Satélite
            dl.BaseLayer(
                dl.TileLayer(
                    url=f"https://api.mapbox.com/styles/v1/mapbox/satellite-v9/tiles/{{z}}/{{x}}/{{y}}?access_token={MAPBOX_KEY}",
                    attribution="© Mapbox, © OpenStreetMap",
                    tileSize=512,
                    zoomOffset=-1,
                ),
                name="Satélite",
                checked=False,
            ),
            # 🛰️ + 🗺️ Híbrido
            dl.BaseLayer(
                dl.TileLayer(
                    url=f"https://api.mapbox.com/styles/v1/mapbox/satellite-streets-v12/tiles/{{z}}/{{x}}/{{y}}?access_token={MAPBOX_KEY}",
                    attribution="© Mapbox, © OpenStreetMap",
                    tileSize=512,
                    zoomOffset=-1,
                ),
                name="Híbrido",
                checked=False,
            ),
            # 🛣️ Ruas
            dl.BaseLayer(
                dl.TileLayer(
                    url=f"https://api.mapbox.com/styles/v1/mapbox/streets-v12/tiles/{{z}}/{{x}}/{{y}}?access_token={MAPBOX_KEY}",
                    attribution="© Mapbox, © OpenStreetMap",
                    tileSize=512,
                    zoomOffset=-1,
                ),
                name="Ruas",
                checked=True,
            ),
        ]
    else:
        return [
            # OpenStreetMap (ruas padrão)
            dl.BaseLayer(
                dl.TileLayer(url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"),
                name="OpenStreetMap",
                checked=False,
            ),
            # ESRI Satellite (sem nomes de rua)
            dl.BaseLayer(
                dl.TileLayer(
                    url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                    attribution="Tiles © Esri",
                ),
                name="ESRI Satellite",
                checked=True,
            ),
        ]


layout = dbc.Container(
    [
        # Estado
        dcc.Store(id="store-input-dados-detalhamento-os"),
        dcc.Store(id="store-output-dados-detalhamento-os"),
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="fluent-mdl2:repair", width=45), width="auto"),
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
                                    dmc.Space(h=5),
                                    dbc.FormText(
                                        html.Em(
                                            "OS não encontrada",
                                            id="input-detalhamento-os-selecionada-error",
                                        ),
                                        color="secondary",
                                    ),
                                ],
                                className="dash-bootstrap",
                            ),
                        ],
                        id="card-input-detalhamento-os-selecionada",
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
                                    dmc.Space(h=5),
                                    dbc.FormText(
                                        html.Em(
                                            "Período inválido",
                                            id="input-detalhamento-select-dias-os-retrabalho-error",
                                        ),
                                        color="secondary",
                                    ),
                                ],
                                className="dash-bootstrap",
                            ),
                        ],
                        id="card-input-detalhamento-select-dias-os-retrabalho",
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
                                "Histórico do problema selecionado ",
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
        dmc.Space(h=40),
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
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="oui:inspect", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Detalhamento de eventos ao longo da OS e do problema selecionado ",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            gera_labels_inputs_detalhamento_os("detalhe-grafico-eventos-os"),
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
                                    dbc.Label("Eventos da Mix (até 3 eventos)"),
                                    dcc.Dropdown(
                                        id="input-select-data-eventos-mix-detalhamento-os",
                                        options=[
                                            {"label": evt["label"], "value": evt["value"]}
                                            for evt in lista_todos_eventos_com_data
                                        ],
                                        multi=True,
                                        value=[
                                            "ra_uso_indevido_do_pedal_de_acelerador_85",
                                            "ra_acelerando_parado",
                                        ],
                                        placeholder="Selecione um ou mais eventos...",
                                    ),
                                    dbc.FormText(
                                        html.Em("⚠️ Máximo de 3 eventos permitidos"),
                                        color="secondary",
                                        id="input-select-data-eventos-mix-detalhamento-os-error",
                                        style={"display": "none"},
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
        dcc.Graph(id="graph-historico-eventos-detalhamento-os"),
        dmc.Space(h=20),
        dl.Map(
            children=dl.LayersControl(getMapaFundo(), id="layer-control-eventos-detalhe-os", collapsed=False),
            id="mapa-eventos-detalhe-os",
            bounds=None,
            center=(-16.665136, -49.286041),
            zoom=11,
            style={
                "height": "60vh",
                "border": "2px solid gray", 
                "borderRadius": "6px",
            },
        ),
        dmc.Space(h=80),
    ]
)

##############################################################################
# Registro da página #########################################################
##############################################################################
dash.register_page(__name__, name="OS", path="/retrabalho-por-os", icon="fluent-mdl2:repair")
