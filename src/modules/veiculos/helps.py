

# Imports básicos
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import re


from modules.sql_utils import subquery_oficinas, subquery_secoes, subquery_os, subquery_veiculos, subquery_modelos_veiculos
from modules.veiculos.inputs import input_valido2, input_valido


class HelpsVeiculos:
    def __init__(self, dbEngine):
        self.dbEngine = dbEngine

    def media_geral_retrabalho_modelos(self, datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos, lista_modelos):
        # Chama a função input_valido com todos os parâmetros
        if not input_valido2(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos, lista_modelos):
            return go.Figure()

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
        subquery_modelos = subquery_modelos_veiculos(lista_modelos)

        query = f"""
        SELECT
            to_char(to_timestamp("DATA DE FECHAMENTO DO SERVICO", 'YYYY-MM-DD"T"HH24:MI:SS'), 'YYYY-MM') AS year_month,
            100 * ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
            100 * ROUND(SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA",
            "CODIGO DO VEICULO",
            "DESCRICAO DO MODELO"
        FROM
            mat_view_retrabalho_{min_dias}_dias
        WHERE
            "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            {subquery_oficinas_str} 
            {subquery_secoes_str}
            {subquery_os_str}
            {subquery_modelos}
        GROUP BY
            year_month, "CODIGO DO VEICULO", "DESCRICAO DO MODELO"
        ORDER BY
            year_month;
        """

        # Executa query
        df = pd.read_sql(query, self.dbEngine)

        # Arruma dt
        df["year_month_dt"] = pd.to_datetime(df["year_month"], format="%Y-%m", errors="coerce")

        # Funde (melt) colunas de retrabalho e correção
        # Funde (melt) colunas de retrabalho e correção
        df_combinado = df.melt(
            id_vars=["year_month_dt", "CODIGO DO VEICULO", "DESCRICAO DO MODELO"],
            value_vars=["PERC_RETRABALHO", "PERC_CORRECAO_PRIMEIRA"],
            var_name="CATEGORIA",
            value_name="PERC",
        )

        #df_combinado["CODIGO DO VEICULO"] = "Geral"

        # Renomeia as colunas
        df_combinado["CATEGORIA"] = df_combinado["CATEGORIA"].replace(
            {"PERC_RETRABALHO": "RETRABALHO", "PERC_CORRECAO_PRIMEIRA": "CORRECAO_PRIMEIRA"}
        )

        df_media = df_combinado.groupby(["year_month_dt", "CATEGORIA", "DESCRICAO DO MODELO"]).agg(
            PERC=('PERC', 'mean')
        ).reset_index()

        df_media["CODIGO DO VEICULO"] = df_media["DESCRICAO DO MODELO"]

        #print(df_media.head())
        
        return df_media

    def media_geral_retrabalho_geral(self, datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
        # Chama a função input_valido com todos os parâmetros
        if not input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
            return go.Figure()

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
            to_char(to_timestamp("DATA DE FECHAMENTO DO SERVICO", 'YYYY-MM-DD"T"HH24:MI:SS'), 'YYYY-MM') AS year_month,
            100 * ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
            100 * ROUND(SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA",
            "CODIGO DO VEICULO"
        FROM
            mat_view_retrabalho_{min_dias}_dias
        WHERE
            "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            {subquery_oficinas_str} 
            {subquery_secoes_str}
            {subquery_os_str}
        GROUP BY
            year_month, "CODIGO DO VEICULO"
        ORDER BY
            year_month;
        """

        # Executa query
        df = pd.read_sql(query, self.dbEngine)

        # Arruma dt
        df["year_month_dt"] = pd.to_datetime(df["year_month"], format="%Y-%m", errors="coerce")

        # Funde (melt) colunas de retrabalho e correção
        # Funde (melt) colunas de retrabalho e correção
        df_combinado = df.melt(
            id_vars=["year_month_dt", "CODIGO DO VEICULO"],
            value_vars=["PERC_RETRABALHO", "PERC_CORRECAO_PRIMEIRA"],
            var_name="CATEGORIA",
            value_name="PERC",
        )

        #df_combinado["CODIGO DO VEICULO"] = "Geral"

        # Renomeia as colunas
        df_combinado["CATEGORIA"] = df_combinado["CATEGORIA"].replace(
            {"PERC_RETRABALHO": "RETRABALHO", "PERC_CORRECAO_PRIMEIRA": "CORRECAO_PRIMEIRA"}
        )

        df_media = df_combinado.groupby(["year_month_dt", "CATEGORIA"]).agg(
            PERC=('PERC', 'mean')
        ).reset_index()

        df_media["CODIGO DO VEICULO"] = 'Geral'

        #print(df_media.head())
        
        return df_media
