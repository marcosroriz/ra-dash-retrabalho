#!/usr/bin/env python
# coding: utf-8

# Arquivo que centraliza as tabelas utilizadas na página os

# Tabela Mecânicos
tbl_top_mecanicos = [
    {
        "field": "NOME_COLABORADOR",
        "headerName": "Colaborador",
        "pinned": "left",
    },
    {"field": "ID_COLABORADOR", "headerName": "ID", "filter": "agNumberColumnFilter", "minWidth": 120, "maxWidth": 120},
    # {
    #     "field": "TOTAL_TEMPO",
    #     "headerName": "SOMA DO TEMPO (PADRÃO)",
    #     "wrapHeaderText": True,
    #     "autoHeaderHeight": True,
    #     "filter": "agNumberColumnFilter",
    #     "type": ["numericColumn"],
    # },
    # {
    #     "field": "TOTAL_TEMPO_RETRABALHO",
    #     "headerName": "TEMPO EM RETRABALHO (PADRÃO)",
    #     "wrapHeaderText": True,
    #     "autoHeaderHeight": True,
    #     "filter": "agNumberColumnFilter",
    #     "type": ["numericColumn"],
    # },
    {
        "field": "TOTAL_DE_OS",
        "headerName": "TOTAL DE OS",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "filter": "agNumberColumnFilter",
        "type": ["numericColumn"],
    },
    {
        "field": "PERC_RETRABALHO",
        "headerName": "% OS RETRABALHOS",
        "filter": "agNumberColumnFilter",
        "valueFormatter": {"function": "params.value.toLocaleString('pt-BR') + '%'"},
        "type": ["numericColumn"],
    },
    {
        "field": "PERC_CORRECAO_PRIMEIRA",
        "headerName": "% OS CORREÇÕES DE PRIMEIRA",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "filter": "agNumberColumnFilter",
        "maxWidth": 160,
        "valueFormatter": {"function": "params.value.toLocaleString('pt-BR') + '%'"},
        "type": ["numericColumn"],
    },
    {
        "field": "TOTAL_PROBLEMA",
        "headerName": "TOTAL DE PROBLEMAS",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "maxWidth": 160,
        "filter": "agNumberColumnFilter",
        "type": ["numericColumn"],
    },
    {
        "field": "REL_OS_PROBLEMA",
        "headerName": "REL OS/PROBLEMA",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "valueFormatter": {"function": "params.value.toLocaleString('pt-BR')"},
        "filter": "agNumberColumnFilter",
        "type": ["numericColumn"],
    },
    {
        "field": "NOTA_MEDIA_SOLUCAO",
        "headerName": "NOTA MÉDIA (LLM)",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "maxWidth": 160,
        "valueFormatter": {"function": "params.value.toLocaleString('pt-BR')"},
        "filter": "agNumberColumnFilter",
        "type": ["numericColumn"],
    },
    {
        "field": "PERC_SOLUCAO_COERENTE",
        "headerName": "% SOLUÇÕES COERENTES (LLM)",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "maxWidth": 160,
        "filter": "agNumberColumnFilter",
        "valueFormatter": {"function": "params.value.toLocaleString('pt-BR') + '%'"},
        "type": ["numericColumn"],
    },
    {
        "field": "TOTAL_GASTO",
        "headerName": "TOTAL GASTO (PEÇAS)",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "maxWidth": 160,
        "valueFormatter": {
            "function": "'R$ ' + (params.value.toLocaleString('pt-BR', { maximumFractionDigits: 2, minimumFractionDigits: 2 }))"
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
            "function": "'R$ ' + (params.value.toLocaleString('pt-BR', { maximumFractionDigits: 2, minimumFractionDigits: 2 }))"
        },
        "filter": "agNumberColumnFilter",
        "type": ["numericColumn"],
    },
]

# Tabela veículos mais problemáticos
tbl_top_veiculos_problematicos = [
    {"field": "CODIGO DO VEICULO", "headerName": "VEÍCULO", "maxWidth": 150},
    {"field": "TOTAL_DE_PROBLEMAS", "headerName": "# PROBLEMAS"},
    {"field": "TOTAL_DE_OS", "headerName": "# OS"},
    {
        "field": "TOTAL_DIAS_ATE_CORRIGIR",
        "headerName": "TOTAL DE DIAS GASTOS ATÉ CORRIGIR",
    },
    {"field": "REL_PROBLEMA_OS", "headerName": "REL. PROB/OS"},
]


# Tabela OS
tbl_top_os = [
    {"field": "DIA", "headerName:": "DIA"},
    {"field": "NUMERO DA OS", "headerName": "OS"},
    {"field": "CODIGO DO VEICULO", "headerName": "VEÍCULO"},
    {"field": "DESCRICAO DO VEICULO", "headerName": "MODELO"},
    {"field": "DIAS_ATE_OS_CORRIGIR", "headerName": "DIAS ATÉ ESSA OS"},
]

# Tabel Veículos
tbl_top_vec = [
    {"field": "CODIGO DO VEICULO", "headerName": "VEÍCULO", "maxWidth": 150},
    {
        "field": "TOTAL_DIAS_ATE_CORRIGIR",
        "headerName": "TOTAL DE DIAS GASTOS ATÉ CORRIGIR",
    },
]

# Detalhes das OSs
# df_os_problematicas
tbl_detalhes_vec_os = [
    {"field": "problem_no", "headerName": "PROB", "maxWidth": 150},
    {"field": "NUMERO DA OS", "headerName": "OS", "maxWidth": 150},
    {"field": "DESCRICAO DO SERVICO", "headerName": "SERVIÇO", "minWidth": 200},
    {"field": "CLASSIFICACAO_EMOJI", "headerName": "STATUS", "maxWidth": 150},
    {"field": "LABEL_COLABORADOR", "headerName": "COLABORADOR"},
    {"field": "DIA_INICIO", "headerName": "INÍCIO", "minWidth": 150},
    {"field": "DIA_TERMINO", "headerName": "FECHAMENTO", "minWidth": 150},
    {"field": "DIAS_ENTRE_OS", "headerName": "DIFF DIAS COM ANT", "maxWidth": 120},
    {"field": "TOTAL_DE_OS", "headerName": "NUM OS ATÉ CORRIGIR", "maxWidth": 150},
    {
        "field": "COMPLEMENTO DO SERVICO",
        "headerName": "DESCRIÇÃO",
        "minWidth": 800,
        "wrapText": True,
        "autoHeight": True,
    },
]

