#!/usr/bin/env python
# coding: utf-8

# Dashboard que lista o retrabalho de uma ou mais OS

##############################################################################
# IMPORTS ####################################################################
##############################################################################
# Bibliotecas básicas
from datetime import date
import math
import numpy as np
import pandas as pd
import os
import re

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
import tema
import locale_utils

# Banco de Dados
from db import PostgresSingleton

##############################################################################
# LEITURA DE DADOS ###########################################################
##############################################################################
# Conexão com os bancos
pgDB = PostgresSingleton.get_instance()
pgEngine = pgDB.get_engine()

# Colaboradores / Mecânicos
df_mecanicos = pd.read_sql("SELECT * FROM colaboradores_frotas_os", pgEngine)

# Obtem a lista de OS
df_lista_os = pd.read_sql(
    """
    SELECT DISTINCT
       "DESCRICAO DA SECAO" as "SECAO",
       "DESCRICAO DO SERVICO" AS "LABEL"
    FROM 
        mat_view_retrabalho_10_dias mvrd 
    ORDER BY
        "DESCRICAO DO SERVICO"
    """,
    pgEngine,
)
lista_todas_os = df_lista_os.to_dict(orient="records")
lista_todas_os.insert(0, {"LABEL": "TODAS"})

# Tabela Top OS de Retrabalho
tbl_top_os_geral_retrabalho = [
    {"field": "DESCRICAO DA OFICINA", "headerName": "OFICINA", "pinned": "left", "minWidth": 200},
    {"field": "DESCRICAO DA SECAO", "headerName": "SEÇÃO", "minWidth": 200},
    {"field": "DESCRICAO DO SERVICO", "headerName": "SERVIÇO", "minWidth": 250},
    {
        "field": "TOTAL_OS",
        "headerName": "TOTAL DE OS",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "maxWidth": 160,
        "filter": "agNumberColumnFilter",
        "type": ["numericColumn"],
    },
    {
        "field": "PERC_RETRABALHO",
        "headerName": "% RETRABALHOS",
        "filter": "agNumberColumnFilter",
        "maxWidth": 160,
        "valueFormatter": {"function": "params.value.toLocaleString() + '%'"},
        "type": ["numericColumn"],
    },
    {
        "field": "PERC_CORRECAO_PRIMEIRA",
        "headerName": "% CORREÇÕES DE PRIMEIRA",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "filter": "agNumberColumnFilter",
        "maxWidth": 160,
        "valueFormatter": {"function": "params.value.toLocaleString() + '%'"},
        "type": ["numericColumn"],
    },
    {
        "field": "TOTAL_PROBLEMA",
        "headerName": "TOTAL DE PROBLEMA",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "filter": "agNumberColumnFilter",
        "maxWidth": 160,
        "type": ["numericColumn"],
    },
    {
        "field": "REL_OS_PROBLEMA",
        "headerName": "REL OS/PROBLEMA",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "maxWidth": 160,
        "valueFormatter": {"function": "params.value.toLocaleString()"},
        "filter": "agNumberColumnFilter",
        "type": ["numericColumn"],
    },
]

# Tabela Top OS Colaborador
tbl_top_colaborador_geral_retrabalho = [
    {"field": "NOME_COLABORADOR", "headerName": "Colaborador"},
    {"field": "ID_COLABORADOR", "headerName": "ID", "filter": "agNumberColumnFilter"},
    {
        "field": "TOTAL_OS",
        "headerName": "TOTAL DE OS",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "filter": "agNumberColumnFilter",
        "type": ["numericColumn"],
    },
    {
        "field": "PERC_RETRABALHO",
        "headerName": "% RETRABALHOS",
        "filter": "agNumberColumnFilter",
        "valueFormatter": {"function": "params.value.toLocaleString() + '%'"},
        "type": ["numericColumn"],
    },
    {
        "field": "PERC_CORRECAO_PRIMEIRA",
        "headerName": "% CORREÇÕES DE PRIMEIRA",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "filter": "agNumberColumnFilter",
        "valueFormatter": {"function": "params.value.toLocaleString() + '%'"},
        "type": ["numericColumn"],
    },
    {
        "field": "TOTAL_PROBLEMA",
        "headerName": "TOTAL DE PROBLEMA",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "filter": "agNumberColumnFilter",
        "type": ["numericColumn"],
    },
    {
        "field": "REL_OS_PROBLEMA",
        "headerName": "REL OS/PROBLEMA",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "valueFormatter": {"function": "params.value.toLocaleString()"},
        "filter": "agNumberColumnFilter",
        "type": ["numericColumn"],
    },
]


##############################################################################
# CALLBACKS ##################################################################
##############################################################################

##############################################################################
# Callbacks para os inputs ##################################################
##############################################################################


# Função para validar o input
def input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os):
    if datas is None or not datas or None in datas or min_dias is None:
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
    Output("input-select-oficina-visao-geral", "value"),
    Input("input-select-oficina-visao-geral", "value"),
)
def corrige_input_oficina(lista_oficinas):
    return corrige_input(lista_oficinas)


@callback(
    Output("input-select-secao-visao-geral", "value"),
    Input("input-select-secao-visao-geral", "value"),
)
def corrige_input_secao(lista_secaos):
    return corrige_input(lista_secaos)


