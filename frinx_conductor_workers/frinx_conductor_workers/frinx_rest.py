import json
import os
from collections import namedtuple
from http.cookies import SimpleCookie

uniconfig_url_base = os.getenv("UNICONFIG_URL_BASE", "https://uniconfig:8181/rests")
elastic_url_base = os.getenv("ELASTICSEACRH_URL_BASE", "http://elasticsearch:9200")
conductor_url_base = os.getenv("CONDUCTOR_URL_BASE", "http://workflow-proxy:8088/proxy/api")
inventory_url_base = os.getenv("INVENTORY_URL_BASE", "http://inventory:8000/graphql")
influxdb_url_base = os.getenv("INFLUXDB_URL_BASE", "http://influxdb:8086")
resource_manager_url_base = os.getenv(
    "RESOURCE_MANAGER_URL_BASE", "http://resource-manager:8884/query"
)

uniconfig_user = os.getenv("UNICONFIG_USER", "admin")
uniconfig_passwd = os.getenv("UNICONFIG_PASSWD", "admin")
uniconfig_credentials = (uniconfig_user, uniconfig_passwd)
uniconfig_headers = {"Content-Type": "application/json"}
elastic_headers = {"Content-Type": "application/json"}

x_tenant_id = os.getenv("X_TENANT_ID", "frinx")
x_from = os.getenv("X_FROM", "fm-base-workers")
x_auth_user_group = os.getenv("X_AUTH_USER_GROUP", "network-admin")
conductor_headers = {
    "Content-Type": "application/json",
    "x-tenant-id": x_tenant_id,
    "from": x_from,
    "x-auth-user-groups": x_auth_user_group,
}

additional_uniconfig_request_params = {
    "auth": uniconfig_credentials,
    "verify": False,
    "headers": uniconfig_headers,
}


def parse_response(r):
    decode = r.content.decode("utf8")
    try:
        response_json = json.loads(decode if decode else "{}")
    except ValueError as e:
        response_json = json.loads("{}")

    response_code = r.status_code
    return response_code, response_json


def extract_uniconfig_cookies(task):
    uniconfig_cookies_multizone = extract_uniconfig_cookies_multizone(task)

    cluster_for_device = get_uniconfig_cluster_from_task(task)

    return uniconfig_cookies_multizone.get(cluster_for_device, {}) or {}


def extract_uniconfig_cookies_multizone(task):
    uniconfig_context = task.get("inputData", {}).get("uniconfig_context", {}) or {}
    uniconfig_cookies_multizone = uniconfig_context.get("uniconfig_cookies_multizone", {}) or {}

    return uniconfig_cookies_multizone


def get_devices_by_uniconfig(devices, task, existing_uniconfig_cookies_multizone=None):
    device_with_cluster = namedtuple("devices", ["uc_cluster", "device_names"])

    return [device_with_cluster(uc_cluster=uniconfig_url_base, device_names=devices)]


def get_uniconfig_cluster_from_task(task):
    return uniconfig_url_base


# these could be removed>>>
def parse_header(r):
    cookie = SimpleCookie()
    cookie.load(r.cookies)
    cookies = {}
    for key, val in cookie.items():
        if key == "UNICONFIGTXID":
            cookies[key] = val.value
    return cookies


def add_uniconfig_tx_cookie(uniconfig_tx_id):
    header = uniconfig_headers
    if uniconfig_tx_id and uniconfig_tx_id != "":
        header["Cookie"] = "UNICONFIGTXID=" + uniconfig_tx_id
    return header


# <<<these could be removed
