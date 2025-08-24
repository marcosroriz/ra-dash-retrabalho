#!/usr/bin/env python
# coding: utf-8

# Tela para editar uma regra para detecção de retrabalho

##############################################################################
# IMPORTS ####################################################################
##############################################################################
# Bibliotecas básicas
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
from modules.entities_utils import get_mecanicos, get_lista_os, get_oficinas, get_secoes, get_modelos, gerar_excel

# Imports específicos
from modules.crud_regra.crud_regra_service import CRUDRegraService
from modules.crud_regra.crud_email_test import CRUDEmailTestService
from modules.crud_regra.crud_wpp_test import CRUDWppTestService

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

@callback(
    [
        Output("store-input-id-editar-regra", "data"),
        Output("modal-erro-carregar-dados-editar-regra", "opened"),
        Output("input-nome-regra-monitoramento-retrabalho", "value"),
        Output("input-periodo-dias-monitoramento-regra-editar-retrabalho", "value"),
        Output("input-select-dias-regra-editar-retrabalho", "value"),
        Output("input-select-modelo-veiculos-regra-editar-retrabalho", "value"),
        Output("input-select-oficina-regra-editar-retrabalho", "value"),
        Output("input-select-secao-regra-editar-retrabalho", "value"),
        Output("input-select-ordens-servico-regra-editar-retrabalho", "value"),
        Output("checklist-alertar-alvo-regra-editar-retrabalho", "value"),
        Output("switch-enviar-email-regra-editar-retrabalho", "checked"),
        Output("input-email-1-regra-editar-retrabalho", "value"),
        Output("input-email-2-regra-editar-retrabalho", "value"),
        Output("input-email-3-regra-editar-retrabalho", "value"),
        Output("input-email-4-regra-editar-retrabalho", "value"),
        Output("input-email-5-regra-editar-retrabalho", "value"),
        Output("switch-enviar-wpp-regra-editar-retrabalho", "checked"),
        Output("input-wpp-1-regra-editar-retrabalho", "value"),
        Output("input-wpp-2-regra-editar-retrabalho", "value"),
        Output("input-wpp-3-regra-editar-retrabalho", "value"),
        Output("input-wpp-4-regra-editar-retrabalho", "value"),
        Output("input-wpp-5-regra-editar-retrabalho", "value"),
        Output("horario-envio-regra-editar-retrabalho", "value"),
    ],
    Input("url", "href"),
    running=[(Output("loading-overlay-guia-editar-regra", "visible"), True, False)],
)
def callback_receber_campos_via_url_editar_regra(href):
    # Store da regra padrao
    store_id_regra = {"id_regra": -1, "valido": False}
    # Resposta padrão
    resposta_padrao = [store_id_regra, True] + [dash.no_update] * 21

    if not href:
        return resposta_padrao

    # Faz o parse dos parâmetros da url
    parsed_url = urlparse(href)
    query_params = parse_qs(parsed_url.query)

    id_regra = query_params.get("id_regra", [0])[0]

    # Verifica se o id da regra é válido
    if id_regra is None or id_regra == 0:
        return resposta_padrao

    # Pega os dados da regra
    df_regra = crud_regra_service.get_regra_by_id(id_regra)

    if df_regra.empty:
        return resposta_padrao

    # Store da regra (define como valido)
    store_id_regra = {"id_regra": id_regra, "valido": True}

    # Pega os dados da regra
    dados_regra = df_regra.to_dict(orient="records")[0]

    id_regra = dados_regra["id"]
    nome_regra = dados_regra["nome"]
    data_periodo_regra = dados_regra["data_periodo_regra"]
    min_dias_retrabalho = dados_regra["min_dias_retrabalho"]
    lista_modelos = dados_regra["modelos_veiculos"]
    lista_oficinas = dados_regra["oficinas"]
    lista_secoes = dados_regra["secoes"]
    lista_os = dados_regra["os"]
    alerta_alvo = []

    if dados_regra["target_nova_os_sem_retrabalho_previo"]:
        alerta_alvo.append("nova_os_sem_retrabalho_anterior")

    if dados_regra["target_nova_os_com_retrabalho_previo"]:
        alerta_alvo.append("nova_os_com_retrabalho_anterior")

    if dados_regra["target_retrabalho"]:
        alerta_alvo.append("retrabalho")

    email_ativo = dados_regra["target_email"]
    email_dest_1 = dados_regra["target_email_dest1"]
    email_dest_2 = dados_regra["target_email_dest2"]
    email_dest_3 = dados_regra["target_email_dest3"]
    email_dest_4 = dados_regra["target_email_dest4"]
    email_dest_5 = dados_regra["target_email_dest5"]

    wpp_ativo = dados_regra["target_wpp"]
    wpp_dest_1 = dados_regra["target_wpp_dest1"]
    wpp_dest_2 = dados_regra["target_wpp_dest2"]
    wpp_dest_3 = dados_regra["target_wpp_dest3"]
    wpp_dest_4 = dados_regra["target_wpp_dest4"]
    wpp_dest_5 = dados_regra["target_wpp_dest5"]

    hora_disparar = dados_regra["hora_disparar"].strftime("%H:%M")

    resposta = [
        # Store com o id da regra para podermos atualizar depois
        store_id_regra,
        # Não mostra modal de erro
        False,
        # Dados da regra / que vão para os inputs
        nome_regra,
        data_periodo_regra,
        min_dias_retrabalho,
        lista_modelos,
        lista_oficinas,
        lista_secoes,
        lista_os,
        alerta_alvo,
        email_ativo,
        email_dest_1,
        email_dest_2,
        email_dest_3,
        email_dest_4,
        email_dest_5,
        wpp_ativo,
        wpp_dest_1,
        wpp_dest_2,
        wpp_dest_3,
        wpp_dest_4,
        wpp_dest_5,
        hora_disparar,
    ]

    print(resposta)
    return resposta


