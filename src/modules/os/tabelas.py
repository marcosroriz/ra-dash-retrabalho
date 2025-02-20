#!/usr/bin/env python
# coding: utf-8

# Arquivo que centraliza as tabelas utilizadas na página os

# Tabela Mecânicos
tbl_top_mecanicos = [
    {
        "field": "LABEL_COLABORADOR",
        "headerName": "COLABORADOR",
        "pinned": "left",
        "minWidth": 200,
    },
    {"field": "NUM_PROBLEMAS", "headerName": "# PROBLEMAS"},
    {"field": "TOTAL_DE_OS", "headerName": "# OS"},
    {"field": "RETRABALHOS", "headerName": "# RETRABALHOS"},
    {"field": "CORRECOES", "headerName": "# CORREÇÕES"},
    {
        "field": "CORRECOES_DE_PRIMEIRA",
        "headerName": "# CORREÇÕES DE PRIMEIRA",
        "maxWidth": 150,
    },
    {
        "field": "PERC_RETRABALHO",
        "headerName": "% RETRABALHOS",
        "valueFormatter": {"function": "params.value + '%'"},
        "type": ["numericColumn"],
    },
    {
        "field": "PERC_CORRECOES",
        "headerName": "% CORREÇÕES",
        "valueFormatter": {"function": "params.value + '%'"},
        "type": ["numericColumn"],
    },
    {
        "field": "PERC_CORRECOES_DE_PRIMEIRA",
        "headerName": "% CORREÇÕES DE PRIMEIRA",
        "valueFormatter": {"function": "params.value + '%'"},
        "type": ["numericColumn"],
        "maxWidth": 150,
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

