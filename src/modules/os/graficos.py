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
