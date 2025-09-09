#!/usr/bin/env python
# coding: utf-8

# Classe que centraliza os serviços para mostrar na página de detalhamento de OS

# Imports básicos
import pandas as pd
import numpy as np
import re

# Imports auxiliares
from modules.sql_utils import subquery_oficinas, subquery_secoes, subquery_os, subquery_modelos
from modules.service_utils import definir_status, definir_status_label, definir_emoji_status

# Imports do tema
import tema


class OSService:
    def __init__(self, dbEngine):
        self.pgEngine = dbEngine

    def os_existe(self, os_numero, min_dias):
        """Verifica se a OS existe"""
        query = f"""
        SELECT 
            1
        FROM 
            mat_view_retrabalho_{min_dias}_dias m
        WHERE 
            m."NUMERO DA OS" = '{os_numero}'
        """
        df_os_existe = pd.read_sql(query, self.pgEngine)

        return not df_os_existe.empty

    def obtem_detalhamento_os(self, os_numero, min_dias):
        """Retorna dados de detalhamento de uma OS específica"""
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
            GROUP BY 
                pg."OS"
        ),
        os_alvo AS (
            SELECT 
                "NUMERO DA OS",
                "DESCRICAO DO SERVICO",
                "CODIGO DO VEICULO"
            FROM 
                mat_view_retrabalho_{min_dias}_dias_distinct m
            WHERE 
                m."NUMERO DA OS" = '{os_numero}'
        ),
        os_correlatas AS (
            SELECT
                todas.*
            FROM 
                mat_view_retrabalho_{min_dias}_dias todas
            JOIN 
                os_alvo alvo
            ON
                todas."CODIGO DO VEICULO" = alvo."CODIGO DO VEICULO"
            AND todas."DESCRICAO DO SERVICO" = alvo."DESCRICAO DO SERVICO"
        ),
        os_avaliadas AS (
            SELECT
                *
            FROM
                os_correlatas m
            LEFT JOIN 
                os_dados_classificacao odc
            ON 
                m."KEY_HASH" = odc."KEY_HASH" 
        ),
        os_avaliadas_com_pecas AS (
            SELECT 
                *
            FROM 
                os_avaliadas os
            LEFT JOIN 
                pecas_agg p
            ON 
                os."NUMERO DA OS" = p."OS"
        )
        SELECT 
            *
        FROM 
            os_avaliadas_com_pecas os
        LEFT JOIN 
            colaboradores_frotas_os cfo 
        ON 
            os."COLABORADOR QUE EXECUTOU O SERVICO" = cfo.cod_colaborador
        ORDER BY
            os."DATA DA ABERTURA DA OS" DESC
        """
        df_os_detalhada = pd.read_sql(query, self.pgEngine)

        # Formata datas de abertura
        df_os_detalhada["DATA DA ABERTURA DA OS DT"] = pd.to_datetime(
            df_os_detalhada["DATA DA ABERTURA DA OS"], errors="coerce"
        )
        df_os_detalhada["DATA DA ABERTURA LABEL"] = df_os_detalhada["DATA DA ABERTURA DA OS DT"].dt.strftime(
            "%d/%m/%Y %H:%M"
        )

        # Formata datas de fechamento
        # Cria máscara para valores válidos (pois pode ter valores nulos - OS que não foram fechadas)
        mask = df_os_detalhada["DATA DO FECHAMENTO DA OS"].notna() & (df_os_detalhada["DATA DO FECHAMENTO DA OS"] != "")

        # Converte apenas os válidos
        df_os_detalhada.loc[mask, "DATA DO FECHAMENTO DA OS DT"] = pd.to_datetime(
            df_os_detalhada.loc[mask, "DATA DO FECHAMENTO DA OS"], errors="coerce"
        )

        # Formata os válidos
        df_os_detalhada.loc[mask, "DATA DO FECHAMENTO LABEL"] = df_os_detalhada.loc[
            mask, "DATA DO FECHAMENTO DA OS DT"
        ].dt.strftime("%d/%m/%Y %H:%M")

        # Para os inválidos (NaN ou vazio), seta o label fixo
        df_os_detalhada.loc[~mask, "DATA DO FECHAMENTO LABEL"] = "Ainda não foi fechada"

        # Preenche valores nulos do colaborador
        df_os_detalhada["nome_colaborador"] = df_os_detalhada["nome_colaborador"].fillna("Não Informado")
        df_os_detalhada["nome_colaborador"] = df_os_detalhada["nome_colaborador"].apply(
            lambda x: re.sub(r"(?<!^)([A-Z])", r" \1", x)
        )

        # Preenche valores nulos de peças
        df_os_detalhada["total_valor"] = df_os_detalhada["total_valor"].fillna(0)
        df_os_detalhada["pecas_valor_str"] = df_os_detalhada["pecas_valor_str"].fillna("0")
        df_os_detalhada["pecas_trocadas_str"] = df_os_detalhada["pecas_trocadas_str"].fillna("Nenhuma")

        # Preenche valores nulos da LLM
        df_os_detalhada["WHY_SOLUTION_IS_PROBLEM"] = df_os_detalhada["WHY_SOLUTION_IS_PROBLEM"].fillna(
            "Não classificado"
        )
        df_os_detalhada["SINTOMA"] = df_os_detalhada["SINTOMA"].fillna("Não Informado")
        df_os_detalhada["CORRECAO"] = df_os_detalhada["CORRECAO"].fillna("Não Informado")

        # Aplica a função para definir o status de cada OS
        df_os_detalhada["status_os"] = df_os_detalhada.apply(definir_status, axis=1)
        df_os_detalhada["status_os_label"] = df_os_detalhada.apply(definir_status_label, axis=1)
        df_os_detalhada["status_os_emoji"] = df_os_detalhada.apply(definir_emoji_status, axis=1)

        return df_os_detalhada

    def obtem_os_problema_atual(self, df, problem_no):
        # Pega as OS do problema atual
        df_problema_os_alvo = df[(df["problem_no"] == int(problem_no))].copy()
        df_problema_os_alvo["CLASSE"] = "OS"

        # Formata datas de abertura
        df_problema_os_alvo["DATA DA ABERTURA DA OS DT"] = pd.to_datetime(
            df_problema_os_alvo["DATA DA ABERTURA DA OS"], errors="coerce"
        )
        df_problema_os_alvo["DATA DO FECHAMENTO DA OS DT"] = pd.to_datetime(
            df_problema_os_alvo["DATA DO FECHAMENTO DA OS"], errors="coerce"
        )

        # Agrupa por número de OS
        df_agg_problema_alvo = (
            df_problema_os_alvo.groupby("NUMERO DA OS")
            .agg(
                {
                    "DATA DA ABERTURA DA OS DT": "min",
                    "DATA DO FECHAMENTO DA OS DT": "max",
                    "problem_no": "count",
                }
            )
            .rename(columns={"problem_no": "os_count"})
            .reset_index()
        )
        # Calcula tempo em dias
        df_agg_problema_alvo["DIAS"] = (
            df_agg_problema_alvo["DATA DO FECHAMENTO DA OS DT"] - df_agg_problema_alvo["DATA DA ABERTURA DA OS DT"]
        ).dt.total_seconds() / (24 * 3600)

        # Arredonda para int ou coloca em aberto para vazio
        df_agg_problema_alvo["DIAS"] = df_agg_problema_alvo["DIAS"].apply(
            lambda x: str(int(np.ceil(x))) if pd.notna(x) else "EM ABERTO"
        )

        # Define a classe
        df_agg_problema_alvo["CLASSE"] = "OS"

        # Retorna o df agregado
        return df_agg_problema_alvo

    def obtem_asset_id_veiculo(self, vec_codigo_id):
        """Retorna o AssetId do veículo com base no código do veículo"""
        query = f"""
                SELECT 
                    va."AssetId"
                FROM veiculos_api va
                WHERE 
                    va."Description" = '{vec_codigo_id}'
                LIMIT 1;
            """
        df = pd.read_sql(query, self.pgEngine)

        if not df.empty:
            return df.iloc[0]["AssetId"]
        else:
            return None

    def obtem_odometro_veiculo(self, vec_asset_id, data_inicio_str, data_fim_str):
        """Retorna dados de odômetro do veículo ao longo do tempo com base nos dados das trips"""
        query = f"""
            SELECT 
                ("TripStart"::timestamptz AT TIME ZONE 'America/Sao_Paulo')::date AS travel_date,
                COUNT(*) AS trip_count,
                SUM("DistanceKilometers") AS distance_km
            FROM trips_api ta
            WHERE 
                ta."AssetId" = '{vec_asset_id}'
                AND ("TripStart"::timestamptz AT TIME ZONE 'America/Sao_Paulo') BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            GROUP BY travel_date
            ORDER BY travel_date;
        """
        df = pd.read_sql(query, self.pgEngine)

        # Seta a classe
        df["CLASSE"] = "Odômetro (km)"
        df["target_value"] = df["distance_km"]
        df["target_label"] = df["distance_km"].apply(lambda x: f"{x:.0f}")

        return df

    def obtem_consumo_veiculo(self, vec_asset_id, data_inicio_str, data_fim_str):
        """Retorna dados de consumo do veículo ao longo do tempo com base nos dados das trips"""
        query = f"""
            SELECT 
                ("TripStart"::timestamptz AT TIME ZONE 'America/Sao_Paulo')::date AS travel_date,
                COUNT(*) AS trip_count,
                SUM("FuelUsedLitres") AS consumo_litros
            FROM trips_api ta
            WHERE 
                ta."AssetId" = '{vec_asset_id}'
                AND ("TripStart"::timestamptz AT TIME ZONE 'America/Sao_Paulo') BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            GROUP BY travel_date
            ORDER BY travel_date;
        """
        df = pd.read_sql(query, self.pgEngine)

        # Seta a classe
        df["CLASSE"] = "Consumo (L)"
        df["target_value"] = df["consumo_litros"]
        df["target_label"] = df["consumo_litros"].apply(lambda x: f"{x:.0f}")

        return df

    def obtem_historico_evento_veiculo(self, vec_asset_id, event_name, data_inicio_str, data_fim_str):
        """Retorna dados de eventos do veículo ao longo do tempo"""
        query = f"""
            SELECT 
                "AssetId", DATE("StartDateTime"::timestamptz AT TIME ZONE 'America/Sao_Paulo') AS travel_date,
                COUNT(*) AS total_evts
            FROM 
                public.{event_name} 
            WHERE 
                "AssetId" = '{vec_asset_id}'
                AND 
                "StartDateTime" IS NOT NULL
                AND "StartDateTime"::text NOT ILIKE 'NaN'
                AND ("StartDateTime"::timestamptz AT TIME ZONE 'America/Sao_Paulo')
                    BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
            GROUP BY "AssetId", travel_date;

        """
        df = pd.read_sql(query, self.pgEngine)

        # Seta a classe
        df["CLASSE"] = event_name
        df["target_value"] = df["total_evts"]
        df["target_label"] = df["total_evts"].apply(lambda x: f"{x:.0f}")

        return df

    def obtem_detalhamento_evento_os(self, vec_asset_id, event_name, data_inicio_str, data_fim_str):
        query = f"""
            SELECT
            *
            FROM
                public.{event_name} evt
            LEFT JOIN motoristas_api ma 
                on evt."DriverId" = ma."DriverId" 
            WHERE
                "AssetId" = '{vec_asset_id}'
                AND
                "StartDateTime" IS NOT NULL
                AND "StartDateTime"::text NOT ILIKE 'NaN'
                AND ("StartDateTime"::timestamptz AT TIME ZONE 'America/Sao_Paulo')
                    BETWEEN '{data_inicio_str}' AND '{data_fim_str}'
        """
        df = pd.read_sql(query, self.pgEngine)

        # Seta nome não conhecido para os motoristas que não tiverem dado
        df["Name"] = df["Name"].fillna("Não informado")
        return df