@callback(
    [
        Output("input-select-ordens-servico-visao-geral", "options"),
        Output("input-select-ordens-servico-visao-geral", "value"),
    ],
    [
        Input("input-select-ordens-servico-visao-geral", "value"),
        Input("input-select-secao-visao-geral", "value"),
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


# Subqueries para filtrar as oficinas, seções e ordens de serviço quando TODAS não for selecionado
def subquery_oficinas(lista_oficinas, prefix=""):
    query = ""
    if "TODAS" not in lista_oficinas:
        query = f"""AND {prefix}"DESCRICAO DA OFICINA" IN ({', '.join([f"'{x}'" for x in lista_oficinas])})"""

    return query


def subquery_secoes(lista_secaos, prefix=""):
    query = ""
    if "TODAS" not in lista_secaos:
        query = f"""AND {prefix}"DESCRICAO DA SECAO" IN ({', '.join([f"'{x}'" for x in lista_secaos])})"""

    return query


def subquery_os(lista_os, prefix=""):
    query = ""
    if "TODAS" not in lista_os:
        query = f"""AND {prefix}"DESCRICAO DO SERVICO" IN ({', '.join([f"'{x}'" for x in lista_os])})"""

    return query


##############################################################################
# Callbacks para os gráficos ################################################
##############################################################################


# Callback para o grafico de síntese do retrabalho
@callback(
    Output("graph-pizza-sintese-retrabalho-geral", "figure"),
    [
        Input("input-intervalo-datas-geral", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
        Input("input-select-oficina-visao-geral", "value"),
        Input("input-select-secao-visao-geral", "value"),
        Input("input-select-ordens-servico-visao-geral", "value"),
    ],
)
def plota_grafico_pizza_sintese_geral(datas, min_dias, lista_oficinas, lista_secaos, lista_os):
    # Valida input
    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os):
        return go.Figure()

    # Datas
    data_inicio_str = datas[0]

    # Remove min_dias antes para evitar que a última OS não seja retrabalho
    data_fim = pd.to_datetime(datas[1])
    data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
    data_fim_str = data_fim.strftime("%Y-%m-%d")

    # Subqueries
    subquery_oficinas_str = subquery_oficinas(lista_oficinas)
    subquery_secoes_str = subquery_secoes(lista_secaos)
    subquery_os_str = subquery_os(lista_os)

    # Query
    query = f"""
        SELECT
            COUNT(*) AS "TOTAL_NUM_OS",
            SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END) AS "TOTAL_RETRABALHO",
            SUM(CASE WHEN correcao THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO",
            SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO_PRIMEIRA",
            100 * ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
            100 * ROUND(SUM(CASE WHEN correcao THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO",
            100 * ROUND(SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA"
        FROM
            mat_view_retrabalho_{min_dias}_dias
        WHERE
            "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            {subquery_oficinas_str}
            {subquery_secoes_str}
            {subquery_os_str}
    """

    # Executa a query
    df = pd.read_sql(query, pgEngine)

    # Calcula o total de correções tardia
    df["TOTAL_CORRECAO_TARDIA"] = df["TOTAL_CORRECAO"] - df["TOTAL_CORRECAO_PRIMEIRA"]

    # Prepara os dados para o gráfico
    labels = ["Correções de Primeira", "Correções Tardias", "Retrabalhos"]
    values = [
        df["TOTAL_CORRECAO_PRIMEIRA"].values[0],
        df["TOTAL_CORRECAO_TARDIA"].values[0],
        df["TOTAL_RETRABALHO"].values[0],
    ]

    # Gera o gráfico
    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                direction="clockwise",
                marker_colors=[tema.COR_SUCESSO, tema.COR_ALERTA, tema.COR_ERRO],
                sort=True,
            )
        ]
    )

    # Arruma legenda e texto
    fig.update_traces(textinfo="value+percent", sort=False)

    # Total numérico de OS, para o título
    total_num_os = df["TOTAL_NUM_OS"].values[0]
    total_num_os_str = f"{total_num_os:,}".replace(",", ".")
    fig.update_layout(
        title=dict(
            text=f"Total de OS: {total_num_os_str}",
            y=0.97,  # Posição vertical do título
            x=0.5,  # Centraliza o título horizontalmente
            xanchor="center",
            yanchor="top",
            font=dict(size=18),  # Tamanho do texto
        ),
        separators=",.",
    )

    # Remove o espaçamento em torno do gráfico
    fig.update_layout(
        margin=dict(t=40, b=0),  # Remove as margens
        height=320,  # Ajuste conforme necessário
        legend=dict(
            orientation="h",  # Legenda horizontal
            yanchor="top",  # Ancora no topo
            xanchor="center",  # Centraliza
            y=-0.1,  # Coloca abaixo
            x=0.5,  # Alinha com o centro
        ),
    )

    # Retorna o gráfico
    return fig


