from fastapi import HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from dotenv import load_dotenv
import os

dotenv_path = os.path.join(os.path.dirname(__file__), "../scripts/.env")

load_dotenv(dotenv_path)
API_TOKEN = os.getenv('api_token')
API_TOKEN_NAME = 'API-TOKEN'

api_token_header = APIKeyHeader(name=API_TOKEN_NAME, auto_error=True)

def verify_api_key(token: str = Security(api_token_header)):
    if token != API_TOKEN:
        raise HTTPException(status_code=403, detail="Acesso negado: API Key inválida.")
    return token
