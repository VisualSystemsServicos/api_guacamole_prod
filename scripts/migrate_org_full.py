from dotenv import load_dotenv
import requests
import json
import os
import re

from scripts import load_connections_org_guacamole 
from scripts import create_org_guacamole
from scripts import functions
# from db import *

# Chamada da função de logging
log_geral = functions.setup_logger(name='logging-geral')
script_name = os.path.splitext(os.path.basename(__file__))[0]

def list_org_vault(url_vault, token_vault, org_path):
    try:
        url = f'{url_vault}/{org_path}/?list=true'
        headers = {
            'X-Vault-Token' : token_vault
        }
        r = requests.get(url=url, headers=headers)
        hosts = r.json().get('data', {}).get('keys', [])
        return hosts
    
    except Exception as e:
        log_geral.error(f'({script_name}) - erro na função list_org_vault - {e}')
        return None

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
        log_geral.error(f'({script_name}) - erro na função get_connections_group_guacamole - {e}')
        return None

def delete_connections_guacamole(url_guacamole, data_source, token, list_connections):
    try:
        for connection in list_connections:
            connection_name = connection.get('name')
            connection_identifier = connection.get('identifier')
            url = f'{url_guacamole}/api/session/data/{data_source}/connections/{connection_identifier}?token={token}'
            payload = {}
            headers = {}
            r = requests.delete(url=url, headers=headers, data=payload)
            log_geral.info(f'({script_name}) - função delete_connections_guacamole - connection: {connection_name} / status: {r.status_code}')

    except Exception as e:
        log_geral.error(f'({script_name}) - erro na função delete_connections_guacamole - {e}')
        return None

def delete_group_guacamole(url_guacamole, data_source, token, group_identifier):
    try:
        url = f'{url_guacamole}/api/session/data/{data_source}/connectionGroups/{group_identifier}?token={token}'
        payload = {}
        headers = {}
        r = requests.delete(url=url, headers=headers, data=payload)
        log_geral.info(f'({script_name}) - função delete_group_guacamole - group: {group_identifier} / status: {r.status_code}')

    except Exception as e:
        log_geral.error(f'({script_name}) - erro na função delete_group_guacamole - {e}')
        return none

def create_vault_new_org(url_vault, token, path_old_org, path_new_org, list_hosts):
    try:
        path_new_org = path_new_org.replace('metadata', 'data')

        for host in list_hosts:
            for host_name, data_secrets in host.items():
                url = f'{url_vault}/{path_new_org}/{host_name}'
                headers = {
                    'X-Vault-Token': token,
                    'Content-Type': 'application/json'
                }
                payload = {
                    'data': data_secrets
                }
                r = requests.post(url=url, headers=headers, data=json.dumps(payload))
                log_geral.info(f'({script_name}) - função create_vault_new_org - create new host: {host_name} / status: {r.status_code}')

        
                if r.status_code == 200:
                    delete_url = f'{url_vault}/{path_old_org}/{host_name}'
                    delete_response = requests.delete(url=delete_url, headers=headers)
                    log_geral.info(f'({script_name}) - função create_vault_new_org - delete old host: {host_name} / status: {delete_response.status_code}')
                    
        # Verifica se a org antiga deixou de existir
        old_hosts = list_org_vault(url_vault=url_vault, token_vault=token, org_path=path_old_org)
        if old_hosts == []:
            log_geral.info(f'({script_name}) - função create_vault_new_org - sucesso na migracao para a nova org')
            return True
        else:
            log_geral.error(f'({script_name}) - erro na função create_vault_new_org - falha na migracao para a nova org')
            return False
                    
    except Exception as e:
        log_geral.error(f'({script_name}) - erro na função create_vault_new_org - {e}')
        return False

def main(old_org, new_org, ip_guacd, token_guacamole=None, data_source=None):
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

            old_org = f'{base_vault}/{old_org}'
            new_org = f'{base_vault}/{new_org}'
            grupo = old_org.split('/')[-1]
            org_path_guacamole = new_org.split('metadata/', 1)[1]

            log_geral.info(f'({script_name}) - old_org - {old_org}')
            log_geral.info(f'({script_name}) - nel_org - {new_org}')
            log_geral.info(f'({script_name}) - org_guacamole - {org_path_guacamole}')

            list_host_for_new_org = []
            list_hosts = list_org_vault(url_vault=url_vault, token_vault=token_vault, org_path=old_org)
            
            log_geral.info(f'({script_name}) - lista de hosts localizados no Vault - {list_hosts}')

            for host in list_hosts:
                path_host = f'{old_org}/{host}'
                path_host = path_host.replace('metadata', 'data')
                get_secrets = vault_secrets(url_vault=url_vault, token=token_vault, org_path=path_host)

                host_full = {
                    host : get_secrets
                }
                list_host_for_new_org.append(host_full)

            list_guacamole_connections = list_connetions_guacamole(url_guacamole=url_guacamole, data_source=data_source, token=token_guacamole)
            connections_group, group_identifier = get_connections_group_guacamole(data=list_guacamole_connections, group_name=grupo)
            
            clear_guacamole = delete_connections_guacamole(url_guacamole=url_guacamole, data_source=data_source, token=token_guacamole, list_connections=connections_group)
            delete_group = delete_group_guacamole(url_guacamole=url_guacamole, data_source=data_source, token=token_guacamole, group_identifier=group_identifier)

            # Cria a nova organização no Vault e Deleta a antiga
            create_new_org_vault = create_vault_new_org(url_vault=url_vault, token=token_vault, path_old_org=old_org, path_new_org=new_org, list_hosts=list_host_for_new_org)
            
            # Cria a org dentro do Guacamole
            create_guacamole = create_org_guacamole.main(path_org=org_path_guacamole, token_guacamole=token_guacamole, data_source=data_source)
            log_geral.info(f'({script_name}) - retorno da chamada do script (create_org_guacamole) - {create_guacamole}')

            if create_guacamole == True:
                # Realiza a carga dos dados da nova Organização
                carga_connections = load_connections_org_guacamole.main(org=org_path_guacamole, ip_guacd=ip_guacd, token_guacamole=token_guacamole, data_source=data_source)
                log_geral.info(f'({script_name}) - retorno da chamada do script (load_connections_org_guacamole) - {carga_connections}')

        else:
            # Não conseguiu localizar ou gerar algum token de acesso
            log_geral.error(f'({script_name}) - Algum token de acesso não foi localizado ou gerado.')

    except Exception as e:
        log_geral.error(f'({script_name}) - erro na função main - {e}')
        return False

if __name__ == '__main__':
    """
        Exemplo de chamada da main:
        
        old_org = 'v1/Guacamole/metadata/Visual Systems Service/Visual Systems-Equinix SP2'
        new_org = 'v1/Guacamole/metadata/Visual Systems Service/Visual SP2'
        ip_guacd = '192.168.150.127'
    """

    main_result = main(old_org=old_org, new_org=new_org, ip_guacd=ip_guacd)

