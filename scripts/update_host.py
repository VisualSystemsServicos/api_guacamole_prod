from dotenv import load_dotenv
# from db import *
import requests
import time
import json
import os
import re

from scripts import functions
# from db import *

# Chamada da função de logging
log_geral = functions.setup_logger(name='logging-geral')
script_name = os.path.splitext(os.path.basename(__file__))[0]

def vault_secrets(url_vault, token, org_path):
    try:
        url = f'{url_vault}/{org_path}'
        headers = {
            'X-Vault-Token' : token
        }
        r = requests.get(url=url, headers=headers)
        secrets = r.json().get('data', {}).get('data', {})
        return secrets

    except Exception as e:
        log_geral.error(f'({script_name}) - erro na função vault_secrets - {e}')
        return None

def update_vault_secret(url_vault, token, path_org, json_secrets):
    try:
        url = f'{url_vault}/{path_org}'
        headers = {
            'X-Vault-Token': token,
            'Content-Type': 'application/json'
        }
        payload = {
            'data': json_secrets
        }
        r = requests.post(url=url, headers=headers, data=json.dumps(payload))

        if r.status_code == 200:
            return True
        else:
            return False
                    
    except Exception as e:
        log_geral.error(f'({script_name}) - erro na função update_vault_secret - {e}')
        return False

def main(org, host, data, token_guacamole=None, data_source=None):
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
            
            path = f'{base_vault}/{org}'
            path_vault = f'{path}/{host}'
            path_vault = path_vault.replace('metadata', 'data')

            log_geral.info(f'({script_name}) - host informado - {host}')
            log_geral.info(f'({script_name}) - path_vault - {path_vault}')
            log_geral.info(f'({script_name}) - json informado - {data}')

            get_secrets = vault_secrets(url_vault=url_vault, token=token_vault, org_path=path_vault)
            
            if get_secrets:
                new_data = {**get_secrets, **data}

                update = update_vault_secret(url_vault=url_vault, token=token_vault, path_org=path_vault, json_secrets=new_data)
                
                if update == True:
                    log_geral.info(f'({script_name}) - Update de dados realizado com sucesso')
                else:
                    log_geral.info(f'({script_name}) - Falha ao realizar o update dos dados')
            
            else:
                log_geral.info(f'({script_name}) - Host não localizado')

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
        host = 'vm-teste'
        data = {
            'username_00' : '...',
            'password_00' : '...'
        }

    """
    
    main_result = main(org=org, host=host, data=data)