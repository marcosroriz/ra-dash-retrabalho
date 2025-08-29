#!/usr/bin/env python
# coding: utf-8

# Funções utilitárias para gerar os gráficos da visão de criação de regra

# Imports básicos
import pandas as pd
import numpy as np

# Imports gráficos
import plotly.express as px
import plotly.graph_objects as go

# Imports do tema
import tema


# Rotinas para gerar os Gráficos
def gerar_grafico_pizza_sinteze_geral(df, labels, values, usar_checklist=False, checklist_alvo=[]):
    """Gera o gráfico de pizza com síntese do total de OS e retrabalhos da tela de criação de regras"""

    # Checklist alvo vai determinar a paletra de cores a se utilizar
    paleta_cores_padrao = [
        # tema.COR_SUCESSO, # Correção Primeira
        # tema.COR_SUCESSO_BRANDO, # Correção Tardia
        tema.COR_PADRAO, # Nova OS, sem retrabalho prévio
        tema.COR_ALERTA, # Nova OS, com retrabalho prévio
        tema.COR_ERRO, # Retrabalho
    ]

    if usar_checklist:
        paleta_cores_padrao = [
            # tema.COR_SUCESSO if "nova_os_sem_retrabalho_anterior" in checklist_alvo else tema.COR_NEUTRO,
            # tema.COR_SUCESSO_BRANDO if "nova_os_com_retrabalho_anterior" in checklist_alvo else tema.COR_NEUTRO,
            tema.COR_PADRAO if "nova_os_sem_retrabalho_anterior" in checklist_alvo else tema.COR_NEUTRO,
            tema.COR_ALERTA if "nova_os_com_retrabalho_anterior" in checklist_alvo else tema.COR_NEUTRO,
            tema.COR_ERRO if "retrabalho" in checklist_alvo else tema.COR_NEUTRO,
        ]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                direction="clockwise",
                marker_colors=paleta_cores_padrao,
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
        # margin=dict(t=60, b=0),  # Remove as margens
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


def gerar_grafico_retrabalho_por_modelo(df):
    """Gera o gráfico de barras (colunas) por modelo referentes ao retrabalho e correções de primeira"""

    bar_chart = px.bar(
        df,
        x="DESCRICAO DO MODELO",
        y=[
            "PERC_NAO_TEVE_PROBLEMA",
            "PERC_TEVE_PROBLEMA_SEM_RETRABALHO",
            "PERC_TEVE_PROBLEMA_E_RETRABALHO",
        ],
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
                df["TEVE_PROBLEMA_SEM_RETRABALHO"],
                df["PERC_TEVE_PROBLEMA_SEM_RETRABALHO"],
            )
        ],
        selector=dict(name="PERC_TEVE_PROBLEMA_SEM_RETRABALHO"),
    )

    # Atualizando os valores de rótulo para PERC_RETRABALHO (percentual e valor absoluto de retrabalhos)
    bar_chart.update_traces(
        text=[
            f"{perc_teve_prob_e_retrab:.0f}%<br>({teve_prob_e_retrab:.0f})"
            for teve_prob_e_retrab, perc_teve_prob_e_retrab in zip(df["TEVE_PROBLEMA_E_RETRABALHO"], df["PERC_TEVE_PROBLEMA_E_RETRABALHO"])
        ],
        selector=dict(name="PERC_TEVE_PROBLEMA_E_RETRABALHO"),
    )

    # Exibir os rótulos nas barras
    bar_chart.update_traces(texttemplate="%{text}")

    # Ajustar a margem inferior para evitar corte de rótulos
    bar_chart.update_layout(
        yaxis=dict(range=[0, 118]),
    )

    if len(df) > 5:
        bar_chart.update_layout(
            margin=dict(t=10, b=200),
            height=500,
        )

    # Separador numérico
    bar_chart.update_layout(separators=",.")

    # Retorna o gráfico
    return bar_chart