# Callback para o grafico por modelo
@callback(
    Output("graph-visao-geral-por-modelo", "figure"),
    [
        Input("input-intervalo-datas-geral", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
        Input("input-select-oficina-visao-geral", "value"),
        Input("input-select-secao-visao-geral", "value"),
        Input("input-select-ordens-servico-visao-geral", "value"),
    ],
)
def plota_grafico_por_modelo(datas, min_dias, lista_oficinas, lista_secaos, lista_os):
    # Valida input
    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os):
        return go.Figure()

    # Datas
    data_inicio_str = datas[0]

    # Remove min_dias antes para evitar que a última OS não seja retrabalho
    data_fim = pd.to_datetime(datas[1])
    data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
    data_fim_str = data_fim.strftime("%Y-%m-%d")

    # Subqueries
    subquery_oficinas_str = subquery_oficinas(lista_oficinas)
    subquery_secoes_str = subquery_secoes(lista_secaos)
    subquery_os_str = subquery_os(lista_os)

    inner_subquery_oficinas_str = subquery_oficinas(lista_oficinas, "submat.")
    inner_subquery_secoes_str = subquery_secoes(lista_secaos, "submat.")
    inner_subquery_os_str = subquery_os(lista_os, "submat.")

    # Queries
    # Primeiro pegamos o total de veículos por modelo no período, não vamos restringir por problema
    query_total_frota = f"""
    SELECT 
        "DESCRICAO DO MODELO", 
        COUNT(DISTINCT "CODIGO DO VEICULO") AS "TOTAL_FROTA_PERIODO"
    FROM 
        mat_view_retrabalho_{min_dias}_dias
    WHERE
        "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
        {subquery_oficinas_str}
    GROUP BY 
        "DESCRICAO DO MODELO"
    """

    query_teve_problema = f"""
    SELECT 
        "DESCRICAO DO MODELO", 
        COUNT(DISTINCT "CODIGO DO VEICULO") AS "TOTAL_FROTA_TEVE_PROBLEMA"
    FROM 
        mat_view_retrabalho_{min_dias}_dias
    WHERE
        "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
        {subquery_oficinas_str}
        {subquery_secoes_str}
        {subquery_os_str}
    GROUP BY 
        "DESCRICAO DO MODELO"
    """

    query_teve_retrabalho = f"""
    SELECT 
        "DESCRICAO DO MODELO", 
        COUNT(DISTINCT "CODIGO DO VEICULO") AS "TOTAL_FROTA_TEVE_RETRABALHO"
    FROM 
        mat_view_retrabalho_{min_dias}_dias
    WHERE
        "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
        {subquery_oficinas_str}
        {subquery_secoes_str}
        {subquery_os_str}
        AND retrabalho = TRUE
    GROUP BY 
        "DESCRICAO DO MODELO"
    """

    # Executa Queries
    df_total_frota = pd.read_sql(query_total_frota, pgEngine)
    df_teve_problema = pd.read_sql(query_teve_problema, pgEngine)
    df_teve_retrabalho = pd.read_sql(query_teve_retrabalho, pgEngine)

    # Merge dos dataframes
    df = df_total_frota.merge(df_teve_problema, on="DESCRICAO DO MODELO", how="left")
    df = df.merge(df_teve_retrabalho, on="DESCRICAO DO MODELO", how="left")
    df.fillna(0, inplace=True)

    # Calcular campos
    df["NAO_TEVE_PROBLEMA"] = df["TOTAL_FROTA_PERIODO"] - df["TOTAL_FROTA_TEVE_PROBLEMA"]
    df["TEVE_PROBLEMA_SEM_RETRABALHO"] = df["TOTAL_FROTA_TEVE_PROBLEMA"] - df["TOTAL_FROTA_TEVE_RETRABALHO"]
    df["TEVE_PROBLEMA_E_RETRABALHO"] = df["TOTAL_FROTA_TEVE_RETRABALHO"]

    # Calcula as porcentagens
    df["PERC_NAO_TEVE_PROBLEMA"] = round(100 * df["NAO_TEVE_PROBLEMA"] / df["TOTAL_FROTA_PERIODO"], 1)
    df["PERC_TEVE_PROBLEMA_SEM_RETRABALHO"] = round(
        100 * df["TEVE_PROBLEMA_SEM_RETRABALHO"] / df["TOTAL_FROTA_PERIODO"], 1
    )
    df["PERC_TEVE_PROBLEMA_E_RETRABALHO"] = round(100 * df["TEVE_PROBLEMA_E_RETRABALHO"] / df["TOTAL_FROTA_PERIODO"], 1)

    # Gera o gráfico
    # Gera o gráfico
    bar_chart = px.bar(
        df,
        x="DESCRICAO DO MODELO",
        y=["PERC_NAO_TEVE_PROBLEMA", "PERC_TEVE_PROBLEMA_SEM_RETRABALHO", "PERC_TEVE_PROBLEMA_E_RETRABALHO"],
        barmode="stack",
        color_discrete_sequence=[tema.COR_SUCESSO, tema.COR_ALERTA, tema.COR_ERRO],
        labels={
            "value": "Percentagem",
            "DESCRICAO DO MODELO": "Modelo",
            "variable": "Status",
            "PERC_NAO_TEVE_PROBLEMA": "Não teve problema",
        },
    )

    # Atualizando os valores de rótulo para PERC_NAO_TEVE_PROBLEMA (percentual que não teve problema)
    bar_chart.update_traces(
        text=[
            f"{perc_nao_teve_prob:.0f}%<br>({nao_teve_prob:.0f})"
            for nao_teve_prob, perc_nao_teve_prob in zip(df["NAO_TEVE_PROBLEMA"], df["PERC_NAO_TEVE_PROBLEMA"])
        ],
        selector=dict(name="PERC_NAO_TEVE_PROBLEMA"),
    )

    # Atualizando os valores de rótulo para PERC_TEVE_PROBLEMA_SEM_RETRABALHO (percentual que teve problema, mas não retrabalho)
    bar_chart.update_traces(
        text=[
            f"{perc_teve_prob_sem_retrab:.0f}%<br>({teve_prob_sem_retrab:.0f})"
            for teve_prob_sem_retrab, perc_teve_prob_sem_retrab in zip(
                df["TEVE_PROBLEMA_SEM_RETRABALHO"], df["PERC_TEVE_PROBLEMA_SEM_RETRABALHO"]
            )
        ],
        selector=dict(name="PERC_TEVE_PROBLEMA_SEM_RETRABALHO"),
    )

    # Atualizando os valores de rótulo para PERC_RETRABALHO (percentual e valor absoluto de retrabalhos)
    bar_chart.update_traces(
        text=[
            f"{perc_teve_prob_e_retrab:.0f}%<br>({teve_prob_e_retrab:.0f})"
            for teve_prob_e_retrab, perc_teve_prob_e_retrab in zip(
                df["TEVE_PROBLEMA_E_RETRABALHO"], df["PERC_TEVE_PROBLEMA_E_RETRABALHO"]
            )
        ],
        selector=dict(name="PERC_TEVE_PROBLEMA_E_RETRABALHO"),
    )

    # Exibir os rótulos nas barras
    bar_chart.update_traces(texttemplate="%{text}")

    # Ajustar a margem inferior para evitar corte de rótulos
    bar_chart.update_layout(
        yaxis=dict(range=[0, 118]), margin=dict(t=10, b=200), height=500  # Adjust the upper limit as needed
    )

    # Separador numérico
    bar_chart.update_layout(separators=",.")

    # Retorna o gráfico
    return bar_chart


