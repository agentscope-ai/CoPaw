# -*- coding: utf-8 -*-
"""Unified QR code authorization handlers for channels.

Each channel that supports QR-code-based login/authorization implements a
concrete ``QRCodeAuthHandler`` and registers it in ``QRCODE_AUTH_HANDLERS``.
The router in *config.py* exposes two generic endpoints that delegate to
the appropriate handler based on the ``{channel}`` path parameter.

Typical flow
------------
1. ``GET /config/channels/{channel}/qrcode``
   → calls ``handler.fetch_qrcode(request)``
   → returns ``{"qrcode_img": "<base64 PNG>", "poll_token": "..."}``

2. ``GET /config/channels/{channel}/qrcode/status?token=...``
   → calls ``handler.poll_status(token, request)``
   → returns ``{"status": "...", "credentials": {...}}``
"""

from __future__ import annotations

import base64
import io
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict

import segno
from fastapi import HTTPException, Request

from ...constant import PROJECT_NAME


@dataclass
class QRCodeResult:
    """Value object returned by ``fetch_qrcode``."""

    scan_url: str
    poll_token: str


@dataclass
class PollResult:
    """Value object returned by ``poll_status``."""

    status: str
    credentials: Dict[str, Any]


class QRCodeAuthHandler(ABC):
    """Abstract base class for channel QR code authorization."""

    @abstractmethod
    async def fetch_qrcode(self, request: Request) -> QRCodeResult:
        """Obtain the scan URL and a token used for subsequent polling."""

    @abstractmethod
    async def poll_status(self, token: str, request: Request) -> PollResult:
        """Check whether the user has scanned & confirmed authorization."""


def generate_qrcode_image(scan_url: str) -> str:
    """Generate a base64-encoded PNG QR code image from *scan_url*."""
    try:
        qr_code = segno.make(scan_url, error="M")
        buf = io.BytesIO()
        qr_code.save(buf, kind="png", scale=6, border=2)
        return base64.b64encode(buf.getvalue()).decode()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"QR code image generation failed: {exc}",
        ) from exc


# ---------------------------------------------------------------------------
# WeChat (iLink) handler
# ---------------------------------------------------------------------------


class WeChatQRCodeAuthHandler(QRCodeAuthHandler):
    """QR code auth handler for WeChat iLink Bot login."""

    async def _get_base_url(self, request: Request) -> str:
        from ..channels.wechat.client import _DEFAULT_BASE_URL

        try:
            from ..agent_context import get_agent_for_request

            agent = await get_agent_for_request(request)
            channels = agent.config.channels
            if channels is not None:
                wechat_cfg = getattr(channels, "wechat", None)
                if wechat_cfg is not None:
                    return (
                        getattr(wechat_cfg, "base_url", "")
                        or _DEFAULT_BASE_URL
                    )
        except Exception:
            pass
        return _DEFAULT_BASE_URL

    async def fetch_qrcode(self, request: Request) -> QRCodeResult:
        import httpx
        from ..channels.wechat.client import ILinkClient

        base_url = await self._get_base_url(request)
        client = ILinkClient(base_url=base_url)
        await client.start()
        try:
            qr_data = await client.get_bot_qrcode()
        except (httpx.HTTPError, Exception) as exc:
            raise HTTPException(
                status_code=502,
                detail=f"WeChat QR code fetch failed: {exc}",
            ) from exc
        finally:
            await client.stop()

        qrcode = qr_data.get("qrcode", "")
        qrcode_img_content = qr_data.get("qrcode_img_content", "")

        if not qrcode and not qrcode_img_content:
            raise HTTPException(
                status_code=502,
                detail="WeChat returned empty QR code data",
            )

        if qrcode_img_content.startswith("http"):
            scan_url = qrcode_img_content
        else:
            scan_url = (
                f"https://liteapp.weixin.qq.com/q/7GiQu1"
                f"?qrcode={qrcode}&bot_type=3"
            )

        return QRCodeResult(scan_url=scan_url, poll_token=qrcode)

    async def poll_status(self, token: str, request: Request) -> PollResult:
        import httpx
        from ..channels.wechat.client import ILinkClient

        base_url = await self._get_base_url(request)
        client = ILinkClient(base_url=base_url)
        await client.start()
        try:
            data = await client.get_qrcode_status(token)
        except (httpx.HTTPError, Exception) as exc:
            raise HTTPException(
                status_code=502,
                detail=f"WeChat status check failed: {exc}",
            ) from exc
        finally:
            await client.stop()

        return PollResult(
            status=data.get("status", "waiting"),
            credentials={
                "bot_token": data.get("bot_token", ""),
                "base_url": data.get("baseurl", ""),
            },
        )


