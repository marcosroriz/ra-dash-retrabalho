#!/usr/bin/env python
# coding: utf-8

# Arquivo que centraliza as tabelas utilizadas na página de detalhamento por OS

# Tabela detalhamento do problema/OS
tbl_detalhamento_problema_os = [
    {"field": "status_os", "pinned": "left", "headerName": "STATUS", "minWidth": 250},
    {"field": "problem_no", "headerName": "PROBLEMA", "minWidth": 150},
    {
        "field": "COLABORADOR QUE EXECUTOU O SERVICO",
        "headerName": "CÓDIGO DO COLABORADOR",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "maxWidth": 150,
    },
    {"field": "nome_colaborador", "headerName": "COLABORADOR", "minWidth": 200},
    {"field": "NUMERO DA OS", "headerName": "OS", "minWidth": 120},
    {
        "headerName": "DATA DE ABERTURA DA OS",
        "field": "DATA DA ABERTURA DA OS DT",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "maxWidth": 200,
        "valueFormatter": {
            "function": "params.value ? params.value.slice(8,10) + '/' + params.value.slice(5,7) + '/' + params.value.slice(0,4) + ' ' + params.value.slice(11,13) + ':' + params.value.slice(14,16) : ''"
        },
        "sort": "desc",
        "sortable": True,
    },
    {
        "headerName": "DATA DO FECHAMENTO DA OS",
        "field": "DATA DO FECHAMENTO LABEL",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "maxWidth": 200,
        # "valueFormatter": {
        #     "function": "params.value ? params.value.slice(8,10) + '/' + params.value.slice(5,7) + '/' + params.value.slice(0,4) : ''"
        # },
        "sortable": True,
    },
    {
        "field": "next_days",
        "headerName": "DIAS PRÓXIMA OS",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "maxWidth": 180,
        "valueFormatter": {"function": "params.value !== null ? params.value + ' dias' : 'NÃO HÁ'"},
    },
    {
        "field": "SINTOMA",
        "headerName": "SINTOMA (TEXTO DO COLABORADOR)",
        "minWidth": 300,
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "autoHeight": True,
        "wrapText": True,
    },
    {
        "field": "SCORE_SYMPTOMS_TEXT_QUALITY",
        "headerName": "NOTA SINTOMA (LLM)",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "valueFormatter": {"function": "params.value !== null ? params.value : 'NÃO CLASSIFICADO'"},
        "minWidth": 180,
    },
    {
        "field": "CORRECAO",
        "headerName": "CORREÇÃO (TEXTO DO COLABORADOR)",
        "minWidth": 500,
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "autoHeight": True,
        "wrapText": True,
    },
    {
        "field": "SCORE_SOLUTION_TEXT_QUALITY",
        "headerName": "NOTA SOLUÇÃO (LLM)",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "valueFormatter": {"function": "params.value !== null ? params.value : 'NÃO CLASSIFICADO'"},
        "minWidth": 180,
    },
    {
        "field": "WHY_SOLUTION_IS_PROBLEM",
        "headerName": "JUSTIFICATIVA (LLM)",
        "minWidth": 600,
        "autoHeight": True,
        "wrapText": True,
    },
    {
        "field": "total_valor",
        "headerName": "TOTAL GASTO (PEÇAS)",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "maxWidth": 150,
        "valueFormatter": {
            "function": "params.value !== null ? 'R$ ' + params.value.toLocaleString('pt-BR', { maximumFractionDigits: 2, minimumFractionDigits: 2 }) : 'R$ 0,00'"
        },
        "filter": "agNumberColumnFilter",
        "type": ["numericColumn"],
    },
    {
        "field": "pecas_trocadas_str",
        "headerName": "PEÇAS TROCADAS",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "autoHeight": True,
        "wrapText": True,
        "minWidth": 550,
        "cellRenderer": "BulletViaStringRenderer",
    },
]
