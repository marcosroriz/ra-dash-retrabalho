

# Função para validar o input
def input_valido(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos):
    if datas is None or not datas or None in datas or min_dias is None:
        return False

    if lista_oficinas is None or not lista_oficinas or None in lista_oficinas:
        return False

    if lista_secaos is None or not lista_secaos or None in lista_secaos:
        return False

    if lista_os is None or not lista_os or None in lista_os:
        return False
    
    if lista_veiculos is None or not lista_veiculos or None in lista_veiculos:
        return False

    return True

def input_valido2(datas, min_dias, lista_oficinas, lista_secaos, lista_os, lista_veiculos, lista_modelos):
    if datas is None or not datas or None in datas or min_dias is None:
        return False

    if lista_oficinas is None or not lista_oficinas or None in lista_oficinas:
        return False

    if lista_secaos is None or not lista_secaos or None in lista_secaos:
        return False

    if lista_os is None or not lista_os or None in lista_os:
        return False
    
    if lista_veiculos is None or not lista_veiculos or None in lista_veiculos:
        return False

    if lista_modelos is None or not lista_modelos or None in lista_modelos:
        return False
        
    return True
# Corrige o input para garantir que "TODAS" não seja selecionado junto com outras opções

def input_valido3(datas, min_dias, lista_veiculos):
    if datas is None or not datas or None in datas or min_dias is None:
            return False
    if lista_veiculos is None or not lista_veiculos or None in lista_veiculos:
            return False
    return True

def input_valido4(datas, min_dias, lista_oficinas, lista_secaos, lista_veiculos):
    if datas is None or not datas or None in datas or min_dias is None:
        return False

    if lista_oficinas is None or not lista_oficinas or None in lista_oficinas:
        return False

    if lista_secaos is None or not lista_secaos or None in lista_secaos:
        return False
    
    if lista_veiculos is None or not lista_veiculos or None in lista_veiculos:
        return False
    return True


def corrige_input(lista):
    # Caso 1: Nenhuma opcao é selecionada, reseta para "TODAS"
    if not lista:
        return ["TODAS"]

    # Caso 2: Se "TODAS" foi selecionado após outras opções, reseta para "TODAS"
    if len(lista) > 1 and "TODAS" in lista[1:]:
        return ["TODAS"]

    # Caso 3: Se alguma opção foi selecionada após "TODAS", remove "TODAS"
    if "TODAS" in lista and len(lista) > 1:
        return [value for value in lista if value != "TODAS"]

    # Por fim, se não caiu em nenhum caso, retorna o valor original
    return lista

