from datetime import datetime, timedelta
from dotenv import load_dotenv
import requests
import time
import json
import os

from scripts import functions
# from db import *

# Chamada da função de logging
log_geral = functions.setup_logger(name='logging-geral')
script_name = os.path.splitext(os.path.basename(__file__))[0]

def delete_vault_secret(url_vault, token, path_org):
    try:
        url = f'{url_vault}/{path_org}'
        headers = {
            'X-Vault-Token': token
        }
        r = requests.delete(url=url, headers=headers)

        if r.status_code == 204:  
            return True
        else:
            log_geral.error(f'Erro ao deletar segredo: {r.status_code} - {r.text}')
            return False

    except Exception as e:
        log_geral.error(f'Erro na função delete_vault_secret: {e}')
        return False

def list_connetions_guacamole(url_guacamole, data_source, token):
    try:
        lista_connections = []
        url = f'{url_guacamole}/api/session/data/{data_source}/connectionGroups/ROOT/tree?token={token}'
        payload = {}
        headers = {}
        r = requests.get(url=url, headers=headers, data=payload)
        list_connections = json.loads(r.text)
        return list_connections

    except Exception as e:
        log_geral.error(f'({script_name}) - erro na função list_connections_guacamole - {e}')
        return None

def get_connections_group_guacamole(data, group_name):
    try:
        # Verifica se o nome do grupo atual corresponde ao grupo alvo
        if data.get('name') == group_name:
            group_identifier = data.get('identifier')
            return data.get('childConnections', []), group_identifier

        # Se não é o grupo alvo, verifica em cada subgrupo
        for group in data.get('childConnectionGroups', []):
            result = get_connections_group_guacamole(group, group_name)
            if result is not None:
                return result
        return None
    
    except Exception as e:
        log_geral.error(f'({script_name}) - erro na função list_connections_guacamole - {e}')
        return None

def delete_connection_guacamole(url_guacamole, data_source, token, connection):
    try:
        connection_name = connection.get('name')
        connection_identifier = connection.get('identifier')    
        url = f'{url_guacamole}/api/session/data/{data_source}/connections/{connection_identifier}?token={token}'
        payload = {}
        headers = {}
        r = requests.delete(url=url, headers=headers, data=payload)

        if r.status_code == 204:  
            return True
        else:
            log_geral.error(f'Erro ao deletar segredo: {r.status_code} - {r.text}')
            return False

    except Exception as e:
        log_geral.error(f'({script_name}) - erro na função list_connections_guacamole - {e}')
        return None

def main(org, host, token_guacamole=None, data_source=None):
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

        # Verifica se a automação foi chamado com token do Guacamole, se não, cria um novo.
        if token_guacamole is None or data_source is None:
            token_guacamole, data_source = functions.auth_guacamole(url_guacamole=url_guacamole, username=guacamole_user, password=guacamole_pass, totp_secret=totp_secret)

        # Verifica se todos os tokens foram coletados
        if token_vault is not None or token_guacamole is not None:
            log_geral.info(f'({script_name}) - Coletou todos os tokens, continuando.')

            path = f'{base_vault}/{org}'
            path_vault = f'{path}/{host}'

            grupo = path.split('/')[-1]
            org_path_guacamole = path_vault.split('data/', 1)[1]

            log_geral.info(f'({script_name}) - path informado - "{path}"')
            log_geral.info(f'({script_name}) - host informado - "{host}"')

            delete_vault = delete_vault_secret(url_vault=url_vault, token=token_vault, path_org=path_vault)
            if delete_vault == True:
                log_geral.info(f'({script_name}) - Host "{host}" deletado do Vault com sucesso')
            
            list_guacamole_connections = list_connetions_guacamole(url_guacamole=url_guacamole, data_source=data_source, token=token_guacamole)
            connections_group, group_identifier = get_connections_group_guacamole(data=list_guacamole_connections, group_name=grupo)
            connections_filtred = [item for item in connections_group if item['name'] == host]

            if connections_filtred:
                connection = connections_filtred[0]
                delete_guacamole = delete_connection_guacamole(url_guacamole=url_guacamole, data_source=data_source, token=token_guacamole, connection=connection)
                
                if delete_guacamole == True:
                    log_geral.info(f'({script_name}) - Host "{host}" deletado do Guacamole com sucesso')
            else:
                log_geral.info(f'({script_name}) - Host "{host}" não possui conexao no guacamole')

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
        }
    """

    main_result = main(org=org, host=host)
