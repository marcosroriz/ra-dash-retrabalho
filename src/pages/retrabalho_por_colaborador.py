#!/usr/bin/env python
# coding: utf-8

# Dashboard que lista o retrabalho de um colaborador

##############################################################################
# IMPORTS ####################################################################
##############################################################################
# Bibliotecas básicas
from datetime import date
import pandas as pd

# Importar bibliotecas do dash básicas e plotly
from dash import html, dcc, callback, Input, Output
import plotly.graph_objects as go
import plotly.express as px
import dash

# Importar bibliotecas do bootstrap e ag-grid
import dash_bootstrap_components as dbc
import dash_ag_grid as dag

# Dash componentes Mantine e icones
import dash_mantine_components as dmc
from dash_iconify import DashIconify

# Importar nossas constantes e funções utilitárias
from modules.entities_utils import gerar_excel
from modules.colaborador.tabelas import *
import locale_utils

# Banco de Dados
from db import PostgresSingleton

##############################################################################
# LEITURA DE DADOS ###########################################################
##############################################################################
# Conexão com os bancos
pgDB = PostgresSingleton.get_instance()
pgEngine = pgDB.get_engine()

from modules.colaborador.colaborador_service import ColaboradorService
from modules.colaborador.graficos import *

colab = ColaboradorService(pgEngine)


##############################################################################
# Obtêm os dados dos colaboradores
##############################################################################

# Obtêm os dados de todos os mecânicos que trabalharam na RA, mesmo os desligados
df_mecanicos_todos = colab.get_mecanicos()

#Obtem lista das os
df_lista_os = colab.df_lista_os()
lista_todas_os = df_lista_os.to_dict(orient="records")
lista_todas_os.insert(0, {"LABEL": "TODAS"})
##############################################################################
# Registro da página #########################################################
##############################################################################
dash.register_page(
    __name__, name="Colaborador", path="/retrabalho-por-colaborador", icon="fluent-mdl2:timeline"
)

##############################################################################
# CALLBACKS ##################################################################
##############################################################################   

##############################################################################
# Callbacks para os inputs ###################################################
##############################################################################

# Função para validar o input
def input_valido(id_colaborador, datas, min_dias, lista_oficinas, lista_secaos, lista_os):
    if id_colaborador is None or not id_colaborador or None in id_colaborador:
        return False
    
    if datas is None or not datas or None in datas or min_dias is None:
        return False

    if lista_oficinas is None or not lista_oficinas or None in lista_oficinas:
        return False

    if lista_secaos is None or not lista_secaos or None in lista_secaos:
        return False

    if lista_os is None or not lista_os or None in lista_os:
        return False

    return True


# Corrige o input para garantir que "TODAS" não seja selecionado junto com outras opções
def corrige_input(lista):
    # Caso 1: Nenhuma opcao é selecionada, reseta para "TODAS"
    if not lista:
        return ["TODAS"]

    # Caso 2: Se "TODAS" foi selecionado após outras opções, reseta para "TODAS"
    if len(lista) > 1 and "TODAS" in lista[1:]:
        return ["TODAS"]

    # Caso 3: Se alguma opção foi selecionada após "TODAS", remove "TODAS"
    if "TODAS" in lista and len(lista) > 1:
        return [value for value in lista if value != "TODAS"]

    # Por fim, se não caiu em nenhum caso, retorna o valor original
    return lista

def gera_labels_inputs(campo):
    # Cria o callback
    @callback(
        [
            Output(component_id=f"{campo}-labels", component_property="children"),
        ],
        [
            Input("input-min-dias-colaborador", "value"),
            Input("input-select-secao-colaborador", "value"),
            Input("input-select-ordens-servico-colaborador", "value"),
            Input("input-select-modelos-colaborador", "value"),
            Input("input-select-oficina-colaborador", "value"),
        ],
    )
    def atualiza_labels_inputs( min_dias, lista_secaos, lista_os, lista_modelo, lista_oficinas):
        labels_antes = [
            # DashIconify(icon="material-symbols:filter-arrow-right", width=20),
            dmc.Badge("Filtro", color="gray", variant="outline"),
        ]
        min_dias_label = [dmc.Badge(f"{min_dias} dias", variant="outline")]
        lista_oficinas_labels = []
        lista_secaos_labels = []
        lista_os_labels = []

        if lista_oficinas is None or not lista_oficinas or "TODAS" in lista_oficinas:
            lista_oficinas_labels.append(dmc.Badge("Todas as oficinas", variant="outline"))
        else:
            for oficina in lista_oficinas:
                lista_oficinas_labels.append(dmc.Badge(oficina, variant="dot"))
                
        if lista_modelo is None or not lista_modelo or "TODAS" in lista_modelo:
            lista_oficinas_labels.append(dmc.Badge("Todos os modelos", variant="outline"))
        else:
            for oficina in lista_modelo:
                lista_oficinas_labels.append(dmc.Badge(oficina, variant="dot"))

        if lista_secaos is None or not lista_secaos or "TODAS" in lista_secaos:
            lista_secaos_labels.append(dmc.Badge("Todas as seções", variant="outline"))
        else:
            for secao in lista_secaos:
                lista_secaos_labels.append(dmc.Badge(secao, variant="dot"))

        if lista_os is None or not lista_os or "TODAS" in lista_os:
            lista_os_labels.append(dmc.Badge("Todas as ordens de serviço", variant="outline"))
        else:
            for os in lista_os:
                lista_os_labels.append(dmc.Badge(f"OS: {os}", variant="dot"))

        return [
            dmc.Group(labels_antes + min_dias_label + lista_oficinas_labels + lista_secaos_labels + lista_os_labels)
        ]

    # Cria o componente
    return dmc.Group(id=f"{campo}-labels", children=[])


