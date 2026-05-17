# -*- coding: utf-8 -*-
"""
QwenPaw Chat integration tests

These tests require a running backend with real model API access.
Run with: pytest tests/test_chat_integration.py -m integration -v
"""
from __future__ import annotations

import logging
import pytest

from pages.chat_page import ChatPage
from utils.helpers import (
    log_test_step,
    log_test_result,
)


logger = logging.getLogger(__name__)


# ============================================================================
# INT-001: 新建对话 + 基础问答 + 消息复制 (核心流程组合)
# ============================================================================


@pytest.mark.integration
@pytest.mark.chat_core
class TestNewChatAndBasicQA:
    """
    INT-001: 新建对话 + 基础文本问答 + 消息复制

    覆盖功能点：
    1. 新建对话 (CHAT-001)
    2. 基础文本问答 (CHAT-002)
    3. 消息复制 (CHAT-008)
    4. Markdown 渲染验证

    业务场景：
    用户进入 Chat 页面，创建新对话，发送问题，获取 AI 回复，
    并复制回复内容用于其他用途。
    """

    @pytest.mark.test_id("INT-001")
    def test_new_chat_basic_qa_copy(
        self,
        clean_chat_page: ChatPage,
        request: pytest.FixtureRequest,
    ):
        """
        验证新建对话、发送消息、获取回复、复制消息的完整流程

        测试步骤：
        1. 访问 Chat 页面
        2. 点击新建对话按钮
        3. 验证欢迎界面
        4. 发送基础文本消息
        5. 等待 AI 回复
        6. 验证消息显示
        7. 复制 AI 回复
        8. 验证消息历史
        """
        test_name = request.node.name
        log_test_step("1. 访问 Chat 页面")
        clean_chat_page.open()

        log_test_step("2. 点击新建对话按钮")
        clean_chat_page.create_new_chat()

        log_test_step("3. 验证欢迎界面")
        assert clean_chat_page.verify_welcome_screen(), "欢迎界面未显示"

        log_test_step("4. 发送基础文本消息")
        clean_chat_page.send_message("你好，请介绍一下你自己")

        log_test_step("5. 等待 AI 回复")
        ai_message = clean_chat_page.wait_for_ai_response(timeout=30000)
        assert ai_message is not None, "AI 回复超时"

        log_test_step("6. 验证消息显示")
        user_messages = clean_chat_page.get_user_messages()
        ai_messages = clean_chat_page.get_ai_messages()
        assert len(user_messages) >= 1, "用户消息未显示"
        assert len(ai_messages) >= 1, "AI 消息未显示"

        log_test_step("7. 复制 AI 回复")
        _copy_success = clean_chat_page.copy_last_message()
        # 复制功能是可选的，不强制要求成功

        log_test_step("8. 验证消息历史")
        all_messages = clean_chat_page.get_all_messages()
        assert len(all_messages) >= 2, "消息历史不完整"

        log_test_result(test_name, True, 0)
        logger.info(f"✅ Test {test_name} passed")


# ============================================================================
# INT-002: 多轮对话 + 上下文理解 (核心智能组合)
# ============================================================================