# Callbacks para o grafico de evolução do retrabalho por oficina
@callback(
    Output("graph-evolucao-retrabalho-por-garagem-por-mes", "figure"),
    [
        Input("input-intervalo-datas-geral", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
        Input("input-select-oficina-visao-geral", "value"),
        Input("input-select-secao-visao-geral", "value"),
        Input("input-select-ordens-servico-visao-geral", "value"),
    ],
)
def plota_grafico_evolucao_retrabalho_por_oficina_por_mes(datas, min_dias, lista_oficinas, lista_secaos, lista_os):
    # Valida input
    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os):
        return go.Figure()

    # Datas
    data_inicio_str = datas[0]

    # Remove min_dias antes para evitar que a última OS não seja retrabalho
    data_fim = pd.to_datetime(datas[1])
    data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
    data_fim_str = data_fim.strftime("%Y-%m-%d")

    # Subqueries
    subquery_oficinas_str = subquery_oficinas(lista_oficinas)
    subquery_secoes_str = subquery_secoes(lista_secaos)
    subquery_os_str = subquery_os(lista_os)

    query = f"""
    SELECT
        to_char(to_timestamp("DATA DE FECHAMENTO DO SERVICO", 'YYYY-MM-DD"T"HH24:MI:SS'), 'YYYY-MM') AS year_month,
        "DESCRICAO DA OFICINA",
        100 * ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
        100 * ROUND(SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA"
    FROM
        mat_view_retrabalho_{min_dias}_dias
    WHERE
        "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
        {subquery_oficinas_str}
        {subquery_secoes_str}
        {subquery_os_str}
    GROUP BY
        year_month, "DESCRICAO DA OFICINA"
    ORDER BY
        year_month;
    """

    # Executa query
    df = pd.read_sql(query, pgEngine)

    # Arruma dt
    df["year_month_dt"] = pd.to_datetime(df["year_month"], format="%Y-%m", errors="coerce")

    # Funde (melt) colunas de retrabalho e correção
    df_combinado = df.melt(
        id_vars=["year_month_dt", "DESCRICAO DA OFICINA"],
        value_vars=["PERC_RETRABALHO", "PERC_CORRECAO_PRIMEIRA"],
        var_name="CATEGORIA",
        value_name="PERC",
    )

    # Renomeia as colunas
    df_combinado["CATEGORIA"] = df_combinado["CATEGORIA"].replace(
        {"PERC_RETRABALHO": "RETRABALHO", "PERC_CORRECAO_PRIMEIRA": "CORRECAO_PRIMEIRA"}
    )

    # Gera o gráfico
    fig = px.line(
        df_combinado,
        x="year_month_dt",
        y="PERC",
        color="DESCRICAO DA OFICINA",
        facet_col="CATEGORIA",
        facet_col_spacing=0.05,  # Espaçamento entre os gráficos
        labels={"DESCRICAO DA OFICINA": "Oficina", "year_month_dt": "Ano-Mês", "PERC": "%"},
        markers=True,
    )

    # Coloca % no eixo y
    fig.update_yaxes(tickformat=".0f%")

    # Renomeia o eixo y
    fig.update_layout(
        yaxis=dict(
            title="% Retrabalho",
        ),
        yaxis2=dict(
            title="% Correção de Primeira",
            overlaying="y",
            side="right",
            anchor="x",
        ),
        margin=dict(b=100),
    )

    # Titulo
    fig.update_layout(
        annotations=[
            dict(
                text="Retrabalho por oficina (% das OS)",
                x=0.25,  # Posição X para o primeiro plot
                y=1.05,  # Posição Y (em cima do plot)
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=16),
            ),
            dict(
                text="Correção de primeira por oficina (% das OS)",
                x=0.75,  # Posição X para o segundo plot
                y=1.05,  # Posição Y (em cima do plot)
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=16),
            ),
        ]
    )

    # Gera ticks todo mês
    fig.update_xaxes(dtick="M1", tickformat="%Y-%b", title_text="Ano-Mês", title_standoff=90)

    # Aumenta o espaçamento do titulo
    fig.for_each_xaxis(lambda axis: axis.update(title_standoff=90))  # Increase standoff for spacing

    # Ajusta a altura do gráfico
    # fig.update_layout(
    #     height=400,  # Define a altura do gráfico
    # )

    return fig


