#!/usr/bin/env python
# coding: utf-8

# Funções utilitárias para gerar os gráficos do detalhamento de uma OS

# Imports básicos
import math
import pandas as pd
import numpy as np

# Imports gráficos
import plotly.express as px
import plotly.graph_objects as go

# Imports do tema
import tema


# Rotinas para gerar os Gráficos
def gerar_grafico_gantt_historico_problema_detalhamento_os(df, problem_no, buffer_dias=2):
    """Gera o gráfico de gantt com o histórico do problema da OS"""

    # Seta colunas como dt
    df["DATA DA ABERTURA DA OS DT"] = pd.to_datetime(df["DATA DA ABERTURA DA OS DT"])
    df["DATA DO FECHAMENTO DA OS DT"] = pd.to_datetime(df["DATA DO FECHAMENTO DA OS DT"])

    # Agrega por problema e calcula a data de início e fim
    df_agg = (
        df.groupby("problem_no")
        .agg(
            {
                "DATA DA ABERTURA DA OS DT": "min",
                "DATA DO FECHAMENTO DA OS DT": "max",
                "problem_no": "count",  # count how many rows
            }
        )
        .rename(columns={"problem_no": "os_count"})
        .reset_index()
    )

    # Adiciona labels e duração
    df_agg["problem_no_label"] = "Problema " + df_agg["problem_no"].astype(str)
    df_agg["duracao_dias"] = (df_agg["DATA DO FECHAMENTO DA OS DT"] - df_agg["DATA DA ABERTURA DA OS DT"]).dt.days

    # Adiciona uma borda de 2 dias para facilitar a visualização
    border = pd.Timedelta(days=buffer_dias)
    df_agg["DATA DA ABERTURA PAD"] = df_agg["DATA DA ABERTURA DA OS DT"] - border
    df_agg["DATA DO FECHAMENTO PAD"] = df_agg["DATA DO FECHAMENTO DA OS DT"] + border

    # Gerá o gráfico
    # Ver + aqui: https://plotly.com/python/gantt/
    fig = px.timeline(
        df_agg,
        x_start="DATA DA ABERTURA PAD",
        x_end="DATA DO FECHAMENTO PAD",
        y="problem_no_label",
        color="problem_no_label",
        color_discrete_sequence=tema.PALETA_CORES_DISCRETA,
        custom_data=[
            "problem_no",
            "DATA DA ABERTURA DA OS DT",
            "DATA DO FECHAMENTO DA OS DT",
            "os_count",
            "duracao_dias",
        ],
    )

    fig.update_traces(
        hovertemplate=(
            "Problema: %{customdata[0]}<br>"
            "Início: %{customdata[1]|%H:%M %d/%m/%Y}<br>"
            "Fim: %{customdata[2]|%H:%M %d/%m/%Y}<br>"
            "Total de OS: %{customdata[3]}<br>"
            "Duração: %{customdata[4]} dias"
            "<extra></extra>"
        ),
    )

    fig.update_yaxes(
        autorange="reversed",
        title="",
        # showticklabels=False
    )

    # # abre um “respiro” à esquerda e à direita para evitar sobreposição com o eixo y
    # pad_label = pd.Timedelta(days=5)
    # xmin = df_agg["DATA DA ABERTURA PAD"].min() - pad_label
    # xmax = df_agg["DATA DO FECHAMENTO PAD"].max() + pad_label
    # fig.update_xaxes(range=[xmin, xmax])

    # deixa com cara de gantt e ajusta margens
    fig.update_layout(
        # margin=dict(l=240),
        legend_title_text="Legenda"
    )  # aumenta a margem esquerda se ainda estiver apertado

    # Destaca o problema mencionado
    target_label = f"Problema {problem_no}"
    for tr in fig.data:
        if tr.name == target_label:
            tr.update(marker_line=dict(width=3, color="black"))
            break

    # get start/end from your aggregated dataframe
    row = df_agg.loc[df_agg["problem_no"] == problem_no].iloc[0]
    x0 = row["DATA DA ABERTURA PAD"]
    x1 = row["DATA DO FECHAMENTO PAD"]
    y_label = row["problem_no_label"]

    # add label next to the bar
    fig.add_annotation(
        x=x1 + pd.Timedelta(days=1),  # 1 day to the right of end
        y=y_label,
        text="<em>Problema da OS</em>",
        showarrow=False,
        align="left",
        xanchor="left",
        yanchor="middle",
    )

    return fig


