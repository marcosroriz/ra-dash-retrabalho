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
from modules.entities_utils import get_regras_monitoramento_os, get_mecanicos, get_lista_os, get_oficinas, get_secoes, get_modelos, gerar_excel

# Imports específicos
from modules.crud_regra.crud_regra_service import CRUDRegraService

import modules.crud_regra.graficos as crud_regra_graficos
import modules.crud_regra.tabelas as crud_regra_tabelas

##############################################################################
# LEITURA DE DADOS ###########################################################
##############################################################################
# Conexão com os bancos
pgDB = PostgresSingleton.get_instance()
pgEngine = pgDB.get_engine()

# Cria o serviço
crud_regra_service = CRUDRegraService(pgEngine)

# Obtem a lista de regras de monitoramento de OS
df_regras_monitoramento_os = get_regras_monitoramento_os(pgEngine)
lista_regras_monitoramento_os = df_regras_monitoramento_os.to_dict(orient="records")

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
    Output("relatorio-input-select-regra-retrabalho", "value"),
    Output("relatorio-input-data-relatorio-regra-retrabalho", "value"),
    Input("url", "href"),
)
def callback_receber_campos_via_url_relatorio_regra(href):
    if not href:
        raise dash.exceptions.PreventUpdate

    # Faz o parse dos parâmetros da url
    parsed_url = urlparse(href)
    query_params = parse_qs(parsed_url.query)

    id_regra = safe_int(query_params.get("id_regra", [None])[0])
    data_relatorio = query_params.get("data_relatorio", [None])[0]

    # Verifica se a regra existe
    lista_id_regras = [regra["value"] for regra in lista_regras_monitoramento_os]
    if id_regra is not None and id_regra not in lista_id_regras:
        id_regra = None
        data_relatorio = None

    if id_regra is not None and data_relatorio is None:
        df_ultima_data_regra = crud_regra_service.get_ultima_data_regra(id_regra)
        if not df_ultima_data_regra.empty:
            data_relatorio = df_ultima_data_regra["ultimo_dia"].iloc[0]

    return id_regra, data_relatorio


# Sincroniza o store com os valores dos inputs
@callback(
    [
        Output("store-relatorio-relatorio-regra", "data"),
        Output("relatorio-card-input-select-regra-retrabalho", "style"),
        Output("relatorio-card-input-data-relatorio-regra-retrabalho", "style"),
        Output("relatorio-input-select-regra-retrabalho-error", "style"),
        Output("relatorio-input-data-relatorio-regra-retrabalho-error", "style"),
    ],
    Input("relatorio-input-select-regra-retrabalho", "value"),
    Input("relatorio-input-data-relatorio-regra-retrabalho", "value"),
    running=[(Output("loading-overlay-guia-relatorio-regra", "visible"), True, False)],
)
def callback_sincroniza_input_store_relatorio_regra(id_regra, dia_execucao):
    # Flags para validação
    input_regra_valido = True
    input_data_valido = True

    # Store padrão
    store_payload = { "valido": False }

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
    if dia_execucao and crud_regra_service.existe_execucao_regra_no_dia(id_regra, dia_execucao):
        style_borda_input_data = style_borda_ok
        style_campo_erro_input_data = style_campo_erro_oculto
    else:
        input_data_valido = False

    if input_regra_valido and input_data_valido:
        # Pega os campos da regra
        df_regra = crud_regra_service.get_regra_by_id(id_regra)
        dados_regra = df_regra.to_dict(orient="records")[0]

        id_regra = dados_regra["id"]
        nome_regra = dados_regra["nome"]
        min_dias_retrabalho = dados_regra["min_dias_retrabalho"]

        # Pega o resultado da regra
        df_resultado_regra = crud_regra_service.get_resultado_regra(id_regra, dia_execucao)
        
        # Adiciona min_dias para facilitar o clique no botão para detalhamento de OS
        df_resultado_regra["min_dias_retrabalho"] = min_dias_retrabalho

        # Ação de visualização
        df_resultado_regra["acao"] = "🔍 Detalhar"

        # Atualiza o store
        store_payload = {
            "valido": input_regra_valido and input_data_valido and not df_resultado_regra.empty,
            "id_regra": id_regra,
            "nome_regra": nome_regra,
            "min_dias_retrabalho": min_dias_retrabalho,
            "df_resultado_regra": df_resultado_regra.to_dict(orient="records"),
            "dados_regra": dados_regra,
        }

    return store_payload, style_borda_input_regra, style_borda_input_data, style_campo_erro_input_regra, style_campo_erro_input_data