# Callbacks para o grafico de evolução do retrabalho por seção
@callback(
    Output("graph-evolucao-retrabalho-por-secao-por-mes", "figure"),
    [
        Input("input-intervalo-datas-geral", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
        Input("input-select-oficina-visao-geral", "value"),
        Input("input-select-secao-visao-geral", "value"),
        Input("input-select-ordens-servico-visao-geral", "value"),
    ],
)
def plota_grafico_evolucao_retrabalho_por_secao_por_mes(datas, min_dias, lista_oficinas, lista_secaos, lista_os):
    # Valida input
    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os):
        return go.Figure()

    # Datas
    data_inicio_str = datas[0]

    # Remove min_dias antes para evitar que a última OS não seja retrabalho
    data_fim = pd.to_datetime(datas[1])
    data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
    data_fim_str = data_fim.strftime("%Y-%m-%d")

    # Subqueries
    subquery_oficinas_str = subquery_oficinas(lista_oficinas)
    subquery_secoes_str = subquery_secoes(lista_secaos)
    subquery_os_str = subquery_os(lista_os)

    query = f"""
    SELECT
        to_char(to_timestamp("DATA DE FECHAMENTO DO SERVICO", 'YYYY-MM-DD"T"HH24:MI:SS'), 'YYYY-MM') AS year_month,
        "DESCRICAO DA SECAO",
        100 * ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
        100 * ROUND(SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA"
    FROM
        mat_view_retrabalho_{min_dias}_dias
    WHERE
        "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
        {subquery_oficinas_str}
        {subquery_secoes_str}
        {subquery_os_str}
    GROUP BY
        year_month, "DESCRICAO DA SECAO"
    ORDER BY
        year_month;
    """

    # Executa Query
    df = pd.read_sql(query, pgEngine)

    # Arruma dt
    df["year_month_dt"] = pd.to_datetime(df["year_month"], format="%Y-%m", errors="coerce")

    # Funde (melt) colunas de retrabalho e correção
    df_combinado = df.melt(
        id_vars=["year_month_dt", "DESCRICAO DA SECAO"],
        value_vars=["PERC_RETRABALHO", "PERC_CORRECAO_PRIMEIRA"],
        var_name="CATEGORIA",
        value_name="PERC",
    )

    # Renomeia as colunas
    df_combinado["CATEGORIA"] = df_combinado["CATEGORIA"].replace(
        {"PERC_RETRABALHO": "RETRABALHO", "PERC_CORRECAO_PRIMEIRA": "CORRECAO_PRIMEIRA"}
    )

    # Multiplica por 100
    # df_combinado["PERC"] = df_combinado["PERC"] * 100

    # Gera o gráfico
    fig = px.line(
        df_combinado,
        x="year_month_dt",
        y="PERC",
        color="DESCRICAO DA SECAO",
        facet_col="CATEGORIA",
        facet_col_spacing=0.05,  # Espaçamento entre os gráficos
        labels={"DESCRICAO DA SECAO": "Seção", "year_month_dt": "Ano-Mês", "PERC": "%"},
        markers=True,
    )

    # Coloca % no eixo y
    fig.update_yaxes(tickformat=".0f%")

    # Renomeia o eixo y
    fig.update_layout(
        yaxis=dict(
            title="% Retrabalho",
        ),
        yaxis2=dict(
            title="% Correção de Primeira",
            overlaying="y",
            side="right",
            anchor="x",
        ),
        margin=dict(b=100),
    )

    # Titulo
    fig.update_layout(
        annotations=[
            dict(
                text="Retrabalho por seção (% das OS)",
                x=0.25,  # Posição X para o primeiro plot
                y=1.05,  # Posição Y (em cima do plot)
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=16),
            ),
            dict(
                text="Correção de primeira por seção (% das OS)",
                x=0.75,  # Posição X para o segundo plot
                y=1.05,  # Posição Y (em cima do plot)
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=16),
            ),
        ]
    )

    # Gera ticks todo mês
    fig.update_xaxes(dtick="M1", tickformat="%Y-%b", title_text="Ano-Mês", title_standoff=90)

    # Aumenta o espaçamento do titulo
    fig.for_each_xaxis(lambda axis: axis.update(title_standoff=90))  # Increase standoff for spacing

    return fig