@callback(
    Output("url", "href", allow_duplicate=True),
    Input("btn-close-modal-erro-carregar-dados-editar-regra", "n_clicks"),
    prevent_initial_call=True,
)
def cb_botao_close_modal_erro_carregar_dados_editar_regra(n_clicks):
    if n_clicks is None or n_clicks == 0:
        return dash.no_update
    
    return "/regra-gerenciar"


##############################################################################
# Callbacks para os inputs ###################################################
##############################################################################


# Função para validar o input
def input_valido_editar_regra(data_periodo_regra, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os):
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


time_pattern = re.compile(r"^(?:[01]?\d|2[0-3]):[0-5]\d$")


def horario_valido_editar_regra(horario_envio):
    if not horario_envio:
        return False

    if not time_pattern.match(horario_envio):
        return False

    return True


def target_os_valido_editar_regra(checklist):
    if not checklist:
        return False

    if (
        "nova_os_sem_retrabalho_anterior" in checklist
        or "nova_os_com_retrabalho_anterior" in checklist
        or "retrabalho" in checklist
    ):
        return True

    return False


# Corrige o input para garantir que o termo para todas ("TODAS") não seja selecionado junto com outras opções
def corrige_input_editar_regra(lista, termo_all="TODAS"):
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
    Output("input-select-modelo-veiculos-regra-editar-retrabalho", "value", allow_duplicate=True),
    Input("input-select-modelo-veiculos-regra-editar-retrabalho", "value"),
    prevent_initial_call=True,
)
def corrige_input_modelos_editar_regra(lista_modelos):
    return corrige_input_editar_regra(lista_modelos, "TODOS")


@callback(
    Output("input-select-oficina-regra-editar-retrabalho", "value", allow_duplicate=True),
    Input("input-select-oficina-regra-editar-retrabalho", "value"),
    prevent_initial_call=True,
)
def corrige_input_oficina_editar_regra(lista_oficinas):
    return corrige_input_editar_regra(lista_oficinas)


@callback(
    Output("input-select-secao-regra-editar-retrabalho", "value", allow_duplicate=True),
    Input("input-select-secao-regra-editar-retrabalho", "value"),
    prevent_initial_call=True,
)
def corrige_input_secao_editar_regra(lista_secaos):
    return corrige_input_editar_regra(lista_secaos)


@callback(
    [
        Output("input-select-ordens-servico-regra-editar-retrabalho", "options"),
        Output("input-select-ordens-servico-regra-editar-retrabalho", "value", allow_duplicate=True),
    ],
    [
        Input("input-select-ordens-servico-regra-editar-retrabalho", "value"),
        Input("input-select-secao-regra-editar-retrabalho", "value"),
    ],
    prevent_initial_call=True,
)
def corrige_input_ordem_servico_editar_regra(lista_os, lista_secaos):
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

    return lista_options, corrige_input_editar_regra(lista_os)


# Função para mostrar o input de email de destino
@callback(
    Output("input-email-destino-container-regra-editar-retrabalho", "style"),
    Input("switch-enviar-email-regra-editar-retrabalho", "checked"),
)
def mostra_input_email_destino_editar_regra(email_ativo):
    if email_ativo:
        return {"display": "block"}
    else:
        return {"display": "none"}


# Função para mostrar o input de WhatsApp de destino
@callback(
    Output("input-wpp-destino-container-regra-editar-retrabalho", "style"),
    Input("switch-enviar-wpp-regra-editar-retrabalho", "checked"),
)
def mostra_input_wpp_destino_editar_regra(wpp_ativo):
    if wpp_ativo:
        return {"display": "block"}
    else:
        return {"display": "none"}


# Função para validar o input de email de destino
def verifica_erro_email_editar_regra(email_destino):
    if not email_destino:
        return False

    email_limpo = email_destino.strip()

    if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$", email_limpo):
        return True

    return False


@callback(
    Output("input-email-1-regra-editar-retrabalho", "error"),
    Input("input-email-1-regra-editar-retrabalho", "value"),
)
def verifica_erro_email_1_editar_regra(email_destino):
    return verifica_erro_email_editar_regra(email_destino)


@callback(
    Output("input-email-2-regra-editar-retrabalho", "error"),
    Input("input-email-2-regra-editar-retrabalho", "value"),
)
def verifica_erro_email_2_editar_regra(email_destino):
    return verifica_erro_email_editar_regra(email_destino)


@callback(
    Output("input-email-3-regra-editar-retrabalho", "error"),
    Input("input-email-3-regra-editar-retrabalho", "value"),
)
def verifica_erro_email_3_editar_regra(email_destino):
    return verifica_erro_email_editar_regra(email_destino)


@callback(
    Output("input-email-4-regra-editar-retrabalho", "error"),
    Input("input-email-4-regra-editar-retrabalho", "value"),
)
def verifica_erro_email_4_editar_regra(email_destino):
    return verifica_erro_email_editar_regra(email_destino)


@callback(
    Output("input-email-5-regra-editar-retrabalho", "error"),
    Input("input-email-5-regra-editar-retrabalho", "value"),
)
def verifica_erro_email_5_editar_regra(email_destino):
    return verifica_erro_email_editar_regra(email_destino)