##############################################################################
# Callbacks para os indicadores ##############################################
##############################################################################


@callback(
    [
        Output("card-regra-nome", "children"),
        Output("card-regra-periodo-monitoramento", "children"),
        Output("card-regra-min-dias-retrabalho", "children"),
        Output("card-regra-modelos", "children"),
        Output("card-regra-secoes", "children"),
        Output("card-regra-oficinas", "children"),
        Output("card-regra-os", "children"),
        Output("card-regra-alvos-alerta", "children"),
        Output("card-regra-horario-envio", "children"),
        Output("card-regra-alvos-email", "children"),
        Output("card-regra-alvos-whatsapp", "children"),
    ],
    Input("store-relatorio-relatorio-regra", "data"),
)
def atualiza_dados_card_descricao_regra_relatorio(store_relatorio_regra):
    # Valida se os dados do estado estão OK, caso contrário retorna os dados padrão
    if not store_relatorio_regra or not store_relatorio_regra["valido"]:
        return [
            "🔍 Nome da regra: Não Informado",
            "🕒 Período de monitoramento: Não Informado",
            "🔄 Mínimo de dias de retrabalho: Não Informado",
            "🚗 Modelos: Não Informado",
            "🛠️ Seções: Não Informado",
            "🏢 Oficinas: Não Informado",
            "🚨 OSs: Não Informado",
            "🔔 Alvos de alerta: Não Informado",
            "🕒 Horário de disparo: Não Informado",
            "📧 Alvos de email: Não Informado",
            "📱 Alvos de WhatsApp: Não Informado",
        ]

    # Obtem os dados da regra
    dados_regra = store_relatorio_regra["dados_regra"]

    html_nome_regra = f"🔍 Nome da regra: {dados_regra['nome']}"
    html_periodo_monitoramento = f"🕒 Período de monitoramento: {dados_regra['data_periodo_regra']}"
    html_min_dias_retrabalho = f"🔄 Mínimo de dias de retrabalho: {dados_regra['min_dias_retrabalho']}"
    # html_modelos = html.Div([html.Span("🚗 Modelos:"), html.Ul([html.Li(m) for m in dados_regra["modelos_veiculos"]])])
    html_modelos = "🚗 Modelos: " + ", ".join(dados_regra["modelos_veiculos"])
    # html_oficinas = html.Div([html.Span("🏢 Oficinas:"), html.Ul([html.Li(o) for o in dados_regra["oficinas"]])])
    html_oficinas = "🏢 Oficinas: " + ", ".join(dados_regra["oficinas"])
    # html_secoes = html.Div([html.Span("🛠️ Seções:"), html.Ul([html.Li(s) for s in dados_regra["secoes"]])])
    html_secoes = "🛠️ Seções: " + ", ".join(dados_regra["secoes"])
    # html_os = html.Div([html.Span("🚨 OSs:"), html.Ul([html.Li(o) for o in dados_regra["os"]])])
    html_os = "🚨 OSs: " + ", ".join(dados_regra["os"])

    alvos_alerta = [
        "✅ Nova OS COM retrabalho" if dados_regra["target_nova_os_com_retrabalho_previo"] else "❌ Nova OS COM retrabalho",
        "✅ Nova OS SEM retrabalho" if dados_regra["target_nova_os_sem_retrabalho_previo"] else "❌ Nova OS SEM retrabalho",
        "✅ Retrabalho" if dados_regra["target_retrabalho"] else "❌ Retrabalho",
    ]
    html_alvos_alerta = html.Div([html.Span("🔔 Alvos de alerta:"), html.Ul([html.Li(a) for a in alvos_alerta])])
    
    html_horario_disparo = f"🕒 Horário de disparo: {dados_regra['hora_disparar']}"

    html_email = "📧 Alvos de email: Não Informado"
    if dados_regra["target_email"]:
        email_destinos = []
        email_destinos.append(dados_regra["target_email_dest1"])
        email_destinos.append(dados_regra["target_email_dest2"])
        email_destinos.append(dados_regra["target_email_dest3"])
        email_destinos.append(dados_regra["target_email_dest4"])
        email_destinos.append(dados_regra["target_email_dest5"])
    
        html_email = html.Div([html.Span("📧 Alvos de email:"), html.Ul([html.Li(e) for e in email_destinos if e])])

    html_whatsapp = "📱 Alvos de WhatsApp: Não Informado"
    if dados_regra["target_wpp"]:
        wpp_destinos = []
        wpp_destinos.append(dados_regra["target_wpp_dest1"])
        wpp_destinos.append(dados_regra["target_wpp_dest2"])
        wpp_destinos.append(dados_regra["target_wpp_dest3"])
        wpp_destinos.append(dados_regra["target_wpp_dest4"])
        wpp_destinos.append(dados_regra["target_wpp_dest5"])
        
        html_whatsapp = html.Div([html.Span("📱 Alvos de WhatsApp:"), html.Ul([html.Li(w) for w in wpp_destinos if w])])

    return [
        html_nome_regra,
        html_periodo_monitoramento,
        html_min_dias_retrabalho,
        html_modelos,
        html_oficinas,
        html_secoes,
        html_os,
        html_alvos_alerta,
        html_horario_disparo,
        html_email,
        html_whatsapp,
    ]



