#!/usr/bin/env python
# coding: utf-8

# Arquivo que centraliza as tabelas utilizadas na página regra de monitoramento

# Tabela de regras existentes
tbl_regras_existentes = [
    {"field": "nome_regra", "headerName": "NOME DA REGRA", "minWidth": 250},
    {
        "field": "data_criacao",
        "headerName": "DATA DE CRIAÇÃO",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "minWidth": 120,
        "filter": "agDateColumnFilter",
        "valueFormatter": {
            "function": "params.value ? params.value.slice(8,10) + '/' + params.value.slice(5,7) + '/' + params.value.slice(0,4) : ''"
        },
    },
    {
        "field": "data_atualizacao",
        "headerName": "DATA DE ATUALIZAÇÃO",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "minWidth": 200,
        "filter": "agDateColumnFilter",
        "valueFormatter": {
            "function": "params.value ? params.value.slice(8,10) + '/' + params.value.slice(5,7) + '/' + params.value.slice(0,4) : ''"
        },
    },
    {
        "field": "relatorio",
        "headerName": "VER RELATÓRIO",
        "cellRenderer": "Button",
        "floatingFilter": False,
        "filter": False,
        "cellRendererParams": {"className": "btn btn-outline-primary btn-sm"},
    },
    {
        "field": "editar",
        "headerName": "EDITAR",
        "cellRenderer": "Button",
        "floatingFilter": False,
        "filter": False,
        "cellRendererParams": {"className": "btn btn-outline-warning btn-sm"},
    },
    {
        "field": "apagar",
        "headerName": "APAGAR",
        "cellRenderer": "Button",
        "floatingFilter": False,
        "filter": False,
        "cellRendererParams": {"className": "btn btn-outline-danger btn-sm"},
    },
]

# Tabela detalhamento do problema/OS que envolve a regra
tbl_detalhamento_problema_regra = [
    {"field": "status_os", "pinned": "left", "headerName": "STATUS", "minWidth": 200},
    {"field": "cod_colaborador", "headerName": "CÓDIGO DO COLABORADOR", "minWidth": 150},
    {"field": "nome_colaborador", "headerName": "COLABORADOR", "minWidth": 200},
    {"field": "DESCRICAO DO SERVICO", "headerName": "SERVIÇO", "minWidth": 250},
    {"field": "DESCRICAO DO MODELO", "headerName": "MODELO"},
    {"field": "CODIGO DO VEICULO", "headerName": "VEÍCULO", "maxWidth": 150},
    {"field": "NUMERO DA OS", "headerName": "OS", "minWidth": 150},
    {
        "headerName": "DATA DE ABERTURA DA OS",
        "field": "DATA DA ABERTURA DA OS DT",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "maxWidth": 180,
        "valueFormatter": {
            "function": "params.value ? params.value.slice(8,10) + '/' + params.value.slice(5,7) + '/' + params.value.slice(0,4) : ''"
        },
        "sort": "asc",
        "sortable": True,
    },
    {
        "headerName": "DATA DO FECHAMENTO DA OS",
        "field": "DATA DO FECHAMENTO DA OS DT",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "maxWidth": 180,
        "valueFormatter": {
            "function": "params.value ? params.value.slice(8,10) + '/' + params.value.slice(5,7) + '/' + params.value.slice(0,4) : ''"
        },
        "sortable": True,
    },
    {
        "field": "prev_days",
        "headerName": "DIAS OS ANTERIOR",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "maxWidth": 180,
        "valueFormatter": {"function": "params.value !== null ? params.value + ' dias' : '0 dias'"},
        "filter": "agNumberColumnFilter",
        "type": ["numericColumn"],
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
        "filter": "agNumberColumnFilter",
        "type": ["numericColumn"],
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
        "filter": "agNumberColumnFilter",
        "type": ["numericColumn"],
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
        "headerName": "PEÇAS TROCADAS NESTA OS",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "autoHeight": True,
        "wrapText": True,
        "minWidth": 550,
        "cellRenderer": "BulletViaStringRenderer",
    },
]
