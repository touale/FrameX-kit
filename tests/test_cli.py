from typing import Any

import framex
from framex.cli import framex as framex_cli
from framex.config import settings
from framex.consts import VERSION


def test_framex_version_option(runner):
    """framex --version prints version"""
    result = runner.invoke(framex_cli, ["--version"])
    assert result.exit_code == 0
    assert VERSION in result.output


def test_run_command_with_defaults(monkeypatch, runner):
    """
    framex run
    - should NOT override settings
    - should call framex.run()
    """
    called = {"called": False}

    def fake_run(*_: Any, **__: Any) -> None:
        called["called"] = True

    monkeypatch.setattr(framex, "run", fake_run)

    original_host = settings.server.host
    original_port = settings.server.port
    original_use_ray = settings.server.use_ray

    result = runner.invoke(framex_cli, ["run"])

    assert result.exit_code == 0
    assert called["called"] is True
    assert "🚀 Starting FrameX with configuration" in result.output

    assert settings.server.host == original_host
    assert settings.server.port == original_port
    assert settings.server.use_ray == original_use_ray


def test_run_command_override_basic_options(monkeypatch, runner) -> None:
    """
    framex run --host --port
    - should override settings
    """

    def fake_run(*args: Any, **kwargs: Any) -> None:
        pass

    monkeypatch.setattr(framex, "run", fake_run)

    result = runner.invoke(
        framex_cli,
        [
            "run",
            "--host",
            "127.0.0.1",
            "--port",
            "9999",
        ],
    )

    assert result.exit_code == 0
    assert settings.server.host == "127.0.0.1"
    assert settings.server.port == 9999


def test_run_command_tristate_bool(monkeypatch, runner) -> None:
    """
    --use-ray / --no-use-ray should override settings
    """

    def fake_run(*args: Any, **kwargs: Any) -> None:
        pass

    monkeypatch.setattr(framex, "run", fake_run)

    result = runner.invoke(framex_cli, ["run", "--no-use-ray"])
    assert result.exit_code == 0
    assert settings.server.use_ray is False

    result = runner.invoke(framex_cli, ["run", "--use-ray"])
    assert result.exit_code == 0
    assert settings.server.use_ray is True
