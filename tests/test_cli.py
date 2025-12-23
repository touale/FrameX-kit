from typing import Any

import framex
from framex.cli import framex as framex_cli
from framex.consts import VERSION


def test_framex_version_option(runner):
    """Test that framex --version prints correct version"""
    result = runner.invoke(framex_cli, ["--version"])
    assert result.exit_code == 0
    assert VERSION in result.output


def test_run_command_with_defaults(monkeypatch, runner):
    """Test that 'framex run' calls fx.run() with default ServerConfig values."""
    called = {}

    def _fake_run(**kwargs: Any) -> None:
        called.update(kwargs)

    monkeypatch.setattr(framex, "run", _fake_run)

    result = runner.invoke(framex_cli, ["run"])

    assert result.exit_code == 0
    assert "🚀 Starting FrameX with configuration:" in result.output

    assert called["server_host"] == "127.0.0.1"
    assert called["server_port"] == 8080
    assert called["dashboard_host"] == "127.0.0.1"
    assert called["dashboard_port"] == 8260
