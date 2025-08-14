#!/usr/bin/env python
# coding: utf-8

# Bibliotecas padrão
import io
import re
import pandas as pd

# Funções utilitárias para obtenção das principais entidades do sistema


def get_linhas(dbEngine):
    # Linhas
    return pd.read_sql(
        """
        SELECT 
            DISTINCT "linhanumero" AS "LABEL"
        FROM 
            rmtc_linha_info
        ORDER BY
            "linhanumero"
        """,
        dbEngine,
    )


def get_oficinas(dbEngine):
    # Oficinas
    return pd.read_sql(
        """
        SELECT 
            DISTINCT "DESCRICAO DA OFICINA" AS "LABEL"
        FROM 
            mat_view_retrabalho_10_dias mvrd 
        ORDER BY 
            "DESCRICAO DA OFICINA"
        """,
        dbEngine,
    )


def get_secoes(dbEngine):
    # Seções
    return pd.read_sql(
        """
        SELECT 
            DISTINCT "DESCRICAO DA SECAO" AS "LABEL"
        FROM 
            mat_view_retrabalho_10_dias mvrd
        ORDER BY 
            "DESCRICAO DA SECAO"
        """,
        dbEngine,
    )


def get_mecanicos(dbEngine):
    # Colaboradores / Mecânicos
    df = pd.read_sql(
        """
        SELECT DISTINCT "COLABORADOR QUE EXECUTOU O SERVICO" as "CODIGO", cfo.id, cfo.cod_colaborador, cfo.nome_colaborador 
        FROM mat_view_retrabalho_10_dias mvrd 
        LEFT JOIN colaboradores_frotas_os cfo 
        ON mvrd."COLABORADOR QUE EXECUTOU O SERVICO" = cfo.cod_colaborador 
        """,
        dbEngine,
    )
    df["nome_colaborador"] = df["nome_colaborador"].fillna("Não informado").infer_objects(copy=False)
    df["LABEL_COLABORADOR"] = (
        df["nome_colaborador"].apply(lambda x: re.sub(r"(?<!^)([A-Z])", r" \1", x))
        + " (" + df["CODIGO"].astype(int).astype(str) + ")"
    )
    df.sort_values(by="LABEL_COLABORADOR", inplace=True)

    return df


def get_lista_os(dbEngine):
    # Lista de OS
    return pd.read_sql(
        """
        SELECT DISTINCT
            "DESCRICAO DA SECAO" as "SECAO",
            "DESCRICAO DO SERVICO" AS "LABEL"
        FROM 
            mat_view_retrabalho_10_dias mvrd 
        ORDER BY
            "DESCRICAO DO SERVICO"
        """,
        dbEngine,
    )


def get_modelos(dbEngine):
    # Lista de OS
    return pd.read_sql(
        """
        SELECT DISTINCT
            "DESCRICAO DO MODELO" AS "MODELO"
        FROM 
            mat_view_retrabalho_10_dias mvrd
        """,
        dbEngine,
    )


def gerar_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Dados")
    output.seek(0)
    return output.getvalue()
