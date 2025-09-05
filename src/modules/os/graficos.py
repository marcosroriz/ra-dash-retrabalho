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
from plotly.subplots import make_subplots

# Imports do tema
import tema


# Rotinas para gerar o gráfico de gantt
def gerar_grafico_gantt_historico_problema_detalhamento_os(df, os_numero, problem_no, buffer_dias=1):
    """Gera o gráfico de gantt com o histórico do problema da OS"""

    # Adiciona categoria
    df["CATEGORIA"] = "OS DOS CASOS"
    df["TARGET"] = "CASOS"

    # Adiciona problema
    df["problem_no_label"] = "Caso " + df["problem_no"].astype(str)

    # Seta colunas como dt
    df["DATA DA ABERTURA DA OS DT"] = pd.to_datetime(df["DATA DA ABERTURA DA OS DT"])
    df["DATA DO FECHAMENTO DA OS DT"] = pd.to_datetime(df["DATA DO FECHAMENTO DA OS DT"])
    # Seta apenas das OS que não tem data de fechamento válida
    # Porém, apenas para o caso em que não há outro tempo válido
    mask_os_all_nat = df.groupby("NUMERO DA OS")["DATA DO FECHAMENTO DA OS DT"].transform(lambda grp: grp.isna().all())
    df.loc[mask_os_all_nat, "DATA DO FECHAMENTO DA OS DT"] = pd.Timestamp.today().normalize()

    # Duração da OS
    df["duracao_dias"] = (df["DATA DO FECHAMENTO DA OS DT"] - df["DATA DA ABERTURA DA OS DT"]).dt.days

    # Adiciona uma borda para facilitar a visualização
    border = pd.Timedelta(days=buffer_dias)
    df["DATA DA ABERTURA PAD"] = df["DATA DA ABERTURA DA OS DT"] - border
    df["DATA DO FECHAMENTO PAD"] = df["DATA DO FECHAMENTO DA OS DT"] + border

    # Cria um df com a OS escolhida para destacar no gráfico
    df_os_escolhida = df[df["NUMERO DA OS"] == int(os_numero)].copy()
    df_os_escolhida["CATEGORIA"] = "OS EM ANÁLISE"

    # Agrega por número de OS
    df_agg_os = (
        df.groupby("NUMERO DA OS")
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
    border = pd.Timedelta(days=buffer_dias)
    df_agg_os["DATA DA ABERTURA PAD"] = df_agg_os["DATA DA ABERTURA DA OS DT"] - border
    df_agg_os["DATA DO FECHAMENTO PAD"] = df_agg_os["DATA DO FECHAMENTO DA OS DT"] + border

    # Adiciona labels e duração
    df_agg_os["problem_no_label"] = "OS " + df_agg_os["NUMERO DA OS"].astype(str)
    df_agg_os["duracao_dias"] = (
        df_agg_os["DATA DO FECHAMENTO DA OS DT"] - df_agg_os["DATA DA ABERTURA DA OS DT"]
    ).dt.days

    # Adiciona categoria
    df_agg_os["CATEGORIA"] = "OS DOS CASOS"
    df_agg_os["TARGET"] = "CASOS"

    # Agrega por problema e calcula a data de início e fim
    df_agg_problema = (
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
    df_agg_problema["DATA DA ABERTURA PAD"] = df_agg_problema["DATA DA ABERTURA DA OS DT"] - border
    df_agg_problema["DATA DO FECHAMENTO PAD"] = df_agg_problema["DATA DO FECHAMENTO DA OS DT"] + border

    # Adiciona labels e duração
    df_agg_problema["problem_no_label"] = "Caso " + df_agg_problema["problem_no"].astype(str)
    df_agg_problema["duracao_dias"] = (
        df_agg_problema["DATA DO FECHAMENTO DA OS DT"] - df_agg_problema["DATA DA ABERTURA DA OS DT"]
    ).dt.days

    # Adiciona categoria
    df_agg_problema["CATEGORIA"] = "DURAÇÃO DO CASO"
    df_agg_problema["TARGET"] = "CASOS"

    # Merge
    df_merge = pd.concat([df_os_escolhida, df_agg_os, df_agg_problema])

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
                "OS: %{customdata[5]}<br>"
                "TOTAL DE OS: %{customdata[3]}<br>"
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


def wrap_label_by_words(text, max_line_length=20):
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        if len(current_line + " " + word) <= max_line_length:
            current_line += " " + word if current_line else word
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)

    return "<br>".join(lines)


def gerar_grafico_historico_eventos_detalhamento_os(numero_os, df_problema, list_df_evts):
    """Gera o gráfico de histórico de eventos do problema da OS"""

    # Cria o gráfico de subplots
    fig = make_subplots(
        rows=len(list_df_evts) + 1,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        # subplot_titles=("Timeline", "Odômetro", "Marcha Lenta", "Uso Indevido do Pedal"),
        # row_heights=[0.3, 0.23, 0.23, 0.23],
        # specs=[[{"type": "xy"}], [{"type": "xy"}], [{"type": "xy"}], [{"type": "xy"}]],
    )

    # Adiciona dados do problema
    for _, r in df_problema.iterrows():
        fig.add_trace(
            go.Scatter(
                x=[r["DATA DA ABERTURA DA OS DT"], r["DATA DO FECHAMENTO DA OS DT"]],
                y=[r["CLASSE"], r["CLASSE"]],
                mode="markers+lines",
                line=dict(width=48, color="#ccb271" if r["NUMERO DA OS"] != int(numero_os) else "#16707d"),
                showlegend=False,
                hoverinfo="text",
                text=f"OS: {r['NUMERO DA OS']}<br>Abertura: {r['DATA DA ABERTURA DA OS DT']}<br>Fechamento: {r['DATA DO FECHAMENTO DA OS DT']}",
            ),
            row=1,
            col=1,
        )

    for i, df_evt in enumerate(list_df_evts):
        # Adiciona dados do evento
        df_evt["travel_date"] = pd.to_datetime(df_evt["travel_date"])

        # Dá espaçamento adequado nos labels
        df_evt["CLASSE"] = df_evt["CLASSE"].apply(lambda x: wrap_label_by_words(x))

        # Garante que os valores de tamanho sejam float e não objetos inválidos
        marker_sizes = pd.to_numeric(df_evt["target_value"], errors="coerce").fillna(0).astype(float)

        # Evita divisão por zero no sizeref
        max_size = max(marker_sizes) if marker_sizes.max() > 0 else 1.0

        fig.add_trace(
            go.Scatter(
                x=df_evt["travel_date"],
                y=df_evt["CLASSE"],
                mode="markers+text",
                marker=dict(
                    size=marker_sizes.tolist(),
                    sizemode="area",
                    sizeref=2.0 * max_size / (40.0**2),
                    sizemin=5,
                    color=tema.PALETA_CORES_DISCRETA[i % len(tema.PALETA_CORES_DISCRETA)],
                ),
                text=[f"{d}" for d in df_evt["target_label"]],
                textposition="middle center",
                hovertemplate="Data: %{x}<br>Total: %{text}<extra></extra>",
            ),
            row=i + 2,
            col=1,
        )

    fig.update_layout(
        height=600,
        margin=dict(t=40, l=150),  # ← margem esquerda aumentada
    )

    fig.update_layout(showlegend=False)

    fig.update_yaxes(
        automargin=True,  # ensures margin grows to fit long labels
    )
    return fig


