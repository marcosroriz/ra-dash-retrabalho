#!/usr/bin/env python
# coding: utf-8

# Arquivo que centraliza as tabelas utilizadas na página de relatórios

# Tabela de relatorios existentes
tbl_relatorios_existentes = [
    {"field": "nome", "headerName": "NOME DO RELATÓRIO", "minWidth": 200},
    {
        "field": "created_at",
        "headerName": "DATA DE CRIAÇÃO",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "minWidth": 120,
        "filter": "agDateColumnFilter",
        "valueFormatter": {
            "function": "params.value ? params.value.slice(8,10) + '/' + params.value.slice(5,7) + '/' + params.value.slice(0,4) + ' ' + params.value.slice(11,16) : ''"
        },
    },
    {
        "field": "executed_at",
        "headerName": "ÚLTIMO RELATÓRIO",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "minWidth": 200,
        "filter": "agDateColumnFilter",
        "valueFormatter": {
            "function": "params.value ? params.value.slice(8,10) + '/' + params.value.slice(5,7) + '/' + params.value.slice(0,4) + ' ' + params.value.slice(11,16) : ''"
        },
    },
    {
        "field": "acao_relatorio",
        "headerName": "VER RELATÓRIO",
        "cellRenderer": "Button",
        "floatingFilter": False,
        "filter": False,
        "minWidth": 150,
        "cellRendererParams": {"className": "btn btn-outline-primary btn-sm"},
    },
    {
        "field": "acao_editar",
        "headerName": "EDITAR",
        "cellRenderer": "Button",
        "floatingFilter": False,
        "filter": False,
        "minWidth": 120,
        "cellRendererParams": {"className": "btn btn-outline-warning btn-sm"},
    },
    {
        "field": "acao_apagar",
        "headerName": "APAGAR",
        "cellRenderer": "Button",
        "floatingFilter": False,
        "filter": False,
        "minWidth": 130,
        "cellRendererParams": {"className": "btn btn-outline-danger btn-sm"},
    },
]
