"""Pytest runtime configuration."""

from __future__ import annotations

import pytest


def pytest_addoption(parser: pytest.Parser):
    parser.addoption(
        "--runfuzz", action="store_true", default=False, help="run fuzz tests"
    )
    parser.addoption(
        "--generate-autofix",
        action="store_true",
        default=False,
        help="generate autofix file content",
    )
    parser.addoption(
        "--enable-codes",
        default="TRIO",
        help="select error codes whose visitors to run.",
    )


def pytest_configure(config: pytest.Config):
    config.addinivalue_line(
        "markers", "fuzz: mark test as a slow fuzzer to not run by default"
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]):
    if config.getoption("--runfuzz"):
        # --runfuzz given in cli: do not skip fuzz tests
        return
    skip_fuzz = pytest.mark.skip(reason="need --runfuzz option to run")
    for item in items:
        if "fuzz" in item.keywords:
            item.add_marker(skip_fuzz)


@pytest.fixture()
def generate_autofix(request: pytest.FixtureRequest):
    return request.config.getoption("generate_autofix")


@pytest.fixture()
def enable_codes(request: pytest.FixtureRequest):
    return request.config.getoption("--enable-codes")