def gerar_grafico_evolucao_retrabalho_por_modelo_por_mes(df):
    """Gera o gráfico de linhas referentes a evolução do retrabalho por modelo"""

    # Gera o gráfico
    fig = px.line(
        df,
        x="year_month_dt",
        y="PERC",
        color="DESCRICAO DO MODELO",
        facet_col="CATEGORIA",
        facet_col_spacing=0.05,  # Espaçamento entre os gráficos
        labels={"DESCRICAO DO MODELO": "Modelo", "year_month_dt": "Ano-Mês", "PERC": "%"},
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
        height=500,  # Ajuste conforme necessário
        annotations=[
            dict(
                text="Retrabalho por modelo (% das OS)",
                x=0.25,  # Posição X para o primeiro plot
                y=1.05,  # Posição Y (em cima do plot)
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=16),
            ),
            dict(
                text="Correção de primeira por modelo (% das OS)",
                x=0.75,  # Posição X para o segundo plot
                y=1.05,  # Posição Y (em cima do plot)
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=16),
            ),
        ],
    )

    # Gera ticks todo mês
    fig.update_xaxes(dtick="M1", tickformat="%Y-%b", title_text="Ano-Mês", title_standoff=90)

    # Aumenta o espaçamento do titulo
    fig.for_each_xaxis(lambda axis: axis.update(title_standoff=90))

    return fig


def gerar_grafico_evolucao_retrabalho_por_oficina_por_mes(df):
    """Gera o gráfico de linhas referentes a evolução do retrabalho por mês"""

    # Gera o gráfico
    fig = px.line(
        df,
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
    fig.for_each_xaxis(lambda axis: axis.update(title_standoff=90))

    return fig


def gerar_grafico_evolucao_retrabalho_por_secao_por_mes(df):
    """Gera o gráfico de linhas referentes a evolução do retrabalho por seção por mês"""

    # Gera o gráfico
    fig = px.line(
        df,
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
    fig.for_each_xaxis(lambda axis: axis.update(title_standoff=90))

    return fig


def gerar_grafico_evolucao_retrabalho_por_nota_por_mes(df):
    """Gera o gráfico de linhas referentes a evolução do retrabalho por nota por mês"""

    # Gera o gráfico
    fig = px.line(
        df,
        x="year_month_dt",
        y="NOTA_MEDIA",
        color="TIPO",
        facet_col="CATEGORIA",
        facet_col_spacing=0.05,  # Espaçamento entre os gráficos
        labels={"DESCRICAO DA SECAO": "Seção", "year_month_dt": "Ano-Mês", "PERC": "%"},
        markers=True,
    )

    # Coloca % no eixo y
    # fig.update_yaxes(tickformat=".0f%")

    # Renomeia o eixo y
    fig.update_layout(
        yaxis=dict(
            title="Nota Sintoma",
        ),
        yaxis2=dict(
            title="Nota Solução",
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
                text="Nota das OSs com Retrabalho",
                x=0.25,  # Posição X para o primeiro plot
                y=1.05,  # Posição Y (em cima do plot)
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=16),
            ),
            dict(
                text="Nota das OSs corrigidas de primeira",
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
    fig.for_each_xaxis(lambda axis: axis.update(title_standoff=90))

    return fig


def gerar_grafico_evolucao_retrabalho_por_custo_por_mes(df):
    """Gera o gráfico de linhas referentes a evolução do retrabalho por custo por mês"""

    # Gera o gráfico
    fig = px.line(
        df,
        x="year_month_dt",
        y="GASTO",
        color="CATEGORIA",
        labels={"year_month_dt": "Ano-Mês"},
        markers=True,
    )

    # Renomeia o eixo y
    fig.update_layout(
        yaxis=dict(
            title="Custo em R$",
            tickformat=",.2f",  # Arredonda
            tickprefix="R$ ",  # Prefixo
            tickmode="auto",
            automargin=True,  # Adjusts margins dynamically
        ),
        margin=dict(b=100),
    )

    # Gera ticks todo mês
    fig.update_xaxes(dtick="M1", tickformat="%Y-%b", title_text="Ano-Mês", title_standoff=90)

    # Aumenta o espaçamento do titulo
    fig.for_each_xaxis(lambda axis: axis.update(title_standoff=90))

    return fig


def gerar_grafico_top_10_problemas_relatorio_regras(df):
    """Gera o gráfico de barras referentes aos 10 problemas mais frequentes"""

    fig = px.bar(
        df,
        x="DESCRICAO DO SERVICO",
        y="count"
    )

    fig.update_traces(
        texttemplate="%{y} (%{customdata:.1f}%)",
        customdata=df["PERC_TOTAL_OS"],
        textposition="auto",
    )

    # Renomeia o eixo y
    fig.update_layout(
        yaxis=dict(
            title="Total de OSs",
            tickmode="auto",
            automargin=True,
        ),
        margin=dict(b=200),
    )

    return fig

