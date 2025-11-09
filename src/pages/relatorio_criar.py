#!/usr/bin/env python
# coding: utf-8

# Tela para criar um relatório de retrabalho

##############################################################################
# IMPORTS ####################################################################
##############################################################################
# Bibliotecas básicas
import re

# Importar bibliotecas do dash básicas e plotly
import dash
from dash import html, dcc, callback, Input, Output, callback_context
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
from modules.entities_utils import get_mecanicos, get_lista_os, get_oficinas, get_secoes, get_modelos

# Imports específicos
from modules.crud_relatorio.crud_relatorio_service import CRUDRelatorioService

##############################################################################
# LEITURA DE DADOS ###########################################################
##############################################################################
# Conexão com os bancos
pgDB = PostgresSingleton.get_instance()
pgEngine = pgDB.get_engine()

# Cria o serviço
crud_relatorio_service = CRUDRelatorioService(pgEngine)

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
def input_valido(periodo_regra, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os):
    if periodo_regra is None or not periodo_regra or periodo_regra == 0 or min_dias is None:
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


def horario_valido(horario_envio):
    if not horario_envio:
        return False

    if not time_pattern.match(horario_envio):
        return False

    return True

def target_dia_semana_valido(checklist):
    if checklist is None:
        return False

    # Dias da semana
    if checklist >= 0 and checklist <= 6:
        return True

    return False

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
    Output("pag-criar-relatorio-input-select-modelo-veiculos", "value"),
    Input("pag-criar-relatorio-input-select-modelo-veiculos", "value"),
)
def corrige_input_modelos(lista_modelos):
    return corrige_input(lista_modelos, "TODOS")


@callback(
    Output("pag-criar-relatorio-input-select-oficina", "value"),
    Input("pag-criar-relatorio-input-select-oficina", "value"),
)
def corrige_input_oficina(lista_oficinas):
    return corrige_input(lista_oficinas)


@callback(
    Output("pag-criar-relatorio-input-select-secao", "value"),
    Input("pag-criar-relatorio-input-select-secao", "value"),
)
def corrige_input_secao(lista_secaos):
    return corrige_input(lista_secaos)


