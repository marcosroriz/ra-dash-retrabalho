#!/usr/bin/env python
# coding: utf-8

# Classe que centraliza os serviços para mostrar na página de detalhamento de OS

# Imports básicos
import pandas as pd
import numpy as np
import re

# Imports auxiliares
from modules.sql_utils import subquery_oficinas, subquery_secoes, subquery_os, subquery_modelos
from modules.service_utils import definir_status, definir_status_label, definir_emoji_status

# Imports do tema
import tema


class OSService:
    def __init__(self, dbEngine):
        self.pgEngine = dbEngine

    def os_existe(self, os_numero, min_dias):
        """Verifica se a OS existe"""
        query = f"""
        SELECT 
            1
        FROM 
            mat_view_retrabalho_{min_dias}_dias m
        WHERE 
            m."NUMERO DA OS" = '{os_numero}'
        """
        df_os_existe = pd.read_sql(query, self.pgEngine)

        return not df_os_existe.empty

    def obtem_detalhamento_os(self, os_numero, min_dias):
        """Retorna dados de detalhamento de uma OS específica"""
        # Query
        query = f"""
        WITH 
        pecas_agg AS (
            SELECT 
                pg."OS", 
                SUM(pg."VALOR") AS total_valor, 
                STRING_AGG(pg."VALOR"::TEXT, '__SEP__' ORDER BY pg."PRODUTO") AS pecas_valor_str,
                STRING_AGG(pg."PRODUTO"::text, '__SEP__' ORDER BY pg."PRODUTO") AS pecas_trocadas_str
            FROM 
                view_pecas_desconsiderando_combustivel pg 
            GROUP BY 
                pg."OS"
        ),
        os_alvo AS (
            SELECT 
                "NUMERO DA OS",
                "DESCRICAO DO SERVICO",
                "CODIGO DO VEICULO"
            FROM 
                mat_view_retrabalho_{min_dias}_dias_distinct m
            WHERE 
                m."NUMERO DA OS" = '{os_numero}'
        ),
        os_correlatas AS (
            SELECT
                todas.*
            FROM 
                mat_view_retrabalho_{min_dias}_dias todas
            JOIN 
                os_alvo alvo
            ON
                todas."CODIGO DO VEICULO" = alvo."CODIGO DO VEICULO"
            AND todas."DESCRICAO DO SERVICO" = alvo."DESCRICAO DO SERVICO"
        ),
        os_avaliadas AS (
            SELECT
                *
            FROM
                os_correlatas m
            LEFT JOIN 
                os_dados_classificacao odc
            ON 
                m."KEY_HASH" = odc."KEY_HASH" 
        ),
        os_avaliadas_com_pecas AS (
            SELECT 
                *
            FROM 
                os_avaliadas os
            LEFT JOIN 
                pecas_agg p
            ON 
                os."NUMERO DA OS" = p."OS"
        )
        SELECT 
            *
        FROM 
            os_avaliadas_com_pecas os
        LEFT JOIN 
            colaboradores_frotas_os cfo 
        ON 
            os."COLABORADOR QUE EXECUTOU O SERVICO" = cfo.cod_colaborador
        ORDER BY
            os."DATA DO FECHAMENTO DA OS" DESC
        """
        print("------")
        print(query)
        df_os_detalhada = pd.read_sql(query, self.pgEngine)

        df_os_detalhada["DATA DA ABERTURA DA OS DT"] = pd.to_datetime(df_os_detalhada["DATA DA ABERTURA DA OS"])
        df_os_detalhada["DATA DO FECHAMENTO DA OS DT"] = pd.to_datetime(df_os_detalhada["DATA DO FECHAMENTO DA OS"])
        df_os_detalhada["DATA DA ABERTURA LABEL"] = df_os_detalhada["DATA DA ABERTURA DA OS DT"].dt.strftime(
            "%d/%m/%Y %H:%M"
        )
        df_os_detalhada["DATA DO FECHAMENTO LABEL"] = df_os_detalhada["DATA DO FECHAMENTO DA OS DT"].dt.strftime(
            "%d/%m/%Y %H:%M"
        )

        # Preenche valores nulos do colaborador
        df_os_detalhada["nome_colaborador"] = df_os_detalhada["nome_colaborador"].fillna("Não Informado")

        # Preenche valores nulos de peças
        df_os_detalhada["total_valor"] = df_os_detalhada["total_valor"].fillna(0)
        df_os_detalhada["pecas_valor_str"] = df_os_detalhada["pecas_valor_str"].fillna("0")
        df_os_detalhada["pecas_trocadas_str"] = df_os_detalhada["pecas_trocadas_str"].fillna("Nenhuma")

        # Preenche valores nulos da LLM
        df_os_detalhada["WHY_SOLUTION_IS_PROBLEM"] = df_os_detalhada["WHY_SOLUTION_IS_PROBLEM"].fillna(
            "Não classificado"
        )
        df_os_detalhada["SINTOMA"] = df_os_detalhada["SINTOMA"].fillna("Não Informado")
        df_os_detalhada["CORRECAO"] = df_os_detalhada["CORRECAO"].fillna("Não Informado")

        # Aplica a função para definir o status de cada OS
        df_os_detalhada["status_os"] = df_os_detalhada.apply(definir_status, axis=1)
        df_os_detalhada["status_os_label"] = df_os_detalhada.apply(definir_status_label, axis=1)
        df_os_detalhada["status_os_emoji"] = df_os_detalhada.apply(definir_emoji_status, axis=1)

        return df_os_detalhada