@callback(
    Output("input-select-oficina-colaborador", "value"),
    Input("input-select-oficina-colaborador", "value"),
)
def corrige_input_oficina(lista_oficinas):
    return corrige_input(lista_oficinas)

@callback(
    Output("input-select-secao-colaborador", "value"),
    Input("input-select-secao-colaborador", "value"),
)
def corrige_input_secao(lista_secaos):
    return corrige_input(lista_secaos)

@callback(
    [
        Output("input-select-ordens-servico-colaborador", "options"),
        Output("input-select-ordens-servico-colaborador", "value"),
    ],
    [
        Input("input-select-ordens-servico-colaborador", "value"),
        Input("input-select-secao-colaborador", "value"),
        Input("input-lista-colaborador", "value"),
        Input("input-min-dias-colaborador", "value"),
        Input("input-intervalo-datas-colaborador", "value")
    ],
)
def corrige_input_ordem_servico(lista_os, lista_secaos, id_colaborador, min_dias, datas):
    # Vamos pegar as OS possíveis para as seções selecionadas
    df_lista_os_secao = colab.df_lista_os_colab(min_dias, id_colaborador, datas)

    if "TODAS" not in lista_secaos:
        df_lista_os_secao = df_lista_os_secao[df_lista_os_secao["SECAO"].isin(lista_secaos)]

    # Essa rotina garante que, ao alterar a seleção de oficinas ou seções, a lista de ordens de serviço seja coerente
    lista_os_possiveis = df_lista_os_secao.to_dict(orient="records")
    lista_os_possiveis.insert(0, {"LABEL": "TODAS"})

    lista_options = [{"label": os["LABEL"], "value": os["LABEL"]} for os in lista_os_possiveis]

    # OK, algor vamos remover as OS que não são possíveis para as seções selecionadas
    if "TODAS" not in lista_os:
        df_lista_os_atual = df_lista_os_secao[df_lista_os_secao["LABEL"].isin(lista_os)]
        lista_os = df_lista_os_atual["LABEL"].tolist()

    return lista_options, corrige_input(lista_os)


@callback(
    [
        Output("input-select-modelos-colaborador", "options"),
        Output("input-select-modelos-colaborador", "value"),
    ],
    [
        Input("input-select-modelos-colaborador", "value"),
        Input("input-select-secao-colaborador", "value"),
        Input("input-select-ordens-servico-colaborador", "value"),
        Input("input-lista-colaborador", "value"),
        Input("input-min-dias-colaborador", "value"),
        Input("input-intervalo-datas-colaborador", "value")
    ],
)
def corrige_input_modelo(lista_modelos, lista_secaos, lista_os, id_colaborador, min_dias, datas):
    # Vamos pegar as OS possíveis para as seções selecionadas
    df_lista_os_secao = colab.df_lista_os_colab_modelo(lista_secaos, lista_os, min_dias, id_colaborador, datas)


    # Essa rotina garante que, ao alterar a seleção de oficinas ou seções, a lista de ordens de serviço seja coerente
    lista_modelos_possiveis = df_lista_os_secao.to_dict(orient="records")
    lista_modelos_possiveis.insert(0, {"LABEL": "TODAS"})

    lista_options = [{"label": os["LABEL"], "value": os["LABEL"]} for os in lista_modelos_possiveis]

    # OK, algor vamos remover as OS que não são possíveis para as seções selecionadas
    if "TODAS" not in lista_modelos:
        df_lista_os_atual = df_lista_os_secao[df_lista_os_secao["LABEL"].isin(lista_modelos)]
        lista_modelos = df_lista_os_atual["LABEL"].tolist()

    return lista_options, corrige_input(lista_modelos)



