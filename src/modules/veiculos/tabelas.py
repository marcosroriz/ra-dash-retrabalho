# Tabela Top OS de Retrabalho
tbl_top_os_geral_retrabalho = [
    {"field": "DESCRICAO DO SERVICO", "headerName": "DESCRIÇÃO (PROBLEMA)", "minWidth": 300},
    {"field": "TOTAL_OS", "headerName": "QTD DE OS'S", "minWidth": 200},
    {"field": "PERC_RETRABALHO", "headerName": "% RETRABALHO", "minWidth": 200, "valueFormatter": {"function": "params.value + '%'"},},
    # {
    #     "field": "TOTAL_OS",
    #     "headerName": "MÉDIA",
    #     "wrapHeaderText": True,
    #     "autoHeaderHeight": True,
    #     "maxWidth": 160,
    #     "filter": "agNumberColumnFilter",
    #     "type": ["numericColumn"],
    # },
    {
        "field": "PERC_CORRECAO_PRIMEIRA",
        "headerName": "% CORREÇÃO DE PRIMEIRA",
        "filter": "agNumberColumnFilter",
        "maxWidth": 230,
        "valueFormatter": {"function": "params.value + '%'"},
        "type": ["numericColumn"],
    },
    {
        "field": "QUANTIDADE DE PECAS",
        "headerName": "PEÇAS TROCADAS/OS",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "filter": "agNumberColumnFilter",
        "maxWidth": 230,
        "type": ["numericColumn"],
    },
    {
        "field": "VALOR_",
        "headerName": "VALOR TOTAL",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "filter": "agNumberColumnFilter",
        "maxWidth": 160,
        "type": ["numericColumn"],
        "valueFormatter": {"function": "'R$' + Number(params.value).toFixed(2).toLocaleString()"},
    },
    {
        "field": "TOTAL_GASTO_RETRABALHO_",
        "headerName": "VALOR DO RETRABALHO",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "filter": "agNumberColumnFilter",
        "maxWidth": 160,
        "type": ["numericColumn"],
        "valueFormatter": {"function": "'R$' + Number(params.value).toFixed(2).toLocaleString()"},
    },

    # {
    #     "field": "TOTAL_PROBLEMA", 
    #     "headerName": "MÉDIA DE TROCA DE PEÇAS PARA ESSE MODELO",
    #     "wrapHeaderText": True,
    #     "autoHeaderHeight": True,
    #     "filter": "agNumberColumnFilter",
    #     "maxWidth": 160,
    #     "type": ["numericColumn"],
    # },
    # {
    #     "field": "QUANTIDADE DE COLABORADORES",
    #     "headerName": "COLABORADORES",
    #     "wrapHeaderText": True,
    #     "autoHeaderHeight": True,
    #     "maxWidth": 160,
    #     "filter": "agNumberColumnFilter",
    #     "type": ["numericColumn"],
    # },
]

#Tabela ranking de peças por modelo
tbl_ranking_por_modelo = [
    {"field": "POSICAO", "headerName": "POSIÇÃO", "minWidth": 200, "valueFormatter": {"function": "params.value + 'º'"},},
    {"field": "VEICULO", "headerName": "VEÍCULO", "minWidth": 250},
    {"field": "MODELO", "headerName": "MODELO", "minWidth": 550},
    {
        "field": "VALOR",
        "headerName": "VALOR GASTO",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "filter": "agNumberColumnFilter",
        "minWidth": 290,
        "type": ["numericColumn"],
    },
]


# Tabela Top OS Colaborador
tbl_top_colaborador_geral_retrabalho = [
    {"field": "NOME_COLABORADOR", "headerName": "Colaborador"},
    {"field": "ID_COLABORADOR", "headerName": "ID", "filter": "agNumberColumnFilter"},
    {
        "field": "TOTAL_OS",
        "headerName": "TOTAL DE OS",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "filter": "agNumberColumnFilter",
        "type": ["numericColumn"],
    },
    {
        "field": "PERC_RETRABALHO",
        "headerName": "% RETRABALHOS",
        "filter": "agNumberColumnFilter",
        "valueFormatter": {"function": "params.value + '%'"},
        "type": ["numericColumn"],
    },
    {
        "field": "PERC_CORRECAO_PRIMEIRA",
        "headerName": "% CORREÇÕES DE PRIMEIRA",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "filter": "agNumberColumnFilter",
        "valueFormatter": {"function": "params.value + '%'"},
        "type": ["numericColumn"],
    },
    {
        "field": "TOTAL_PROBLEMA",
        "headerName": "TOTAL DE PROBLEMA",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "filter": "agNumberColumnFilter",
        "type": ["numericColumn"],
    },
    {
        "field": "REL_OS_PROBLEMA",
        "headerName": "REL OS/PROBLEMA",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "filter": "agNumberColumnFilter",
        "type": ["numericColumn"],
    },
]

