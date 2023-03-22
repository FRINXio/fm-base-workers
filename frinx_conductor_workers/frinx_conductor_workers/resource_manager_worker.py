import ipaddress
import json
import logging
import os

from frinx_conductor_workers.frinx_rest import conductor_headers
from frinx_conductor_workers.frinx_rest import resource_manager_url_base
from frinx_conductor_workers.logging_helpers import logging_handler
from frinx_conductor_workers.util import completed_response_with_logs
from frinx_conductor_workers.util import failed_response_with_logs
from jinja2 import Template
from python_graphql_client import GraphqlClient

log = logging.getLogger(__name__)

client = GraphqlClient(endpoint=resource_manager_url_base, headers=conductor_headers)

claim_resource_template = Template(
    """
    mutation ClaimResource($pool_id: ID!, $description: String!, $user_input: Map!{{ alternative_id_variable }}) {
    {{ claim_resource }}(
        poolId: $pool_id,
        description: $description,
        userInput: $user_input{{ alternative_id }})
    {
        id
        Properties
        AlternativeId
    }
    }"""
)

create_pool_template = Template(
    """
    mutation CreatePool($pool_name: String!, $resource_type_id: ID!, $resource_type_strat_id: ID!,{{ pool_properties_variables }}) {
    {{ create_pool }}(
        input: {
            resourceTypeId: $resource_type_id,
            poolName: $pool_name,
            allocationStrategyId: $resource_type_strat_id,
            poolDealocationSafetyPeriod: 0,
            {{ pool_properties_types }},
            {{ pool_properties }},
            {{ parent_resource_id }},
            tags: [$pool_name],
        }
    ) {
        pool { id }
    }
    }"""
)

query_pool_template = Template(
    """
    query QueryPool($resource_type_id: ID!) {
    QueryResourcePools(
        tags: { matchesAny: [
            { matchesAll: [{{ pool_names }}] }
            ]
        },
        resourceTypeId: $resource_type_id)
    {
        id
    }
    }"""
)

query_resource_template = Template(
    """
    query QueryId($resource: String) {
    QueryResourceTypes(byName: $resource) {
        id   
    }
    QueryAllocationStrategies(byName: $resource) {
        id
    }
    }"""
)

query_pool_by_tag_template = Template(
    """
    query SearchPools($poolTag: String!) {
    SearchPoolsByTags(tags: { matchesAny: [{matchesAll: [$poolTag]}]}) {
        id
        AllocationStrategy {Name}
        Name
        PoolProperties
    }
    } """
)

query_claimed_resource_template = Template(
    """
    query QueryClaimedResource($pool_id: ID!,{{ input_variable }}) {
    {{ query_resource }}(
        poolId: $pool_id,
        {{ input }})
    {
        edges {
            cursor {
                ID
            }
            node {
                id
                Properties
                ParentPool {
                    id
                    Name
                }
                NestedPool {
                    id
                    Name
                    Tags{
                        Tag
                    }
                }
                AlternativeId
                }
            }
        }
    }"""
)

update_alternative_id_for_resource_template = Template(
    """
    mutation UpdateResourceAltId($pool_id: ID!, $input: Map!, $alternative_id: Map!) {
        {{ update_alt_id }}(
        poolId: $pool_id, input: $input, alternativeId: $alternative_id) {
            AlternativeId
        }
    }
    """
)

create_nested_pool_template = Template(
    """
    mutation CreateNestedAllocPool($pool_name: String!, $resource_type_id: ID!, $resource_type_strat_id: ID!, $parentResourceId: ID!) {
        CreateNestedAllocatingPool(
            input: {
                resourceTypeId: $resource_type_id,
                poolName: $pool_name,
                allocationStrategyId: $resource_type_strat_id,
                poolDealocationSafetyPeriod: 0
                parentResourceId: $parentResourceId,
                tags: [$pool_name]
           }
    ) {
        pool { id , PoolProperties }
    }
    }"""
)

query_capacity_template = Template(
    """
    query QueryPoolCapacity($pool_id: ID!) {
    QueryPoolCapacity(poolId: $pool_id) {
        freeCapacity
        utilizedCapacity
    }
    }"""
)

query_resource_by_alt_id_template = Template(
    """
    query QueryResourcesByAltId($poolId: ID, $input: Map!, $first: Int, $last: Int, $after: String, $before: String) {
    QueryResourcesByAltId(input: $input, poolId: $poolId, first: $first, last: $last, after: $after, before: $before) {
        edges {
            cursor {
                ID
            }
            node {
                id
                Properties
                ParentPool {
                    id
                    Name
                }
                NestedPool {
                    id
                    Name
                    Tags{
                        Tag
                    }
                }
                AlternativeId
            }
        }
    }
    } """
)

deallocate_resource_template = Template(
    """
    mutation freeResource($pool_id: ID!, $input: Map!) {
    FreeResource(
        poolId: $pool_id,
        input: $input
    )
    }"""
)

delete_pool_template = Template(
    """
    mutation deleteResourcePool ($pool_id: ID!) {
    DeleteResourcePool(
        input: {
            resourcePoolId: $pool_id
        }
    ) {
        resourcePoolId
    }
    }"""
)

query_search_empty_pools_template = Template(
    """
    query getEmptyPools($resourceTypeId: ID) {
    QueryEmptyResourcePools(resourceTypeId: $resourceTypeId) {
        id
        Name
        Tags {
            Tag
        }
        AllocationStrategy {
            Name        
        }    
    }
    }"""
)

query_recently_active_resources_template = Template(
    """
    query QueryRecentlyActiveResources($fromDatetime: String!, $toDatetime: String, $first: Int, $last: Int, $before: String, $after: String) {
    QueryRecentlyActiveResources(fromDatetime:$fromDatetime, toDatetime:$toDatetime, first:$first, last:$last, before:$before, after:$after){
        edges {
            node {        
                id
                Properties
                AlternativeId
                ParentPool {
                    id
                    Name
                } 
                NestedPool {
                id                    
                Name
                } 
            }
            cursor{
                ID
            }
        }
    }
    }
    """
)


def execute(body, variables):
    return client.execute(query=body, variables=variables)