# Função para validar o input de telefone
def verifica_erro_wpp_editar_regra(wpp_telefone):
    # Se estive vazio, não considere erro
    if not wpp_telefone:
        return False

    wpp_limpo = wpp_telefone.replace(" ", "")

    padroes_validos = [
        r"^\(\d{2}\)\d{5}-\d{4}$",  # (62)99999-9999
        r"^\(\d{2}\)\d{4}-\d{4}$",  # (62)9999-9999
        r"^\d{2}\d{5}-\d{4}$",  # 6299999-9999
        r"^\d{2}\d{4}-\d{4}$",  # 629999-9999
        r"^\d{10}$",  # 6299999999 (fixo)
        r"^\d{11}$",  # 62999999999 (celular)
    ]

    if not any(re.match(padrao, wpp_limpo) for padrao in padroes_validos):
        return True

    return False


@callback(
    Output("input-wpp-1-regra-editar-retrabalho", "error"),
    Input("input-wpp-1-regra-editar-retrabalho", "value"),
)
def verifica_erro_wpp_1_editar_regra(wpp_telefone):
    return verifica_erro_wpp_editar_regra(wpp_telefone)


@callback(
    Output("input-wpp-2-regra-editar-retrabalho", "error"),
    Input("input-wpp-2-regra-editar-retrabalho", "value"),
)
def verifica_erro_wpp_2_editar_regra(wpp_telefone):
    return verifica_erro_wpp_editar_regra(wpp_telefone)


@callback(
    Output("input-wpp-3-regra-editar-retrabalho", "error"),
    Input("input-wpp-3-regra-editar-retrabalho", "value"),
)
def verifica_erro_wpp_3_editar_regra(wpp_telefone):
    return verifica_erro_wpp_editar_regra(wpp_telefone)


@callback(
    Output("input-wpp-4-regra-editar-retrabalho", "error"),
    Input("input-wpp-4-regra-editar-retrabalho", "value"),
)
def verifica_erro_wpp_4_editar_regra(wpp_telefone):
    return verifica_erro_wpp_editar_regra(wpp_telefone)


@callback(
    Output("input-wpp-5-regra-editar-retrabalho", "error"),
    Input("input-wpp-5-regra-editar-retrabalho", "value"),
)
def verifica_erro_wpp_5_editar_regra(wpp_telefone):
    return verifica_erro_wpp_editar_regra(wpp_telefone)


##############################################################################
# Callbacks para os gráficos #################################################
##############################################################################


# Callback para o grafico de síntese de todas as OS no período monitorado
@callback(
    [
        Output("graph-pizza-sintese-retrabalho-regra-editar", "figure"),
        Output("graph-pizza-filtro-retrabalho-regra-editar", "figure"),
    ],
    [
        Input("input-periodo-dias-monitoramento-regra-editar-retrabalho", "value"),
        Input("input-select-dias-regra-editar-retrabalho", "value"),
        Input("input-select-modelo-veiculos-regra-editar-retrabalho", "value"),
        Input("input-select-oficina-regra-editar-retrabalho", "value"),
        Input("input-select-secao-regra-editar-retrabalho", "value"),
        Input("input-select-ordens-servico-regra-editar-retrabalho", "value"),
        Input("checklist-alertar-alvo-regra-editar-retrabalho", "value"),
    ],
)
def plota_grafico_pizza_sintese_editar_regra(
    data_periodo_regra, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os, checklist_alvo
):
    # Valida input
    if not input_valido_editar_regra(
        data_periodo_regra, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os
    ):
        return go.Figure(), go.Figure()

    # Obtem os dados
    df = crud_regra_service.get_sintese_geral(
        data_periodo_regra, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os
    )

    # Copia o DF para checklist
    df_checklist = df.copy()

    # Termo e coluna para pegar o total de cada categoria na query
    dict_checklist = {
        "correcao_primeira": "TOTAL_CORRECAO_PRIMEIRA",
        "correcao_tardia": "TOTAL_CORRECAO_TARDIA",
        "nova_os_sem_retrabalho_anterior": "TOTAL_NOVA_OS_SEM_RETRABALHO_ANTERIOR",
        "nova_os_com_retrabalho_anterior": "TOTAL_NOVA_OS_COM_RETRABALHO_ANTERIOR",
        "retrabalho": "TOTAL_RETRABALHO",
    }

    # Computa o total de OS por categoria
    total_checklist = 0
    for termo, coluna in dict_checklist.items():
        if termo in checklist_alvo:
            total_checklist += df[coluna].values[0]

    df_checklist["TOTAL_NUM_OS"] = total_checklist

    # Prepara os dados para o gráfico
    labels = [
        # "Correção Primeira",
        # "Correção Tardia",
        "Nova OS, sem retrabalho prévio",
        "Nova OS, com retrabalho prévio",
        "Retrabalho",
    ]
    values = [
        # df["TOTAL_CORRECAO_PRIMEIRA"].values[0],
        # df["TOTAL_CORRECAO_TARDIA"].values[0],
        df["TOTAL_NOVA_OS_SEM_RETRABALHO_ANTERIOR"].values[0],
        df["TOTAL_NOVA_OS_COM_RETRABALHO_ANTERIOR"].values[0],
        df["TOTAL_RETRABALHO"].values[0],
    ]

    # Gera o gráfico
    fig_geral = crud_regra_graficos.gerar_grafico_pizza_sinteze_geral(df, labels, values, usar_checklist=False)
    fig_filtro = crud_regra_graficos.gerar_grafico_pizza_sinteze_geral(
        df_checklist, labels, values, usar_checklist=True, checklist_alvo=checklist_alvo
    )
    return fig_geral, fig_filtro


