import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--collect-stats-folder",
        action="store",
        metavar="ga_workflows_collected_data",
        required=False,
        help="in context of github workflow updates the files in the repo ga_workflows_collected_data",
    )


@pytest.fixture(autouse=True)
def collect_stats_folder(pytestconfig):
    pytest.COLLECT_STATS_FOLDER = pytestconfig.getoption("--collect-stats-folder")