@callback(
    [
        Output("indicador-total-os-trabalho", "children"),
        Output("indicador-quantidade-servico", "children"),
        Output("indicador-correcao-de-primeira", "children"),
        Output("indicador-retrabalho", "children"),
        Output("indicador-rank-servico", "children"),
        Output("indicador-rank-os", "children"),
        Output("indicador-nota-colaborador", "children"),
        Output("indicador-rank-posicao-nota", "children"),
        Output("indicador-gasto-total-colaborador", "children"),
        Output("indicador-gasto-retrabalho-total-colaborador", "children")#indicador-gasto-retrabalho-total-colaborador
        
    ],
    [
        Input("input-lista-colaborador", "value"),
        Input("input-intervalo-datas-colaborador", "value"),
        Input("input-min-dias-colaborador", "value"),
        Input("input-select-secao-colaborador", "value"),
        Input("input-select-ordens-servico-colaborador", "value"),
        Input("input-select-modelos-colaborador", "value"),
        Input("input-select-oficina-colaborador", "value"),
    ],
    running=[(Output("loading-overlay", "visible"), True, False)],
)
def calcular_indicadores(id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina):
    
    id_colaborador = 3295 if id_colaborador is None else id_colaborador
    # Validação dos inputs
    if datas is None or not datas or None in datas or min_dias is None:
        return False
    if not id_colaborador or not datas or any(d is None for d in datas) or not isinstance(min_dias, int) or min_dias < 1:
        return '', '', '', '','', '', '', '', '',''
    
    
    # Obtém análise estatística
    df_os_analise = colab.obtem_estatistica_retrabalho_sql(
        datas=datas, id_colaborador=id_colaborador, min_dias=min_dias, 
        lista_secaos=lista_secaos, lista_os=lista_os, lista_modelo=lista_modelo,
        lista_oficina=lista_oficina
    )

    if df_os_analise.empty:
        return (
            "Nenhuma OS realizada no período selecionado.",
            "Nenhuma OS realizada no período selecionado.",
            'Nenhuma OS realizada no período selecionado.',
            'Nenhuma OS realizada no período selecionado.',
            'Nenhuma OS realizada no período selecionado.',
            'Nenhuma OS realizada no período selecionado.',
            'Nenhuma OS realizada no período selecionado.',
            'Nenhuma OS realizada no período selecionado.',
            'Nenhuma OS realizada no período selecionado.',
            'Nenhuma OS realizada no período selecionado.',
        )

    # Indicador 1: Total de OSs trabalhadas
    total_os = f"{df_os_analise['TOTAL_OS'].iloc[0]}"
    # Indicador 2: Quantidade de serviços únicos realizados
    servicos_diferentes = df_os_analise['QTD_SERVICOS_DIFERENTES'].iloc[0]
    quantidade_servicos = f"{servicos_diferentes}"

    # Indicadores de correção de primeira e retrabalho
    if not df_os_analise.empty and all(
        col in df_os_analise.columns for col in ["PERC_CORRECAO_PRIMEIRA", "PERC_RETRABALHO"]
    ):
        correcao_primeira = f"{df_os_analise['PERC_CORRECAO_PRIMEIRA'].iloc[0]}%"
        retrabalho = f"{df_os_analise['PERC_RETRABALHO'].iloc[0] if not df_os_analise['PERC_RETRABALHO'].iloc[0] == None else 0}%"
    else:
        correcao_primeira = "Dados insuficientes para calcular correções de primeira"
        retrabalho = "Dados insuficientes para calcular retrabalho"
        
    df_rank_servico = colab.indcador_rank_servico(
        datas=datas, id_colaborador=id_colaborador, min_dias=min_dias, 
        lista_secaos=lista_secaos, lista_os=lista_os, lista_modelo=lista_modelo,
        lista_oficina=lista_oficina
    )
    
    if df_rank_servico.empty:
        return (
            "Nenhuma OS realizada no período selecionado.",
            "Nenhuma OS realizada no período selecionado.",
            'Nenhuma OS realizada no período selecionado.',
            'Nenhuma OS realizada no período selecionado.',
            'Nenhuma OS realizada no período selecionado.',
            'Nenhuma OS realizada no período selecionado.',
            'Nenhuma OS realizada no período selecionado.',
            'Nenhuma OS realizada no período selecionado.',
            'Nenhuma OS realizada no período selecionado.',
            'Nenhuma OS realizada no período selecionado.',
        )
    
    df_rank_os = colab.indcador_rank_total_os(
        datas=datas, id_colaborador=id_colaborador, min_dias=min_dias, 
        lista_secaos=lista_secaos, lista_os=lista_os, lista_modelo=lista_modelo,
        lista_oficina=lista_oficina
    )
    if df_rank_os.empty:
        return (
            "Nenhuma OS realizada no período selecionado.",
            "Nenhuma OS realizada no período selecionado.",
            'Nenhuma OS realizada no período selecionado.',
            'Nenhuma OS realizada no período selecionado.',
            'Nenhuma OS realizada no período selecionado.',
            'Nenhuma OS realizada no período selecionado.',
            'Nenhuma OS realizada no período selecionado.',
            'Nenhuma OS realizada no período selecionado.',
            'Nenhuma OS realizada no período selecionado.',
            'Nenhuma OS realizada no período selecionado.',
        )
    # Indicadores Rank
    rank_servico = f"{df_rank_servico['rank_colaborador'].iloc[0]}"
    rank_os_absoluta = f"{df_rank_os['rank_colaborador'].iloc[0]}"
    
    df_nota_media = colab.nota_media_colaborador(
        datas=datas, id_colaborador=id_colaborador, min_dias=min_dias, 
        lista_secaos=lista_secaos, lista_os=lista_os, lista_modelo=lista_modelo,
        lista_oficina=lista_oficina
    )
    
    if df_nota_media.empty:
        return (
            "Nenhuma OS realizada no período selecionado.",
            "Nenhuma OS realizada no período selecionado.",
            'Nenhuma OS realizada no período selecionado.',
            'Nenhuma OS realizada no período selecionado.',
            'Nenhuma OS realizada no período selecionado.',
            'Nenhuma OS realizada no período selecionado.',
            'Nenhuma OS realizada no período selecionado.',
            'Nenhuma OS realizada no período selecionado.',
            'Nenhuma OS realizada no período selecionado.',
            'Nenhuma OS realizada no período selecionado.',
        )
    nota_media = f"{df_nota_media['nota_media_colaborador'].iloc[0] if not df_nota_media['nota_media_colaborador'].iloc[0]  is None else 0}"
    
    df_nota_posicao = colab.posicao_rank_nota_media(
        datas=datas, id_colaborador=id_colaborador, min_dias=min_dias, 
        lista_secaos=lista_secaos, lista_os=lista_os, lista_modelo=lista_modelo,
        lista_oficina=lista_oficina
    )
    if df_nota_posicao.empty:
        return (
            "Nenhuma OS realizada no período selecionado.",
            "Nenhuma OS realizada no período selecionado.",
            'Nenhuma OS realizada no período selecionado.',
            'Nenhuma OS realizada no período selecionado.',
            'Nenhuma OS realizada no período selecionado.',
            'Nenhuma OS realizada no período selecionado.',
            'Nenhuma OS realizada no período selecionado.',
            'Nenhuma OS realizada no período selecionado.',
            'Nenhuma OS realizada no período selecionado.',
            'Nenhuma OS realizada no período selecionado.',
        )

    rank_nota_posicao = f"{df_nota_posicao['rank_colaborador'].iloc[0]}"

    df_gasto = colab.gasto_colaborador(
        datas=datas, id_colaborador=id_colaborador, min_dias=min_dias, 
        lista_secaos=lista_secaos, lista_os=lista_os, lista_modelo=lista_modelo,
        lista_oficina=lista_oficina  
    )
    gasto_colaborador = f"{df_gasto['TOTAL_GASTO'].iloc[0]}"
    gasto_retrabalho = f"{df_gasto['TOTAL_GASTO_RETRABALHO'].iloc[0]}"
    
    return total_os, quantidade_servicos, correcao_primeira, retrabalho, rank_servico, rank_os_absoluta, nota_media, rank_nota_posicao, gasto_colaborador, gasto_retrabalho



