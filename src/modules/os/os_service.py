#!/usr/bin/env python
# coding: utf-8

# Classe que centraliza os serviços para mostrar na página retrabalho por OS (tipo de serviço)

# Imports básicos
import re
import pandas as pd
import numpy as np

# Imports auxiliares
from modules.sql_utils import subquery_oficinas, subquery_secoes, subquery_os, subquery_modelos
from modules.entities_utils import get_mecanicos


# Classe do serviço
class OSService:
    def __init__(self, dbEngine):
        self.dbEngine = dbEngine

    # Função que retorna as OS para os filtros selecionados
    def obtem_dados_os_sql(self, datas, min_dias, lista_modelos, lista_oficinas, lista_os):
        # Extraí a data inicial (já em string)
        data_inicio_str = datas[0]

        # Extraí a data final
        # Remove min_dias antes para evitar que a última OS não seja retrabalho
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")

        # Subqueries
        withquery_modelos_str = subquery_modelos(lista_modelos, prefix="od.", termo_all="TODOS")
        withquery_oficinas_str = subquery_oficinas(lista_oficinas, prefix="od.")
        withquery_os_str = subquery_os(lista_os, prefix="od.")

        subquery_modelos_str = subquery_modelos(lista_modelos, prefix="problem_grouping.", termo_all="TODOS")
        subquery_oficinas_str = subquery_oficinas(lista_oficinas, prefix="problem_grouping.")
        subquery_os_str = subquery_os(lista_os, prefix="problem_grouping.")

        # Query
        query = f"""
        WITH 
        os_clean AS (
		    SELECT 
			    *
		    FROM
    			os_dados od
            WHERE 
                od."DATA DA ABERTURA DA OS" IS NOT NULL 
                AND od."DATA DO FECHAMENTO DA OS" IS NOT NULL 
                AND od."DATA DA ABERTURA DA OS" ~ '^\\d{{4}}-\\d{{2}}-\\d{{2}}T\\d{{2}}:\\d{{2}}:\\d{{2}}$'::text 
                AND od."DATA DO FECHAMENTO DA OS" ~ '^\\d{{4}}-\\d{{2}}-\\d{{2}}T\\d{{2}}:\\d{{2}}:\\d{{2}}$'::text 
                AND od."DESCRICAO DO TIPO DA OS" = 'OFICINA'::text
                {withquery_modelos_str}
                {withquery_oficinas_str}
                {withquery_os_str}
        ),
        os_remove_duplicadas AS (
		    SELECT DISTINCT ON (od."NUMERO DA OS", od."DESCRICAO DO SERVICO") 
			    *
		    FROM 
    			os_clean od
		    ORDER BY 
		        od."NUMERO DA OS", od."DESCRICAO DO SERVICO", od."DATA DA ABERTURA DA OS" DESC
	    ),
        os_diff_days AS (
            SELECT 
                od."KEY_HASH",
                od."PRIORIDADE SERVICO",
                od."DESCRICAO DA SECAO",
                od."DESCRICAO DA OFICINA",
                od."OBSERVACAO DA OS",
                od."COMPLEMENTO DO SERVICO",
                od."NUMERO DA OS",
                od."CODIGO DO VEICULO",
                od."DESCRICAO DO SERVICO",
                od."DATA DA ABERTURA DA OS",
                od."DATA DO FECHAMENTO DA OS",
                od."DESCRICAO DO MODELO",
                od."DATA INICIO SERVIÇO",
                od."DATA DE FECHAMENTO DO SERVICO",
                od."COLABORADOR QUE EXECUTOU O SERVICO",
                lag(od."DATA DO FECHAMENTO DA OS") OVER (PARTITION BY od."CODIGO DO VEICULO" ORDER BY od."DATA DA ABERTURA DA OS") AS "PREV_DATA_FECHAMENTO",
                lead(od."DATA DA ABERTURA DA OS") OVER (PARTITION BY od."CODIGO DO VEICULO" ORDER BY od."DATA DA ABERTURA DA OS") AS "NEXT_DATA_ABERTURA",
                    CASE
                        WHEN lag(od."DATA DO FECHAMENTO DA OS") OVER (PARTITION BY od."CODIGO DO VEICULO" ORDER BY od."DATA DA ABERTURA DA OS") IS NOT NULL 
                             AND od."DATA DA ABERTURA DA OS" IS NOT NULL 
                        THEN date_part('day'::text, od."DATA DA ABERTURA DA OS"::timestamp without time zone - lag(od."DATA DO FECHAMENTO DA OS") OVER (PARTITION BY od."CODIGO DO VEICULO" ORDER BY od."DATA DA ABERTURA DA OS")::timestamp without time zone)
                        ELSE NULL::double precision
                    END AS prev_days,
                    CASE
                        WHEN od."DATA DO FECHAMENTO DA OS" IS NOT NULL AND lead(od."DATA DA ABERTURA DA OS") OVER (PARTITION BY od."CODIGO DO VEICULO" ORDER BY od."DATA DA ABERTURA DA OS") IS NOT NULL 
                        THEN date_part('day'::text, lead(od."DATA DA ABERTURA DA OS") OVER (PARTITION BY od."CODIGO DO VEICULO" ORDER BY od."DATA DA ABERTURA DA OS")::timestamp without time zone - od."DATA DO FECHAMENTO DA OS"::timestamp without time zone)
                        ELSE NULL::double precision
                    END AS next_days
            FROM 
                os_remove_duplicadas od
            ORDER BY
                od."DATA DA ABERTURA DA OS"
        ), 
        os_with_flags AS (
            SELECT 
                os_diff_days."NUMERO DA OS",
                os_diff_days."CODIGO DO VEICULO",
                os_diff_days."DESCRICAO DA OFICINA",
                os_diff_days."DESCRICAO DO SERVICO",
                os_diff_days."DESCRICAO DO MODELO",
                os_diff_days."DATA INICIO SERVIÇO",
                os_diff_days."DATA DE FECHAMENTO DO SERVICO",
                os_diff_days."DATA DA ABERTURA DA OS",
                os_diff_days."DATA DO FECHAMENTO DA OS",
                os_diff_days."COLABORADOR QUE EXECUTOU O SERVICO",
                os_diff_days."COMPLEMENTO DO SERVICO",
                os_diff_days.prev_days,
                os_diff_days.next_days,
                CASE
                    WHEN os_diff_days.next_days <= {min_dias}::numeric THEN true
                    ELSE false
                END AS retrabalho,
                CASE
                    WHEN os_diff_days.next_days > {min_dias}::numeric OR os_diff_days.next_days IS NULL THEN true
                    ELSE false
                END AS correcao,
                CASE
                    WHEN 
                        (os_diff_days.next_days > {min_dias}::numeric OR os_diff_days.next_days IS NULL) 
                        AND 
                        (os_diff_days.prev_days > {min_dias}::numeric OR os_diff_days.prev_days IS NULL) 
                        THEN true
                    ELSE false
                END AS correcao_primeira
            FROM 
                os_diff_days
        ),
        problem_grouping AS (
            SELECT 
                SUM(
                    CASE
                        WHEN os_with_flags.correcao THEN 1
                        ELSE 0
                    END) OVER (PARTITION BY os_with_flags."CODIGO DO VEICULO" ORDER BY os_with_flags."DATA DA ABERTURA DA OS") AS problem_no,
                os_with_flags."NUMERO DA OS",
                os_with_flags."CODIGO DO VEICULO",
                os_with_flags."DESCRICAO DO SERVICO",
                os_with_flags."DESCRICAO DO MODELO",
                os_with_flags."DESCRICAO DA OFICINA",
                os_with_flags."DATA DA ABERTURA DA OS",
                os_with_flags."DATA DO FECHAMENTO DA OS",
                os_with_flags."DATA INICIO SERVIÇO",
                os_with_flags."DATA DE FECHAMENTO DO SERVICO",
                os_with_flags."COLABORADOR QUE EXECUTOU O SERVICO",
                os_with_flags."COMPLEMENTO DO SERVICO",
                os_with_flags.prev_days,
                os_with_flags.next_days,
                os_with_flags.retrabalho,
                os_with_flags.correcao,
                os_with_flags.correcao_primeira
            FROM 
                os_with_flags
        ),
        os_with_fix_problem_number AS (
            SELECT
                CASE
                    WHEN problem_grouping.retrabalho
                    THEN problem_grouping.problem_no + 1
                    ELSE problem_grouping.problem_no
                END AS problem_no,
                problem_grouping."NUMERO DA OS",
                problem_grouping."CODIGO DO VEICULO",
                problem_grouping."DESCRICAO DA OFICINA",
                problem_grouping."DESCRICAO DO MODELO",
                problem_grouping."DESCRICAO DO SERVICO",
                problem_grouping."DATA INICIO SERVIÇO",
                problem_grouping."DATA DE FECHAMENTO DO SERVICO",
                problem_grouping."DATA DA ABERTURA DA OS",
                problem_grouping."DATA DO FECHAMENTO DA OS",
                problem_grouping."COLABORADOR QUE EXECUTOU O SERVICO",
                problem_grouping."COMPLEMENTO DO SERVICO",
                problem_grouping.prev_days,
                problem_grouping.next_days,
                problem_grouping.retrabalho,
                problem_grouping.correcao,
                problem_grouping.correcao_primeira
            FROM 
                problem_grouping
            WHERE
                problem_grouping."DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                {subquery_modelos_str}
                {subquery_oficinas_str}
                {subquery_os_str}
            ORDER BY 
                problem_grouping."DATA DA ABERTURA DA OS"
        )
        SELECT
 		    od_fix."problem_no",
 		    od_fix."retrabalho", 
 		    od_fix."correcao", 
 		    od_fix."correcao_primeira", 
 		    od_fix."prev_days", 
 		    od_fix."next_days", 
 		    od.*
	    FROM
    		os_clean od
        LEFT JOIN 
		    os_with_fix_problem_number od_fix
	    ON 
            od."NUMERO DA OS" = od_fix."NUMERO DA OS" and od."DESCRICAO DO SERVICO" = od_fix."DESCRICAO DO SERVICO"
        WHERE
            od."DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            and (
            	od."CODIGO DO VEICULO" = '50714'
            --	or 
            --	od."CODIGO DO VEICULO" = '50774'
            --	or
            --	od."CODIGO DO VEICULO" = '50763'
            	)
	    ORDER BY
		    od."DATA DA ABERTURA DA OS" 
        """
        print(query)

        df_os_query = pd.read_sql_query(query, self.dbEngine)

        # Tratamento de datas
        df_os_query["DATA INICIO SERVICO"] = pd.to_datetime(df_os_query["DATA INICIO SERVIÇO"])
        df_os_query["DATA DE FECHAMENTO DO SERVICO"] = pd.to_datetime(df_os_query["DATA DE FECHAMENTO DO SERVICO"])

        return df_os_query

    # Função que retorna a sintese geral das OS
    def get_sintese_os(self, df):
        total_num_os = len(df)
        total_retrabalho = len(df[df["retrabalho"]])
        total_correcao = len(df[df["correcao"]])
        total_correcao_primeira = len(df[df["correcao_primeira"]])
        total_correcao_tardia = total_correcao - total_correcao_primeira

        perc_retrabalho = (total_retrabalho / total_num_os) * 100
        perc_correcao = (total_correcao / total_num_os) * 100
        perc_correcao_primeira = (total_correcao_primeira / total_num_os) * 100

        return {
            "total_num_os": total_num_os,
            "total_retrabalho": total_retrabalho,
            "total_correcao": total_correcao,
            "total_correcao_primeira": total_correcao_primeira,
            "total_correcao_tardia": total_correcao_tardia,
            "perc_retrabalho": perc_retrabalho,
            "perc_correcao": perc_correcao,
            "perc_correcao_primeira": perc_correcao_primeira,
        }

    def get_tempo_cumulativo_para_retrabalho(self, df):
        # Processa cada problema de um veiculo
        # Cálculo entre DATA DA ABERTURA DA OS do início do problem até a DATA DO FECHAMENTO DA OS da solução

        # Lista de tempos cumulativos
        tempos_cumulativos = []

        for (problem_no, vehicle_id), group in df.groupby(["problem_no", "CODIGO DO VEICULO"]):
            try:
                # Vamos verificar se houve solução
                if group["correcao"].sum() > 0:
                    data_abertura_os = pd.to_datetime(group["DATA DA ABERTURA DA OS"].min())
                    data_fechamento_os = pd.to_datetime(group["DATA DO FECHAMENTO DA OS"].max())

                    # Calcula a diferença em dias
                    diff_in_days = (data_fechamento_os - data_abertura_os).days

                    # Diff tem que ser no minimo 0
                    if diff_in_days < 0:
                        diff_in_days = 0

                    tempos_cumulativos.append({"problem_no": problem_no, "vehicle_id": vehicle_id, "tempo_cumulativo": diff_in_days})
            except Exception as e:
                print(e)
                # Adiciona como -1 para indicar que não foi possível calcular e sinalizar o problema
                tempos_cumulativos.append({"problem_no": problem_no, "vehicle_id": vehicle_id, "tempo_cumulativo": -1})

        # Recria o dataframe
        df_tempos_cumulativos = pd.DataFrame(tempos_cumulativos)

        # Ordena
        df_tempos_cumulativos_sorted = df_tempos_cumulativos.sort_values(by="tempo_cumulativo")

        # Criando a coluna cumulativa em termos percentuais
        df_tempos_cumulativos_sorted["cumulative_percentage"] = (
            df_tempos_cumulativos_sorted["tempo_cumulativo"].expanding().count() / len(df_tempos_cumulativos_sorted) * 100
        )

        return df_tempos_cumulativos_sorted

    def get_retrabalho_por_modelo(self, df):
        df_agg_modelo_veiculo = (
            df.groupby(["DESCRICAO DO MODELO", "CODIGO DO VEICULO"])
            .agg(
                {
                    "NUMERO DA OS": "count",
                    "retrabalho": "sum",
                    "correcao": "sum",
                    "correcao_primeira": "sum",
                    "problem_no": lambda x: x.nunique(),  # Conta o número de problemas distintos
                }
            )
            .reset_index()
        )

        df_modelo = (
            df_agg_modelo_veiculo.groupby("DESCRICAO DO MODELO")
            .agg(
                {
                    "NUMERO DA OS": "sum",
                    "retrabalho": "sum",
                    "correcao": "sum",
                    "correcao_primeira": "sum",
                    "problem_no": "sum",  #
                }
            )
            .reset_index()
            .copy()
        )

        # Renomeia algumas colunas para  CAPS LOCK para facilitar a visualização
        df_modelo.rename(
            columns={
                "NUMERO DA OS": "TOTAL_DE_OS",
                "retrabalho": "RETRABALHO",
                "correcao": "CORRECAO",
                "correcao_primeira": "CORRECOES_DE_PRIMEIRA",
                "problem_no": "NUM_PROBLEMAS",
            },
            inplace=True,
        )

        # Adiciona algumas colunas para facilitar a análise
        df_modelo["CORRECOES_TARDIA"] = df_modelo["CORRECAO"] - df_modelo["CORRECOES_DE_PRIMEIRA"]

        # Calcula as porcentagens
        df_modelo["PERC_RETRABALHO"] = 100 * (df_modelo["RETRABALHO"] / df_modelo["TOTAL_DE_OS"])
        df_modelo["PERC_CORRECOES"] = 100 * (df_modelo["CORRECAO"] / df_modelo["TOTAL_DE_OS"])
        df_modelo["PERC_CORRECOES_DE_PRIMEIRA"] = 100 * (df_modelo["CORRECOES_DE_PRIMEIRA"] / df_modelo["TOTAL_DE_OS"])
        df_modelo["PERC_CORRECOES_TARDIA"] = 100 * (df_modelo["CORRECOES_TARDIA"] / df_modelo["TOTAL_DE_OS"])
        df_modelo["REL_PROBLEMA_OS"] = df_modelo["NUM_PROBLEMAS"] / df_modelo["TOTAL_DE_OS"]

        return df_modelo
