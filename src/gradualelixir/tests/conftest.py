import pytest

from . import TEST_ENV

_options = {
    "display_results": (
        "--display-results",
        {"action": "store_true", "default": False},
    ),
    "display_results_verbose": (
        "--display-results-verbose",
        {"action": "store_true", "default": False},
    ),
    "success_only": (
        "--success-only",
        {"action": "store_true", "default": False},
    ),
    "errors_only": (
        "--errors-only",
        {"action": "store_true", "default": False},
    ),
}


def pytest_addoption(parser):
    for item in _options.values():
        parser.addoption(item[0], **item[1])


@pytest.fixture(autouse=True)
def options(request):
    TEST_ENV.update({key: request.config.getoption(item[0]) for key, item in _options.items()})
