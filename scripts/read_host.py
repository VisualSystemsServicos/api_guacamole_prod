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

def extract_secrets(data):
    try:
        result = []
        for key, value in data.items():
            if key.startswith('username_'):
                index = key.split('_')[1]  # Extrai o índice do username
                password_key = f'password_{index}'  # Gera a chave correspondente da senha
                password_value = data.get(password_key, '')  # Obtém o valor da senha
                
                # Adiciona o resultado no formato desejado
                result.append({
                    "key": index,
                    "username": value,
                    "password": password_value
                })
        
        return {"secrets": result}  # Retorna o JSON com a lista de segredos

    except Exception as e:
        log_geral.error(f'({script_name}) - erro na função extract_secrets - {e}')
        return None

def main(org, host, method, token_guacamole=None, data_source=None):
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
            log_geral.info(f'({script_name}) - method informado - {method}')

            data_secrets = vault_secrets(url_vault=url_vault, token=token_vault, org_path=path_vault)

            if method == 'credentials':
                secrets = extract_secrets(data_secrets)
                log_geral.info(f'({script_name}) - script pegou os segredos com o method - {method}')

            elif method == 'full':
                secrets = data_secrets
                log_geral.info(f'({script_name}) - script pegou os segredos com o method - {method}')
            
            else:
                log_geral.info(f'({script_name}) - method informado invalido - {method}')
                return f'method informado invalido'

            if secrets != []:   
                log_geral.info(f'({script_name}) - script pegou os segredos com sucesso')
                return secrets
            else:
                log_geral.info(f'({script_name}) - host não localizado')
                return f'host não localizado'

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

    """

    main_result = main(org=org, host=host, method=method)