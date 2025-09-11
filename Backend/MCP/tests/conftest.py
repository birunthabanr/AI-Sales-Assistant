import asyncio
import importlib
import os
import sys
import pytest

pytest_plugins = ("pytest_asyncio",)

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def server_module():
    # Add the parent folder (MCP) to sys.path so Python can find the server module
    mcp_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if mcp_folder not in sys.path:
        sys.path.insert(0, mcp_folder)

    # Import your server module
    module_name = "mcp_server_new"  # your server filename without .py
    mod = importlib.import_module(module_name)
    return mod

@pytest.fixture
async def mcp_client(server_module):
    # server_module must expose `mcp` (FastMCP instance)
    mcp = getattr(server_module, "mcp")
    async with mcp.test_client() as client:
        yield client
