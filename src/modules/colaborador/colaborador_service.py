#!/usr/bin/env python
# coding: utf-8

# Classe que centraliza os serviços para mostrar na página de colaborador

# Imports básicos
import pandas as pd
import numpy as np
import re

# Imports auxiliares
from modules.sql_utils import subquery_oficinas, subquery_secoes, subquery_os, subquery_modelos
from modules.service_utils import definir_status

# Imports do tema
import tema


class ColaboradorService:
    def __init__(self, dbEngine):
        self.pgEngine = dbEngine

    def get_modelos_veiculos_colaborador(self, id_colaborador):
        """Retorna uma lista dos modelos de veículos possíveis para o colaborador"""

        # Query
        query = f"""
        SELECT DISTINCT
            "DESCRICAO DO MODELO" as "LABEL"
        FROM 
            mat_view_retrabalho_10_dias mvrd 
        WHERE "COLABORADOR QUE EXECUTOU O SERVICO"= '{id_colaborador}'
        ORDER BY
            "DESCRICAO DO MODELO"
        """

        # Executa a query
        df = pd.read_sql(query, self.pgEngine)

        return df
    

    def get_os_possiveis_colaborador(self, id_colaborador):
        """Retorna uma lista dos OS possíveis para o colaborador"""

        # Query
        query = f"""
        SELECT DISTINCT
            "DESCRICAO DO SERVICO" as "LABEL"
        FROM 
            mat_view_retrabalho_10_dias mvrd 
        WHERE "COLABORADOR QUE EXECUTOU O SERVICO"= '{id_colaborador}'
        ORDER BY
            "DESCRICAO DO SERVICO"
        """

        # Executa a query
        df = pd.read_sql(query, self.pgEngine)

        return df

    def get_sinteze_retrabalho_colaborador_para_grafico_pizza(
        self, id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina
    ):
        """Obtem dados de retrabalho para grafico de resumo"""
        data_inicio_str = datas[0]

        # Remove min_dias antes para evitar que a última OS não seja retrabalho
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")

        # Filtro das subqueries
        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)
        subquery_modelo_str = subquery_modelos(lista_modelo)
        subquery_oficina_str = subquery_oficinas(lista_oficina)

        query = f"""
        SELECT
            SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END) AS "TOTAL_RETRABALHO",
            SUM(CASE WHEN correcao THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO",
            SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO_PRIMEIRA",
            100 * ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
            100 * ROUND(SUM(CASE WHEN correcao THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO",
            100 * ROUND(SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA"
        FROM
            mat_view_retrabalho_{min_dias}_dias
        WHERE
            "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}' AND "COLABORADOR QUE EXECUTOU O SERVICO"= '{id_colaborador}'
            {subquery_secoes_str}
            {subquery_os_str}
            {subquery_modelo_str}
            {subquery_oficina_str}
        """

        # Executa query
        df = pd.read_sql(query, self.pgEngine)
        
        # Calcula o total de correções tardia
        df["TOTAL_CORRECAO_TARDIA"] = df["TOTAL_CORRECAO"] - df["TOTAL_CORRECAO_PRIMEIRA"]

        return df


    def get_indicadores_gerais_retrabalho_colaborador(
        self, id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina
    ):
        """Obtem estatisticas e dados analisados de retrabalho para o grafico de pizza geral"""
        data_inicio_str = datas[0]

        # Remove min_dias antes para evitar que a última OS não seja retrabalho
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")

        # Filtro das subqueries
        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)
        subquery_modelo_str = subquery_modelos(lista_modelo)
        subquery_oficina_str = subquery_oficinas(lista_oficina)

        query = f"""
        SELECT
            COUNT("NUMERO DA OS") AS "TOTAL_OS",
            SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END) AS "TOTAL_RETRABALHO",
            SUM(CASE WHEN correcao THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO",
            SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO_PRIMEIRA",
            100 * ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
            100 * ROUND(SUM(CASE WHEN correcao THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO",
            100 * ROUND(SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA",
            COUNT(DISTINCT "DESCRICAO DO SERVICO") AS "QTD_SERVICOS_DIFERENTES"
        FROM
            mat_view_retrabalho_{min_dias}_dias
        WHERE
            "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}' AND "COLABORADOR QUE EXECUTOU O SERVICO"= '{id_colaborador}'
            {subquery_secoes_str}
            {subquery_os_str}
            {subquery_modelo_str}
            {subquery_oficina_str}
        """

        # Executa query
        df = pd.read_sql(query, self.pgEngine)
        
        # Calcula o total de correções tardia
        df["TOTAL_CORRECAO_TARDIA"] = df["TOTAL_CORRECAO"] - df["TOTAL_CORRECAO_PRIMEIRA"]

        return df


    def get_indicador_rank_servico_colaborador(
        self, id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina
    ):
        """Obtem dados para rank de serviços diferentes"""
        data_inicio_str = datas[0]
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")
        
        # Filtro das subqueries
        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)
        subquery_modelo_str = subquery_modelos(lista_modelo)
        subquery_oficina_str = subquery_oficinas(lista_oficina)

        query = f"""
        WITH TABELA_RANK AS (
            SELECT 
                "COLABORADOR QUE EXECUTOU O SERVICO",
                COUNT(DISTINCT "DESCRICAO DO SERVICO") AS quantidade_de_servicos_diferentes,
                ROW_NUMBER() OVER (ORDER BY COUNT(DISTINCT "DESCRICAO DO SERVICO") DESC) AS rank_colaborador
            FROM
                mat_view_retrabalho_{min_dias}_dias
            WHERE
                "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                {subquery_secoes_str}
                {subquery_os_str}
                {subquery_modelo_str}
                {subquery_oficina_str}
            GROUP BY 
                "COLABORADOR QUE EXECUTOU O SERVICO"
        ),
        TOTAL AS (
                SELECT COUNT(*) AS total_colaboradores FROM TABELA_RANK
        ) 
        SELECT 
            tr.rank_colaborador || '/' || t.total_colaboradores AS rank_colaborador
        FROM 
            TABELA_RANK tr, TOTAL t
        WHERE
            "COLABORADOR QUE EXECUTOU O SERVICO"= '{id_colaborador}'
        """
        df = pd.read_sql(query, self.pgEngine)

        return df

    def get_indicador_rank_total_os_colaborador(
        self, id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina
    ):
        """Obtem dados para rank de total de OS"""
        data_inicio_str = datas[0]
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")

        # Filtro das subqueries
        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)
        subquery_modelo_str = subquery_modelos(lista_modelo)
        subquery_oficina_str = subquery_oficinas(lista_oficina)

        query = f"""
            WITH TABELA_RANK AS (
                SELECT 
                "COLABORADOR QUE EXECUTOU O SERVICO",
                COUNT(*) AS quantidade_de_OS,
                ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC) AS rank_colaborador
            FROM
                mat_view_retrabalho_{min_dias}_dias
            WHERE
                "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                {subquery_secoes_str}
                {subquery_os_str}
                {subquery_modelo_str}
                {subquery_oficina_str}
            GROUP BY "COLABORADOR QUE EXECUTOU O SERVICO"),
            TOTAL AS (
                SELECT COUNT(*) AS total_colaboradores FROM TABELA_RANK
            ) 
            SELECT 
                tr.rank_colaborador || '/' || t.total_colaboradores AS rank_colaborador
            FROM 
                TABELA_RANK tr, TOTAL t
            WHERE
                "COLABORADOR QUE EXECUTOU O SERVICO"= '{id_colaborador}'
        """
        df = pd.read_sql(query, self.pgEngine)

        return df


    def get_indicador_nota_media_colaborador(
        self, id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina
    ):
        """Retorna a nota media do colaborador"""

        data_inicio_str = datas[0]
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")

        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)
        subquery_modelo_str = subquery_modelos(lista_modelo)
        subquery_oficina_str = subquery_oficinas(lista_oficina)

        query = f"""
        SELECT
          	ROUND(AVG("SCORE_SOLUTION_TEXT_QUALITY"), 2) as nota_media_colaborador
        FROM
            mat_view_retrabalho_{min_dias}_dias mt
        LEFT JOIN
		    os_dados_classificacao odc  on mt."KEY_HASH" = odc."KEY_HASH" 

        WHERE
            "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}' AND "COLABORADOR QUE EXECUTOU O SERVICO"= '{id_colaborador}'
            {subquery_secoes_str}
            {subquery_os_str}
            {subquery_modelo_str}
            {subquery_oficina_str}
    
        """
        
        df = pd.read_sql(query, self.pgEngine)
        
        return df


    def get_indicador_posicao_rank_nota_media(
        self, id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina
    ):
        """Retorna o rank do colaborador (nota média)"""

        data_inicio_str = datas[0]
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")

        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)
        subquery_modelo_str = subquery_modelos(lista_modelo)
        subquery_oficina_str = subquery_oficinas(lista_oficina)

        query = f"""
        WITH TABELA_RANK AS (
        SELECT
            "COLABORADOR QUE EXECUTOU O SERVICO",
            ROUND(AVG("SCORE_SOLUTION_TEXT_QUALITY"), 2) AS nota_media_colaborador,
            ROW_NUMBER() OVER (
                ORDER BY 
                    ROUND(AVG("SCORE_SOLUTION_TEXT_QUALITY"), 2) DESC NULLS LAST
            ) AS rank_colaborador
        FROM
            mat_view_retrabalho_{min_dias}_dias mt
        LEFT JOIN
            os_dados_classificacao odc ON mt."KEY_HASH" = odc."KEY_HASH"
        WHERE
            "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}' 
            {subquery_secoes_str}
            {subquery_os_str}
            {subquery_modelo_str}
            {subquery_oficina_str}
        GROUP BY 
            "COLABORADOR QUE EXECUTOU O SERVICO"
        ), 
        TOTAL AS (
            SELECT COUNT(*) AS total_colaboradores FROM TABELA_RANK
        ) 
        SELECT 
            tr.rank_colaborador || '/' || t.total_colaboradores AS rank_colaborador
        FROM 
            TABELA_RANK tr, TOTAL t
        WHERE
            "COLABORADOR QUE EXECUTOU O SERVICO"= '{id_colaborador}'
        """

        df = pd.read_sql(query, self.pgEngine)
        return df


    def get_indicador_gasto_colaborador(
        self, id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina
    ):
        """Retorna dados de gasto do colaborador"""

        data_inicio_str = datas[0]
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")

        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)
        subquery_modelo_str = subquery_modelos(lista_modelo)
        subquery_oficina_str = subquery_oficinas(lista_oficina)

        query = f"""SELECT
            SUM(pg."VALOR") AS "TOTAL_GASTO",
            SUM(CASE WHEN retrabalho THEN pg."VALOR" ELSE NULL END) AS "TOTAL_GASTO_RETRABALHO"
        FROM
            mat_view_retrabalho_{min_dias}_dias main
        JOIN
            view_pecas_desconsiderando_combustivel pg 
        ON
            main."NUMERO DA OS" = pg."OS"
        WHERE
            main."DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}' AND main."COLABORADOR QUE EXECUTOU O SERVICO"= '{id_colaborador}'
            {subquery_secoes_str}
            {subquery_os_str}
            {subquery_modelo_str}
            {subquery_oficina_str}
        """

        df = pd.read_sql(query, self.pgEngine)

        # Formatar "VALOR" para R$ no formato brasileiro e substituindo por 0 os valores nulos
        df["TOTAL_GASTO"] = df["TOTAL_GASTO"].fillna(0).astype(float).round(2)
        df["TOTAL_GASTO"] = df["TOTAL_GASTO"].apply(
            lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )
        df["TOTAL_GASTO_RETRABALHO"] = df["TOTAL_GASTO_RETRABALHO"].fillna(0).astype(float).round(2)
        df["TOTAL_GASTO_RETRABALHO"] = df["TOTAL_GASTO_RETRABALHO"].apply(
            lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )

        return df


    def get_evolucao_retrabalho_por_mes(
        self, id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina
    ):
        """Obtem estatisticas e dados analisados de retrabalho para o grafico de pizza geral"""

        # Extraí a data inicial (já em string)
        data_inicio_str = datas[0]

        # Extraí a data final
        # Remove min_dias antes para evitar que a última OS não seja retrabalho
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")

        # Filtro das subqueries
        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)
        subquery_modelo_str = subquery_modelos(lista_modelo)
        subquery_oficina_str = subquery_oficinas(lista_oficina)

        query = f"""
        SELECT
            'COLABORADOR' AS escopo,
            to_char(to_timestamp("DATA DO FECHAMENTO DA OS", 'YYYY-MM-DD"T"HH24:MI:SS'), 'YYYY-MM') AS year_month,
            SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END) AS "TOTAL_RETRABALHO",
            SUM(CASE WHEN correcao THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO",
            SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO_PRIMEIRA",
            100 * ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
            100 * ROUND(SUM(CASE WHEN correcao THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO",
            100 * ROUND(SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA"
        FROM
            mat_view_retrabalho_{min_dias}_dias
        WHERE
            "COLABORADOR QUE EXECUTOU O SERVICO"= '{id_colaborador}'
            AND "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            {subquery_secoes_str}
            {subquery_os_str}
            {subquery_modelo_str}
            {subquery_oficina_str}
        GROUP BY
            year_month

        UNION ALL

        SELECT
            "DESCRICAO DA OFICINA" AS escopo,
            to_char(to_timestamp("DATA DO FECHAMENTO DA OS", 'YYYY-MM-DD"T"HH24:MI:SS'), 'YYYY-MM') AS year_month,
            SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END) AS "TOTAL_RETRABALHO",
            SUM(CASE WHEN correcao THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO",
            SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO_PRIMEIRA",
            100 * ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
            100 * ROUND(SUM(CASE WHEN correcao THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO",
            100 * ROUND(SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA"
        FROM
            mat_view_retrabalho_{min_dias}_dias
        WHERE
            "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            {subquery_secoes_str}
            {subquery_os_str}
            {subquery_modelo_str}
            {subquery_oficina_str}
        GROUP BY
            year_month, "DESCRICAO DA OFICINA"
        ORDER BY
            year_month,
            escopo;
        """

        # Executa query
        df = pd.read_sql(query, self.pgEngine)

        # Converte para datetime
        df["year_month_dt"] = pd.to_datetime(df["year_month"], format="%Y-%m", errors="coerce")
        
        return df


    def get_evolucao_nota_media_colaborador_por_mes(
        self, id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina
    ):
        """Retorna evoluçao da nota media do colaborador e da oficina"""

        # Extraí a data inicial (já em string)
        data_inicio_str = datas[0]

        # Extraí a data final
        # Remove min_dias antes para evitar que a última OS não seja retrabalho
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")

        # Filtro das subqueries
        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)
        subquery_modelo_str = subquery_modelos(lista_modelo)
        subquery_oficina_str = subquery_oficinas(lista_oficina)

        query = f"""
        SELECT
            'COLABORADOR' AS escopo,
            to_char(to_timestamp("DATA DO FECHAMENTO DA OS", 'YYYY-MM-DD"T"HH24:MI:SS'), 'YYYY-MM') AS year_month,
            ROUND(AVG("SCORE_SOLUTION_TEXT_QUALITY"), 2) as nota_media
        FROM
            mat_view_retrabalho_{min_dias}_dias mt1
        LEFT JOIN
		    os_dados_classificacao odc  on mt1."KEY_HASH" = odc."KEY_HASH"
        WHERE
            "COLABORADOR QUE EXECUTOU O SERVICO"= '{id_colaborador}'
            AND "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            {subquery_secoes_str}
            {subquery_os_str}
            {subquery_modelo_str}
            {subquery_oficina_str}
        GROUP BY
            year_month

        UNION ALL

        SELECT
            "DESCRICAO DA OFICINA" AS escopo,
            to_char(to_timestamp("DATA DO FECHAMENTO DA OS", 'YYYY-MM-DD"T"HH24:MI:SS'), 'YYYY-MM') AS year_month,
            ROUND(AVG("SCORE_SOLUTION_TEXT_QUALITY"), 2) as nota_media
        FROM
            mat_view_retrabalho_{min_dias}_dias mt2
        LEFT JOIN
		    os_dados_classificacao odc  on mt2."KEY_HASH" = odc."KEY_HASH" 
        WHERE 
            "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            {subquery_secoes_str}
            {subquery_os_str}
            {subquery_modelo_str}
            {subquery_oficina_str}
        GROUP BY
            year_month, "DESCRICAO DA OFICINA"
        ORDER BY
            year_month,
            escopo;
        """

        # Executa a query
        df = pd.read_sql(query, self.pgEngine)

        return df


    def get_evolucao_gasto_colaborador_por_mes(
        self, id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina
    ):
        """Retorna dados de evolução de gasto do colaborador"""

        # Extraí a data inicial (já em string)
        data_inicio_str = datas[0]

        # Extraí a data final
        # Remove min_dias antes para evitar que a última OS não seja retrabalho
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")

        # Filtro das subqueries
        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)
        subquery_modelo_str = subquery_modelos(lista_modelo)
        subquery_oficina_str = subquery_oficinas(lista_oficina)

        query = f"""
        WITH retrabalho_por_colaborador_por_oficina_por_mes AS (
            SELECT
                "DESCRICAO DA OFICINA" AS escopo,
                "COLABORADOR QUE EXECUTOU O SERVICO",
                to_char(to_timestamp("DATA DO FECHAMENTO DA OS", 'YYYY-MM-DD"T"HH24:MI:SS'), 'YYYY-MM') AS year_month,
                ROUND(SUM(CASE WHEN mt2.retrabalho THEN pg."VALOR" ELSE 0 END), 2) as soma_gasto_retrabalho
            FROM
                mat_view_retrabalho_{min_dias}_dias mt2
            JOIN view_pecas_desconsiderando_combustivel pg
                ON mt2."NUMERO DA OS" = pg."OS"
            WHERE
                "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                {subquery_secoes_str}
                {subquery_os_str}
                {subquery_modelo_str}
                {subquery_oficina_str}
            GROUP BY
                year_month, "DESCRICAO DA OFICINA", "COLABORADOR QUE EXECUTOU O SERVICO"
            ORDER BY
                year_month,
                escopo
        )
        SELECT
            'COLABORADOR' AS escopo,
            to_char(to_timestamp("DATA DO FECHAMENTO DA OS", 'YYYY-MM-DD"T"HH24:MI:SS'), 'YYYY-MM') AS year_month,
            ROUND(SUM(CASE WHEN mt1.retrabalho THEN pg."VALOR" ELSE 0 END), 2) as media_gasto
        FROM
            mat_view_retrabalho_{min_dias}_dias mt1
        JOIN view_pecas_desconsiderando_combustivel pg
            ON mt1."NUMERO DA OS" = pg."OS"
        WHERE
            "COLABORADOR QUE EXECUTOU O SERVICO"= '{id_colaborador}'
            AND "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            {subquery_secoes_str}
            {subquery_os_str}
            {subquery_modelo_str}
            {subquery_oficina_str}
        GROUP BY
            year_month

        UNION ALL

        SELECT
            escopo, year_month, AVG(soma_gasto_retrabalho) as media_gasto
        FROM
            retrabalho_por_colaborador_por_oficina_por_mes
        GROUP BY
            escopo, year_month
        ORDER BY
            year_month,
            escopo;
        """

        # Executa a query
        df = pd.read_sql(query, self.pgEngine)

        # Preenche valores nulos com 0
        df["media_gasto"] = pd.to_numeric(df["media_gasto"], errors="coerce").fillna(0).round(2)

        # Verifica se há colaborador no dataframe para cada mês
        # Quando não houver, adiciona uma linha com o mês e o escopo "COLABORADOR" e media_gasto = 0
        meses = df["year_month"].unique()
        novas_linhas = []
        for mes in meses:
            df_mes = df[df["year_month"] == mes]
            if "COLABORADOR" not in df_mes["escopo"].unique():
                novas_linhas.append({"escopo": "COLABORADOR", "year_month": mes, "media_gasto": 0})

        # Concatena as novas linhas (se houver)
        df = pd.concat([df, pd.DataFrame(novas_linhas)], ignore_index=True)

        return df


    def get_atuacao_colaborador(self, id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina):
        """Retorna dados de atuação do colaborador"""

        # Extraí a data inicial (já em string)
        data_inicio_str = datas[0]

        # Extraí a data final
        # Remove min_dias antes para evitar que a última OS não seja retrabalho
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")

        # Filtro das subqueries
        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)
        subquery_modelo_str = subquery_modelos(lista_modelo)
        subquery_oficina_str = subquery_oficinas(lista_oficina)

        query = f"""
        SELECT
            "DESCRICAO DO TIPO DA OS",
            COUNT(*) AS "QUANTIDADE"
        FROM
            mat_view_retrabalho_{min_dias}_dias
        WHERE
            "COLABORADOR QUE EXECUTOU O SERVICO"= '{id_colaborador}'
            AND "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            {subquery_secoes_str}
            {subquery_os_str}
            {subquery_modelo_str}
            {subquery_oficina_str}
        GROUP BY
            "DESCRICAO DO TIPO DA OS"
        ORDER BY
            "DESCRICAO DO TIPO DA OS"
        """ 

        # Executa a query
        df = pd.read_sql(query, self.pgEngine)

        return df

    def get_top_10_tipo_os_colaborador(
        self, id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina
    ):
        # Datas
        data_inicio_str = datas[0]

        # Remove min_dias antes para evitar que a última OS não seja retrabalho
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")

        # Subqueries
        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)
        subquery_modelo_str = subquery_modelos(lista_modelo)
        subquery_oficina_str = subquery_oficinas(lista_oficina)

        query = f"""
        SELECT
            "DESCRICAO DO SERVICO",
            COUNT(*) as "TOTAL_OS" 
        FROM
            mat_view_retrabalho_{min_dias}_dias
        WHERE
            "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}' AND "COLABORADOR QUE EXECUTOU O SERVICO" = {id_colaborador}
            {subquery_secoes_str}
            {subquery_os_str}
            {subquery_modelo_str}
            {subquery_oficina_str}
        GROUP BY
            "DESCRICAO DO SERVICO"
        ORDER BY
            "TOTAL_OS" DESC
        """

        # Executa a query
        df = pd.read_sql(query, self.pgEngine)

        # Total de OS
        total_os = df["TOTAL_OS"].sum()
        df["PERC_TOTAL_OS"] = (100 * pd.to_numeric(df["TOTAL_OS"], errors="coerce") / total_os).round(2)

        # Ordena por total de OS
        df = df.sort_values("TOTAL_OS", ascending=False)

        # Seleciona as 10 primeiras linhas
        df = df.head(10)

        return df


    def get_dados_tabela_retrabalho_por_categoria_os_colaborador(
        self, id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina
    ):
        # Datas
        data_inicio_str = datas[0]

        # Remove min_dias antes para evitar que a última OS não seja retrabalho
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")

        # Subqueries
        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)
        subquery_modelo_str = subquery_modelos(lista_modelo)
        subquery_oficina_str = subquery_oficinas(lista_oficina)

        query = f"""
        WITH os_nota_media AS (
            SELECT
                "DESCRICAO DA OFICINA",
                "DESCRICAO DA SECAO",
                "DESCRICAO DO SERVICO",
                ROUND(AVG(odc."SCORE_SOLUTION_TEXT_QUALITY"), 2) AS nota_media_os
            FROM mat_view_retrabalho_{min_dias}_dias mt
            LEFT JOIN os_dados_classificacao odc
                ON mt."KEY_HASH" = odc."KEY_HASH"
            WHERE
                mt."DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                {subquery_secoes_str}
                {subquery_os_str}
                {subquery_modelo_str}
                {subquery_oficina_str}
            GROUP BY
                "DESCRICAO DA OFICINA",
                "DESCRICAO DA SECAO",
                "DESCRICAO DO SERVICO"
        ),

        os_do_colaborador_com_pecas AS (
            SELECT
                main.*,
                pg."VALOR"
            FROM mat_view_retrabalho_{min_dias}_dias main
            LEFT JOIN 
                view_pecas_desconsiderando_combustivel pg
            ON 
                main."NUMERO DA OS" = pg."OS"
            WHERE
                main."COLABORADOR QUE EXECUTOU O SERVICO" = {id_colaborador}
                AND main."DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                {subquery_secoes_str}
                {subquery_os_str}
                {subquery_modelo_str}
                {subquery_oficina_str}
        ),

        os_do_colaborador_com_pecas_e_classificacao AS (
            SELECT *
            FROM os_do_colaborador_com_pecas main
            LEFT JOIN os_dados_classificacao odc
                ON main."KEY_HASH" = odc."KEY_HASH"
        ),

        os_estatistica_colaborador AS (
            SELECT 
                main."DESCRICAO DA OFICINA",
                main."DESCRICAO DA SECAO",
                main."DESCRICAO DO SERVICO",

                COUNT(distinct main."NUMERO DA OS") AS "TOTAL_OS",
                SUM(CASE WHEN main.retrabalho THEN 1 ELSE 0 END) AS "TOTAL_RETRABALHO",
                SUM(CASE WHEN main.correcao THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO",
                SUM(CASE WHEN main.correcao_primeira THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO_PRIMEIRA",

                100 * ROUND(SUM(CASE WHEN main.retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
                100 * ROUND(SUM(CASE WHEN main.correcao THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO",
                100 * ROUND(SUM(CASE WHEN main.correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA",
                100 * ROUND(
                    COUNT(DISTINCT main."NUMERO DA OS")::NUMERIC
                    / SUM(COUNT(DISTINCT main."NUMERO DA OS")) OVER (),
                    4
                ) AS "PERC_TOTAL_OS",

                ROUND(AVG(main."SCORE_SOLUTION_TEXT_QUALITY"), 2) AS "nota_media_colaborador",

                SUM(main."VALOR") AS "TOTAL_GASTO",
                SUM(CASE WHEN main.retrabalho THEN main."VALOR" ELSE 0 END) AS "TOTAL_GASTO_RETRABALHO",
                100 * ROUND(
                    COALESCE(
                        SUM(CASE WHEN main.retrabalho THEN main."VALOR" ELSE 0 END)::NUMERIC
                        / NULLIF(SUM(main."VALOR")::NUMERIC, 0),
                        0
                    ),
                    4
                ) AS "PERC_GASTO_RETRABALHO"

            FROM os_do_colaborador_com_pecas_e_classificacao main
            GROUP BY 
                main."DESCRICAO DA OFICINA",
                main."DESCRICAO DA SECAO",
                main."DESCRICAO DO SERVICO"
        )

        SELECT 
            main.*, 
            onm.*
        FROM os_estatistica_colaborador main
        LEFT JOIN os_nota_media onm 
            ON main."DESCRICAO DA OFICINA" = onm."DESCRICAO DA OFICINA"
            AND main."DESCRICAO DA SECAO" = onm."DESCRICAO DA SECAO"
            AND main."DESCRICAO DO SERVICO" = onm."DESCRICAO DO SERVICO";
        """

        df = pd.read_sql(query, self.pgEngine)
        df["nota_media_colaborador"] = df["nota_media_colaborador"].replace(np.nan, 0)
        df["nota_media_os"] = df["nota_media_os"].replace(np.nan, 0)

        return df

    def get_dados_tabela_detalhamento_os_colaborador(
        self, id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina
    ):
        """Retorna dados de detalhamento das OSs do colaborador no período selecionado"""
        # Query
        data_inicio_str = datas[0]

        # Remove min_dias antes para evitar que a última OS não seja retrabalho
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")

        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)
        subquery_modelo_str = subquery_modelos(lista_modelo)
        subquery_oficina_str = subquery_oficinas(lista_oficina)

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
            WHERE 
                to_timestamp(pg."DATA", 'DD/MM/YYYY') BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            GROUP BY 
                pg."OS"
        ),
        os_avaliadas AS (
            SELECT
                *
            FROM
                mat_view_retrabalho_{min_dias}_dias m
            LEFT JOIN 
                os_dados_classificacao odc
            ON 
                m."KEY_HASH" = odc."KEY_HASH" 
            WHERE
                "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}' AND "COLABORADOR QUE EXECUTOU O SERVICO"= '{id_colaborador}'
                {subquery_secoes_str}
                {subquery_os_str}
                {subquery_modelo_str}
                {subquery_oficina_str}
        )
        SELECT *
        FROM os_avaliadas os
        LEFT JOIN pecas_agg p
        ON os."NUMERO DA OS" = p."OS"
        """
        df_os_detalhada_colaborador = pd.read_sql(query, self.pgEngine)

        # Preenche valores nulos
        df_os_detalhada_colaborador["total_valor"] = df_os_detalhada_colaborador["total_valor"].fillna(0)
        df_os_detalhada_colaborador["pecas_valor_str"] = df_os_detalhada_colaborador["pecas_valor_str"].fillna("0")
        df_os_detalhada_colaborador["pecas_trocadas_str"] = df_os_detalhada_colaborador["pecas_trocadas_str"].fillna(
            "Nenhuma"
        )

        # Aplica a função para definir o status de cada OS
        df_os_detalhada_colaborador["status_os"] = df_os_detalhada_colaborador.apply(definir_status, axis=1)

        # Datas aberturas (converte para DT)
        df_os_detalhada_colaborador["DATA DA ABERTURA DA OS DT"] = pd.to_datetime(
            df_os_detalhada_colaborador["DATA DA ABERTURA DA OS"]
        )
        df_os_detalhada_colaborador["DATA DO FECHAMENTO DA OS DT"] = pd.to_datetime(
            df_os_detalhada_colaborador["DATA DO FECHAMENTO DA OS"]
        )

        # Ordena por data de abertura
        df_os_detalhada_colaborador = df_os_detalhada_colaborador.sort_values(
            by="DATA DA ABERTURA DA OS DT", ascending=False
        )

        return df_os_detalhada_colaborador

    def get_dados_tabela_detalhamento_problema_colaborador(
        self, id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina, vec_problema, servico, num_problema
    ):
        """Retorna dados de detalhamento das OSs do colaborador no período selecionado"""
        # Query
        data_inicio_str = datas[0]

        # Remove min_dias antes para evitar que a última OS não seja retrabalho
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")

        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)
        subquery_modelo_str = subquery_modelos(lista_modelo)
        subquery_oficina_str = subquery_oficinas(lista_oficina)

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
            WHERE 
                to_timestamp(pg."DATA", 'DD/MM/YYYY') BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            GROUP BY 
                pg."OS"
        ),
        os_avaliadas AS (
            SELECT
                *
            FROM
                mat_view_retrabalho_{min_dias}_dias m
            LEFT JOIN 
                os_dados_classificacao odc
            ON 
                m."KEY_HASH" = odc."KEY_HASH" 
            WHERE
                "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                {subquery_secoes_str}
                {subquery_os_str}
                {subquery_modelo_str}
                {subquery_oficina_str}
                AND "CODIGO DO VEICULO" = '{vec_problema}'
                AND "DESCRICAO DO SERVICO" = '{servico}'
                AND "problem_no" = {num_problema}
        ),
        os_avaliadas_com_pecas AS (
            SELECT *
            FROM os_avaliadas os
            LEFT JOIN pecas_agg p
            ON os."NUMERO DA OS" = p."OS"
        )
        SELECT *
        FROM os_avaliadas_com_pecas os
        LEFT JOIN colaboradores_frotas_os cfo 
        ON os."COLABORADOR QUE EXECUTOU O SERVICO" = cfo.cod_colaborador
        """
        df_os_detalhada_colaborador = pd.read_sql(query, self.pgEngine)

        # Preenche valores nulos
        df_os_detalhada_colaborador["total_valor"] = df_os_detalhada_colaborador["total_valor"].fillna(0).infer_objects(copy=False)
        df_os_detalhada_colaborador["pecas_valor_str"] = df_os_detalhada_colaborador["pecas_valor_str"].fillna("0").infer_objects(copy=False)
        df_os_detalhada_colaborador["pecas_trocadas_str"] = df_os_detalhada_colaborador["pecas_trocadas_str"].fillna(
            "Nenhuma"
        ).infer_objects(copy=False)

        # Campos da LLM
        df_os_detalhada_colaborador["WHY_SOLUTION_IS_PROBLEM"] = df_os_detalhada_colaborador[
            "WHY_SOLUTION_IS_PROBLEM"
        ].fillna("Não classificado").infer_objects(copy=False)

        # Aplica a função para definir o status de cada OS
        df_os_detalhada_colaborador["status_os"] = df_os_detalhada_colaborador.apply(definir_status, axis=1)

        # Datas aberturas (converte para DT)
        df_os_detalhada_colaborador["DATA DA ABERTURA DA OS DT"] = pd.to_datetime(
            df_os_detalhada_colaborador["DATA DA ABERTURA DA OS"]
        )
        df_os_detalhada_colaborador["DATA DO FECHAMENTO DA OS DT"] = pd.to_datetime(
            df_os_detalhada_colaborador["DATA DO FECHAMENTO DA OS"]
        )

        # Ordena por data de abertura
        df_os_detalhada_colaborador = df_os_detalhada_colaborador.sort_values(
            by="DATA DA ABERTURA DA OS DT", ascending=False
        )

        # Calcula a diferença de dias entre a abertura da OS e a próxima
        df_os_detalhada_colaborador["diff_abertura_proxima"] = (
            df_os_detalhada_colaborador["DATA DO FECHAMENTO DA OS DT"]
            - df_os_detalhada_colaborador["DATA DA ABERTURA DA OS DT"].shift(1)
        ).abs()

        # Converte para número de dias (float) e seta 0 para os valores nulos
        df_os_detalhada_colaborador["diff_abertura_proxima_dias"] = df_os_detalhada_colaborador[
            "diff_abertura_proxima"
        ].dt.days
        df_os_detalhada_colaborador["diff_abertura_proxima_dias"] = (
            df_os_detalhada_colaborador["diff_abertura_proxima_dias"].fillna(0).astype(int)
        )

        # Conversão que arredonda o dia para cima
        # df_os_detalhada_colaborador["diff_abertura_proxima_dias"] = np.ceil(
        #     df_os_detalhada_colaborador["diff_abertura_proxima"].dt.total_seconds() / 86400 # 86400 segundos = 1 dia
        # ).fillna(0).astype(int)

        return df_os_detalhada_colaborador
