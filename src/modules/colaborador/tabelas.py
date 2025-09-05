#!/usr/bin/env python
# coding: utf-8

# Arquivo que centraliza as tabelas utilizadas na página retrabalho colaborador

# Tabela Top OS de Retrabalho
tbl_top_os_geral_retrabalho = [
    {
        "field": "DESCRICAO DA OFICINA",
        "headerName": "OFICINA",
        "minWidth": 200,
    },
    {"field": "DESCRICAO DA SECAO", "headerName": "SEÇÃO", "minWidth": 200},
    {"field": "DESCRICAO DO SERVICO", "pinned": "left", "headerName": "SERVIÇO", "minWidth": 250},
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
        "valueFormatter": {"function": "params.value !== null ? params.value + '%' : '0%'"},
        "type": ["numericColumn"],
    },
    {
        "field": "PERC_RETRABALHO",
        "headerName": "% RETRABALHOS",
        "filter": "agNumberColumnFilter",
        "maxWidth": 160,
        "valueFormatter": {"function": "params.value !== null ? params.value + '%' : '0%'"},
        "type": ["numericColumn"],
    },
    {
        "field": "PERC_CORRECAO_PRIMEIRA",
        "headerName": "% CORREÇÕES DE PRIMEIRA",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "filter": "agNumberColumnFilter",
        "maxWidth": 250,
        "valueFormatter": {"function": "params.value !== null ? params.value + '%' : '0%'"},
        "type": ["numericColumn"],
        "minWidth": 200,
    },
    {
        "field": "nota_media_colaborador",
        "headerName": "NOTA MÉDIA DO COLABORADOR",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "filter": "agNumberColumnFilter",
        "maxWidth": 150,
        "type": ["numericColumn"],
        "minWidth": 200,
    },
    {
        "field": "nota_media_os",
        "headerName": "NOTA MÉDIA DA OS",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "filter": "agNumberColumnFilter",
        "maxWidth": 150,
        "type": ["numericColumn"],
        "minWidth": 200,
    },
    {
        "field": "TOTAL_GASTO",
        "headerName": "TOTAL GASTO (PEÇAS)",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "maxWidth": 160,
        "valueFormatter": {
            "function": "params.value !== null ? 'R$ ' + params.value.toLocaleString('pt-BR', { maximumFractionDigits: 2, minimumFractionDigits: 2 }) : 'R$ 0,00'"
        },
        "filter": "agNumberColumnFilter",
        "type": ["numericColumn"],
    },
    {
        "field": "TOTAL_GASTO_RETRABALHO",
        "headerName": "TOTAL GASTO RETRABALHO (PEÇAS)",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "maxWidth": 200,
        "valueFormatter": {
            "function": "params.value !== null ? 'R$ ' + params.value.toLocaleString('pt-BR', { maximumFractionDigits: 2, minimumFractionDigits: 2 }) : 'R$ 0,00'"
        },
        "filter": "agNumberColumnFilter",
        "type": ["numericColumn"],
    },
    {
        "field": "PERC_GASTO_RETRABALHO",
        "headerName": "% GASTO RETRABALHO",
        "filter": "agNumberColumnFilter",
        "maxWidth": 200,
        "valueFormatter": {"function": "params.value !== null ? params.value + '%' : '0%'"},
        "type": ["numericColumn"],
    },
]

# Tabela detalhamento da OS do colaborador
tbl_detalhamento_os_colaborador = [
    {"field": "status_os", "pinned": "left", "headerName": "STATUS", "minWidth": 200},
    {
        "field": "acao",
        "headerName": "DETALHAR OS",
        "cellRenderer": "Button",
        "cellRendererParams": {"className": "btn btn-outline-primary btn-sm"},
        "minWidth": 150,
        "pinned": "left",
    },
    {"field": "DESCRICAO DO SERVICO", "headerName": "SERVIÇO", "minWidth": 250},
    {"field": "DESCRICAO DO MODELO", "headerName": "MODELO"},
    {"field": "CODIGO DO VEICULO", "headerName": "VEÍCULO", "maxWidth": 150},
    {"field": "problem_no", "headerName": "PROBLEMA", "maxWidth": 150},
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
        "headerName": "PEÇAS TROCADAS",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "autoHeight": True,
        "wrapText": True,
        "minWidth": 550,
        "cellRenderer": "BulletViaStringRenderer",
    },
]


# Tabela detalhamento do problema/OS que envolve o colaborador
tbl_detalhamento_problema_colaborador = [
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
        "field": "diff_abertura_proxima_dias",
        "headerName": "DIAS PRÓXIMA OS",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "maxWidth": 180,
        "valueFormatter": {
            "function": "params.value !== null ? params.value + ' dias' : '0 dias'"
        },
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
        "headerName": "PEÇAS TROCADAS",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "autoHeight": True,
        "wrapText": True,
        "minWidth": 550,
        "cellRenderer": "BulletViaStringRenderer",
    },
]