@logging_handler(log)
def claim_resource(task, logs):
    """
    Claim resource from Uniresource
    Claim resource can use two types of claims: ClaimResource, ClaimResourceWithAltId.
    For using ClaimResourceWithAltId you have to fill alternativeId in input data

         Args:

             task (dict): dictionary with input data ["poolId", "userInput", "description", "alternativeId"]

             logs: stream of log messages

        Returns:
            Response from uniresource. Worker output format::
            "result": {
              "data": {
                "<claim_operation>": {
                  "id": "<id>",
                  "Properties": {
                    <properties>
                  }
                  "AlternativeId": {
                    <alternativeId>
                  }
                }
              }
            }

    """
    pool_id = task["inputData"]["poolId"] if "poolId" in task["inputData"] else None
    if pool_id is None:
        return failed_response_with_logs(logs, {"result": {"error": "No pool id"}})
    user_input = task["inputData"]["userInput"] if "userInput" in task["inputData"] else {}
    description = task["inputData"]["description"] if "description" in task["inputData"] else ""
    alternative_id = (
        None if "alternativeId" not in task["inputData"] else task["inputData"]["alternativeId"]
    )
    variables = {"pool_id": pool_id, "user_input": user_input, "description": description}

    if alternative_id is not None and len(alternative_id) > 0:
        if "status" not in alternative_id:
            alternative_id.update({"status": "active"})
        variables.update({"alternative_id": alternative_id})
        body = claim_resource_template.render(
            {
                "claim_resource": "ClaimResourceWithAltId",
                "alternative_id_variable": ", $alternative_id: Map!",
                "alternative_id": ", alternativeId: $alternative_id",
            }
        )
    else:
        body = claim_resource_template.render(
            {"claim_resource": "ClaimResource", "alternative_id_variable": "", "alternative_id": ""}
        )

    log.debug("Sending graphql variables: %s\n with query: %s" % (variables, body))
    response = execute(body, variables)
    if "errors" in response:
        return failed_response_with_logs(
            logs, {"result": {"error": response["errors"][0]["message"]}}
        )
    return completed_response_with_logs(logs, {"result": response})


@logging_handler(log)
def query_claimed_resources(task, logs):
    """
    Query claimed resources from Uniresource
    Query resource can use two types of claims: QueryResources, QueryResourceWithAltId.
    For using QueryResourceWithAltId you have to fill alternativeId in input data

         Args:

             task (dict): dictionary with input data ["poolId", "alternativeId"]

             logs: stream of log messages

        Returns:
            Response from uniresource. Worker output format::
            "result": {
              "data": {
                "<query_type>": {
                    edges [
                        cursor {
                            <ID>
                        }
                        node {
                          "id": "<id>",
                          "Properties": {
                            <properties>
                          }
                          ParentPool {
                            <id>
                            <Name>
                          }
                          NestedPool {
                            <id>
                            <Name>
                            Tags {
                                <Tag>
                            }
                          }
                          "AlternativeId": {
                            <alternativeId>
                          }
                        }
                    ]
                }
              }
            }

    """
    pool_id = task["inputData"]["poolId"] if "poolId" in task["inputData"] else None
    alternative_id = (
        None if "alternativeId" not in task["inputData"] else task["inputData"]["alternativeId"]
    )
    if pool_id is None:
        return failed_response_with_logs(logs, {"result": {"error": "No pool id"}})
    variables = {"pool_id": pool_id}
    if alternative_id is not None and len(alternative_id) > 0:
        variables.update({"alternative_id": alternative_id})
        body = query_claimed_resource_template.render(
            {
                "query_resource": "QueryResourcesByAltId",
                "input": "input: $input",
                "input_variable": "$input: Map!",
            }
        )
        variables.update({"input": alternative_id})
    else:
        body = query_claimed_resource_template.render({"query_resource": "QueryResources"})
    log.debug("Sending graphql variables: %s\n with query: %s" % (variables, body))
    response = execute(body, variables)
    if "errors" in response:
        return failed_response_with_logs(
            logs, {"result": {"error": response["errors"][0]["message"]}}
        )
    return completed_response_with_logs(logs, {"result": response})


def query_resource_id(resource):
    # Query resource type and resource allocation strategy id from uniresource
    body = query_resource_template.render()
    variables = {"resource": resource}
    body = body.replace("\n", "").replace("\\", "")
    log.debug("Sending graphql variables: %s\n with query: %s" % (variables, body))
    data = execute(body, variables)
    resource_type_id = (
        data["data"]["QueryResourceTypes"][0]["id"] if data["data"]["QueryResourceTypes"] else None
    )
    resource_strategy_id = (
        data["data"]["QueryAllocationStrategies"][0]["id"]
        if data["data"]["QueryAllocationStrategies"]
        else None
    )
    return resource_type_id, resource_strategy_id


@logging_handler(log)
def create_pool(task, logs):
    """
    Create pool id in Uniresource

         Args:

             task (dict): dictionary with input data ["resource", "poolName", "poolProperties"]

             logs: stream of log messages

        Returns:
            Response from uniresource. Worker output format::
            "result": {
              "data": {
                "CreateAllocatingPool": {
                  "pool": {
                    "id": "<id>"
                  }
                }
              }
            }

    """

    pool_name = task["inputData"]["poolName"]
    resource_type = task["inputData"]["resourceType"]
    resource_type_id, resource_strategy_id = query_resource_id(resource_type)
    if resource_type_id is None or resource_strategy_id is None:
        log.warning("Unknown resource: %s", resource_type)
        return failed_response_with_logs(logs, {"result": {"error": "Unknown resource"}})

    variables = {
        "resource_type_id": resource_type_id,
        "resource_type_strat_id": resource_strategy_id,
        "pool_name": pool_name,
    }
    pool_types_string, pool_string, pool_variables_string = "", "", ""
    if task["inputData"]["poolProperties"]:
        pool_properties = task["inputData"]["poolProperties"]
        for index, key in enumerate(pool_properties.keys()):
            variable_type = type(pool_properties[key])
            property_variable = ""
            if variable_type is str:
                variable_type = "string"
                property_variable = "String!"
            elif variable_type is dict:
                variable_type = "map"
                property_variable = "Map!"
            elif variable_type is int:
                variable_type = "int"
                property_variable = "ID!"
            elif variable_type is bool:
                variable_type = "bool"
                property_variable = "Boolean"
            pool_types_string += key + ': "' + variable_type + '"'
            pool_variables_string += "$" + key + ": " + property_variable
            pool_string += key + ": $" + key
            if index < len(pool_properties.keys()) - 1:
                pool_string += ",\n"
                pool_types_string += ",\n"
                pool_variables_string += ", "
            variables.update({key: pool_properties[key]})

    body = create_pool_template.render(
        {
            "create_pool": "CreateAllocatingPool",
            "pool_properties_types": "poolPropertyTypes: {\n" + pool_types_string + "\n}",
            "pool_properties": "poolProperties: {\n" + pool_string + "\n}",
            "pool_properties_variables": pool_variables_string,
        }
    )
    body = body.replace("\n", "").replace("\\", "")

    log.debug("Sending graphql variables: %s\n with query: %s" % (variables, body))
    response = execute(body, variables)
    if "errors" in response:
        return failed_response_with_logs(
            logs, {"result": {"error": response["errors"][0]["message"]}}
        )
    return completed_response_with_logs(logs, {"result": response})


