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


def test_run_command_with_dashboard_options(monkeypatch, runner) -> None:
    """
    Test --dashboard-host and --dashboard-port options
    """

    def fake_run(*args, **kwargs: Any) -> None:
        pass

    monkeypatch.setattr(framex, "run", fake_run)

    result = runner.invoke(
        framex_cli,
        [
            "run",
            "--dashboard-host",
            "0.0.0.0",  # noqa: S104
            "--dashboard-port",
            "8265",
        ],
    )

    assert result.exit_code == 0
    assert settings.server.dashboard_host == "0.0.0.0"  # noqa: S104
    assert settings.server.dashboard_port == 8265


def test_run_command_with_num_cpus(monkeypatch, runner) -> None:
    """
    Test --num-cpus option
    """

    def fake_run(*args: Any, **kwargs: Any) -> None:
        pass

    monkeypatch.setattr(framex, "run", fake_run)

    result = runner.invoke(framex_cli, ["run", "--num-cpus", "4"])

    assert result.exit_code == 0
    assert settings.server.num_cpus == 4


def test_run_command_with_enable_proxy(monkeypatch, runner) -> None:
    """
    Test --enable-proxy / --no-enable-proxy options
    """

    def fake_run(*args: Any, **kwargs: Any) -> None:
        pass

    monkeypatch.setattr(framex, "run", fake_run)

    # Test --enable-proxy
    result = runner.invoke(framex_cli, ["run", "--enable-proxy"])
    assert result.exit_code == 0
    assert settings.server.enable_proxy is True

    # Test --no-enable-proxy
    result = runner.invoke(framex_cli, ["run", "--no-enable-proxy"])
    assert result.exit_code == 0
    assert settings.server.enable_proxy is False


def test_run_command_with_load_plugins(monkeypatch, runner) -> None:
    """
    Test --load-plugins and --load-builtin-plugins options
    """
    loaded_plugins: list[str] = []
    loaded_builtin_plugins: list[str] = []

    def fake_load_plugins(*plugins) -> None:
        loaded_plugins.extend(plugins)

    def fake_load_builtin_plugins(*plugins) -> None:
        loaded_builtin_plugins.extend(plugins)

    def fake_run(*args: Any, **kwargs: Any) -> None:
        pass

    monkeypatch.setattr(framex, "load_plugins", fake_load_plugins)
    monkeypatch.setattr(framex, "load_builtin_plugins", fake_load_builtin_plugins)
    monkeypatch.setattr(framex, "run", fake_run)

    result = runner.invoke(
        framex_cli,
        [
            "run",
            "--load-plugins",
            "plugin1",
            "--load-plugins",
            "plugin2",
            "--load-builtin-plugins",
            "builtin1",
        ],
    )

    assert result.exit_code == 0
    assert "plugin1" in loaded_plugins
    assert "plugin2" in loaded_plugins
    assert "builtin1" in loaded_builtin_plugins
