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

def get_directorys(url_vault, token_vault, path_vault):
    try:
        list_hosts = []
        listagem = '?list=true'
        url = f'{url_vault}/{path_vault}/{listagem}'
        headers = {
            'X-Vault-Token': token_vault
        }
        r = requests.get(url=url, headers=headers)
        retorno = json.loads(r.text)

        for host in retorno['data']['keys']:
            list_hosts.append(host)

        return list_hosts

    except Exception as e:
        log_geral.error(f'({script_name}) - erro na função get_directorys - {e}')
        return None

def identify_parentIdentifier(url_guacamole, data_source, token, org):
    try:
        lista_connections = []
        url = f'{url_guacamole}/api/session/data/{data_source}/connectionGroups?token={token}'
        data = {}
        headers = {}
        r = requests.get(url=url, headers=headers, data=data)
        for key, value in r.json().items():

            if org == value['name']:
                org_id = key
                log_geral.info(f'({script_name}) - função identify_parentIdentifier - identificado org_name: {org} / org_id : {org_id}')
                return org_id
            else:
                continue
        return None
    
    except Exception as e:
        log_geral.error(f'({script_name}) - erro na função identify_parentIdentifier - {e}')
        return None

def vault_secrets(url_vault, token, path):
    try:
        url = f'{url_vault}/{path}'
        headers = {
            'X-Vault-Token' : token
        }
        r = requests.get(url=url, headers=headers)
        secrets = r.json().get('data', {}).get('data', {})
        username = secrets.get('username_00') or None
        password = secrets.get('password_00') or None
        hostname = secrets.get('hostname') or None
        type_host = secrets.get('type') or None
        port = secrets.get('port') or None
        url_acess = secrets.get('url') or None
        return username, password, hostname, port, type_host, url_acess

    except Exception as e:
        log_geral.error(f'({script_name}) - erro na função vault_secrets - {e}')
        return None

def create_connection_guaca(url_guacamole, data_source, token, data):
    try:
        url = f'{url_guacamole}/api/session/data/{data_source}/connections'
        data = data
        params = {
            "token": token
        }
        headers = {
            'Content-Type': 'application/json'
        }
        r = requests.post(url=url, headers=headers, params=params, json=data)

        if r.status_code == 200:
            id_connection = r.json().get('identifier')
            return id_connection
        else:
            return None
    
    except Exception as e:
        log_geral.error(f'({script_name}) - erro na função create_connection_guaca - {e}')
        return None

