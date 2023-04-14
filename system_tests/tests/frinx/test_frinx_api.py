import asyncio
import json
import logging
import os
import statistics
import time as sleep_time
from datetime import timedelta
from timeit import default_timer as timer

import aiohttp
import pytest
from system_tests.tests.frinx.test_performance import CONDUCTOR_HEADERS
from system_tests.tests.frinx.test_performance import CONDUCTOR_URL
from system_tests.tests.frinx.test_performance import exec_wf
from system_tests.tests.frinx.test_performance import get_wf_execution

LOGGER = logging.getLogger(__name__)

CONDUCTOR_WF_EXEC_RQ_FORK = {
    "name": "Test_fork_workflow",
    "input": {
        "fork_count": 5,
        "num_paragraphs": 1,
        "num_sentences": 1,
        "num_words": 1,
        "sleep_time": 0,
    },
}


async def get_wf_path(session, wf_id) -> dict:
    url = CONDUCTOR_URL + "workflow/path/" + wf_id
    async with session.get(url, headers=CONDUCTOR_HEADERS) as r_future:
        response = await r_future.read()
        r_future.raise_for_status()
        return json.loads(response)


async def get_wf_family(session, wf_id, summary=True) -> dict:
    url = CONDUCTOR_URL + "workflow/family/" + wf_id + "?summaryOnly=" + str(summary).lower()
    async with session.get(url, headers=CONDUCTOR_HEADERS) as r_future:
        response = await r_future.read()
        r_future.raise_for_status()
        return json.loads(response)


@pytest.mark.asyncio
async def test_path_and_family_apis():
    SLEEP = 4

    async with aiohttp.ClientSession() as session:
        executed_id = await asyncio.ensure_future(exec_wf(session, CONDUCTOR_WF_EXEC_RQ_FORK, 0))
        await wait_for_completion(SLEEP, executed_id, session)

        # Root WF, path is of length 1
        path = await get_wf_path(session, executed_id)
        assert [executed_id] == path
        # Root WF, family is all forks + root with all parameters
        family = await get_wf_family(session, executed_id, False)
        assert len(family) == CONDUCTOR_WF_EXEC_RQ_FORK["input"]["fork_count"] + 1

        # Find any child workflow
        child_wf = next(filter(lambda wf: wf["workflowName"] == "Test_workflow", family))
        child_id = child_wf["workflowId"]

        # Child WF, path is of length 2
        path = await get_wf_path(session, child_id)
        assert [executed_id, child_id] == path
        # Child WF, family is just the child returned as summary only
        family = await get_wf_family(session, child_id, True)
        assert len(family) == 1
        # This was summary only, workflowInput should be null
        assert family[0].get("input", None) is None


async def wait_for_completion(sleep_seconds, executed_id, session):
    iterations = 10

    for i in range(iterations):
        wf_execution = await get_wf_execution(session, executed_id)
        if wf_execution["status"] == "COMPLETED":
            break
        elif i is (iterations - 1):
            LOGGER.error("Workflow not completed. Execution: %s", wf_execution)
            raise Exception(
                "Workflow not completed in %s seconds. Current status: %s"
                % (iterations * sleep_seconds, wf_execution["status"])
            )

        sleep_time.sleep(sleep_seconds)
