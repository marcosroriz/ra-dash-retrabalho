 #Classe que centraliza os serviços para mostrar na página home

# Imports básicos
import re
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Imports auxiliares
from modules.sql_utils import subquery_oficinas, subquery_secoes, subquery_os, subquery_veiculos, subquery_modelos_veiculos, subquery_equipamentos, subquery_modelos_pecas
from modules.veiculos.helps import HelpsVeiculos

# Classe do serviço
class VeiculoService:
    def __init__(self, dbEngine):
        self.dbEngine = dbEngine

    def atualizar_veiculos_func(self, modelos_selecionados):

        subquery_modelos_veiculos_str = subquery_modelos_veiculos(modelos_selecionados)

        df_lista_veiculos = pd.read_sql(
            f"""
            SELECT DISTINCT
                "CODIGO DO VEICULO" AS "VEICULO",
                "DESCRICAO DO MODELO" AS "MODELO"
            FROM 
                mat_view_retrabalho_10_dias mvrd
            WHERE 1=1
                {subquery_modelos_veiculos_str}
            """,
            self.dbEngine,
        )

        # Ordenar os resultados
        df_lista_veiculos = df_lista_veiculos.sort_values("VEICULO")

        # Adicionar a opção "TODAS" manualmente
        # PARA VOLTAR A FUNÇÃO "TODAS", SÓ DESCOMENTAR E COMENTAR/EXCLUIR A LINHA POSTERIOR 
        #lista_todos_veiculos = [{"VEICULO": "TODAS", "MODELO": "TODOS OS VEÍCULOS"}] + df_lista_veiculos.to_dict(orient="records")

        # Adicionar a opção "TODAS" manualmente
        lista_todos_veiculos = df_lista_veiculos.to_dict(orient="records")

        return lista_todos_veiculos
    
    def atualizar_servicos_func(self, datas, min_dias, lista_oficinas, lista_secaos, lista_veiculos):
        # Datas
        data_inicio_str = datas[0]

        # Remove min_dias antes para evitar que a última OS não seja retrabalho
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")

        # Subqueries para oficinas, seções e veículos
        subquery_oficinas_str = subquery_oficinas(lista_oficinas)
        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_veiculos_str = subquery_veiculos(lista_veiculos)
        
        query = f"""
            SELECT 
                "CODIGO DO VEICULO",
                DATE_TRUNC('month', "DATA DO FECHAMENTO DA OS"::timestamp) AS "MÊS",
                COUNT("NUMERO DA OS") AS "QUANTIDADE_DE_OS",
                "DESCRICAO DO SERVICO",
                "DESCRICAO DO MODELO",
                COUNT(DISTINCT "COLABORADOR QUE EXECUTOU O SERVICO") AS "QTD_COLABORADORES"
            FROM
                mat_view_retrabalho_{min_dias}_dias
            WHERE
                "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                {subquery_oficinas_str}
                {subquery_secoes_str}
                {subquery_veiculos_str}
            GROUP BY
                "CODIGO DO VEICULO",
                DATE_TRUNC('month', "DATA DO FECHAMENTO DA OS"::timestamp),
                "DESCRICAO DO SERVICO",
                "DESCRICAO DO MODELO"
            ORDER BY
                "CODIGO DO VEICULO",
                "MÊS";
            """
        # Consulta SQL para pegar os serviços
        df_lista_servicos = pd.read_sql(query,self.dbEngine,)

        # Extrair e retornar a lista de serviços
        lista_servicos = sorted(df_lista_servicos["DESCRICAO DO SERVICO"].dropna().unique().tolist())
        
        return lista_servicos

    def sintese_geral_fun(self, datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
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
        subquery_veiculos_os = subquery_veiculos(lista_veiculos)


        # Query
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
                "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                {subquery_oficinas_str}
                {subquery_secoes_str}
                {subquery_os_str}
                {subquery_veiculos_os}
        """
        
        # Executa a query
        df = pd.read_sql(query, self.dbEngine)

        # Calcula o total de correções tardia
        df["TOTAL_CORRECAO_TARDIA"] = df["TOTAL_CORRECAO"] - df["TOTAL_CORRECAO_PRIMEIRA"]

        # Prepara os dados para o gráfico
        labels = ["Correções de Primeira", "Correções Tardias", "Retrabalhos"]
        values = [
            df["TOTAL_CORRECAO_PRIMEIRA"].values[0],
            df["TOTAL_CORRECAO_TARDIA"].values[0],
            df["TOTAL_RETRABALHO"].values[0],
        ]


        total_correcao_primeira = f'''{df.iloc[0]['PERC_CORRECAO_PRIMEIRA']}%'''
        total_retrabalho = f'''{df.iloc[0]['PERC_RETRABALHO']}%'''

        return total_retrabalho, total_correcao_primeira, labels, values

    def evolucao_retrabalho_por_veiculo_por_mes_fun(self, datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
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
        subquery_veiculos_str = subquery_veiculos(lista_veiculos)

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
            {subquery_oficinas_str} 
            {subquery_secoes_str}
            {subquery_os_str}
            {subquery_veiculos_str}

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

        lista_modelos = df["DESCRICAO DO MODELO"].dropna().unique().tolist() ## preciso da lista de nomes dos modelos

        if len(lista_modelos) >= 1:
            pass
        else:
            lista_modelos = [""]

        service_aux = HelpsVeiculos(self.dbEngine)

        media_geral_modelos = service_aux.media_geral_retrabalho_modelos(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos, lista_modelos)

        media_geral = service_aux.media_geral_retrabalho_geral(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos)

        df_combinado = pd.concat([df_combinado, media_geral_modelos, media_geral], ignore_index=True)

        return df_combinado
    
    def retrabalho_por_secao_por_mes_fun(self, datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
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
        subquery_veiculos_str = subquery_veiculos(lista_veiculos)

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
            {subquery_oficinas_str}
            {subquery_secoes_str}
            {subquery_os_str}
            {subquery_veiculos_str}
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

        # Multiplica por 100
        # df_combinado["PERC"] = df_combinado["PERC"] * 100

        return df_combinado

    def evolucao_quantidade_os_por_mes_fun(self, datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):

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
        subquery_veiculos_str = subquery_veiculos(lista_veiculos)

        if data_inicio_str is None:
            data_inicio_str = '1900-01-01'  # Ou algum valor padrão válido
        if data_fim_str is None:
            data_fim_str = '1901-01-01'  # Ou algum valor padrão válido

        query = f"""
            SELECT 
                "CODIGO DO VEICULO",
                DATE_TRUNC('month', "DATA DO FECHAMENTO DA OS"::timestamp) AS "MÊS",
                COUNT(DISTINCT "NUMERO DA OS") AS "QUANTIDADE_DE_OS",
                COUNT(DISTINCT "NUMERO DA OS") AS "QUANTIDADE_DE_OS_DIF",
                "DESCRICAO DO SERVICO",
                "DESCRICAO DO MODELO",
                COUNT(DISTINCT "COLABORADOR QUE EXECUTOU O SERVICO") AS "QTD_COLABORADORES"
            FROM
                mat_view_retrabalho_{min_dias}_dias_distinct
            WHERE
                "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                {subquery_oficinas_str}
                {subquery_secoes_str}
                {subquery_os_str}
                {subquery_veiculos_str}
            GROUP BY
                "CODIGO DO VEICULO",
                DATE_TRUNC('month', "DATA DO FECHAMENTO DA OS"::timestamp),
                "DESCRICAO DO SERVICO",
                "DESCRICAO DO MODELO"
            ORDER BY
                "CODIGO DO VEICULO",
                "MÊS";
        """

        query_colaboradores_diferentes = f"""
                SELECT 
                COUNT(DISTINCT "COLABORADOR QUE EXECUTOU O SERVICO") AS "TOTAL_COLABORADORES_DIFERENTES"
            FROM 
                mat_view_retrabalho_{min_dias}_dias
            WHERE 
                "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                {subquery_oficinas_str}
                {subquery_secoes_str}
                {subquery_os_str}
                {subquery_veiculos_str};
        """

        query_descobrir_os_problemas = f"""
            SELECT 
            COUNT(DISTINCT ("NUMERO DA OS", "DESCRICAO DO SERVICO")) AS "TOTAL_OS",
            COUNT(DISTINCT "DESCRICAO DO SERVICO")  AS "TOTAL_DESCRIÇOES",
            COUNT(DISTINCT ("problem_no", "DESCRICAO DO SERVICO")) AS "TOTAL_PROBLEMOS_DESCRICOES",
            COUNT(DISTINCT "COLABORADOR QUE EXECUTOU O SERVICO")  AS "TOTAL_COLABORADORES"
            FROM (
                SELECT "NUMERO DA OS", "DESCRICAO DO SERVICO", "problem_no", "COLABORADOR QUE EXECUTOU O SERVICO"
                FROM mat_view_retrabalho_{min_dias}_dias
                WHERE "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                    {subquery_oficinas_str}
                    {subquery_secoes_str}
                    {subquery_os_str}
                    {subquery_veiculos_str}
            ) AS subquery;
        """


        query_ranking_os_problemas = f"""
            SELECT
                "CODIGO DO VEICULO",
                "DESCRICAO DO MODELO",
                COUNT(DISTINCT ("problem_no", "DESCRICAO DO SERVICO"))AS "TOTAL_CORRECAO",
                COUNT(DISTINCT ("NUMERO DA OS", "DESCRICAO DO SERVICO")) AS "TOTAL_OS"
            FROM
                mat_view_retrabalho_{min_dias}_dias
            WHERE
                "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                {subquery_oficinas_str}
                {subquery_secoes_str}
                {subquery_os_str}
            GROUP BY
                "CODIGO DO VEICULO",
                "DESCRICAO DO MODELO";
        """
        #### RANKING DE OS/PROBLEMA GERAL
        df_ranking = pd.read_sql(query_ranking_os_problemas, self.dbEngine)
        df_ranking["OS_POR_PROBLEMAS_RAW"] = df_ranking["TOTAL_OS"] / df_ranking["TOTAL_CORRECAO"]
        df_ranking["RANKING"] = df_ranking["OS_POR_PROBLEMAS_RAW"].rank(ascending=True, method='min')
        df_ranking_sorted = df_ranking.sort_values(by="RANKING", ascending=True)

        ### INDICADORES DE PROBLEMAS

        df_qtd_os = pd.read_sql(query_descobrir_os_problemas, self.dbEngine) 

        total_problemas = df_qtd_os["TOTAL_PROBLEMOS_DESCRICOES"].iloc[0]

        os_veiculo_filtradas = df_qtd_os["TOTAL_OS"].iloc[0]

        servicos_diff = df_qtd_os["TOTAL_DESCRIÇOES"].iloc[0]
        
        total_colaboradores = df_qtd_os["TOTAL_COLABORADORES"].iloc[0]


        ##QUERY OK !!
        query_media = f"""
            WITH os_count AS (
                SELECT 
                    "CODIGO DO VEICULO",
                    DATE_TRUNC('month', "DATA DO FECHAMENTO DA OS"::timestamp) AS "MÊS",
                    COUNT(DISTINCT ("NUMERO DA OS", "DESCRICAO DO SERVICO")) AS "QUANTIDADE_DE_OS",
                    COUNT(DISTINCT "DESCRICAO DO SERVICO") AS "QUANTIDADE_DE_DESCRICOES_DISTINTAS"
                FROM mat_view_retrabalho_{min_dias}_dias
                WHERE 
                "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                {subquery_oficinas_str}
                {subquery_secoes_str}
                {subquery_os_str}
                GROUP BY
                    "CODIGO DO VEICULO",
                    DATE_TRUNC('month', "DATA DO FECHAMENTO DA OS"::timestamp)
            )
            SELECT 
                "MÊS",
                SUM("QUANTIDADE_DE_OS") AS "TOTAL_DE_OS_NO_MÊS",
                AVG("QUANTIDADE_DE_OS") AS "QUANTIDADE_DE_OS",  -- MEDIA_GERAL_OS_POR_MÊS
                AVG("QUANTIDADE_DE_DESCRICOES_DISTINTAS") AS "MEDIA_DESCRICOES_DISTINTAS_POR_MÊS"
            FROM os_count
            GROUP BY
                "MÊS"
            ORDER BY
                "MÊS";
            """
        # Executa Query
        df = pd.read_sql(query, self.dbEngine)

        lista_modelos = df["DESCRICAO DO MODELO"].dropna().unique().tolist()
        

        if len(lista_modelos) >= 1:
            pass
        else:
            lista_modelos = [""]

        ### RANKING DE OS/PROBLEMA POR MODELO AGORA
        df_ranking_modelos = df_ranking[df_ranking["DESCRICAO DO MODELO"].isin(lista_modelos)]
        df_ranking_modelos["OS_POR_PROBLEMAS_RAW"] = df_ranking_modelos["TOTAL_OS"] / df_ranking_modelos["TOTAL_CORRECAO"]
        df_ranking_modelos["RANKING"] = df_ranking_modelos["OS_POR_PROBLEMAS_RAW"].rank(ascending=True, method='min')
        df_ranking_modelos = df_ranking_modelos.sort_values(by="RANKING", ascending=True)


        subquery_modelos_str = subquery_modelos_veiculos(lista_modelos)
        ##QUERY OK !!
        query_media_modelos = f"""
            WITH os_count AS (
                SELECT 
                    "CODIGO DO VEICULO",
                    DATE_TRUNC('month', "DATA DO FECHAMENTO DA OS"::timestamp) AS "MÊS",
                    COUNT(DISTINCT ("NUMERO DA OS", "DESCRICAO DO SERVICO")) AS "QUANTIDADE_DE_OS",
                    COUNT(DISTINCT "DESCRICAO DO SERVICO") AS "QUANTIDADE_DE_DESCRICOES_DISTINTAS",
                    "DESCRICAO DO MODELO"
                FROM mat_view_retrabalho_{min_dias}_dias
                WHERE 
                "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                {subquery_oficinas_str}
                {subquery_secoes_str}
                {subquery_os_str}
                {subquery_modelos_str}
                GROUP BY
                    "CODIGO DO VEICULO",
                    DATE_TRUNC('month', "DATA DO FECHAMENTO DA OS"::timestamp),
                    "DESCRICAO DO MODELO"
            )
            SELECT 
                "MÊS",
                SUM("QUANTIDADE_DE_OS") AS "TOTAL_DE_OS_NO_MÊS",
                AVG("QUANTIDADE_DE_OS") AS "QUANTIDADE_DE_OS",  -- MEDIA_GERAL_OS_POR_MÊS
                AVG("QUANTIDADE_DE_DESCRICOES_DISTINTAS") AS "MEDIA_DESCRICOES_DISTINTAS_POR_MÊS",
                "DESCRICAO DO MODELO"
            FROM os_count
            GROUP BY
                "MÊS",
                "DESCRICAO DO MODELO"
            ORDER BY
                "MÊS";
            """
        df_media_modelos_str = pd.read_sql(query_media_modelos, self.dbEngine)

        df_media_geral = pd.read_sql(query_media, self.dbEngine)
        df_media_geral["CODIGO DO VEICULO"] = 'Geral'

        df_media_modelos_os = df_media_modelos_str.rename(columns={"DESCRICAO DO MODELO": "CODIGO DO VEICULO"})

        # Novo DataFrame com a soma de OS por mês
        df_soma_mes_veiculos = df.groupby(["MÊS", "CODIGO DO VEICULO"], as_index=False)["QUANTIDADE_DE_OS"].sum()

        df_soma_mes = pd.concat([df_soma_mes_veiculos, df_media_geral, df_media_modelos_os], ignore_index=True)


        # Processamento de dados para o segundo gráfico
        colunas_selecionadas = ['MÊS', 'MEDIA_DESCRICOES_DISTINTAS_POR_MÊS', 'CODIGO DO VEICULO']
        df_unico_geral = df_media_geral[colunas_selecionadas]
        df_unico_geral = df_unico_geral.rename(columns={'MEDIA_DESCRICOES_DISTINTAS_POR_MÊS': 'QUANTIDADE_DE_OS'})

        df_unico_modelo = df_media_modelos_os[colunas_selecionadas]
        df_unico_modelo = df_unico_modelo.rename(columns={'MEDIA_DESCRICOES_DISTINTAS_POR_MÊS': 'QUANTIDADE_DE_OS'})


        df_unico = df.drop_duplicates(subset=["DESCRICAO DO SERVICO"], keep="first")
        df_unico["DESCRICAO DO SERVICO"] = df_unico["DESCRICAO DO SERVICO"].str.strip()
        df_unico_soma = df_unico.groupby(["MÊS", "CODIGO DO VEICULO"], as_index=False)["QUANTIDADE_DE_OS"].sum()

        df_os_unicas = pd.concat([df_unico_soma, df_unico_geral, df_unico_modelo], ignore_index=True)
        df_colab_dif = pd.read_sql(query_colaboradores_diferentes, self.dbEngine)
        
        mecanicos_diferentes = int(df_colab_dif['TOTAL_COLABORADORES_DIFERENTES'].sum())
        os_diferentes = int(df_unico['QUANTIDADE_DE_OS_DIF'].sum())
        os_totais_veiculo = int(df_soma_mes_veiculos['QUANTIDADE_DE_OS'].sum()) # 
        
        if len(df_soma_mes_veiculos) >= 1:
            os_problema = os_veiculo_filtradas/total_problemas
            os_problema = round(os_problema, 2)

        else:
            os_problema = 0

        
        rk_os_problema_geral = f'0°'
        rk_os_problema_modelos = f'0°'
        if len(lista_veiculos) <= 1:
            df_rk_veic = df_ranking_sorted.loc[df_ranking_sorted["CODIGO DO VEICULO"] == lista_veiculos[0]]

            if len(df_rk_veic) >= 1:
                rk_n_problema_geral = int(df_rk_veic.iloc[0]["RANKING"])
                contagem_ranking_geral = len(df_ranking_sorted)
                rk_os_problema_geral = f'{rk_n_problema_geral}°/{contagem_ranking_geral}'

            df_rk_veic_mode = df_ranking_modelos.loc[df_ranking_modelos["CODIGO DO VEICULO"] == lista_veiculos[0]]
            if len(df_rk_veic_mode) >= 1:
                rk_n_problema_mode = int(df_rk_veic_mode.iloc[0]["RANKING"])
                contagem_ranking_modelos = len(df_ranking_modelos)
                rk_os_problema_modelos = f'{rk_n_problema_mode}°/{contagem_ranking_modelos}'

        return servicos_diff, total_colaboradores, os_veiculo_filtradas, os_problema, df_soma_mes, df_os_unicas, rk_os_problema_geral, rk_os_problema_modelos
    
    def pecas_trocadas_por_mes_fun(self, datas, min_dias, lista_oficinas, lista_secaos, lista_os, equipamentos):
            # Converte equipamentos para formato compatível com SQL (lista formatada)
        equipamentos_sql = ", ".join(f"'{equip}'" for equip in equipamentos)

        # Datas
        data_inicio_str = datas[0]

        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
        data_fim_str = data_fim.strftime("%Y-%m-%d")

        if data_inicio_str is None:
            data_inicio_str = '1900-01-01'  # Ou algum valor padrão válido
        if data_fim_str is None:
            data_fim_str = '1901-01-01'  # Ou algum valor padrão válido
        
        # # Query para buscar peças trocadas por mês para os veículos selecionados
        # query_veiculos = f"""
        # SELECT 
        #     to_char("DATA"::DATE, 'YYYY-MM') AS year_month,
        #     "EQUIPAMENTO",
        #     ROUND(SUM("VALOR"), 2) AS total_pecas
        # FROM 
        #     pecas_gerais
        # WHERE 
        #     "EQUIPAMENTO" IN ({equipamentos_sql})
        #     AND "DATA"::DATE BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
        #     AND "GRUPO" NOT IN ('COMBUSTIVEIS E LUBRIFICANTES', 'Lubrificantes e Combustiveis Especiais')
        # GROUP BY 
        #     year_month, "EQUIPAMENTO"
        # ORDER BY 
        #     year_month;
        # """
        subquery_equipamentos_str = subquery_equipamentos(equipamentos, "pg.")
        subquery_oficinas_str = subquery_oficinas(lista_oficinas, "od.")
        subquery_secoes_str = subquery_secoes(lista_secaos, "od.")
        subquery_os_str = subquery_os(lista_os, "od.")


        query_teste = f"""
            SELECT
                to_char(pg."DATA"::DATE, 'YYYY-MM') AS year_month,
                ROUND(SUM(pg."VALOR"), 2) AS total_pecas,
                pg."EQUIPAMENTO"
            FROM view_pecas_desconsiderando_combustivel pg
            LEFT JOIN mat_view_retrabalho_{min_dias}_dias_distinct AS od 
                ON pg."OS" = od."NUMERO DA OS"
            WHERE
                od."DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                AND pg."GRUPO" NOT IN ('COMBUSTIVEIS E LUBRIFICANTES', 'Lubrificantes e Combustiveis Especiais')
                {subquery_equipamentos_str}
                {subquery_oficinas_str}
                {subquery_secoes_str}
                {subquery_os_str}
            GROUP BY 
                year_month, pg."EQUIPAMENTO"
            ORDER BY 
                year_month ASC, pg."EQUIPAMENTO" ASC;
            """
        
        # Query para calcular a média geral de peças trocadas por mês
        query_media_geral = f"""
        SELECT 
            to_char("DATA"::DATE, 'YYYY-MM') AS year_month,
            ROUND(SUM("VALOR") / COUNT(DISTINCT "EQUIPAMENTO"), 2) AS media_geral
        FROM 
            view_pecas_desconsiderando_combustivel
        WHERE 
            "DATA"::DATE BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            AND "GRUPO" NOT IN ('COMBUSTIVEIS E LUBRIFICANTES', 'Lubrificantes e Combustiveis Especiais')
        GROUP BY 
            year_month
        ORDER BY 
            year_month;
        """
        query_media_geral_2 = f"""
            SELECT
                to_char(pg."DATA"::DATE, 'YYYY-MM') AS year_month,
                ROUND(SUM(pg."VALOR") / COUNT(DISTINCT pg."EQUIPAMENTO"), 2) AS media_geral
            FROM view_pecas_desconsiderando_combustivel pg
            LEFT JOIN mat_view_retrabalho_{min_dias}_dias_distinct AS od 
                ON pg."OS" = od."NUMERO DA OS"
            WHERE
                od."DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                AND pg."GRUPO" NOT IN ('COMBUSTIVEIS E LUBRIFICANTES', 'Lubrificantes e Combustiveis Especiais')
                {subquery_oficinas_str}
                {subquery_secoes_str}
                {subquery_os_str}
            GROUP BY 
                year_month
            ORDER BY 
                year_month;
        """
        query_media_modelo = f"""
        SELECT 
            to_char(pg."DATA"::DATE, 'YYYY-MM') AS year_month,
            pg."MODELO",
            ROUND(SUM(pg."VALOR") / COUNT(DISTINCT pg."EQUIPAMENTO"), 2) AS media_modelo
        FROM 
            view_pecas_desconsiderando_combustivel pg
            LEFT JOIN mat_view_retrabalho_{min_dias}_dias_distinct AS od 
                ON pg."OS" = od."NUMERO DA OS"
        WHERE 
            od."DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            AND pg."GRUPO" NOT IN ('COMBUSTIVEIS E LUBRIFICANTES', 'Lubrificantes e Combustiveis Especiais')
            AND pg."MODELO" IN (SELECT DISTINCT "MODELO" FROM pecas_gerais WHERE "EQUIPAMENTO" IN ({equipamentos_sql}))
            {subquery_oficinas_str}
            {subquery_secoes_str}
            {subquery_os_str}
        GROUP BY 
            year_month, "MODELO"
        ORDER BY 
            year_month, "MODELO";

        """
        try:
            # Executa a query dos veículos
            df_veiculos = pd.read_sql(query_teste, self.dbEngine)
            # Executa a query da média geral
            df_media_geral = pd.read_sql(query_media_geral_2, self.dbEngine)
            #Executa a query para da a média do modelo
            df_media_modelo = pd.read_sql(query_media_modelo, self.dbEngine)

            # Verifica se há dados
            if df_veiculos.empty and df_media_geral.empty:
                return [], []
            # Converte a coluna de datas para datetime
            df_veiculos["year_month_dt"] = pd.to_datetime(df_veiculos["year_month"], format="%Y-%m", errors="coerce")
            df_media_geral["year_month_dt"] = pd.to_datetime(df_media_geral["year_month"], format="%Y-%m", errors="coerce")
            df_media_modelo["year_month_dt"] = pd.to_datetime(df_media_modelo["year_month"], format="%Y-%m", errors="coerce")

            return df_veiculos, df_media_geral, df_media_modelo
        except Exception as e:
            print(f"Erro ao executar as consultas: {e}")
            return [], [], []
        
    def tabela_pecas_fun(self, datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
            # Datas
        data_inicio_str = datas[0]
        
        # Remove min_dias antes para evitar que a última OS não seja retrabalho
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)

        data_inicio_dt = pd.to_datetime(data_inicio_str)
        data_inicio_str = data_inicio_dt.strftime("%Y/%m/%d")
        data_fim_str = data_fim.strftime("%Y/%m/%d")
        
        subquery_veiculos_str = subquery_equipamentos(lista_veiculos)

        # query_detalhes = f"""
        # SELECT 
        #     "OS", 
        #     "EQUIPAMENTO", 
        #     "MODELO", 
        #     "PRODUTO", 
        #     "QUANTIDADE", 
        #     "VALOR", 
        #     "DATA"
        # FROM pecas_gerais 
        #     WHERE 
        #         TO_DATE("DATA", 'DD/MM/YY') 
        #             BETWEEN TO_DATE('{data_inicio_str}', 'DD/MM/YYYY') 
        #                 AND TO_DATE('{data_fim_str}', 'DD/MM/YYYY')
        #         AND "GRUPO" NOT IN ('COMBUSTIVEIS E LUBRIFICANTES', 'Lubrificantes e Combustiveis Especiais')
        #         {subquery_veiculos_str}
        # """
        subquery_equipamentos_str = subquery_equipamentos(lista_veiculos, "pg.")
        subquery_oficinas_str = subquery_oficinas(lista_oficinas, "od.")
        subquery_secoes_str = subquery_secoes(lista_secaos, "od.")
        subquery_os_str = subquery_os(lista_os, "od.")
        
        query_teste = f"""
            SELECT
                pg."EQUIPAMENTO",
                pg."OS",
                pg."MODELO",
                pg."PRODUTO",
                pg."QUANTIDADE",
                pg."VALOR",
                pg."DATA",
                od."DESCRICAO DO SERVICO",
                od."retrabalho" 
            FROM view_pecas_desconsiderando_combustivel pg
            LEFT JOIN mat_view_retrabalho_{min_dias}_dias_distinct AS od 
                ON pg."OS" = od."NUMERO DA OS"
            WHERE
                1=1
                {subquery_equipamentos_str}
                {subquery_oficinas_str}
                {subquery_secoes_str}
                {subquery_os_str}
                AND od."DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                AND pg."GRUPO" NOT IN ('COMBUSTIVEIS E LUBRIFICANTES', 'Lubrificantes e Combustiveis Especiais')
            ORDER BY 
                pg."VALOR" ASC;
            """

        query_teste_ranking = f"""
         WITH ranking_veiculos AS (
                SELECT
                    pg."EQUIPAMENTO",
                    ROW_NUMBER() OVER (ORDER BY SUM("VALOR") ASC) AS ranking,
                    SUM(pg."VALOR") as total_pecas
                FROM view_pecas_desconsiderando_combustivel pg
                LEFT JOIN mat_view_retrabalho_{min_dias}_dias_distinct AS od 
                    ON pg."OS" = od."NUMERO DA OS"
                WHERE
                    1=1
                    {subquery_oficinas_str}
                    {subquery_secoes_str}
                    {subquery_os_str}
                    AND od."DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                    AND pg."GRUPO" NOT IN ('COMBUSTIVEIS E LUBRIFICANTES', 'Lubrificantes e Combustiveis Especiais')
                GROUP BY "EQUIPAMENTO"
                )
            SELECT * 
            FROM ranking_veiculos
                    WHERE "EQUIPAMENTO" = '{lista_veiculos[0]}'
            ORDER BY ranking;
                """

    #     query_ranking_veiculo = f"""
    #     WITH ranking_veiculos AS (
    #         SELECT 
    #             ROW_NUMBER() OVER (ORDER BY SUM("VALOR") ASC) AS ranking,
    #             "EQUIPAMENTO",  -- Veículo
    #             SUM("VALOR") AS total_pecas
    #         FROM pecas_gerais 
    #         WHERE 
    #             TO_DATE("DATA", 'DD/MM/YY') 
    #             BETWEEN TO_DATE('{data_inicio_str}', 'DD/MM/YYYY') 
    #                     AND TO_DATE('{data_fim_str}', 'DD/MM/YYYY')
    #             AND "GRUPO" NOT IN ('COMBUSTIVEIS E LUBRIFICANTES', 'Lubrificantes e Combustiveis Especiais')
    #         GROUP BY "EQUIPAMENTO"
    #         )
    #         SELECT * 
    #         FROM ranking_veiculos
    #             WHERE "EQUIPAMENTO" = '{lista_veiculos[0]}'
    #         ORDER BY ranking;
    # """
        query_contar_veiculos_testes= f"""
         WITH ranking_veiculos AS (
                SELECT
                    pg."EQUIPAMENTO",
                    ROW_NUMBER() OVER (ORDER BY SUM("VALOR") ASC) AS ranking,
                    SUM(pg."VALOR") as total_pecas
                FROM view_pecas_desconsiderando_combustivel pg
                LEFT JOIN mat_view_retrabalho_{min_dias}_dias_distinct AS od 
                ON pg."OS" = od."NUMERO DA OS"
                WHERE
                    1=1
                    {subquery_oficinas_str}
                    {subquery_secoes_str}
                    {subquery_os_str}
                    AND od."DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                    AND pg."GRUPO" NOT IN ('COMBUSTIVEIS E LUBRIFICANTES', 'Lubrificantes e Combustiveis Especiais')
                GROUP BY "EQUIPAMENTO"
            )
            SELECT COUNT(DISTINCT "EQUIPAMENTO") AS "QTD_VEICULOS"
            FROM ranking_veiculos;
    """
    #     query_quantidade_ranking_veiculos = f"""
    #     WITH ranking_veiculos AS (
    #         SELECT 
    #             ROW_NUMBER() OVER (ORDER BY SUM("VALOR") ASC) AS ranking,
    #             "EQUIPAMENTO",  -- Veículo
    #             SUM("VALOR") AS total_pecas
    #         FROM pecas_gerais 
    #         WHERE 
    #             TO_DATE("DATA", 'DD/MM/YY') 
    #             BETWEEN TO_DATE('{data_inicio_str}', 'DD/MM/YYYY') 
    #                     AND TO_DATE('{data_fim_str}', 'DD/MM/YYYY')
    #             AND "GRUPO" NOT IN ('COMBUSTIVEIS E LUBRIFICANTES', 'Lubrificantes e Combustiveis Especiais')
    #         GROUP BY "EQUIPAMENTO"
    #     )
    #     SELECT COUNT(DISTINCT "EQUIPAMENTO") AS "QTD_VEICULOS"
    #     FROM ranking_veiculos;

    # """
        try:
            df_detalhes = pd.read_sql(query_teste, self.dbEngine)
            

            df_detalhes["DT"] = pd.to_datetime(df_detalhes["DATA"], dayfirst=True)

            # Formatar a coluna "VALOR"
            
            #df_detalhes["VALOR_T"] = df_detalhes["VALOR"].apply(lambda x: f'R$ {x:,.2f}'.replace(",", "X").replace(".", ",").replace("X", "."))
            df_detalhes["VALOR"] = df_detalhes["VALOR"].astype(float).round(2)
        
            #num_meses = df_detalhes['DT'].dt.to_period('M').nunique() ## MESES DAS PEÇAS
            num_meses = len(pd.date_range(start=data_inicio_dt, end=data_fim, freq='MS'))

            numero_pecas_veiculos_total = int(df_detalhes['QUANTIDADE'].sum())
            valor_total_veiculos = df_detalhes['VALOR'].replace('[R$,]', '', regex=True).astype(float).sum().round(2)

            valor_total_veiculos_str = f"R${valor_total_veiculos:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

            df_quantidade_veiculos = pd.read_sql(query_contar_veiculos_testes, self.dbEngine)

            if not df_quantidade_veiculos.empty:
                qtd_veiculos = df_quantidade_veiculos.iloc[0]["QTD_VEICULOS"]
            else:
                qtd_veiculos = 0  # Ou outro valor padrão

            
            if len(lista_veiculos) <= 1:
                df_rk = pd.read_sql(query_teste_ranking, self.dbEngine)
                rk_n = df_rk.iloc[0]["ranking"]
                rk = f'{rk_n}°/{qtd_veiculos}'
            else:
                rk = f'0°'
            pecas_mes = round((numero_pecas_veiculos_total / num_meses), 2)
            valor_mes = round((valor_total_veiculos / num_meses), 2)
            valor_mes_str = f"R$ {valor_mes:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            

            df_detalhes_dict = df_detalhes.to_dict("records")
            return df_detalhes_dict, valor_total_veiculos_str, valor_mes_str, rk, numero_pecas_veiculos_total

        except Exception as e:
            print(f"Erro ao executar a consulta da tabela: {e}")
            return [], 0, 0, 0, 0
        
    def tabela_top_os_geral_retrabalho_fun(self, datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculo):
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
        subquery_veiculos_str = subquery_veiculos(lista_veiculo)

        inner_subquery_oficinas_str = subquery_oficinas(lista_oficinas, "main.")
        inner_subquery_secoes_str = subquery_secoes(lista_secaos, "main.")
        inner_subquery_os_str = subquery_os(lista_os, "main.")
        inner_subquery_veiculos_str = subquery_veiculos(lista_veiculo, "main.")

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
                "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                {subquery_oficinas_str}
                {subquery_secoes_str}
                {subquery_os_str}
                {subquery_veiculos_str}
            GROUP BY
                "DESCRICAO DA OFICINA",
                "DESCRICAO DA SECAO",
                "DESCRICAO DO SERVICO",
                "CODIGO DO VEICULO",
                "problem_no"
        ),
        os_problema AS (
            SELECT
                servico,
                COUNT(*) AS num_problema
            FROM
                normaliza_problema
            GROUP BY
                servico
        ),
        ind1 AS (
            SELECT
                main."DESCRICAO DO SERVICO",
                main."CODIGO DO VEICULO",
                COUNT(DISTINCT (main."NUMERO DA OS", main."DESCRICAO DO SERVICO")) AS "TOTAL_OS",
                SUM(CASE WHEN main.retrabalho THEN 1 ELSE 0 END) AS "TOTAL_RETRABALHO",
                SUM(CASE WHEN main.correcao THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO",
                SUM(CASE WHEN main.correcao_primeira THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO_PRIMEIRA",
                100 * ROUND(SUM(CASE WHEN main.retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
                100 * ROUND(SUM(CASE WHEN main.correcao THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO",
                100 * ROUND(SUM(CASE WHEN main.correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA",
                COUNT(main."COLABORADOR QUE EXECUTOU O SERVICO") AS "QUANTIDADE DE COLABORADORES"
            FROM
                mat_view_retrabalho_{min_dias}_dias main
            WHERE
                main."DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                {inner_subquery_oficinas_str}
                {inner_subquery_secoes_str}
                {inner_subquery_os_str}
                {inner_subquery_veiculos_str}
            GROUP BY
                main."DESCRICAO DO SERVICO",
                main."CODIGO DO VEICULO"
        ),
        ind2 AS (
            SELECT
                main."DESCRICAO DO SERVICO",
                main."CODIGO DO VEICULO",
                ROUND(SUM(pg."QUANTIDADE")) AS "QUANTIDADE DE PECAS",
                SUM(pg."VALOR") AS "VALOR"
            FROM
                mat_view_retrabalho_{min_dias}_dias_distinct main
            LEFT JOIN
                view_pecas_desconsiderando_combustivel pg
            ON 
                main."NUMERO DA OS" = pg."OS"
            WHERE
                main."DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                {inner_subquery_oficinas_str}
                {inner_subquery_secoes_str}
                {inner_subquery_os_str}
                {inner_subquery_veiculos_str}
            GROUP BY
                main."DESCRICAO DO SERVICO",
                main."CODIGO DO VEICULO"
        ),
        ind3 AS (
            WITH retrabalho_enumerado AS (
                SELECT DISTINCT 
                    "DESCRICAO DO SERVICO", 
                    "CODIGO DO VEICULO", 
                    "NUMERO DA OS", 
                    "DATA DO FECHAMENTO DA OS", 
                    "DESCRICAO DA SECAO",
                    "retrabalho"
                FROM mat_view_retrabalho_{min_dias}_dias
                WHERE 
                    "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                    AND retrabalho = true
                    {subquery_oficinas_str}
                    {subquery_secoes_str}
                    {subquery_os_str}
                    {subquery_veiculos_str}
            )
            SELECT 
                main."DESCRICAO DO SERVICO",
                main."CODIGO DO VEICULO",
                SUM(CASE WHEN main.retrabalho THEN pg."VALOR" ELSE 0 END) AS "TOTAL_GASTO_RETRABALHO"
            FROM retrabalho_enumerado main
            LEFT JOIN view_pecas_desconsiderando_combustivel pg
                ON main."NUMERO DA OS" = pg."OS"
            WHERE
                main."DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                {inner_subquery_oficinas_str}
                {inner_subquery_secoes_str}
                {inner_subquery_os_str}
                {inner_subquery_veiculos_str}
            GROUP BY
                main."DESCRICAO DO SERVICO",
                main."CODIGO DO VEICULO"
        )
        SELECT
            ind1."DESCRICAO DO SERVICO",
            ind1."CODIGO DO VEICULO",
            ind1."TOTAL_OS",
            ind1."TOTAL_RETRABALHO",
            ind1."TOTAL_CORRECAO",
            ind1."TOTAL_CORRECAO_PRIMEIRA",
            --ind1."TOTAL_PROBLEMA",
            ind1."PERC_RETRABALHO",
            ind1."PERC_CORRECAO",
            ind1."PERC_CORRECAO_PRIMEIRA",
            ind1."QUANTIDADE DE COLABORADORES",
            ind2."QUANTIDADE DE PECAS" AS "QUANTIDADE DE PECAS",
            ind2."VALOR" AS "VALOR",
            ind3."TOTAL_GASTO_RETRABALHO" AS "TOTAL_GASTO_RETRABALHO"
        FROM
            ind1
        LEFT JOIN
            ind2
        ON
            ind1."DESCRICAO DO SERVICO" = ind2."DESCRICAO DO SERVICO"
                AND ind1."CODIGO DO VEICULO" = ind2."CODIGO DO VEICULO"
        LEFT JOIN
            ind3
        ON
            ind1."DESCRICAO DO SERVICO" = ind3."DESCRICAO DO SERVICO"
                AND ind1."CODIGO DO VEICULO" = ind3."CODIGO DO VEICULO"
        ORDER BY
            ind1."PERC_RETRABALHO" DESC;

        """

        # Executa a query
        df = pd.read_sql(query, self.dbEngine)

        #df["REL_OS_PROBLEMA"] = round(df["TOTAL_OS"] / df["TOTAL_PROBLEMA"], 2)

        df["QUANTIDADE DE PECAS"] = df["QUANTIDADE DE PECAS"].fillna(0).astype(int)

        # Formatar "VALOR" para R$ no formato brasileiro e substituindo por 0 os valores nulos
        df["VALOR"] = df["VALOR"].fillna(0).astype(float).round(2)
        df["VALOR_"] = df["VALOR"].fillna(0).astype(float).round(2)
        df["VALOR"] = df["VALOR"].apply(lambda x: f'R$ {x:,.2f}'.replace(",", "X").replace(".", ",").replace("X", "."))

        df["TOTAL_GASTO_RETRABALHO"] = df["TOTAL_GASTO_RETRABALHO"].fillna(0).astype(float).round(2)
        df["TOTAL_GASTO_RETRABALHO_"] = df["TOTAL_GASTO_RETRABALHO"].fillna(0).astype(float).round(2)
        valor_retrabalho = df["TOTAL_GASTO_RETRABALHO"].sum().round(2)
        valor_retralho_str = f"R$ {valor_retrabalho:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        df["TOTAL_GASTO_RETRABALHO"] = df["TOTAL_GASTO_RETRABALHO"].apply(lambda x: f'R$ {x:,.2f}'.replace(",", "X").replace(".", ",").replace("X", "."))

        df_dict = df.to_dict("records")

        return df_dict, valor_retralho_str
    
    def ranking_retrabalho_veiculos_fun(self, datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
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
        subquery_veiculos_str = subquery_veiculos(lista_veiculos)
        

        query_ranking_retrabalho_correcao = f"""
                SELECT
                    "CODIGO DO VEICULO",
                    "DESCRICAO DO MODELO",
                    "TOTAL_RETRABALHO",
                    "TOTAL_CORRECAO",
                    "TOTAL_CORRECAO_PRIMEIRA",
                    "PERC_RETRABALHO",
                    "PERC_CORRECAO",
                    "PERC_CORRECAO_PRIMEIRA",
                    ranking_retrabalho,
                    ranking_correcao,
                    ranking_correcao_primeira
                FROM (
                    SELECT
                        "CODIGO DO VEICULO",
                        "DESCRICAO DO MODELO",
                        SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END) AS "TOTAL_RETRABALHO",
                        SUM(CASE WHEN correcao THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO",
                        SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO_PRIMEIRA",
                        100 * ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
                        100 * ROUND(SUM(CASE WHEN correcao THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO",
                        100 * ROUND(SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA",
                        DENSE_RANK() OVER (ORDER BY 100 * ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) ASC) AS ranking_retrabalho,
                        DENSE_RANK() OVER (ORDER BY 100 * ROUND(SUM(CASE WHEN correcao THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) ASC) AS ranking_correcao,
                        DENSE_RANK() OVER (ORDER BY 100 * ROUND(SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) desc)  ranking_correcao_primeira
                    FROM
                        mat_view_retrabalho_{min_dias}_dias
                    WHERE
                        "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                        {subquery_oficinas_str}
                        {subquery_secoes_str}
                        {subquery_os_str}
                        
                    GROUP BY
                        "CODIGO DO VEICULO", "DESCRICAO DO MODELO"
                ) subquery
                WHERE
                    ranking_retrabalho >= 1  -- Exemplo de filtro pelo ranking
                ORDER BY 
                    ranking_retrabalho, ranking_correcao, ranking_correcao_primeira;                
    """
        
        rk_retrabalho_geral = f'0°'
        rk_correcao_primeira_geral = f'0°'
        
        rk_retrabalho_modelo = f'0°'
        rk_correcao_primeira_modelo = f'0°'

        if len(lista_veiculos) <= 1:
            df = pd.read_sql(query_ranking_retrabalho_correcao, self.dbEngine)
            df = df.rename(columns={
                "PERC_RETRABALHO": "RETRABALHO",
                "PERC_CORRECAO_PRIMEIRA": "CORRECAO_PRIMEIRA"
            })
            df_veiculo = df.loc[df["CODIGO DO VEICULO"] == lista_veiculos[0]]

            if len(df_veiculo) >= 1:
                contagem_ranking_geral = len(df)

                rk_n_retrabalho = df_veiculo.iloc[0]["ranking_retrabalho"]
                retra = df_veiculo.iloc[0]["RETRABALHO"]
                rk_retrabalho_geral = f'{rk_n_retrabalho}°/{contagem_ranking_geral}'

                rk_n_correcao_primeira = df_veiculo.iloc[0]["ranking_correcao_primeira"]
                rk_correcao_primeira_geral = f'{rk_n_correcao_primeira}°/{contagem_ranking_geral}'

            ########################################################### POR MODELO AGORA
                lista_modelos = df_veiculo["DESCRICAO DO MODELO"].dropna().unique().tolist()
                sub_query_modelos_str = subquery_modelos_veiculos(lista_modelos)

                query_ranking_retrabalho_correcao_modelos = f"""
                    SELECT
                        "CODIGO DO VEICULO",
                        "DESCRICAO DO MODELO",
                        "TOTAL_RETRABALHO",
                        "TOTAL_CORRECAO",
                        "TOTAL_CORRECAO_PRIMEIRA",
                        "PERC_RETRABALHO",
                        "PERC_CORRECAO",
                        "PERC_CORRECAO_PRIMEIRA",
                        ranking_retrabalho,
                        ranking_correcao,
                        ranking_correcao_primeira
                    FROM (
                        SELECT
                            "CODIGO DO VEICULO",
                            "DESCRICAO DO MODELO",
                            SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END) AS "TOTAL_RETRABALHO",
                            SUM(CASE WHEN correcao THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO",
                            SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO_PRIMEIRA",
                            100 * ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
                            100 * ROUND(SUM(CASE WHEN correcao THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO",
                            100 * ROUND(SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA",
                            DENSE_RANK() OVER (ORDER BY 100 * ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) ASC) AS ranking_retrabalho,
                            DENSE_RANK() OVER (ORDER BY 100 * ROUND(SUM(CASE WHEN correcao THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) ASC) AS ranking_correcao,
                            DENSE_RANK() OVER (ORDER BY 100 * ROUND(SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) desc)  ranking_correcao_primeira
                        FROM
                            mat_view_retrabalho_{min_dias}_dias
                        WHERE
                            "DATA DO FECHAMENTO DA OS" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                            {subquery_oficinas_str}
                            {subquery_secoes_str}
                            {subquery_os_str}
                            {sub_query_modelos_str}
                        GROUP BY
                            "CODIGO DO VEICULO", "DESCRICAO DO MODELO"
                    ) subquery
                    WHERE
                        ranking_retrabalho >= 1  -- Exemplo de filtro pelo ranking
                    ORDER BY 
                        ranking_retrabalho, ranking_correcao, ranking_correcao_primeira;                
                    """

                df_modelos = pd.read_sql(query_ranking_retrabalho_correcao_modelos, self.dbEngine)
                df_modelos = df_modelos.rename(columns={
                    "PERC_RETRABALHO": "RETRABALHO",
                    "PERC_CORRECAO_PRIMEIRA": "CORRECAO_PRIMEIRA"
                })
                contagem_ranking_modelos = len(df_modelos)
                df_veiculo_modelo = df_modelos.loc[df_modelos["CODIGO DO VEICULO"] == lista_veiculos[0]]

                rk_n_retrabalho_modelo = df_veiculo_modelo.iloc[0]["ranking_retrabalho"]
                rk_retrabalho_modelo = f'{rk_n_retrabalho_modelo}°/{contagem_ranking_modelos}'

                rk_n_correcao_primeira_modelos = df_veiculo_modelo.iloc[0]["ranking_correcao_primeira"]
                rk_correcao_primeira_modelo = f'{rk_n_correcao_primeira_modelos}°/{contagem_ranking_modelos}'

        return rk_retrabalho_geral, rk_correcao_primeira_geral, rk_retrabalho_modelo, rk_correcao_primeira_modelo
    
    def tabela_pecas_por_descricao_fun(self, datas, min_dias, lista_veiculos):
        data_inicio_str = datas[0]
 
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)
 
        data_inicio_dt = pd.to_datetime(data_inicio_str)
        data_inicio_str = data_inicio_dt.strftime("%d/%m/%Y")
        data_fim_str = data_fim.strftime("%d/%m/%Y")

        if data_inicio_str is None:
            return go.Figure()  # Ou algum valor padrão válido
        if data_fim_str is None:
            return go.Figure()  # Ou algum valor padrão válido
        
        subquery_veiculos_str = subquery_equipamentos(lista_veiculos)
 
        query_detalhes = f"""
        SELECT
            od."DESCRICAO DO SERVICO" AS "DESCRIÇÃO DE SERVIÇO",
            COUNT(DISTINCT pg."OS") AS "QUANTIDADE DE OS'S",
            SUM(pg."QUANTIDADE") AS "QUANTIDADE DE PEÇAS",
            pg."MODELO",
            SUM(pg."VALOR") AS "VALOR"
            FROM pecas_gerais pg
            LEFT JOIN mat_view_retrabalho_{min_dias}_dias_distinct AS od 
        ON pg."OS" = od."NUMERO DA OS"
        WHERE
            TO_DATE(pg."DATA", 'DD/MM/YY')
                BETWEEN TO_DATE('{data_inicio_str}', 'DD/MM/YYYY')
                    AND TO_DATE('{data_fim_str}', 'DD/MM/YYYY')
            AND pg."GRUPO" NOT IN ('COMBUSTIVEIS E LUBRIFICANTES', 'Lubrificantes e Combustiveis Especiais')
            {subquery_veiculos_str}
        GROUP BY
            od."DESCRICAO DO SERVICO",
            pg."MODELO"
        ORDER BY
            COUNT(DISTINCT pg."OS") DESC;
        """
       
        try:
            df_detalhes = pd.read_sql(query_detalhes, self.dbEngine)
 
            # Converter VALOR para float e formatar como moeda (R$)
            
            df_detalhes["VALOR_T"] = df_detalhes["VALOR"].astype(float).apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            df_detalhes["VALOR"] = df_detalhes["VALOR"].astype(float)

            # Número de meses distintos
            num_meses = len(datas)  
 
            # Cálculo de totais
            numero_pecas_veiculos_total = int(df_detalhes['QUANTIDADE DE PEÇAS'].sum())
            valor_total_veiculos = df_detalhes['VALOR_T'].str.replace("R$ ", "").str.replace(".", "").str.replace(",", ".").astype(float).sum().round(2)
 
            # Formatação dos valores totais
            valor_total_veiculos_str = f"R$ {valor_total_veiculos:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            pecas_mes = round((numero_pecas_veiculos_total / num_meses), 2)
            valor_mes = round((valor_total_veiculos / num_meses), 2)
            valor_mes_str = f"R$ {valor_mes:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
 
            # Converter para dicionário
            df_detalhes_dict = df_detalhes.to_dict("records")

            # Seleciona a coluna "DESCRIÇÃO DE SERVIÇO" e obtém os valores únicos
            descricao_servico_unicas = df_detalhes["DESCRIÇÃO DE SERVIÇO"].unique()

            # Converte para uma lista
            descricao_servico_unicas_lista = descricao_servico_unicas.tolist()

            return df_detalhes_dict, valor_total_veiculos_str, valor_mes_str, descricao_servico_unicas_lista
 
        except Exception as e:
            print(f"Erro ao executar a consulta da tabela: {e}")
            return [], "R$ 0,00", "R$ 0,00",[]
        
    def tabela_ranking_pecas_fun(self, datas, min_dias, lista_oficinas, lista_secoes, lista_os, lista_veiculos):
        subquery_oficinas_str = subquery_oficinas(lista_oficinas, "od.")
        subquery_secoes_str = subquery_secoes(lista_secoes, "od.")
        subquery_os_str = subquery_os(lista_os, "od.")
        #subquery_veiculos_str = subquery_equipamentos(lista_veiculos, "pg.")
        subquery_vei_str = subquery_veiculos(lista_veiculos)
        
        data_inicio_str = datas[0]
        data_fim = pd.to_datetime(datas[1]) - pd.DateOffset(days=min_dias + 1)
        data_inicio_str = pd.to_datetime(data_inicio_str).strftime("%d/%m/%Y")
        data_fim_str = data_fim.strftime("%d/%m/%Y")

        try:
            # 1. Buscar APENAS um modelo associado aos veículos selecionados
            query_modelo = f"""
            SELECT DISTINCT 
                "DESCRICAO DO MODELO" AS "MODELO"
            FROM mat_view_retrabalho_{min_dias}_dias_distinct
            WHERE 
                1=1
                {subquery_vei_str}
            LIMIT 1;
            """

            df_modelo = pd.read_sql(query_modelo, self.dbEngine)
            modelo_unico = df_modelo["MODELO"].iloc[0].strip() if not df_modelo.empty else "N/A"
            subquery_modelos_veiculos_str = subquery_modelos_pecas([modelo_unico],"pg.")


            query_ranking_modelo = f"""
            WITH ranking_veiculos AS (
                SELECT 
                    pg."EQUIPAMENTO" AS "EQUIPAMENTO",
                    SUM(pg."VALOR") AS "VALOR"
                FROM view_pecas_desconsiderando_combustivel pg
                LEFT JOIN mat_view_retrabalho_{min_dias}_dias_distinct AS od 
                    ON pg."OS" = od."NUMERO DA OS"
                WHERE 1=1
                    AND TO_DATE(od."DATA DO FECHAMENTO DA OS", 'YYYY/MM/DD')
                        BETWEEN TO_DATE('{data_inicio_str}', 'DD/MM/YYYY')
                        AND TO_DATE('{data_fim_str}', 'DD/MM/YYYY')
                        {subquery_oficinas_str}
                        {subquery_secoes_str}
                        {subquery_os_str}
                        {subquery_modelos_veiculos_str}
                GROUP BY pg."EQUIPAMENTO"
            ),
            ranking_filtrado AS (
                SELECT *, 
                    ROW_NUMBER() OVER (ORDER BY "VALOR" ASC) AS "POSICAO"
                FROM ranking_veiculos
            )
            SELECT "POSICAO", "EQUIPAMENTO", "VALOR"
            FROM ranking_filtrado
            WHERE 1=1
            ORDER BY "POSICAO";
            """
            rk_valor_modelo = f'0°'
            if len(lista_veiculos) > 1 or len(lista_veiculos) == 0:
                return rk_valor_modelo  
            if len(lista_veiculos) == 1:
                df = pd.read_sql(query_ranking_modelo, self.dbEngine)
                equipamento_alvo = str(lista_veiculos[0]).strip()
                df_veiculo = df[df["EQUIPAMENTO"].astype(str).str.contains(equipamento_alvo, case=False, na=False)]
                if len(df_veiculo) == 1:
                    contagem_ranking_geral = len(df)
                    rk_n_valor_modelo = df_veiculo.iloc[0]["POSICAO"]
                    rk_valor_modelo = f'{rk_n_valor_modelo}°/{contagem_ranking_geral}'
            return rk_valor_modelo

        except Exception as e:
            print(f"Erro ao executar a consulta do ranking de peças por modelo: {e}")
            return []


