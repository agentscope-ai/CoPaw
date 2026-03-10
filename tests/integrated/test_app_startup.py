# -*- coding: utf-8 -*-
"""Integrated tests for CoPaw app startup and console."""
from __future__ import annotations

import socket
import subprocess
import sys
import time

import httpx


def _find_free_port(host: str = "127.0.0.1") -> int:
    """Bind to port 0 and return the OS-assigned free port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        sock.listen(1)
        return sock.getsockname()[1]


def test_app_startup_and_console() -> None:
    """Test that copaw app starts correctly with backend and console."""
    host = "127.0.0.1"
    port = _find_free_port(host)

    with subprocess.Popen(
        [
            sys.executable,
            "-m",
            "copaw",
            "app",
            "--host",
            host,
            "--port",
            str(port),
            "--log-level",
            "info",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd="/Users/raykkk/Desktop/repo/CoPaw",
    ) as process:
        max_wait = 45
        start_time = time.time()
        backend_ready = False
        last_error = None

        with httpx.Client(timeout=5.0) as client:
            while time.time() - start_time < max_wait:
                if process.poll() is not None:
                    _, stderr = process.communicate()
                    if (
                        "ImportError" in stderr
                        or "ModuleNotFoundError" in stderr
                    ):
                        raise AssertionError(
                            f"Skipping due to dependency issue: "
                            f"{stderr[:1000]}",
                        )
                    raise AssertionError(
                        f"Process exited early with code "
                        f"{process.returncode}. "
                        f"Stderr: {stderr[:1000]}",
                    )

                try:
                    response = client.get(
                        f"http://{host}:{port}/api/version",
                    )
                    if response.status_code == 200:
                        backend_ready = True
                        version_data = response.json()
                        assert "version" in version_data
                        assert isinstance(version_data["version"], str)
                        break
                except (
                    httpx.ConnectError,
                    httpx.TimeoutException,
                ) as e:
                    last_error = str(e)
                    time.sleep(1.0)
                    continue

            assert backend_ready, (
                f"Backend did not start within timeout period. "
                f"Last error: {last_error}"
            )

            console_response = client.get(f"http://{host}:{port}/console/")
            assert (
                console_response.status_code == 200
            ), f"Console not accessible: {console_response.status_code}"
            assert (
                "text/html"
                in console_response.headers.get("content-type", "").lower()
            ), "Console should return HTML content"

            html_content = console_response.text
            assert len(html_content) > 0, "Console HTML should not be empty"
            assert (
                "<!doctype html>" in html_content.lower()
                or "<html" in html_content.lower()
            ), "Console should return valid HTML"