@logging_handler(log)
def create_vlan_pool(task, logs):
    """
    Create vlan pool in Uniresource
    Args:

         task (dict): dictionary with input data ["poolName", "from", "to", "parent_resource_id"]

         logs: stream of log messages
    """
    pool_name = task["inputData"]["poolName"]
    from_range = task["inputData"]["from"] if "from" in task["inputData"] else None
    to_range = task["inputData"]["to"] if "to" in task["inputData"] else None
    parent_resource_id = (
        task["inputData"]["parentResourceId"] if "parentResourceId" in task["inputData"] else None
    )
    if parent_resource_id == "":
        parent_resource_id = None

    resource_type_id, resource_strategy_id = query_resource_id("vlan")
    variables = {
        "pool_name": pool_name,
        "resource_type_id": resource_type_id,
        "resource_type_strat_id": resource_strategy_id,
        "from": int(from_range) if from_range else from_range,
        "to": int(to_range) if to_range else to_range,
    }

    if parent_resource_id is not None:
        body = create_pool_template.render(
            {
                "create_pool": "CreateNestedAllocatingPool",
                "parent_resource_id": 'parentResourceId: "' + str(parent_resource_id) + '"',
            }
        )
    else:
        body = create_pool_template.render(
            {
                "create_pool": "CreateAllocatingPool",
                "pool_properties_variables": " $from: Int!, $to: Int!",
                "pool_properties_types": 'poolPropertyTypes:{ from: "int", to: "int"}',
                "pool_properties": "poolProperties:{ from: $from, to: $to }",
            }
        )
    log.debug("Sending graphql variables: %s\n with query: %s" % (variables, body))
    response = execute(body, variables)
    if "errors" in response:
        return failed_response_with_logs(
            logs, {"result": {"error": response["errors"][0]["message"]}}
        )
    return completed_response_with_logs(logs, {"result": response})


@logging_handler(log)
def create_vlan_range_pool(task, logs):
    """
    Create vlan range pool in Uniresource
    Args:

         task (dict): dictionary with input data ["poolName", "from", "to"]

         logs: stream of log messages
    """
    pool_name = task["inputData"]["poolName"]
    from_range = task["inputData"]["from"]
    to_range = task["inputData"]["to"]

    resource_type_id, resource_strategy_id = query_resource_id("vlan_range")
    variables = {
        "pool_name": pool_name,
        "resource_type_id": resource_type_id,
        "resource_type_strat_id": resource_strategy_id,
        "from": int(from_range) if from_range else from_range,
        "to": int(to_range) if to_range else to_range,
    }

    body = create_pool_template.render(
        {
            "create_pool": "CreateAllocatingPool",
            "pool_properties_variables": " $from: Int!, $to: Int!",
            "pool_properties_types": 'poolPropertyTypes:{ from: "int", to: "int"}',
            "pool_properties": "poolProperties:{ from: $from, to: $to }",
        }
    )
    log.debug("Sending graphql variables: %s\n with query: %s" % (variables, body))
    response = execute(body, variables)
    if "errors" in response:
        return failed_response_with_logs(
            logs, {"result": {"error": response["errors"][0]["message"]}}
        )
    return completed_response_with_logs(logs, {"result": response})


@logging_handler(log)
def create_unique_id_pool(task, logs):
    """
    Create vlan range pool in Uniresource
    Args:

         task (dict): dictionary with input data ["poolName", "idFormat"]

         logs: stream of log messages
    """
    pool_name = task["inputData"]["poolName"]
    id_format = task["inputData"]["idFormat"]
    from_value = task["inputData"]["from"] if "from" in task["inputData"] else None
    if from_value == "":
        from_value = None

    to_value = task["inputData"]["to"] if "to" in task["inputData"] else None
    if to_value == "":
        to_value = None

    resource_type_id, resource_strategy_id = query_resource_id("unique_id")
    variables = {
        "resource_type_id": resource_type_id,
        "resource_type_strat_id": resource_strategy_id,
        "pool_name": pool_name,
    }

    to_poperty_type = ', to: "int"' if to_value is not None else ""
    to_poperty = ", to: " + str(to_value) if to_value is not None else ""

    from_poperty_type = ', from: "int"' if from_value is not None else ""
    from_poperty = ", from: " + str(from_value) if from_value is not None else ""

    body = create_pool_template.render(
        {
            "create_pool": "CreateAllocatingPool",
            "pool_properties_types": 'poolPropertyTypes:{ idFormat: "string"'
            + from_poperty_type
            + to_poperty_type
            + "}",
            "pool_properties": 'poolProperties:{ idFormat: "'
            + id_format
            + '"'
            + from_poperty
            + to_poperty
            + "}",
        }
    )
    log.debug("Sending graphql variables: %s\n with query: %s" % (variables, body))
    response = execute(body, variables)
    if "errors" in response:
        return failed_response_with_logs(
            logs, {"result": {"error": response["errors"][0]["message"]}}
        )
    return completed_response_with_logs(logs, {"result": response})


@logging_handler(log)
def query_pool(task, logs):
    """
    Query pool id in Uniresource

         Args:

             task (dict): dictionary with input data ["poolNames", "resourceTypeId"]

             logs: stream of log messages

        Returns:
            Response from uniresource. Worker output format::
            "result":{
              "data": {
                "QueryResourcePools": [
                  {
                    "id": "<id>"
                  }
                ]
              }
            }

    """
    pool_names = task["inputData"]["poolNames"]
    if type(pool_names) == str:
        pool_names = [name.strip() for name in pool_names.split(",")]
    resource = task["inputData"]["resource"]
    resource_type_id, resource_strategy_id = query_resource_id(resource)
    if resource_type_id is None or resource_strategy_id is None:
        log.warning("Unknown resource: %s", resource)
        return failed_response_with_logs(logs, {"result": {"error": "Unknown resource"}})
    pool_names_string = ""
    for index, pool_name in enumerate(pool_names):
        pool_names_string += '"' + pool_name + '"'
        if index < len(pool_names) - 1:
            pool_names_string += ", "
    variables = {"resource_type_id": resource_type_id}
    body = query_pool_template.render({"pool_names": pool_names_string})
    log.debug("Sending graphql variables: %s\n with query: %s" % (variables, body))
    response = execute(body, variables)
    if "errors" in response:
        return failed_response_with_logs(
            logs, {"result": {"error": response["errors"][0]["message"]}}
        )
    return completed_response_with_logs(logs, {"result": response})