@callback(
    Output("store-dados-colaborador-retrabalho", "data"),
    [
        Input("input-lista-colaborador", "value"),
        Input("input-intervalo-datas-colaborador", "value"),
        Input("input-min-dias-colaborador", "value"),
        Input("input-select-secao-colaborador", "value"),
        Input("input-select-ordens-servico-colaborador", "value"),
        Input("input-select-modelos-colaborador", "value"),
        Input("input-select-oficina-colaborador", "value"),
    ],
)
def computa_retrabalho_mecanico(id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina):
    dados_vazios = {"df_os_mecanico": pd.DataFrame().to_dict("records"), "vazio": True}

    if (id_colaborador is None) or (datas is None or not datas or None in datas) or (min_dias is None or min_dias < 1):
        return dados_vazios

    # Obtem os dados de retrabalho
    df_os_mecanico = colab.obtem_dados_os_mecanico(id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina)


    return {"df_os_mecanico": df_os_mecanico.to_dict("records"), "vazio": False}


@callback(Output("graph-barra-atuacao-geral", "figure"), Input("store-dados-colaborador-retrabalho", "data"), running=[(Output("loading-overlay", "visible"), True, False)])
def computa_atuacao_mecanico_tipo_os(data):
    if data["vazio"]:
        return go.Figure()

    # Obtem OS
    df_os_mecanico = pd.DataFrame(data["df_os_mecanico"])

    # Prepara os dados para o gráfico
    df_agg_atuacao = (
        df_os_mecanico.groupby(["DESCRICAO DO TIPO DA OS"])
        .size()
        .reset_index(name="QUANTIDADE")
        .sort_values(by="QUANTIDADE", ascending=True)
    )

    # Percentagem
    df_agg_atuacao["PERCENTAGE"] = (df_agg_atuacao["QUANTIDADE"] / df_agg_atuacao["QUANTIDADE"].sum()) * 100

    # Gera o Gráfico
    fig = px.pie(
        df_agg_atuacao,
        values="QUANTIDADE",
        names="DESCRICAO DO TIPO DA OS",
        hole=0.2,
    )

    # Update the chart to show percentages as labels
    fig.update_traces(
        textinfo="label+percent",
        texttemplate="%{value}<br>%{percent:.2%}",
    )

    fig.update_layout(
        legend=dict(
            orientation="h",  # Horizontal orientation
            y=0,  # Position the legend below the chart
            x=0.5,  # Center align the legend
            xanchor="center",
        ),
    )

    return fig


@callback(
    Output("graph-principais-os", "figure"), 
    [
        Input("input-lista-colaborador", "value"),
        Input("input-intervalo-datas-colaborador", "value"),
        Input("input-min-dias-colaborador", "value"),
        Input("input-select-secao-colaborador", "value"),
        Input("input-select-ordens-servico-colaborador", "value"),
        Input("input-select-modelos-colaborador", "value"),
        Input("input-select-oficina-colaborador", "value"),
    ],
)
def computa_atuacao_mecanico_tipo_os(id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina):
    if not id_colaborador:
        return go.Figure()

    # Obtem OS
    df_os_mecanico = colab.dados_grafico_top_10_do_colaborador(
        datas=datas, id_colaborador=id_colaborador, min_dias=min_dias, 
        lista_secaos=lista_secaos, lista_os=lista_os, lista_modelo=lista_modelo,
        lista_oficina=lista_oficina
    ).sort_values('TOTAL_OS',ascending=False)

    if df_os_mecanico.empty:
        return go.Figure()
    # Top 10 serviços
    df_agg_servico_top10 = df_os_mecanico.head(10)

    # Gera o Gráfico
    fig = px.bar(
        df_agg_servico_top10,
        x="DESCRICAO DO SERVICO",
        y="TOTAL_OS",
        # orientation="h",
        text="TOTAL_OS",  # Initial text for display
    )

    fig.update_traces(
        texttemplate="%{y} (%{customdata:.1f}%)",
        customdata=df_agg_servico_top10["PERC_TOTAL_OS"],  # Add percentage data
        textposition="auto",
    )
    fig.update_layout(xaxis_title="")
    return fig

@callback(
    Output("graph-evolucao-retrabalho-por-mes", "figure"), 
    [
        Input("input-lista-colaborador", "value"),
        Input("input-intervalo-datas-colaborador", "value"),
        Input("input-min-dias-colaborador", "value"),
        Input("input-select-secao-colaborador", "value"),
        Input("input-select-ordens-servico-colaborador", "value"),
        Input("input-select-modelos-colaborador", "value"),
        Input("input-select-oficina-colaborador", "value"),
    ],
)
def grafico_retrabalho_mes(id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina):
    '''plota grafico de evolução de retrabalho por ano'''
    
    dados_vazios = {"df_os_mecanico": pd.DataFrame().to_dict("records"), "vazio": True}
    # Validação dos inputs
    if (id_colaborador is None) or (datas is None) or (min_dias is None):
        return go.Figure()
    
    # Obtém análise estatística
    df_os_analise = colab.obtem_estatistica_retrabalho_grafico(
        datas=datas, id_colaborador=id_colaborador, min_dias=min_dias, 
        lista_secaos=lista_secaos, lista_os=lista_os, lista_modelo=lista_modelo,
        lista_oficina=lista_oficina
    )
    if df_os_analise.empty:
        return go.Figure()

    fig = generate_grafico_evolucao(df_os_analise)
    return fig

