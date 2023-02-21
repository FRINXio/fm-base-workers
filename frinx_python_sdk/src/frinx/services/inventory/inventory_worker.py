import copy
import json
import logging
from dataclasses import asdict
from math import ceil

from frinx.services.frinx_rest import inventory_url_base
from frinx.services.frinx_rest import x_tenant_id
from frinx.services.inventory import templates
from frinx.services.inventory import utils as inventory_utils
from python_graphql_client import GraphqlClient

# def validate_output:


def get_device_status(device_name: str) -> inventory_utils.InventoryOutput:
    try:
        variables = {"deviceName": str(device_name)}
        return inventory_utils.execute_inventory(templates.device_info_template, variables)
    except Exception as e:
        return inventory_utils.InventoryOutput(data=str(e), status="failed", code=500)


def install_device_by_id(device_id: str) -> inventory_utils.InventoryOutput:
    try:
        if len(device_id) == 0:
            raise Exception("Missing input data")

        variables = templates.install_device_variables
        variables["id"] = device_id

        return inventory_utils.execute_inventory(templates.install_device_template, variables)

    except Exception as e:
        return inventory_utils.InventoryOutput(data=str(e), status="failed", code=500)


def uninstall_device_by_id(device_id: str) -> inventory_utils.InventoryOutput:
    try:
        if len(device_id) == 0:
            raise Exception("Missing input data")

        variables = templates.install_device_variables
        variables["id"] = device_id

        return inventory_utils.execute_inventory(templates.uninstall_device_template, variables)

    except Exception as e:
        return inventory_utils.InventoryOutput(data=str(e), status="failed", code=500)


def install_device_by_name(device_name: str) -> inventory_utils.InventoryOutput:
    try:
        if len(device_name) == 0:
            raise Exception("Missing input data")

        response = get_device_status(device_name)

        if len(response.data["devices"]["edges"]) == 0:
            raise Exception("Device " + device_name + " missing in inventory")

        # TODO install only one device or all by regex?

        variables = templates.install_device_variables
        variables["id"] = response.data["devices"]["edges"][0]["node"]["id"]

        return inventory_utils.execute_inventory(templates.install_device_template, variables)

    except Exception as e:
        return inventory_utils.InventoryOutput(data=str(e), status="failed", code=500)


def uninstall_device_by_name(device_name: str) -> inventory_utils.InventoryOutput:
    try:
        if len(device_name) == 0:
            raise Exception("Missing input data")

        response = get_device_status(device_name)

        if len(response.data["devices"]["edges"]) == 0:
            raise Exception("Device " + device_name + " missing in inventory")

        # TODO uninstall only one device or all by regex?
        variables = templates.install_device_variables
        variables["id"] = response.data["devices"]["edges"][0]["node"]["id"]

        return inventory_utils.execute_inventory(templates.uninstall_device_template, variables)

    except Exception as e:
        return inventory_utils.InventoryOutput(data=str(e), status="failed", code=500)


def get_labels() -> inventory_utils.InventoryOutput:
    try:
        return inventory_utils.execute_inventory(templates.label_ids_template, None)

    except Exception as e:
        return inventory_utils.InventoryOutput(data=str(e), status="failed", code=500)


def create_label(label: str) -> inventory_utils.InventoryOutput:
    try:
        variables = templates.InputVariable(templates.CreateLabelInput(name=str(label)))

        return inventory_utils.execute_inventory(templates.create_label_template, variables)

    except Exception as e:
        return inventory_utils.InventoryOutput(data=str(e), status="failed", code=500)


def add_device(
    device_name: str,
    zone: str,
    service_state: str,
    mount_body: dict,
    vendor=None,
    model=None,
    size=None,
    labels=None,
) -> inventory_utils.InventoryOutput:
    try:
        if len(device_name) == 0:
            raise Exception("Missing input device_name")
        if len(zone) == 0:
            raise Exception("Missing input zone")
        if not inventory_utils.ServiceState.has_value(service_state):
            raise Exception("Missing input service state")
        if len(mount_body) == 0:
            raise Exception("Missing input mount_body")
        if type(labels) is not None:
            labels = list(labels.replace(" ", "").split(","))

        label_ids = []

        if labels is not None and len(labels) > 0:
            labels_name_id = inventory_utils.label_name_id(get_labels().data)

            for label_name in labels:
                label_id = labels_name_id.get(label_name)
                if label_id is None:
                    response = create_label(label_name)
                    match response.status:
                        case "data":
                            label_ids.append(response.data["createLabel"]["label"]["id"])
                        case "errors" | "failed":
                            raise Exception(response.data)
                else:
                    label_ids.append(label_id)

        variables = templates.InputVariable(
            templates.AddDeviceVariable(
                name=str(device_name),
                zoneId=str(inventory_utils.get_zone_id(zone)),
                serviceState=str(service_state),
                mountParameters=str(mount_body).replace("'", '"'),
                labelIds=label_ids if type(label_ids) is not None else None,
                vendor=vendor if type(vendor) is not None and len(vendor) > 0 else None,
                model=model if type(model) is not None and len(model) > 0 else None,
                size=size if type(size) is not None and len(size) > 0 else None,
            )
        )

        return inventory_utils.execute_inventory(templates.add_device_template, variables)

    except Exception as e:
        print(e.args)
        return inventory_utils.InventoryOutput(data=str(e), status="failed", code=500)


