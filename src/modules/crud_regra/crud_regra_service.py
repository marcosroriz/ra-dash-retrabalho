#!/usr/bin/env python
# coding: utf-8

# Classe que centraliza os serviços para CRUD de regras

# Imports básicos
import re
import pandas as pd
import numpy as np

# Imports BD
import sqlalchemy
from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql import text

# Imports auxiliares
from modules.sql_utils import subquery_oficinas, subquery_secoes, subquery_os, subquery_modelos
from modules.entities_utils import get_mecanicos
from modules.service_utils import definir_status, definir_status_label, definir_emoji_status


# Classe do serviço
class CRUDRegraService:
    def __init__(self, dbEngine):
        self.dbEngine = dbEngine

    def get_regra_by_id(self, id_regra):
        """Função para obter uma regra de monitoramento pelo ID"""

        # Query
        query = f"""
            SELECT * FROM regra_monitoramento_os WHERE id = {id_regra}
            ORDER BY nome
        """

        # Executa a query
        df = pd.read_sql(query, self.dbEngine)

        return df

    def get_todas_regras(self):
        """Função para obter todas as regras de monitoramento"""

        # Query
        query = """
            SELECT * FROM regra_monitoramento_os
            ORDER BY nome
        """

        # Executa a query
        df = pd.read_sql(query, self.dbEngine)

        return df

    def apagar_regra(self, id_regra):
        """Função para apagar uma regra de monitoramento"""

        # Query
        query = f"""
            DELETE FROM regra_monitoramento_os WHERE id = {id_regra}
        """

        try:
            # Executa a query
            with self.dbEngine.begin() as conn:
                conn.execute(text(query))

            return True
        except Exception as e:
            print(f"Erro ao apagar regra: {e}")
            return False

    def criar_regra_monitoramento(self, payload):
        """Função para criar uma regra de monitoramento"""
        table = sqlalchemy.Table("regra_monitoramento_os", sqlalchemy.MetaData(), autoload_with=self.dbEngine)

        try:
            with self.dbEngine.begin() as conn:
                stmt = insert(table).values(payload)
                conn.execute(stmt)

            return True
        except Exception as e:
            print(f"Erro ao criar regra de monitoramento: {e}")
            return False

    def atualizar_regra_monitoramento(self, id_regra, payload):
        """Função para atualizar uma regra de monitoramento"""
        table = sqlalchemy.Table("regra_monitoramento_os", sqlalchemy.MetaData(), autoload_with=self.dbEngine)

        try:
            with self.dbEngine.begin() as conn:
                stmt = update(table).where(table.c.id == id_regra).values(payload)
                conn.execute(stmt)

            return True
        except Exception as e:
            print(f"Erro ao atualizar regra de monitoramento: {e}")
            return False
        

    def get_ultima_data_regra(self, id_regra):
        """Função para obter a última data de uma regra de monitoramento"""
        query = f"""
            SELECT id_regra, MAX(dia) AS ultimo_dia
            FROM relatorio_regra_monitoramento_os
            WHERE id_regra = {id_regra}
            GROUP BY id_regra
        """
        df = pd.read_sql(query, self.dbEngine)
        return df

    def subquery_checklist(self, checklist_alvo, prefix=""):
        query = ""
        query_parts = [f"""{prefix}"{alvo}" = TRUE""" for alvo in checklist_alvo]

        if query_parts:
            query_or = " OR ".join(query_parts)
            query = f"AND ({query_or})"

        return query

    def get_sintese_geral(self, data_periodo_regra, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os):
        """Função para obter a síntese geral (que será usado para o gráfico de pizza)"""

        # Subqueries
        subquery_modelos_str = subquery_modelos(lista_modelos, termo_all="TODOS")
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
                SUM(CASE WHEN nova_os_com_retrabalho_anterior THEN 1 ELSE 0 END) AS "TOTAL_NOVA_OS_COM_RETRABALHO_ANTERIOR",
                SUM(CASE WHEN nova_os_sem_retrabalho_anterior THEN 1 ELSE 0 END) AS "TOTAL_NOVA_OS_SEM_RETRABALHO_ANTERIOR",
                100 * ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
                100 * ROUND(SUM(CASE WHEN correcao THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO",
                100 * ROUND(SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA",
                100 * ROUND(SUM(CASE WHEN nova_os_com_retrabalho_anterior THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_NOVA_OS_COM_RETRABALHO_ANTERIOR",
                100 * ROUND(SUM(CASE WHEN nova_os_sem_retrabalho_anterior THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_NOVA_OS_SEM_RETRABALHO_ANTERIOR"
            FROM
                mat_view_retrabalho_{min_dias}_dias_distinct
            WHERE
                "DATA DA ABERTURA DA OS"::timestamp BETWEEN CURRENT_DATE - INTERVAL '{data_periodo_regra} days' AND CURRENT_DATE
                {subquery_modelos_str}
                {subquery_oficinas_str}
                {subquery_secoes_str}
                {subquery_os_str}
        """

        # Executa a query
        df = pd.read_sql(query, self.dbEngine)

        # Calcula o total de correções tardia
        df["TOTAL_CORRECAO_TARDIA"] = df["TOTAL_CORRECAO"] - df["TOTAL_CORRECAO_PRIMEIRA"]

        return df

    def get_sintese_geral_filtro_periodo(
        self, data_periodo_regra, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os, checklist_alvo
    ):
        """Função para obter a síntese geral (que será usado para o gráfico de pizza)"""

        # Subqueries
        subquery_modelos_str = subquery_modelos(lista_modelos, termo_all="TODOS")
        subquery_oficinas_str = subquery_oficinas(lista_oficinas)
        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)

        # Subquery checklist
        subquery_checklist_str = self.subquery_checklist(checklist_alvo)

        # Query
        query = f"""
            SELECT
                COUNT(*) AS "TOTAL_NUM_OS",
                SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END) AS "TOTAL_RETRABALHO",
                SUM(CASE WHEN correcao THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO",
                SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END) AS "TOTAL_CORRECAO_PRIMEIRA",
                SUM(CASE WHEN nova_os_com_retrabalho_anterior THEN 1 ELSE 0 END) AS "TOTAL_NOVA_OS_COM_RETRABALHO_ANTERIOR",
                SUM(CASE WHEN nova_os_sem_retrabalho_anterior THEN 1 ELSE 0 END) AS "TOTAL_NOVA_OS_SEM_RETRABALHO_ANTERIOR",
                100 * ROUND(SUM(CASE WHEN retrabalho THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_RETRABALHO",
                100 * ROUND(SUM(CASE WHEN correcao THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO",
                100 * ROUND(SUM(CASE WHEN correcao_primeira THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_CORRECAO_PRIMEIRA",
                100 * ROUND(SUM(CASE WHEN nova_os_com_retrabalho_anterior THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_NOVA_OS_COM_RETRABALHO_ANTERIOR",
                100 * ROUND(SUM(CASE WHEN nova_os_sem_retrabalho_anterior THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)::NUMERIC, 4) AS "PERC_NOVA_OS_SEM_RETRABALHO_ANTERIOR"
            FROM
                mat_view_retrabalho_{min_dias}_dias_distinct
            WHERE
                "DATA DA ABERTURA DA OS"::timestamp BETWEEN CURRENT_DATE - INTERVAL '{data_periodo_regra} days' AND CURRENT_DATE
                {subquery_modelos_str}
                {subquery_oficinas_str}
                {subquery_secoes_str}
                {subquery_os_str}
                {subquery_checklist_str}
        """

        # Executa a query
        df = pd.read_sql(query, self.dbEngine)

        return df

    def get_previa_os_regra(
        self, data_periodo_regra, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os, checklist_alvo
    ):
        """Função para obter a prévia das OS detectadas pela regra (que será usado para envio do e-mail / WhatsApp)"""

        # Subqueries
        subquery_modelos_str = subquery_modelos(lista_modelos, termo_all="TODOS")
        subquery_oficinas_str = subquery_oficinas(lista_oficinas)
        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)
        subquery_checklist_str = self.subquery_checklist(checklist_alvo)

        # Query
        query = f"""
            SELECT
                *
            FROM
                mat_view_retrabalho_{min_dias}_dias_distinct
            WHERE
                "DATA DA ABERTURA DA OS"::timestamp BETWEEN CURRENT_DATE - INTERVAL '{data_periodo_regra} days' AND CURRENT_DATE
                {subquery_modelos_str}
                {subquery_oficinas_str}
                {subquery_secoes_str}
                {subquery_os_str}
                {subquery_checklist_str}
        """

        # Executa a query
        df = pd.read_sql(query, self.dbEngine)

        # Aplica a função para definir o status de cada OS
        df["status_os"] = df.apply(definir_status, axis=1)
        df["status_os_label"] = df.apply(definir_status_label, axis=1)
        df["status_os_emoji"] = df.apply(definir_emoji_status, axis=1)

        return df

    def get_previa_os_regra_detalhada(
        self, data_periodo_regra, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os, checklist_alvo
    ):
        """Função para obter a prévia das OS detectadas pela regra (que será usado para envio do e-mail / WhatsApp)"""

        # Subqueries
        subquery_modelos_str = subquery_modelos(lista_modelos, termo_all="TODOS")
        subquery_oficinas_str = subquery_oficinas(lista_oficinas)
        subquery_secoes_str = subquery_secoes(lista_secaos)
        subquery_os_str = subquery_os(lista_os)
        subquery_checklist_str = self.subquery_checklist(checklist_alvo)

        # Query
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
                to_timestamp(pg."DATA", 'DD/MM/YYYY') BETWEEN CURRENT_DATE - INTERVAL '{data_periodo_regra} days' AND CURRENT_DATE
            GROUP BY 
                pg."OS"
        ),
        os_avaliadas AS (
            SELECT
                *
            FROM
                mat_view_retrabalho_{min_dias}_dias_distinct m
            LEFT JOIN 
                os_dados_classificacao odc
            ON 
                m."KEY_HASH" = odc."KEY_HASH" 
            WHERE
                "DATA DA ABERTURA DA OS"::timestamp BETWEEN CURRENT_DATE - INTERVAL '{data_periodo_regra} days' AND CURRENT_DATE
                {subquery_modelos_str}
                {subquery_oficinas_str}
                {subquery_secoes_str}
                {subquery_os_str}
                {subquery_checklist_str}
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

        # Executa a query
        df = pd.read_sql(query, self.dbEngine)

        # Preenche valores nulos
        df["total_valor"] = df["total_valor"].fillna(0)
        df["pecas_valor_str"] = df["pecas_valor_str"].fillna("0")
        df["pecas_trocadas_str"] = df["pecas_trocadas_str"].fillna("Nenhuma / Não inserida ainda")
        df["nome_colaborador"] = df["nome_colaborador"].fillna("Não inserido ainda")
        df["nome_colaborador"] = df["nome_colaborador"].apply(lambda x: re.sub(r"(?<!^)([A-Z])", r" \1", x)    )

        # Campos da LLM
        df["SCORE_SYMPTOMS_TEXT_QUALITY"] = df["SCORE_SYMPTOMS_TEXT_QUALITY"].fillna("-")
        df["SCORE_SOLUTION_TEXT_QUALITY"] = df["SCORE_SOLUTION_TEXT_QUALITY"].fillna("-")
        df["WHY_SOLUTION_IS_PROBLEM"] = df["WHY_SOLUTION_IS_PROBLEM"].fillna("Não classificado")

        # Aplica a função para definir o status de cada OS
        df["status_os"] = df.apply(definir_status, axis=1)

        # Datas aberturas (converte para DT)
        df["DATA DA ABERTURA DA OS DT"] = pd.to_datetime(df["DATA DA ABERTURA DA OS"])
        df["DATA DO FECHAMENTO DA OS DT"] = pd.to_datetime(df["DATA DO FECHAMENTO DA OS"])

        # Dias OS Anterior
        df["prev_days"] = df["prev_days"].fillna("Não há OS anterior para esse problema")

        # Ordena por data de abertura
        df = df.sort_values(by="DATA DA ABERTURA DA OS DT", ascending=False)

        return df
