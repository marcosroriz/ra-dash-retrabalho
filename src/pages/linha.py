#!/usr/bin/env python
# coding: utf-8

# Dashboard que lista o retrabalho de uma ou mais OS

##############################################################################
# IMPORTS ####################################################################
##############################################################################
# Bibliotecas básicas
from datetime import date
import pandas as pd

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

# Imports gerais
from modules.entities_utils import get_linhas, get_mecanicos, get_lista_os, get_oficinas, get_secoes, get_modelos


##############################################################################
# LEITURA DE DADOS ###########################################################
##############################################################################
# Conexão com os bancos
pgDB = PostgresSingleton.get_instance()
pgEngine = pgDB.get_engine()

# Obtem as linhas
df_linhas = get_linhas(pgEngine)
lista_todas_linhas = df_linhas.to_dict(orient="records")

# Modelos de veículos
df_modelos_veiculos = pd.read_sql(
    """
    SELECT 
        DISTINCT "vec_model" AS "LABEL"
    FROM 
        rmtc_viagens_analise
    WHERE 
        "vec_model" IS NOT NULL
    ORDER BY
        "vec_model"
    """,
    pgEngine,
)
lista_todos_modelos_veiculos = df_modelos_veiculos.to_dict(orient="records")

# Obtem a lista de OS
df_lista_os = get_lista_os(pgEngine)
lista_todas_os = df_lista_os.to_dict(orient="records")
# lista_todas_os.insert(0, {"LABEL": "TODAS"})

##############################################################################
# CALLBACKS ##################################################################
##############################################################################

##############################################################################
# Callbacks para os inputs ###################################################
##############################################################################


@callback(
    Output("input-select-linha-onibus", "options"),
    Input("input-select-modelo-veiculos-visao-linha", "value"),
)
def corrige_input_modelos_tela_linha(modelo):
    if not modelo:
        return []

    subquery_str = ""
    if modelo:
        subquery_str = f"AND vec_model IN ('{modelo}')"

    query = f"""
        SELECT 
            DISTINCT "encontrou_numero_linha" AS "LABEL"
        FROM 
            rmtc_viagens_analise
        WHERE
            "encontrou_numero_linha" IS NOT NULL
        {subquery_str}
        ORDER BY
            "encontrou_numero_linha"
    """
    print(query)
    # Linhas
    df_linhas = pd.read_sql(query, pgEngine)
    lista_linhas = df_linhas.to_dict(orient="records")

    lista_linhas_options = [{"label": linha["LABEL"], "value": linha["LABEL"]} for linha in lista_linhas]

    return lista_linhas_options