@callback(
    [
        Output("card-relatorio-resultado-total-os-detectadas", "children"),
        Output("card-relatorio-resultado-total-problemas-detectados", "children"),
        Output("card-relatorio-resultado-hora-execucao-regra", "children"),
        Output("card-relatorio-resultado-modelos", "children"),
        Output("card-relatorio-resultado-secoes", "children"),
        Output("card-relatorio-resultado-oficinas", "children"),
        # Output("card-relatorio-resultado-os", "children"),
    ],
    Input("store-relatorio-relatorio-regra", "data"),
)
def atualiza_dados_card_resultado_regra_relatorio(store_relatorio_regra):
    # Valida se os dados do estado estão OK, caso contrário retorna os dados padrão
    if not store_relatorio_regra or not store_relatorio_regra["valido"]:
        return [
            "⚡ Total de OSs detectadas: Não Informado",
            "💣 Total de problemas detectados: Não Informado",
            "🕒 Horário de execução: Não Informado",
            "🚗 Modelos: Não Informado",
            "🛠️ Seções: Não Informado",
            "🏢 Oficinas: Não Informado",
            # "🚨 OSs: Não Informado",
        ]

    # Obtem o resultado da regra
    df_resultado_regra = pd.DataFrame(store_relatorio_regra["df_resultado_regra"])

    # Obtem os dados do dataframe
    total_os_detectadas = df_resultado_regra["os_num"].nunique()
    html_total_os_detectadas = html.Div([html.Span("⚡ Total de OSs detectadas: "), html.Strong(total_os_detectadas)])

    total_problemas = df_resultado_regra["DESCRICAO DO SERVICO"].nunique()
    html_total_problemas = html.Div([html.Span("💣 Total de problemas detectados: "), html.Strong(total_problemas)])

    data_execucao = pd.to_datetime(df_resultado_regra["executed_at"].max()).strftime("%d/%m/%Y %H:%M")
    html_hora_execucao = html.Div([html.Span("🕒 Horário de execução: "), html.Strong(data_execucao)])

    df_modelos = df_resultado_regra.groupby("DESCRICAO DO MODELO").size().reset_index(name="total")
    df_modelos["PERC_TOTAL_OS"] = (df_modelos["total"] / df_modelos["total"].sum()) * 100
    html_modelos = html.Div([html.Span("🚗 Modelos:"), html.Ul([html.Li(f"{m} = {t} ({p:.1f}%)") for m, t, p in zip(df_modelos["DESCRICAO DO MODELO"], df_modelos["total"], df_modelos["PERC_TOTAL_OS"])])])

    df_secoes = df_resultado_regra.groupby("DESCRICAO DA SECAO").size().reset_index(name="total")
    df_secoes["PERC_TOTAL_OS"] = (df_secoes["total"] / df_secoes["total"].sum()) * 100
    html_secoes = html.Div([html.Span("🛠️ Seções:"), html.Ul([html.Li(f"{s} = {t} ({p:.1f}%)") for s, t, p in zip(df_secoes["DESCRICAO DA SECAO"], df_secoes["total"], df_secoes["PERC_TOTAL_OS"])])])

    df_oficinas = df_resultado_regra.groupby("DESCRICAO DA OFICINA").size().reset_index(name="total")
    df_oficinas["PERC_TOTAL_OS"] = (df_oficinas["total"] / df_oficinas["total"].sum()) * 100
    html_oficinas = html.Div([html.Span("🏢 Oficinas:"), html.Ul([html.Li(f"{o} = {t} ({p:.1f}%)") for o, t, p in zip(df_oficinas["DESCRICAO DA OFICINA"], df_oficinas["total"], df_oficinas["PERC_TOTAL_OS"])])])

    # df_os = df_resultado_regra.groupby("DESCRICAO DO SERVICO").size().reset_index(name="total")
    # html_os = html.Div([html.Span("🚨 OSs:"), html.Ul([html.Li(f"{o} = {t}") for o, t in zip(df_os["DESCRICAO DO SERVICO"], df_os["total"])])])

    return [
        html_total_os_detectadas,
        html_total_problemas,
        html_hora_execucao,
        html_modelos,
        html_secoes,
        html_oficinas,
        # html_os,
    ]

