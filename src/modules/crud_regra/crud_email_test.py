#!/usr/bin/env python
# coding: utf-8

# Classe que fornecer o serviço de teste de email para novas regras de monitoramento

# Imports básicos
import pandas as pd
import numpy as np
import os
import json

# Import SMTP
import smtplib
from email.message import EmailMessage

##############################################################################
# CONFIGURAÇÕES BÁSICAS ######################################################
##############################################################################
DASHBOARD_URL = os.getenv("DASHBOARD_URL")
SMTP_KEY = os.getenv("SMTP")

##############################################################################
# TEMPLATES ##################################################################
##############################################################################

# TODO: Usar uma linguagem mais adequada, como Jinja


# Classe do serviço
class CRUDEmailTestService:

    def get_email_header_text(
        self, nome_regra, num_os, data_periodo_regra, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os
    ):
        regra_str = f"""
    ========================================================
    🚨 REGRA: {nome_regra}    
    ========================================================
    * Período da Regra: {data_periodo_regra}
    * Mínimo de dias para Retrabalho: {min_dias}
    * Modelos: {", ".join(lista_modelos)}
    * Oficinas: {", ".join(lista_oficinas)}
    * Seções: {", ".join(lista_secaos)}
    * OS: {", ".join(lista_os)}
    * Total de OS detectadas: {num_os}
    """

        return regra_str

    def get_email_header_html(
        self, nome_regra, num_os, data_periodo_regra, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os
    ):
        regra_str = f"""
    <h2>🚨 REGRA: {nome_regra}</h2>
    <ul>
    <li>Período da Regra: {data_periodo_regra}</li>
    <li>Mínimo de dias para Retrabalho: {min_dias}</li>
    <li>Modelos: {", ".join(lista_modelos)}</li>
    <li>Oficinas: {", ".join(lista_oficinas)}</li>
    <li>Seções: {", ".join(lista_secaos)}</li>
    <li>OS: {", ".join(lista_os)}</li>
    <li>Total de OS detectadas: {num_os}</li>
    </ul>
    """

        return regra_str

    def get_email_problema_header_text(self, nome_problema, numero_os):
        secao_str = f"""💣 Problema: {nome_problema} / Total de OS: {numero_os}"""
        return secao_str

    def get_email_problema_header_html(self, nome_problema, numero_os):
        secao_str = f"""<h3>💣 Problema: {nome_problema} / Total de OS: {numero_os}</h3>"""
        return secao_str

    def get_email_problema_content_text(self, row_os_detectada, min_dias):
        numero_os = row_os_detectada["NUMERO DA OS"]
        codigo_veiculo = row_os_detectada["CODIGO DO VEICULO"]
        status_os = row_os_detectada["status_os"]
        link_str = f"{DASHBOARD_URL}/retrabalho-por-os?os={numero_os}&mindiasretrabalho={min_dias}"

        os_str = f"""
🚍 {codigo_veiculo} / ⚙️ OS: {numero_os} / {status_os}
    {link_str}

        """
        return os_str

    def get_email_problema_content_html(self, row_os_detectada, min_dias):
        numero_os = row_os_detectada["NUMERO DA OS"]
        codigo_veiculo = row_os_detectada["CODIGO DO VEICULO"]
        status_os = row_os_detectada["status_os"]
        link_str = f"{DASHBOARD_URL}/retrabalho-por-os?os={numero_os}&mindiasretrabalho={min_dias}"

        os_str = f"""
        <h4>🚍 {codigo_veiculo} / ⚙️ OS: {numero_os} / {status_os}</h4>
        <a href="{link_str}">{link_str}</a>
        <br />
        <br />
        """
        return os_str

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
        email_destino,
    ):
        # Conteúdo do
        email_text = ""
        email_html = ""

        # Cabeçalho
        cabecalho_text = self.get_email_header_text(
            nome_regra, num_os, data_periodo_regra, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os
        )
        cabecalho_html = self.get_email_header_html(
            nome_regra, num_os, data_periodo_regra, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os
        )
        email_text += cabecalho_text
        email_html += cabecalho_html

        # Analisa cada problema
        lista_problemas = df["DESCRICAO DO SERVICO"].unique()
        lista_problemas.sort()
        for problema in lista_problemas:
            df_problema = df[df["DESCRICAO DO SERVICO"] == problema]

            problema_text = self.get_email_problema_header_text(problema, len(df_problema))
            problema_html = self.get_email_problema_header_html(problema, len(df_problema))

            email_text += problema_text
            email_html += problema_html

            # Conteúdo de cada OS
            # Ordena por status_os e codigo do veiculo
            df_problema_ordenado = df_problema.sort_values(by=["status_os", "CODIGO DO VEICULO"])

            for _, row in df_problema_ordenado.iterrows():
                os_text = self.get_email_problema_content_text(row, min_dias)
                os_html = self.get_email_problema_content_html(row, min_dias)
                email_text += os_text
                email_html += os_html

            email_text += "\n"
            email_html += "<hr />"

        # Constrói o email
        msg = EmailMessage()
        msg["Subject"] = f"🚨 TESTE ALERTA REGRA: {nome_regra}"
        msg["From"] = "ceia.ra.ufg@gmail.com"
        msg["To"] = email_destino
        msg.set_content(email_text)
        msg.add_alternative(email_html, subtype="html")

        print("Enviando para:", email_destino)
        print("Email Texto:")
        print(email_text)
        print("Email HTML:")
        print(email_html)

        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login("ceia.ra.ufg@gmail.com", SMTP_KEY)
            smtp.send_message(msg)

        print("Email enviado com sucesso")
        return True