# Callback para a tabela com a prévia da OS a serem criadas
@callback(
    Output("tabela-previa-os-regra-editar", "rowData"),
    [
        Input("input-periodo-dias-monitoramento-regra-editar-retrabalho", "value"),
        Input("input-select-dias-regra-editar-retrabalho", "value"),
        Input("input-select-modelo-veiculos-regra-editar-retrabalho", "value"),
        Input("input-select-oficina-regra-editar-retrabalho", "value"),
        Input("input-select-secao-regra-editar-retrabalho", "value"),
        Input("input-select-ordens-servico-regra-editar-retrabalho", "value"),
        Input("checklist-alertar-alvo-regra-editar-retrabalho", "value"),
    ],
)
def tabela_previa_os_regra_editar_regra(
    data_periodo_regra, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os, checklist_alvo
):
    # Valida input
    if not input_valido_editar_regra(
        data_periodo_regra, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os
    ):
        return []

    # Obtem os dados
    df = crud_regra_service.get_previa_os_regra_detalhada(
        data_periodo_regra, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os, checklist_alvo
    )

    return df.to_dict(orient="records")


##############################################################################
# Callbacks para o teste da regra ############################################
##############################################################################


# Callback para o botão de fechar o modal de erro ao testar a regra
@callback(
    Output("modal-erro-teste-editar-regra", "opened", allow_duplicate=True),
    Input("btn-close-modal-erro-teste-editar-regra", "n_clicks"),
    prevent_initial_call=True,
)
def fecha_modal_erro_teste_regra_editar_regra(n_clicks_btn_fechar):
    if n_clicks_btn_fechar and n_clicks_btn_fechar > 0:
        return False
    else:
        return dash.no_update


# Callback para o botão de fechar o modal de sucesso ao testar a regra
@callback(
    Output("modal-sucesso-teste-editar-regra", "opened", allow_duplicate=True),
    Input("btn-close-modal-sucesso-teste-editar-regra", "n_clicks"),
    prevent_initial_call=True,
)
def fecha_modal_sucesso_teste_regra_editar_regra(n_clicks_btn_fechar):
    if n_clicks_btn_fechar and n_clicks_btn_fechar > 0:
        return False
    else:
        return dash.no_update


# Callback para o botão de testar a regra
@callback(
    [
        Output("modal-erro-teste-editar-regra", "opened", allow_duplicate=True),
        Output("modal-sucesso-teste-editar-regra", "opened", allow_duplicate=True),
    ],
    [
        Input("btn-testar-regra-monitoramento-editar-retrabalho", "n_clicks"),
        Input("input-nome-regra-monitoramento-retrabalho", "value"),
        Input("input-periodo-dias-monitoramento-regra-editar-retrabalho", "value"),
        Input("input-select-dias-regra-editar-retrabalho", "value"),
        Input("input-select-modelo-veiculos-regra-editar-retrabalho", "value"),
        Input("input-select-oficina-regra-editar-retrabalho", "value"),
        Input("input-select-secao-regra-editar-retrabalho", "value"),
        Input("input-select-ordens-servico-regra-editar-retrabalho", "value"),
        Input("checklist-alertar-alvo-regra-editar-retrabalho", "value"),
        Input("switch-enviar-email-regra-editar-retrabalho", "checked"),
        Input("input-email-1-regra-editar-retrabalho", "value"),
        Input("input-email-2-regra-editar-retrabalho", "value"),
        Input("input-email-3-regra-editar-retrabalho", "value"),
        Input("input-email-4-regra-editar-retrabalho", "value"),
        Input("input-email-5-regra-editar-retrabalho", "value"),
        Input("switch-enviar-wpp-regra-editar-retrabalho", "checked"),
        Input("input-wpp-1-regra-editar-retrabalho", "value"),
        Input("input-wpp-2-regra-editar-retrabalho", "value"),
        Input("input-wpp-3-regra-editar-retrabalho", "value"),
        Input("input-wpp-4-regra-editar-retrabalho", "value"),
        Input("input-wpp-5-regra-editar-retrabalho", "value"),
    ],
    prevent_initial_call=True,
)
def testa_regra_monitoramento_retrabalho_editar_regra(
    n_clicks_btn_testar,
    nome_regra,
    data_periodo_regra,
    min_dias,
    lista_modelos,
    lista_oficinas,
    lista_secaos,
    lista_os,
    checklist_alvo,
    email_ativo,
    email_destino_1,
    email_destino_2,
    email_destino_3,
    email_destino_4,
    email_destino_5,
    wpp_ativo,
    wpp_telefone_1,
    wpp_telefone_2,
    wpp_telefone_3,
    wpp_telefone_4,
    wpp_telefone_5,
):
    ctx = callback_context  # Obtém o contexto do callback
    if not ctx.triggered:
        return dash.no_update  # Evita execução desnecessária

    # Verifica se o callback foi acionado pelo botão de download
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Checa se o trigger foi o botão de fechar o popup
    if triggered_id != "btn-testar-regra-monitoramento-editar-retrabalho":
        return [dash.no_update, dash.no_update]

    # Botão clicado foi o de testar a regra

    # Se o botão não foi clicado, não faz nada
    if not n_clicks_btn_testar or n_clicks_btn_testar <= 0:
        return [dash.no_update, dash.no_update]

    # Valida Resto do input
    if not input_valido_editar_regra(
        data_periodo_regra, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os
    ) or not target_os_valido_editar_regra(checklist_alvo):
        return [True, False]

    # Valida nome da regra
    if not nome_regra:
        return [True, False]

    # Verifica se pelo menos um email ou wpp está ativo
    if not email_ativo and not wpp_ativo:
        return [True, False]

    # Valida se há pelo menos um telefone de whatsapp válido caso esteja ativo
    wpp_telefones = [wpp_telefone_1, wpp_telefone_2, wpp_telefone_3, wpp_telefone_4, wpp_telefone_5]
    wpp_tel_validos = []
    if wpp_ativo:
        wpp_tel_validos = [wpp for wpp in wpp_telefones if wpp != "" and not verifica_erro_wpp_editar_regra(wpp)]
        if len(wpp_tel_validos) == 0:
            return [True, False]

    # Valida se há pelo menos um email válido caso esteja ativo
    email_destinos = [email_destino_1, email_destino_2, email_destino_3, email_destino_4, email_destino_5]
    email_destinos_validos = []
    if email_ativo:
        email_destinos_validos = [
            email for email in email_destinos if email != "" and not verifica_erro_email_editar_regra(email)
        ]
        if len(email_destinos_validos) == 0:
            return [True, False]

    # Obtem os dados
    df = crud_regra_service.get_previa_os_regra_detalhada(
        data_periodo_regra, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os, checklist_alvo
    )
    num_os = len(df)

    # Envia mensagem via WhatsApp se ativo
    if wpp_ativo:
        wpp_service = CRUDWppTestService()
        for wpp_tel in wpp_tel_validos:
            wpp_service.build_and_send_msg(
                df,
                num_os,
                nome_regra,
                data_periodo_regra,
                min_dias,
                lista_modelos,
                lista_oficinas,
                lista_secaos,
                lista_os,
                wpp_tel,
            )

    # Envia mensagem via email se ativo
    if email_ativo:
        email_service = CRUDEmailTestService()
        for email_destino in email_destinos_validos:
            email_service.build_and_send_msg(
                df,
                num_os,
                nome_regra,
                data_periodo_regra,
                min_dias,
                lista_modelos,
                lista_oficinas,
                lista_secaos,
                lista_os,
                email_destino,
            )

    return [False, True]


