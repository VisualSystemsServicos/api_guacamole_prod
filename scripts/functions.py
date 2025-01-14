from datetime import datetime
from logging import Logger
import requests
import logging
import pyotp
import json
import time
import os

TIME_TOKEN = 10

# Token Guacamole Teste
# TOKEN_CACHE_FILE = '/var/log/api_guacamole/guacamole_hom_token_cache.json'

# Token Guacamole Produtivo
TOKEN_CACHE_FILE = "/var/log/api_guacamole/guacamole_prod_token_cache.json"

def setup_logger(name: str = "logging", level: int = logging.INFO, log_dir: str = '/var/log/api_guacamole/') -> Logger:
    """
    Configura um logger personalizado.

    Args:
        name (str): Nome do logger.
        level (int): Nível do logger (ex: logging.DEBUG, logging.INFO).
        log_dir (str): Caminho do diretório de logs. O arquivo terá um nome dinâmico com a data.

    Returns:
        Logger: Objeto logger configurado.
    """
    # Cria o diretório de logs, se não existir
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    # Nome do arquivo de log com a data
    current_date = datetime.now().strftime("%d-%m-%Y")
    log_file = os.path.join(log_dir, f'{name}-{current_date}.log')

    # Configuração do logger
    logger = logging.getLogger(name)

    # Verifica se o logger já tem handlers configurados
    if not logger.hasHandlers():
        logger.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
    
def auth_vault(url_vault, vault_user, vault_pass):
    try:
        url = f'{url_vault}/v1/auth/userpass/login/{vault_user}'
        payload = {
            'password' : vault_pass,
        }
        r = requests.post(url=url, data=payload)
        if r.status_code == 200:
            token = r.json()['auth']['client_token']
            return token
        else:
            return None
    except Exception as e:
        print(f"Erro na autenticação: {e}")
        return None

def auth_guacamole(url_guacamole, username, password, totp_secret):
    """
    Autentica no Apache Guacamole com suporte a TOTP e armazenamento em cache do token.
    
    :param url_guacamole: URL do Guacamole (ex: http://guacamole.local)
    :param username: Nome de usuário
    :param password: Senha do usuário
    :param totp_secret: Chave secreta do TOTP
    :return: authToken e dataSource
    """
    # Verifica se há um token armazenado e tenta reutilizá-lo
    if os.path.exists(TOKEN_CACHE_FILE):
        try:
            with open(TOKEN_CACHE_FILE, "r") as f:
                cached_data = json.load(f)
                cached_token = cached_data.get("authToken")
                cached_data_source = cached_data.get("dataSource")
                expiration_time = cached_data.get("expirationTime")

                # Se o token ainda for válido, retorna ele
                if cached_token and time.time() < expiration_time:
                    return cached_token, cached_data_source
        except (json.JSONDecodeError, FileNotFoundError):
            # Caso o arquivo esteja vazio ou corrompido, ignora e continua
            pass

    # Caso não exista um token válido, gera um novo
    try:
        url = f'{url_guacamole}/api/tokens'
        payload = {
            'username': username,
            'password': password
        }
        response = requests.post(url, data=payload)

        # Verificar se o TOTP é requerido
        if response.status_code == 403 and 'guac-totp' in response.json().get('expected', [{}])[0].get('name', ''):
            totp = pyotp.TOTP(totp_secret)
            totp_code = totp.now()
            response = requests.post(
                url,
                data={
                    'username': username,
                    'password': password,
                    'guac-totp': totp_code
                }
            )

        # Se a autenticação for bem-sucedida, armazena o token em cache
        if response.status_code == 200:
            token_data = response.json()
            auth_token = token_data['authToken']
            data_source = token_data['dataSource']
            # Calcula o tempo de expiração do token
            expiration_time = time.time() + 10 * 60  # 30 minutos

            # Salva o token em um arquivo local
            with open(TOKEN_CACHE_FILE, "w") as f:
                json.dump({
                    "authToken": auth_token,
                    "dataSource": data_source,
                    "expirationTime": expiration_time
                }, f)

            return auth_token, data_source
        else:
            print(f"Erro na autenticação: {response.status_code}, {response.text}")
            return None

    except Exception as e:
        print(f"Erro na autenticação: {e}")
        return None

if __name__ == '__main__':
    ...
