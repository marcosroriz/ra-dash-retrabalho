#!/usr/bin/env python
# coding: utf-8

# Funções utilitárias para gerar os gráficos da visão OS

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
def gerar_grafico_pizza_sinteze_os(df, labels, values):
    """Gera o gráfico de pizza com síntese do total de OS e retrabalhos da tela inicial"""

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
    total_num_os = len(df)
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
        height=420,  # Ajuste conforme necessário
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


def gerar_grafico_cumulativo_os(df):
    # Verifica se df não está vazio
    if df.empty:
        return go.Figure()

    # Criando o gráfico cumulativo com o eixo y em termos percentuais
    fig = px.line(
        df,
        x="tempo_cumulativo",
        y="cumulative_percentage",
        labels={
            "tempo_cumulativo": "Dias",
            "cumulative_percentage": "Correções Cumulativas (%)",
        },
    )

    # Mostrando os pontos e linhas
    fig.update_traces(
        mode="markers+lines",
    )

    # Adiciona o Topo
    df_top = df.groupby("tempo_cumulativo", as_index=False).agg(
        cumulative_percentage=("cumulative_percentage", "max"),
        count=("tempo_cumulativo", "count"),
    )
    # Reseta o index para garantir a sequencialidade
    df_top = df_top.reset_index(drop=True)
    # Adiciona o rótulo vazio
    df_top["label"] = ""

    # Vamos decidir qual a frequência dos labels
    label_frequency = 1
    num_records = len(df_top)
    if num_records >= 30:
        label_frequency = math.ceil(num_records / 20) + 1
    elif num_records >= 10:
        label_frequency = 4
    elif num_records >= 5:
        label_frequency = 2

    # Adiciona o rótulo a cada freq de registros
    for i in range(len(df_top)):
        if i % label_frequency == 0:
            df_top.at[i, "label"] = f"{df_top.at[i, 'cumulative_percentage']:.0f}% <br>({df_top.at[i, 'count']})"

    fig.add_scatter(
        x=df_top["tempo_cumulativo"],
        y=df_top["cumulative_percentage"] + 3,
        mode="text",
        text=df_top["label"],
        textposition="middle right",
        showlegend=False,
        marker=dict(color=tema.COR_PADRAO),
    )

    fig.update_layout(
        xaxis=dict(range=[-1, df["tempo_cumulativo"].max() + 3]),
    )

    # Retorna o gráfico
    return fig


def gerar_grafico_barras_retrabalho_por_modelo_perc(df):
    # Gera o gráfico
    bar_chart = px.bar(
        df,
        x="DESCRICAO DO MODELO",
        y=["PERC_CORRECOES_DE_PRIMEIRA", "PERC_CORRECOES_TARDIA", "PERC_RETRABALHO"],
        barmode="stack",
        color_discrete_sequence=[tema.COR_SUCESSO, tema.COR_ALERTA, tema.COR_ERRO],
        labels={
            "value": "Percentagem",
            "DESCRICAO DO SERVICO": "Ordem de Serviço",
            "variable": "Itens",
        },
    )

    # Atualizando os valores de rótulo para PERC_CORRECOES_DE_PRIMEIRA (percentual e valor absoluto de correções de primeira)
    bar_chart.update_traces(
        text=[
            f"{retrabalho} ({perc_retrab:.2f}%)"
            for retrabalho, perc_retrab in zip(
                df["CORRECOES_DE_PRIMEIRA"],
                df["PERC_CORRECOES_DE_PRIMEIRA"],
            )
        ],
        selector=dict(name="PERC_CORRECOES_DE_PRIMEIRA"),
    )

    # Atualizando os valores de rótulo para PERC_CORRECOES_TARDIA (percentual e valor absoluto de correções tardias)
    bar_chart.update_traces(
        text=[
            f"{correcoes} ({perc_correcoes:.2f}%)"
            for correcoes, perc_correcoes in zip(
                df["CORRECOES_TARDIA"], df["PERC_CORRECOES_TARDIA"]
            )
        ],
        selector=dict(name="PERC_CORRECOES_TARDIA"),
    )

    # Atualizando os valores de rótulo para PERC_RETRABALHO (percentual e valor absoluto de retrabalhos)
    bar_chart.update_traces(
        text=[
            f"{correcoes} ({perc_correcoes:.2f}%)"
            for correcoes, perc_correcoes in zip(
                df["RETRABALHO"], df["PERC_RETRABALHO"]
            )
        ],
        selector=dict(name="PERC_RETRABALHO"),
    )

    # Exibir os rótulos nas barras
    bar_chart.update_traces(texttemplate="%{text}")

    # Ajustar a margem inferior para evitar corte de rótulos
    bar_chart.update_layout(margin=dict(b=200), height=600)

    # Retorna o gráfico
    return bar_chart