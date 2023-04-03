import logging
import os

from frinx.common.logging import logging_common
from frinx.common.logging.logging_common import LoggerConfig
from frinx.common.logging.logging_common import Root


def DebugLocal():
    import os

    os.environ["UNICONFIG_URL_BASE"] = "http://localhost/api/uniconfig"
    os.environ["CONDUCTOR_URL_BASE"] = os.environ.get(
        "CONDUCTOR_URL_BASE", "http://localhost:8088/proxy/api"
    )
    os.environ["INVENTORY_URL_BASE"] = "http://localhost/api/inventory"
    os.environ["INFLUXDB_URL_BASE"] = "http://localhost:8086"
    os.environ["RESOURCE_MANAGER_URL_BASE"] = "http://localhost/api/resource"


def RegisterTasks(cc):
    from frinx.workers.inventory.inventory_worker import Inventory
    from frinx.workers.monitoring.influxdb_workers import Influx
    from frinx.workers.test.test_worker import TestWorker
    from frinx.workers.uniconfig.uniconfig_worker import Uniconfig

    TestWorker().register(cc)
    Inventory().register(cc)
    Uniconfig().register(cc)
    Influx().register(cc)


def RegisterWorkflows():
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

    DebugLocal()

    from frinx.client.FrinxConductorWrapper import FrinxConductorWrapper
    from frinx.common.frinx_rest import conductor_headers
    from frinx.common.frinx_rest import conductor_url_base

    cc = FrinxConductorWrapper(
        server_url=conductor_url_base,
        polling_interval=0.1,
        max_thread_count=10,
        headers=conductor_headers,
    )

    RegisterTasks(cc)
    RegisterWorkflows()
    cc.start_workers()


if __name__ == "__main__":
    main()
