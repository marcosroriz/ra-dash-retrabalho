#!/usr/bin/env python
# coding: utf-8

# Funções utilitárias para gerar os gráficos da visão OS

# Imports básicos
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
