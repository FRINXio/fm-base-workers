import os
import requests
import traceback
from frinx_conductor_workers.frinx_rest import conductor_url_base, conductor_headers

workflow_import_url = conductor_url_base + '/metadata/workflow'


def import_workflows(path):
    if os.path.isdir(path):
        print('Importing workflows from folder ' + path)
        with os.scandir(path) as entries:
            for entry in entries:
                if entry.is_file():
                    try:
                        print('Importing workflow ' + entry.name)
                        with open(entry, 'rb') as payload:
                            r = requests.post(workflow_import_url,
                                              data=payload, headers=conductor_headers)
                            print('Response - ' + r.text)
                    except Exception as err:
                        print('Error while registering workflow ' + traceback.format_exc())
                        raise err
                elif entry.is_dir():
                    import_workflows(entry.path)
                else:
                    print('Ignoring, unknown type ' + entry)
    else:
        print('Path to workflows ' + path + ' is not a directory.')