@logging_handler(log)
def query_unique_id_pool(task, logs):
    """
    Query Unique id pool in Uniresource

         Args:

             task (dict): dictionary with input data ["poolNames"]

             logs: stream of log messages

    """
    pool_names = task["inputData"]["poolNames"]
    query_pool_result = query_pool(
        {"inputData": {"resource": "unique_id", "poolNames": pool_names}}
    )
    return completed_response_with_logs(logs, {"result": query_pool_result["output"]["result"]})


@logging_handler(log)
def query_vlan_pool(task, logs):
    """
    Query Vlan pool in Uniresource

         Args:

             task (dict): dictionary with input data ["poolNames"]

             logs: stream of log messages

    """
    pool_names = task["inputData"]["poolNames"]
    query_pool_result = query_pool({"inputData": {"resource": "vlan", "poolNames": pool_names}})
    return completed_response_with_logs(logs, {"result": query_pool_result["output"]["result"]})


@logging_handler(log)
def query_pool_by_tag(task, logs):
    """
    Query pool by tag in Uniresource

         Args:

             task (dict): dictionary with input data ["poolTag"]


         Returns:
            Response from uniresource. Worker output format::
            "result": {
                "data": {
                    "SearchPoolsByTags": [
                        {
                            "id": "<id>",
                            "AllocationStrategy": <Name>
                            "Name": "<name>"
                            "PoolProperties": <PoolProperties>
                        }
                    ]
                }
            }

    """
    pool_tag = task["inputData"]["poolTag"]
    body = query_pool_by_tag_template.render()
    variables = {"poolTag": pool_tag}
    body = body.replace("\n", "").replace("\\", "")
    log.debug("Sending graphql variables: %s\n with query: %s" % (variables, body))
    response = execute(body, variables)
    if "errors" in response:
        return failed_response_with_logs(
            logs, {"result": {"error": response["errors"][0]["message"]}}
        )
    return completed_response_with_logs(logs, {"result": response})


@logging_handler(log)
def query_vlan_range_pool(task, logs):
    """
    Query Vlan range pool in Uniresource

         Args:

             task (dict): dictionary with input data ["poolNames"]

             logs: stream of log messages

    """
    pool_names = task["inputData"]["poolNames"]
    query_pool_result = query_pool(
        {"inputData": {"resource": "vlan_range", "poolNames": pool_names}}
    )
    return completed_response_with_logs(logs, {"result": query_pool_result["output"]["result"]})


@logging_handler(log)
def update_alt_id_for_resource(task, logs):
    """
    Update alternative id for resource from Uniresource

         Args:

             task (dict): dictionary with input data ["poolId", "resourceProperties", "alternativeId"]

             logs: stream of log messages

        Returns:
            Response from Uniresource. Worker output format::
            "result": {
              "data": {
                "UpdateResourceAltId": {
                  "AlternativeId": {
                    <alternativeId>
                  }
                }
              }
            }

    """
    pool_id = task["inputData"]["poolId"] if "poolId" in task["inputData"] else None
    if pool_id is None:
        return failed_response_with_logs(logs, {"result": {"error": "No pool id"}})
    resource_properties = (
        task["inputData"]["resourceProperties"]
        if "resourceProperties" in task["inputData"]
        else None
    )
    if resource_properties is None:
        return failed_response_with_logs(logs, {"result": {"error": "No user input"}})
    alternative_id = (
        task["inputData"]["alternativeId"] if "alternativeId" in task["inputData"] else None
    )
    if alternative_id is None:
        return failed_response_with_logs(logs, {"result": {"error": "No alternative id"}})
    variables = {"pool_id": pool_id, "input": resource_properties, "alternative_id": alternative_id}
    if alternative_id is not None and len(alternative_id) > 0:
        variables.update({"alternative_id": alternative_id})
    if resource_properties is not None and len(resource_properties) > 0:
        variables.update({"input": resource_properties})
    body = update_alternative_id_for_resource_template.render(
        {"update_alt_id": "UpdateResourceAltId"}
    )
    log.debug("Sending graphql variables: %s\n with query: %s" % (variables, body))
    response = execute(body, variables)
    if "errors" in response:
        return failed_response_with_logs(
            logs, {"result": {"error": response["errors"][0]["message"]}}
        )
    return completed_response_with_logs(logs, {"result": response})


@logging_handler(log)
def read_x_tenant(task, logs):
    """
    Read X_TENANT_ID variable and return as a string.
    Fail if X_TENANT_ID is not found.
    """

    if "X_TENANT_ID" not in os.environ:
        return failed_response_with_logs(
            logs, {"result": {"error": "X_TENANT_ID not found in the environment"}}
        )
    return completed_response_with_logs(
        logs, {"result": {"data": {"X_TENANT_ID": os.environ["X_TENANT_ID"]}}}
    )


@logging_handler(log)
def read_resource_manager_url_base(task, logs):
    """
    Read resource_manager_base variable and return as a string.
    """

    return completed_response_with_logs(
        logs, {"result": {"data": {"RESOURCE_MANAGER_URL_BASE": resource_manager_url_base}}}
    )


@logging_handler(log)
def accumulate_report(task, logs):
    """
    Accumulate one report from two reports

         Args:

             task (dict): dictionary with input data ["first_report", "last_report"]

             logs: stream of log messages

        Returns:
            Accumulated subnets from 2 input reports:
            "result":{"data": "/24":"2","/25":"4","/26":"8","/27":"16","/28":"32","/29":"64","/30":"128","/31":"256","/32":"512"}}
    """
    first_report = task["inputData"]["firstReport"]
    last_report = task["inputData"]["lastReport"]
    global_report = dict()

    if first_report:
        if len(first_report) < len(last_report):
            for key, value in last_report.items():
                if key not in first_report.keys():
                    global_report[key] = int(value)
                elif key in first_report.keys():
                    values = int(value) + int(first_report[key])
                    global_report.update({key: str(values)})
        else:
            for key, value in first_report.items():
                if key not in last_report.keys():
                    global_report[key] = int(value)
                elif key in last_report.keys():
                    values = int(value) + int(last_report[key])
                    global_report.update({key: str(values)})
    else:
        global_report = last_report
    return completed_response_with_logs(logs, {"result": {"data": global_report}})