##############################################################################
# Callbacks para a tabela ####################################################
##############################################################################

@callback(
    Output("tabela-relatorio-regra", "rowData"),
    Input("store-relatorio-relatorio-regra", "data"),
)
def tabela_relatorio_regra(store_relatorio_regra):
    # Valida input
    if store_relatorio_regra and store_relatorio_regra["valido"]:
        df = pd.DataFrame(store_relatorio_regra["df_resultado_regra"])

        # Datas aberturas (converte para DT) 
        df["DATA DA ABERTURA DA OS DT"] = pd.to_datetime(df["DATA DA ABERTURA DA OS"])
        df["DATA DO FECHAMENTO DA OS DT"] = pd.to_datetime(df["DATA DO FECHAMENTO DA OS"])

        return df.to_dict(orient="records")
    else:
        return []
    

##############################################################################
# Callbacks para o botão de detalhamento #####################################
##############################################################################

@callback(
    Output("url", "href", allow_duplicate=True),
    Input("tabela-relatorio-regra", "cellRendererData"),
    Input("tabela-relatorio-regra", "virtualRowData"),
    Input("store-relatorio-relatorio-regra", "data"),
    prevent_initial_call=True,
)
def callback_botao_relatorio_detalhamento_regra(
    linha, linha_virtual, store_relatorio_regra
):
    ctx = callback_context  # Obtém o contexto do callback
    if not ctx.triggered:
        return dash.no_update  # Evita execução desnecessária

    # Verifica se o callback foi acionado pelo botão de visualização
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[1]

    if triggered_id != "cellRendererData":
        return dash.no_update
    
    # Valida inputs (tabela e store)
    if linha is None or linha_virtual is None:
        return dash.no_update

    if not store_relatorio_regra or not store_relatorio_regra["valido"]:
        return dash.no_update
    
    # Pega a linha alvo
    linha_alvo = linha_virtual[linha["rowIndex"]]
    os_num = linha_alvo["os_num"]
    min_dias_retrabalho = store_relatorio_regra["min_dias_retrabalho"]

    url_params = [
        f"os={os_num}",
        f"mindiasretrabalho={min_dias_retrabalho}",
    ]
    url_params_str = "&".join(url_params)

    return f"/retrabalho-por-os?{url_params_str}"

