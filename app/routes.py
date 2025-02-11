from app.security import verify_api_key
from fastapi import APIRouter
from fastapi import Depends
from typing import List

from app.utils import run_main_script_create_host_secrets
from app.utils import run_main_script_create_org_guacamole
from app.utils import run_main_script_load_connections_org_guacamole
from app.utils import run_main_script_migrate_org_full
from app.utils import run_main_script_migrate_org_parcial
from app.utils import run_main_script_delete_host
from app.utils import run_main_script_read_host
from app.utils import run_main_script_update_host
from app.utils import run_main_script_verify_org

router = APIRouter()

@router.post("/create_host_secrets")
async def execute_script_create_host_secrets(org: str, host: str, json_secrets: dict, ip_guacd: str, api_key: str = Depends(verify_api_key)):
    """
    Route create host secrets.
    """

    result = run_main_script_create_host_secrets(org, host, json_secrets, ip_guacd)
    return {"route_status": "sucess", "result": result}

@router.post("/create_org_guacamole")
async def execute_script_create_org_guacamole(path_org: str, api_key: str = Depends(verify_api_key)):
    """
    Route create org guacamole.
    """

    result = run_main_script_create_org_guacamole(path_org)
    return {"route_status": "sucess", "result": result}

@router.post("/load_connections_org_guacamole")
async def execute_script_load_connections_org_guacamole(org: str, ip_guacd: str, api_key: str = Depends(verify_api_key)):
    """
    Route load connections org guacamole.
    """

    result = run_main_script_load_connections_org_guacamole(org, ip_guacd)
    return {"route_status": "sucess", "result": result}

@router.post("/migrate_org_full")
async def execute_script_migrate_org_full(old_org: str, new_org: str, ip_guacd: str, api_key: str = Depends(verify_api_key)):
    """
    Route migrate org full.
    """

    result = run_main_script_migrate_org_full(old_org, new_org, ip_guacd)
    return {"route_status": "sucess", "result": result}

@router.post("/migrate_org_parcial")
async def execute_script_migrate_org_parcial(old_org: str, new_org: str, list_hosts: List[str], ip_guacd: str, api_key: str = Depends(verify_api_key)):
    """
    Route migrate org parcial.
    """

    result = run_main_script_migrate_org_parcial(old_org, new_org, list_hosts, ip_guacd)
    return {"route_status": "sucess", "result": result}

@router.post("/delete_host")
async def execute_script_delete_host(org: str, host: str, api_key: str = Depends(verify_api_key)):
    """
    Route delete host.
    """

    result = run_main_script_delete_host(org, host)
    return {"route_status": "sucess", "result": result}

@router.post("/read_host")
async def execute_script_read_host(org: str, host: str, method: str = 'credentials', api_key: str = Depends(verify_api_key)):
    """
    Route read host.
    """

    result = run_main_script_read_host(org, host, method)
    return {"route_status": "sucess", "result": result}

@router.post("/update_host")
async def execute_script_update_host(org: str, host: str, data: dict, api_key: str = Depends(verify_api_key)):
    """
    Route update host.
    """

    result = run_main_script_update_host(org, host, data)
    return {"route_status": "sucess", "result": result}

@router.post("/verify_org")
async def execute_script_verify_org(org: str, api_key: str = Depends(verify_api_key)):
    """
    Route verify org.
    """

    result = run_main_script_verify_org(org)
    return {"route_status": "sucess", "result": result}