@logging_handler(log)
def calculate_available_prefixes_for_address_pool(task, logs):
    """
    Calculate available prefixes for address pool

         Args:

             task (dict): dictionary with input data ["free_capacity", "resource_type"]

             logs: stream of log messages
        Returns:
            "result":{"data": "/24":"1","/25":"2","/26":"4","/27":"8","/28":"16","/29":"32","/30":"64","/31":"128","/32":"256"}}
    """
    pool_id = task["inputData"]["poolId"]
    resource_type = str(task["inputData"]["resourceType"])

    available_prefixes = {}
    free_capacity = query_capacity(pool_id)

    if resource_type.startswith("ipv4"):
        for prefix in range(1, 33):
            prefix_capacity = 2 ** (32 - prefix)
            if prefix_capacity <= int(free_capacity[0]):
                result = int(free_capacity[0]) // prefix_capacity
                available_prefixes["/" + str(prefix)] = str(result)
    elif resource_type.startswith("ipv6"):
        for prefix in range(1, 129):
            prefix_capacity = 2 ** (128 - prefix)
            if prefix_capacity <= int(free_capacity[0]):
                result = int(free_capacity[0]) // prefix_capacity
                available_prefixes["/" + str(prefix)] = str(result)

    return completed_response_with_logs(logs, {"result": {"data": available_prefixes}})


@logging_handler(log)
def create_nested_pool(task, logs):
    """
    Create nested pool

         Args:

             task (dict): dictionary with input data ["poolName", "resourceType", "parentResourceId"]

             logs: stream of log messages

        Returns:
            Response from uniresource. Worker output format::
            "result": {
              "data": {
                "CreateNestedAllocatingPool": {
                  "pool": {
                    "id": "<id>"
                    "PoolProperties": <PoolProperties>
                  }
                }
              }
            }

    """

    pool_name = task["inputData"]["poolName"]
    resource_type = task["inputData"]["resourceType"]
    parent_resource_id = task["inputData"]["parentResourceId"]
    resource_type_id, resource_strategy_id = query_resource_id(resource_type)
    if resource_type_id is None or resource_strategy_id is None:
        log.warning("Unknown resource: %s", resource_type)
        return failed_response_with_logs(logs, {"result": {"error": "Unknown resource"}})

    variables = {
        "resource_type_id": resource_type_id,
        "resource_type_strat_id": resource_strategy_id,
        "pool_name": pool_name,
        "parentResourceId": parent_resource_id,
    }

    body = create_nested_pool_template.render()
    body = body.replace("\n", "").replace("\\", "")

    log.debug("Sending graphql variables: %s\n with query: %s" % (variables, body))
    response = execute(body, variables)
    if "errors" in response:
        return failed_response_with_logs(
            logs, {"result": {"error": response["errors"][0]["message"]}}
        )
    return completed_response_with_logs(logs, {"result": response})


def query_capacity(pool_id):
    # Query free capacity and utilized capacity from pool
    body = query_capacity_template.render()
    variables = {"pool_id": pool_id}
    log.debug("Sending graphql variables: %s\n with query: %s" % (variables, body))
    data = execute(body, variables)
    log.info(data)
    free_capacity = (
        data["data"]["QueryPoolCapacity"]["freeCapacity"]
        if data["data"]["QueryPoolCapacity"]
        else None
    )
    utilized_capacity = (
        data["data"]["QueryPoolCapacity"]["utilizedCapacity"]
        if data["data"]["QueryPoolCapacity"]
        else None
    )
    return free_capacity, utilized_capacity


@logging_handler(log)
def query_resource_by_alt_id(task, logs):
    """
    Query resource by alternative id in Uniresource
         Args:
             task (dict): dictionary with input data ["alternativeId"] and optional data ["poolId", "first"]
         Returns:
            Response from uniresource. Worker output format::
            "result": {
                "data": {
                    "QueryResourcesByAltId": {
                        "edges": [
                        {
                            "id": "<id>",
                            "Properties": <Properties>,
                            "Description": "<description>"
                        }
                        ]
                    }
                }
            }

    """
    alternative_id = task["inputData"]["alternativeId"]
    pool_id = task["inputData"]["poolId"] if "poolId" in task["inputData"] else None
    first = task["inputData"]["first"] if "first" in task["inputData"] else None
    last = task["inputData"]["last"] if "last" in task["inputData"] else None
    after = task["inputData"]["after"] if "after" in task["inputData"] else None
    before = task["inputData"]["before"] if "before" in task["inputData"] else None
    if (after is not None) and (before is not None):
        return failed_response_with_logs(
            logs,
            {
                "result": {
                    "error": "Data cannot be extracted with the parameter after and before at the same request"
                }
            },
        )
    body = query_resource_by_alt_id_template.render()
    alternative_id = json.loads(alternative_id)
    variables = {
        "input": alternative_id,
        "poolId": pool_id,
        "first": first,
        "last": last,
        "after": after,
        "before": before,
    }
    body = body.replace("\n", "").replace("\\", "")
    log.info("Sending graphql variables: %s\n with query: %s" % (variables, body))
    response = execute(body, variables)
    if "errors" in response:
        return failed_response_with_logs(
            logs, {"result": {"error": response["errors"][0]["message"]}}
        )
    return completed_response_with_logs(logs, {"result": response})


@logging_handler(log)
def deallocate_resource(task, logs):
    """
    Deallocate resource from pool

         Args:

             task (dict): dictionary with input data ["poolId", "userInput", "alternativeId"]

             logs: stream of log messages

        Returns:
            Response from Uniresource. Worker output format:
            "result": {
              "data": {
                "FreeResorce": "Resource freed successfully"
                }
              }
            }

    """
    pool_id = task["inputData"]["poolId"] if "poolId" in task["inputData"] else None
    if pool_id is None:
        return failed_response_with_logs(logs, {"result": {"error": "No pool id"}})
    user_input = task["inputData"]["userInput"] if "userInput" in task["inputData"] else None
    if user_input is None:
        return failed_response_with_logs(logs, {"result": {"error": "No user input"}})
    variables = {"pool_id": pool_id, "input": user_input}
    body = deallocate_resource_template.render()

    log.debug("Sending graphql variables: %s\n with query: %s" % (variables, body))
    response = execute(body, variables)
    if "errors" in response:
        return failed_response_with_logs(
            logs, {"result": {"error": response["errors"][0]["message"]}}
        )
    return completed_response_with_logs(logs, {"result": response})