@callback(
    Output("graph-pizza-sintese-colaborador", "figure"), 
    [
        Input("input-lista-colaborador", "value"),
        Input("input-intervalo-datas-colaborador", "value"),
        Input("input-min-dias-colaborador", "value"),
        Input("input-select-secao-colaborador", "value"),
        Input("input-select-ordens-servico-colaborador", "value"),
        Input("input-select-modelos-colaborador", "value"),
        Input("input-select-oficina-colaborador", "value"),
    ],
)
def grafico_retrabalho_resumo(id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina):
    '''plota grafico de evolução de retrabalho por ano'''
    dados_vazios = {"df_os_mecanico": pd.DataFrame().to_dict("records"), "vazio": True}
    # Validação dos inputs
    if (id_colaborador is None) or (datas is None) or (min_dias is None):
        return go.Figure()
    
    # Obtém análise estatística
    df_os_analise = colab.obtem_estatistica_retrabalho_grafico_resumo(
        datas=datas, id_colaborador=id_colaborador, min_dias=min_dias, 
        lista_secaos=lista_secaos, lista_os=lista_os, lista_modelo=lista_modelo,
        lista_oficina=lista_oficina
    )

    if df_os_analise.empty:
        return go.Figure()
    
    fig = grafico_pizza_colaborador(df_os_analise)
    return fig

@callback(
    Output("tabela-top-os-colaborador", "rowData"), 
    [
        Input("input-lista-colaborador", "value"),
        Input("input-intervalo-datas-colaborador", "value"),
        Input("input-min-dias-colaborador", "value"),
        Input("input-select-secao-colaborador", "value"),
        Input("input-select-ordens-servico-colaborador", "value"),
        Input("input-select-modelos-colaborador", "value"),
        Input("input-select-oficina-colaborador", "value"),
    ],
)
def tabela_visao_geral_colaborador(id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina):
    
    if (id_colaborador is None) or (datas is None) or (min_dias is None):
        return []
    
    return colab.dados_tabela_do_colaborador(
        datas=datas, id_colaborador=id_colaborador, min_dias=min_dias, 
        lista_secaos=lista_secaos, lista_os=lista_os, lista_modelo=lista_modelo,
        lista_oficina=lista_oficina
    ).to_dict("records")
    
@callback(
    Output("graph-evolucao-nota-por-mes", "figure"), 
    [
        Input("input-lista-colaborador", "value"),
        Input("input-intervalo-datas-colaborador", "value"),
        Input("input-min-dias-colaborador", "value"),
        Input("input-select-secao-colaborador", "value"),
        Input("input-select-ordens-servico-colaborador", "value"),
        Input("input-select-modelos-colaborador", "value"),
        Input("input-select-oficina-colaborador", "value"),
    ],
    running=[(Output("loading-overlay", "visible"), True, False)],
)
def grafico_nota_media_mes(id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina):
    '''plota grafico de evolução de retrabalho por ano'''
    
    # Validação dos inputs
    if (id_colaborador is None) or (datas is None) or (min_dias is None):
        return go.Figure()
    
    # Obtém análise estatística
    df_os_analise = colab.evolucao_nota_media_colaborador(
        datas=datas, id_colaborador=id_colaborador, min_dias=min_dias, 
        lista_secaos=lista_secaos, lista_os=lista_os, lista_modelo=lista_modelo,
        lista_oficina=lista_oficina
    )
    if df_os_analise.empty:
        return go.Figure()

    fig = generate_grafico_evolucao_nota(df_os_analise)
    return fig

@callback(
    Output("graph-evolucao-gasto-colaborador", "figure"), 
    [
        Input("input-lista-colaborador", "value"),
        Input("input-intervalo-datas-colaborador", "value"),
        Input("input-min-dias-colaborador", "value"),
        Input("input-select-secao-colaborador", "value"),
        Input("input-select-ordens-servico-colaborador", "value"),
        Input("input-select-modelos-colaborador", "value"),
        Input("input-select-oficina-colaborador", "value"),
    ],
    running=[(Output("loading-overlay", "visible"), True, False)],
)
def grafico_gasto_mes(id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina):
    '''plota grafico de evolução de retrabalho por ano'''
    
    # Validação dos inputs
    if (id_colaborador is None) or (datas is None) or (min_dias is None):
        return go.Figure()
    
    # Obtém análise estatística
    df_os_analise = colab.evolucao_gasto_colaborador(
        datas=datas, id_colaborador=id_colaborador, min_dias=min_dias, 
        lista_secaos=lista_secaos, lista_os=lista_os, lista_modelo=lista_modelo,
        lista_oficina=lista_oficina
    )
    if df_os_analise.empty:
        return go.Figure()

    fig = generate_grafico_evolucao_gasto(df_os_analise)
    return fig


    
