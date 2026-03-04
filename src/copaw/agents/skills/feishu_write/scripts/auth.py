# -*- coding: utf-8 -*-
"""
飞书认证模块
"""

from typing import Optional
import requests


class FeishuAuth:
    """飞书认证模块"""

    TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"

    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self._token: Optional[str] = None

    def get_token(self) -> str:
        """获取 tenant_access_token"""
        if self._token:
            return self._token

        resp = requests.post(self.TOKEN_URL, json={
            "app_id": self.app_id,
            "app_secret": self.app_secret
        })
        resp.raise_for_status()
        data = resp.json()

        if data.get("code") != 0:
            raise Exception(f"获取 token 失败: {data.get('msg')}")

        self._token = data["tenant_access_token"]
        return self._token
