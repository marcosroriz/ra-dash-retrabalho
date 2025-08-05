#!/usr/bin/env python
# coding: utf-8

# Imports básicos
import pandas as pd
import io

# Imports específicos
import tema

# Funções utilitárias para os serviços


# Função para definir o status de uma OS
def definir_status(os_row):
    if os_row.get("correcao_primeira") == True:
        return f"{tema.ICONE_CORRECAO_PRIMEIRA} Correção Primeira"
    elif os_row.get("correcao") == True:
        return f"{tema.ICONE_CORRECAO_TARDIA} Correção Tardia"
    elif os_row.get("retrabalho") == True:
        return f"{tema.ICONE_RETRABALHO} Retrabalho"
    elif os_row.get("nova_os_com_retrabalho_anterior") == True:
        return f"{tema.ICONE_NOVA_OS_COM_RETRABALHO_ANTERIOR} Nova OS, com retrabalho prévio"
    elif os_row.get("nova_os_sem_retrabalho_anterior") == True:
        return f"{tema.ICONE_NOVA_OS_SEM_RETRABALHO_ANTERIOR} Nova OS, sem retrabalho prévio"
    else:
        return f"{tema.ICONE_NAO_CLASSIFICADO} Não classificado"
