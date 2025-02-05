#!/usr/bin/env python
# coding: utf-8

import pandas as pd

# Funções utilitárias para obtenção das principais entidades do sistema


def get_garagens(dbEngine):
    # Oficinas
    return pd.read_sql(
        """
        SELECT 
            DISTINCT "DESCRICAO DA OFICINA" AS "LABEL"
        FROM 
            mat_view_retrabalho_10_dias mvrd 
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
        """,
        dbEngine,
    )


def get_mecanicos(dbEngine):
    # Colaboradores / Mecânicos
    return pd.read_sql("SELECT * FROM colaboradores_frotas_os", dbEngine)


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