# ---------------------------------------------------------------------------
# WeCom (Enterprise WeChat) handler
# ---------------------------------------------------------------------------

_WECOM_AUTH_ORIGIN = "https://work.weixin.qq.com"
_WECOM_SOURCE = PROJECT_NAME.lower()


class WecomQRCodeAuthHandler(QRCodeAuthHandler):
    """QR code auth handler for WeCom bot authorization."""

    async def fetch_qrcode(self, request: Request) -> QRCodeResult:
        import json
        import re
        import secrets
        import time
        import httpx

        state = secrets.token_urlsafe(16)
        gen_url = (
            f"{_WECOM_AUTH_ORIGIN}/ai/qc/gen"
            f"?source={_WECOM_SOURCE}&state={state}"
            f"&timestamp={int(time.time() * 1000)}"
        )

        try:
            async with httpx.AsyncClient(
                timeout=15,
                follow_redirects=True,
            ) as client:
                resp = await client.get(gen_url)
                resp.raise_for_status()
                html = resp.text
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=f"WeCom auth page fetch failed: {exc}",
            ) from exc

        settings_match = re.search(
            r"window\.settings\s*=\s*(\{.*\})",
            html,
            re.DOTALL,
        )
        if not settings_match:
            raise HTTPException(
                status_code=502,
                detail="Failed to parse WeCom auth page settings",
            )

        try:
            settings = json.loads(settings_match.group(1))
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to parse WeCom settings JSON: {exc}",
            ) from exc

        scode = settings.get("scode", "")
        auth_url = settings.get("auth_url", "")

        if not scode or not auth_url:
            raise HTTPException(
                status_code=502,
                detail="WeCom returned empty scode or auth_url",
            )

        return QRCodeResult(scan_url=auth_url, poll_token=scode)

    async def poll_status(self, token: str, request: Request) -> PollResult:
        from urllib.parse import quote
        import httpx

        query_url = (
            f"{_WECOM_AUTH_ORIGIN}/ai/qc/query_result" f"?scode={quote(token)}"
        )

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(query_url)
                resp.raise_for_status()
                result = resp.json()
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=f"WeCom status check failed: {exc}",
            ) from exc

        data = result.get("data", {})
        bot_info = data.get("bot_info", {})

        return PollResult(
            status=data.get("status", "waiting"),
            credentials={
                "bot_id": bot_info.get("botid", ""),
                "secret": bot_info.get("secret", ""),
            },
        )


# ---------------------------------------------------------------------------
# DingTalk (Device Flow) handler
# ---------------------------------------------------------------------------

_DINGTALK_API_BASE = "https://oapi.dingtalk.com"
_DINGTALK_SOURCE = "QWENPAW"


class DingtalkQRCodeAuthHandler(QRCodeAuthHandler):
    """QR code auth handler for DingTalk bot registration via Device Flow.

    Flow:
    1. POST /app/registration/init   → nonce (5 min TTL)
    2. POST /app/registration/begin  → device_code + verification_uri_complete
    3. POST /app/registration/poll   → client_id + client_secret on SUCCESS
    """

    async def fetch_qrcode(self, request: Request) -> QRCodeResult:
        import httpx

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                # Step 1: init – obtain a one-time nonce
                init_resp = await client.post(
                    f"{_DINGTALK_API_BASE}/app/registration/init",
                    json={"source": _DINGTALK_SOURCE},
                )
                init_resp.raise_for_status()
                init_data = init_resp.json()

                if init_data.get("errcode", -1) != 0:
                    raise HTTPException(
                        status_code=502,
                        detail=(
                            f"DingTalk init failed: "
                            f"{init_data.get('errmsg', 'unknown error')}"
                        ),
                    )

                nonce = init_data.get("nonce", "")
                if not nonce:
                    raise HTTPException(
                        status_code=502,
                        detail="DingTalk returned empty nonce",
                    )

                # Step 2: begin – exchange nonce for device_code & QR URL
                begin_resp = await client.post(
                    f"{_DINGTALK_API_BASE}/app/registration/begin",
                    json={"nonce": nonce},
                )
                begin_resp.raise_for_status()
                begin_data = begin_resp.json()

                if begin_data.get("errcode", -1) != 0:
                    raise HTTPException(
                        status_code=502,
                        detail=(
                            f"DingTalk begin failed: "
                            f"{begin_data.get('errmsg', 'unknown error')}"
                        ),
                    )

                device_code = begin_data.get("device_code", "")
                scan_url = begin_data.get("verification_uri_complete", "")

                if not device_code or not scan_url:
                    raise HTTPException(
                        status_code=502,
                        detail="DingTalk returned empty device_code or URI",
                    )

                return QRCodeResult(
                    scan_url=scan_url,
                    poll_token=device_code,
                )

        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=f"DingTalk QR code fetch failed: {exc}",
            ) from exc

    async def poll_status(self, token: str, request: Request) -> PollResult:
        import httpx

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    f"{_DINGTALK_API_BASE}/app/registration/poll",
                    json={"device_code": token},
                )
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=f"DingTalk status check failed: {exc}",
            ) from exc

        status = data.get("status", "WAITING")

        if status == "SUCCESS":
            return PollResult(
                status="success",
                credentials={
                    "client_id": data.get("client_id", ""),
                    "client_secret": data.get("client_secret", ""),
                },
            )
        elif status == "FAIL":
            return PollResult(
                status="fail",
                credentials={
                    "fail_reason": data.get("fail_reason", ""),
                },
            )
        elif status == "EXPIRED":
            return PollResult(status="expired", credentials={})
        else:
            # WAITING or any other status
            return PollResult(status="waiting", credentials={})