def get_device_pages_cursors(labels=None) -> inventory_utils.InventoryOutput:
    try:
        label_names = (
            None if labels is None or labels == "" else list(labels.replace(" ", "").split(","))
        )

        device_step = 10
        cursor_count = 20
        has_next_page = True
        page_ids = []
        last_page_id = ""

        if labels is not None and len(labels) > 0:
            labels_name_id = inventory_utils.label_name_id(get_labels().data)

            for label_name in label_names:
                label_id = labels_name_id.get(label_name)
                if label_id is None:
                    raise Exception("Label " + label_name + " not exist")

        while has_next_page:
            variables = templates.DevicePageCursorInput(
                first=device_step, after=last_page_id, labels=label_names
            )
            response = inventory_utils.execute_inventory(templates.device_page_template, variables)

            match response.status:
                case "data":
                    has_next_page = response.data["devices"]["pageInfo"]["hasNextPage"]
                    if response.data["devices"]["pageInfo"]["hasPreviousPage"] is False:
                        last_page_id = ""
                        page_ids.append(last_page_id)
                    if has_next_page is not False:
                        last_page_id = response.data["devices"]["pageInfo"]["endCursor"]
                        page_ids.append(last_page_id)
                    if has_next_page is False:
                        break
                case _:
                    raise Exception(response.data)

        page_loop = {}
        for i in range(ceil(len(page_ids) / cursor_count)):
            page_loop[i] = []
            for j in range(cursor_count):
                try:
                    page_loop[i].append(page_ids[i * cursor_count + j])
                except Exception as e:
                    print(e)
                    break

        return inventory_utils.InventoryOutput(
            data={
                "page_ids": page_loop,
                "page_size": len(page_ids),
                "page_ids_count": len(page_ids),
            },
            status="data",
            code=200,
        )

    except Exception as e:
        print(e.args)
        return inventory_utils.InventoryOutput(data=str(e), status="failed", code=500)


def page_device_dynamic_fork_tasks(
    task: str, page_ids: list[str], labels=None
) -> inventory_utils.InventoryOutput:
    try:
        if len(task) == 0:
            raise Exception("Missing input task name")
        if len(page_ids) == 0 and type(page_ids) is not (str | list[str]):
            raise Exception("Missing input page_ids")
        if type(page_ids) is str:
            page_ids = list(page_ids.replace(" ", "").split(","))

        labels_list = (
            None if labels is None or labels == "" else list(labels.replace(" ", "").split(","))
        )

        if labels_list is not None and len(labels_list) > 0:
            labels_name_id = inventory_utils.label_name_id(get_labels().data)

            for label_name in labels_list:
                label_id = labels_name_id.get(label_name)
                if label_id is None:
                    raise Exception("Label " + label_name + " not exist")

        device_step = 40
        dynamic_tasks = []
        dynamic_tasks_i = {}
        taskReferenceName_id = 0

        for device_id in page_ids:
            task_body = copy.deepcopy(templates.task_body_template)
            task_body["taskReferenceName"] = "devices_page_" + str(taskReferenceName_id)
            task_body["subWorkflowParam"]["name"] = task
            dynamic_tasks.append(task_body)

            per_device_params = dict({})
            per_device_params.update({"page_id": device_id})
            per_device_params.update({"page_size": device_step})
            per_device_params.update({"labels": labels_list})
            dynamic_tasks_i.update({"devices_page_" + str(taskReferenceName_id): per_device_params})
            taskReferenceName_id += 1

        return inventory_utils.InventoryOutput(
            data={"dynamic_tasks_i": dynamic_tasks_i, "dynamic_tasks": dynamic_tasks},
            status="data",
            code=200,
        )

    except Exception as e:
        print(e.args)
        return inventory_utils.InventoryOutput(data=str(e), status="failed", code=500)