@logging_handler(log)
def delete_pool(task, logs):
    """
    Delete pool

         Args:

             task (dict): dictionary with input data ["poolId"]

             logs: stream of log messages

        Returns:
            Response from Uniresource. Worker output format::
            "result": {
              "data": {
                "DeleteResourcePool": {
                  "resourcePoolId: "<id>"
                }
              }
            }

    """
    pool_id = task["inputData"]["poolId"] if "poolId" in task["inputData"] else None
    if pool_id is None:
        return failed_response_with_logs(logs, {"result": {"error": "No pool id"}})
    variables = {"pool_id": pool_id}
    body = delete_pool_template.render()

    log.debug("Sending graphql variables: %s\n with query: %s" % (variables, body))
    response = execute(body, variables)
    if "errors" in response:
        return failed_response_with_logs(
            logs, {"result": {"error": response["errors"][0]["message"]}}
        )
    return completed_response_with_logs(logs, {"result": response})


@logging_handler(log)
def calculate_host_and_broadcast_address(task, logs):
    """
    Calculate host and broadcast address from customer and provider ip address, if those ip addresses are not defined, it will calculate even these

         Args:

             task (dict): dictionary with input data ["desired_size", "resource_type"] and optional ["customer_address", "provider_address"]

             logs: stream of log messages
        Returns:
            "result":{
                "data": {
                    "network_address": <network_address>
                    "broadcast_address": <broadcast_address>
                    "address_capacity_in_subnet": <desiredSize>
                    "owner_of_lower_address": <print_lower_address>
                    "owner_of_higher_address": <print_higher_address>
                    "lower_address": <lower_address>
                }
            }
    """
    desired_size = task["inputData"]["desiredSize"]
    resource_type = str(task["inputData"]["resourceType"])
    customer_ip_address = (
        str(task["inputData"]["customerAddress"])
        if "customerAddress" in task["inputData"]
        else None
    )
    provider_ip_address = (
        str(task["inputData"]["providerAddress"])
        if "providerAddress" in task["inputData"]
        else None
    )
    network_ip_address = (
        str(task["inputData"]["networkAddress"]) if "networkAddress" in task["inputData"] else None
    )

    if network_ip_address is not None and (
        customer_ip_address is None or provider_ip_address is None
    ):
        provider_ip_address, customer_ip_address = calculate_provider_and_customer_address(
            network_ip_address, resource_type
        )
    if resource_type.startswith("ipv4"):
        customer_converted_ip_address = int(ipaddress.IPv4Address(customer_ip_address))
        provider_converted_ip_address = int(ipaddress.IPv4Address(provider_ip_address))
        if customer_converted_ip_address < provider_converted_ip_address:
            response = calculate_network_address_from_lower_address(
                "Customer",
                "Provider",
                customer_ip_address,
                customer_converted_ip_address,
                int(desired_size),
            )
        else:
            response = calculate_network_address_from_lower_address(
                "Provider",
                "Customer",
                provider_ip_address,
                provider_converted_ip_address,
                int(desired_size),
            )
    elif resource_type.startswith("ipv6"):
        customer_converted_ip_address = int(ipaddress.IPv6Address(customer_ip_address))
        provider_converted_ip_address = int(ipaddress.IPv6Address(provider_ip_address))
        if customer_converted_ip_address < provider_converted_ip_address:
            response = calculate_network_address_from_lower_address(
                "Customer",
                "Provider",
                customer_ip_address,
                customer_converted_ip_address,
                int(desired_size),
            )
        else:
            response = calculate_network_address_from_lower_address(
                "Provider",
                "Customer",
                provider_ip_address,
                provider_converted_ip_address,
                int(desired_size),
            )

    return completed_response_with_logs(logs, {"result": {"data": response}})


def calculate_network_address_from_lower_address(
    owner_of_lower_address,
    owner_of_higher_address,
    first_availiable_ip_address,
    first_availiable_hexa_ip_address,
    desired_size,
):
    lower_address = first_availiable_ip_address
    network_address = int(first_availiable_hexa_ip_address) - 1
    broadcast_address = int(network_address) + desired_size - 1
    network_address = ipaddress.ip_address(network_address).__str__()
    broadcast_address = ipaddress.ip_address(broadcast_address).__str__()

    return {
        "network_address": network_address,
        "broadcast_address": str(broadcast_address),
        "owner_of_lower_address": owner_of_lower_address,
        "owner_of_higher_address": owner_of_higher_address,
        "first_availiable_ip_address": lower_address,
    }


def calculate_provider_and_customer_address(network_address, resource_type):
    if str(resource_type).startswith("ipv4"):
        network_address = int(ipaddress.IPv4Address(network_address))
    else:
        network_address = int(ipaddress.IPv6Address(network_address))
    provider_address = int(network_address) + 1
    customer_address = int(network_address) + 2
    provider_address = ipaddress.ip_address(provider_address).__str__()
    customer_address = ipaddress.ip_address(customer_address).__str__()

    return provider_address, customer_address


@logging_handler(log)
def calculate_desired_size_from_prefix(task, logs):
    """
    Calculate desired size from prefix

         Args:

             task (dict): dictionary with input data ["prefix", "resource_type"]

             logs: stream of log messages
        Returns:
            "result": {
                "data": <desired_size>
            }
    """
    prefix = task["inputData"]["prefix"] if "prefix" in task["inputData"] else None
    if prefix is None:
        return failed_response_with_logs(logs, {"result": {"error": "No prefix"}})
    resource_type = str(task["inputData"]["resourceType"])

    if resource_type.startswith("ipv4"):
        if 0 < int(prefix) < 33:
            desired_size = 2 ** (32 - int(prefix))
        else:
            return failed_response_with_logs(
                logs, {"result": {"error": "Prefix must be between 1 and 32 for ipv4"}}
            )
    elif resource_type.startswith("ipv6"):
        if 0 < int(prefix) < 129:
            desired_size = 2 ** (128 - int(prefix))
        else:
            return failed_response_with_logs(
                logs, {"result": {"error": "Prefix must be between 1 and 128 for ipv6"}}
            )

    return completed_response_with_logs(logs, {"result": {"data": str(desired_size)}})


@logging_handler(log)
def query_search_empty_pools(task, logs):
    """
    Query search for empty pools in Uniresource

         Args:

             task (dict): dictionary with input data ["resourceTypeId"]


         Returns:
            Response from uniresource. Worker output format::
            "result": {
                "data": {
                    "QueryEmptyResourcePools": [
                        {
                            "id": "<id>",
                            "AllocationStrategy": <Name>
                            "Name": "<name>"
                            "Tags": <tag>
                        }
                    ]
                }
            }

    """
    resource_type_id = task["inputData"]["resourceTypeId"]
    body = query_search_empty_pools_template.render()
    variables = {"resourceTypeId": resource_type_id}
    log.debug("Sending graphql variables: %s\n with query: %s" % (variables, body))
    response = execute(body, variables)
    if "errors" in response:
        return failed_response_with_logs(
            logs, {"result": {"error": response["errors"][0]["message"]}}
        )
    return completed_response_with_logs(logs, {"result": response})