# Callback para atualizar o link de download quando o botão for clicado
@callback(
    Output("download-excel", "data")
    ,
    [
        Input("btn-exportar", "n_clicks"),
        Input("input-lista-colaborador", "value"),
        Input("input-intervalo-datas-colaborador", "value"),
        Input("input-min-dias-colaborador", "value"),
        Input("input-select-secao-colaborador", "value"),
        Input("input-select-ordens-servico-colaborador", "value"),
        Input("input-select-modelos-colaborador", "value"),
        Input("input-select-oficina-colaborador", "value"),
    ],
    prevent_initial_call=True
)
def atualizar_download(n_clicks, id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina):
    if not n_clicks or n_clicks <= 0: # Garantre que ao iniciar ou carregar a page, o arquivo não seja baixado
        return dash.no_update
    
    date_now = datetime.now().strftime('%d-%m-%Y')
    
    df = colab.dados_tabela_do_colaborador(
        datas=datas, id_colaborador=id_colaborador, min_dias=min_dias, 
        lista_secaos=lista_secaos, lista_os=lista_os, lista_modelo=lista_modelo,
        lista_oficina=lista_oficina
    )
    excel_data = gerar_excel(df=df)
    return dcc.send_bytes(excel_data, f"tabela_os_retrabalho{date_now}.xlsx")



