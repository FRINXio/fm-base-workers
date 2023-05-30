# fm-base-workers

Common repository for Frinx-Machine workflow manager pypi packages.

## frinx_conductor_workers

Base workers and workflows for Frinx-Machine workflow-manager.
https://pypi.org/project/frinx-conductor-workers/

## frinx_python_sdk

Python SDK for Frinx-Machine workflow manager.
Including common workers for services.

### For developers

Before PR is created, format python files

```bash
python -m black .
python -m isort .
```

##### ENV variables
```
UNICONFIG_URL_BASE
ELASTICSEACRH_URL_BASE
CONDUCTOR_URL_BASE
INVENTORY_URL_BASE
INFLUXDB_URL_BASE
RESOURCE_MANAGER_URL_BASE
UNICONFIG_USER
UNICONFIG_PASSWD
X_TENANT_ID
X_FROM
X_AUTH_USER_GROUP
```
e.g.:
Uniconfig host can be configured in env.:```UNICONFIG_URL_BASE=http://uniconfig:8181/rests```

# Conductor system tests grafana dashboard
http://10.19.0.20:3000/public-dashboards/93faf068d01d45289a17ef659795c918
