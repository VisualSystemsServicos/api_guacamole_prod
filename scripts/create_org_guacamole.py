from dotenv import load_dotenv
import requests
import json
import time
import re
import os

from scripts import functions
# from db import *

# Chamada da função de logging
log_geral = functions.setup_logger(name='logging-geral')
script_name = os.path.splitext(os.path.basename(__file__))[0]
        
def verify_connectiongroup(url, token, data_source, org_name):
    try:
        url = f'{url}/api/session/data/{data_source}/connectionGroups?token={token}'
        payload = {}
        headers = {}
        r = requests.get(url=url, headers=headers, data=payload)
        list_connectionsgroups = json.loads(r.text)
        validador = None

        for key, value in list_connectionsgroups.items():
            if value.get('name') == org_name:
                validador = (value.get('name'), value.get('identifier'))

        if validador != None:
            group_name, group_identifier = validador
            return group_name, group_identifier
        else:
            return None
    
    except Exception as e:
        log_geral.error(f'({script_name}) - erro na função verify_connectiongroup - {e}')
        return None

def create_connectiongroup(url, token, data_source, name, parent='ROOT'):
    try:
        url = f'{url}/api/session/data/{data_source}/connectionGroups'
        data = {
            "parentIdentifier": parent,
            "name": name,
            "type": "ORGANIZATIONAL",
            "attributes": {
                "max-connections": "",
                "max-connections-per-user": "",
                "enable-session-affinity": ""
            }
        }
        params = {
            "token": token
        }
        headers = {
            'Content-Type': 'application/json'
        }
        r = requests.post(url=url, headers=headers, params=params, json=data)

        if r.status_code == 200:
            retorno = json.loads(r.text)
            group_name = data.get("name")
            group_identifier = data.get("identifier")
            return group_identifier, group_name  
        else:
            return None

    except Exception as e:
        log_geral.error(f'({script_name}) - erro na função create_connectiongroup - {e}')
        return None

def main(path_org, token_guacamole=None, data_source=None):
    log_geral.info(f'')
    log_geral.info(f'############################################################################')
    log_geral.info(f'')
    log_geral.info(f'({script_name}) - Iniciando script {script_name}.')

    load_dotenv()
    url_guacamole = os.getenv('url_guacamole')
    guacamole_user = os.getenv('guacamole_user')
    guacamole_pass = os.getenv('guacamole_pass')
    url_vault = os.getenv('url_vault')
    vault_user = os.getenv('vault_user')
    vault_pass = os.getenv('vault_pass')
    totp_secret = os.getenv('totp_secret')
    base_vault = os.getenv('base_vault')
    
    try:
        # Verifica se a automação foi chamado com token do Guacamole, se não, cria um novo.
        if token_guacamole is None or data_source is None:
            token_guacamole, data_source = functions.auth_guacamole(url_guacamole=url_guacamole, username=guacamole_user, password=guacamole_pass, totp_secret=totp_secret)

        # Verifica se todos os tokens foram coletados
        if token_guacamole is not None:
            log_geral.info(f'({script_name}) - Coletou todos os tokens, continuando.')

            log_geral.info(f'({script_name}) - path_org recebeu o valor {path_org}')
            padrao_org = None

            if '/' in path_org:
                group_name, org_name = path_org.split('/', 1)
                padrao_org = 'Grupo'
            else:
                org_name = path_org
                padrao_org = 'Organizacao'

            log_geral.info(f'({script_name}) - Identificou que a organização é do tipo - {padrao_org}')
            
            # Caminho apenas com ORGANIZAÇÃO
            if padrao_org == 'Organizacao':
                verify = verify_connectiongroup(url=url_guacamole, token=token_guacamole, data_source=data_source, org_name=org_name)
                if verify == None:
                    create = create_connectiongroup(url=url_guacamole, token=token_guacamole, data_source=data_source, name=org_name)
                    if create != None:
                        log_geral.info(f'({script_name}) - O script criou a organizacao "{org_name}" no guacamole.')
                else:
                    log_geral.info(f'({script_name}) - O script identificou que a organizacao "{org_name}" já existe no guacamole.')
                    
            # Caminho com PARENT e ORGANIZAÇÃO
            else:
                verify = verify_connectiongroup(url=url_guacamole, token=token_guacamole, data_source=data_source, org_name=group_name)

                # A conexão pai não existe
                if verify == None:
                    create_group = create_connectiongroup(url=url_guacamole, token=token_guacamole, data_source=data_source, name=group_name)
                    if create_group != None:
                        group_name, group_id = create_group
                        log_geral.info(f'({script_name}) - O script criou a organizacao Pai "{org_name}" no guacamole.')
                        create_org = create_connectiongroup(url=url_guacamole, token=token_guacamole, data_source=data_source, name=org_name, parent=group_id)
                        if create_org != None:
                            log_geral.info(f'({script_name}) - O script criou a organizacao Filha "{org_name}" no guacamole.')

                # A conexão pai ja exite
                else:
                    # Verifica se a organização filho existe
                    group_name, group_id = verify
                    verify_org = verify_connectiongroup(url=url_guacamole, token=token_guacamole, data_source=data_source, org_name=org_name)
                    if verify_org == None:
                        create = create_connectiongroup(url=url_guacamole, token=token_guacamole, data_source=data_source, name=org_name, parent=group_id)
                        if create != None:
                            log_geral.info(f'({script_name}) - O script criou a organizacao Filha "{org_name}" no guacamole.')
                            
                    else:
                        log_geral.info(f'({script_name}) - O script identificou que a organizacao Filha "{org_name}" já existe no guacamole.')
            
            log_geral.info(f'({script_name}) - O script passou pela criaçao de organizacao com sucesso.')
            return True

        else:
            # Não conseguiu localizar ou gerar algum token de acesso
            log_geral.error(f'({script_name}) - Algum token de acesso não foi localizado ou gerado.')
        
    except Exception as e:
        log_geral.error(f'({script_name}) - erro na função main - {e}')
        return False
            
if __name__ == '__main__':
    """
        Exemplo de chamada da main:
        
        path_org = 'Visual Systems Service/Visual Systems-OCI' - Grupo / Organização
        path_org = 'Visual Systems-OCI' - Apenas Organização
    """

    main_result = main(path_org=path_org)