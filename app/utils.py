from scripts import create_host_secrets
from scripts import create_org_guacamole
from scripts import load_connections_org_guacamole
from scripts import migrate_org_full
from scripts import migrate_org_parcial
from scripts import delete_host
from scripts import read_host
from scripts import update_host
from scripts import verify_org

def run_main_script_create_host_secrets(org, host, json_secrets, ip_guacd):
    try:
        create_host_secrets.main(
            org=org, 
            host=host, 
            json_secrets=json_secrets, 
            ip_guacd=ip_guacd
        )
        return {"message": "Script executado com sucesso."}
    except Exception as e:
        return {"error": str(e)}

def run_main_script_create_org_guacamole(path_org):
    try:
        create_org_guacamole.main(
            path_org=path_org
        )
        return {"message": "Script executado com sucesso."}
    except Exception as e:
        return {"error": str(e)}

def run_main_script_load_connections_org_guacamole(org, ip_guacd):
    try:
        load_connections_org_guacamole.main(
            org = org, 
            ip_guacd = ip_guacd
        )
        return {"message": "Script executado com sucesso."}
    except Exception as e:
        return {"error": str(e)}

def run_main_script_migrate_org_full(old_org, new_org, ip_guacd):
    try:
        migrate_org_full.main(
            old_org = old_org,
            new_org = new_org,
            ip_guacd = ip_guacd
        )
        return {"message": "Script executado com sucesso."}
    except Exception as e:
        return {"error": str(e)}

def run_main_script_migrate_org_parcial(old_org, new_org, list_hosts, ip_guacd):
    try:
        migrate_org_parcial.main(
            old_org = old_org,
            new_org = new_org,
            list_hosts = list_hosts,
            ip_guacd = ip_guacd
        )
        return {"message": "Script executado com sucesso."}
    except Exception as e:
        return {"error": str(e)}

def run_main_script_delete_host(org, host):
    try:
        delete_host.main(
            org = org, 
            host = host
        )
        return {"message": "Script executado com sucesso."}
    except Exception as e:
        return {"error": str(e)}

def run_main_script_read_host(org, host):
    try:
        secrets = read_host.main(
            org = org, 
            host = host
        )
        return {"message": f"Secrets: {secrets}"}
    except Exception as e:
        return {"error": str(e)}

def run_main_script_update_host(org, host, data):
    try:
        update_host.main(
            org=org, 
            host=host, 
            data=data, 
        )
        return {"message": "Script executado com sucesso."}
    except Exception as e:
        return {"error": str(e)}

def run_main_script_verify_org(org):
    try:
        verify = verify_org.main(
            org = org
        )
        return {"message": f"Verify: {verify}"}
    except Exception as e:
        return {"error": str(e)}