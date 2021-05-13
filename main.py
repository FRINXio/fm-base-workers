import time
import os

from conductor.FrinxConductorWrapper import FrinxConductorWrapper
from frinx_conductor_workers.frinx_rest import conductor_url_base, conductor_headers
from frinx-conductor-workers import cli_worker
from frinx-conductor-workers import netconf_worker
from frinx-conductor-workers import uniconfig_worker
from frinx-conductor-workers import common_worker
from frinx-conductor-workers import http_worker
from frinx-conductor-workers.import_workflows import import_workflows

workflows_folder_path = './workflows'
healtchchek_file_path = './healthcheck'


def main():
    if os.path.exists(healtchchek_file_path):
        os.remove(healtchchek_file_path)

    print('Starting FRINX workers')
    cc = FrinxConductorWrapper(conductor_url_base, 1, 1, headers=conductor_headers)
    cc.start_queue_polling()
    register_workers(cc)
    import_workflows(workflows_folder_path)

    with open(healtchchek_file_path, 'w'): pass




    # block
    while 1:
        time.sleep(1000)


def register_workers(cc):
    cli_worker.start(cc)
    netconf_worker.start(cc)
    uniconfig_worker.start(cc)
    common_worker.start(cc)
    http_worker.start(cc)


if __name__ == '__main__':
    main()
