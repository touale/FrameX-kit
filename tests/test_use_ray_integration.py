import json
import os
import socket
import subprocess
import sys
import tempfile
from contextlib import suppress
from pathlib import Path

import pytest


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def test_use_ray_nested_service_call_uses_remote_apis() -> None:
    pytest.importorskip("ray")

    repo_root = Path(__file__).resolve().parents[1]
    plugin_dir = repo_root / "tests" / "ray_plugins"
    server_port = _find_free_port()
    dashboard_port = _find_free_port()
    with tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8", suffix=".json", delete=False) as output_file:
        output_path = Path(output_file.name)
    with tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8", suffix=".log", delete=False) as named_log_file:
        log_path = Path(named_log_file.name)

    launch_code = """
import asyncio
import json
import time
from pathlib import Path

import framex
import ray
from ray import serve
from framex.config import settings
from framex.consts import APP_NAME


async def main() -> None:
    settings.server.use_ray = True
    plugin_dir = Path(r"__PLUGIN_DIR__")
    output_path = Path(r"__OUTPUT_PATH__")
    framex.run(
        use_ray=True,
        blocking=False,
        server_host="127.0.0.1",
        server_port=__SERVER_PORT__,
        dashboard_host="127.0.0.1",
        dashboard_port=__DASHBOARD_PORT__,
        num_cpus=4,
        enable_proxy=False,
        load_builtin_plugins=["echo"],
        load_plugins=[str(plugin_dir)],
    )
    handle = serve.get_deployment_handle(
        "test_service_caller.RayServiceCallerPlugin",
        app_name=APP_NAME,
    )
    deadline = time.time() + 90.0
    last_error = None
    while time.time() < deadline:
        try:
            result = await handle.service_echo.remote(message="ray-ok")
            output_path.write_text(json.dumps({"result": result}), encoding="utf-8")
            return
        except Exception as exc:
            last_error = exc
            await asyncio.sleep(1)
    raise RuntimeError(f"Timed out waiting for Ray service call: {last_error!r}")


try:
    asyncio.run(main())
finally:
    try:
        serve.shutdown()
    finally:
        ray.shutdown()
"""
    launch_code = (
        launch_code.replace("__PLUGIN_DIR__", str(plugin_dir))
        .replace("__OUTPUT_PATH__", str(output_path))
        .replace("__SERVER_PORT__", str(server_port))
        .replace("__DASHBOARD_PORT__", str(dashboard_port))
    )

    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        (str(repo_root / "tools" / "coverage_support"), str(repo_root), env.get("PYTHONPATH", ""))
    )
    env["SERVER__USE_RAY"] = "true"

    with log_path.open("w", encoding="utf-8") as log_file:
        proc = subprocess.Popen(  # noqa: S603
            [sys.executable, "-c", launch_code],
            cwd=repo_root,
            env=env,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        )

        try:
            return_code = proc.wait(timeout=150)
            logs = log_path.read_text(encoding="utf-8", errors="replace")
            if logs:
                sys.stdout.write(logs if logs.endswith("\n") else f"{logs}\n")
            if return_code != 0:
                pytest.fail(f"Ray integration subprocess failed with code {return_code}.\n{logs}")

            payload = json.loads(output_path.read_text(encoding="utf-8"))
            assert payload["result"] == "ray-ok"
        finally:
            if proc.poll() is None:
                proc.terminate()
                with suppress(subprocess.TimeoutExpired):
                    proc.wait(timeout=10)
                if proc.poll() is None:
                    proc.kill()
                    proc.wait(timeout=10)
            output_path.unlink(missing_ok=True)
            log_path.unlink(missing_ok=True)