@callback(
    Output("tabela-top-os-retrabalho-geral", "rowData"),
    [
        Input("input-intervalo-datas-geral", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
        Input("input-select-oficina-visao-geral", "value"),
        Input("input-select-secao-visao-geral", "value"),
        Input("input-select-ordens-servico-visao-geral", "value"),
    ],
    running=[(Output("loading-overlay-guia-geral", "visible"), True, False)],
)
def atualiza_tabela_top_os_geral_retrabalho(datas, min_dias, lista_oficinas, lista_secaos, lista_os):
    # Valida input
    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os):
        return []

    # Datas
    data_inicio_str = datas[0]

    # Remove min_dias antes para evitar que a última OS não seja retrabalho
    data_fim = pd.to_datetime(datas[1])
    data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
    data_fim_str = data_fim.strftime("%Y-%m-%d")

    # Subqueries
    subquery_oficinas_str = subquery_oficinas(lista_oficinas)
    subquery_secoes_str = subquery_secoes(lista_secaos)
    subquery_os_str = subquery_os(lista_os)

    inner_subquery_oficinas_str = subquery_oficinas(lista_oficinas, "main.")
    inner_subquery_secoes_str = subquery_secoes(lista_secaos, "main.")
    inner_subquery_os_str = subquery_os(lista_os, "main.")

    query = f"""
    WITH normaliza_problema AS (
        SELECT
            "DESCRICAO DA OFICINA",
            "DESCRICAO DA SECAO",
            "DESCRICAO DO SERVICO" as servico,
            "CODIGO DO VEICULO",
            "problem_no"
        FROM
            mat_view_retrabalho_{min_dias}_dias
        WHERE
            "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            {subquery_oficinas_str}
            {subquery_secoes_str}
            {subquery_os_str}
        GROUP BY
            "DESCRICAO DA OFICINA",
            "DESCRICAO DA SECAO",
            "DESCRICAO DO SERVICO",
            "CODIGO DO VEICULO",
            "problem_no"
    ),
    os_problema AS (
        SELECT
            "DESCRICAO DA OFICINA",
            "DESCRICAO DA SECAO",
            servico,
            COUNT(*) AS num_problema
        FROM
            normaliza_problema
        GROUP BY
            "DESCRICAO DA OFICINA",
            "DESCRICAO DA SECAO",
            servico
    )
    SELECT
        main."DESCRICAO DA OFICINA",
        main."DESCRICAO DA SECAO",
        main."DESCRICAO DO SERVICO",
        COUNT(*) AS "TOTAL_OS",
        SUM(CASE WHEN main.retrabalho THEN 1 ELSE 0 END) AS "TOTAL_RETRABALHO",
        SUM(CASE WHEN main.correcao THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO",
        SUM(CASE WHEN main.correcao_primeira THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO_PRIMEIRA",
        100 * ROUND(SUM(CASE WHEN main.retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
        100 * ROUND(SUM(CASE WHEN main.correcao THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO",
        100 * ROUND(SUM(CASE WHEN main.correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA",
        COALESCE(op.num_problema, 0) AS "TOTAL_PROBLEMA"
    FROM
        mat_view_retrabalho_{min_dias}_dias main
    LEFT JOIN
        os_problema op
    ON
        main."DESCRICAO DA OFICINA" = op."DESCRICAO DA OFICINA"
        AND main."DESCRICAO DA SECAO" = op."DESCRICAO DA SECAO"
        AND main."DESCRICAO DO SERVICO" = op.servico
    WHERE
        main."DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
        {inner_subquery_oficinas_str}
        {inner_subquery_secoes_str}
        {inner_subquery_os_str}
    GROUP BY
        main."DESCRICAO DA OFICINA",
        main."DESCRICAO DA SECAO",
        main."DESCRICAO DO SERVICO",
        op.num_problema
    ORDER BY
        "PERC_RETRABALHO" DESC;
    """

    # Executa a query
    df = pd.read_sql(query, pgEngine)

    df["REL_OS_PROBLEMA"] = round(df["TOTAL_OS"] / df["TOTAL_PROBLEMA"], 2)

    return df.to_dict("records")