# ---------------------------------------------------------------------------
# Feishu/Lark (Device Authorization Grant - RFC 8628) handler
# ---------------------------------------------------------------------------

_FEISHU_ACCOUNTS_DOMAIN = "https://accounts.feishu.cn"
_LARK_ACCOUNTS_DOMAIN = "https://accounts.larksuite.com"

# Global cache for ongoing registration sessions
_FEISHU_REGISTRATION_SESSIONS: Dict[str, Dict[str, Any]] = {}


class FeishuQRCodeAuthHandler(QRCodeAuthHandler):
    """QR code auth handler for Feishu/Lark bot registration via Device Flow.

    Uses the OAuth 2.0 Device Authorization Grant (RFC 8628) protocol
    to enable one-click app creation by scanning a QR code.

    Flow:
    1. Call lark_oapi.aregister_app() to get QR code URL
    2. User scans QR code in Feishu/Lark mobile app
    3. Poll for completion to get app_id and app_secret

    Note: This requires lark-oapi >= 1.5.5
    """

    async def _get_domain(self, request: Request) -> str:
        """Determine if using Feishu (China) or Lark (International) domain."""
        try:
            from ..agent_context import get_agent_for_request

            agent = await get_agent_for_request(request)
            channels = agent.config.channels
            if channels is not None:
                feishu_cfg = getattr(channels, "feishu", None)
                if feishu_cfg is not None:
                    domain = getattr(feishu_cfg, "domain", "feishu")
                    return domain if domain in ("feishu", "lark") else "feishu"
        except Exception:
            pass
        return "feishu"

    def _get_accounts_domain(self, domain: str) -> str:
        """Get accounts domain based on feishu/lark selection."""
        return (
            _LARK_ACCOUNTS_DOMAIN
            if domain == "lark"
            else _FEISHU_ACCOUNTS_DOMAIN
        )

    async def fetch_qrcode(self, request: Request) -> QRCodeResult:
        """Initiate device authorization flow and return QR code URL."""
        import asyncio
        import secrets

        # Check if lark-oapi is installed
        try:
            import lark_oapi as lark
        except ImportError as exc:
            raise HTTPException(
                status_code=500,
                detail=(
                    "lark-oapi SDK not installed. "
                    "Please install it: pip install lark-oapi>=1.5.5"
                ),
            ) from exc

        domain = await self._get_domain(request)
        accounts_domain = self._get_accounts_domain(domain)
        lark_domain = self._get_accounts_domain(
            "lark" if domain == "feishu" else "feishu",
        )

        # Generate a unique session ID for this registration attempt
        session_id = secrets.token_urlsafe(32)

        # Shared state between coroutine and callbacks
        qrcode_info = {}
        registration_result = {}
        registration_error = None

        def on_qr_code_ready(info):
            """Callback when QR code URL is ready."""
            qrcode_info["url"] = info["url"]
            qrcode_info["expire_in"] = info.get("expire_in", 300)

        def on_status_change(info):
            """Callback for status changes during polling."""
            # We can log this for debugging
            status = info.get("status", "unknown")
            if status == "slow_down":
                # SDK is slowing down polling
                pass

        async def register_app_task():
            """Background task to complete the registration."""
            nonlocal registration_result, registration_error
            try:
                result = await lark.aregister_app(
                    on_qr_code=on_qr_code_ready,
                    on_status_change=on_status_change,
                    source=PROJECT_NAME,
                    domain=accounts_domain,
                    lark_domain=lark_domain,
                )

                # Update the shared dictionary
                registration_result.update(result)

                # Also update the session dict directly
                if session_id in _FEISHU_REGISTRATION_SESSIONS:
                    _FEISHU_REGISTRATION_SESSIONS[session_id][
                        "result"
                    ] = result

            except Exception as e:
                registration_error = e
                import logging

                logging.error(
                    f"Feishu register_app failed: {e}",
                    exc_info=True,
                )

        # Start the background task
        task = asyncio.create_task(register_app_task())

        # Wait briefly for the QR code URL to be ready
        # (the SDK calls on_qr_code very quickly)
        max_wait_seconds = 10
        wait_iterations = max_wait_seconds * 10  # 0.1s per iteration
        for _ in range(wait_iterations):
            if "url" in qrcode_info:
                break
            # Check if task failed early
            if registration_error is not None:
                task.cancel()
                raise HTTPException(
                    status_code=502,
                    detail=f"Feishu registration failed: {registration_error}",
                )
            await asyncio.sleep(0.1)

        if "url" not in qrcode_info:
            task.cancel()
            # Provide more detailed error message
            error_detail = "Feishu QR code URL not ready in time"
            if registration_error:
                error_detail += f": {registration_error}"
            raise HTTPException(
                status_code=502,
                detail=error_detail,
            )

        # Store the session for later polling
        import time

        _FEISHU_REGISTRATION_SESSIONS[session_id] = {
            "qrcode_url": qrcode_info["url"],
            "expire_in": qrcode_info.get("expire_in", 300),
            "task": task,
            "result": registration_result,
            "error": None,
            "created_at": time.time(),
        }

        return QRCodeResult(
            scan_url=qrcode_info["url"],
            poll_token=session_id,
        )

    # pylint: disable=too-many-return-statements
    async def poll_status(self, token: str, request: Request) -> PollResult:
        """Poll authorization status until user scans and confirms.

        Args:
            token: The session_id returned from fetch_qrcode
            request: FastAPI request object

        Returns:
            PollResult with status and credentials
        """
        session = _FEISHU_REGISTRATION_SESSIONS.get(token)

        if not session:
            return PollResult(
                status="expired",
                credentials={"fail_reason": "Session not found or expired"},
            )

        task = session["task"]

        # Check if task is done
        if task.done():
            try:
                # Clean up session
                _FEISHU_REGISTRATION_SESSIONS.pop(token, None)

                # Check for errors first
                if task.exception():
                    exc = task.exception()
                    error_msg = str(exc)

                    # Check for specific error types
                    if (
                        "AppAccessDeniedError" in error_msg
                        or "access_denied" in error_msg
                    ):
                        return PollResult(
                            status="fail",
                            credentials={
                                "fail_reason": "User denied authorization",
                            },
                        )
                    elif (
                        "AppExpiredError" in error_msg
                        or "expired_token" in error_msg
                    ):
                        return PollResult(
                            status="expired",
                            credentials={"fail_reason": "QR code expired"},
                        )
                    else:
                        return PollResult(
                            status="fail",
                            credentials={"fail_reason": error_msg},
                        )

                result = session["result"]

                if result and "client_id" in result:
                    # Success!
                    user_info = result.get("user_info", {})
                    return PollResult(
                        status="success",
                        credentials={
                            "app_id": result["client_id"],
                            "app_secret": result["client_secret"],
                            "open_id": user_info.get("open_id", ""),
                            "tenant_brand": user_info.get(
                                "tenant_brand",
                                "feishu",
                            ),
                        },
                    )
                else:
                    return PollResult(
                        status="fail",
                        credentials={"fail_reason": "No credentials returned"},
                    )
            except Exception as exc:
                import logging

                logging.error(
                    f"Feishu poll_status error: {exc}",
                    exc_info=True,
                )
                return PollResult(
                    status="fail",
                    credentials={"fail_reason": str(exc)},
                )
        else:
            # Still waiting
            return PollResult(status="waiting", credentials={})


# ---------------------------------------------------------------------------
# Handler registry – add new channels here
# ---------------------------------------------------------------------------

QRCODE_AUTH_HANDLERS: Dict[str, QRCodeAuthHandler] = {
    "wechat": WeChatQRCodeAuthHandler(),
    "wecom": WecomQRCodeAuthHandler(),
    "dingtalk": DingtalkQRCodeAuthHandler(),
    "feishu": FeishuQRCodeAuthHandler(),
}
