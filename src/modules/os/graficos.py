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


def gerar_grafico_historico_eventos_detalhamento_os(numero_os, df_problema, df_odometro, df_marcha_lenta):
    """Gera o gráfico de histórico de eventos do problema da OS"""

    # Cria o gráfico de subplots
    fig = make_subplots(
        rows=3,
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

    # Adiciona dados do odômetro
    df_odometro["travel_date"] = pd.to_datetime(df_odometro["travel_date"])
    fig.add_trace(
        go.Scatter(
            x=df_odometro["travel_date"],
            y=df_odometro["CLASSE"],
            mode="markers+text",
            marker=dict(
                size=df_odometro["distance_km"],  # Proportional size
                sizemode="area",
                sizeref=2.0 * max(df_odometro["distance_km"]) / (40.0**2),
                sizemin=5,
                color="lightblue",
                # line=dict(width=1, color='darkblue')
            ),
            text=[f"{d:.0f}" for d in df_odometro["distance_km"]],
            textposition="middle center",
            hovertemplate="Data: %{x}<br>Distância: %{text}<extra></extra>",
        ),
        row=2,
        col=1,
    )

    # Adiciona dados do evento
    df_marcha_lenta["travel_date"] = pd.to_datetime(df_marcha_lenta["travel_date"])
    
    fig.add_trace(
        go.Scatter(
            x=df_marcha_lenta["travel_date"],
            y=df_marcha_lenta["CLASSE"],
            mode="markers+text",
            marker=dict(
                size=df_marcha_lenta["total_evts"],  # Proportional size
                sizemode="area",
                sizeref=2.0 * max(df_marcha_lenta["total_evts"]) / (40.0**2),
                sizemin=5,
                color="lightblue",
                # line=dict(width=1, color='darkblue')
            ),
            text=[f"{d}" for d in df_marcha_lenta["total_evts"]],
            textposition="middle center",
            hovertemplate="Data: %{x}<br>Total de Eventos: %{text}<extra></extra>",
        ),
        row=3,
        col=1,
    )


    fig.update_layout(
        height=600,
        margin=dict(l=150),  # ← margem esquerda aumentada
        # xaxis=dict(
        #     title="Data",
        #     showline=True,
        #     showgrid=True,
        #     zeroline=False,
        # ),
    )

    # Ajuste dos eixos para garantir alinhamento
    # fig.update_yaxes(matches='y', row=1, col=1)
    # fig.update_yaxes(matches='y', row=2, col=1)

    
    fig.update_layout(showlegend=False)

    
    # # Ajustes de layout
    # fig.update_layout(
    #     height=800,
    #     margin=dict(t=40, b=80),  # margem inferior aumentada para evitar corte
    #     xaxis=dict(
    #         title="Data",
    #         showline=True,
    #         showgrid=True,
    #         zeroline=False,
    #     ),
    # )

    # # Garante que o eixo X seja visível em todos os subplots compartilhados
    # fig.update_xaxes(
    #     showline=True,
    #     linewidth=1,
    #     linecolor='black',
    #     showgrid=True,
    #     zeroline=False
    # )

    return fig


#     fig.add_trace(
#         go.Scatter(
#             x=df["travel_date"],
#             y=["Odômetro"] * len(df),  # Constant y to align dots on the same line
#             mode="markers+text",
#             marker=dict(
#                 size=df["distance_km"],  # Proportional size
#                 sizemode="area",
#                 sizeref=2.0 * max(df["distance_km"]) / (40.0**2),  # scale for reasonable max dot size
#                 sizemin=5,
#                 color="lightblue",
#                 # line=dict(width=1, color='darkblue')
#             ),
#             text=[f"{d:.2f}km" for d in df["distance_km"]],
#             textposition="middle center",
#             hovertemplate="Data: %{x}<br>Distância: %{text}<extra></extra>",
#         ),
#         row=2,
#         col=1,
#     )

#     fig.add_trace(
#         go.Scatter(
#             x=df_marcha_lenta["travel_date"],
#             y=["Marcha Lenta"] * len(df_marcha_lenta),  # Constant y to align dots on the same line
#             mode="markers+text",
#             marker=dict(
#                 size=df_marcha_lenta["count"],  # Proportional size
#                 sizemode="area",
#                 sizeref=2.0 * max(df_marcha_lenta["count"]) / (40.0**2),  # scale for reasonable max dot size
#                 sizemin=5,
#                 color="orange",
#                 # line=dict(width=1, color='darkblue')
#             ),
#             text=[f"{d}" for d in df_marcha_lenta["count"]],
#             textposition="middle center",
#             hovertemplate="Data: %{x}<br>Distância: %{text}<extra></extra>",
#         ),
#         row=3,
#         col=1,
#     )

#     fig.add_trace(
#         go.Scatter(
#             x=df_2["travel_date"],
#             y=["USO INDEVIDO DO PEDAL"] * len(df_2),  # Constant y to align dots on the same line
#             mode="markers+text",
#             marker=dict(
#                 size=df_2["count"],  # Proportional size
#                 sizemode="area",
#                 sizeref=2.0 * max(df_2["count"]) / (40.0**2),  # scale for reasonable max dot size
#                 sizemin=5,
#                 color="orange",
#                 # line=dict(width=1, color='darkblue')
#             ),
#             text=[f"{d}" for d in df_2["count"]],
#             textposition="middle center",
#             hovertemplate="Data: %{x}<br>Distância: %{text}<extra></extra>",
#         ),
#         row=4,
#         col=1,
#     )
#     fig.update_layout(showlegend=False)


#     fig