# Rotinas para gerar o gráfico de gantt
def gerar_grafico_gantt_historico_problema_detalhamento_os_v2(df, os_numero, problem_no, buffer_dias=2):
    """Gera o gráfico de gantt com o histórico do problema da OS"""

    # Adiciona categoria
    df["CATEGORIA"] = "OS DOS CASOS"
    df["TARGET"] = "CASOS"

    # Adiciona problema
    df["problem_no_label"] = "Caso " + df["problem_no"].astype(str)

    # Seta colunas como dt
    df["DATA DA ABERTURA DA OS DT"] = pd.to_datetime(df["DATA DA ABERTURA DA OS DT"])
    df["DATA DO FECHAMENTO DA OS DT"] = pd.to_datetime(df["DATA DO FECHAMENTO DA OS DT"])

    # Duração da OS
    df["duracao_dias"] = (df["DATA DO FECHAMENTO DA OS DT"] - df["DATA DA ABERTURA DA OS DT"]).dt.days

    # Adiciona uma borda de 2 dias para facilitar a visualização
    border = pd.Timedelta(days=buffer_dias)
    df["DATA DA ABERTURA PAD"] = df["DATA DA ABERTURA DA OS DT"] - border
    df["DATA DO FECHAMENTO PAD"] = df["DATA DO FECHAMENTO DA OS DT"] + border

    # Cria um df com a OS escolhida para destacar no gráfico
    df_os_escolhida = df[df["NUMERO DA OS"] == int(os_numero)].copy()
    df_os_escolhida["CATEGORIA"] = "OS EM ANÁLISE"

    # Agrega por problema e calcula a data de início e fim
    df_agg = (
        df.groupby("problem_no")
        .agg(
            {
                "DATA DA ABERTURA DA OS DT": "min",
                "DATA DO FECHAMENTO DA OS DT": "max",
                "problem_no": "count",  # count how many rows
            }
        )
        .rename(columns={"problem_no": "os_count"})
        .reset_index()
    )

    # Adiciona uma borda de 2 dias + 1 dia (para não sobrepor) para facilitar a visualização
    border = pd.Timedelta(days=buffer_dias + 1)
    df_agg["DATA DA ABERTURA PAD"] = df_agg["DATA DA ABERTURA DA OS DT"] - border
    df_agg["DATA DO FECHAMENTO PAD"] = df_agg["DATA DO FECHAMENTO DA OS DT"] + border

    # Adiciona labels e duração
    df_agg["problem_no_label"] = "Caso " + df_agg["problem_no"].astype(str)
    df_agg["duracao_dias"] = (df_agg["DATA DO FECHAMENTO DA OS DT"] - df_agg["DATA DA ABERTURA DA OS DT"]).dt.days

    # Adiciona categoria
    df_agg["CATEGORIA"] = "DURAÇÃO DO CASO"
    df_agg["TARGET"] = "CASOS"

    # Merge
    df_merge = pd.concat([df_os_escolhida, df, df_agg])

    # Seta 1 para os casos que não tem total de OS
    df_merge["os_count"] = df_merge["os_count"].fillna(1)

    # Alvo
    df_merge["TARGET"] = "CASOS"

    # Ordena
    df_merge = df_merge.sort_values(by="CATEGORIA")

    # Gerá o gráfico
    # Ver + aqui: https://plotly.com/python/gantt/
    fig = px.timeline(
        df_merge,
        x_start="DATA DA ABERTURA PAD",
        x_end="DATA DO FECHAMENTO PAD",
        y="TARGET",
        color="CATEGORIA",
        color_discrete_sequence=["#f9fadc", "#ccb271", "#16707d"],
        custom_data=[
            "problem_no",
            "DATA DA ABERTURA DA OS DT",
            "DATA DO FECHAMENTO DA OS DT",
            "os_count",
            "duracao_dias",
            "NUMERO DA OS",
        ],
    )

    for tr in fig.data:
        if tr.name == "DURAÇÃO DO CASO":
            tr.hovertemplate = (
                "CASO: %{customdata[0]}<br>"
                "INÍCIO: %{customdata[1]|%H:%M %d/%m/%Y}<br>"
                "FIM: %{customdata[2]|%H:%M %d/%m/%Y}<br>"
                "TOTAL DE OS: %{customdata[3]}<br>"
                "DURAÇÃO: %{customdata[4]} dias"
                "<extra></extra>"
            )
        else:
            tr.hovertemplate = (
                "CASO: %{customdata[0]}<br>"
                "OS: %{customdata[5]}<br>"
                "INÍCIO: %{customdata[1]|%H:%M %d/%m/%Y}<br>"
                "FIM: %{customdata[2]|%H:%M %d/%m/%Y}<br>"
                "<extra></extra>"
            )

    # Tira o título do eixo Y
    fig.update_yaxes(title="")

    # Tamanho das barras no eixo Y
    fig.update_traces(width=0.3)
    
    # Define o título da legenda
    fig.update_layout(
        legend_title_text="Legenda",
    )

    # Destaca os problemas mencionados
    for tr in fig.data:
        if tr.name == "DURAÇÃO DO CASO":
            tr.update(width=0.32, marker_line=dict(width=2, color="black"))
            break

    return fig


