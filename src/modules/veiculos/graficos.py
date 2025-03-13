# Bibliotecas básicas
from datetime import date
import numpy as np
import pandas as pd

# Importar bibliotecas do dash básicas e plotly
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.subplots as sp

# Importar nossas constantes e funções utilitárias
import tema
import locale_utils

def grafico_pizza_sintese_geral(labels, values):
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

    # Remove o espaçamento em torno do gráfico
    fig.update_layout(
        margin=dict(t=20, b=0),  # Remove as margens
        height=350,  # Ajuste conforme necessário
        legend=dict(
            orientation="h",  # Legenda horizontal
            yanchor="top",  # Ancora no topo
            xanchor="center",  # Centraliza
            y=-0.1,  # Coloca abaixo
            x=0.5,  # Alinha com o centro
        ),
    )
    return fig


def grafico_evolucao_retrabalho_por_secao_por_mes(df):
    fig = px.line(
        df,
        x="year_month_dt",
        y="PERC",
        color="DESCRICAO DA SECAO",
        facet_col="CATEGORIA",
        facet_col_spacing=0.05,  # Espaçamento entre os gráficos
        labels={"DESCRICAO DA SECAO": "Seção", "year_month_dt": "Ano-Mês", "PERC": "%"},
    )

    # Ajusta o formato do eixo Y para exibir valores como porcentagem
    fig.update_yaxes(tickformat=".0f%")

    # Personaliza o layout do gráfico
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
        margin=dict(b=100),  # Espaço na parte inferior
    )

    # Adiciona títulos específicos para cada gráfico
    fig.update_layout(
        annotations=[
            dict(
                text="Retrabalho por seção (% das OS)",
                x=0.25,  # Posição X para o primeiro plot
                y=1.05,  # Posição Y acima do gráfico
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=16),
            ),
            dict(
                text="Correção de primeira por seção (% das OS)",
                x=0.75,  # Posição X para o segundo plot
                y=1.05,  # Posição Y acima do gráfico
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=16),
            ),
        ]
    )

    # Configura os ticks no eixo X para exibição mensal
    fig.update_xaxes(dtick="M1", tickformat="%Y-%b", title_text="Ano-Mês", title_standoff=90)

    # Ajusta o espaçamento dos títulos do eixo X
    fig.for_each_xaxis(lambda axis: axis.update(title_standoff=90))

    return fig


def grafico_qtd_os_e_soma_de_os_mes(df_soma_mes, df_os_unicas):
        # Gráfico 1: Quantidade de OS por Veículo e por mês
    fig1 = px.line(
        df_soma_mes,
        x="MÊS",
        y="QUANTIDADE_DE_OS",
        color="CODIGO DO VEICULO",
        labels={"MÊS": "Ano-Mês", "QUANTIDADE_DE_OS": "Quantidade de OS", "CODIGO DO VEICULO": "Código do Veículo"},
    )

    fig1.update_traces(mode="lines+markers", showlegend=True)  # Adiciona pontos às linhas e habilita legenda
    fig1.update_layout(
        title="Quantidade de Ordens de Serviço por Veículo e por mês",
        xaxis_title="Ano-Mês",
        yaxis_title="Quantidade de OS",
        margin=dict(b=100),
        showlegend=False  # Desativa a legenda no primeiro gráfico
    )

    # Gráfico 2: Soma de OS por Mês
    fig2 = px.line(
        df_os_unicas,
        x="MÊS",
        y="QUANTIDADE_DE_OS",
        color="CODIGO DO VEICULO",
        labels={"MÊS": "Ano-Mês", "QUANTIDADE_DE_OS": "Quantidade de OS", "CODIGO DO VEICULO": "Código do Veículo"},
    )

    fig2.update_traces(mode="lines+markers", showlegend=True)  # Remove a definição explícita da cor e habilita legenda
    fig2.update_layout(
        title="Quantidade de Ordens de Serviço diferentes por Veículo e por mês",
        xaxis_title="Ano-Mês",
        yaxis_title="Quantidade de OS",
        showlegend=False  # Desativa a legenda no segundo gráfico
    )

    # Combina os gráficos em uma única visualização lado a lado
    fig = sp.make_subplots(
        rows=1,
        cols=2,
        subplot_titles=[
            "Quantidade de Ordens de Serviço por Veículo e por mês",
            "Quantidade de Ordens de Serviço diferentes por Veículo e por mês",
        ],
    )

    # Adiciona os traços de cada gráfico
    for trace in fig1.data:
        fig.add_trace(trace, row=1, col=1)

    for trace in fig2.data:
        trace.showlegend = False  # Desativa a legenda para os traços do segundo gráfico
        fig.add_trace(trace, row=1, col=2)

    # Configuração geral do layout
    fig.update_layout(
        # title=dict(
        #     text="Análise de quantidade de ordens de serviço",
        #     y=0.95,  # Move o título mais para cima (valores entre 0 e 1)
        #     x=0.5,  # Centraliza o título
        #     xanchor="center",
        #     yanchor="top"
        # ),
        showlegend=True,  
        legend=dict(
            title="Código do Veículo",
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="right",
            x=1.3
        ),
        margin=dict(t=95, b=100)  # Reduz o espaço superior para puxar o título mais para cima
    )
    # Configuração dos eixos para cada subplot
    fig.update_xaxes(title_text="Ano-Mês", row=1, col=1)
    fig.update_yaxes(title_text="Quantidade de OS", row=1, col=1)
    fig.update_xaxes(title_text="Ano-Mês", row=1, col=2)
    fig.update_yaxes(title_text="Quantidade de OS", row=1, col=2)

    return fig


