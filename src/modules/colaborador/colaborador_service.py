import pandas as pd
import numpy as np
import traceback
import re

from db import PostgresSingleton
from ..sql_utils import *

class ColaboradorService:
    def __init__(self, dbEngine):
        self.pgEngine = dbEngine

    def get_mecanicos(self)->pd.DataFrame:
        '''Obtêm os dados de todos os mecânicos que trabalharam na RA, mesmo os desligados'''
        try:
            df_mecanicos_todos = pd.read_sql(
                """
               SELECT * FROM colaboradores_frotas_os
                """,
                self.pgEngine,
            )
            df_mecanicos_todos["nome_colaborador"] = df_mecanicos_todos["nome_colaborador"].apply(lambda x: re.sub(r"(?<!^)([A-Z])", r" \1", x)) 
            # Adiciona o campo "cod_colaborador" para o campo LABEL
            df_mecanicos_todos["LABEL_COLABORADOR"] = (
                df_mecanicos_todos["nome_colaborador"] + " (" + df_mecanicos_todos["cod_colaborador"].astype(str) + ")"
            )

            # Ordena os colaboradores
            df_mecanicos_todos = df_mecanicos_todos.sort_values("LABEL_COLABORADOR")
            return df_mecanicos_todos
        except Exception as e:
            return pd.DataFrame()
        

    def obtem_dados_os_mecanico(self, id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina):
        # Query
        data_inicio_str = datas[0]

        # Remove min_dias antes para evitar que a última OS não seja retrabalho
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")

        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)
        subquery_modelo_str = subquery_modelos(lista_modelo)
        subquery_ofcina_str = subquery_oficinas(lista_oficina)

        query = f"""
        SELECT
            *
        FROM
            os_dados
        WHERE
            "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}' AND "COLABORADOR QUE EXECUTOU O SERVICO"= '{id_colaborador}'
            {subquery_secoes_str}
            {subquery_os_str}
            {subquery_modelo_str}
            {subquery_ofcina_str}
        """
        df_os_mecanico_query = pd.read_sql_query(query, self.pgEngine)
        # Tratamento de datas
        df_os_mecanico_query["DATA INICIO SERVICO"] = pd.to_datetime(df_os_mecanico_query["DATA INICIO SERVIÇO"])
        df_os_mecanico_query["DATA DE FECHAMENTO DO SERVICO"] = pd.to_datetime(
            df_os_mecanico_query["DATA DE FECHAMENTO DO SERVICO"]
        )
        return df_os_mecanico_query 

    
    def obtem_estatistica_retrabalho_sql(self, datas, min_dias, id_colaborador, lista_secaos, lista_os, lista_modelo, lista_oficina):
        '''Obtem estatisticas e dados analisados de retrabalho para o grafico de pizza geral'''
        data_inicio_str = datas[0]

        # Remove min_dias antes para evitar que a última OS não seja retrabalho
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")

        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)
        subquery_modelo_str = subquery_modelos(lista_modelo)
        subquery_ofcina_str = subquery_oficinas(lista_oficina)
        query = f"""
        SELECT
            COUNT("DESCRICAO DO SERVICO") AS "TOTAL_OS",
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
            "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}' AND "COLABORADOR QUE EXECUTOU O SERVICO"= '{id_colaborador}'
            {subquery_secoes_str}
            {subquery_os_str}
            {subquery_modelo_str}
            {subquery_ofcina_str}
        """
        # Executa query
        df = pd.read_sql(query, self.pgEngine)
         # Calcula o total de correções tardia
        df["TOTAL_CORRECAO_TARDIA"] = df["TOTAL_CORRECAO"] - df["TOTAL_CORRECAO_PRIMEIRA"]
        return df 
    
    def obtem_estatistica_retrabalho_grafico(self, datas, id_colaborador, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina):
        '''Obtem estatisticas e dados analisados de retrabalho para o grafico de pizza geral'''
        data_inicio_str = datas[0]

        # Remove min_dias antes para evitar que a última OS não seja retrabalho
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")
        
        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)
        subquery_modelo_str = subquery_modelos(lista_modelo)
        subquery_ofcina_str = subquery_oficinas(lista_oficina)
        
        query = f"""
            WITH oficina_colaborador AS (
            SELECT DISTINCT "DESCRICAO DA SECAO"
            FROM mat_view_retrabalho_{min_dias}_dias
            WHERE 
                "COLABORADOR QUE EXECUTOU O SERVICO"= '{id_colaborador}'
                AND "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
        )
        SELECT
            'COLABORADOR' AS escopo,
            to_char(to_timestamp("DATA DE FECHAMENTO DO SERVICO", 'YYYY-MM-DD"T"HH24:MI:SS'), 'YYYY-MM') AS year_month,
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
            "COLABORADOR QUE EXECUTOU O SERVICO"= '{id_colaborador}'
            AND "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            AND "DESCRICAO DA SECAO" IN (SELECT "DESCRICAO DA SECAO" FROM oficina_colaborador)
        GROUP BY
            year_month

        UNION ALL

        SELECT
            "DESCRICAO DA SECAO" AS escopo,
            to_char(to_timestamp("DATA DE FECHAMENTO DO SERVICO", 'YYYY-MM-DD"T"HH24:MI:SS'), 'YYYY-MM') AS year_month,
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
            "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            AND "DESCRICAO DA SECAO" IN (SELECT "DESCRICAO DA SECAO" FROM oficina_colaborador)
            {subquery_secoes_str}
            {subquery_os_str}
            {subquery_modelo_str}
            {subquery_ofcina_str}
        GROUP BY
            year_month, "DESCRICAO DA SECAO"

        ORDER BY
            year_month,
            escopo;
            """
        # Executa query
        df = pd.read_sql(query, self.pgEngine)
        df["year_month_dt"] = pd.to_datetime(df["year_month"], format="%Y-%m", errors="coerce")
        return df
        
    def obtem_estatistica_retrabalho_grafico_resumo(self, datas, min_dias, id_colaborador, lista_secaos, lista_os, lista_modelo, lista_oficina):
        '''Obtem dados de retrabalho para grafico de resumo'''
        data_inicio_str = datas[0]

        # Remove min_dias antes para evitar que a última OS não seja retrabalho
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")

        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)
        subquery_modelo_str = subquery_modelos(lista_modelo)
        subquery_ofcina_str = subquery_oficinas(lista_oficina)
        
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
            "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}' AND "COLABORADOR QUE EXECUTOU O SERVICO"= '{id_colaborador}'
            {subquery_secoes_str}
            {subquery_os_str}
            {subquery_modelo_str}
            {subquery_ofcina_str}
    
        """
        
        # Executa query
        df = pd.read_sql(query, self.pgEngine)
         # Calcula o total de correções tardia
        df["TOTAL_CORRECAO_TARDIA"] = df["TOTAL_CORRECAO"] - df["TOTAL_CORRECAO_PRIMEIRA"]
        return df


    def dados_tabela_do_colaborador(self, id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina):
        '''Obtem dados para tabela'''
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
        subquery_ofcina_str = subquery_oficinas(lista_oficina)

        inner_subquery_secoes_str1 = subquery_secoes(lista_secaos, "mt.")
        inner_subquery_os_str1= subquery_os(lista_os, "mt.")
        inner_subquery_modelo_str1= subquery_modelos(lista_modelo, "mt.")
        inner_subquery_ofcina_str1= subquery_oficinas(lista_oficina, "mt.")
        
        inner_subquery_secoes_str2 = subquery_secoes(lista_secaos, "main.")
        inner_subquery_os_str2 = subquery_os(lista_os, "main.")
        inner_subquery_modelo_str2 = subquery_modelos(lista_modelo, "main.")
        inner_subquery_oficina_str2 = subquery_oficinas(lista_oficina, "main.")
        
        query = f"""
        WITH normaliza_problema AS (
            SELECT
                "DESCRICAO DA OFICINA",
                "DESCRICAO DA SECAO",
                "DESCRICAO DO SERVICO" as servico,
                "CODIGO DO VEICULO",
                "problem_no"
            FROM
                mat_view_retrabalho_{min_dias}_dias
            WHERE
                "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}' AND "COLABORADOR QUE EXECUTOU O SERVICO" = {id_colaborador}
                {subquery_secoes_str}
                {subquery_os_str}
                {subquery_modelo_str}
                {subquery_ofcina_str}
            GROUP BY
                "DESCRICAO DA OFICINA",
                "DESCRICAO DA SECAO",
                "DESCRICAO DO SERVICO",
                "CODIGO DO VEICULO",
                "problem_no"
        ),
        os_problema AS (
            SELECT
                "DESCRICAO DA OFICINA",
                "DESCRICAO DA SECAO",
                servico,
                COUNT(*) AS num_problema
            FROM
                normaliza_problema
            GROUP BY
                "DESCRICAO DA OFICINA",
                "DESCRICAO DA SECAO",
                servico
        ),
        os_nota_media AS (
            -- Calculando a nota média por OS (sem filtro de colaborador)
            SELECT
                "DESCRICAO DA OFICINA",
                "DESCRICAO DA SECAO",
                "DESCRICAO DO SERVICO",
                ROUND(AVG(odc."SCORE_SOLUTION_TEXT_QUALITY"), 2) AS nota_media_os
            FROM mat_view_retrabalho_{min_dias}_dias mt
            LEFT JOIN os_dados_classificacao odc
            ON mt."KEY_HASH" = odc."KEY_HASH"
            WHERE
                mt."DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                {inner_subquery_secoes_str1}
                {inner_subquery_os_str1}
                {inner_subquery_modelo_str1}
                {inner_subquery_ofcina_str1}
            GROUP BY
                "DESCRICAO DA OFICINA",
                "DESCRICAO DA SECAO",
                "DESCRICAO DO SERVICO"
        )
        SELECT
            main."DESCRICAO DA OFICINA",
            main."DESCRICAO DA SECAO",
            main."DESCRICAO DO SERVICO",
            COUNT(main."DESCRICAO DO SERVICO") AS "TOTAL_OS",
            SUM(CASE WHEN main.retrabalho THEN 1 ELSE 0 END) AS "TOTAL_RETRABALHO",
            SUM(CASE WHEN main.correcao THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO",
            SUM(CASE WHEN main.correcao_primeira THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO_PRIMEIRA",
            100 * ROUND(SUM(CASE WHEN main.retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
            100 * ROUND(SUM(CASE WHEN main.correcao THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO",
            100 * ROUND(SUM(CASE WHEN main.correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA",
            100 * ROUND(COUNT(*)::NUMERIC / SUM(COUNT(*)) OVER (), 4) AS "PERC_TOTAL_OS",
            ROUND(AVG("SCORE_SOLUTION_TEXT_QUALITY"), 2) as nota_media_colaborador,
            COALESCE(op.num_problema, 0) AS "TOTAL_PROBLEMA",
            osn.nota_media_os AS "nota_media_os",
            SUM(pg."VALOR") AS "TOTAL_GASTO",
            SUM(CASE WHEN retrabalho THEN pg."VALOR" ELSE NULL END) AS "TOTAL_GASTO_RETRABALHO",
            100 * ROUND(SUM(CASE WHEN retrabalho THEN pg."VALOR" ELSE 0 END)::NUMERIC / SUM(pg."VALOR")::NUMERIC, 4) AS "PERC_GASTO_RETRABALHO"
        FROM
            mat_view_retrabalho_{min_dias}_dias main
        LEFT JOIN
            os_problema op
        ON
            main."DESCRICAO DA OFICINA" = op."DESCRICAO DA OFICINA"
            AND main."DESCRICAO DA SECAO" = op."DESCRICAO DA SECAO"
            AND main."DESCRICAO DO SERVICO" = op.servico
        LEFT JOIN 
        	os_dados_classificacao odc  
        ON
            main."KEY_HASH" = odc."KEY_HASH"
            
        LEFT JOIN os_nota_media osn
            ON main."DESCRICAO DA OFICINA" = osn."DESCRICAO DA OFICINA"
            AND main."DESCRICAO DA SECAO" = osn."DESCRICAO DA SECAO"
            AND main."DESCRICAO DO SERVICO" = osn."DESCRICAO DO SERVICO"
        JOIN
            view_pecas_desconsiderando_combustivel pg 
        ON
            main."NUMERO DA OS" = pg."OS"
        WHERE
            main."DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}' AND main."COLABORADOR QUE EXECUTOU O SERVICO" = {id_colaborador}
            {inner_subquery_secoes_str2}
            {inner_subquery_os_str2}
            {inner_subquery_modelo_str2}
            {inner_subquery_oficina_str2}
        GROUP BY
            main."DESCRICAO DA OFICINA",
            main."DESCRICAO DA SECAO",
            main."DESCRICAO DO SERVICO",
            op.num_problema,
            osn.nota_media_os
        ORDER BY
            "PERC_RETRABALHO" DESC;
        """
        # Executa a query
        df = pd.read_sql(query, self.pgEngine)
        df['nota_media_colaborador'] = df['nota_media_colaborador'].replace(np.nan, 0)
        df['nota_media_os'] = df['nota_media_os'].replace(np.nan, 0)
        
        return df.to_dict("records")
    
    
    def dados_grafico_top_10_do_colaborador(self, id_colaborador, datas, min_dias, lista_secaos, lista_os, lista_modelo, lista_oficina):
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
        subquery_ofcina_str = subquery_oficinas(lista_oficina)

        inner_subquery_secoes_str1 = subquery_secoes(lista_secaos, "mt.")
        inner_subquery_os_str1= subquery_os(lista_os, "mt.")
        inner_subquery_modelo_str1= subquery_modelos(lista_modelo, "mt.")
        inner_subquery_ofcina_str1= subquery_oficinas(lista_oficina, "mt.")
        
        inner_subquery_secoes_str2 = subquery_secoes(lista_secaos, "main.")
        inner_subquery_os_str2 = subquery_os(lista_os, "main.")
        inner_subquery_modelo_str2 = subquery_modelos(lista_modelo, "main.")
        inner_subquery_oficina_str2 = subquery_oficinas(lista_oficina, "main.") 
        query = f"""
        WITH normaliza_problema AS (
            SELECT
                "DESCRICAO DA OFICINA",
                "DESCRICAO DA SECAO",
                "DESCRICAO DO SERVICO" as servico,
                "CODIGO DO VEICULO",
                "problem_no"
            FROM
                mat_view_retrabalho_{min_dias}_dias
            WHERE
                "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}' AND "COLABORADOR QUE EXECUTOU O SERVICO" = {id_colaborador}
                {subquery_secoes_str}
                {subquery_os_str}
                {subquery_modelo_str}
                {subquery_ofcina_str}
            GROUP BY
                "DESCRICAO DA OFICINA",
                "DESCRICAO DA SECAO",
                "DESCRICAO DO SERVICO",
                "CODIGO DO VEICULO",
                "problem_no"
        ),
        os_problema AS (
            SELECT
                "DESCRICAO DA OFICINA",
                "DESCRICAO DA SECAO",
                servico,
                COUNT(*) AS num_problema
            FROM
                normaliza_problema
            GROUP BY
                "DESCRICAO DA OFICINA",
                "DESCRICAO DA SECAO",
                servico
        ),
        os_nota_media AS (
            -- Calculando a nota média por OS (sem filtro de colaborador)
            SELECT
                "DESCRICAO DA OFICINA",
                "DESCRICAO DA SECAO",
                "DESCRICAO DO SERVICO",
                ROUND(AVG(odc."SCORE_SOLUTION_TEXT_QUALITY"), 2) AS nota_media_os
            FROM mat_view_retrabalho_{min_dias}_dias mt
            LEFT JOIN os_dados_classificacao odc
            ON mt."KEY_HASH" = odc."KEY_HASH"
            WHERE
                mt."DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                {inner_subquery_secoes_str1}
                {inner_subquery_os_str1}
                {inner_subquery_modelo_str1}
                {inner_subquery_ofcina_str1}
            GROUP BY
                "DESCRICAO DA OFICINA",
                "DESCRICAO DA SECAO",
                "DESCRICAO DO SERVICO"
        )
        SELECT
            main."DESCRICAO DA OFICINA",
            main."DESCRICAO DA SECAO",
            main."DESCRICAO DO SERVICO",
            COUNT(main."DESCRICAO DO SERVICO") AS "TOTAL_OS",
            SUM(CASE WHEN main.retrabalho THEN 1 ELSE 0 END) AS "TOTAL_RETRABALHO",
            SUM(CASE WHEN main.correcao THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO",
            SUM(CASE WHEN main.correcao_primeira THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO_PRIMEIRA",
            100 * ROUND(SUM(CASE WHEN main.retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
            100 * ROUND(SUM(CASE WHEN main.correcao THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO",
            100 * ROUND(SUM(CASE WHEN main.correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA",
            100 * ROUND(COUNT(*)::NUMERIC / SUM(COUNT(*)) OVER (), 4) AS "PERC_TOTAL_OS",
            ROUND(AVG("SCORE_SOLUTION_TEXT_QUALITY"), 2) as nota_media_colaborador,
            COALESCE(op.num_problema, 0) AS "TOTAL_PROBLEMA",
            osn.nota_media_os AS "nota_media_os",
            SUM(pg."VALOR") AS "TOTAL_GASTO",
            SUM(CASE WHEN retrabalho THEN pg."VALOR" ELSE NULL END) AS "TOTAL_GASTO_RETRABALHO",
            100 * ROUND(SUM(CASE WHEN retrabalho THEN pg."VALOR" ELSE 0 END)::NUMERIC / SUM(pg."VALOR")::NUMERIC, 4) AS "PERC_GASTO_RETRABALHO"
        FROM
            mat_view_retrabalho_{min_dias}_dias main
        LEFT JOIN
            os_problema op
        ON
            main."DESCRICAO DA OFICINA" = op."DESCRICAO DA OFICINA"
            AND main."DESCRICAO DA SECAO" = op."DESCRICAO DA SECAO"
            AND main."DESCRICAO DO SERVICO" = op.servico
        LEFT JOIN 
        	os_dados_classificacao odc  
        ON
            main."KEY_HASH" = odc."KEY_HASH"
            
        LEFT JOIN os_nota_media osn
            ON main."DESCRICAO DA OFICINA" = osn."DESCRICAO DA OFICINA"
            AND main."DESCRICAO DA SECAO" = osn."DESCRICAO DA SECAO"
            AND main."DESCRICAO DO SERVICO" = osn."DESCRICAO DO SERVICO"
        JOIN
            view_pecas_desconsiderando_combustivel pg 
        ON
            main."NUMERO DA OS" = pg."OS"
        WHERE
            main."DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}' AND main."COLABORADOR QUE EXECUTOU O SERVICO" = {id_colaborador}
            {inner_subquery_secoes_str2}
            {inner_subquery_os_str2}
            {inner_subquery_modelo_str2}
            {inner_subquery_oficina_str2}
        GROUP BY
            main."DESCRICAO DA OFICINA",
            main."DESCRICAO DA SECAO",
            main."DESCRICAO DO SERVICO",
            op.num_problema,
            osn.nota_media_os
        ORDER BY
            "PERC_RETRABALHO" DESC;
        """
        
        # Executa a query
        df = pd.read_sql(query, self.pgEngine)

        return df
    
    def indcador_rank_servico(self, datas, min_dias, id_colaborador, lista_secaos, lista_os, lista_modelo, lista_oficina):
        '''Obtem dados para rank de serviços diferentes'''
        data_inicio_str = datas[0]
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")
        
        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)
        subquery_modelo_str = subquery_modelos(lista_modelo)
        subquery_ofcina_str = subquery_oficinas(lista_oficina)
        
        query = F"""
            with TABELA_RANK as (SELECT 
            "COLABORADOR QUE EXECUTOU O SERVICO",
            COUNT(DISTINCT "DESCRICAO DO SERVICO") AS quantidade_de_servicos_diferentes,
            ROW_NUMBER() OVER (ORDER BY COUNT(DISTINCT "DESCRICAO DO SERVICO") DESC) AS rank_colaborador
            FROM
                mat_view_retrabalho_{min_dias}_dias
            WHERE
                "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                {subquery_secoes_str}
                {subquery_os_str}
                {subquery_modelo_str}
                {subquery_ofcina_str}
            GROUP BY "COLABORADOR QUE EXECUTOU O SERVICO"),
            TOTAL AS (
                SELECT COUNT(*) AS total_colaboradores FROM TABELA_RANK
            ) 
            SELECT 
                tr.rank_colaborador || '/' || t.total_colaboradores AS rank_colaborador
            FROM 
                TABELA_RANK tr, TOTAL t
            where  "COLABORADOR QUE EXECUTOU O SERVICO"= '{id_colaborador}'
            """
        
        df_mecanicos = pd.read_sql(
            query,
            self.pgEngine
        )  

        return df_mecanicos
    
    def indcador_rank_total_os(self, datas, min_dias, id_colaborador, lista_secaos, lista_os, lista_modelo, lista_oficina):
        '''Obtem dados para rank de total de OS'''
        data_inicio_str = datas[0]
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")
        
        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)
        subquery_modelo_str = subquery_modelos(lista_modelo)
        subquery_ofcina_str = subquery_oficinas(lista_oficina)
        
        query = F"""
            with TABELA_RANK as (SELECT 
                "COLABORADOR QUE EXECUTOU O SERVICO",
                COUNT(*) AS quantidade_de_OS,
                ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC) AS rank_colaborador
            FROM
                mat_view_retrabalho_{min_dias}_dias
            WHERE
                "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                {subquery_secoes_str}
                {subquery_os_str}
                {subquery_modelo_str}
                {subquery_ofcina_str}
            GROUP BY "COLABORADOR QUE EXECUTOU O SERVICO"),
            TOTAL AS (
                SELECT COUNT(*) AS total_colaboradores FROM TABELA_RANK
            ) 
            SELECT 
                tr.rank_colaborador || '/' || t.total_colaboradores AS rank_colaborador
            FROM 
                TABELA_RANK tr, TOTAL t
        where  "COLABORADOR QUE EXECUTOU O SERVICO"= '{id_colaborador}'
        """
        df_mecanicos = pd.read_sql(
            query,
            self.pgEngine
        )
        
        return df_mecanicos

    
    def df_lista_os(self):
        '''Retorna uma lista das OSs'''
        df_lista_os = pd.read_sql(
            f"""
            SELECT DISTINCT
            "DESCRICAO DA SECAO" as "SECAO",
            "DESCRICAO DO SERVICO" AS "LABEL"
            FROM 
                mat_view_retrabalho_10_dias mvrd 
            ORDER BY
                "DESCRICAO DO SERVICO"
            """,
            self.pgEngine,
        )
        
        return df_lista_os
    
    def df_lista_os_colab(self, min_dias, id_colaborador, datas):
        '''Retorna uma lista das OSs'''
        
        data_inicio_str = datas[0]
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")
        
        
        df_lista_os = pd.read_sql(
            f"""
            SELECT DISTINCT
            "DESCRICAO DA SECAO" as "SECAO",
            "DESCRICAO DO SERVICO" AS "LABEL"
            FROM 
                mat_view_retrabalho_{min_dias}_dias mvrd 
            WHERE "COLABORADOR QUE EXECUTOU O SERVICO"= '{id_colaborador}' AND "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            
            ORDER BY
                "DESCRICAO DO SERVICO"
            """,
            self.pgEngine,
        )
        
        return df_lista_os
    
    def df_lista_os_colab_modelo(self, lista_secaos, lista_os, min_dias, id_colaborador, datas):
        '''Retorna uma lista das OSs'''
        
        data_inicio_str = datas[0]
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")
        
        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)
        
        df_lista_os = pd.read_sql(
            f"""
            SELECT DISTINCT
            "DESCRICAO DO MODELO" as "LABEL"
            FROM 
                mat_view_retrabalho_{min_dias}_dias mvrd 
            WHERE "COLABORADOR QUE EXECUTOU O SERVICO"= '{id_colaborador}' AND "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            {subquery_secoes_str}
            {subquery_os_str}
            ORDER BY
                "DESCRICAO DO MODELO"
            """,
            self.pgEngine,
        )
        return df_lista_os
    
    def nota_media_colaborador(self, datas, min_dias, id_colaborador, lista_secaos, lista_os, lista_modelo, lista_oficina):
        '''Retorna a nota media do colaborador'''
        
        data_inicio_str = datas[0]
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")
        
        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)
        subquery_modelo_str = subquery_modelos(lista_modelo)
        subquery_ofcina_str = subquery_oficinas(lista_oficina)
        
        
        query = f"""
        SELECT
          	ROUND(AVG("SCORE_SOLUTION_TEXT_QUALITY"), 2) as nota_media_colaborador
        FROM
            mat_view_retrabalho_{min_dias}_dias mt
        LEFT JOIN
		    os_dados_classificacao odc  on mt."KEY_HASH" = odc."KEY_HASH" 

        WHERE
            "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}' AND "COLABORADOR QUE EXECUTOU O SERVICO"= '{id_colaborador}'
            {subquery_secoes_str}
            {subquery_os_str}
            {subquery_modelo_str}
            {subquery_ofcina_str}
    
        """
        df_mecanico = pd.read_sql(query, self.pgEngine)
        return df_mecanico
        
    def evolucao_nota_media_colaborador(self, datas, min_dias, id_colaborador, lista_secaos, lista_os, lista_modelo, lista_oficina):
        
        '''Retorna evoluçao da nota media do colaborador e da oficina'''
        
        data_inicio_str = datas[0]
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")
        
        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)
        subquery_modelo_str = subquery_modelos(lista_modelo)
        subquery_ofcina_str = subquery_oficinas(lista_oficina)
        
        query = f"""
            WITH oficina_colaborador AS (
            SELECT DISTINCT "DESCRICAO DA OFICINA"
            FROM mat_view_retrabalho_{min_dias}_dias
            WHERE 
                "COLABORADOR QUE EXECUTOU O SERVICO"= '{id_colaborador}'
                AND "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
        )
        SELECT
            'COLABORADOR' AS escopo,
            to_char(to_timestamp("DATA DE FECHAMENTO DO SERVICO", 'YYYY-MM-DD"T"HH24:MI:SS'), 'YYYY-MM') AS year_month,
            ROUND(AVG("SCORE_SOLUTION_TEXT_QUALITY"), 2) as nota_media
        FROM
            mat_view_retrabalho_{min_dias}_dias mt1
        LEFT JOIN
		    os_dados_classificacao odc  on mt1."KEY_HASH" = odc."KEY_HASH"
        WHERE
            "COLABORADOR QUE EXECUTOU O SERVICO"= '{id_colaborador}'
            AND "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            AND "DESCRICAO DA OFICINA" IN (SELECT "DESCRICAO DA OFICINA"  FROM oficina_colaborador)
        GROUP BY
            year_month

        UNION ALL

        SELECT
            "DESCRICAO DA OFICINA" AS escopo,
            to_char(to_timestamp("DATA DE FECHAMENTO DO SERVICO", 'YYYY-MM-DD"T"HH24:MI:SS'), 'YYYY-MM') AS year_month,
            ROUND(AVG("SCORE_SOLUTION_TEXT_QUALITY"), 2) as nota_media
        FROM
            mat_view_retrabalho_{min_dias}_dias mt2
        LEFT JOIN
		    os_dados_classificacao odc  on mt2."KEY_HASH" = odc."KEY_HASH" 
      
        WHERE 
            "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            AND "DESCRICAO DA OFICINA" IN (SELECT "DESCRICAO DA OFICINA" FROM oficina_colaborador)
            {subquery_secoes_str}
            {subquery_os_str}
            {subquery_modelo_str}
            {subquery_ofcina_str}
        GROUP BY
            year_month, "DESCRICAO DA OFICINA"

        ORDER BY
            year_month,
            escopo;
            """
        df_mecanico = pd.read_sql(query, self.pgEngine)
        return df_mecanico
    
    def posicao_rank_nota_media(self, datas, min_dias, id_colaborador, lista_secaos, lista_os, lista_modelo, lista_oficina):
        '''Retorna o rank do colaborador'''
        
        data_inicio_str = datas[0]
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")
        
        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)
        subquery_modelo_str = subquery_modelos(lista_modelo)
        subquery_ofcina_str = subquery_oficinas(lista_oficina)
        
        query = f'''
        with TABELA_RANK as (
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
            "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}' 
            {subquery_secoes_str}
            {subquery_os_str}
            {subquery_modelo_str}
            {subquery_ofcina_str}
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
        where  "COLABORADOR QUE EXECUTOU O SERVICO"= '{id_colaborador}'
        '''
        
        df_mecanico = pd.read_sql(query, self.pgEngine)
        return df_mecanico
    
    def evolucao_gasto_colaborador(self, datas, min_dias, id_colaborador, lista_secaos, lista_os, lista_modelo, lista_oficina):
        '''retorna dados de evolução de gasto do colaborador'''

        data_inicio_str = datas[0]
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")
        
        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)
        subquery_modelo_str = subquery_modelos(lista_modelo)
        subquery_ofcina_str = subquery_oficinas(lista_oficina)

        query = f'''
            WITH oficina_colaborador AS (
            SELECT DISTINCT "DESCRICAO DA OFICINA"
            FROM mat_view_retrabalho_{min_dias}_dias
            WHERE 
                "COLABORADOR QUE EXECUTOU O SERVICO"= '{id_colaborador}'
                AND "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
        )
        SELECT
            'COLABORADOR' AS escopo,
            to_char(to_timestamp("DATA DE FECHAMENTO DO SERVICO", 'YYYY-MM-DD"T"HH24:MI:SS'), 'YYYY-MM') AS year_month,
            Round(SUM(pg."VALOR"), 2) AS total_gasto
        FROM
            mat_view_retrabalho_{min_dias}_dias mt1
        JOIN view_pecas_desconsiderando_combustivel pg
            ON mt1."NUMERO DA OS" = pg."OS"
        WHERE
            "COLABORADOR QUE EXECUTOU O SERVICO"= '{id_colaborador}'
            AND "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            AND "DESCRICAO DA OFICINA" IN (SELECT "DESCRICAO DA OFICINA"  FROM oficina_colaborador)
        GROUP BY
            year_month

        UNION ALL

        SELECT
            "DESCRICAO DA OFICINA" AS escopo,
            to_char(to_timestamp("DATA DE FECHAMENTO DO SERVICO", 'YYYY-MM-DD"T"HH24:MI:SS'), 'YYYY-MM') AS year_month,
            Round(SUM(pg."VALOR"), 2) AS total_gasto
        FROM
            mat_view_retrabalho_{min_dias}_dias mt2
        JOIN view_pecas_desconsiderando_combustivel pg
            ON mt2."NUMERO DA OS" = pg."OS"
      
        WHERE 
            "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            AND "DESCRICAO DA OFICINA" IN (SELECT "DESCRICAO DA OFICINA" FROM oficina_colaborador)
            {subquery_secoes_str}
            {subquery_os_str}
            {subquery_modelo_str}
            {subquery_ofcina_str}
        GROUP BY
            year_month, "DESCRICAO DA OFICINA"

        ORDER BY
            year_month,
            escopo;'''
        df_mecanico = pd.read_sql(query, self.pgEngine)
        return df_mecanico
    
    def gasto_colaborador(self, datas, min_dias, id_colaborador, lista_secaos, lista_os, lista_modelo, lista_oficina):
        '''retorna dados de gasto do colaborador'''

        data_inicio_str = datas[0]
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")
        
        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)
        subquery_modelo_str = subquery_modelos(lista_modelo)
        subquery_ofcina_str = subquery_oficinas(lista_oficina)

        query = f'''SELECT
            SUM(pg."VALOR") AS "TOTAL_GASTO",
            SUM(CASE WHEN retrabalho THEN pg."VALOR" ELSE NULL END) AS "TOTAL_GASTO_RETRABALHO"
        FROM
            mat_view_retrabalho_{min_dias}_dias main
        JOIN
            view_pecas_desconsiderando_combustivel pg 
        ON
            main."NUMERO DA OS" = pg."OS"
        WHERE
            main."DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}' AND main."COLABORADOR QUE EXECUTOU O SERVICO"= '{id_colaborador}'
            {subquery_secoes_str}
            {subquery_os_str}
            {subquery_modelo_str}
            {subquery_ofcina_str}
        '''
        print(query)
        df_mecanico = pd.read_sql(query, self.pgEngine)
        # Formatar "VALOR" para R$ no formato brasileiro e substituindo por 0 os valores nulos
        df_mecanico["TOTAL_GASTO"] = df_mecanico["TOTAL_GASTO"].fillna(0).astype(float).round(2)
        df_mecanico["TOTAL_GASTO"] = df_mecanico["TOTAL_GASTO"].apply(lambda x: f'R$ {x:,.2f}'.replace(",", "X").replace(".", ",").replace("X", "."))
        return df_mecanico