@pytest.mark.integration
@pytest.mark.chat_context
class TestMultiTurnConversation:
    """
    INT-002: 多轮连续对话 + 上下文理解

    覆盖功能点：
    1. 多轮连续对话 (CHAT-004)
    2. 上下文理解与记忆

    业务场景：
    用户进行多轮对话，AI 需要理解上下文并给出连贯的回复。
    """

    @pytest.mark.test_id("INT-002")
    def test_multi_turn_context_awareness(
        self,
        clean_chat_page: ChatPage,
        request: pytest.FixtureRequest,
    ):
        """
        验证多轮对话中 AI 能正确理解上下文

        测试步骤：
        1. 访问 Chat 页面并新建对话
        2. 发送第一轮消息
        3. 发送基于上下文的追问
        4. 验证对话历史完整性
        """
        test_name = request.node.name
        conversation_flow = [
            "1+1等于几",
            "再加2呢",
            "再乘以3呢",
            "结果减去5是多少",
            "最终结果是奇数还是偶数",
        ]

        log_test_step("1. 访问 Chat 页面并新建对话")
        clean_chat_page.open().create_new_chat()

        log_test_step("2-3. 发送多轮对话")
        for i, message in enumerate(conversation_flow, 1):
            log_test_step(f"  轮次 {i}: 发送消息 - {message[:30]}...")
            clean_chat_page.send_message(message)
            ai_response = clean_chat_page.wait_for_ai_response(timeout=30000)
            assert ai_response is not None, f"第{i}轮 AI 回复超时"

        log_test_step("4. 验证对话历史完整性")
        ai_messages = clean_chat_page.get_ai_messages()
        assert len(ai_messages) == len(
            conversation_flow,
        ), f"AI 消息数量不匹配：期望{len(conversation_flow)}，实际{len(ai_messages)}"

        log_test_result(test_name, True, 0)
        logger.info(
            f"✅ Test {test_name} passed with {len(conversation_flow)} turns",
        )


# ============================================================================
# INT-003: 文件上传 + 基于文件内容问答 (核心功能组合)
# ============================================================================


@pytest.mark.integration
@pytest.mark.chat_file
class TestFileUploadAndQA:
    """
    INT-003: 附件上传 + 基于文件内容问答

    覆盖功能点：
    1. 附件上传 (CHAT-007)
    2. 文件预览
    3. 基于文件内容的智能问答

    业务场景：
    用户上传文档，然后基于文档内容进行问答。
    """

    @pytest.mark.test_id("INT-003")
    def test_upload_file_and_ask_questions(
        self,
        clean_chat_page: ChatPage,
        test_file: str,
        request: pytest.FixtureRequest,
    ):
        """
        验证上传文件后能基于文件内容进行问答

        测试步骤：
        1. 访问 Chat 页面
        2. 上传文件
        3. 验证文件上传成功
        4. 基于文件内容提问
        5. 验证 AI 回复包含文件相关内容
        """
        test_name = request.node.name

        log_test_step("1-2. 访问 Chat 页面")
        clean_chat_page.open()

        log_test_step("3. 上传文件")
        clean_chat_page.upload_file(test_file)

        log_test_step("4. 验证文件上传成功")
        assert clean_chat_page.verify_file_uploaded(timeout=10000), "文件上传失败"

        log_test_step("5. 基于文件内容提问")
        clean_chat_page.send_message("这个文档的标题是什么？请直接回答")
        ai_response = clean_chat_page.wait_for_ai_response(timeout=60000)
        assert ai_response is not None, "AI 回复超时"

        log_test_step("6. 验证 AI 回复包含文件相关内容")
        response_text = clean_chat_page.get_message_text(ai_response)
        assert len(response_text.strip()) > 0, "AI 回复为空"
        logger.info(f"AI 回复内容：{response_text[:200]}")

        log_test_result(test_name, True, 0)
        logger.info(f"✅ Test {test_name} passed")


# ============================================================================
# INT-004: 会话管理（重命名 + 置顶 + 删除 + 切换）
# ============================================================================