@callback(
    Output("tabela-top-os-colaborador-geral", "rowData"),
    [
        Input("input-intervalo-datas-geral", "value"),
        Input("input-select-dias-geral-retrabalho", "value"),
        Input("input-select-oficina-visao-geral", "value"),
        Input("input-select-secao-visao-geral", "value"),
        Input("input-select-ordens-servico-visao-geral", "value"),
    ],
)
def atualiza_tabela_top_colaboradores_geral_retrabalho(datas, min_dias, lista_oficinas, lista_secaos, lista_os):
    # Valida input
    if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os):
        return []

    # Datas
    data_inicio_str = datas[0]

    # Remove min_dias antes para evitar que a última OS não seja retrabalho
    data_fim = pd.to_datetime(datas[1])
    data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
    data_fim_str = data_fim.strftime("%Y-%m-%d")

    # Subqueries
    subquery_oficinas_str = subquery_oficinas(lista_oficinas)
    subquery_secoes_str = subquery_secoes(lista_secaos)
    subquery_os_str = subquery_os(lista_os)

    inner_subquery_oficinas_str = subquery_oficinas(lista_oficinas, "main.")
    inner_subquery_secoes_str = subquery_secoes(lista_secaos, "main.")
    inner_subquery_os_str = subquery_os(lista_os, "main.")

    query = f"""
        WITH normaliza_problema AS (
            SELECT
                "COLABORADOR QUE EXECUTOU O SERVICO" AS colaborador,
                "DESCRICAO DO SERVICO",
                "CODIGO DO VEICULO",
                "problem_no"
            FROM
                mat_view_retrabalho_{min_dias}_dias
            WHERE
                "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                {subquery_oficinas_str}
                {subquery_secoes_str}
                {subquery_os_str}
            GROUP BY
                "COLABORADOR QUE EXECUTOU O SERVICO",
                "DESCRICAO DO SERVICO",
                "CODIGO DO VEICULO",
                "problem_no"
        ),
        colaborador_problema AS (
            SELECT 
                colaborador, 
                COUNT(*) AS num_problema
            FROM 
                normaliza_problema
            GROUP BY 
                colaborador
        )
        SELECT
            main."COLABORADOR QUE EXECUTOU O SERVICO",
            COUNT(*) AS "TOTAL_OS",
            SUM(CASE WHEN main.retrabalho THEN 1 ELSE 0 END) AS "TOTAL_RETRABALHO",
            SUM(CASE WHEN main.correcao THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO",
            SUM(CASE WHEN main.correcao_primeira THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO_PRIMEIRA",
            100 * ROUND(SUM(CASE WHEN main.retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
            100 * ROUND(SUM(CASE WHEN main.correcao THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO",
            100 * ROUND(SUM(CASE WHEN main.correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA",
            COALESCE(cp.num_problema, 0) AS "TOTAL_PROBLEMA"
        FROM
            mat_view_retrabalho_{min_dias}_dias main
        LEFT JOIN
            colaborador_problema cp
            ON
            main."COLABORADOR QUE EXECUTOU O SERVICO" = cp.colaborador
        WHERE
            main."DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            {inner_subquery_oficinas_str}
            {inner_subquery_secoes_str}
            {inner_subquery_os_str}
        GROUP BY
            main."COLABORADOR QUE EXECUTOU O SERVICO",
            cp.num_problema
        ORDER BY
            "PERC_RETRABALHO" DESC;
    """

    # Executa Query
    df = pd.read_sql(query, pgEngine)

    df["REL_OS_PROBLEMA"] = round(df["TOTAL_OS"] / df["TOTAL_PROBLEMA"], 2)

    # Adiciona label de nomes
    df["COLABORADOR QUE EXECUTOU O SERVICO"] = df["COLABORADOR QUE EXECUTOU O SERVICO"].astype(int)

    # Encontra o nome do colaborador
    for ix, linha in df.iterrows():
        colaborador = linha["COLABORADOR QUE EXECUTOU O SERVICO"]
        nome_colaborador = "Não encontrado"
        if colaborador in df_mecanicos["cod_colaborador"].values:
            nome_colaborador = df_mecanicos[df_mecanicos["cod_colaborador"] == colaborador]["nome_colaborador"].values[
                0
            ]
            nome_colaborador = re.sub(r"(?<!^)([A-Z])", r" \1", nome_colaborador)

        df.at[ix, "LABEL_COLABORADOR"] = f"{nome_colaborador} - {int(colaborador)}"
        df.at[ix, "NOME_COLABORADOR"] = f"{nome_colaborador}"
        df.at[ix, "ID_COLABORADOR"] = int(colaborador)

    return df.to_dict("records")


##############################################################################
### Callbacks para os labels #################################################
##############################################################################


def gera_labels_inputs(campo):
    # Cria o callback
    @callback(
        [
            Output(component_id=f"{campo}-labels", component_property="children"),
        ],
        [
            Input("input-select-dias-geral-retrabalho", "value"),
            Input(component_id="input-select-oficina-visao-geral", component_property="value"),
            Input(component_id="input-select-secao-visao-geral", component_property="value"),
            Input(component_id="input-select-ordens-servico-visao-geral", component_property="value"),
        ],
    )
    def atualiza_labels_inputs(min_dias, lista_oficinas, lista_secaos, lista_os):
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


##############################################################################
# Registro da página #########################################################
##############################################################################
dash.register_page(__name__, name="Visão Geral", path="/", icon="mdi:bus-alert")