##############################################################################
# Callbacks para salvar a regra ##############################################
##############################################################################


# Callback para o botão de fechar o modal de erro ao salvar a regra
@callback(
    Output("modal-erro-atualizar-editar-regra", "opened", allow_duplicate=True),
    Input("btn-close-modal-erro-atualizar-editar-regra", "n_clicks"),
    prevent_initial_call=True,
)
def fecha_modal_erro_atualizar_regra_editar_regra(n_clicks_btn_fechar):
    if n_clicks_btn_fechar and n_clicks_btn_fechar > 0:
        return False
    else:
        return dash.no_update


# Callback para o botão de fechar o modal de sucesso ao salvar a regra
@callback(
    [
        Output("modal-sucesso-atualizar-editar-regra", "opened", allow_duplicate=True),
        Output("url", "href", allow_duplicate=True),
    ],
    Input("btn-close-modal-sucesso-atualizar-editar-regra", "n_clicks"),
    prevent_initial_call=True,
)
def fecha_modal_sucesso_atualizar_regra_editar_regra(n_clicks_btn_fechar):
    if n_clicks_btn_fechar and n_clicks_btn_fechar > 0:
        return [False, "/regra-gerenciar"]
    else:
        return [dash.no_update, dash.no_update]


# Callback para o botão de salvar a regra
@callback(
    [
        Output("modal-erro-atualizar-editar-regra", "opened", allow_duplicate=True),
        Output("modal-sucesso-atualizar-editar-regra", "opened", allow_duplicate=True),
    ],
    [
        Input("store-input-id-editar-regra", "data"),
        Input("btn-editar-regra-monitoramento-atualizar-retrabalho", "n_clicks"),
        Input("input-nome-regra-monitoramento-retrabalho", "value"),
        Input("input-periodo-dias-monitoramento-regra-editar-retrabalho", "value"),
        Input("input-select-dias-regra-editar-retrabalho", "value"),
        Input("input-select-modelo-veiculos-regra-editar-retrabalho", "value"),
        Input("input-select-oficina-regra-editar-retrabalho", "value"),
        Input("input-select-secao-regra-editar-retrabalho", "value"),
        Input("input-select-ordens-servico-regra-editar-retrabalho", "value"),
        Input("checklist-alertar-alvo-regra-editar-retrabalho", "value"),
        Input("switch-enviar-email-regra-editar-retrabalho", "checked"),
        Input("input-email-1-regra-editar-retrabalho", "value"),
        Input("input-email-2-regra-editar-retrabalho", "value"),
        Input("input-email-3-regra-editar-retrabalho", "value"),
        Input("input-email-4-regra-editar-retrabalho", "value"),
        Input("input-email-5-regra-editar-retrabalho", "value"),
        Input("switch-enviar-wpp-regra-editar-retrabalho", "checked"),
        Input("input-wpp-1-regra-editar-retrabalho", "value"),
        Input("input-wpp-2-regra-editar-retrabalho", "value"),
        Input("input-wpp-3-regra-editar-retrabalho", "value"),
        Input("input-wpp-4-regra-editar-retrabalho", "value"),
        Input("input-wpp-5-regra-editar-retrabalho", "value"),
        Input("horario-envio-regra-editar-retrabalho", "value"),
    ],
    prevent_initial_call=True,
)
def atualizar_regra_monitoramento_retrabalho_editar_regra(
    store_regra,
    n_clicks_btn_salvar,
    nome_regra,
    data_periodo_regra,
    min_dias,
    lista_modelos,
    lista_oficinas,
    lista_secaos,
    lista_os,
    checklist_alvo,
    email_ativo,
    email_destino_1,
    email_destino_2,
    email_destino_3,
    email_destino_4,
    email_destino_5,
    wpp_ativo,
    wpp_telefone_1,
    wpp_telefone_2,
    wpp_telefone_3,
    wpp_telefone_4,
    wpp_telefone_5,
    horario_envio,
):
    ctx = callback_context  # Obtém o contexto do callback
    if not ctx.triggered:
        return [dash.no_update, dash.no_update]  # Evita execução desnecessária

    # Verifica se o callback foi acionado pelo botão de download
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Botão clicado foi o de salvar a regra?
    if triggered_id != "btn-editar-regra-monitoramento-atualizar-retrabalho":
        return [dash.no_update, dash.no_update]

    # Se o botão não foi clicado, não faz nada
    if not n_clicks_btn_salvar or n_clicks_btn_salvar <= 0:
        return [dash.no_update, dash.no_update]

    # Valida se tem o id da regra
    if not store_regra:
        return [dash.no_update, dash.no_update]

    id_regra = store_regra["id_regra"] if store_regra["valido"] else -1

    # Se não tem o id da regra, não faz nada
    if id_regra == -1:
        return [dash.no_update, dash.no_update]

    # Valida Resto do input
    if (
        not input_valido_editar_regra(
            data_periodo_regra, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os
        )
        or not target_os_valido_editar_regra(checklist_alvo)
        or not horario_valido_editar_regra(horario_envio)
    ):
        return [True, False]

    # Valida nome da regra
    if not nome_regra:
        return [True, False]

    # Verifica se pelo menos um email ou wpp está ativo
    if not email_ativo and not wpp_ativo:
        return [True, False]

    # Valida se há pelo menos um telefone de whatsapp válido caso esteja ativo
    wpp_telefones = [wpp_telefone_1, wpp_telefone_2, wpp_telefone_3, wpp_telefone_4, wpp_telefone_5]
    wpp_tel_validos = []
    if wpp_ativo:
        wpp_tel_validos = [wpp for wpp in wpp_telefones if wpp != "" and not verifica_erro_wpp_editar_regra(wpp)]
        if len(wpp_tel_validos) == 0:
            return [True, False]

    # Valida se há pelo menos um email válido caso esteja ativo
    email_destinos = [email_destino_1, email_destino_2, email_destino_3, email_destino_4, email_destino_5]
    email_destinos_validos = []
    if email_ativo:
        email_destinos_validos = [
            email for email in email_destinos if email != "" and not verifica_erro_email_editar_regra(email)
        ]
        if len(email_destinos_validos) == 0:
            return [True, False]

    # Obtem os dados restantes para salvar a regra
    target_nova_os_sem_retrabalho_previo = True if "nova_os_sem_retrabalho_anterior" in checklist_alvo else False
    target_nova_os_com_retrabalho_previo = True if "nova_os_com_retrabalho_anterior" in checklist_alvo else False
    target_retrabalho = True if "retrabalho" in checklist_alvo else False

    target_wpp_telefones = wpp_telefones
    target_wpp_telefones_validos = [
        wpp if wpp and not verifica_erro_wpp_editar_regra(wpp) else None for wpp in target_wpp_telefones
    ]

    target_email_destinos = email_destinos
    target_email_destinos_validos = [
        email if email and not verifica_erro_email_editar_regra(email) else None for email in target_email_destinos
    ]

    payload = {
        "nome": nome_regra,
        "data_periodo_regra": data_periodo_regra,
        "min_dias_retrabalho": min_dias,
        "modelos_veiculos": lista_modelos,
        "oficinas": lista_oficinas,
        "secoes": lista_secaos,
        "os": lista_os,
        "target_nova_os_sem_retrabalho_previo": target_nova_os_sem_retrabalho_previo,
        "target_nova_os_com_retrabalho_previo": target_nova_os_com_retrabalho_previo,
        "target_retrabalho": target_retrabalho,
        "target_email": email_ativo,
        "target_email_dest1": target_email_destinos_validos[0],
        "target_email_dest2": target_email_destinos_validos[1],
        "target_email_dest3": target_email_destinos_validos[2],
        "target_email_dest4": target_email_destinos_validos[3],
        "target_email_dest5": target_email_destinos_validos[4],
        "target_wpp": wpp_ativo,
        "target_wpp_dest1": target_wpp_telefones_validos[0],
        "target_wpp_dest2": target_wpp_telefones_validos[1],
        "target_wpp_dest3": target_wpp_telefones_validos[2],
        "target_wpp_dest4": target_wpp_telefones_validos[3],
        "target_wpp_dest5": target_wpp_telefones_validos[4],
        "hora_disparar": horario_envio,
    }

    regra_atualizada_com_sucesso = crud_regra_service.atualizar_regra_monitoramento(id_regra, payload)

    if regra_atualizada_com_sucesso:
        return [False, True]
    else:
        return [True, False]


