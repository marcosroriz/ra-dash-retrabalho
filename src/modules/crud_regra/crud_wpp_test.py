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

    def get_wpp_header(
        self, nome_regra, num_os, data_periodo_regra, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os
    ):
        regra_str = f"""
----
🚨 *REGRA*: {nome_regra}
* Período da Regra: {data_periodo_regra}
* Mínimo de dias para Retrabalho: {min_dias}
* Modelos: {", ".join(lista_modelos)}
* Oficinas: {", ".join(lista_oficinas)}
* Seções: {", ".join(lista_secaos)}
* OS: {", ".join(lista_os)}
* Total de OS detectadas: {num_os}
----
"""
        return regra_str

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
        link_description_str,
        link_str,
        telefone_destino,
    ):
        payload = {
            "phone": telefone_destino,
            "message": msg_str,
            "title": title_str,
            "linkDescription": link_description_str,
            "link": link_str,
        }

        payload_json = json.dumps(payload)
        print("MANDANDO MENSAGEM:")
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
        lista_modelos,
        lista_oficinas,
        lista_secaos,
        lista_os,
        telefone_destino,
    ):
        cabecalho_str = self.get_wpp_header(
            nome_regra, num_os, data_periodo_regra, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os
        )

        # Envia o cabeçalho
        self.__wpp_send_text(cabecalho_str, telefone_destino)

        # Analisa cada problema
        lista_problemas = df["DESCRICAO DO SERVICO"].unique()
        for problema in lista_problemas:
            df_problema = df[df["DESCRICAO DO SERVICO"] == problema]
            problema_str = self.get_wpp_problema_header(problema, len(df_problema))

            # Envia o problema
            self.__wpp_send_text(problema_str, telefone_destino)

            # Envia o conteúdo de cada OS
            for _, row in df_problema.iterrows():
                os_str, title_str, link_description_str, link_str = self.get_wpp_problema_content(row, min_dias)
                self.__wpp_send_link(os_str, title_str, link_description_str, link_str, telefone_destino)
