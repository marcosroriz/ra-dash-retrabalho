# Tabela Top Categorias de Problemas do Veículo
tbl_top_servicos_categorizados_veiculo = [
    {"field": "DESCRICAO DO SERVICO", "pinned": "left", "headerName": "SERVIÇO", "minWidth": 250},
    {"field": "DESCRICAO DA SECAO", "headerName": "SEÇÃO", "minWidth": 200},
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
        "sort": "desc",
        "sortable": True,
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
]

# Tabela detalhamento da OS do veículo
tbl_detalhamento_os_pecas_veiculo = [
    {"field": "NUMERO DA OS", "headerName": "OS", "minWidth": 150, "pinned": "left"},
    {
        "field": "acao",
        "headerName": "DETALHAR OS",
        "cellRenderer": "Button",
        "cellRendererParams": {"className": "btn btn-outline-primary btn-sm"},
        "minWidth": 150,
        "pinned": "left",
    },
    {"field": "status_os", "pinned": "left", "headerName": "STATUS", "minWidth": 200},
    {"field": "DESCRICAO DO SERVICO", "headerName": "SERVIÇO", "minWidth": 250},
    {
        "headerName": "DATA DE ABERTURA DA OS",
        "field": "DATA DA ABERTURA DA OS DT",
        "wrapHeaderText": True,
        "autoHeaderHeight": True,
        "maxWidth": 180,
        "valueFormatter": {
            "function": "params.value ? params.value.slice(8,10) + '/' + params.value.slice(5,7) + '/' + params.value.slice(0,4) : ''"
        },
        "sort": "desc",
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
        "minWidth": 350,
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
        "headerName": "PEÇAS TROCADAS",
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

