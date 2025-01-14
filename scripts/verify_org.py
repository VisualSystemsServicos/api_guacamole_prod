from dotenv import load_dotenv
# from db import *
import requests
import json
import time
import os
import re

from scripts import functions
# from db import *

# Chamada da função de logging
log_geral = functions.setup_logger(name='logging-geral')
script_name = os.path.splitext(os.path.basename(__file__))[0]

def consult_org(url_vault, token_vault, org_path):
    try:
        url = f'{url_vault}/{org_path}/?list=true'
        headers = {
            'X-Vault-Token' : token_vault
        }
        r = requests.get(url=url, headers=headers)
        consult = r.json().get('data', {}).get('keys', [])

        if consult != []:
            return True
        else:
            return False
    
    except Exception as e:
        log_geral.error(f'({script_name}) - erro na função main - {e}')
        return None

def main(org, token_guacamole=None, data_source=None):
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
        token_vault = functions.auth_vault(url_vault=url_vault, vault_user=vault_user, vault_pass=vault_pass)
        
        # Verifica se todos os tokens foram coletados
        if token_vault:
            
            path_vault = f'{base_vault}/{org}'
            log_geral.info(f'({script_name}) - path_vault - {path_vault}')

            consult = consult_org(url_vault=url_vault, token_vault=token_vault, org_path=path_vault)

            if consult == True:
                log_geral.info(f'({script_name}) - Org "{org}" encontrada no Vault')
                return True
            
            else:
                log_geral.info(f'({script_name}) - Org "{org}" não encontrada no Vault')
                return False

        else:
            # Não conseguiu localizar ou gerar algum token de acesso
            log_geral.error(f'({script_name}) - Algum token de acesso não foi localizado ou gerado.')
        
    except Exception as e:
        log_geral.error(f'({script_name}) - erro na função main - {e}')
        return False

if __name__ == '__main__':
    """
        Exemplo de chamada da main:
        
        org = 'Visual Systems Service/Visual Systems-Equinix SP4'

    """

    main_result = main(org=org)