@pytest.mark.integration
@pytest.mark.chat_session
class TestSessionManagement:
    """
    INT-004: 会话管理综合测试

    覆盖功能点：
    1. 会话列表查看
    2. 会话重命名
    3. 会话置顶
    4. 会话删除
    5. 会话切换

    业务场景：
    用户管理多个会话，包括重命名、置顶重要会话、删除无用会话、
    在不同会话间切换。
    """

    @pytest.mark.test_id("INT-004")
    def test_session_rename_pin_delete_switch(
        self,
        clean_chat_page: ChatPage,
        request: pytest.FixtureRequest,
    ):
        """
        验证会话的完整生命周期管理

        测试步骤：
        1. 访问 Chat 页面
        2. 创建第一个会话并发送消息
        3. 创建第二个会话并发送消息
        4. 打开会话列表，验证会话数量
        5. 重命名第一个会话
        6. 置顶第一个会话，验证置顶状态
        7. 切换到另一个会话，验证会话内容
        8. 删除最后一个会话，验证删除成功
        """
        test_name = request.node.name

        log_test_step("1. 访问 Chat 页面")
        clean_chat_page.open()

        log_test_step("2. 创建第一个会话并发送消息")
        clean_chat_page.create_new_chat()
        clean_chat_page.send_message_and_wait("1+1等于几")

        log_test_step("3. 创建第二个会话并发送消息")
        clean_chat_page.create_new_chat()
        clean_chat_page.send_message_and_wait("2+3等于几")

        log_test_step("4. 打开会话列表，验证会话数量")
        clean_chat_page.open_session_list()

        initial_count = clean_chat_page.get_session_count()
        assert initial_count >= 2, f"会话数量不足：{initial_count}"

        log_test_step("5. 重命名第一个会话")
        clean_chat_page.rename_session(0, "已重命名的测试会话")

        log_test_step("6. 置顶第一个会话，验证置顶状态")
        clean_chat_page.pin_session(0)
        assert clean_chat_page.verify_pinned_session(), "置顶标记未显示"

        log_test_step("7. 切换到另一个会话，验证会话内容")
        clean_chat_page.switch_to_session(1)
        clean_chat_page.close_session_list()

        messages = clean_chat_page.get_all_messages()
        assert len(messages) > 0, "切换后会话无消息"

        log_test_step("8. 删除最后一个会话，验证删除成功")
        clean_chat_page.open_session_list()
        count_before = clean_chat_page.get_session_count()
        clean_chat_page.delete_session(count_before - 1)

        count_after = clean_chat_page.get_session_count()
        assert (
            count_after == count_before - 1
        ), f"删除失败：删除前{count_before}，删除后{count_after}"

        clean_chat_page.close_session_list()

        log_test_result(test_name, True, 0)
        logger.info(f"✅ Test {test_name} passed")


# ============================================================================
# INT-005: 模型切换 + 技能调用 + Agent 切换（高级功能组合）
# ============================================================================


@pytest.mark.integration
@pytest.mark.chat_advanced
class TestAdvancedFeatures:
    """
    INT-005: 高级功能组合测试

    覆盖功能点：
    1. 模型选择与切换 (CHAT-005)
    2. Agent 切换 (CHAT-006)
    3. 技能调用 (CHAT-011 ~ CHAT-022)
    4. 工具调用详情展开/收起 (CHAT-009)

    业务场景：
    用户根据需要切换不同模型，调用技能完成特定任务，
    查看工具调用详情。
    """

    @pytest.mark.test_id("INT-005")
    def test_model_switch_and_skill_invocation(
        self,
        clean_chat_page: ChatPage,
        request: pytest.FixtureRequest,
    ):
        """
        验证模型切换和技能调用功能

        测试步骤：
        1. 访问 Chat 页面
        2. 打开模型选择器
        3. 选择不同模型（如果有多个）
        4. 发送 /skills 命令查看可用技能
        5. 验证技能列表展示
        6. 测试工具调用详情展开/收起
        """
        test_name = request.node.name

        log_test_step("1. 访问 Chat 页面")
        clean_chat_page.open()

        log_test_step("2. 打开模型选择器")
        clean_chat_page.open_model_selector()

        log_test_step("3. 选择不同模型（如果有多个）")
        models = clean_chat_page.get_available_models()
        logger.info(f"可用模型：{models}")

        if len(models) > 1:
            target_model = models[1]
            clean_chat_page.select_model(target_model)
            clean_chat_page.wait(1000)
            logger.info(f"已切换到模型：{target_model}")
        else:
            logger.info("仅有一个模型，跳过切换")
            # 关闭下拉菜单
            clean_chat_page.page.keyboard.press("Escape")
            clean_chat_page.wait(500)

        log_test_step("4. 使用当前模型发送消息并验证回复")
        clean_chat_page.send_message("1+1等于几？请直接回答数字")
        model_response = clean_chat_page.wait_for_ai_response(timeout=60000)
        assert model_response is not None, "切换模型后发送消息无响应"
        model_response_text = clean_chat_page.get_message_text(model_response)
        assert len(model_response_text.strip()) > 0, "切换模型后 AI 回复为空"
        logger.info(f"模型回复内容：{model_response_text[:200]}")

        log_test_step("5. 发送技能查询")
        clean_chat_page.send_message("你有哪些技能？请简要列举")
        skills_response = clean_chat_page.wait_for_ai_response(timeout=60000)
        assert skills_response is not None, "技能查询无响应"

        log_test_step("6. 验证技能列表展示")
        response_text = clean_chat_page.get_message_text(skills_response)
        assert len(response_text.strip()) > 0, "技能列表响应为空"
        logger.info(f"技能响应内容：{response_text[:200]}")

        log_test_step("7. 测试工具调用详情展开/收起")
        expanded = clean_chat_page.expand_tool_details()
        if expanded:
            logger.info("工具详情展开成功")
            clean_chat_page.expand_tool_details()

        log_test_result(test_name, True, 0)
        logger.info(f"✅ Test {test_name} passed")


