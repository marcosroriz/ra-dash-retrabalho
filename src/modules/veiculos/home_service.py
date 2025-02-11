 #Classe que centraliza os serviços para mostrar na página home

# Imports básicos
import re
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Imports auxiliares
from modules.sql_utils import subquery_oficinas, subquery_secoes, subquery_os, subquery_veiculos, subquery_modelos_veiculos, subquery_equipamentos
from modules.veiculos.helps import HelpsVeiculos

# Classe do serviço
class HomeServiceVeiculo:
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
        lista_todos_veiculos = [{"VEICULO": "TODAS", "MODELO": "TODOS OS VEÍCULOS"}] + df_lista_veiculos.to_dict(orient="records")

        return lista_todos_veiculos

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
                "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
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

        #print(df.head())

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


        query = f"""
            SELECT 
                "CODIGO DO VEICULO",
                DATE_TRUNC('month', "DATA DE FECHAMENTO DO SERVICO"::timestamp) AS "MÊS",
                COUNT("NUMERO DA OS") AS "QUANTIDADE_DE_OS",
                "DESCRICAO DO SERVICO",
                "DESCRICAO DO MODELO",
                COUNT(DISTINCT "COLABORADOR QUE EXECUTOU O SERVICO") AS "QTD_COLABORADORES"
            FROM
                os_dados
            WHERE
                "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                {subquery_oficinas_str}
                {subquery_secoes_str}
                {subquery_os_str}
                {subquery_veiculos_str}
            GROUP BY
                "CODIGO DO VEICULO",
                DATE_TRUNC('month', "DATA DE FECHAMENTO DO SERVICO"::timestamp),
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
                os_dados
            WHERE 
                "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                {subquery_oficinas_str}
                {subquery_secoes_str}
                {subquery_os_str}
                {subquery_veiculos_str};
        """

        query_descobrir_problemas = f"""
            SELECT
                SUM(CASE WHEN correcao THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO"
            FROM
                mat_view_retrabalho_{min_dias}_dias
            WHERE
                "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                {subquery_oficinas_str}
                {subquery_secoes_str}
                {subquery_os_str}
                {subquery_veiculos_str};
        """

        df_problemas = pd.read_sql(query_descobrir_problemas, self.dbEngine)
        total_problemas = df_problemas["TOTAL_CORRECAO"].iloc[0]

        query_media = f"""
            WITH os_count AS (
                SELECT 
                    "CODIGO DO VEICULO",
                    DATE_TRUNC('month', "DATA DE FECHAMENTO DO SERVICO"::timestamp) AS "MÊS",
                    COUNT("NUMERO DA OS") AS "QUANTIDADE_DE_OS",
                    COUNT(DISTINCT "DESCRICAO DO SERVICO") AS "QUANTIDADE_DE_DESCRICOES_DISTINTAS"
                FROM os_dados
                WHERE 
                "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                {subquery_oficinas_str}
                {subquery_secoes_str}
                {subquery_os_str}

                GROUP BY
                    "CODIGO DO VEICULO",
                    DATE_TRUNC('month', "DATA DE FECHAMENTO DO SERVICO"::timestamp)
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

        subquery_modelos_str = subquery_modelos_veiculos(lista_modelos)


        query_media_modelos = f"""
            WITH os_count AS (
                SELECT 
                    "CODIGO DO VEICULO",
                    DATE_TRUNC('month', "DATA DE FECHAMENTO DO SERVICO"::timestamp) AS "MÊS",
                    COUNT("NUMERO DA OS") AS "QUANTIDADE_DE_OS",
                    COUNT(DISTINCT "DESCRICAO DO SERVICO") AS "QUANTIDADE_DE_DESCRICOES_DISTINTAS",
                    "DESCRICAO DO MODELO"
                FROM os_dados
                WHERE 
                "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                {subquery_oficinas_str}
                {subquery_secoes_str}
                {subquery_os_str}
                {subquery_modelos_str}

                GROUP BY
                    "CODIGO DO VEICULO",
                    DATE_TRUNC('month', "DATA DE FECHAMENTO DO SERVICO"::timestamp),
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

        #print(df_media_modelos_str.head())

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
        os_diferentes = int(df_unico['QUANTIDADE_DE_OS'].sum())
        os_totais_veiculo = int(df_soma_mes_veiculos['QUANTIDADE_DE_OS'].sum())
        
        if len(df_soma_mes_veiculos) >= 1:
            os_problema = os_totais_veiculo/total_problemas
            os_problema = round(os_problema, 2)
        else:
            os_problema = 0

        return os_diferentes, mecanicos_diferentes, os_totais_veiculo, os_problema, df_soma_mes, df_os_unicas
    
    def pecas_trocadas_por_mes_fun(self, datas, equipamentos):
            # Converte equipamentos para formato compatível com SQL (lista formatada)
        equipamentos_sql = ", ".join(f"'{equip}'" for equip in equipamentos)

        # Datas
        data_inicio_str = datas[0]
        data_fim_str = datas[1]

        # Query para buscar peças trocadas por mês para os veículos selecionados
        query_veiculos = f"""
        SELECT 
            to_char("DATA"::DATE, 'YYYY-MM') AS year_month,
            "EQUIPAMENTO",
            ROUND(SUM("VALOR"), 2) AS total_pecas
        FROM 
            pecas_gerais
        WHERE 
            "EQUIPAMENTO" IN ({equipamentos_sql})
            AND "DATA"::DATE BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            AND "GRUPO" NOT IN ('COMBUSTIVEIS E LUBRIFICANTES', 'Lubrificantes e Combustiveis Especiais')
        GROUP BY 
            year_month, "EQUIPAMENTO"
        ORDER BY 
            year_month;
        """

        # Query para calcular a média geral de peças trocadas por mês
        query_media_geral = f"""
        SELECT 
            to_char("DATA"::DATE, 'YYYY-MM') AS year_month,
            ROUND(SUM("VALOR") / COUNT(DISTINCT "EQUIPAMENTO"), 2) AS media_geral
        FROM 
            pecas_gerais
        WHERE 
            "DATA"::DATE BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            AND "GRUPO" NOT IN ('COMBUSTIVEIS E LUBRIFICANTES', 'Lubrificantes e Combustiveis Especiais')
        GROUP BY 
            year_month
        ORDER BY 
            year_month;
        """

        try:
            # Executa a query dos veículos
            df_veiculos = pd.read_sql(query_veiculos, self.dbEngine)
            # Executa a query da média geral
            df_media_geral = pd.read_sql(query_media_geral, self.dbEngine)

            # Verifica se há dados
            if df_veiculos.empty and df_media_geral.empty:
                return go.Figure().update_layout(
                    title_text="Nenhum dado disponível para o equipamento e intervalo selecionados."
                )

            # Converte a coluna de datas para datetime
            df_veiculos["year_month_dt"] = pd.to_datetime(df_veiculos["year_month"], format="%Y-%m", errors="coerce")
            df_media_geral["year_month_dt"] = pd.to_datetime(df_media_geral["year_month"], format="%Y-%m", errors="coerce")

            return df_veiculos, df_media_geral
        except Exception as e:
            print(f"Erro ao executar as consultas: {e}")
            return go.Figure().update_layout(title_text=f"Erro ao carregar os dados: {e}")
        
    def tabela_pecas_fun(self, datas, min_dias, lista_veiculos):
            # Datas
        data_inicio_str = datas[0]
        
        # Remove min_dias antes para evitar que a última OS não seja retrabalho
        data_fim = pd.to_datetime(datas[1])
        data_fim = data_fim - pd.DateOffset(days=min_dias + 1)

        data_inicio_dt = pd.to_datetime(data_inicio_str)
        data_inicio_str = data_inicio_dt.strftime("%d/%m/%Y")
        data_fim_str = data_fim.strftime("%d/%m/%Y")

        subquery_veiculos_str = subquery_equipamentos(lista_veiculos)

        query_detalhes = f"""
        SELECT "OS", 
            "EQUIPAMENTO", 
            "MODELO", 
            "PRODUTO", 
            "QUANTIDADE", 
            "VALOR", 
            "DATA"
        FROM pecas_gerais 
            WHERE 
                TO_DATE("DATA", 'DD/MM/YY') 
                    BETWEEN TO_DATE('{data_inicio_str}', 'DD/MM/YYYY') 
                        AND TO_DATE('{data_fim_str}', 'DD/MM/YYYY')
                AND "GRUPO" NOT IN ('COMBUSTIVEIS E LUBRIFICANTES', 'Lubrificantes e Combustiveis Especiais')
                {subquery_veiculos_str}
        """
        query_ranking_veiculo = f"""
        WITH ranking_veiculos AS (
            SELECT 
                ROW_NUMBER() OVER (ORDER BY SUM("VALOR") ASC) AS ranking,
                "EQUIPAMENTO",  -- Veículo
                SUM("VALOR") AS total_pecas
            FROM pecas_gerais 
            WHERE 
                TO_DATE("DATA", 'DD/MM/YY') 
                BETWEEN TO_DATE('{data_inicio_str}', 'DD/MM/YYYY') 
                        AND TO_DATE('{data_fim_str}', 'DD/MM/YYYY')
                AND "GRUPO" NOT IN ('COMBUSTIVEIS E LUBRIFICANTES', 'Lubrificantes e Combustiveis Especiais')
            GROUP BY "EQUIPAMENTO"
            )
            SELECT * 
            FROM ranking_veiculos
                WHERE "EQUIPAMENTO" = '{lista_veiculos[0]}'
            ORDER BY ranking;
    """
        try:
            df_detalhes = pd.read_sql(query_detalhes, self.dbEngine)

            df_detalhes["DT"] = pd.to_datetime(df_detalhes["DATA"], dayfirst=True)

            # Formatar a coluna "VALOR"
            df_detalhes["VALOR"] = df_detalhes["VALOR"].astype(float) 

            num_meses = df_detalhes['DT'].dt.to_period('M').nunique()

            numero_pecas_veiculos_total = int(df_detalhes['QUANTIDADE'].sum())
            valor_total_veiculos = df_detalhes['VALOR'].replace('[R$,]', '', regex=True).astype(float).sum().round(2)

            valor_total_veiculos_str = f"R${valor_total_veiculos:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

            if len(lista_veiculos) <= 1:
                df_rk = pd.read_sql(query_ranking_veiculo, self.dbEngine)
                rk_n = df_rk.iloc[0]["ranking"]
                rk = f'{rk_n}°'
            else:
                rk = f'0°'

            pecas_mes = round((numero_pecas_veiculos_total / num_meses), 2)
            valor_mes = round((valor_total_veiculos / num_meses), 2)
            valor_mes_str = f"R$ {valor_mes:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

            df_detalhes_dict = df_detalhes.to_dict("records")
            return df_detalhes_dict, valor_total_veiculos_str, valor_mes_str, rk

        except Exception as e:
            print(f"Erro ao executar a consulta da tabela: {e}")
            return [], 0, 0, 0
        
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
                "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
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
        )
        SELECT
            main."DESCRICAO DA OFICINA",
            main."DESCRICAO DA SECAO",
            main."DESCRICAO DO SERVICO",
            COUNT(*) AS "TOTAL_OS",
            SUM(CASE WHEN main.retrabalho THEN 1 ELSE 0 END) AS "TOTAL_RETRABALHO",
            SUM(CASE WHEN main.correcao THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO",
            SUM(CASE WHEN main.correcao_primeira THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO_PRIMEIRA",
            100 * ROUND(SUM(CASE WHEN main.retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
            100 * ROUND(SUM(CASE WHEN main.correcao THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO",
            100 * ROUND(SUM(CASE WHEN main.correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA",
            COALESCE(op.num_problema, 0) AS "TOTAL_PROBLEMA",
            SUM(pg."QUANTIDADE") as "QUANTIDADE DE PECAS" ,
            COUNT(main."COLABORADOR QUE EXECUTOU O SERVICO") as "QUANTIDADE DE COLABORADORES" 
        FROM
            mat_view_retrabalho_{min_dias}_dias main
        LEFT JOIN
            os_problema op
        ON
            main."DESCRICAO DA OFICINA" = op."DESCRICAO DA OFICINA"
            AND main."DESCRICAO DA SECAO" = op."DESCRICAO DA SECAO"
            AND main."DESCRICAO DO SERVICO" = op.servico
        LEFT JOIN
            PECAS_GERAIS pg
        ON 
            main."NUMERO DA OS" = pg."OS"
        WHERE
            main."DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            {inner_subquery_oficinas_str}
            {inner_subquery_secoes_str}
            {inner_subquery_os_str}
            {inner_subquery_veiculos_str}
        GROUP BY
            main."DESCRICAO DA OFICINA",
            main."DESCRICAO DA SECAO",
            main."DESCRICAO DO SERVICO",
            op.num_problema
        ORDER BY
            "PERC_RETRABALHO" DESC;
        """

        # Executa a query
        df = pd.read_sql(query, self.dbEngine)

        df["REL_OS_PROBLEMA"] = round(df["TOTAL_OS"] / df["TOTAL_PROBLEMA"], 2)

        df_dict = df.to_dict("records")

        return df_dict
    
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
                        "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
                        {subquery_oficinas_str}
                        {subquery_secoes_str}
                        {subquery_os_str}
                        
                    GROUP BY
                        "CODIGO DO VEICULO", "DESCRICAO DO MODELO"
                ) subquery
                WHERE
                    ranking_retrabalho >= 1  -- Exemplo de filtro pelo ranking
                    --{subquery_veiculos_str}
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
                            "DATA DE FECHAMENTO DO SERVICO" BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
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