def grafico_tabela_pecas(df_veiculos, df_media_geral, df_media_modelo):
    # Cria o gráfico de linhas
    fig = go.Figure()

    # Adiciona linhas para cada veículo selecionado
    for equip in df_veiculos["EQUIPAMENTO"].unique():
        df_equip = df_veiculos[df_veiculos["EQUIPAMENTO"] == equip]
        fig.add_trace(
            go.Scatter(
                x=df_equip["year_month_dt"],
                y=df_equip["total_pecas"],
                mode="lines+markers",
                name=f"Veículo {equip}",
                line=dict(width=2),
                marker=dict(size=8),
                hovertemplate=(
                    "<b>Veículo:</b> %{text}<br>"
                    "<b>Mês:</b> %{x|%Y-%m}<br>"
                    "<b>Valor:</b> R$ %{y:.2f}<extra></extra>"
                ),
                text=df_equip["EQUIPAMENTO"]  # Adiciona o nome do veículo ao hover
            )
        )

    # Adiciona a linha para a média geral
    if not df_media_geral.empty:
        fig.add_trace(
            go.Scatter(
                x=df_media_geral["year_month_dt"],
                y=df_media_geral["media_geral"],
                mode="lines",
                name="Média Geral",
                line=dict(color="orange", dash="dot", width=2),
                hovertemplate=(
                    "<b>Média Geral</b><br>"
                    "<b>Mês:</b> %{x|%Y-%m}<br>"
                    "<b>Valor:</b> R$ %{y:.2f}<extra></extra>"
                ),
            )
        )

    # Adiciona a linha para a média por modelo (com verificação)
    if not df_media_modelo.empty and "MODELO" in df_media_modelo.columns:
        for modelo in df_media_modelo["MODELO"].unique():
            df_modelo = df_media_modelo[df_media_modelo["MODELO"] == modelo]
            fig.add_trace(
                go.Scatter(
                    x=df_modelo["year_month_dt"],
                    y=df_modelo["media_modelo"],
                    mode="lines",
                    name=f"Média {modelo}",
                    line=dict(dash="dash", width=2),
                    hovertemplate=(
                        "<b>Modelo:</b> %{text}<br>"
                        "<b>Mês:</b> %{x|%Y-%m}<br>"
                        "<b>Valor:</b> R$ %{y:.2f}<extra></extra>"
                    ),
                    text=df_modelo["MODELO"]
                )
            )

    # Layout melhorado
    fig.update_layout(
        xaxis_title="Mês",
        yaxis_title="Valor (R$)",
        hovermode="x unified",
        template="plotly_white"
    )

    return fig

def gerar_grafico_evolucao_retrabalho_por_veiculo_por_mes(df):
        # Gera o gráfico
    fig = px.line(
        df,
        x="year_month_dt",
        y="PERC",
        color="CODIGO DO VEICULO",
        facet_col="CATEGORIA",
        facet_col_spacing=0.05,  # Espaçamento entre os gráficos
        labels={"CODIGO DO VEICULO": "Veiculo", "year_month_dt": "Ano-Mês", "PERC": "%"},
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
                text="Retrabalho(%) por veículo",
                x=0.25,  # Posição X para o primeiro plot
                y=1.05,  # Posição Y (em cima do plot)
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=16),
            ),
            dict(
                text="Correção de primeira(%) por veículo",
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