##############################################################################
# Callback para o grafico
##############################################################################
@callback(
    Output("graph-km-l-por-linha", "figure"),
    [
        Input("input-intervalo-datas-combustivel", "value"),
        Input("input-select-modelo-veiculos-visao-linha", "value"),
        Input("input-select-linha-onibus", "value"),
    ],
)
def computa_grafico_consumo_combustivel(datas, modelo, linha):
    if not datas or not modelo or not linha:
        return go.Figure()

    data_inicio = datas[0]
    data_fim = datas[1]

    query = f"""
    SELECT
        *
    FROM
        rmtc_viagens_analise
    WHERE
        "vec_model" IN ('{modelo}')
        AND "encontrou_numero_linha" = '{linha}'
        AND "dia" >= '{data_inicio}'
        AND "dia" <= '{data_fim}'
        AND "km_por_litro" >= 0
    """
    print(query)

    df_linha = pd.read_sql(query, pgEngine)
    df_linha["dia_dt"] = pd.to_datetime(df_linha["dia"])
    df_linha["WEEKDAY_CATEGORY"] = df_linha["dia_dt"].dt.dayofweek.apply(lambda x: "SATURDAY" if x == 5 else ("SUNDAY" if x == 6 else "WEEKDAY"))
    df_linha["WEEKDAY_NUMBER"] = df_linha["dia_dt"].dt.dayofweek
    df_linha["rmtc_timestamp_inicio"] = pd.to_datetime(df_linha["rmtc_timestamp_inicio"])

    # Pega apenas as colunas que interessam
    df = df_linha[
        [
            "dia",
            "vec_num_id",
            "rmtc_linha_prevista",
            "rmtc_destino_curto",
            "encontrou_linha",
            "rmtc_timestamp_inicio",
            "WEEKDAY_NUMBER",
            "WEEKDAY_CATEGORY",
            "km_por_litro",
        ]
    ].copy()

    # Computa tempo bin
    df["time_bin"] = df["rmtc_timestamp_inicio"].dt.floor("30T")
    df["time_bin_only_time"] = df["time_bin"].dt.time

    # Somente aqueles que encontraram a linha
    df = df[df["encontrou_linha"]]
    # remove nans from column km_por_litro
    df = df.dropna(subset=["km_por_litro"])

    # remove outliers > 15 km/l
    df = df[df["km_por_litro"] <= 15]

    # Filtro weekday
    df = df[df["WEEKDAY_CATEGORY"] == "WEEKDAY"]

    # Agrupa por tempo bin
    df_agg = df.groupby("time_bin_only_time")["km_por_litro"].agg(["mean", "std", "min", "max"]).reset_index()


    # Gera grafico
    fig = px.line(
            df_agg,
            x="time_bin_only_time",
            y="mean",
            # error_y=df_agg["max"] - df_agg["mean"],  # Upper error bar
            # error_y_minus=df_agg["mean"] - df_agg["min"],  # Lower error bar
        )

    fig.add_trace(go.Scatter(
        x=df_agg["time_bin_only_time"].tolist() + df_agg["time_bin_only_time"].tolist()[::-1],
        y=df_agg["max"].tolist() + df_agg["min"].tolist()[::-1],
        fill="toself",
        fillcolor="rgba(0, 100, 255, 0.2)",  # Light blue transparent buffer
        line=dict(color="rgba(255,255,255,0)"),  # No outline
        name="Intervalo Min-Max"
    ))

    fig.update_layout(
        xaxis_title="Hora",
        yaxis_title="Consumo de Combustível (km/l)",
    )

    return fig


##############################################################################
# Layout #####################################################################
##############################################################################
layout = dbc.Container(
    [
        # Cabeçalho
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
                                        dbc.Col(DashIconify(icon="bi:fuel-pump-fill", width=45), width="auto"),
                                        dbc.Col(
                                            html.H1(
                                                [
                                                    "Combustível por\u00a0",
                                                    html.Strong("linha"),
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
                                                        id="input-intervalo-datas-combustivel",
                                                        allowSingleDateInRange=True,
                                                        type="range",
                                                        minDate=date(2025, 1, 1),
                                                        maxDate=date.today(),
                                                        value=[date(2025, 1, 1), date.today()],
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
                                                    dbc.Label("Modelos de Veículos"),
                                                    dcc.Dropdown(
                                                        id="input-select-modelo-veiculos-visao-linha",
                                                        options=[
                                                            {
                                                                "label": os["LABEL"],
                                                                "value": os["LABEL"],
                                                            }
                                                            for os in lista_todos_modelos_veiculos
                                                        ],
                                                        value=[],
                                                        placeholder="Selecione o modelo",
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
                                                    dbc.Label("Linha"),
                                                    dcc.Dropdown(
                                                        id="input-select-linha-onibus",
                                                        options=[],
                                                        placeholder="Período em dias",
                                                        value=10,
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
                    md=12,
                ),
            ]
        ),
        # Gráficos
        # Gráfico cumulativo
        dmc.Space(h=30),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="mdi:chart-bell-curve-cumulative", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Gráfico do km/L por Linha",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        dcc.Graph(id="graph-km-l-por-linha"),
    ]
)

##############################################################################
# Registro da página #########################################################
##############################################################################
dash.register_page(__name__, name="Linha", path="/linha", icon="vaadin:lines-list")
