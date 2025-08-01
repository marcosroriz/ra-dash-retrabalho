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
                AND (od."PRIORIDADE SERVICO" = ANY (ARRAY['Vermelho'::text, 'Amarelo'::text, 'Verde'::text]))
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
            --AND (
            --    od."COLABORADOR QUE EXECUTOU O SERVICO" = '3561'
            --)
            --and (
            --	od."CODIGO DO VEICULO" = '50714'
            --	or 
            --	od."CODIGO DO VEICULO" = '50774'
            --	or
            --	od."CODIGO DO VEICULO" = '50763'
            --	)
	    ORDER BY
		    od."DATA DA ABERTURA DA OS" 
        """
        df_os_query = pd.read_sql_query(query, self.dbEngine)
        print(query)
        print("shape", df_os_query.shape)

        print(df_os_query[["NUMERO DA OS"]].drop_duplicates().shape)

        # Tratamento de datas
        df_os_query["DATA INICIO SERVICO"] = pd.to_datetime(df_os_query["DATA INICIO SERVIÇO"])
        df_os_query["DATA DE FECHAMENTO DO SERVICO"] = pd.to_datetime(df_os_query["DATA DE FECHAMENTO DO SERVICO"])

        return df_os_query

    def obtem_dados_os_llm_sql(self, datas, min_dias, lista_modelos, lista_oficinas, lista_os):
        # Extraí a data inicial (já em string)
        data_inicio_str = datas[0]

        # Extraí a data final
        # Remove min_dias antes para evitar que a última OS não seja retrabalho
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")

        # Subqueries
        subquery_modelos_str = subquery_modelos(lista_modelos, prefix="main.", termo_all="TODOS")
        subquery_oficinas_str = subquery_oficinas(lista_oficinas, prefix="main.")
        subquery_os_str = subquery_os(lista_os, prefix="main.")

        query = f"""
        SELECT 
            *
        FROM 
            os_dados main
        LEFT JOIN
            os_dados_classificacao osclass
        ON 
            main."KEY_HASH" = osclass."KEY_HASH"
        WHERE
            main."DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            AND main."DATA DA ABERTURA DA OS" IS NOT NULL 
            AND main."DATA DO FECHAMENTO DA OS" IS NOT NULL 
            AND main."DATA DA ABERTURA DA OS" ~ '^\\d{{4}}-\\d{{2}}-\\d{{2}}T\\d{{2}}:\\d{{2}}:\\d{{2}}$'::text 
            AND main."DATA DO FECHAMENTO DA OS" ~ '^\\d{{4}}-\\d{{2}}-\\d{{2}}T\\d{{2}}:\\d{{2}}:\\d{{2}}$'::text 
            AND main."DESCRICAO DO TIPO DA OS" = 'OFICINA'::text
            {subquery_modelos_str}
            {subquery_oficinas_str}
            {subquery_os_str}
	    """

        df_llm = pd.read_sql_query(query, self.dbEngine)
        df_llm = df_llm.loc[:, ~df_llm.columns.duplicated()]

        return df_llm

    def obtem_dados_os_custo_sql(self, datas, min_dias, lista_modelos, lista_oficinas, lista_os):
        # Extraí a data inicial (já em string)
        data_inicio_str = datas[0]

        # Extraí a data final
        # Remove min_dias antes para evitar que a última OS não seja retrabalho
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")

        # Subqueries
        subquery_modelos_str = subquery_modelos(lista_modelos, prefix="main.", termo_all="TODOS")
        subquery_oficinas_str = subquery_oficinas(lista_oficinas, prefix="main.")
        subquery_os_str = subquery_os(lista_os, prefix="main.")

        query = f"""
        SELECT 
            *
        FROM 
            os_dados main
        JOIN
            view_pecas_desconsiderando_combustivel pg
        ON
            main."NUMERO DA OS" = pg."OS"
        WHERE
            main."DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            AND main."DATA DA ABERTURA DA OS" IS NOT NULL 
            AND main."DATA DO FECHAMENTO DA OS" IS NOT NULL 
            AND main."DATA DA ABERTURA DA OS" ~ '^\\d{{4}}-\\d{{2}}-\\d{{2}}T\\d{{2}}:\\d{{2}}:\\d{{2}}$'::text 
            AND main."DATA DO FECHAMENTO DA OS" ~ '^\\d{{4}}-\\d{{2}}-\\d{{2}}T\\d{{2}}:\\d{{2}}:\\d{{2}}$'::text 
            AND main."DESCRICAO DO TIPO DA OS" = 'OFICINA'::text
            {subquery_modelos_str}
            {subquery_oficinas_str}
            {subquery_os_str}
	    """

        df_custo = pd.read_sql_query(query, self.dbEngine)
        df_custo = df_custo.loc[:, ~df_custo.columns.duplicated()]

        return df_custo

    # Função que retorna os dados dos colaboradores de um conjunto de OS
    def obtem_dados_colaboradores_pandas(self, df_os, df_llm, df_custo):
        # Obtem lista de mecânicos
        df_mecanicos = get_mecanicos(self.dbEngine)

        # Estatísticas por colaborador
        df_colaborador = (
            df_os.groupby("COLABORADOR QUE EXECUTOU O SERVICO")
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

        # Renomeia algumas colunas
        df_colaborador = df_colaborador.rename(
            columns={
                "NUMERO DA OS": "TOTAL_DE_OS",
                "retrabalho": "RETRABALHOS",
                "correcao": "CORRECOES",
                "correcao_primeira": "CORRECOES_DE_PRIMEIRA",
                "problem_no": "NUM_PROBLEMAS",
            }
        )
        df_colaborador["TOTAL_PROBLEMA"] = df_colaborador["NUM_PROBLEMAS"]

        # Calcula notas LLM
        df_llm_agg = df_llm.groupby("COLABORADOR QUE EXECUTOU O SERVICO").agg(
            {"SOLUTION_HAS_COHERENCE_TO_PROBLEM": ["sum", "count"], "SCORE_SOLUTION_TEXT_QUALITY": "mean"}
        ).reset_index()

        df_llm_agg.columns = ["COLABORADOR QUE EXECUTOU O SERVICO", "sum_coherence", "count_coherence", "NOTA_MEDIA_SOLUCAO"]
        # Drop nans
        df_llm_agg = df_llm_agg.dropna()
        df_llm_agg["PERC_SOLUCAO_COERENTE"] = 100 * (df_llm_agg["sum_coherence"] / df_llm_agg["count_coherence"])

        # Merge colaborador com LLM
        df_colaborador = df_colaborador.merge(df_llm_agg, how="left", on="COLABORADOR QUE EXECUTOU O SERVICO")

        # Retrabalho
        df_retrabalho = df_os[df_os["retrabalho"]]
        df_retrabalho_custo = df_retrabalho.merge(df_custo, how="left", on="NUMERO DA OS")
        # Primeiro agrupa por OS e colaborador para evitar contar mais de uma vez o custo de uma OS de um colaborador
        df_retrabalho_custo_agg = df_retrabalho_custo.groupby(["COLABORADOR QUE EXECUTOU O SERVICO","NUMERO DA OS"])["VALOR"].sum().reset_index()
        # Agora agrupa por colaborador
        df_retrabalho_custo_colaborador = df_retrabalho_custo_agg.groupby("COLABORADOR QUE EXECUTOU O SERVICO")["VALOR"].sum().reset_index()
        # Renomeia coluna VALOR para TOTAL_GASTO_RETRABALHO
        df_retrabalho_custo_colaborador = df_retrabalho_custo_colaborador.rename(columns={"VALOR": "TOTAL_GASTO_RETRABALHO"})

        # Gasto total
        df_colaborador_custo = df_os.merge(df_custo, how="left", on="NUMERO DA OS")
        # Primeiro agrupa por OS e colaborador para evitar contar mais de uma vez o custo de uma OS de um colaborador
        df_colaborador_custo_agg = df_colaborador_custo.groupby(["COLABORADOR QUE EXECUTOU O SERVICO","NUMERO DA OS"])["VALOR"].sum().reset_index()
        # Agora agrupa por colaborador
        df_total_custo_colaborador = df_colaborador_custo_agg.groupby("COLABORADOR QUE EXECUTOU O SERVICO")["VALOR"].sum().reset_index()
        # Renomeia coluna VALOR para TOTAL_GASTO
        df_total_custo_colaborador = df_total_custo_colaborador.rename(columns={"VALOR": "TOTAL_GASTO"})

        # Merge com custos
        df_colaborador = df_colaborador.merge(df_retrabalho_custo_colaborador, on="COLABORADOR QUE EXECUTOU O SERVICO", how="left")
        df_colaborador = df_colaborador.merge(df_total_custo_colaborador, on="COLABORADOR QUE EXECUTOU O SERVICO", how="left")
        df_colaborador = df_colaborador.fillna(0)

        # Correções Tardias
        df_colaborador["CORRECOES_TARDIA"] = df_colaborador["CORRECOES"] - df_colaborador["CORRECOES_DE_PRIMEIRA"]
        # Calcula as porcentagens
        df_colaborador["PERC_RETRABALHO"] = 100 * (df_colaborador["RETRABALHOS"] / df_colaborador["TOTAL_DE_OS"])
        df_colaborador["PERC_CORRECOES"] = 100 * (df_colaborador["CORRECOES"] / df_colaborador["TOTAL_DE_OS"])
        df_colaborador["PERC_CORRECAO_PRIMEIRA"] = 100 * (
            df_colaborador["CORRECOES_DE_PRIMEIRA"] / df_colaborador["TOTAL_DE_OS"]
        )
        df_colaborador["PERC_CORRECOES_TARDIA"] = 100 * (
            df_colaborador["CORRECOES_TARDIA"] / df_colaborador["TOTAL_DE_OS"]
        )
        df_colaborador["REL_OS_PROBLEMA"] =  df_colaborador["TOTAL_DE_OS"] / df_colaborador["NUM_PROBLEMAS"]

        # Adiciona label de nomes
        df_colaborador["COLABORADOR QUE EXECUTOU O SERVICO"] = df_colaborador[
            "COLABORADOR QUE EXECUTOU O SERVICO"
        ].astype(int)

        # Encontra o nome do colaborador
        for ix, linha in df_colaborador.iterrows():
            colaborador = linha["COLABORADOR QUE EXECUTOU O SERVICO"]
            nome_colaborador = "Não encontrado"
            if colaborador in df_mecanicos["cod_colaborador"].values:
                nome_colaborador = df_mecanicos[df_mecanicos["cod_colaborador"] == colaborador][
                    "nome_colaborador"
                ].values[0]
                nome_colaborador = re.sub(r"(?<!^)([A-Z])", r" \1", nome_colaborador)

            df_colaborador.at[ix, "LABEL_COLABORADOR"] = f"{nome_colaborador} - {int(colaborador)}"
            df_colaborador.at[ix, "NOME_COLABORADOR"] = f"{nome_colaborador}"
            df_colaborador.at[ix, "ID_COLABORADOR"] = int(colaborador)

        return df_colaborador

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

                    tempos_cumulativos.append(
                        {"problem_no": problem_no, "vehicle_id": vehicle_id, "tempo_cumulativo": diff_in_days}
                    )
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
            df_tempos_cumulativos_sorted["tempo_cumulativo"].expanding().count()
            / len(df_tempos_cumulativos_sorted)
            * 100
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

    def get_indicadores_gerais(self, df):
        # Tempo para conclusão
        df_dias_para_correcao = (
            df.groupby(["problem_no", "CODIGO DO VEICULO", "DESCRICAO DO MODELO"])
            .agg(
                data_inicio=("DATA DA ABERTURA DA OS", "min"),
                data_fim=("DATA DO FECHAMENTO DA OS", "max"),
            )
            .reset_index()
        )
        df_dias_para_correcao["data_inicio"] = pd.to_datetime(df_dias_para_correcao["data_inicio"])
        df_dias_para_correcao["data_fim"] = pd.to_datetime(df_dias_para_correcao["data_fim"])
        df_dias_para_correcao["dias_correcao"] = (
            df_dias_para_correcao["data_fim"] - df_dias_para_correcao["data_inicio"]
        ).dt.days

        # Num de OS para correção
        df_num_os_por_problema = df.groupby(["problem_no", "CODIGO DO VEICULO"]).size().reset_index(name="TOTAL_DE_OS")

        # DF estatística
        df_estatistica = pd.DataFrame(
            {
                "TOTAL_DE_OS": len(df),
                "TOTAL_DE_PROBLEMAS": len(df[df["correcao"]]),
                "TOTAL_DE_RETRABALHOS": len(df[df["retrabalho"]]),
                "TOTAL_DE_CORRECOES": len(df[df["correcao"]]),
                "TOTAL_DE_CORRECOES_DE_PRIMEIRA": len(df[df["correcao_primeira"]]),
                "MEDIA_DE_DIAS_PARA_CORRECAO": df_dias_para_correcao["dias_correcao"].mean(),
                "MEDIANA_DE_DIAS_PARA_CORRECAO": df_dias_para_correcao["dias_correcao"].median(),
                "MEDIA_DE_OS_PARA_CORRECAO": df_num_os_por_problema["TOTAL_DE_OS"].mean(),
            },
            index=[0],
        )
        # Correções tardias
        df_estatistica["TOTAL_DE_CORRECOES_TARDIAS"] = (
            df_estatistica["TOTAL_DE_CORRECOES"] - df_estatistica["TOTAL_DE_CORRECOES_DE_PRIMEIRA"]
        )
        # Rel probl/os
        df_estatistica["RELACAO_OS_PROBLEMA"] = df_estatistica["TOTAL_DE_OS"] / df_estatistica["TOTAL_DE_PROBLEMAS"]

        # Porcentagens
        df_estatistica["PERC_RETRABALHO"] = 100 * (
            df_estatistica["TOTAL_DE_RETRABALHOS"] / df_estatistica["TOTAL_DE_OS"]
        )
        df_estatistica["PERC_CORRECOES"] = 100 * (df_estatistica["TOTAL_DE_CORRECOES"] / df_estatistica["TOTAL_DE_OS"])
        df_estatistica["PERC_CORRECOES_DE_PRIMEIRA"] = 100 * (
            df_estatistica["TOTAL_DE_CORRECOES_DE_PRIMEIRA"] / df_estatistica["TOTAL_DE_OS"]
        )
        df_estatistica["PERC_CORRECOES_TARDIAS"] = 100 * (
            df_estatistica["TOTAL_DE_CORRECOES_TARDIAS"] / df_estatistica["TOTAL_DE_OS"]
        )

        return df_dias_para_correcao, df_num_os_por_problema, df_estatistica

    def get_indicadores_colaboradores(self, df):
        df_colaborador = (
            df.groupby("COLABORADOR QUE EXECUTOU O SERVICO")
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

        # Renomeia algumas colunas
        df_colaborador = df_colaborador.rename(
            columns={
                "NUMERO DA OS": "TOTAL_DE_OS",
                "retrabalho": "RETRABALHOS",
                "correcao": "CORRECOES",
                "correcao_primeira": "CORRECOES_DE_PRIMEIRA",
                "problem_no": "NUM_PROBLEMAS",
            }
        )

        # Correções Tardias
        df_colaborador["CORRECOES_TARDIA"] = df_colaborador["CORRECOES"] - df_colaborador["CORRECOES_DE_PRIMEIRA"]
        # Calcula as porcentagens
        df_colaborador["PERC_RETRABALHO"] = 100 * (df_colaborador["RETRABALHOS"] / df_colaborador["TOTAL_DE_OS"])
        df_colaborador["PERC_CORRECOES"] = 100 * (df_colaborador["CORRECOES"] / df_colaborador["TOTAL_DE_OS"])
        df_colaborador["PERC_CORRECOES_DE_PRIMEIRA"] = 100 * (
            df_colaborador["CORRECOES_DE_PRIMEIRA"] / df_colaborador["TOTAL_DE_OS"]
        )
        df_colaborador["PERC_CORRECOES_TARDIA"] = 100 * (
            df_colaborador["CORRECOES_TARDIA"] / df_colaborador["TOTAL_DE_OS"]
        )
        df_colaborador["REL_PROBLEMA_OS"] = df_colaborador["NUM_PROBLEMAS"] / df_colaborador["TOTAL_DE_OS"]

        return df_colaborador
