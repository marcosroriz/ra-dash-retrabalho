#!/usr/bin/env python
# coding: utf-8

# Arquivo que centraliza as tabelas utilizadas na página retrabalho colaboraddor

# Tabela Top OS de Retrabalho
tbl_top_os_geral_retrabalho = [
    {"field": "DESCRICAO DA OFICINA", "headerName": "OFICINA", "filter": "agSetColumnFilter", "minWidth": 200},
    {"field": "DESCRICAO DA SECAO", "headerName": "SEÇÃO", "filter": "agSetColumnFilter", "minWidth": 200},
    {"field": "DESCRICAO DO SERVICO", "headerName": "SERVIÇO", "filter": "agSetColumnFilter", "minWidth": 250},
    {
        "field": "TOTAL_OS",
        "headerName": "TOTAL DE OS",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "maxWidth": 160,
        "filter": "agNumberColumnFilter",
        "type": ["numericColumn"],
    },
    {
        "field": "PERC_TOTAL_OS",
        "headerName": "% OS",
        "filter": "agNumberColumnFilter",
        "maxWidth": 160,
        "valueFormatter": {"function": "params.value + '%'"},
        "type": ["numericColumn"],
    },
    {
        "field": "PERC_RETRABALHO",
        "headerName": "% RETRABALHOS",
        "filter": "agNumberColumnFilter",
        "maxWidth": 160,
        "valueFormatter": {"function": "params.value + '%'"},
        "type": ["numericColumn"],
    },
    {
        "field": "PERC_CORRECAO_PRIMEIRA",
        "headerName": "% CORREÇÕES DE PRIMEIRA",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "filter": "agNumberColumnFilter",
        "maxWidth": 250,
        "valueFormatter": {"function": "params.value + '%'"},
        "type": ["numericColumn"],
        "minWidth": 200
    },
    {
        "field": "nota_media_colaborador",
        "headerName": "NOTA MEDIA DO COLABORADOR",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "filter": "agNumberColumnFilter",
        "maxWidth": 150,
        "type": ["numericColumn"],
        "minWidth": 200
    },
    {
        "field": "nota_media_os",
        "headerName": "NOTA MEDIA DA OS",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "filter": "agNumberColumnFilter",
        "maxWidth": 150,
        "type": ["numericColumn"],
        "minWidth": 200
    },

]