@logging_handler(log)
def query_recently_active_resources(task, logs):
    """
    Query resource by alternative id in Uniresource
         Args:
             task (dict): dictionary with input data ["alternativeId"] and optional data ["poolId", "first"]
         Returns:
            Response from uniresource. Worker output format::
            "result": {
                "data": {
                    "QueryRecentlyActiveResources": {
                        edges {
                            node {
                                id
                                Properties
                                AlternativeId
                                ParentPool {
                                    id
                                    Name
                                }
                                NestedPool {
                                id
                                Name
                                }
                            }
                            cursor{
                                ID
                            }
                        }
                    }
                }
            }

    """
    from_datetime = task["inputData"]["fromDatetime"]
    to_datetime = task["inputData"]["toDatetime"] if "toDatetime" in task["inputData"] else None
    first = task["inputData"]["first"] if "first" in task["inputData"] else None
    last = task["inputData"]["last"] if "last" in task["inputData"] else None
    before = task["inputData"]["before"] if "before" in task["inputData"] else None
    after = task["inputData"]["after"] if "after" in task["inputData"] else None
    if (after is not None) and (before is not None):
        return failed_response_with_logs(
            logs,
            {
                "result": {
                    "error": "Data cannot be extracted with the parameter after and before at the same request"
                }
            },
        )
    body = query_recently_active_resources_template.render()
    variables = {
        "fromDatetime": from_datetime,
        "toDatetime": to_datetime,
        "first": first,
        "last": last,
        "before": before,
        "after": after,
    }
    log.info("Sending graphql variables: %s\n with query: %s" % (variables, body))
    response = execute(body, variables)
    if "errors" in response:
        return failed_response_with_logs(
            logs, {"result": {"error": response["errors"][0]["message"]}}
        )
    return completed_response_with_logs(logs, {"result": response})


