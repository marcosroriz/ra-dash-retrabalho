import plotly.graph_objects as go
import plotly.express as px
import tema

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