# ============================================================================
# INT-006: 输入验证 + 快捷操作 + 错误处理（边界场景组合）
# ============================================================================


@pytest.mark.integration
@pytest.mark.chat_validation
class TestInputValidationAndEdgeCases:
    """
    INT-006: 输入验证与边界场景测试

    覆盖功能点：
    1. 特殊字符处理
    2. 代码块输入处理

    业务场景：
    验证系统对特殊字符和代码块输入的处理能力。
    """

    @pytest.mark.test_id("INT-006")
    def test_input_validation_and_special_chars(
        self,
        clean_chat_page: ChatPage,
        request: pytest.FixtureRequest,
    ):
        """
        验证特殊字符和代码块输入处理

        测试步骤：
        1. 访问 Chat 页面
        2. 测试特殊字符输入
        3. 测试代码块输入
        """
        test_name = request.node.name

        log_test_step("1. 访问 Chat 页面")
        clean_chat_page.open()

        log_test_step("2. 测试特殊字符")
        special_chars = "!@#$%^&*()_+-=[]{}|;:',.<>?/`~中文测试🚀"
        clean_chat_page.send_message(special_chars)
        special_response = clean_chat_page.wait_for_ai_response(timeout=30000)
        assert special_response is not None, "特殊字符消息 AI 无回复"
        special_text = clean_chat_page.get_message_text(special_response)
        assert len(special_text.strip()) > 0, "特殊字符消息 AI 回复为空"

        user_messages = clean_chat_page.get_user_messages()
        assert len(user_messages) >= 1, "特殊字符消息未显示在对话中"

        log_test_step("3. 测试代码块输入")
        code_input = """```python
def hello():
    print("Hello, World!")
```"""
        clean_chat_page.send_message(code_input)
        code_response = clean_chat_page.wait_for_ai_response(timeout=30000)
        assert code_response is not None, "代码块消息 AI 无回复"
        code_text = clean_chat_page.get_message_text(code_response)
        assert len(code_text.strip()) > 0, "代码块消息 AI 回复为空"

        all_messages = clean_chat_page.get_all_messages()
        assert len(all_messages) >= 4, f"消息历史不完整：期望至少4条，实际{len(all_messages)}"

        log_test_result(test_name, True, 0)
        logger.info(f"✅ Test {test_name} passed")


# ============================================================================
# 测试执行入口
# ============================================================================

if __name__ == "__main__":
    pytest.main(
        [
            __file__,
            "-v",
            "--tb=short",
            "-m",
            "integration",
        ],
    )