##############################################################################
# Layout #####################################################################
##############################################################################
layout = dbc.Container(
    [
        # Loading
        dmc.LoadingOverlay(
            visible=True,
            id="loading-overlay-guia-geral",
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
                                        dbc.Col(DashIconify(icon="mdi:bus-alert", width=45), width="auto"),
                                        dbc.Col(
                                            html.H1(
                                                [
                                                    "Visão geral do\u00a0",
                                                    html.Strong("retrabalho"),
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
                                                        id="input-intervalo-datas-geral",
                                                        allowSingleDateInRange=True,
                                                        type="range",
                                                        minDate=date(2024, 1, 1),
                                                        maxDate=date.today(),
                                                        value=[date(2024, 1, 1), date.today()],
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
                                                        id="input-select-dias-geral-retrabalho",
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
                                                    dbc.Label("Oficinas"),
                                                    dcc.Dropdown(
                                                        id="input-select-oficina-visao-geral",
                                                        options=[
                                                            {"label": "TODAS", "value": "TODAS"},
                                                            {
                                                                "label": "GARAGEM CENTRAL",
                                                                "value": "GARAGEM CENTRAL - RAL",
                                                            },
                                                            {
                                                                "label": "GARAGEM NOROESTE",
                                                                "value": "GARAGEM NOROESTE - RAL",
                                                            },
                                                            {
                                                                "label": "GARAGEM SUL",
                                                                "value": "GARAGEM SUL - RAL",
                                                            },
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
                                                        id="input-select-secao-visao-geral",
                                                        options=[
                                                            {"label": "TODAS", "value": "TODAS"},
                                                            {
                                                                "label": "BORRACHARIA",
                                                                "value": "MANUTENCAO BORRACHARIA",
                                                            },
                                                            {
                                                                "label": "ELETRICA",
                                                                "value": "MANUTENCAO ELETRICA",
                                                            },
                                                            {"label": "GARAGEM", "value": "MANUTENÇÃO GARAGEM"},
                                                            {
                                                                "label": "LANTERNAGEM",
                                                                "value": "MANUTENCAO LANTERNAGEM",
                                                            },
                                                            {"label": "LUBRIFICAÇÃO", "value": "LUBRIFICAÇÃO"},
                                                            {
                                                                "label": "MECANICA",
                                                                "value": "MANUTENCAO MECANICA",
                                                            },
                                                            {"label": "PINTURA", "value": "MANUTENCAO PINTURA"},
                                                            {
                                                                "label": "SERVIÇOS DE TERCEIROS",
                                                                "value": "SERVIÇOS DE TERCEIROS",
                                                            },
                                                            {
                                                                "label": "SETOR DE ALINHAMENTO",
                                                                "value": "SETOR DE ALINHAMENTO",
                                                            },
                                                            {
                                                                "label": "SETOR DE POLIMENTO",
                                                                "value": "SETOR DE POLIMENTO",
                                                            },
                                                        ],
                                                        multi=True,
                                                        value=["TODAS"],
                                                        placeholder="Selecione uma ou mais seções...",
                                                    ),
                                                ],
                                                # className="dash-bootstrap",
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
                                                        id="input-select-ordens-servico-visao-geral",
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
                            dcc.Graph(id="graph-pizza-sintese-retrabalho-geral"),
                        ]
                    ),
                    md=4,
                ),
            ]
        ),
        # Gráfico de Retrabalho por Modelo
        dmc.Space(h=30),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="mdi:fleet", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Quantitativo da frota que teve problema e retrabalho por modelo",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            gera_labels_inputs("visao-geral-quanti-frota"),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        dcc.Graph(id="graph-visao-geral-por-modelo"),
        dmc.Space(h=40),
        # Graficos de Evolução do Retrabalho por Garagem e Seção
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="fluent:arrow-trending-wrench-20-filled", width=45), width="auto"),
                # dbc.Col(html.H4("Evolução do retrabalho por oficina / mês", className="align-self-center"), width=True),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Evolução do retrabalho por oficina / mês",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            gera_labels_inputs("visao-geral-evolucao-por-oficina"),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        dcc.Graph(id="graph-evolucao-retrabalho-por-garagem-por-mes"),
        dmc.Space(h=40),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="fluent:arrow-trending-text-20-filled", width=45), width="auto"),
                # dbc.Col(html.H4("Evolução do retrabalho por seção / mês", className="align-self-center"), width=True),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Evolução do retrabalho por seção / mês",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            gera_labels_inputs("visao-geral-evolucao-por-secao"),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        dcc.Graph(id="graph-evolucao-retrabalho-por-secao-por-mes"),
        dmc.Space(h=40),
        # Tabela com as estatísticas gerais de Retrabalho
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="fluent:line-horizontal-4-search-16-filled", width=45), width="auto"),
                # dbc.Col(html.H4("Detalhamento por tipo de OS (serviço)", className="align-self-center"), width=True),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Detalhamento por tipo de OS (serviço)",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            gera_labels_inputs("visao-geral-tabela-tipo-os"),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        dmc.Space(h=20),
        dag.AgGrid(
            # enableEnterpriseModules=True,
            id="tabela-top-os-retrabalho-geral",
            columnDefs=tbl_top_os_geral_retrabalho,
            rowData=[],
            defaultColDef={"filter": True, "floatingFilter": True},
            columnSize="autoSize",
            dashGridOptions={
                "localeText": locale_utils.AG_GRID_LOCALE_BR,
            },
        ),
        dmc.Space(h=40),
        # Tabela com as estatísticas gerais por Colaborador
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="mdi:account-wrench", width=45), width="auto"),
                # dbc.Col(
                #     html.H4("Detalhamento por colaborador das OSs escolhidas", className="align-self-center"),
                #     width=True,
                # ),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Detalhamento por colaborador das OSs escolhidas",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            gera_labels_inputs("visao-geral-tabela-colaborador-os"),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        dmc.Space(h=20),
        dag.AgGrid(
            id="tabela-top-os-colaborador-geral",
            columnDefs=tbl_top_colaborador_geral_retrabalho,
            rowData=[],
            defaultColDef={"filter": True, "floatingFilter": True},
            columnSize="responsiveSizeToFit",
            dashGridOptions={
                "localeText": locale_utils.AG_GRID_LOCALE_BR,
            },
        ),
        dmc.Space(h=40),
    ]
)
