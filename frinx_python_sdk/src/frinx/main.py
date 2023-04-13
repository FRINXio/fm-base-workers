import logging
import os

from frinx.common.logging import logging_common
from frinx.common.logging.logging_common import LoggerConfig
from frinx.common.logging.logging_common import Root


def debug_local():
    import os

    os.environ["UNICONFIG_URL_BASE"] = "http://localhost/api/uniconfig"
    os.environ["CONDUCTOR_URL_BASE"] = os.environ.get(
        "CONDUCTOR_URL_BASE", "http://localhost:8088/proxy/api"
    )
    os.environ["INVENTORY_URL_BASE"] = "http://localhost/api/inventory"
    os.environ["INFLUXDB_URL_BASE"] = "http://localhost:8086"
    os.environ["RESOURCE_MANAGER_URL_BASE"] = "http://localhost/api/resource"


def register_tasks(conductor_client):
    from frinx.workers.inventory.inventory_worker import Inventory
    from frinx.workers.monitoring.influxdb_workers import Influx
    from frinx.workers.test.test_worker import TestWorker
    from frinx.workers.uniconfig.uniconfig_worker import Uniconfig

    TestWorker().register(conductor_client)
    Inventory().register(conductor_client)
    Uniconfig().register(conductor_client)
    Influx().register(conductor_client)


def register_workflows():
    logging.info("Register workflows")
    from frinx.workflows.inventory.inventory_workflows import InventoryWorkflows
    from frinx.workflows.misc.test import TestForkWorkflow
    from frinx.workflows.misc.test import TestWorkflow
    from frinx.workflows.monitoring.influxdb import InfluxWF
    from frinx.workflows.uniconfig.transactions import UniconfigTransactions

    TestWorkflow().register(overwrite=True)
    TestForkWorkflow().register(overwrite=True)
    UniconfigTransactions().register(overwrite=True)
    InfluxWF().register(overwrite=True)
    InventoryWorkflows().register(overwrite=True)


def main():
    logging_common.configure_logging(
        LoggerConfig(root=Root(level=os.environ.get("LOG_LEVEL", "INFO").upper()))
    )

    debug_local()

    from frinx.client.FrinxConductorWrapper import FrinxConductorWrapper
    from frinx.common.frinx_rest import conductor_headers
    from frinx.common.frinx_rest import conductor_url_base

    conductor_client = FrinxConductorWrapper(
        server_url=conductor_url_base,
        polling_interval=0.1,
        max_thread_count=10,
        headers=conductor_headers,
    )

    register_tasks(conductor_client)
    register_workflows()
    conductor_client.start_workers()


if __name__ == "__main__":
    main()
