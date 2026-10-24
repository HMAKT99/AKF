"""End-to-end tests: a real MCP client talks to the AKF server in-process."""

import asyncio
import json

import pytest

from mcp_server_akf.server import TOOLS, create_server

Client = getattr(pytest.importorskip("mcp"), "Client", None)


def _call(name, arguments):
    async def run():
        async with Client(create_server()) as client:
            return await client.call_tool(name, arguments)
    return asyncio.run(run())


def _payload(result):
    return json.loads(result.content[0].text)


@pytest.mark.skipif(Client is None, reason="in-process Client requires mcp 2.x")
class TestServer:
    def test_lists_all_tools(self):
        async def run():
            async with Client(create_server()) as client:
                return await client.list_tools()
        names = {t.name for t in asyncio.run(run()).tools}
        assert names == {t.name for t in TOOLS}

    def test_check_file_unstamped(self, tmp_path):
        f = tmp_path / "notes.md"
        f.write_text("# hello\n")
        payload = _payload(_call("check_file", {"path": str(f)}))
        assert payload["status"] == "UNSTAMPED"

    def test_stamp_then_check(self, tmp_path):
        f = tmp_path / "notes.md"
        f.write_text("# hello\n")
        _call("stamp_file", {"path": str(f), "agent": "test-agent", "evidence": "3/3 tests passed"})
        payload = _payload(_call("check_file", {"path": str(f)}))
        assert payload["status"] in {"OK", "LOW"}
        assert payload["agent"] == "test-agent"

    def test_unknown_tool_returns_error(self):
        assert "Unknown tool" in _payload(_call("nope", {}))["error"]
