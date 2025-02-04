#!/usr/bin/env python
# coding: utf-8

# Classe que centraliza os serviços para mostrar na página home

# Imports básicos
import pandas as pd
import numpy as np

# Imports auxiliares
from modules.sql_utils import subquery_oficinas, subquery_secoes, subquery_os


# Classe do serviço
class HomeService:
    def __init__(self, dbEngine):
        self.dbEngine = dbEngine

    def get_sintese_geral(
        self, datas, min_dias, lista_oficinas, lista_secaos, lista_os
    ):
        """Função para obter a síntese geral (que será usado para o gráfico de pizza)"""

        # Extraí a data inicial (já em string)
        data_inicio_str = datas[0]

        # Extraí a data final
        # Remove min_dias antes para evitar que a última OS não seja retrabalho
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")

        # Subqueries
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
                100 * ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
                100 * ROUND(SUM(CASE WHEN correcao THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO",
                100 * ROUND(SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA"
            FROM
                mat_view_retrabalho_{min_dias}_dias
            WHERE
                "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                {subquery_oficinas_str}
                {subquery_secoes_str}
                {subquery_os_str}
        """

        # Executa a query
        df = pd.read_sql(query, self.dbEngine)

        # Calcula o total de correções tardia
        df["TOTAL_CORRECAO_TARDIA"] = (
            df["TOTAL_CORRECAO"] - df["TOTAL_CORRECAO_PRIMEIRA"]
        )

        return df

    def get_retrabalho_por_modelo(
        self, datas, min_dias, lista_oficinas, lista_secaos, lista_os
    ):
        """Função para obter o quantitativo de retrabalho e correções de primeira por modelo"""

        # Extraí a data inicial (já em string)
        data_inicio_str = datas[0]

        # Extraí a data final
        # Remove min_dias antes para evitar que a última OS não seja retrabalho
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")

        # Subqueries
        subquery_oficinas_str = subquery_oficinas(lista_oficinas)
        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)

        # Queries
        # Primeiro pegamos o total de veículos por modelo no período, não vamos restringir por problema
        query_total_frota = f"""
        SELECT 
            "DESCRICAO DO MODELO", 
            COUNT(DISTINCT "CODIGO DO VEICULO") AS "TOTAL_FROTA_PERIODO"
        FROM 
            mat_view_retrabalho_{min_dias}_dias
        WHERE
            "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            {subquery_oficinas_str}
        GROUP BY 
            "DESCRICAO DO MODELO"
        """

        query_teve_problema = f"""
        SELECT 
            "DESCRICAO DO MODELO", 
            COUNT(DISTINCT "CODIGO DO VEICULO") AS "TOTAL_FROTA_TEVE_PROBLEMA"
        FROM 
            mat_view_retrabalho_{min_dias}_dias
        WHERE
            "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            {subquery_oficinas_str}
            {subquery_secoes_str}
            {subquery_os_str}
        GROUP BY 
            "DESCRICAO DO MODELO"
        """

        query_teve_retrabalho = f"""
        SELECT 
            "DESCRICAO DO MODELO", 
            COUNT(DISTINCT "CODIGO DO VEICULO") AS "TOTAL_FROTA_TEVE_RETRABALHO"
        FROM 
            mat_view_retrabalho_{min_dias}_dias
        WHERE
            "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            {subquery_oficinas_str}
            {subquery_secoes_str}
            {subquery_os_str}
            AND retrabalho = TRUE
        GROUP BY 
            "DESCRICAO DO MODELO"
        """

        # Executa Queries
        df_total_frota = pd.read_sql(query_total_frota, self.dbEngine)
        df_teve_problema = pd.read_sql(query_teve_problema, self.dbEngine)
        df_teve_retrabalho = pd.read_sql(query_teve_retrabalho, self.dbEngine)

        # Merge dos dataframes
        df = df_total_frota.merge(
            df_teve_problema, on="DESCRICAO DO MODELO", how="left"
        )
        df = df.merge(df_teve_retrabalho, on="DESCRICAO DO MODELO", how="left")
        df.fillna(0, inplace=True)

        # Calcular campos
        df["NAO_TEVE_PROBLEMA"] = (
            df["TOTAL_FROTA_PERIODO"] - df["TOTAL_FROTA_TEVE_PROBLEMA"]
        )
        df["TEVE_PROBLEMA_SEM_RETRABALHO"] = (
            df["TOTAL_FROTA_TEVE_PROBLEMA"] - df["TOTAL_FROTA_TEVE_RETRABALHO"]
        )
        df["TEVE_PROBLEMA_E_RETRABALHO"] = df["TOTAL_FROTA_TEVE_RETRABALHO"]

        # Calcula as porcentagens
        df["PERC_NAO_TEVE_PROBLEMA"] = round(
            100 * df["NAO_TEVE_PROBLEMA"] / df["TOTAL_FROTA_PERIODO"], 1
        )
        df["PERC_TEVE_PROBLEMA_SEM_RETRABALHO"] = round(
            100 * df["TEVE_PROBLEMA_SEM_RETRABALHO"] / df["TOTAL_FROTA_PERIODO"], 1
        )
        df["PERC_TEVE_PROBLEMA_E_RETRABALHO"] = round(
            100 * df["TEVE_PROBLEMA_E_RETRABALHO"] / df["TOTAL_FROTA_PERIODO"], 1
        )

        return df

    def get_evolucao_retrabalho_por_oficina_por_mes(
        self, datas, min_dias, lista_oficinas, lista_secaos, lista_os
    ):
        """Função para obter a evolução do retrabalho por oficinal por mes"""
        # Extraí a data inicial (já em string)
        data_inicio_str = datas[0]

        # Extraí a data final
        # Remove min_dias antes para evitar que a última OS não seja retrabalho
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")

        # Subqueries
        subquery_oficinas_str = subquery_oficinas(lista_oficinas)
        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)

        query = f"""
        SELECT
            to_char(to_timestamp("DATA DE FECHAMENTO DO SERVICO", 'YYYY-MM-DD"T"HH24:MI:SS'), 'YYYY-MM') AS year_month,
            "DESCRICAO DA OFICINA",
            100 * ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
            100 * ROUND(SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA"
        FROM
            mat_view_retrabalho_{min_dias}_dias
        WHERE
            "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            {subquery_oficinas_str}
            {subquery_secoes_str}
            {subquery_os_str}
        GROUP BY
            year_month, "DESCRICAO DA OFICINA"
        ORDER BY
            year_month;
        """

        # Executa query
        df = pd.read_sql(query, self.dbEngine)

        # Arruma dt
        df["year_month_dt"] = pd.to_datetime(df["year_month"], format="%Y-%m", errors="coerce")

        # Funde (melt) colunas de retrabalho e correção
        df_combinado = df.melt(
            id_vars=["year_month_dt", "DESCRICAO DA OFICINA"],
            value_vars=["PERC_RETRABALHO", "PERC_CORRECAO_PRIMEIRA"],
            var_name="CATEGORIA",
            value_name="PERC",
        )

        # Renomeia as colunas
        df_combinado["CATEGORIA"] = df_combinado["CATEGORIA"].replace(
            {"PERC_RETRABALHO": "RETRABALHO", "PERC_CORRECAO_PRIMEIRA": "CORRECAO_PRIMEIRA"}
        )

        return df_combinado

    def get_evolucao_retrabalho_por_secao_por_mes(
        self, datas, min_dias, lista_oficinas, lista_secaos, lista_os
    ):
        """Função para obter a evolução do retrabalho por seção por mes"""
        # Extraí a data inicial (já em string)
        data_inicio_str = datas[0]

        # Extraí a data final
        # Remove min_dias antes para evitar que a última OS não seja retrabalho
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")

        # Subqueries
        subquery_oficinas_str = subquery_oficinas(lista_oficinas)
        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)

        query = f"""
        SELECT
            to_char(to_timestamp("DATA DE FECHAMENTO DO SERVICO", 'YYYY-MM-DD"T"HH24:MI:SS'), 'YYYY-MM') AS year_month,
            "DESCRICAO DA SECAO",
            100 * ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
            100 * ROUND(SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA"
        FROM
            mat_view_retrabalho_{min_dias}_dias
        WHERE
            "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            {subquery_oficinas_str}
            {subquery_secoes_str}
            {subquery_os_str}
        GROUP BY
            year_month, "DESCRICAO DA SECAO"
        ORDER BY
            year_month;
        """

        # Executa Query
        df = pd.read_sql(query, self.dbEngine)

        # Arruma dt
        df["year_month_dt"] = pd.to_datetime(df["year_month"], format="%Y-%m", errors="coerce")

        # Funde (melt) colunas de retrabalho e correção
        df_combinado = df.melt(
            id_vars=["year_month_dt", "DESCRICAO DA SECAO"],
            value_vars=["PERC_RETRABALHO", "PERC_CORRECAO_PRIMEIRA"],
            var_name="CATEGORIA",
            value_name="PERC",
        )

        # Renomeia as colunas
        df_combinado["CATEGORIA"] = df_combinado["CATEGORIA"].replace(
            {"PERC_RETRABALHO": "RETRABALHO", "PERC_CORRECAO_PRIMEIRA": "CORRECAO_PRIMEIRA"}
        )

        return df_combinado
