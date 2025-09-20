# Classe que centraliza os serviços para mostrar na página home

# Imports básicos
import re
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Imports auxiliares
from modules.sql_utils import (
    subquery_oficinas,
    subquery_secoes,
    subquery_os,
    subquery_veiculos,
    subquery_modelos,
    subquery_modelos_veiculos,
    subquery_equipamentos,
    subquery_modelos_pecas,
)

from modules.service_utils import definir_status
from modules.veiculos.helps import HelpsVeiculos


# Classe do serviço
class VeiculoService:
    def __init__(self, dbEngine):
        self.dbEngine = dbEngine

    def get_veiculos_possiveis_nos_modelos(self, modelos_selecionados):
        # Filtro
        subquery_modelos_veiculos_str = subquery_modelos_veiculos(modelos_selecionados)

        # Query
        query = f"""
            SELECT DISTINCT
                "CODIGO DO VEICULO" AS "VEICULO",
                "DESCRICAO DO MODELO" AS "MODELO"
            FROM 
                mat_view_retrabalho_10_dias mvrd
            WHERE 1=1
                {subquery_modelos_veiculos_str}
        """

        # Executa a query
        df = pd.read_sql(query, self.dbEngine)

        # Ordenar os resultados
        df = df.sort_values("VEICULO")

        return df

    def get_os_possiveis_do_veiculo(self, id_veiculo):
        query = f"""
            SELECT DISTINCT
                "DESCRICAO DO SERVICO" AS "SERVICO"
            FROM
                mat_view_retrabalho_10_dias
            WHERE
                "CODIGO DO VEICULO" = '{id_veiculo}'
            ORDER BY
                "DESCRICAO DO SERVICO" ASC
        """

        df = pd.read_sql(query, self.dbEngine)

        return df

    def get_sinteze_retrabalho_veiculo_para_grafico_pizza(
        self, id_veiculo, datas, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os
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
        subquery_modelo_str = subquery_modelos(lista_modelos, termo_all="TODOS")
        subquery_oficina_str = subquery_oficinas(lista_oficinas)

        query = f"""
        SELECT
            COUNT(*) AS "TOTAL_OS",
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
            AND "CODIGO DO VEICULO" = '{id_veiculo}'
            {subquery_secoes_str}
            {subquery_os_str}
            {subquery_modelo_str}
            {subquery_oficina_str}
        """
        # Executa query
        df = pd.read_sql(query, self.dbEngine)

        # Calcula o total de correções tardia
        df["TOTAL_CORRECAO_TARDIA"] = df["TOTAL_CORRECAO"] - df["TOTAL_CORRECAO_PRIMEIRA"]

        return df

    def get_indicador_rank_retrabalho_modelo_veiculo(
        self, id_veiculo, datas, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os
    ):
        """Função para obter o ranking do veículo em termos de retrabalho por modelo nas opções selecionadas"""

        data_inicio_str = datas[0]

        # Remove min_dias antes para evitar que a última OS não seja retrabalho
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")

        # Filtro das subqueries
        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)
        subquery_modelo_str = subquery_modelos(lista_modelos, termo_all="TODOS")
        subquery_oficina_str = subquery_oficinas(lista_oficinas)

        query = f"""
        WITH TABELA_RANK AS (       
            SELECT 
                "CODIGO DO VEICULO",
                COUNT(*) AS quantidade_de_os_retrabalho,
                ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC) AS rank_veiculo
            FROM
                mat_view_retrabalho_{min_dias}_dias
            WHERE
                retrabalho = TRUE
                AND "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}' 
                AND "DESCRICAO DO MODELO" IN (
                    SELECT DISTINCT "DESCRICAO DO MODELO"
                    FROM mat_view_retrabalho_{min_dias}_dias
                    WHERE "CODIGO DO VEICULO" = '{id_veiculo}'
                )
                {subquery_secoes_str}
                {subquery_os_str}
                {subquery_modelo_str}
                {subquery_oficina_str}
            GROUP BY
                "CODIGO DO VEICULO"
        ), 
        TOTAL AS (
            SELECT 
                COUNT(DISTINCT "CODIGO DO VEICULO") as total_veiculos 
            FROM 
                mat_view_retrabalho_{min_dias}_dias
            WHERE
                "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}' 
                AND "DESCRICAO DO MODELO" IN (
                    SELECT DISTINCT "DESCRICAO DO MODELO"
                    FROM mat_view_retrabalho_{min_dias}_dias
                    WHERE "CODIGO DO VEICULO" = '{id_veiculo}'
                )
                {subquery_secoes_str}
                {subquery_os_str}
                {subquery_modelo_str}
                {subquery_oficina_str}
        )
        SELECT 
            tr.rank_veiculo || '/' || t.total_veiculos AS rank_veiculo
        FROM 
            TABELA_RANK tr, TOTAL t
        WHERE
            "CODIGO DO VEICULO" = '{id_veiculo}'
        """
        # Executa query
        df = pd.read_sql(query, self.dbEngine)

        return df

    def get_indicador_rank_correcao_primeira_modelo_veiculo(
        self, id_veiculo, datas, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os
    ):
        """Função para obter o ranking do veículo em termos de correção de primeira por modelo nas opções selecionadas"""

        data_inicio_str = datas[0]

        # Remove min_dias antes para evitar que a última OS não seja retrabalho
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")

        # Filtro das subqueries
        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)
        subquery_modelo_str = subquery_modelos(lista_modelos, termo_all="TODOS")
        subquery_oficina_str = subquery_oficinas(lista_oficinas)

        query = f"""
        WITH TABELA_RANK AS (       
            SELECT 
                "CODIGO DO VEICULO",
                COUNT(*) AS quantidade_de_os_correcao_primeira,
                ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC) AS rank_veiculo
            FROM
                mat_view_retrabalho_{min_dias}_dias
            WHERE
                correcao_primeira = TRUE
                AND "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}' 
                AND "DESCRICAO DO MODELO" IN (
                    SELECT DISTINCT "DESCRICAO DO MODELO"
                    FROM mat_view_retrabalho_{min_dias}_dias
                    WHERE "CODIGO DO VEICULO" = '{id_veiculo}'
                )
                {subquery_secoes_str}
                {subquery_os_str}
                {subquery_modelo_str}
                {subquery_oficina_str}
            GROUP BY
                "CODIGO DO VEICULO"
        ), 
        TOTAL AS (
            SELECT 
                COUNT(DISTINCT "CODIGO DO VEICULO") as total_veiculos 
            FROM 
                mat_view_retrabalho_{min_dias}_dias
            WHERE
                "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}' 
                AND "DESCRICAO DO MODELO" IN (
                    SELECT DISTINCT "DESCRICAO DO MODELO"
                    FROM mat_view_retrabalho_{min_dias}_dias
                    WHERE "CODIGO DO VEICULO" = '{id_veiculo}'
                )
                {subquery_secoes_str}
                {subquery_os_str}
                {subquery_modelo_str}
                {subquery_oficina_str}
        )
        SELECT 
            tr.rank_veiculo || '/' || t.total_veiculos AS rank_veiculo
        FROM 
            TABELA_RANK tr, TOTAL t
        WHERE
            "CODIGO DO VEICULO" = '{id_veiculo}'
        """
        # Executa query
        df = pd.read_sql(query, self.dbEngine)

        return df

    def get_indicador_total_os_modelo_veiculo(
        self, id_veiculo, datas, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os
    ):
        """Função para obter o total de OS que um veículo teve em um determinado período"""

        data_inicio_str = datas[0]

        # Remove min_dias antes para evitar que a última OS não seja retrabalho
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")

        # Filtro das subqueries
        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)
        subquery_modelo_str = subquery_modelos(lista_modelos, termo_all="TODOS")
        subquery_oficina_str = subquery_oficinas(lista_oficinas)

        query = f"""
        SELECT 
            COUNT(*) AS quantidade_de_os
        FROM
            mat_view_retrabalho_{min_dias}_dias
        WHERE
            "CODIGO DO VEICULO" = '{id_veiculo}'
            AND "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}' 
            {subquery_secoes_str}
            {subquery_os_str}
            {subquery_modelo_str}
            {subquery_oficina_str}
        """
        # Executa query
        df = pd.read_sql(query, self.dbEngine)

        return df

    def get_indicador_rank_total_os_modelo_veiculo(
        self, id_veiculo, datas, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os
    ):
        """Função para obter o ranking de OS que um veículo teve em um determinado período"""

        data_inicio_str = datas[0]

        # Remove min_dias antes para evitar que a última OS não seja retrabalho
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")

        # Filtro das subqueries
        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)
        subquery_modelo_str = subquery_modelos(lista_modelos, termo_all="TODOS")
        subquery_oficina_str = subquery_oficinas(lista_oficinas)

        query = f"""
        WITH TABELA_RANK AS (       
            SELECT 
                "CODIGO DO VEICULO",
                COUNT(*) AS quantidade_de_os,
                ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC) AS rank_veiculo
            FROM
                mat_view_retrabalho_{min_dias}_dias
            WHERE
                "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}' 
                AND "DESCRICAO DO MODELO" IN (
                    SELECT DISTINCT "DESCRICAO DO MODELO"
                    FROM mat_view_retrabalho_{min_dias}_dias
                    WHERE "CODIGO DO VEICULO" = '{id_veiculo}'
                )
                {subquery_secoes_str}
                {subquery_os_str}
                {subquery_modelo_str}
                {subquery_oficina_str}
            GROUP BY
                "CODIGO DO VEICULO"
        ), 
        TOTAL AS (
            SELECT 
                COUNT(DISTINCT "CODIGO DO VEICULO") as total_veiculos 
            FROM 
                mat_view_retrabalho_{min_dias}_dias
            WHERE
                "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}' 
                AND "DESCRICAO DO MODELO" IN (
                    SELECT DISTINCT "DESCRICAO DO MODELO"
                    FROM mat_view_retrabalho_{min_dias}_dias
                    WHERE "CODIGO DO VEICULO" = '{id_veiculo}'
                )
                {subquery_secoes_str}
                {subquery_os_str}
                {subquery_modelo_str}
                {subquery_oficina_str}
        )
        SELECT 
            tr.rank_veiculo || '/' || t.total_veiculos AS rank_veiculo
        FROM 
            TABELA_RANK tr, TOTAL t
        WHERE
            "CODIGO DO VEICULO" = '{id_veiculo}'
        """
        # Executa query
        df = pd.read_sql(query, self.dbEngine)

        return df

    def get_indicador_total_gasto_pecas_modelo_veiculo(
        self, id_veiculo, datas, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os
    ):
        """Função para obter o total gasto com peças que um veículo teve em um determinado período"""

        data_inicio_str = datas[0]

        # Remove min_dias antes para evitar que a última OS não seja retrabalho
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")

        # Filtro das subqueries
        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)
        subquery_modelo_str = subquery_modelos(lista_modelos, termo_all="TODOS")
        subquery_oficina_str = subquery_oficinas(lista_oficinas)

        query = f"""
        SELECT
            SUM(pg."VALOR") AS "TOTAL_GASTO"
        FROM
            mat_view_retrabalho_{min_dias}_dias main
        JOIN
            view_pecas_desconsiderando_combustivel pg 
        ON
            main."NUMERO DA OS" = pg."OS"
        WHERE
            "CODIGO DO VEICULO" = '{id_veiculo}'
            AND "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            {subquery_secoes_str}
            {subquery_os_str}
            {subquery_modelo_str}
            {subquery_oficina_str}
        GROUP BY
            "CODIGO DO VEICULO"
        """
        # Executa query
        df = pd.read_sql(query, self.dbEngine)

        return df

    def get_indicador_rank_gasto_total_pecas_modelo_veiculo(
        self, id_veiculo, datas, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os
    ):
        """Função para obter o ranking de gasto com peças que um veículo teve em um determinado período"""

        data_inicio_str = datas[0]

        # Remove min_dias antes para evitar que a última OS não seja retrabalho
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")

        # Filtro das subqueries
        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)
        subquery_modelo_str = subquery_modelos(lista_modelos, termo_all="TODOS")
        subquery_oficina_str = subquery_oficinas(lista_oficinas)

        query = f"""
        WITH TABELA_RANK AS (       
            SELECT 
                "CODIGO DO VEICULO",
                SUM(pg."VALOR") AS "TOTAL_GASTO",
                ROW_NUMBER() OVER (ORDER BY SUM(pg."VALOR") DESC) AS rank_veiculo
            FROM
                mat_view_retrabalho_{min_dias}_dias main
            JOIN
                view_pecas_desconsiderando_combustivel pg 
            ON
                main."NUMERO DA OS" = pg."OS"
            WHERE
                "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}' 
                AND "DESCRICAO DO MODELO" IN (
                    SELECT DISTINCT "DESCRICAO DO MODELO"
                    FROM mat_view_retrabalho_{min_dias}_dias
                    WHERE "CODIGO DO VEICULO" = '{id_veiculo}'
                )
                {subquery_secoes_str}
                {subquery_os_str}
                {subquery_modelo_str}
                {subquery_oficina_str}
            GROUP BY
                "CODIGO DO VEICULO"
        ), 
        TOTAL AS (
            SELECT 
                COUNT(DISTINCT "CODIGO DO VEICULO") as total_veiculos 
            FROM 
                mat_view_retrabalho_{min_dias}_dias
            WHERE
                "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}' 
                AND "DESCRICAO DO MODELO" IN (
                    SELECT DISTINCT "DESCRICAO DO MODELO"
                    FROM mat_view_retrabalho_{min_dias}_dias
                    WHERE "CODIGO DO VEICULO" = '{id_veiculo}'
                )
                {subquery_secoes_str}
                {subquery_os_str}
                {subquery_modelo_str}
                {subquery_oficina_str}
        )
        SELECT 
            tr.rank_veiculo || '/' || t.total_veiculos AS rank_veiculo
        FROM 
            TABELA_RANK tr, TOTAL t
        WHERE
            "CODIGO DO VEICULO" = '{id_veiculo}'
        """
        # Executa query
        df = pd.read_sql(query, self.dbEngine)

        return df

    def get_indicador_total_gasto_retrabalho_pecas_modelo_veiculo(
        self, id_veiculo, datas, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os
    ):
        """Função para obter o total gasto com peças vinculadas a retrabalho que um veículo teve em um determinado período"""
        data_inicio_str = datas[0]

        # Remove min_dias antes para evitar que a última OS não seja retrabalho
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")

        # Filtro das subqueries
        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)
        subquery_modelo_str = subquery_modelos(lista_modelos, termo_all="TODOS")
        subquery_oficina_str = subquery_oficinas(lista_oficinas)

        query = f"""
        SELECT
            SUM(pg."VALOR") AS "TOTAL_GASTO"
        FROM
            mat_view_retrabalho_{min_dias}_dias main
        JOIN
            view_pecas_desconsiderando_combustivel pg 
        ON
            main."NUMERO DA OS" = pg."OS"
        WHERE
            "CODIGO DO VEICULO" = '{id_veiculo}'
            AND "retrabalho" = TRUE
            AND "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            {subquery_secoes_str}
            {subquery_os_str}
            {subquery_modelo_str}
            {subquery_oficina_str}
        GROUP BY
            "CODIGO DO VEICULO"
        """
        # Executa query
        df = pd.read_sql(query, self.dbEngine)

        return df

    def get_indicador_rank_gasto_retrabalho_pecas_modelo_veiculo(
        self, id_veiculo, datas, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os
    ):
        """Função para obter o ranking de gasto com peças em retrabalho que um veículo teve em um determinado período"""

        data_inicio_str = datas[0]

        # Remove min_dias antes para evitar que a última OS não seja retrabalho
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")

        # Filtro das subqueries
        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)
        subquery_modelo_str = subquery_modelos(lista_modelos, termo_all="TODOS")
        subquery_oficina_str = subquery_oficinas(lista_oficinas)

        query = f"""
        WITH TABELA_RANK AS (       
            SELECT 
                "CODIGO DO VEICULO",
                SUM(pg."VALOR") AS "TOTAL_GASTO",
                ROW_NUMBER() OVER (ORDER BY SUM(pg."VALOR") DESC) AS rank_veiculo
            FROM
                mat_view_retrabalho_{min_dias}_dias main
            JOIN
                view_pecas_desconsiderando_combustivel pg 
            ON
                main."NUMERO DA OS" = pg."OS"
            WHERE
                "retrabalho" = TRUE
                AND "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}' 
                AND "DESCRICAO DO MODELO" IN (
                    SELECT DISTINCT "DESCRICAO DO MODELO"
                    FROM mat_view_retrabalho_{min_dias}_dias
                    WHERE "CODIGO DO VEICULO" = '{id_veiculo}'
                )
                {subquery_secoes_str}
                {subquery_os_str}
                {subquery_modelo_str}
                {subquery_oficina_str}
            GROUP BY
                "CODIGO DO VEICULO"
        ), 
        TOTAL AS (
            SELECT 
                COUNT(DISTINCT "CODIGO DO VEICULO") as total_veiculos 
            FROM 
                mat_view_retrabalho_{min_dias}_dias
            WHERE
                "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}' 
                AND "DESCRICAO DO MODELO" IN (
                    SELECT DISTINCT "DESCRICAO DO MODELO"
                    FROM mat_view_retrabalho_{min_dias}_dias
                    WHERE "CODIGO DO VEICULO" = '{id_veiculo}'
                )
                {subquery_secoes_str}
                {subquery_os_str}
                {subquery_modelo_str}
                {subquery_oficina_str}
        )
        SELECT 
            tr.rank_veiculo || '/' || t.total_veiculos AS rank_veiculo
        FROM 
            TABELA_RANK tr, TOTAL t
        WHERE
            "CODIGO DO VEICULO" = '{id_veiculo}'
        """
        # Executa query
        df = pd.read_sql(query, self.dbEngine)

        return df

    def get_evolucao_quantidade_os_por_mes(
        self, id_veiculo, datas, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os
    ):
        """Função para obter a evolução da quantidade de OSs por veículo por mes"""
        # Extraí a data inicial (já em string)
        data_inicio_str = datas[0]

        # Extraí a data final
        # Remove min_dias antes para evitar que a última OS não seja retrabalho
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")

        # Subqueries
        subquery_modelos_str = subquery_modelos(lista_modelos, termo_all="TODOS")
        subquery_oficinas_str = subquery_oficinas(lista_oficinas)
        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)

        # Query tem quatro partes:
        # 1 - Quantidade de OSs por mês por veículo
        # 2 - Quantidade de OSs por mês por veículo e modelo
        # 3 - Quantidade de OSs por mês por mês
        # 4 - Usa as três queries para obter a média geral, por modelo e do veículo
        query = f"""
        WITH qtd_os_por_veiculo_por_mes as (
            SELECT 
                "DESCRICAO DO MODELO",
                "CODIGO DO VEICULO",
                to_char(to_timestamp("DATA DO FECHAMENTO DA OS", 'YYYY-MM-DD"T"HH24:MI:SS'), 'YYYY-MM') AS year_month,
                COUNT(DISTINCT "NUMERO DA OS") AS "QUANTIDADE_DE_OS"
            FROM 
                mat_view_retrabalho_{min_dias}_dias
            WHERE
                "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                {subquery_oficinas_str}
                {subquery_secoes_str}
                {subquery_os_str}
            GROUP BY 
                "DESCRICAO DO MODELO",
                "CODIGO DO VEICULO",
                year_month
        ),
        qtd_os_media_por_modelo_por_mes AS (
            SELECT
                "DESCRICAO DO MODELO" as "CATEGORIA",	
                year_month,
                ROUND(AVG("QUANTIDADE_DE_OS"), 2) as "QUANTIDADE_DE_OS"
            FROM 
                qtd_os_por_veiculo_por_mes
            WHERE
                "DESCRICAO DO MODELO" IN (
                    SELECT DISTINCT "DESCRICAO DO MODELO"
                    FROM
                        qtd_os_por_veiculo_por_mes
                    WHERE
                        "CODIGO DO VEICULO" = '{id_veiculo}'
                )
            GROUP BY
                "DESCRICAO DO MODELO",
                year_month
        ),
        qtd_os_media_por_mes as (
            SELECT 
                'MÉDIA GERAL' as "CATEGORIA",	
                year_month,
                ROUND(AVG("QUANTIDADE_DE_OS"), 2) as "QUANTIDADE_DE_OS"
            FROM 
                qtd_os_por_veiculo_por_mes
            GROUP BY
                year_month
        )

        SELECT * 
        FROM qtd_os_media_por_modelo_por_mes

        UNION ALL

        SELECT * 
        FROM 
            qtd_os_media_por_mes

        UNION ALL

        SELECT 
            "CODIGO DO VEICULO" AS "CATEGORIA",
            year_month,
            "QUANTIDADE_DE_OS" AS "QUANTIDADE_DE_OS"
        FROM 
            qtd_os_por_veiculo_por_mes
        WHERE
            "CODIGO DO VEICULO" = '{id_veiculo}'
        """

        # Executa a query
        df = pd.read_sql(query, self.dbEngine)

        # Verifica se há veículo no dataframe para cada mês
        # Quando não houver, adiciona uma linha com o mês e o escopo "VEÍCULO" e media_gasto = 0
        meses = df["year_month"].unique()
        novas_linhas = []
        for mes in meses:
            df_mes = df[df["year_month"] == mes]
            if id_veiculo not in df_mes["CATEGORIA"].unique():
                novas_linhas.append({"CATEGORIA": id_veiculo, "year_month": mes, "QUANTIDADE_DE_OS": 0})

        # Concatena as novas linhas (se houver)
        df = pd.concat([df, pd.DataFrame(novas_linhas)], ignore_index=True)

        # Arruma dt
        df["year_month_dt"] = pd.to_datetime(df["year_month"], format="%Y-%m", errors="coerce")

        # Ordena por mês
        df = df.sort_values("year_month_dt")

        return df

    def get_evolucao_retrabalho_por_veiculo_por_mes(
        self, id_veiculo, datas, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os
    ):
        """Função para obter a evolução do retrabalho por veículo por mes"""
        # Extraí a data inicial (já em string)
        data_inicio_str = datas[0]

        # Extraí a data final
        # Remove min_dias antes para evitar que a última OS não seja retrabalho
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")

        # Subqueries
        subquery_modelos_str = subquery_modelos(lista_modelos, termo_all="TODOS")
        subquery_oficinas_str = subquery_oficinas(lista_oficinas)
        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)
        subquery_veiculos_str = subquery_veiculos([id_veiculo])

        # Query tem três partes:
        # 1 - Retrabalho por veículo por mês
        # 2 - Retrabalho por modelo por mês
        # 3 - Retrabalho geral por mês

        query = f"""
        SELECT
            to_char(to_timestamp("DATA DO FECHAMENTO DA OS", 'YYYY-MM-DD"T"HH24:MI:SS'), 'YYYY-MM') AS year_month,
            100 * ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
            100 * ROUND(SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA",
            "CODIGO DO VEICULO",
            "DESCRICAO DO MODELO"
        FROM
            mat_view_retrabalho_{min_dias}_dias
        WHERE
            "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            AND "CODIGO DO VEICULO" IN ('{id_veiculo}')
            {subquery_secoes_str}
            {subquery_os_str}
        GROUP BY
            year_month, "CODIGO DO VEICULO", "DESCRICAO DO MODELO"
            
        UNION ALL 
        
        SELECT
            to_char(to_timestamp("DATA DO FECHAMENTO DA OS", 'YYYY-MM-DD"T"HH24:MI:SS'), 'YYYY-MM') AS year_month,
            100 * ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
            100 * ROUND(SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA",
            "DESCRICAO DO MODELO" as "CODIGO DO VEICULO",
            "DESCRICAO DO MODELO"
        FROM
            mat_view_retrabalho_{min_dias}_dias
        WHERE
            "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            AND "DESCRICAO DO MODELO" in (
             	SELECT DISTINCT "DESCRICAO DO MODELO"
                FROM
                	mat_view_retrabalho_{min_dias}_dias
                WHERE
                	"CODIGO DO VEICULO" = '{id_veiculo}'
            )
            {subquery_secoes_str}
            {subquery_os_str}
        GROUP BY
            year_month, "DESCRICAO DO MODELO"
            
        UNION ALL 
        
        SELECT
            to_char(to_timestamp("DATA DO FECHAMENTO DA OS", 'YYYY-MM-DD"T"HH24:MI:SS'), 'YYYY-MM') AS year_month,
            100 * ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
            100 * ROUND(SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA",
            'MÉDIA GERAL' as "CODIGO DO VEICULO",
            'TODOS OS MODELOS' as "DESCRICAO DO MODELO"
        FROM
            mat_view_retrabalho_{min_dias}_dias
        WHERE
            "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            {subquery_secoes_str}
            {subquery_os_str}
        GROUP BY
            year_month
        ORDER BY
            year_month;
        """

        # Executa a query
        df = pd.read_sql(query, self.dbEngine)

        # Arruma dt
        df["year_month_dt"] = pd.to_datetime(df["year_month"], format="%Y-%m", errors="coerce")

        # Funde (melt) colunas de retrabalho e correção
        df_combinado = df.melt(
            id_vars=["year_month_dt", "CODIGO DO VEICULO"],
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
        self, id_veiculo, datas, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os
    ):
        # Datas
        data_inicio_str = datas[0]

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
            to_char(to_timestamp("DATA DO FECHAMENTO DA OS", 'YYYY-MM-DD"T"HH24:MI:SS'), 'YYYY-MM') AS year_month,
            "DESCRICAO DA SECAO",
            100 * ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
            100 * ROUND(SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA"
        FROM
            mat_view_retrabalho_{min_dias}_dias
        WHERE
            "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            AND "CODIGO DO VEICULO" = '{id_veiculo}'
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

    def get_evolucao_custo_por_mes(
        self, id_veiculo, datas, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os
    ):
        # Datas
        data_inicio_str = datas[0]

        # Remove min_dias antes para evitar que a última OS não seja retrabalho
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")

        # Subqueries
        subquery_oficinas_str = subquery_oficinas(lista_oficinas)
        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)

        # Query para obter o custo total por mês
        # Primeiro, calcula o custo por veículo por mês
        # Segundo, faz os filtros para:
        # - o veículo
        # - o modelo
        # - todos os veículos
        query = f"""
        WITH media_custo_por_veiculo as (
            SELECT
                    to_char(to_timestamp("DATA DO FECHAMENTO DA OS", 'YYYY-MM-DD"T"HH24:MI:SS'), 'YYYY-MM') AS year_month,
                    SUM(pg."VALOR") AS "TOTAL_GASTO",
                    SUM(CASE WHEN main.retrabalho THEN pg."VALOR" ELSE NULL END) AS "TOTAL_GASTO_RETRABALHO",
                    "CODIGO DO VEICULO",
                    "DESCRICAO DO MODELO"
                FROM
                    mat_view_retrabalho_{min_dias}_dias_distinct main
                JOIN
                    view_pecas_desconsiderando_combustivel pg 
                ON
                    main."NUMERO DA OS" = pg."OS"
                WHERE
                    "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                    {subquery_oficinas_str}
                    {subquery_secoes_str}
                    {subquery_os_str}
                GROUP BY
                    year_month, "CODIGO DO VEICULO", "DESCRICAO DO MODELO"
        )

        -- Custo do veículo selecionado
        SELECT
            "CODIGO DO VEICULO" as "CATEGORIA",
            year_month, 
            avg("TOTAL_GASTO") as "TOTAL_GASTO", 
            AVG("TOTAL_GASTO_RETRABALHO") as "TOTAL_GASTO_RETRABALHO"
        FROM 
            media_custo_por_veiculo
        WHERE 
            "CODIGO DO VEICULO" IN ('{id_veiculo}')
        GROUP BY 
            "CODIGO DO VEICULO", year_month

        UNION ALL 
        -- Custo do modelo selecionado
        
        SELECT 
            "DESCRICAO DO MODELO" as "CATEGORIA",
            year_month, 
            avg("TOTAL_GASTO") as "TOTAL_GASTO", 
            AVG("TOTAL_GASTO_RETRABALHO") as "TOTAL_GASTO_RETRABALHO"
        FROM 
            media_custo_por_veiculo
        WHERE 
            "DESCRICAO DO MODELO" in (
                SELECT DISTINCT "DESCRICAO DO MODELO"
                FROM
                    mat_view_retrabalho_{min_dias}_dias_distinct
                WHERE
                    "CODIGO DO VEICULO" = '{id_veiculo}'
            )
        GROUP BY 
            "DESCRICAO DO MODELO", year_month

        UNION ALL
        -- Custo geral
        
        SELECT 
            'MÉDIA GERAL' as "CATEGORIA",
            year_month, 
            avg("TOTAL_GASTO") as "TOTAL_GASTO", 
            AVG("TOTAL_GASTO_RETRABALHO") as "TOTAL_GASTO_RETRABALHO"
        FROM 
            media_custo_por_veiculo
        GROUP BY 
            year_month
        ORDER BY 
            year_month;
        """

        # Executa Query
        df = pd.read_sql(query, self.dbEngine)

        # Limpa os valores nulos
        df["TOTAL_GASTO"] = df["TOTAL_GASTO"].fillna(0)
        df["TOTAL_GASTO_RETRABALHO"] = df["TOTAL_GASTO_RETRABALHO"].fillna(0)

        # Verifica se há dados do veículo no dataframe para cada mês
        # Quando não houver, adiciona uma linha com o mês e o escopo "VEÍCULO" e media_gasto = 0
        meses = df["year_month"].unique()
        categorias = df["CATEGORIA"].unique()
        novas_linhas = []
        for mes in meses:
            df_mes = df[df["year_month"] == mes]
            for cat in categorias:
                if cat not in df_mes["CATEGORIA"].unique():
                    novas_linhas.append(
                        {"CATEGORIA": cat, "year_month": mes, "TOTAL_GASTO": 0, "TOTAL_GASTO_RETRABALHO": 0}
                    )

        # Concatena as novas linhas (se houver)
        df = pd.concat([df, pd.DataFrame(novas_linhas)], ignore_index=True)

        # Arruma dt
        df["year_month_dt"] = pd.to_datetime(df["year_month"], format="%Y-%m", errors="coerce")

        # Ordena o dataframe
        df = df.sort_values(by=["year_month_dt", "CATEGORIA"])

        # Funde (melt) colunas de retrabalho e correção
        df_melt = df.melt(
            id_vars=["CATEGORIA", "year_month_dt"],
            value_vars=["TOTAL_GASTO", "TOTAL_GASTO_RETRABALHO"],
            var_name="TIPO_GASTO",
            value_name="GASTO",
        )

        # Ajustar os nomes em TIPO_GASTO
        df_melt["TIPO_GASTO"] = df_melt["TIPO_GASTO"].replace(
            {"TOTAL_GASTO": "TOTAL", "TOTAL_GASTO_RETRABALHO": "RETRABALHO"}
        )

        # Ordena novamente
        df_melt = df_melt.sort_values(by=["year_month_dt", "CATEGORIA"])

        return df_melt

    def get_dados_tabela_top_servicos_veiculo(
        self, id_veiculo, datas, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os
    ):
        # Datas
        data_inicio_str = datas[0]

        # Remove min_dias antes para evitar que a última OS não seja retrabalho
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")

        # Subqueries
        subquery_oficinas_str = subquery_oficinas(lista_oficinas)
        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)

        query = f"""
        WITH veiculo_com_pecas AS (
            SELECT
                main.*,
                pg."VALOR"
            FROM mat_view_retrabalho_{min_dias}_dias main
            LEFT JOIN 
                view_pecas_desconsiderando_combustivel pg
            ON 
                main."NUMERO DA OS" = pg."OS"
            WHERE
                "CODIGO DO VEICULO" = '{id_veiculo}'
                AND main."DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                {subquery_secoes_str}
                {subquery_os_str}
                {subquery_oficinas_str}
        ),
        veiculo_com_pecas_e_classificacao AS (
            SELECT *
            FROM veiculo_com_pecas main
            LEFT JOIN os_dados_classificacao odc
                ON main."KEY_HASH" = odc."KEY_HASH"
        )
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

        FROM veiculo_com_pecas_e_classificacao main
        GROUP BY 
            main."DESCRICAO DA OFICINA",
            main."DESCRICAO DA SECAO",
            main."DESCRICAO DO SERVICO"
        ORDER BY "TOTAL_GASTO_RETRABALHO" DESC
        """

        df = pd.read_sql(query, self.dbEngine)
        df["TOTAL_GASTO_RETRABALHO"] = df["TOTAL_GASTO_RETRABALHO"].replace(np.nan, 0)
        df["TOTAL_GASTO"] = df["TOTAL_GASTO"].replace(np.nan, 0)

        return df

    def get_dados_tabela_lista_os_pecas_veiculo(
        self, id_veiculo, datas, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os
    ):
        # Datas
        data_inicio_str = datas[0]

        # Remove min_dias antes para evitar que a última OS não seja retrabalho
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")

        # Subqueries
        subquery_oficinas_str = subquery_oficinas(lista_oficinas)
        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)

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
                AND "CODIGO DO VEICULO" = '{id_veiculo}'
                {subquery_secoes_str}
                {subquery_os_str}
                {subquery_oficinas_str}
        )
        SELECT *
        FROM os_avaliadas os
        LEFT JOIN pecas_agg p
        ON os."NUMERO DA OS" = p."OS"
        """

        # Executa a query
        df = pd.read_sql(query, self.dbEngine)

        # Preenche valores nulos
        df["total_valor"] = df["total_valor"].fillna(0)
        df["pecas_valor_str"] = df["pecas_valor_str"].fillna("0")
        df["pecas_trocadas_str"] = df["pecas_trocadas_str"].fillna("Nenhuma")

        # Aplica a função para definir o status de cada OS
        df["status_os"] = df.apply(definir_status, axis=1)

        # Datas aberturas (converte para DT)
        df["DATA DA ABERTURA DA OS DT"] = pd.to_datetime(df["DATA DA ABERTURA DA OS"])
        df["DATA DO FECHAMENTO DA OS DT"] = pd.to_datetime(df["DATA DO FECHAMENTO DA OS"])

        # Ordena por data de abertura
        df = df.sort_values(by="DATA DA ABERTURA DA OS DT", ascending=False)

        return df