##############################################################################
# Callbacks para o gráfico #####################################################
##############################################################################
@callback(
    Output("graph-relatorio-regra-por-servico", "figure"),
    Input("store-relatorio-relatorio-regra", "data"),
    Input("store-window-size", "data"),
)
def graph_relatorio_regra_por_servico(store_relatorio_regra, metadata_browser):
    if store_relatorio_regra and store_relatorio_regra["valido"]:
        df = pd.DataFrame(store_relatorio_regra["df_resultado_regra"])
        
        # Agrega por problema
        df_agg = df.groupby("DESCRICAO DO SERVICO").size().reset_index(name="count").sort_values(by="count", ascending=False)

        # Calcula o percentual de cada problema
        df_agg["PERC_TOTAL_OS"] = (df_agg["count"] / df_agg["count"].sum()) * 100

        # Top 10
        df_agg_top_10 = df_agg.head(10)

        # Soma do restante
        total_outros = df_agg.iloc[10:]["count"].sum()

        # Cria linha "Outros"
        df_demais_problemas = pd.DataFrame({
            "DESCRICAO DO SERVICO": ["Outros"],
            "count": [total_outros],
            "PERC_TOTAL_OS": (total_outros / df_agg["count"].sum()) * 100
        })

        # Junta
        df_agg_top_10 = pd.concat([df_agg_top_10, df_demais_problemas], ignore_index=True)

        return crud_regra_graficos.gerar_grafico_top_10_problemas_relatorio_regras(df_agg_top_10, metadata_browser)
    else:
        return go.Figure()