@callback(
    [
        Output("pag-criar-relatorio-input-select-ordens-servico", "options"),
        Output("pag-criar-relatorio-input-select-ordens-servico", "value"),
    ],
    [
        Input("pag-criar-relatorio-input-select-ordens-servico", "value"),
        Input("pag-criar-relatorio-input-select-secao", "value"),
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



# Função para mostrar o input de email de destino
@callback(
    Output("pag-criar-relatorio-input-email-destino-container", "style"),
    Input("pag-criar-relatorio-switch-enviar-email", "checked"),
)
def mostra_input_email_destino(email_ativo):
    if email_ativo:
        return {"display": "block"}
    else:
        return {"display": "none"}


# Função para mostrar o input de WhatsApp de destino
@callback(
    Output("pag-criar-relatorio-input-wpp-destino-container", "style"),
    Input("pag-criar-relatorio-switch-enviar-wpp-regra", "checked"),
)
def mostra_input_wpp_destino(wpp_ativo):
    if wpp_ativo:
        return {"display": "block"}
    else:
        return {"display": "none"}


# Função para validar o input de email de destino
def verifica_erro_email(email_destino):
    if not email_destino:
        return False

    email_limpo = email_destino.strip()

    if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$", email_limpo):
        return True

    return False


@callback(
    Output("pag-criar-relatorio-input-email-1", "error"),
    Input("pag-criar-relatorio-input-email-1", "value"),
)
def verifica_erro_email_1(email_destino):
    return verifica_erro_email(email_destino)


@callback(
    Output("pag-criar-relatorio-input-email-2", "error"),
    Input("pag-criar-relatorio-input-email-2", "value"),
)
def verifica_erro_email_2(email_destino):
    return verifica_erro_email(email_destino)


@callback(
    Output("pag-criar-relatorio-input-email-3", "error"),
    Input("pag-criar-relatorio-input-email-3", "value"),
)
def verifica_erro_email_3(email_destino):
    return verifica_erro_email(email_destino)


@callback(
    Output("pag-criar-relatorio-input-email-4", "error"),
    Input("pag-criar-relatorio-input-email-4", "value"),
)
def verifica_erro_email_4(email_destino):
    return verifica_erro_email(email_destino)


@callback(
    Output("pag-criar-relatorio-input-email-5", "error"),
    Input("pag-criar-relatorio-input-email-5", "value"),
)
def verifica_erro_email_5(email_destino):
    return verifica_erro_email(email_destino)


# Função para validar o input de telefone
def verifica_erro_wpp(wpp_telefone):
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
    Output("pag-criar-relatorio-input-wpp-1", "error"),
    Input("pag-criar-relatorio-input-wpp-1", "value"),
)
def verifica_erro_wpp_1(wpp_telefone):
    return verifica_erro_wpp(wpp_telefone)


@callback(
    Output("pag-criar-relatorio-input-wpp-2", "error"),
    Input("pag-criar-relatorio-input-wpp-2", "value"),
)
def verifica_erro_wpp_2(wpp_telefone):
    return verifica_erro_wpp(wpp_telefone)


@callback(
    Output("pag-criar-relatorio-input-wpp-3", "error"),
    Input("pag-criar-relatorio-input-wpp-3", "value"),
)
def verifica_erro_wpp_3(wpp_telefone):
    return verifica_erro_wpp(wpp_telefone)


@callback(
    Output("pag-criar-relatorio-input-wpp-4", "error"),
    Input("pag-criar-relatorio-input-wpp-4", "value"),
)
def verifica_erro_wpp_4(wpp_telefone):
    return verifica_erro_wpp(wpp_telefone)


@callback(
    Output("pag-criar-relatorio-input-wpp-5", "error"),
    Input("pag-criar-relatorio-input-wpp-5", "value"),
)
def verifica_erro_wpp_5(wpp_telefone):
    return verifica_erro_wpp(wpp_telefone)

##############################################################################
# Callbacks para salvar a regra ##############################################
##############################################################################


# Callback para o botão de fechar o modal de erro ao salvar a regra
@callback(
    Output("pag-criar-relatorio-modal-erro-salvar", "opened", allow_duplicate=True),
    Input("pag-criar-relatorio-btn-close-modal-erro-salvar", "n_clicks"),
    prevent_initial_call=True,
)
def fecha_modal_erro_salvar_regra(n_clicks_btn_fechar):
    if n_clicks_btn_fechar and n_clicks_btn_fechar > 0:
        return False
    else:
        return dash.no_update


# Callback para o botão de fechar o modal de sucesso ao salvar a regra
@callback(
    [
        Output("pag-criar-relatorio-modal-sucesso-salvar", "opened", allow_duplicate=True),
        Output("url", "href", allow_duplicate=True),
    ],
    Input("pag-criar-relatorio-btn-close-modal-sucesso-salvar", "n_clicks"),
    prevent_initial_call=True,
)
def fecha_modal_sucesso_salvar_regra(n_clicks_btn_fechar):
    if n_clicks_btn_fechar and n_clicks_btn_fechar > 0:
        return [False, "/relatorio-gerenciar"]
    else:
        return [dash.no_update, dash.no_update]


# Callback para o botão de salvar a regra
@callback(
    [
        Output("pag-criar-relatorio-modal-erro-salvar", "opened", allow_duplicate=True),
        Output("pag-criar-relatorio-modal-sucesso-salvar", "opened", allow_duplicate=True),
    ],
    [
        Input("pag-criar-relatorio-btn-salvar-regra", "n_clicks"),
        Input("pag-criar-relatorio-input-nome", "value"),
        Input("pag-criar-relatorio-input-periodo-dias-monitoramento", "value"),
        Input("pag-criar-relatorio-input-select-dias", "value"),
        Input("pag-criar-relatorio-input-select-modelo-veiculos", "value"),
        Input("pag-criar-relatorio-input-select-oficina", "value"),
        Input("pag-criar-relatorio-input-select-secao", "value"),
        Input("pag-criar-relatorio-input-select-ordens-servico", "value"),
        Input("pag-criar-relatorio-checklist-dia-semana", "value"),
        Input("pag-criar-relatorio-switch-enviar-email", "checked"),
        Input("pag-criar-relatorio-input-email-1", "value"),
        Input("pag-criar-relatorio-input-email-2", "value"),
        Input("pag-criar-relatorio-input-email-3", "value"),
        Input("pag-criar-relatorio-input-email-4", "value"),
        Input("pag-criar-relatorio-input-email-5", "value"),
        Input("pag-criar-relatorio-switch-enviar-wpp-regra", "checked"),
        Input("pag-criar-relatorio-input-wpp-1", "value"),
        Input("pag-criar-relatorio-input-wpp-2", "value"),
        Input("pag-criar-relatorio-input-wpp-3", "value"),
        Input("pag-criar-relatorio-input-wpp-4", "value"),
        Input("pag-criar-relatorio-input-wpp-5", "value"),
        Input("pag-criar-relatorio-horario-envio-regra", "value"),
    ],
    prevent_initial_call=True,
)
def salvar_regra_monitoramento_retrabalho(
    n_clicks_btn_salvar,
    nome_regra,
    periodo_regra,
    min_dias,
    lista_modelos,
    lista_oficinas,
    lista_secaos,
    lista_os,
    checklist_dias_semana,
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
    if triggered_id != "pag-criar-relatorio-btn-salvar-regra":
        return [dash.no_update, dash.no_update]

    # Se o botão não foi clicado, não faz nada
    if not n_clicks_btn_salvar or n_clicks_btn_salvar <= 0:
        return [dash.no_update, dash.no_update]

    # Valida Resto do input
    if (
        not input_valido(periodo_regra, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os)
        or not target_dia_semana_valido(checklist_dias_semana)
        or not horario_valido(horario_envio)
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
        wpp_tel_validos = [wpp for wpp in wpp_telefones if wpp != "" and not verifica_erro_wpp(wpp)]
        if len(wpp_tel_validos) == 0:
            return [True, False]

    # Valida se há pelo menos um email válido caso esteja ativo
    email_destinos = [email_destino_1, email_destino_2, email_destino_3, email_destino_4, email_destino_5]
    email_destinos_validos = []
    if email_ativo:
        email_destinos_validos = [email for email in email_destinos if email != "" and not verifica_erro_email(email)]
        if len(email_destinos_validos) == 0:
            return [True, False]

    # Obtem o dia da semana
    dia_semana = checklist_dias_semana

    # Obtém os alvos
    target_wpp_telefones = wpp_telefones
    target_wpp_telefones_validos = [wpp if wpp and not verifica_erro_wpp(wpp) else None for wpp in target_wpp_telefones]

    target_email_destinos = email_destinos
    target_email_destinos_validos = [
        email if email and not verifica_erro_email(email) else None for email in target_email_destinos
    ]

    payload = {
        "nome": nome_regra,
        "periodo": periodo_regra,
        "min_dias_retrabalho": min_dias,
        "modelos_veiculos": lista_modelos,
        "oficinas": lista_oficinas,
        "secoes": lista_secaos,
        "os": lista_os,
        "dia_semana": dia_semana,
        "hora_disparar": horario_envio,
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
    }

    regra_criada_com_sucesso = crud_relatorio_service.criar_relatorio_monitoramento(payload)

    if regra_criada_com_sucesso:
        return [False, True]
    else:
        return [True, False]



##############################################################################
# Layout #####################################################################
##############################################################################
layout = dbc.Container(
    [
        dmc.Modal(
            # title="Erro ao carregar os dados",
            id="pag-criar-relatorio-modal-erro-salvar",
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
                            dmc.ListItem("Nome do relatório;"),
                            dmc.ListItem("Pelo menos um dia de alerta (Segunda, Terça, etc);"),
                            dmc.ListItem("Pelo menos um destino de email ou WhatsApp ativo."),
                        ],
                    ),
                    dmc.Group(
                        [
                            dmc.Button(
                                "Fechar",
                                color="red",
                                variant="outline",
                                id="pag-criar-relatorio-btn-close-modal-erro-salvar",
                            ),
                        ],
                    ),
                ],
                align="center",
                gap="md",
            ),
        ),
        dmc.Modal(
            # title="Erro ao carregar os dados",
            id="pag-criar-relatorio-modal-sucesso-salvar",
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
                                id="pag-criar-relatorio-btn-close-modal-sucesso-salvar",
                            ),
                        ],
                        # justify="flex-end",
                    ),
                ],
                align="center",
                gap="md",
            ),
        ),
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
                                                    html.Strong("Período do relatório:"),
                                                    """
                                                    intervalo em que as OS serão analisadas. Também será analisado o
                                                    período anterior. Exemplo: um período de 7 dias indica que será 
                                                    analisado o retrabalho nos 7 dias anteriores, bem como da outra
                                                    semana (14 dias). A idéia é que isso permita avaliar a evolução
                                                    do retrabalho.
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
            ]
        ),
        # Cabeçalho e Inputs
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="carbon:rule-draft", width=45), width="auto"),
                dbc.Col(
                    html.H1(
                        [
                            "Criar \u00a0",
                            html.Strong("relatório LLM"),
                            "\u00a0 para monitoramento do retrabalho",
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
                                dbc.Label("Nome do Relatório"),
                                dbc.Input(
                                    id="pag-criar-relatorio-input-nome",
                                    type="text",
                                    placeholder="Ex: Relatório do Setor Elétrico...",
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
                                dbc.Label("Período (últimos X dias)"),
                                dbc.InputGroup(
                                    [
                                        dbc.Input(
                                            id="pag-criar-relatorio-input-periodo-dias-monitoramento",
                                            type="number",
                                            placeholder="Dias",
                                            value=7,
                                            step=1,
                                            min=1,
                                        ),
                                        dbc.InputGroupText("dias"),
                                    ]
                                ),
                                dmc.Space(h=5),
                                dbc.FormText(
                                    html.Em(
                                        "Período de análise do relatório"
                                    ),
                                    color="secondary",
                                ),
                            ],
                            className="dash-bootstrap",
                        ),
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
                                        id="pag-criar-relatorio-input-select-dias",
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
                                        id="pag-criar-relatorio-input-select-modelo-veiculos",
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
                    className="mb-3 mb-md-0",
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            html.Div(
                                [
                                    dbc.Label("Oficinas"),
                                    dcc.Dropdown(
                                        id="pag-criar-relatorio-input-select-oficina",
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
                                        id="pag-criar-relatorio-input-select-secao",
                                        options=[
                                            {"label": sec["LABEL"], "value": sec["LABEL"]} for sec in lista_todas_secoes
                                        ],
                                        multi=True,
                                        value=["MANUTENCAO ELETRICA"],
                                        placeholder="Selecione uma ou mais seções...",
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
                                    dbc.Label("Ordens de Serviço"),
                                    dcc.Dropdown(
                                        id="pag-criar-relatorio-input-select-ordens-servico",
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
                                    dbc.Label("Dia da semana:"),
                                    dbc.RadioItems(
                                        options=[
                                            {
                                                "label": "SEG",
                                                "value": 1,
                                            },
                                            {
                                                "label": "TER",
                                                "value": 2,
                                            },
                                            {
                                                "label": "QUA",
                                                "value": 3,
                                            },
                                            {
                                                "label": "QUI",
                                                "value": 4,
                                            },
                                            {
                                                "label": "SEX",
                                                "value": 5,
                                            },
                                            {
                                                "label": "SAB",
                                                "value": 6,
                                            },
                                            {
                                                "label": "DOM",
                                                "value": 0,
                                            },
                                        ],
                                        value=1,
                                        id="pag-criar-relatorio-checklist-dia-semana",
                                        inline=True,
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
                                    dbc.Label("Horário de envio:"),
                                    dmc.TimeInput(
                                        debounce=True, id="pag-criar-relatorio-horario-envio-regra", value="06:00"
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
                                        id="pag-criar-relatorio-switch-enviar-email",
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
                                                    id="pag-criar-relatorio-input-email-1",
                                                    placeholder="email1@odilonsantos.com",
                                                    value="",
                                                    leftSection=DashIconify(icon="mdi:email"),
                                                ),
                                                md=12,
                                            ),
                                            dmc.Space(h=10),
                                            dbc.Col(
                                                dmc.TextInput(
                                                    id="pag-criar-relatorio-input-email-2",
                                                    placeholder="email2@odilonsantos.com",
                                                    value="",
                                                    leftSection=DashIconify(icon="mdi:email"),
                                                ),
                                                md=12,
                                            ),
                                            dmc.Space(h=10),
                                            dbc.Col(
                                                dmc.TextInput(
                                                    id="pag-criar-relatorio-input-email-3",
                                                    placeholder="email3@odilonsantos.com",
                                                    value="",
                                                    leftSection=DashIconify(icon="mdi:email"),
                                                ),
                                                md=12,
                                            ),
                                            dmc.Space(h=10),
                                            dbc.Col(
                                                dmc.TextInput(
                                                    id="pag-criar-relatorio-input-email-4",
                                                    placeholder="email4@odilonsantos.com",
                                                    value="",
                                                    leftSection=DashIconify(icon="mdi:email"),
                                                ),
                                                md=12,
                                            ),
                                            dmc.Space(h=10),
                                            dbc.Col(
                                                dmc.TextInput(
                                                    id="pag-criar-relatorio-input-email-5",
                                                    placeholder="email5@odilonsantos.com",
                                                    value="",
                                                    leftSection=DashIconify(icon="mdi:email"),
                                                ),
                                                md=12,
                                            ),
                                        ],
                                        align="center",
                                    ),
                                    id="pag-criar-relatorio-input-email-destino-container",
                                    md=12,
                                ),
                            ],
                            align="center",
                        ),
                        body=True,
                    ),
                    md=6,
                    className="mb-3 mb-md-0",
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.Row(
                            [
                                dbc.Col(
                                    dmc.Switch(
                                        id="pag-criar-relatorio-switch-enviar-wpp-regra",
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
                                                    id="pag-criar-relatorio-input-wpp-1",
                                                    placeholder="(62) 99999-9999",
                                                    value="",
                                                    leftSection=DashIconify(icon="logos:whatsapp-icon"),
                                                ),
                                                md=12,
                                            ),
                                            dmc.Space(h=10),
                                            dbc.Col(
                                                dmc.TextInput(
                                                    id="pag-criar-relatorio-input-wpp-2",
                                                    placeholder="(62) 99999-9999",
                                                    value="",
                                                    leftSection=DashIconify(icon="logos:whatsapp-icon"),
                                                ),
                                                md=12,
                                            ),
                                            dmc.Space(h=10),
                                            dbc.Col(
                                                dmc.TextInput(
                                                    id="pag-criar-relatorio-input-wpp-3",
                                                    placeholder="(62) 99999-9999",
                                                    value="",
                                                    leftSection=DashIconify(icon="logos:whatsapp-icon"),
                                                ),
                                                md=12,
                                            ),
                                            dmc.Space(h=10),
                                            dbc.Col(
                                                dmc.TextInput(
                                                    id="pag-criar-relatorio-input-wpp-4",
                                                    placeholder="(62) 99999-9999",
                                                    value="",
                                                    leftSection=DashIconify(icon="logos:whatsapp-icon"),
                                                ),
                                                md=12,
                                            ),
                                            dmc.Space(h=10),
                                            dbc.Col(
                                                dmc.TextInput(
                                                    id="pag-criar-relatorio-input-wpp-5",
                                                    placeholder="(62) 99999-9999",
                                                    value="",
                                                    leftSection=DashIconify(icon="logos:whatsapp-icon"),
                                                ),
                                                md=12,
                                            ),
                                        ],
                                        align="center",
                                    ),
                                    id="pag-criar-relatorio-input-wpp-destino-container",
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
                        "Criar Regra",
                        id="pag-criar-relatorio-btn-salvar-regra",
                        color="success",
                        className="me-1",
                        style={"padding": "1em", "width": "100%"},
                    ),
                    md=12,
                ),
            ],
            justify="center",
        ),
        dmc.Space(h=100),
    ]
)


##############################################################################
# Registro da página #########################################################
##############################################################################
dash.register_page(__name__, name="Criar Regra", path="/relatorio-criar", icon="carbon:rule-draft", hide_page=True)
