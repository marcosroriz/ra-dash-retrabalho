#!/usr/bin/env python
# coding: utf-8

# Classe que fornecer o serviço de teste de WhatsApp para novas regras de monitoramento

# Imports básicos
import json
import pandas as pd
import numpy as np
import os
import re

# Imports HTTP
import requests

##############################################################################
# CONFIGURAÇÕES BÁSICAS ######################################################
##############################################################################
WP_ZAPI_URL = os.getenv("WP_ZAPI_URL")
WP_ZAPI_SEND_TEXT_URL = f"{WP_ZAPI_URL}/send-text"
WP_ZAPI_SEND_LINK_URL = f"{WP_ZAPI_URL}/send-link"
WP_ZAPI_TOKEN = os.getenv("WP_ZAPI_TOKEN")
WP_ZAPI_LINK_IMAGE_URL = os.getenv("WP_ZAPI_LINK_IMAGE_URL")

DASHBOARD_URL = os.getenv("DASHBOARD_URL")

headers = {
    "Client-Token": WP_ZAPI_TOKEN,
    "Content-Type": "application/json",
}


##############################################################################
# ROTINAS DE APOIO ###########################################################
##############################################################################
def formatar_telefone(numero_br):
    # Remove tudo que não for número
    somente_digitos = re.sub(r"\D", "", numero_br)

    # Adiciona o DDI do Brasil (55) no início, se não tiver
    if not somente_digitos.startswith("55"):
        somente_digitos = "55" + somente_digitos
    return somente_digitos


##############################################################################
# TEMPLATES ##################################################################
##############################################################################

# TODO: Usar uma linguagem de template mais adequada, como Jinja2


# Classe do serviço
class CRUDWppTestService(object):

    def build_msg_header(self, df, nome_regra, num_os, data_periodo_regra, min_dias):
        # Mensagem Inicial
        msg_str = f"""----------
⚡ *REGRA*: {nome_regra}
----------
🕒 Período de análise da regra: {data_periodo_regra}
🔄 Mínimo de dias para retrabalho: {min_dias}
🚨 Total de OS detectadas: {num_os}
"""

        # Computa o número de OS por status
        df_status_agg = df.groupby("status_os").size().reset_index(name="total")
        df_status_agg["PERC_TOTAL_OS"] = (df_status_agg["total"] / df_status_agg["total"].sum()) * 100

        for _, row in df_status_agg.iterrows():
            status_os = row["status_os"]
            total = row["total"]
            perc_total_os = row["PERC_TOTAL_OS"]
            msg_str += f"* {status_os}: {total} ({perc_total_os:.1f}%)\n"

        return msg_str
    

    def build_msg_top_10_problemas(self, df, nome_regra, num_os, data_periodo_regra, min_dias):
        # Top 10 problemas
        msg_str = "----------\n"
        msg_str += "💣 Top 10 Problemas Encontrados:\n"
        msg_str += "----------\n"
        
        df_problema_agg = df.groupby("DESCRICAO DO SERVICO").size().reset_index(name="total").sort_values(by="total", ascending=False)
        df_problema_agg["PERC_TOTAL_OS"] = (df_problema_agg["total"] / df_problema_agg["total"].sum()) * 100
        df_problema_agg = df_problema_agg.head(10)
        for _, row in df_problema_agg.iterrows():
            problema = row["DESCRICAO DO SERVICO"]
            total = row["total"]
            perc_total_os = row["PERC_TOTAL_OS"]
            msg_str += f"* {problema}: {total} ({perc_total_os:.1f}%)\n"

        return msg_str
    
    def build_msg_link_relatorio(self):
        link_url = f"{DASHBOARD_URL}/regra-relatorio?id_regra=DEFINIR_AO_CRIAR=dia=DEFINIR_AO_EXECUTAR"
        msg_str = f"🔗 Relatório: {link_url}"
        
        return msg_str, link_url

    def get_wpp_problema_header(self, nome_problema, numero_os):
        secao_str = f"""💣 Problema: {nome_problema} / Total de OS: {numero_os}"""
        return secao_str

    def get_wpp_problema_content(self, row_os_detectada, min_dias):
        numero_os = row_os_detectada["NUMERO DA OS"]
        codigo_veiculo = row_os_detectada["CODIGO DO VEICULO"]
        status_os = row_os_detectada["status_os"]

        title_str = f"OS: {numero_os} / {codigo_veiculo}"
        link_description_str = f"Status: {status_os}"
        link_str = f"{DASHBOARD_URL}/retrabalho-por-os?os={numero_os}&mindiasretrabalho={min_dias}"

        os_detectada_str = f"""⚙️ OS: {numero_os} / 🚍 {codigo_veiculo} / {status_os} \n {link_str}"""
        return os_detectada_str, title_str, link_description_str, link_str

    def __wpp_send_text(self, msg_str, telefone_destino):
        payload = {
            "phone": telefone_destino,
            "message": msg_str,
        }
        payload_json = json.dumps(payload)
        print("MANDANDO MENSAGEM:")
        print(payload_json)
        response = requests.post(WP_ZAPI_SEND_TEXT_URL, headers=headers, data=payload_json)

        return response.status_code

    def __wpp_send_link(
        self,
        msg_str,
        title_str,
        link_str,
        link_description_str,
        telefone_destino,
    ):
        payload = {
            "phone": telefone_destino,
            "message": msg_str,
            "image": WP_ZAPI_LINK_IMAGE_URL,
            "title": title_str,
            "linkUrl": link_str,
            "linkDescription": link_description_str,
        }

        payload_json = json.dumps(payload)
        print(payload_json)
        response = requests.post(WP_ZAPI_SEND_LINK_URL, headers=headers, data=payload_json)

        return response.status_code

    def build_and_send_msg(
        self,
        df,
        num_os,
        nome_regra,
        data_periodo_regra,
        min_dias,
        telefone_destino,
    ):
        # Constrói a mensagem
        msg_header = self.build_msg_header(df, nome_regra, num_os, data_periodo_regra, min_dias)
        msg_top_10_problemas = self.build_msg_top_10_problemas(df, nome_regra, num_os, data_periodo_regra, min_dias)
        msg_link_relatorio, link_relatorio_url = self.build_msg_link_relatorio()
        title_link = f"Relatório da Regra {nome_regra}"
        link_description_link = f"Acessar relatório"

        # Envia a mensagem
        self.__wpp_send_text(msg_header, telefone_destino)
        self.__wpp_send_text(msg_top_10_problemas, telefone_destino)
        self.__wpp_send_link(msg_link_relatorio, title_link, link_relatorio_url, link_description_link, telefone_destino)