def start(cc):
    cc.register(
        "RESOURCE_MANAGER_claim_resource",
        {
            "name": "RESOURCE_MANAGER_claim_resource",
            "description": '{"description": "": [""]}',
            "retryCount": 0,
            "timeoutPolicy": "TIME_OUT_WF",
            "retryLogic": "FIXED",
            "retryDelaySeconds": 0,
            "inputKeys": [""],
            "outputKeys": [],
        },
        claim_resource,
    )

    cc.register(
        "RESOURCE_MANAGER_query_claimed_resource",
        {
            "name": "RESOURCE_MANAGER_query_claimed_resource",
            "description": '{"description": "": [""]}',
            "retryCount": 0,
            "timeoutPolicy": "TIME_OUT_WF",
            "retryLogic": "FIXED",
            "retryDelaySeconds": 0,
            "inputKeys": [""],
            "outputKeys": [],
        },
        query_claimed_resources,
    )

    cc.register(
        "RESOURCE_MANAGER_create_pool",
        {
            "name": "RESOURCE_MANAGER_create_pool",
            "description": '{"description": "": [""]}',
            "retryCount": 0,
            "timeoutPolicy": "TIME_OUT_WF",
            "retryLogic": "FIXED",
            "retryDelaySeconds": 0,
            "inputKeys": [""],
            "outputKeys": [],
        },
        create_pool,
    )

    cc.register(
        "RESOURCE_MANAGER_create_vlan_pool",
        {
            "name": "RESOURCE_MANAGER_create_vlan_pool",
            "description": '{"description": "": [""]}',
            "retryCount": 0,
            "timeoutPolicy": "TIME_OUT_WF",
            "retryLogic": "FIXED",
            "retryDelaySeconds": 0,
            "inputKeys": [""],
            "outputKeys": [],
        },
        create_vlan_pool,
    )

    cc.register(
        "RESOURCE_MANAGER_create_vlan_range_pool",
        {
            "name": "RESOURCE_MANAGER_create_vlan_range_pool",
            "description": '{"description": "": [""]}',
            "retryCount": 0,
            "timeoutPolicy": "TIME_OUT_WF",
            "retryLogic": "FIXED",
            "retryDelaySeconds": 0,
            "inputKeys": [""],
            "outputKeys": [],
        },
        create_vlan_range_pool,
    )

    cc.register(
        "RESOURCE_MANAGER_create_unique_id_pool",
        {
            "name": "RESOURCE_MANAGER_create_unique_id_pool",
            "description": '{"description": "": [""]}',
            "retryCount": 0,
            "timeoutPolicy": "TIME_OUT_WF",
            "retryLogic": "FIXED",
            "retryDelaySeconds": 0,
            "inputKeys": [""],
            "outputKeys": [],
        },
        create_unique_id_pool,
    )

    cc.register(
        "RESOURCE_MANAGER_query_pool",
        {
            "name": "RESOURCE_MANAGER_query_pool",
            "description": '{"description": "": [""]}',
            "retryCount": 0,
            "timeoutPolicy": "TIME_OUT_WF",
            "retryLogic": "FIXED",
            "retryDelaySeconds": 0,
            "inputKeys": [""],
            "outputKeys": [],
        },
        query_pool,
    )

    cc.register(
        "RESOURCE_MANAGER_query_unique_id_pool",
        {
            "name": "RESOURCE_MANAGER_query_unique_id_pool",
            "description": '{"description": "": [""]}',
            "retryCount": 0,
            "timeoutPolicy": "TIME_OUT_WF",
            "retryLogic": "FIXED",
            "retryDelaySeconds": 0,
            "inputKeys": [""],
            "outputKeys": [],
        },
        query_unique_id_pool,
    )

    cc.register(
        "RESOURCE_MANAGER_query_vlan_pool",
        {
            "name": "RESOURCE_MANAGER_query_vlan_pool",
            "description": '{"description": "": [""]}',
            "retryCount": 0,
            "timeoutPolicy": "TIME_OUT_WF",
            "retryLogic": "FIXED",
            "retryDelaySeconds": 0,
            "inputKeys": [""],
            "outputKeys": [],
        },
        query_vlan_pool,
    )

    cc.register(
        "RESOURCE_MANAGER_query_pool_by_tag",
        {
            "name": "RESOURCE_MANAGER_query_pool_by_tag",
            "description": '{"description": "": [""]}',
            "retryCount": 0,
            "timeoutPolicy": "TIME_OUT_WF",
            "retryLogic": "FIXED",
            "retryDelaySeconds": 0,
            "inputKeys": [""],
            "outputKeys": [],
        },
        query_pool_by_tag,
    )

    cc.register(
        "RESOURCE_MANAGER_query_vlan_range_pool",
        {
            "name": "RESOURCE_MANAGER_Query_vlan_range_pool",
            "description": '{"description": "": [""]}',
            "retryCount": 0,
            "timeoutPolicy": "TIME_OUT_WF",
            "retryLogic": "FIXED",
            "retryDelaySeconds": 0,
            "inputKeys": [""],
            "outputKeys": [],
        },
        query_vlan_range_pool,
    )

    cc.register(
        "Read_x_tenant",
        {
            "name": "Read_x_tenant",
            "description": '{"description": "Input format: X_TENANT_ID"}',
            "retryCount": 0,
            "timeoutPolicy": "TIME_OUT_WF",
            "retryLogic": "FIXED",
            "retryDelaySeconds": 0,
            "inputKeys": [],
            "outputKeys": [],
        },
        read_x_tenant,
    )

    cc.register(
        "Read_resource_manager_url_base",
        {
            "name": "Read_resource_manager_url_base",
            "description": '{"description": "Input format: RESOURCE_MANAGER_URL_BASE"}',
            "retryCount": 0,
            "timeoutPolicy": "TIME_OUT_WF",
            "retryLogic": "FIXED",
            "retryDelaySeconds": 0,
            "inputKeys": [],
            "outputKeys": [],
        },
        read_resource_manager_url_base,
    )

    cc.register(
        "RESOURCE_MANAGER_accumulate_report",
        {
            "name": "RESOURCE_MANAGER_accumulate_report",
            "description": '{"description": "": [""]}',
            "retryCount": 0,
            "timeoutPolicy": "TIME_OUT_WF",
            "retryLogic": "FIXED",
            "retryDelaySeconds": 0,
            "inputKeys": [""],
            "outputKeys": [],
        },
        accumulate_report,
    )

    cc.register(
        "RESOURCE_MANAGER_calculate_available_prefixes_for_address_pool",
        {
            "name": "RESOURCE_MANAGER_calculate_available_prefixes_for_address_pool",
            "description": '{"description": "": [""]}',
            "retryCount": 0,
            "timeoutPolicy": "TIME_OUT_WF",
            "retryLogic": "FIXED",
            "retryDelaySeconds": 0,
            "inputKeys": [""],
            "outputKeys": [],
        },
        calculate_available_prefixes_for_address_pool,
    )

    cc.register(
        "RESOURCE_MANAGER_update_alt_id_for_resource",
        {
            "name": "RESOURCE_MANAGER_update_alt_id_for_resource",
            "description": '{"description": "": [""]}',
            "retryCount": 0,
            "timeoutPolicy": "TIME_OUT_WF",
            "retryLogic": "FIXED",
            "retryDelaySeconds": 0,
            "inputKeys": [""],
            "outputKeys": [],
        },
        update_alt_id_for_resource,
    )

    cc.register(
        "RESOURCE_MANAGER_query_resource_by_alt_id",
        {
            "name": "RESOURCE_MANAGER_query_resource_by_alt_id",
            "description": '{"description": "": [""]}',
            "retryCount": 0,
            "timeoutPolicy": "TIME_OUT_WF",
            "retryLogic": "FIXED",
            "retryDelaySeconds": 0,
            "inputKeys": [""],
            "outputKeys": [],
        },
        query_resource_by_alt_id,
    )

    cc.register(
        "RESOURCE_MANAGER_create_nested_pool",
        {
            "name": "RESOURCE_MANAGER_create_nested_pool",
            "description": '{"description": "": [""]}',
            "retryCount": 0,
            "timeoutPolicy": "TIME_OUT_WF",
            "retryLogic": "FIXED",
            "retryDelaySeconds": 0,
            "inputKeys": [""],
            "outputKeys": [],
        },
        create_nested_pool,
    )

    cc.register(
        "RESOURCE_MANAGER_deallocate_resource",
        {
            "name": "RESOURCE_MANAGER_deallocate_resource",
            "description": '{"description": "": [""]}',
            "retryCount": 0,
            "timeoutPolicy": "TIME_OUT_WF",
            "retryLogic": "FIXED",
            "retryDelaySeconds": 0,
            "inputKeys": [""],
            "outputKeys": [],
        },
        deallocate_resource,
    )

    cc.register(
        "RESOURCE_MANAGER_delete_pool",
        {
            "name": "RESOURCE_MANAGER_delete_pool",
            "description": '{"description": "": [""]}',
            "retryCount": 0,
            "timeoutPolicy": "TIME_OUT_WF",
            "retryLogic": "FIXED",
            "retryDelaySeconds": 0,
            "inputKeys": [""],
            "outputKeys": [],
        },
        delete_pool,
    )

    cc.register(
        "RESOURCE_MANAGER_calculate_host_and_broadcast_address",
        {
            "name": "RESOURCE_MANAGER_calculate_host_and_broadcast_address",
            "description": '{"description": "": [""]}',
            "retryCount": 0,
            "timeoutPolicy": "TIME_OUT_WF",
            "retryLogic": "FIXED",
            "retryDelaySeconds": 0,
            "inputKeys": [""],
            "outputKeys": [],
        },
        calculate_host_and_broadcast_address,
    )

    cc.register(
        "RESOURCE_MANAGER_calculate_desired_size_from_prefix",
        {
            "name": "RESOURCE_MANAGER_calculate_desired_size_from_prefix",
            "description": '{"description": "": [""]}',
            "retryCount": 0,
            "timeoutPolicy": "TIME_OUT_WF",
            "retryLogic": "FIXED",
            "retryDelaySeconds": 0,
            "inputKeys": [""],
            "outputKeys": [],
        },
        calculate_desired_size_from_prefix,
    )

    cc.register(
        "RESOURCE_MANAGER_query_search_empty_pools",
        {
            "name": "RESOURCE_MANAGER_query_search_empty_pools",
            "description": '{"description": "": [""]}',
            "retryCount": 0,
            "timeoutPolicy": "TIME_OUT_WF",
            "retryLogic": "FIXED",
            "retryDelaySeconds": 0,
            "inputKeys": [""],
            "outputKeys": [],
        },
        query_search_empty_pools,
    )

    cc.register(
        "RESOURCE_MANAGER_query_recently_active_resources",
        {
            "name": "RESOURCE_MANAGER_query_recently_active_resources",
            "description": '{"description": "": [""]}',
            "retryCount": 0,
            "timeoutPolicy": "TIME_OUT_WF",
            "retryLogic": "FIXED",
            "retryDelaySeconds": 0,
            "inputKeys": [""],
            "outputKeys": [],
        },
        query_recently_active_resources,
    )