##############################################################################
layout = dbc.Container(
    [
        # Loading 
        dmc.LoadingOverlay(
            visible=True,
            id="loading-overlay",
            loaderProps={"size": "xl"},
            overlayProps={
                "radius": "lg",
                "blur": 2,
                "style": {
                    "top": 0,  # Start from the top of the viewport
                    "left": 0,  # Start from the left of the viewport
                    "width": "100vw",  # Cover the entire width of the viewport
                    "height": "100vh",  # Cover the entire height of the viewport
                },
            },
            zIndex=10,
        ),
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
                                        dbc.Col(DashIconify(icon="mdi:account-wrench", width=45), width="auto"),
                                        dbc.Col(
                                            html.H1(
                                                [
                                                    "Visão geral do\u00a0",
                                                    html.Strong("Colaborador"),
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
                                                    dbc.Label("Colaborador (Código):"),
                                                    dcc.Dropdown(
                                                        id="input-lista-colaborador",
                                                        options=[
                                                            {
                                                                "label": f"{linha['LABEL_COLABORADOR']}",
                                                                "value": linha["cod_colaborador"],
                                                            }
                                                            for ix, linha in df_mecanicos_todos.iterrows()
                                                        ],
                                                        placeholder="Selecione um colaborador",
                                                        value=3295,
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
                                                    dbc.Label("Data (intervalo) de análise"),
                                                    dmc.DatePicker(
                                                        id="input-intervalo-datas-colaborador",
                                                        allowSingleDateInRange=True,
                                                        type="range",
                                                        minDate=date(2024, 8, 1),
                                                        maxDate=datetime.now().date(),
                                                        value=[date(2024, 8, 1), datetime.now().date()],
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
                                                    dbc.Label("Tempo (em dias) entre OS para retrabalho"),
                                                    dcc.Dropdown(
                                                        id="input-min-dias-colaborador",
                                                        options=[
                                                            {"label": "10 dias", "value": 10},
                                                            {"label": "15 dias", "value": 15},
                                                            {"label": "30 dias", "value": 30},
                                                        ],
                                                        placeholder="Período em dias",
                                                        value=10,
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
                                                    dbc.Label("Seções (categorias) de manutenção"),
                                                    dcc.Dropdown(
                                                        id="input-select-secao-colaborador",
                                                        options=[
                                                            # {"label": "TODAS", "value": "TODAS"},
                                                            # {
                                                            #     "label": "BORRACHARIA",
                                                            #     "value": "MANUTENCAO BORRACHARIA",
                                                            # },
                                                            {
                                                                "label": "ELETRICA",
                                                                "value": "MANUTENCAO ELETRICA",
                                                            },
                                                            # {"label": "GARAGEM", "value": "MANUTENÇÃO GARAGEM"},
                                                            # {
                                                            #     "label": "LANTERNAGEM",
                                                            #     "value": "MANUTENCAO LANTERNAGEM",
                                                            # },
                                                            # {"label": "LUBRIFICAÇÃO", "value": "LUBRIFICAÇÃO"},
                                                            {
                                                                "label": "MECANICA",
                                                                "value": "MANUTENCAO MECANICA",
                                                            },
                                                            # {"label": "PINTURA", "value": "MANUTENCAO PINTURA"},
                                                            # {
                                                            #     "label": "SERVIÇOS DE TERCEIROS",
                                                            #     "value": "SERVIÇOS DE TERCEIROS",
                                                            # },
                                                            # {
                                                            #     "label": "SETOR DE ALINHAMENTO",
                                                            #     "value": "SETOR DE ALINHAMENTO",
                                                            # },
                                                            # {
                                                            #     "label": "SETOR DE POLIMENTO",
                                                            #     "value": "SETOR DE POLIMENTO",
                                                            # },
                                                        ],
                                                        multi=True,
                                                        value=["MANUTENCAO ELETRICA", "MANUTENCAO MECANICA"],
                                                        placeholder="Selecione uma ou mais seções...",
                                                    ),
                                                ],
                                                # className="dash-bootstrap",
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
                                                    dbc.Label("Oficinas"),
                                                    dcc.Dropdown(
                                                        id="input-select-oficina-colaborador",
                                                        options=[
                                                            {"label": "TODAS", "value": "TODAS"},
                                                            {
                                                                "label": "GARAGEM CENTRAL",
                                                                "value": "GARAGEM CENTRAL - RAL",
                                                            },
                                                            {
                                                                "label": "GARAGEM NOROESTE",
                                                                "value": "GARAGEM NOROESTE - RAL",
                                                            },
                                                            {
                                                                "label": "GARAGEM SUL",
                                                                "value": "GARAGEM SUL - RAL",
                                                            },
                                                        ],
                                                        multi=True,
                                                        value=["TODAS"],
                                                        placeholder="Selecione uma ou mais oficinas...",
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
                                                    dbc.Label("Modelo"),
                                                    dcc.Dropdown(
                                                        id="input-select-modelos-colaborador",

                                                        multi=True,
                                                        value=["TODAS"],
                                                        placeholder="Selecione um ou mais modelos...",
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
                                                    dbc.Label("Ordens de Serviço"),
                                                    dcc.Dropdown(
                                                        id="input-select-ordens-servico-colaborador",
                                                        multi=True,
                                                        value=["TODAS"],
                                                        placeholder="Selecione uma ou mais ordens de serviço...",
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
                    md=8,
                ),
                dbc.Col(
                    # Resumo
                    dbc.Row(
                        [
                            dbc.Row(
                                [
                                    # Cabeçalho
                                    html.Hr(),
                                    dbc.Col(
                                        DashIconify(icon="wpf:statistics", width=45),
                                        width="auto",
                                    ),
                                    dbc.Col(html.H1("Resumo", className="align-self-center"), width=True),
                                    dmc.Space(h=15),
                                    html.Hr(),
                                ],
                                align="center",
                            ),
                            # Gráfico de pizza com a relação entre Retrabalho e Correção
                            dcc.Graph(id="graph-pizza-sintese-colaborador"),
                        ]
                    ),
                    md=4,
                ),
            ]
        ),
        dmc.Space(h=30),
        # Estado
        dcc.Store(id="store-dados-colaborador-retrabalho"),
        # Graficos gerais
        html.Hr(),
        # Indicadores
        dbc.Row(
            [
                html.H4("Indicadores", style={"text-align": "center", "margin-bottom": "20px", 'font-size': '45px'}),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                dmc.Group(
                                    [
                                        dmc.Title(id="indicador-quantidade-servico", order=2),
                                        DashIconify(
                                            icon="mdi:bomb",
                                            width=48,
                                            color="black",
                                        ),
                                    ],
                                    justify="center",  # Centralize conteúdo no card
                                    mt="md",
                                    mb="xs",
                                ),
                            ),
                            dbc.CardFooter("Total de tipo serviços"),
                        ],
                        class_name="card-box-shadow",
                    ),
                    md=4,
                    style={"margin-bottom": "20px"},  # Adicione espaçamento inferior
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                dmc.Group(
                                    [
                                        dmc.Title(id="indicador-total-os-trabalho", order=2),
                                        DashIconify(
                                            icon="material-symbols:order-play-outline",
                                            width=48,
                                            color="black",
                                        ),
                                    ],
                                    justify="center",
                                    mt="md",
                                    mb="xs",
                                ),
                            ),
                            dbc.CardFooter("Total de OSs executadas"),
                        ],
                        class_name="card-box-shadow",
                    ),
                    md=4,
                    style={"margin-bottom": "20px"},
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                dmc.Group(
                                    [
                                        dmc.Title(id="indicador-rank-servico", order=2),
                                        DashIconify(
                                            icon="ion:analytics-sharp",
                                            width=48,
                                            color="black",
                                        ),
                                    ],
                                    justify="center",  # Centralize conteúdo no card
                                    mt="md",
                                    mb="xs",
                                ),
                            ),
                            dbc.CardFooter("Rank de serviços diferentes"),
                        ],
                        class_name="card-box-shadow",
                    ),
                    md=4,
                    style={"margin-bottom": "20px"},  # Adicione espaçamento inferior
                )
            ],
            justify="center",  # Centralize a linha inteira
        ),
        
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                dmc.Group(
                                    [
                                        dmc.Title(id="indicador-rank-os", order=2),
                                        DashIconify(
                                            icon="mdi:account-wrench",
                                            width=48,
                                            color="black",
                                        ),
                                    ],
                                    justify="center",  # Centralize conteúdo no card
                                    mt="md",
                                    mb="xs",
                                ),
                            ),
                            dbc.CardFooter("Rank de OSs absolutas"),
                        ],
                        class_name="card-box-shadow",
                    ),
                    md=4,
                    style={"margin-bottom": "20px"},  # Adicione espaçamento inferior
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                dmc.Group(
                                    [
                                        dmc.Title(id="indicador-retrabalho", order=2),
                                        DashIconify(
                                            icon="tabler:reorder",
                                            width=48,
                                            color="black",
                                        ),
                                    ],
                                    justify="center",
                                    mt="md",
                                    mb="xs",
                                ),
                            ),
                            dbc.CardFooter("% das OS são retrabalho"),
                        ],
                        class_name="card-box-shadow",
                    ),
                    md=4,
                    style={"margin-bottom": "20px"},
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                dmc.Group(
                                    [
                                        dmc.Title(id="indicador-nota-colaborador", order=2),
                                        DashIconify(
                                            icon="material-symbols-light:bar-chart-4-bars-rounded",
                                            width=48,
                                            color="black",
                                        ),
                                    ],
                                    justify="center",
                                    mt="md",
                                    mb="xs",
                                ),
                            ),
                            dbc.CardFooter("Nota do colaborador"),
                        ],
                        class_name="card-box-shadow",
                    ),
                    md=4,
                    style={"margin-bottom": "20px"},
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                dmc.Group(
                                    [
                                        dmc.Title(id="indicador-correcao-de-primeira", order=2),
                                        DashIconify(
                                            icon="game-icons:time-bomb",
                                            width=48,
                                            color="black",
                                        ),
                                    ],
                                    justify="center",
                                    mt="md",
                                    mb="xs",
                                ),
                            ),
                            dbc.CardFooter("OSs com correção de primeira"),
                        ],
                        class_name="card-box-shadow",
                    ),
                    md=4,
                    style={"margin-bottom": "20px"},
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                dmc.Group(
                                    [
                                        dmc.Title(id="indicador-rank-posicao-nota", order=2),
                                        DashIconify(
                                            icon="mdi:account-wrench",
                                            width=48,
                                            color="black",
                                        ),
                                    ],
                                    justify="center",  # Centralize conteúdo no card
                                    mt="md",
                                    mb="xs",
                                ),
                            ),
                            dbc.CardFooter("Posição da nota media"),
                        ],
                        class_name="card-box-shadow",
                    ),
                    md=4,
                    style={"margin-bottom": "20px"},
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                dmc.Group(
                                    [
                                        dmc.Title(id="indicador-gasto-total-colaborador", order=2),
                                        DashIconify(
                                            icon="mdi:wrench",
                                            width=48,
                                            color="black",
                                        ),
                                    ],
                                    justify="center",  # Centralize conteúdo no card
                                    mt="md",
                                    mb="xs",
                                ),
                            ),
                            dbc.CardFooter("Gasto total do colaborador"),
                        ],
                        class_name="card-box-shadow",
                    ),
                    md=4,
                    style={"margin-bottom": "20px"},
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardBody(
                                dmc.Group(
                                    [
                                        dmc.Title(id="indicador-gasto-retrabalho-total-colaborador", order=2),
                                        DashIconify(
                                            icon="mdi:wrench",
                                            width=48,
                                            color="black",
                                        ),
                                    ],
                                    justify="center",  # Centralize conteúdo no card
                                    mt="md",
                                    mb="xs",
                                ),
                            ),
                            dbc.CardFooter("Gasto total de Retrabalho do colaborador"),
                        ],
                        class_name="card-box-shadow",
                    ),
                    md=4,
                    style={"margin-bottom": "20px"},
                ),
            ],
            justify="center",
        ),
    ],
    style={"margin-top": "20px", "margin-bottom": "20px"},
    ),
        dmc.Space(h=40),
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="fluent:arrow-trending-text-20-filled", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Evolução das Métricas: Retrabalho e Correção de Primeira por mês",
                                className="align-self-center"
                            ),
                            dmc.Space(h=5),
                            gera_labels_inputs("colaborador-grafico-evolucao-nota-os"),
                        ]
                    ), width=True
                ),
            ],
            align="center",
        ),
        dcc.Graph(id="graph-evolucao-retrabalho-por-mes"),
        dbc.Row(dmc.Space(h=20)),
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="fluent:arrow-trending-text-20-filled", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Evolução das Métricas: Nota media ",
                                className="align-self-center"
                            ),
                            dmc.Space(h=5),
                            gera_labels_inputs("colaborador-grafico-evolucao-retrabalho"),
                        ]
                    ),width=True
                    
                ),
            ],
            align="center",
        ),
        dcc.Graph(id="graph-evolucao-nota-por-mes"),
        dbc.Row(dmc.Space(h=20)),
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="fluent:arrow-trending-text-20-filled", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Evolução das Métricas: Media de gasto por mês",
                                className="align-self-center"
                            ),
                            dmc.Space(h=5),
                            gera_labels_inputs("colaborador-grafico-evolucao-gasto"),
                        ]
                    ),width=True
                    
                ),
            ],
            align="center",
        ),
        dcc.Graph(id="graph-evolucao-gasto-colaborador"),
        dbc.Row(dmc.Space(h=20)),
        html.Hr(),
        dbc.Row(
            [
                # Gráfico de Pizza
                dbc.Col(dbc.Row([html.H4("Atuação Geral"),dmc.Space(h=5), gera_labels_inputs("colaborador-grafico-atuacao-geral"), dcc.Graph(id="graph-barra-atuacao-geral")]), md=4),
                # Indicadores
                dbc.Col(dbc.Row([html.H4("Atuação OS (TOP 10)"), dmc.Space(h=5),gera_labels_inputs("colaborador-graficos-atuacao-os"), dcc.Graph(id="graph-principais-os")]), md=8),
            ],
            align="center",
        ),
        dmc.Space(h=30),
        dbc.Row(
            [
                dbc.Col(DashIconify(icon="mdi:account-wrench", width=45), width="auto"),
                dbc.Col(
                    dbc.Row(
                        [
                            html.H4(
                                "Detalhamento do colaborador das OSs escolhidas",
                                className="align-self-center",
                            ),
                            dmc.Space(h=5),
                            dbc.Row(
                                [
                                    dbc.Col(gera_labels_inputs("tabela-colaborador-os"), width=True),
                                    dbc.Col(
                                        html.Div(
                                            [
                                                html.Button(
                                                    "Exportar para Excel",
                                                    id="btn-exportar",
                                                    n_clicks=0,
                                                    style={
                                                        "background-color": "#007bff",  # Azul
                                                        "color": "white",
                                                        "border": "none",
                                                        "padding": "10px 20px",
                                                        "border-radius": "8px",
                                                        "cursor": "pointer",
                                                        "font-size": "16px",
                                                        "font-weight": "bold",
                                                    },
                                                ),
                                                dcc.Download(id="download-excel"),
                                            ],
                                            style={"text-align": "right"},
                                        ),
                                        width="auto",
                                    ),
                                ],
                                align="center",
                                justify="between",  # Deixa os itens espaçados
                            ),
                        ]
                    ),
                    width=True,
                ),
            ],
            align="center",
        ),
        dmc.Space(h=20),    
        dag.AgGrid(
            id="tabela-top-os-colaborador",
            columnDefs=tbl_top_os_geral_retrabalho,
            rowData=[],
            defaultColDef={"filter": True, "floatingFilter": True},
            columnSize="autoSize",
            dashGridOptions={
                "localeText": locale_utils.AG_GRID_LOCALE_BR,
            },
            # style={"height": 400, "resize": "vertical", "overflow": "hidden"}, #-> permite resize
        ),
        dmc.Space(h=10),
    ]
)