##############################################################################
# Layout #####################################################################
##############################################################################
layout = dbc.Container(
    [
        # Estado
        dcc.Store(id="store-relatorio-relatorio-regra"),
        # Loading
        dmc.LoadingOverlay(
            # visible=True,
            id="loading-overlay-guia-relatorio-regra",
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
        # Modais
        dmc.Modal(
            id="relatorio-modal-carregar-dados-relatorio-regra",
            centered=True,
            radius="lg",
            size="md",
            closeOnClickOutside=False,
            closeOnEscape=False,
            children=dmc.Stack(
                [
                    dmc.ThemeIcon(
                        radius="lg",
                        size=128,
                        color="red",
                        variant="light",
                        children=DashIconify(icon="material-symbols:error-rounded", width=128, height=128),
                    ),
                    dmc.Title("Erro ao carregar dados!", order=1),
                    dmc.Text("Ocorreu um erro ao carregar os dados da regra."),
                    dmc.Group(
                        [
                            dmc.Button(
                                "Fechar",
                                color="red",
                                variant="outline",
                                id="btn-close-relatorio-modal-carregar-dados-relatorio-regra",
                            ),
                        ],
                    ),
                    dmc.Space(h=20),
                ],
                align="center",
                gap="md",
            ),
        ),
        dmc.Modal(
            id="relatorio-modal-teste-relatorio-regra",
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
                                id="btn-close-relatorio-modal-teste-relatorio-regra",
                            ),
                        ],
                    ),
                ],
                align="center",
                gap="md",
            ),
        ),
        dmc.Modal(
            id="relatorio-modal-teste-relatorio-regra",
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
                                id="btn-close-relatorio-modal-teste-relatorio-regra",
                            ),
                        ],
                    ),
                ],
                align="center",
                gap="md",
            ),
        ),
        dmc.Modal(
            id="relatorio-modal-atualizar-relatorio-regra",
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
                    dmc.Text("Ocorreu um erro ao salvar a regra. Verifique se a regra possui:"),
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
                                id="btn-close-relatorio-modal-atualizar-relatorio-regra",
                            ),
                        ],
                    ),
                ],
                align="center",
                gap="md",
            ),
        ),
        dmc.Modal(
            id="relatorio-modal-atualizar-relatorio-regra",
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
                    dmc.Text("A regra foi salva com sucesso."),
                    dmc.Group(
                        [
                            dmc.Button(
                                "Fechar",
                                color="green",
                                variant="outline",
                                id="btn-close-relatorio-modal-atualizar-relatorio-regra",
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
        # Título Desktop
        dmc.Box(
            dbc.Row(
                [
                    dbc.Col(DashIconify(icon="carbon:rule-data-quality", width=45), width="auto"),
                    dbc.Col(
                        html.H1(
                            [
                                "Relatório da \u00a0",
                                html.Strong("regra"),
                                "\u00a0 de monitoramento do retrabalho",
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
                            "Relatório da regra",
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
                                dbc.Label("Nome da Regra de Monitoramento"),
                                dcc.Dropdown(
                                    id="relatorio-input-select-regra-retrabalho",
                                    options=[regra for regra in lista_regras_monitoramento_os],
                                    placeholder="Selecione uma regra...",
                                ),
                                dmc.Space(h=5),
                                dbc.FormText(
                                    html.Em(
                                        "Regra não encontrada",
                                        id="relatorio-input-select-regra-retrabalho-error",
                                    ),
                                    color="secondary",
                                ),
                            ],
                            className="dash-bootstrap",
                        ),
                        id="relatorio-card-input-select-regra-retrabalho",
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
                                    id="relatorio-input-data-relatorio-regra-retrabalho",
                                    minDate=date(2020, 8, 5),
                                    valueFormat="DD/MM/YYYY",
                                    value=(datetime.now() - timedelta(days=10)).date()

                                ),
                                dmc.Space(h=5),
                                dbc.FormText(
                                    html.Em(
                                        "Período inválido",
                                        id="relatorio-input-data-relatorio-regra-retrabalho-error",
                                    ),
                                    color="secondary",
                                ),
                            ],
                            className="dash-bootstrap",
                        ),
                        id="relatorio-card-input-data-relatorio-regra-retrabalho",
                        body=True,
                    ),
                    md=6,
                    className="mb-3 mb-md-0",
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
                                                    "Resumo da Regra",
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
                                            dbc.ListGroupItem("", id="card-regra-nome", active=True),
                                            dbc.ListGroupItem("", id="card-regra-periodo-monitoramento"),
                                            dbc.ListGroupItem("", id="card-regra-min-dias-retrabalho"),
                                            dbc.ListGroupItem("", id="card-regra-modelos"),
                                            dbc.ListGroupItem("", id="card-regra-secoes"),
                                            dbc.ListGroupItem("", id="card-regra-oficinas"),
                                            dbc.ListGroupItem("", id="card-regra-os"),
                                            dbc.ListGroupItem("", id="card-regra-alvos-alerta"),
                                            dbc.ListGroupItem("", id="card-regra-horario-envio"),
                                            dbc.ListGroupItem("", id="card-regra-alvos-email"),
                                            dbc.ListGroupItem("", id="card-regra-alvos-whatsapp"),
                                        ],
                                        className="m-0",
                                    ),
                                ],
                                className="m-0",
                            ),
                        ],
                        className="m-0 m-md-1",  # margem só no desktop
                    ),
                    md=6,
                    className="mb-3 mb-md-0",
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
                                                    "Resumo do relatório",
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
                                            dbc.ListGroupItem("", id="card-relatorio-resultado-total-os-detectadas", active=True),
                                            dbc.ListGroupItem("", id="card-relatorio-resultado-total-problemas-detectados"),
                                            dbc.ListGroupItem("", id="card-relatorio-resultado-hora-execucao-regra"),
                                            dbc.ListGroupItem("", id="card-relatorio-resultado-modelos"),
                                            dbc.ListGroupItem("", id="card-relatorio-resultado-secoes"),
                                            dbc.ListGroupItem("", id="card-relatorio-resultado-oficinas"),
                                            # dbc.ListGroupItem("", id="card-relatorio-resultado-os"),
                                        ],
                                        className="m-0",
                                    ),
                                ],
                                className="m-0",
                            ),
                        ],
                        className="m-0 m-md-1",  # margem só no desktop
                    ),
                    md=6,
                    className="mb-3 mb-md-0",
                ),
            ],
        ),
        dmc.Space(h=40),
        # Gráfico da Regra por Serviço
        dmc.Space(h=30),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="mdi:fleet", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Top 10 problemas detectados pela regra",
                                className="align-self-center",
                            ),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        dcc.Graph(id="graph-relatorio-regra-por-servico"),
        dmc.Space(h=40),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="mdi:car-search-outline", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "OSs detectadas pela regra",
                                className="align-self-center",
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
            id="tabela-relatorio-regra",
            columnDefs=crud_regra_tabelas.tbl_detalhamento_relatorio_regra,
            rowData=[],
            defaultColDef={"filter": True, "floatingFilter": True},
            columnSize="autoSize",
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
dash.register_page(__name__, name="Relatório de Regra", path="/regra-relatorio", icon="carbon:rule-data-quality", hide_page=True)