# Rotinas para gerar os Gráficos
def gerar_grafico_gantt_historico_problema_detalhamento_os_v3(df, problem_no, buffer_dias=2):
    """Gera o gráfico de gantt com o histórico do problema da OS"""

    # Adiciona categoria para as OS normais
    df["CATEGORIA"] = "OS"

    # Adiciona labels
    df["problem_no_label"] = "Caso " + df["problem_no"].astype(str)

    # Seta colunas como dt
    df["DATA DA ABERTURA DA OS DT"] = pd.to_datetime(df["DATA DA ABERTURA DA OS DT"])
    df["DATA DO FECHAMENTO DA OS DT"] = pd.to_datetime(df["DATA DO FECHAMENTO DA OS DT"])

    # Duração da OS
    df["duracao_dias"] = (df["DATA DO FECHAMENTO DA OS DT"] - df["DATA DA ABERTURA DA OS DT"]).dt.days

    # Adiciona uma borda de 2 dias para facilitar a visualização
    border = pd.Timedelta(days=buffer_dias)
    df["DATA DA ABERTURA PAD"] = df["DATA DA ABERTURA DA OS DT"] - border
    df["DATA DO FECHAMENTO PAD"] = df["DATA DO FECHAMENTO DA OS DT"] + border

    # Agrega por problema e calcula a data de início e fim
    # df_agg vai ser a duração do caso, agregando todas as OS que compõe o caso
    df_agg = (
        df.groupby("problem_no")
        .agg(
            {
                "DATA DA ABERTURA DA OS DT": "min",
                "DATA DO FECHAMENTO DA OS DT": "max",
                "problem_no": "count",  # count how many rows
            }
        )
        .rename(columns={"problem_no": "os_count"})
        .reset_index()
    )

    # Adiciona labels e duração
    df_agg["problem_no_label"] = "Caso " + df_agg["problem_no"].astype(str)
    df_agg["duracao_dias"] = (df_agg["DATA DO FECHAMENTO DA OS DT"] - df_agg["DATA DA ABERTURA DA OS DT"]).dt.days

    # Adiciona uma borda de 2 dias para facilitar a visualização
    border = pd.Timedelta(days=buffer_dias)
    df_agg["DATA DA ABERTURA PAD"] = df_agg["DATA DA ABERTURA DA OS DT"] - border
    df_agg["DATA DO FECHAMENTO PAD"] = df_agg["DATA DO FECHAMENTO DA OS DT"] + border

    # Adiciona categoria
    df_agg["CATEGORIA"] = "DURAÇÃO DO CASO"

    # Merge
    df_merge = pd.concat([df, df_agg])

    # Ordena
    df_merge = df_merge.sort_values(by=["CATEGORIA", "problem_no_label"])

    # Gerá o gráfico
    # Ver + aqui: https://plotly.com/python/gantt/
    fig = px.timeline(
        df_merge,
        x_start="DATA DA ABERTURA PAD",
        x_end="DATA DO FECHAMENTO PAD",
        y="problem_no_label",
        color="CATEGORIA",
        color_discrete_sequence=["#f8e8be", "#ccb271"],
        custom_data=[
            "problem_no",
            "DATA DA ABERTURA DA OS DT",
            "DATA DO FECHAMENTO DA OS DT",
            "os_count",
            "duracao_dias",
            "NUMERO DA OS",
        ],
    )

    fig.update_traces(
        hovertemplate=(
            "Caso: %{customdata[0]}<br>"
            "Início: %{customdata[1]|%H:%M %d/%m/%Y}<br>"
            "Fim: %{customdata[2]|%H:%M %d/%m/%Y}<br>"
            "Total de OS: %{customdata[3]}<br>"
            "Duração: %{customdata[4]} dias"
            "<extra></extra>"
        ),
    )

    fig.update_yaxes(
        # autorange="reversed",
        title="",
        # showticklabels=False
    )

    # # abre um “respiro” à esquerda e à direita para evitar sobreposição com o eixo y
    # pad_label = pd.Timedelta(days=5)
    # xmin = df_agg["DATA DA ABERTURA PAD"].min() - pad_label
    # xmax = df_agg["DATA DO FECHAMENTO PAD"].max() + pad_label
    # fig.update_xaxes(range=[xmin, xmax])

    # deixa com cara de gantt e ajusta margens
    fig.update_layout(
        # margin=dict(l=240),
        legend_title_text="Legenda"
    )  # aumenta a margem esquerda se ainda estiver apertado

    # Destaca o problema mencionado
    # fig.update_traces(marker_line=dict(width=1, color="black"))

    # target_label = f"Caso {problem_no}"
    for tr in fig.data:
        if tr.name == "DURAÇÃO DO CASO":  # só na categoria desejada
            # Cria um array de linhas padrão
            line_colors = ["rgba(0,0,0,0)"] * len(tr.x)
            line_widths = [0] * len(tr.x)

            # Marca só o ponto correspondente
            for i, d in enumerate(tr.customdata):
                if d[0] == problem_no:  # customdata[0] = problem_no
                    line_colors[i] = "black"
                    line_widths[i] = 3

            # Aplica individualmente
            tr.marker.line.color = line_colors
            tr.marker.line.width = line_widths

    # get start/end from your aggregated dataframe
    row = df_agg.loc[df_agg["problem_no"] == problem_no].iloc[0]
    x0 = row["DATA DA ABERTURA PAD"]
    x1 = row["DATA DO FECHAMENTO PAD"]
    y_label = row["problem_no_label"]

    # add label next to the bar
    fig.add_annotation(
        x=x1 + pd.Timedelta(days=1),  # 1 day to the right of end
        y=y_label,
        text="<em>Caso da OS</em>",
        showarrow=False,
        align="left",
        xanchor="left",
        yanchor="middle",
    )

    return fig