def all_devices_fork_tasks(
    task: str, task_params, optional=None, labels=None
) -> inventory_utils.InventoryOutput:
    # TODO validate
    try:
        task_params = (
            json.loads(task_params)
            if isinstance(task_params, str)
            else (task_params if task_params else {})
        )
        optional = False if "optional" in optional else "false"

        labels_list = (
            None if labels is None or labels == "" else list(labels.replace(" ", "").split(","))
        )

        if labels_list is not None and len(labels_list) > 0:
            labels_name_id = inventory_utils.label_name_id(get_labels().data)

            for label_name in labels_list:
                label_id = labels_name_id.get(label_name)
                if label_id is None:
                    raise Exception("Label " + label_name + " not exist")

        ids = inventory_utils.get_all_devices(labels)

        dynamic_tasks = []
        dynamic_tasks_i = {}

        for device in ids:
            device_id = device["node"]["name"]

            task_body = copy.deepcopy(templates.task_body_template)
            if optional == "true":
                task_body["optional"] = True
            task_body["taskReferenceName"] = device_id
            task_body["subWorkflowParam"]["name"] = task
            dynamic_tasks.append(task_body)

            per_device_params = dict(task_params)
            per_device_params.update({"device_id": device_id})
            dynamic_tasks_i.update({device_id: per_device_params})

        return inventory_utils.InventoryOutput(
            data={"dynamic_tasks_i": dynamic_tasks_i, "dynamic_tasks": dynamic_tasks},
            status="data",
            code=200,
        )

    except Exception as e:
        print(e.args)
        return inventory_utils.InventoryOutput(data=str(e), status="failed", code=500)


def install_in_batch(page_size: int, page_id="", labels=None) -> inventory_utils.InventoryOutput:
    try:
        if len(page_size) == 0:
            raise Exception("Missing input task name")
        labels_list = (
            None if labels is None or labels == "" else list(labels.replace(" ", "").split(","))
        )

        if labels_list is not None and len(labels_list) > 0:
            labels_name_id = inventory_utils.label_name_id(get_labels().data)

            for label_name in labels_list:
                label_id = labels_name_id.get(label_name)
                if label_id is None:
                    raise Exception("Label " + label_name + " not exist")

        variables = templates.DevicePageCursorInput(
            first=page_size, after=page_id, labels=labels_list
        )

        response = inventory_utils.execute_inventory(templates.device_page_id_template, variables)

        # TODO check if error propagated to exception

        device_status = {}
        for device_id in response.data["devices"]["edges"]:
            variables = templates.InstallDeviceInput(id=str(device_id["node"]["id"]))

            response = inventory_utils.execute_inventory(
                templates.install_device_template, variables
            )

            per_device_params = dict({})
            per_device_params.update({"device_id": device_id["node"]["id"]})
            per_device_params.update({"device_name": device_id["node"]["name"]})

            match response.status:
                case "data":
                    per_device_params.update({"status": "success"})
                case "errors":
                    if "already been installed" not in response.data[0]["message"]:
                        per_device_params.update({"status": "failed"})
                    elif "already been installed" in response.data[0]["message"]:
                        per_device_params.update({"status": "was installed before"})

            device_status.update({device_id["node"]["name"]: per_device_params})

        return inventory_utils.InventoryOutput(
            data={"response_code": 200, "response_body": device_status}, status="data", code=200
        )

    except Exception as e:
        print(e.args)
        return inventory_utils.InventoryOutput(data=str(e), status="failed", code=500)


def uninstall_in_batch(page_size: int, page_id="", labels=None) -> inventory_utils.InventoryOutput:
    try:
        if not isinstance(page_size, int):
            raise Exception("Missing input page size")
        if not isinstance(page_id, str):
            raise Exception("Missing input page id")

        labels_list = (
            None if labels is None or labels == "" else list(labels.replace(" ", "").split(","))
        )

        if labels_list is not None and len(labels_list) > 0:
            labels_name_id = inventory_utils.label_name_id(get_labels().data)

            for label_name in labels_list:
                label_id = labels_name_id.get(label_name)
                if label_id is None:
                    raise Exception("Label " + label_name + " not exist")

        variables = templates.DevicePageCursorInput(
            first=page_size, after=page_id, labels=labels_list
        )

        response = inventory_utils.execute_inventory(templates.device_page_id_template, variables)

        device_status = {}
        for device_id in response.data["devices"]["edges"]:
            variables = templates.InstallDeviceInput(id=str(device_id["node"]["id"]))

            response = inventory_utils.execute_inventory(
                templates.uninstall_device_template, variables
            )

            per_device_params = dict({})
            per_device_params.update({"device_id": device_id["node"]["id"]})
            per_device_params.update({"device_name": device_id["node"]["name"]})

            match response.status:
                case "data":
                    per_device_params.update({"status": "success"})
                case "errors":
                    if "already been installed" not in response.data[0]["message"]:
                        per_device_params.update({"status": "failed"})
                    elif "already been installed" in response.data[0]["message"]:
                        per_device_params.update({"status": "was installed before"})

            device_status.update({device_id["node"]["name"]: per_device_params})

    except Exception as e:
        print(e.args)
        return inventory_utils.InventoryOutput(data=str(e), status="failed", code=500)
