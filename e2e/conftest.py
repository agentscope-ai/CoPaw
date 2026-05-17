# -*- coding: utf-8 -*-
"""
QwenPaw E2E 测试框架 - Pytest 配置
"""
from __future__ import annotations

import sys
import time
import logging
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import pytest  # noqa: E402
from pages.chat_page import ChatPage  # noqa: E402


def pytest_configure(config):
    """配置 pytest 标记"""
    # Test tier markers
    config.addinivalue_line(
        "markers",
        "ui_smoke: UI smoke test (mocked API, no backend needed)",
    )
    config.addinivalue_line(
        "markers",
        "integration: Integration test (requires running backend + API keys)",
    )

    # Legacy markers (kept for backward compatibility)
    config.addinivalue_line(
        "markers",
        "p0: P0 level test - legacy, use integration instead",
    )
    config.addinivalue_line("markers", "p1: P1 level test - legacy")
    config.addinivalue_line("markers", "p2: P2 level test - legacy")

    # Feature markers
    config.addinivalue_line("markers", "chat_core: Chat core functionality")
    config.addinivalue_line("markers", "chat_context: Chat context awareness")
    config.addinivalue_line("markers", "chat_file: Chat file upload")
    config.addinivalue_line("markers", "chat_session: Chat session management")
    config.addinivalue_line("markers", "chat_advanced: Chat advanced features")
    config.addinivalue_line(
        "markers",
        "chat_validation: Chat input validation",
    )

    # Page feature markers
    config.addinivalue_line("markers", "agents_list: Agents list view")
    config.addinivalue_line("markers", "agents_crud: Agents CRUD operations")
    config.addinivalue_line("markers", "agents_toggle: Agents enable/disable")
    config.addinivalue_line("markers", "agents_sort: Agents drag sort")
    config.addinivalue_line("markers", "channels_list: Channels grid view")
    config.addinivalue_line("markers", "channels_filter: Channels filter tabs")
    config.addinivalue_line(
        "markers",
        "channels_toggle: Channels enable/disable",
    )
    config.addinivalue_line("markers", "sessions_list: Sessions table view")
    config.addinivalue_line("markers", "sessions_filter: Sessions filter")
    config.addinivalue_line("markers", "sessions_actions: Sessions actions")
    config.addinivalue_line("markers", "cronjobs_list: CronJobs table view")
    config.addinivalue_line(
        "markers",
        "cronjobs_crud: CronJobs CRUD operations",
    )
    config.addinivalue_line(
        "markers",
        "heartbeat_config: Heartbeat configuration",
    )
    config.addinivalue_line("markers", "models_list: Models provider list")
    config.addinivalue_line("markers", "models_config: Models provider config")
    config.addinivalue_line("markers", "models_manage: Models enable/disable")
    config.addinivalue_line(
        "markers",
        "security_tabs: Security tabs navigation",
    )
    config.addinivalue_line("markers", "envs_list: Environments list view")
    config.addinivalue_line("markers", "envs_crud: Environments CRUD")
    config.addinivalue_line("markers", "backups_list: Backups list view")
    config.addinivalue_line("markers", "backups_create: Backups create")
    config.addinivalue_line("markers", "login_form: Login form rendering")
    config.addinivalue_line("markers", "login_flow: Login flow validation")
    config.addinivalue_line(
        "markers",
        "login_redirect: Login redirect behavior",
    )

    config.addinivalue_line("markers", "test_id: Test case ID")


# ========== Fixtures ==========


@pytest.fixture(scope="function")
def mock_api(page):
    """
    Register all API route mocks for UI smoke tests.

    Intercepts all /api/ requests and returns mock JSON responses,
    so smoke tests only need a frontend dev server running.
    """
    from mocks import register_all

    register_all(page)
    yield page


@pytest.fixture(scope="function")
def chat_page(page):
    """
    创建 ChatPage 实例（不带清理）

    依赖 pytest-playwright 提供的 page fixture
    """
    return ChatPage(page)


@pytest.fixture(scope="function")
def clean_chat_page(page):
    """
    创建 ChatPage 实例，测试结束后自动清理所有会话数据。

    适用于会创建新对话的测试用例，确保测试后不留残余数据。
    """
    chat = ChatPage(page)
    yield chat
    try:
        chat.delete_all_sessions()
    except Exception:
        pass


@pytest.fixture(scope="function")
def test_file(tmp_path):
    """
    创建用于上传测试的临时文件

    Returns:
        临时文件路径字符串
    """
    file_path = tmp_path / "test_document.txt"
    file_path.write_text(
        "QwenPaw 平台功能介绍\n\n"
        "QwenPaw 是一个智能对话平台，支持以下功能：\n"
        "1. 智能问答\n"
        "2. 文件分析\n"
        "3. 代码生成\n"
        "4. 多轮对话\n",
        encoding="utf-8",
    )
    return str(file_path)


@pytest.fixture(scope="function")
def large_test_file(tmp_path):
    """
    创建超过 10MB 的大文件用于测试文件大小限制

    Returns:
        大文件路径字符串
    """
    file_path = tmp_path / "large_file.txt"
    chunk = "A" * 1024  # 1KB
    with open(file_path, "w", encoding="utf-8") as f:
        for _ in range(11 * 1024):
            f.write(chunk)
    return str(file_path)


# ========== Hooks ==========


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    跟踪测试执行状态，用于失败时截图
    """
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


def pytest_runtest_logreport(report):
    """记录测试报告"""
    if report.failed:
        pass


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """测试结束时的终端摘要"""
    passed = len(terminalreporter.getreports("passed"))
    failed = len(terminalreporter.getreports("failed"))
    skipped = len(terminalreporter.getreports("skipped"))
    total = passed + failed + skipped

    terminalreporter.write_sep("=" * 60)
    terminalreporter.write_line("测试摘要:")
    terminalreporter.write_line(f"  总计：{total}")
    terminalreporter.write_line(f"  通过：{passed}")
    terminalreporter.write_line(f"  失败：{failed}")
    terminalreporter.write_line(f"  跳过：{skipped}")

    if total > 0:
        pass_rate = passed / total * 100
        terminalreporter.write_line(f"  通过率：{pass_rate:.1f}%")
    terminalreporter.write_sep("=" * 60)


# ========== 清理 ==========

_logger = logging.getLogger(__name__)

# 报告文件保留天数
REPORT_RETENTION_DAYS = 7


def pytest_sessionfinish(session, exitstatus):
    """测试会话结束后清理过期的报告和日志文件"""
    reports_dir = Path(__file__).parent / "reports"
    if not reports_dir.exists():
        return

    cutoff_time = time.time() - REPORT_RETENTION_DAYS * 86400
    cleaned_count = 0

    cleanup_patterns = ["*.png", "*.html", "*.log", "*.webm"]
    for pattern in cleanup_patterns:
        for file_path in reports_dir.glob(pattern):
            try:
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    cleaned_count += 1
            except OSError:
                pass

    if cleaned_count > 0:
        _logger.info(
            f"Cleaned up {cleaned_count} report files older than "
            f"{REPORT_RETENTION_DAYS} days",
        )
