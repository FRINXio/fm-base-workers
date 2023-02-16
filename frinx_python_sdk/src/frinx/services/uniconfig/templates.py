import dataclasses
from string import Template
from typing import Any
from typing import Optional

UNICONFIGTXID = "UNICONFIGTXID"


uniconfig_url_uniconfig_mount = Template(
    "$base_url/data/network-topology:network-topology/topology=uniconfig/node=$id"
)
uniconfig_url_uniconfig_commit = Template("$base_url/operations/uniconfig-manager:commit")
uniconfig_url_uniconfig_dryrun_commit = Template(
    "$base_url/operations/dryrun-manager:dryrun-commit"
)
uniconfig_url_uniconfig_calculate_diff = Template(
    "$base_url/operations/uniconfig-manager:calculate-diff"
)
uniconfig_url_uniconfig_sync_from_network = Template(
    "$base_url/operations/uniconfig-manager:sync-from-network"
)
uniconfig_url_uniconfig_replace_config_with_operational = Template(
    "$base_url/operations/uniconfig-manager:replace-config-with-operational"
)
uniconfig_url_uniconfig_tx_create = Template(
    "$base_url/operations/uniconfig-manager:create-transaction"
)
uniconfig_url_uniconfig_tx_close = Template(
    "$base_url/operations/uniconfig-manager:close-transaction"
)
uniconfig_url_uniconfig_tx_revert = Template("$base_url/operations/transaction-log:revert-changes")
uniconfig_url_uniconfig_tx_metadata = Template(
    "$base_url/data/transaction-log:transactions-metadata/transaction-metadata=$tx_id"
)
