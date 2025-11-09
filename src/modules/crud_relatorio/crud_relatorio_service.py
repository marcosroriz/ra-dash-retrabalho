#!/usr/bin/env python
# coding: utf-8

# Classe que centraliza os serviços para CRUD dos relatórios (para ser produzido via LLM)

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
class CRUDRelatorioService:
    def __init__(self, dbEngine):
        self.dbEngine = dbEngine

    def criar_relatorio_monitoramento(self, payload):
        """Função para criar um relatório de monitoramento"""
        table = sqlalchemy.Table("regra_relatorio_llm_os", sqlalchemy.MetaData(), autoload_with=self.dbEngine)

        try:
            with self.dbEngine.begin() as conn:
                stmt = insert(table).values(payload)
                conn.execute(stmt)

            return True
        except Exception as e:
            print(f"Erro ao criar relatorio de monitoramento: {e}")
            return False

    def get_todas_regras_relatorios(self):
        """Função para obter todas as regras de relatórios"""

        # Query
        query = """
            SELECT 
                *,
                (
                    SELECT MAX(dia)
                    FROM relatorio_regra_relatorio_llm_os
                    WHERE id_regra = regra.id
                    GROUP BY id_regra
                ) AS "dia_ultimo_relatorio",
                (
                    SELECT MAX(executed_at)
                    FROM relatorio_regra_relatorio_llm_os
                    WHERE id_regra = regra.id
                    GROUP BY id_regra
                ) AS "executed_at"
            FROM regra_relatorio_llm_os regra
            ORDER BY nome
        """

        # Executa a query
        df = pd.read_sql(query, self.dbEngine)

        return df

    def get_ultima_data_regra(self, id_regra):
        """Função para obter a última data de uma regra de relatório"""
        query = f"""
            SELECT id_regra, MAX(dia) AS ultimo_dia
            FROM relatorio_regra_relatorio_llm_os
            WHERE id_regra = {id_regra}
            GROUP BY id_regra
        """
        df = pd.read_sql(query, self.dbEngine)
        return df
    
    def get_datas_regra(self, id_regra):
        """Função para obter todas as datas de uma regra de relatório"""
        query = f"""
            SELECT dia
            FROM relatorio_regra_relatorio_llm_os
            WHERE id_regra = {id_regra}
            ORDER BY dia DESC
        """
        df = pd.read_sql(query, self.dbEngine)
        return df

    def get_relatorio_markdown_regra(self, id_regra, data_relatorio):
        """Função para obter o relatório em markdown de uma regra e data específica"""
        query = f"""
            SELECT relatorio_md
            FROM relatorio_regra_relatorio_llm_os
            WHERE id_regra = {id_regra} AND dia = '{data_relatorio}'
        """
        df = pd.read_sql(query, self.dbEngine)
        return df

    def existe_execucao_regra_no_dia(self, id_regra, dia):
        """Função para verificar se uma regra já foi executada no dia"""
        query = f"""
            SELECT 1 AS "EXISTE" FROM relatorio_regra_relatorio_llm_os WHERE id_regra = {id_regra} AND dia = '{dia}'
        """
        df = pd.read_sql(query, self.dbEngine)

        if df.empty:
            return False
        else:
            return True