##############################################################################
# Layout #####################################################################
##############################################################################
layout = dbc.Container(
    [
        # Estado
        dcc.Store(id="store-input-id-editar-regra"),
        # Loading
        dmc.LoadingOverlay(
            visible=True,
            id="loading-overlay-guia-editar-regra",
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
            id="modal-erro-carregar-dados-editar-regra",
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
                                id="btn-close-modal-erro-carregar-dados-editar-regra",
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
            id="modal-erro-teste-editar-regra",
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
                                id="btn-close-modal-erro-teste-editar-regra",
                            ),
                        ],
                    ),
                ],
                align="center",
                gap="md",
            ),
        ),
        dmc.Modal(
            id="modal-sucesso-teste-editar-regra",
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
                                id="btn-close-modal-sucesso-teste-editar-regra",
                            ),
                        ],
                    ),
                ],
                align="center",
                gap="md",
            ),
        ),
        dmc.Modal(
            id="modal-erro-atualizar-editar-regra",
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
                                id="btn-close-modal-erro-atualizar-editar-regra",
                            ),
                        ],
                    ),
                ],
                align="center",
                gap="md",
            ),
        ),
        dmc.Modal(
            id="modal-sucesso-atualizar-editar-regra",
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
                                id="btn-close-modal-sucesso-atualizar-editar-regra",
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
                dbc.Col(DashIconify(icon="carbon:rule-draft", width=45), width="auto"),
                dbc.Col(
                    html.H1(
                        [
                            "Editar \u00a0",
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
        # dmc.Space(h=15),
        html.Hr(),
        dbc.Row(
            [
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
            ]
        ),
        dmc.Space(h=10),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        html.Div(
                            [
                                dbc.Label("Período de Monitoramento (últimos X dias)"),
                                dbc.InputGroup(
                                    [
                                        dbc.Input(
                                            id="input-periodo-dias-monitoramento-regra-editar-retrabalho",
                                            type="number",
                                            placeholder="Dias",
                                            value=3,
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
                                        id="input-select-dias-regra-editar-retrabalho",
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
            ]
        ),
        dmc.Space(h=10),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            html.Div(
                                [
                                    dbc.Label("Modelos de Veículos"),
                                    dcc.Dropdown(
                                        id="input-select-modelo-veiculos-regra-editar-retrabalho",
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
                    md=6,
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            html.Div(
                                [
                                    dbc.Label("Oficinas"),
                                    dcc.Dropdown(
                                        id="input-select-oficina-regra-editar-retrabalho",
                                        options=[
                                            {"label": os["LABEL"], "value": os["LABEL"]} for os in lista_todas_oficinas
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
            ]
        ),
        dmc.Space(h=10),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            html.Div(
                                [
                                    dbc.Label("Seções (categorias) de manutenção"),
                                    dcc.Dropdown(
                                        id="input-select-secao-regra-editar-retrabalho",
                                        options=[
                                            {"label": sec["LABEL"], "value": sec["LABEL"]} for sec in lista_todas_secoes
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
                dbc.Col(
                    dbc.Card(
                        [
                            html.Div(
                                [
                                    dbc.Label("Ordens de Serviço"),
                                    dcc.Dropdown(
                                        id="input-select-ordens-servico-regra-editar-retrabalho",
                                        options=[{"label": os["LABEL"], "value": os["LABEL"]} for os in lista_todas_os],
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
            ]
        ),
        dmc.Space(h=10),
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            html.Div(
                                [
                                    dbc.Label("Alertar:"),
                                    dbc.Checklist(
                                        options=[
                                            {
                                                "label": "Nova OS, sem retrabalho prévio",
                                                "value": "nova_os_sem_retrabalho_anterior",
                                            },
                                            {
                                                "label": "Nova OS, com retrabalho prévio",
                                                "value": "nova_os_com_retrabalho_anterior",
                                            },
                                            {"label": "Retrabalho", "value": "retrabalho"},
                                            # {
                                            #     "label": "Correção de Primeira",
                                            #     "value": "correcao_primeira",
                                            # },
                                            # {
                                            #     "label": "Correção tardia",
                                            #     "value": "correcao_tardia",
                                            # },
                                        ],
                                        value=["nova_os_com_retrabalho_anterior", "retrabalho"],
                                        id="checklist-alertar-alvo-regra-editar-retrabalho",
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
                dbc.Col(
                    dbc.Card(
                        [
                            html.Div(
                                [
                                    dbc.Label("Horário de envio:"),
                                    dmc.TimeInput(
                                        debounce=True, id="horario-envio-regra-editar-retrabalho", value="06:00"
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
        dmc.Space(h=10),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.Row(
                            [
                                dbc.Col(
                                    dmc.Switch(
                                        id="switch-enviar-email-regra-editar-retrabalho",
                                        label="Enviar email",
                                        checked=False,
                                        size="md",
                                    ),
                                    width="auto",
                                ),
                                dbc.Col(
                                    dbc.Row(
                                        [
                                            dmc.Space(h=10),
                                            dbc.Col(
                                                dbc.Label("Emails de destino (Digite até 5 emails)"),
                                                md=12,
                                            ),
                                            dbc.Col(
                                                dmc.TextInput(
                                                    id="input-email-1-regra-editar-retrabalho",
                                                    placeholder="email1@odilonsantos.com",
                                                    value="",
                                                    leftSection=DashIconify(icon="mdi:email"),
                                                ),
                                                md=12,
                                            ),
                                            dmc.Space(h=10),
                                            dbc.Col(
                                                dmc.TextInput(
                                                    id="input-email-2-regra-editar-retrabalho",
                                                    placeholder="email2@odilonsantos.com",
                                                    value="",
                                                    leftSection=DashIconify(icon="mdi:email"),
                                                ),
                                                md=12,
                                            ),
                                            dmc.Space(h=10),
                                            dbc.Col(
                                                dmc.TextInput(
                                                    id="input-email-3-regra-editar-retrabalho",
                                                    placeholder="email3@odilonsantos.com",
                                                    value="",
                                                    leftSection=DashIconify(icon="mdi:email"),
                                                ),
                                                md=12,
                                            ),
                                            dmc.Space(h=10),
                                            dbc.Col(
                                                dmc.TextInput(
                                                    id="input-email-4-regra-editar-retrabalho",
                                                    placeholder="email4@odilonsantos.com",
                                                    value="",
                                                    leftSection=DashIconify(icon="mdi:email"),
                                                ),
                                                md=12,
                                            ),
                                            dmc.Space(h=10),
                                            dbc.Col(
                                                dmc.TextInput(
                                                    id="input-email-5-regra-editar-retrabalho",
                                                    placeholder="email5@odilonsantos.com",
                                                    value="",
                                                    leftSection=DashIconify(icon="mdi:email"),
                                                ),
                                                md=12,
                                            ),
                                        ],
                                        align="center",
                                    ),
                                    id="input-email-destino-container-regra-editar-retrabalho",
                                    md=12,
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
                                        id="switch-enviar-wpp-regra-editar-retrabalho",
                                        label="Enviar WhatsApp",
                                        checked=False,
                                        size="md",
                                    ),
                                    width="auto",
                                ),
                                dbc.Col(
                                    dbc.Row(
                                        [
                                            dmc.Space(h=10),
                                            dbc.Col(
                                                dbc.Label("WhatsApp de destino (Digite até 5 números)"),
                                                md=12,
                                            ),
                                            dbc.Col(
                                                dmc.TextInput(
                                                    id="input-wpp-1-regra-editar-retrabalho",
                                                    placeholder="(62) 99999-9999",
                                                    value="",
                                                    leftSection=DashIconify(icon="logos:whatsapp-icon"),
                                                ),
                                                md=12,
                                            ),
                                            dmc.Space(h=10),
                                            dbc.Col(
                                                dmc.TextInput(
                                                    id="input-wpp-2-regra-editar-retrabalho",
                                                    placeholder="(62) 99999-9999",
                                                    value="",
                                                    leftSection=DashIconify(icon="logos:whatsapp-icon"),
                                                ),
                                                md=12,
                                            ),
                                            dmc.Space(h=10),
                                            dbc.Col(
                                                dmc.TextInput(
                                                    id="input-wpp-3-regra-editar-retrabalho",
                                                    placeholder="(62) 99999-9999",
                                                    value="",
                                                    leftSection=DashIconify(icon="logos:whatsapp-icon"),
                                                ),
                                                md=12,
                                            ),
                                            dmc.Space(h=10),
                                            dbc.Col(
                                                dmc.TextInput(
                                                    id="input-wpp-4-regra-editar-retrabalho",
                                                    placeholder="(62) 99999-9999",
                                                    value="",
                                                    leftSection=DashIconify(icon="logos:whatsapp-icon"),
                                                ),
                                                md=12,
                                            ),
                                            dmc.Space(h=10),
                                            dbc.Col(
                                                dmc.TextInput(
                                                    id="input-wpp-5-regra-editar-retrabalho",
                                                    placeholder="(62) 99999-9999",
                                                    value="",
                                                    leftSection=DashIconify(icon="logos:whatsapp-icon"),
                                                ),
                                                md=12,
                                            ),
                                        ],
                                        align="center",
                                    ),
                                    id="input-wpp-destino-container-regra-editar-retrabalho",
                                    md=12,
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
        dmc.Space(h=30),
        # Botão Criar Regra
        dbc.Row(
            [
                dbc.Col(
                    dbc.Button(
                        "Testar Regra (enviar mensagem)",
                        id="btn-testar-regra-monitoramento-editar-retrabalho",
                        color="info",
                        className="me-1",
                        style={"padding": "1em", "width": "100%"},
                    ),
                    md=6,
                ),
                dbc.Col(
                    dbc.Button(
                        "Atualizar Regra",
                        id="btn-editar-regra-monitoramento-atualizar-retrabalho",
                        color="success",
                        className="me-1",
                        style={"padding": "1em", "width": "100%"},
                    ),
                    md=6,
                ),
            ],
            justify="center",
        ),
        html.Div(id="mensagem-sucesso", style={"marginTop": "10px", "fontWeight": "bold"}),
        dmc.Space(h=40),
        # Resumo
        dbc.Row(
            [
                dbc.Col(
                    dbc.Row(
                        [
                            # Cabeçalho
                            html.Hr(),
                            dbc.Col(
                                DashIconify(icon="wpf:statistics", width=45),
                                width="auto",
                            ),
                            dbc.Col(html.H1("Total de OS no período", className="align-self-center"), width=True),
                            dmc.Space(h=15),
                            html.Hr(),
                            dbc.Row(dcc.Graph(id="graph-pizza-sintese-retrabalho-regra-editar")),
                        ]
                    ),
                    md=6,
                ),
                dbc.Col(
                    dbc.Row(
                        [
                            # Cabeçalho
                            html.Hr(),
                            dbc.Col(
                                DashIconify(icon="meteor-icons:filter", width=45),
                                width="auto",
                            ),
                            dbc.Col(html.H1("OSs filtradas", className="align-self-center"), width=True),
                            dmc.Space(h=15),
                            html.Hr(),
                            dbc.Row(dcc.Graph(id="graph-pizza-filtro-retrabalho-regra-editar")),
                        ]
                    ),
                    md=6,
                ),
            ]
        ),
        dmc.Space(h=40),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="mdi:car-search-outline", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Pré-visualização das OSs que foram filtradas pela regra criada",
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
            id="tabela-previa-os-regra-editar",
            columnDefs=crud_regra_tabelas.tbl_detalhamento_problema_regra,
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
dash.register_page(__name__, name="Editar Regra", path="/regra-editar", icon="carbon:rule-draft", hide_page=True)
