import logging

from frinx.common.logging import logging_common


def DebugLocal():
    import os

    os.environ["UNICONFIG_URL_BASE"] = "http://localhost/api/uniconfig"
    os.environ["CONDUCTOR_URL_BASE"] = "http://localhost:8088/proxy/api"
    os.environ["INVENTORY_URL_BASE"] = "http://localhost/api/inventory"
    os.environ["INFLUXDB_URL_BASE"] = "http://localhost:8086"
    os.environ["RESOURCE_MANAGER_URL_BASE"] = "http://localhost/api/resource"


def RegisterTasks(cc):
    from frinx.workers.inventory.inventory_worker import Inventory
    from frinx.workers.monitoring.influxdb_workers import Influx
    from frinx.workers.uniconfig.uniconfig_worker import Uniconfig

    Inventory().register(cc)
    Uniconfig().register(cc)
    Influx().register(cc)


def RegisterWorkflows():
    logging.info("Register workflows")
    from frinx.workflows.inventory.inventory_workflows import InventoryWorkflows
    from frinx.workflows.monitoring.influxdb import InfluxWF
    from frinx.workflows.uniconfig.transactions import UniconfigTransactions

    UniconfigTransactions().register(overwrite=True)
    InfluxWF().register(overwrite=True)
    InventoryWorkflows().register(overwrite=True)


def main():
    logging_common.configure_logging()

    DebugLocal()

    from frinx.client.FrinxConductorWrapper import FrinxConductorWrapper
    from frinx.common.frinx_rest import conductor_headers
    from frinx.common.frinx_rest import conductor_url_base

    cc = FrinxConductorWrapper(
        server_url=conductor_url_base,
        polling_interval=0.5,
        max_thread_count=10,
        headers=conductor_headers,
    )

    RegisterTasks(cc)
    RegisterWorkflows()
    cc.start_workers()


if __name__ == "__main__":
    main()