def main(org, ip_guacd, token_guacamole=None, data_source=None):
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

            # Informar caminho a ser realizado a carga
            path = f'{base_vault}/{org}'
            path_vault = f'{base_vault}/{org}'
            log_geral.info(f'({script_name}) - Path Vault recebido - {path_vault}')

            # Informações padrões
            guacd_hostname = ip_guacd
            guacd_port = '22822'
            guacd_encryption = None
            # Informar IP do remote_app
            host_remote_app = '192.168.10.151'
            port_remote_app = '3389'

            org_name = path_vault.split('/')[-1]
            log_geral.info(f'({script_name}) - Org_name identificada - {org_name}.')

            id_parentIdentifier = identify_parentIdentifier(url_guacamole=url_guacamole, data_source=data_source, token=token_guacamole, org=org_name)
            list_hosts = get_directorys(url_vault=url_vault, token_vault=token_vault, path_vault=path_vault)
            log_geral.info(f'({script_name}) - Lista de hosts encotrados dentro do Vault - {list_hosts}')
            
            for host in list_hosts:    
                path = f'{path_vault}/{host}'
                path = path.replace('metadata', 'data')
                consult_secrets = vault_secrets(url_vault=url_vault, token=token_vault, path=path)
                if consult_secrets != None:
                    username, password, hostname, port, type_host, url_acess = consult_secrets

                    # Cria conexão SSH
                    if type_host == 'Linux' or type_host == 'Switch':
                        payload = {
                            "parentIdentifier": id_parentIdentifier,
                            "name": host,
                            "protocol": "ssh",
                            "parameters": {
                                "port": port,
                                "enable-sftp": True,
                                "hostname": hostname,
                                "private-key": '',
                                "username": username,
                                "password": password,
                                "enable-sftp": True,
                                "sftp-root-directory": "/",
                                "recording-path": "/var/guacamole/record",
                                "recording-name": "${HISTORY_UUID}",
                                "typescript-path": "/var/guacamole/text_log",
                                "typescript-name": "${GUAC_CLIENT_HOSTNAME}_${GUAC_USERNAME}_${GUAC_DATE}_${GUAC_TIME}_${HISTORY_UUID}",
                            },
                            "attributes": {
                                "guacd-port": guacd_port,
                                "guacd-encryption": guacd_encryption,
                                "guacd-hostname": guacd_hostname
                            }
                        }
                        create_connection = create_connection_guaca(url_guacamole=url_guacamole, data_source=data_source, token=token_guacamole, data=payload)

                        if create_connection != None:
                            log_geral.info(f'({script_name}) - Conexao do host "{host}" criada com sucesso - type: {type_host}')
                        else:
                            log_geral.info(f'({script_name}) - Conexao do host "{host}" já existe - type: {type_host}')

                    # Cria conexão RDP
                    elif type_host == 'Windows':
                        payload = {
                            "parentIdentifier": id_parentIdentifier,
                            "name": host,
                            "protocol": "rdp",
                            "parameters": {
                                "port": port,
                                # "disable-auth": True,
                                "ignore-cert": True,
                                "enable-drive": True,
                                "hostname": hostname,
                                "username": username,
                                "password": password,
                                "domain": '',
                                "drive-name": "REPO_Guacamole",
                                "drive-path": "/REPO_Guacamole",
                                "recording-path": "/var/guacamole/record",
                                "recording-name": "${HISTORY_UUID}",
                            },
                            "attributes": {
                                "guacd-port": guacd_port,
                                "guacd-encryption": guacd_encryption,
                                "guacd-hostname": guacd_hostname
                            }
                        }
                        create_connection = create_connection_guaca(url_guacamole=url_guacamole, data_source=data_source, token=token_guacamole, data=payload)

                        if create_connection != None:
                            log_geral.info(f'({script_name}) - Conexao do host "{host}" criada com sucesso - type: {type_host}')
                        else:
                            log_geral.info(f'({script_name}) - Conexao do host "{host}" já existe - type: {type_host}')

                    elif type_host == 'Storage' or type_host == 'Vmware' or type_host == 'Firewall' or type_host == 'AcessoRemoto':
                        payload = {
                            "parentIdentifier": id_parentIdentifier,
                            "name": host,
                            "protocol": "rdp",
                            "parameters": {
                                "port": port_remote_app,
                                # "disable-auth": True,
                                "ignore-cert": True,
                                "enable-drive": True,
                                "hostname": host_remote_app,
                                "username": '${GUAC_USERNAME}',
                                "password": '${GUAC_PASSWORD}',
                                "domain": '',
                                "drive-name": "REPO_Guacamole",
                                "drive-path": "/REPO_Guacamole",
                                "recording-path": "/var/guacamole/record",
                                "recording-name": "${HISTORY_UUID}",
                                "remote-app": "||Navegador",
                                "remote-app-args": f'"--app={url_acess}" --kiosk',
                            },
                            "attributes": {
                                "guacd-port": guacd_port,
                                "guacd-encryption": guacd_encryption,
                                "guacd-hostname": guacd_hostname
                            }
                        }
                        create_connection = create_connection_guaca(url_guacamole=url_guacamole, data_source=data_source, token=token_guacamole, data=payload)

                        if create_connection != None:
                            log_geral.info(f'({script_name}) - Conexao do host "{host}" criada com sucesso - type: {type_host}')
                        else:
                            log_geral.info(f'({script_name}) - Conexao do host "{host}" já existe - type: {type_host}')

                    elif type_host == 'Outros' or type_host == 'outros':
                        log_geral.info(f'({script_name}) - Conexao do host "{host}" não foi criada, type da conexão não esta mapeado para criação - type: {type_host}')

                    else:
                        log_geral.error(f'({script_name}) - Erro na criação do host "{host}" - type: {type_host} ')
                    
                else:
                    log_geral.info(f'({script_name}) - Não foi localizado nenhum segredo do host "{host}" dentro do Vault')
                    
            return True

        else:
            # Não conseguiu localizar ou gerar algum token de acesso
            log_geral.error(f'({script_name}) - Algum token de acesso não foi localizado ou gerado.')
            return False
        
    except Exception as e:
        log_geral.error(f'({script_name}) - erro na função main - {e}')
        return False

if __name__ == '__main__':
    """
        Exemplo de chamada da main:
        
        org = ''
        ip_guacd = ''
    """

    main_result = main(org=org, ip_guacd=ip_guacd)
