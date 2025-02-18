#!/usr/bin/env python
# coding: utf-8

# Classe que centraliza os serviços para mostrar na página retrabalho por OS (tipo de serviço)

# Imports básicos
import re
import pandas as pd
import numpy as np

# Imports auxiliares
from modules.sql_utils import subquery_oficinas, subquery_secoes, subquery_os
from modules.entities_utils import get_mecanicos


# Classe do serviço
class OSService:
    def __init__(self, dbEngine):
        self.dbEngine = dbEngine

    def obtem_dados_os_sql(lista_os, data_inicio_str, data_fim_str, min_dias):
        # Extraí a data final
        # Remove min_dias antes para evitar que a última OS não seja retrabalho
        data_fim_dt = pd.to_datetime(data_fim_str)
        data_fim_corrigida_dt = data_fim_dt - pd.DateOffset(days=min_dias + 1)
        data_fim_corrigida_str = data_fim_corrigida_dt.strftime("%Y-%m-%d")

        # Query
        query = f"""
        WITH os_diff_days AS (
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
                lag(od."DATA DE FECHAMENTO DO SERVICO") OVER (PARTITION BY od."CODIGO DO VEICULO" ORDER BY od."DATA DA ABERTURA DA OS") AS "PREV_DATA_FECHAMENTO",
                lead(od."DATA DA ABERTURA DA OS") OVER (PARTITION BY od."CODIGO DO VEICULO" ORDER BY od."DATA DE FECHAMENTO DO SERVICO") AS "NEXT_DATA_ABERTURA",
                    CASE
                        WHEN lag(od."DATA DE FECHAMENTO DO SERVICO") OVER (PARTITION BY od."CODIGO DO VEICULO" ORDER BY od."DATA DA ABERTURA DA OS") IS NOT NULL AND od."DATA DA ABERTURA DA OS" IS NOT NULL THEN date_part('day'::text, od."DATA DA ABERTURA DA OS"::timestamp without time zone - lag(od."DATA DE FECHAMENTO DO SERVICO") OVER (PARTITION BY od."CODIGO DO VEICULO" ORDER BY od."DATA DA ABERTURA DA OS")::timestamp without time zone)
                        ELSE NULL::double precision
                    END AS prev_days,
                    CASE
                        WHEN od."DATA DE FECHAMENTO DO SERVICO" IS NOT NULL AND lead(od."DATA DA ABERTURA DA OS") OVER (PARTITION BY od."CODIGO DO VEICULO" ORDER BY od."DATA DE FECHAMENTO DO SERVICO") IS NOT NULL THEN date_part('day'::text, lead(od."DATA DA ABERTURA DA OS") OVER (PARTITION BY od."CODIGO DO VEICULO" ORDER BY od."DATA DE FECHAMENTO DO SERVICO")::timestamp without time zone - od."DATA DE FECHAMENTO DO SERVICO"::timestamp without time zone)
                        ELSE NULL::double precision
                    END AS next_days
            FROM 
                os_dados od
            WHERE 
                od."DATA INICIO SERVIÇO" IS NOT NULL 
                AND od."DATA DE FECHAMENTO DO SERVICO" IS NOT NULL 
                AND od."DATA INICIO SERVIÇO" ~ '^\\d{{4}}-\\d{{2}}-\\d{{2}}T\\d{{2}}:\\d{{2}}:\\d{{2}}$'::text 
                AND od."DATA DE FECHAMENTO DO SERVICO" ~ '^\\d{{4}}-\\d{{2}}-\\d{{2}}T\\d{{2}}:\\d{{2}}:\\d{{2}}$'::text 
                AND od."DESCRICAO DO TIPO DA OS" = 'OFICINA'::text
            ), 
        os_with_flags AS (
            SELECT 
                os_diff_days."NUMERO DA OS",
                os_diff_days."CODIGO DO VEICULO",
                os_diff_days."DESCRICAO DO SERVICO",
                os_diff_days."DESCRICAO DO MODELO",
                os_diff_days."DATA INICIO SERVIÇO",
                os_diff_days."DATA DE FECHAMENTO DO SERVICO",
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
                    END) OVER (PARTITION BY os_with_flags."CODIGO DO VEICULO" ORDER BY os_with_flags."DATA INICIO SERVIÇO") AS problem_no,
                os_with_flags."NUMERO DA OS",
                os_with_flags."CODIGO DO VEICULO",
                os_with_flags."DESCRICAO DO SERVICO",
                os_with_flags."DESCRICAO DO MODELO",
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
            )
        
        SELECT
            CASE
                WHEN problem_grouping.retrabalho THEN problem_grouping.problem_no + 1
                ELSE problem_grouping.problem_no
            END AS problem_no,
            problem_grouping."NUMERO DA OS",
            problem_grouping."CODIGO DO VEICULO",
            problem_grouping."DESCRICAO DO MODELO",
            problem_grouping."DESCRICAO DO SERVICO",
            problem_grouping."DATA INICIO SERVIÇO",
            problem_grouping."DATA DE FECHAMENTO DO SERVICO",
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
            problem_grouping."DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_corrigida_str}'
            AND problem_grouping."DESCRICAO DO SERVICO" IN ({', '.join([f"'{x}'" for x in lista_os])})
            --  AND problem_grouping."DESCRICAO DO MODELO" IN ('M.BENZ O 500/INDUSCAR MILLEN A')
            -- AND (
            --"DESCRICAO DO SERVICO" = 'Motor cortando alimentação'
            --OR
            --"DESCRICAO DO SERVICO" = 'Motor sem força'
            --)
            --AND 
            --(
            -- AND od."CODIGO DO VEICULO" ='50803'
            --OR
            --od."CODIGO DO VEICULO" ='50530'
            --)
        ORDER BY 
            problem_grouping."DATA INICIO SERVIÇO";
        """

        df_os_query = pd.read_sql_query(query, self.dbEngine)

        # Tratamento de datas
        df_os_query["DATA INICIO SERVICO"] = pd.to_datetime(
            df_os_query["DATA INICIO SERVIÇO"]
        )
        df_os_query["DATA DE FECHAMENTO DO SERVICO"] = pd.to_datetime(
            df_os_query["DATA DE FECHAMENTO DO SERVICO"]
        )

        return df_os_query
