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

SMTP_KEY = os.getenv("SMTP")

##############################################################################
# TEMPLATES ##################################################################
##############################################################################

# TODO: Usar uma linguagem mais adequada, como Jinja


def get_email_body_header(
    nome_regra, num_os, data_periodo_regra, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os
):
    regra_str = f"""
    ========================================================
    🚨 REGRA: {nome_regra}    
    ========================================================
    Período da Regra: {data_periodo_regra}
    Mínimo de dias para Retrabalho: {min_dias}
    Modelos: {", ".join(lista_modelos)}
    Oficinas: {", ".join(lista_oficinas)}
    Seções: {", ".join(lista_secaos)}
    OS: {", ".join(lista_os)}
    Total de OS detectadas: {num_os}
    """

    return regra_str


def get_email_body_content(row_os_detectada, col_width=16):
    os_detectada_str = f"""
    {"-"*col_width}
    {'CATEGORIA'.rjust(col_width)}: {row_os_detectada["status_os"]}
    {'OS'.rjust(col_width)}: {row_os_detectada["NUMERO DA OS"]}
    {'VEÍCULO'.rjust(col_width)}: {row_os_detectada["CODIGO DO VEICULO"]}
    {'MODELO'.rjust(col_width)}: {row_os_detectada["DESCRICAO DO MODELO"]}
    {'SERVIÇO'.rjust(col_width)}: {row_os_detectada["DESCRICAO DO SERVICO"]}
    {'COLABORADOR'.rjust(col_width)}: {row_os_detectada["nome_colaborador"]}
    {'SINTOMA'.rjust(col_width)}: {row_os_detectada["SINTOMA"]}
    {'CORREÇÃO'.rjust(col_width)}: {row_os_detectada["CORRECAO"]}
    {'SCORE SINTOMA'.rjust(col_width)}: {row_os_detectada["SCORE_SYMPTOMS_TEXT_QUALITY"]}
    {'SCORE CORREÇÃO'.rjust(col_width)}: {row_os_detectada["SCORE_SOLUTION_TEXT_QUALITY"]}
    {'JUSTIFICATIVA'.rjust(col_width)}: {row_os_detectada["WHY_SOLUTION_IS_PROBLEM"]}
    {'TOTAL GASTO'.rjust(col_width)}: {row_os_detectada["total_valor"]}
    {'PEÇAS TROCADAS'.rjust(col_width)}:\n"""

    for peca in row_os_detectada["pecas_trocadas_str"].split("__SEP__"):
        os_detectada_str += f"""{''.rjust(col_width)} - {peca.strip()}\n"""

    os_detectada_str += f"{'-'*col_width}\n"

    return os_detectada_str


# Classe do serviço
class CRUDEmailTestService:
    def __init__(self, dbEngine):
        self.dbEngine = dbEngine

    def build_email(
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
    ):

        # Header
        header_str = get_email_body_header(
            nome_regra, num_os, data_periodo_regra, min_dias, lista_modelos, lista_oficinas, lista_secaos, lista_os
        )

        # Content
        # content_str = ""
        # for row in df.to_dict(orient="records"):
        #     content_str += get_email_body_content(row)

        # Build email
        email_str = header_str 
        print(json.dumps(email_str, indent=4))
        return email_str


    def send_email(self, email_str, nome_regra, to_email):
        msg = EmailMessage()
        msg["Subject"] = f"🚨 TESTE ALERTA REGRA: {nome_regra}"
        msg["From"] = "ceia.ra.ufg@gmail.com"
        msg["To"] = to_email
        msg.set_content(email_str)

        print("configurando email")
        print("Enviando para:", to_email)

        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login("ceia.ra.ufg@gmail.com", SMTP_KEY)
            smtp.send_message(msg)

        print("Email enviado com sucesso")
        return True
    