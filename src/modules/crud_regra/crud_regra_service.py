#!/usr/bin/env python
# coding: utf-8

# Classe que centraliza os serviços para CRUD de regras

# Imports básicos
import re
import pandas as pd
import numpy as np

# Imports auxiliares
from modules.sql_utils import subquery_oficinas, subquery_secoes, subquery_os, subquery_modelos
from modules.entities_utils import get_mecanicos


# Classe do serviço
class CRUDRegraService:
    def __init__(self, dbEngine):
        self.dbEngine = dbEngine


    def get_sintese_geral(self, data_periodo_regra, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os):
        """Função para obter a síntese geral (que será usado para o gráfico de pizza)"""

        # Remove min_dias antes para evitar que a última OS não seja retrabalho
        # data_fim = pd.to_datetime(datas[1])
        # data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        # data_fim_str = data_fim.strftime("%Y-%m-%d")

        # Subqueries
        subquery_modelos_str = subquery_modelos(lista_modelos, termo_all="TODOS")
        subquery_oficinas_str = subquery_oficinas(lista_oficinas)
        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)

        # Query
        query = f"""
            SELECT
                COUNT(*) AS "TOTAL_NUM_OS",
                SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END) AS "TOTAL_RETRABALHO",
                SUM(CASE WHEN correcao THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO",
                SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO_PRIMEIRA",
                SUM(CASE WHEN nova_os_com_retrabalho_anterior THEN 1 ELSE 0 END) AS "TOTAL_NOVA_OS_COM_RETRABALHO_ANTERIOR",
                SUM(CASE WHEN nova_os_sem_retrabalho_anterior THEN 1 ELSE 0 END) AS "TOTAL_NOVA_OS_SEM_RETRABALHO_ANTERIOR",
                100 * ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
                100 * ROUND(SUM(CASE WHEN correcao THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO",
                100 * ROUND(SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA",
                100 * ROUND(SUM(CASE WHEN nova_os_com_retrabalho_anterior THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_NOVA_OS_COM_RETRABALHO_ANTERIOR",
                100 * ROUND(SUM(CASE WHEN nova_os_sem_retrabalho_anterior THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_NOVA_OS_SEM_RETRABALHO_ANTERIOR"
            FROM
                mat_view_retrabalho_{min_dias}_dias_distinct
            WHERE
                "DATA DA ABERTURA DA OS"::timestamp BETWEEN CURRENT_DATE - INTERVAL '{data_periodo_regra} days' AND CURRENT_DATE
                {subquery_modelos_str}
                {subquery_oficinas_str}
                {subquery_secoes_str}
                {subquery_os_str}
        """
        print("--------------------------------")
        print(query)

        # Executa a query
        df = pd.read_sql(query, self.dbEngine)

        # Calcula o total de correções tardia
        df["TOTAL_CORRECAO_TARDIA"] = df["TOTAL_CORRECAO"] - df["TOTAL_CORRECAO_PRIMEIRA"]

        return df


    def get_previa_os_regra(self, data_periodo_regra, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os):
        """Função para obter a prévia das OS detectadas pela regra (que será usado para envio do e-mail / WhatsApp)"""

        # Subqueries
        subquery_modelos_str = subquery_modelos(lista_modelos, termo_all="TODOS")
        subquery_oficinas_str = subquery_oficinas(lista_oficinas)
        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)

        # Query
        query = f"""
            SELECT
                *
            FROM
                mat_view_retrabalho_{min_dias}_dias_distinct
            WHERE
                "DATA DA ABERTURA DA OS"::timestamp BETWEEN CURRENT_DATE - INTERVAL '{data_periodo_regra} days' AND CURRENT_DATE
                {subquery_modelos_str}
                {subquery_oficinas_str}
                {subquery_secoes_str}
                {subquery_os_str}
        """
        # print("--------------------------------")
        # print(query)

        # Executa a query
        df = pd.read_sql(query, self.dbEngine)

        # Lógica para definir o status da OS
        def definir_status(row):
            if row.get("correcao_primeira") == True:
                return "✅ Correção Primeira"
            elif row.get("correcao") == True:
                return "☑️ Correção Tardia"
            elif row.get("retrabalho") == True:
                return "🔄 Retrabalho"
            elif row.get("nova_os_com_retrabalho_anterior") == True:
                return "🆕✴️ Nova OS, com retrabalho prévio"
            elif row.get("nova_os_sem_retrabalho_anterior") == True:
                return "🆕✳️ Nova OS, sem retrabalho prévio"
            else:
                return "❓ Não classificado"
            
        # Aplica a função
        df["status_os"] = df.apply(definir_status, axis=1)

        # df_total = df.groupby("status_os").size().reset_index(name="TOTAL")
        # print(df.head())

        # print(df_total.head())
        return df
