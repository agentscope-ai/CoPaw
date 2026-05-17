# -*- coding: utf-8 -*-
"""
QwenPaw Chat 页面对象

封装 Chat 页面的所有交互操作，提供业务级别的方法。
"""
from __future__ import annotations

import logging
from typing import Optional, List
from playwright.sync_api import (
    Page,
    Locator,
    TimeoutError as PlaywrightTimeoutError,
)  # noqa: W0622

from pages.base_page import BasePage
from config.settings import config


logger = logging.getLogger(__name__)


class ChatPage(BasePage):  # pylint: disable=too-many-public-methods
    """
    Chat 页面对象

    封装 Chat 页面的所有用户操作：
    - 新建对话
    - 发送消息
    - 文件上传
    - 会话管理
    - 模型切换
    - 技能调用
    """

    PAGE_TITLE = "QwenPaw Console"
    PAGE_URL = f"{config.base_url}/chat"

    # ========== 选择器定义 ==========
    # 页面组件库使用 qwenpaw- CSS 前缀

    # 导航和新建对话
    NEW_CHAT_BTN = "button:has(.spark-icon-spark-newChat-fill)"
    SESSION_LIST_BTN = "button:has(.spark-icon-spark-history-line)"

    # 输入区域
    CHAT_INPUT = "textarea.qwenpaw-sender-input"
    SEND_BTN = "button.qwenpaw-sender-actions-btn.qwenpaw-btn-primary"
    FILE_INPUT = 'input[type="file"]'
    UPLOAD_WRAPPER = "span.qwenpaw-upload-wrapper"

    # 消息区域
    USER_MESSAGE = ".qwenpaw-bubble.qwenpaw-bubble-end"
    AI_MESSAGE = ".qwenpaw-bubble.qwenpaw-bubble-start"
    MESSAGE_CONTAINER = ".qwenpaw-bubble.qwenpaw-bubble-start, .qwenpaw-bubble.qwenpaw-bubble-end"
    MESSAGE_LIST = ".qwenpaw-bubble-list-scroll"

    # 欢迎界面（检查输入框可见性）
    WELCOME_TEXT = "textarea.qwenpaw-sender-input"
    QUICK_ACTIONS = ".quick-action"

    # 会话管理（通过历史记录抽屉，CSS Module 类名）
    SESSION_ITEM = "[class*=chatSessionItem]"
    SESSION_ACTIVE = "[class*=chatSessionItem][class*=active]"
    SESSION_NAME = "[class*=chatSessionItem] [class*=name]"
    SESSION_PIN_BTN = "button:has(.spark-icon-spark-mark-line)"
    SESSION_EDIT_BTN = "button:has(.spark-icon-spark-edit-line)"
    SESSION_DELETE_BTN = "button:has(.spark-icon-spark-delete-line)"

    # 设置和模型
    MODEL_SELECTOR = ".qwenpaw-dropdown-trigger"
    MODEL_OPTION = ".qwenpaw-dropdown-menu-item"
    AGENT_SELECTOR = ".qwenpaw-select-selector"

    # 操作按钮
    COPY_BTN = 'span[title="复制"]'

    # 工具和技能详情
    TOOL_TOGGLE = ".qwenpaw-operate-card-header-arrow"
    TOOL_DETAILS = ".qwenpaw-operate-card"

    # 错误和提示
    ERROR_MESSAGE = ".qwenpaw-message-error, .qwenpaw-notification-error"
    SUCCESS_MESSAGE = ".qwenpaw-message-success, .qwenpaw-notification-success"
    COPY_SUCCESS = ".qwenpaw-message-success"

    # 抽屉和弹窗
    DRAWER_CLOSE = "[class*=headerRight] button"
    CONFIRM_BTN = 'button:has-text("确认"), button:has-text("OK"), .qwenpaw-btn-primary:has-text("确定")'
    CANCEL_BTN = 'button:has-text("取消"), button:has-text("Cancel")'

    # ========== 初始化 ==========

    def __init__(self, page: Page):
        super().__init__(page)
        logger.info("ChatPage initialized")

    # ========== 页面导航 ==========

    def open(self) -> "ChatPage":
        """打开 Chat 页面"""
        logger.info("Opening Chat page")
        self.goto()
        self.wait_for_loading()
        return self

    def is_loaded(self) -> bool:
        """检查页面是否加载完成"""
        try:
            # 检查输入框或欢迎文本是否存在
            return self.assert_visible(
                self.CHAT_INPUT,
                timeout=5000,
            ) or self.assert_visible(self.WELCOME_TEXT, timeout=5000)
        except Exception:
            return False

    # ========== 新建对话 ==========

    def create_new_chat(self) -> "ChatPage":
        """
        创建新对话

        Returns:
            self
        """
        logger.info("Creating new chat")
        # 重置发送状态（新会话不需要等上一个会话的 AI 响应）
        if hasattr(self, "_has_sent_message"):
            del self._has_sent_message
        self._ai_count_before_send = 0

        new_chat_btn = self.find(self.NEW_CHAT_BTN)
        if new_chat_btn.count() > 0:
            new_chat_btn.click()
            # 等待页面跳转并加载完成
            self.page.wait_for_load_state("networkidle")
            self.page.locator(self.CHAT_INPUT).wait_for(
                state="visible",
                timeout=10000,
            )
        return self

    def verify_welcome_screen(self) -> bool:
        """
        验证欢迎界面

        Returns:
            是否显示欢迎界面
        """
        logger.info("Verifying welcome screen")
        return self.assert_visible(self.WELCOME_TEXT, timeout=5000)

    def get_quick_actions(self) -> List[Locator]:
        """获取快捷操作按钮列表"""
        return self.find_all(self.QUICK_ACTIONS)

    def click_quick_action(self, index: int = 0) -> "ChatPage":
        """
        点击快捷操作按钮

        Args:
            index: 按钮索引

        Returns:
            self
        """
        actions = self.get_quick_actions()
        if actions and index < len(actions):
            actions[index].click()
            logger.info(f"Clicked quick action at index {index}")
        return self

    # ========== 发送消息 ==========

    def send_message(self, text: str) -> "ChatPage":
        """
        发送消息

        Args:
            text: 消息内容

        Returns:
            self
        """
        logger.info(f"Sending message: {text[:50]}...")

        # 如果之前发送过消息，等待发送按钮恢复可用（上一轮 AI 输出完成）
        if hasattr(self, "_has_sent_message"):
            try:
                self.page.wait_for_function(
                    """() => {
                        const btn = document.querySelector('button.qwenpaw-sender-actions-btn.qwenpaw-btn-primary');
                        return btn && !btn.disabled;
                    }""",
                    timeout=60000,
                )
                logger.info("Previous AI response completed, ready to send")
            except (PlaywrightTimeoutError, AssertionError, Exception):
                logger.warning("Previous AI response may not have completed")
        self._has_sent_message = True

        # 记录发送前的消息数量（供 wait_for_ai_response 使用）
        self._ai_count_before_send = self.page.locator(self.AI_MESSAGE).count()
        user_count_before = self.page.locator(self.USER_MESSAGE).count()

        # 填充输入框（先点击确保焦点）
        input_box = self.page.locator(self.CHAT_INPUT)
        input_box.click()
        self.wait(300)

        # 清空后填充，确保内容正确
        input_box.fill("")
        self.wait(200)
        input_box.fill(text)
        self.wait(500)

        # 点击发送按钮（比 Enter 更可靠）
        send_btn = self.page.locator(self.SEND_BTN)
        if send_btn.is_visible() and send_btn.is_enabled():
            send_btn.click()
        else:
            input_box.press("Enter")

        # 等待用户消息出现在 DOM 中，确认发送成功
        try:
            self.page.wait_for_function(
                f"""(expected) => {{
                    const msgs = document.querySelectorAll('.qwenpaw-bubble.qwenpaw-bubble-end');
                    return msgs.length > expected;
                }}""",
                arg=user_count_before,
                timeout=5000,
            )
            logger.info("Message sent successfully")
        except (PlaywrightTimeoutError, AssertionError, Exception):
            logger.warning(
                "Message may not have been sent, retrying with Enter",
            )
            input_box = self.page.locator(self.CHAT_INPUT)
            input_box.click()
            self.wait(200)
            input_box.press("Enter")

        self.wait(500)
        return self

    def send_message_and_wait(
        self,
        text: str,
        timeout: int = 30000,
    ) -> "ChatPage":
        """
        发送消息并等待 AI 回复

        Args:
            text: 消息内容
            timeout: 等待超时时间

        Returns:
            self
        """
        self.send_message(text)
        self.wait_for_ai_response(timeout)
        return self

    def get_user_messages(self) -> List[Locator]:
        """获取所有用户消息"""
        return self.page.locator(self.USER_MESSAGE).all()

    def get_ai_messages(self) -> List[Locator]:
        """获取所有 AI 消息"""
        return self.page.locator(self.AI_MESSAGE).all()

    def get_all_messages(self) -> List[Locator]:
        """获取所有消息"""
        return self.page.locator(self.MESSAGE_CONTAINER).all()

    def get_last_ai_message(self) -> Optional[Locator]:
        """获取最后一条 AI 消息"""
        messages = self.get_ai_messages()
        return messages[-1] if messages else None

    def wait_for_ai_response(self, timeout: int = 30000) -> Optional[Locator]:
        """
        等待 AI 回复完成

        分两步等待：
        1. 等待新的 AI 消息出现（消息数量增加）
        2. 等待发送按钮恢复可用（流式输出完成）

        Args:
            timeout: 超时时间（毫秒）

        Returns:
            AI 消息 Locator 或 None
        """
        logger.info(f"Waiting for AI response (timeout: {timeout}ms)")

        ai_locator = self.page.locator(self.AI_MESSAGE)
        count_before_send = getattr(
            self,
            "_ai_count_before_send",
            ai_locator.count(),
        )
        logger.info(
            f"count_before_send={count_before_send}, current_count={ai_locator.count()}",
        )

        # 第一步：等待 AI 消息出现（给大部分超时时间）
        try:
            self.page.wait_for_function(
                """(expectedCount) => {
                    const aiMsgs = document.querySelectorAll('.qwenpaw-bubble.qwenpaw-bubble-start');
                    return aiMsgs.length > expectedCount;
                }""",
                arg=count_before_send,
                timeout=timeout,
            )
            logger.info("AI message appeared")
        except (PlaywrightTimeoutError, AssertionError, Exception):
            logger.warning("AI response timeout - no message appeared")
            return None

        # 第二步：等待发送按钮恢复可用（流式输出完成，额外等 30s）
        try:
            self.page.wait_for_function(
                """() => {
                    const btn = document.querySelector('button.qwenpaw-sender-actions-btn.qwenpaw-btn-primary');
                    return btn && !btn.disabled;
                }""",
                timeout=30000,
            )
            logger.info("AI response completed")
        except (PlaywrightTimeoutError, AssertionError, Exception):
            logger.info(
                "AI message appeared but streaming not yet finished, continuing",
            )

        self.wait(500)
        return ai_locator.last

    # ========== 消息操作 ==========

    def copy_last_message(self) -> bool:
        """
        复制最后一条 AI 消息

        Returns:
            是否复制成功
        """
        logger.info("Copying last AI message")

        ai_msg = self.get_last_ai_message()
        if not ai_msg:
            logger.warning("No AI message to copy")
            return False

        copy_btn = ai_msg.locator(self.COPY_BTN).first
        if copy_btn.count() > 0:
            copy_btn.click()
            self.wait(500)

            # 验证复制成功
            if self.assert_visible(self.COPY_SUCCESS, timeout=3000):
                logger.info("Message copied successfully")
                return True

        logger.warning("Copy failed or not available")
        return False

    def get_message_text(self, message_locator: Locator) -> str:
        """
        获取消息文本内容

        Args:
            message_locator: 消息 Locator

        Returns:
            消息文本
        """
        return message_locator.inner_text()

    def verify_message_contains(
        self,
        message_locator: Locator,
        expected_text: str,
    ) -> bool:
        """
        验证消息包含指定文本

        Args:
            message_locator: 消息 Locator
            expected_text: 期望包含的文本

        Returns:
            是否包含
        """
        text = self.get_message_text(message_locator)
        return expected_text.lower() in text.lower()

    # ========== 文件上传 ==========

    def upload_file(self, file_path: str) -> "ChatPage":
        """
        上传文件

        Args:
            file_path: 文件路径

        Returns:
            self
        """
        logger.info(f"Uploading file: {file_path}")

        # 直接通过 file input 设置文件（无需点击上传按钮）
        file_input = self.page.locator(self.FILE_INPUT)
        file_input.set_input_files(file_path)

        self.wait(2000)  # 等待上传完成
        logger.info("File upload initiated")
        return self

    def verify_file_uploaded(self, timeout: int = 10000) -> bool:
        """
        验证文件上传成功

        Args:
            timeout: 超时时间

        Returns:
            是否上传成功
        """
        file_preview_selector = '.qwenpaw-upload-list-item, .qwenpaw-sender-content [class*="file"], [class*="attachment"]'
        return self.assert_visible(file_preview_selector, timeout=timeout)

    # ========== 会话管理 ==========

    def open_session_list(self) -> "ChatPage":
        """打开会话列表"""
        logger.info("Opening session list")
        session_btn = self.find(self.SESSION_LIST_BTN)
        session_btn.click()
        # 等待会话列表抽屉渲染完成
        try:
            self.page.locator(self.SESSION_ITEM).first.wait_for(
                state="visible",
                timeout=8000,
            )
        except (PlaywrightTimeoutError, Exception):
            logger.warning("Session list may be empty or slow to render")
        self.wait(500)
        return self

    def close_session_list(self) -> "ChatPage":
        """关闭会话列表"""
        logger.info("Closing session list")
        close_btn = self.page.locator(".qwenpaw-drawer " + self.DRAWER_CLOSE)
        if close_btn.count() > 0:
            close_btn.first.click()
            self.wait(500)
        return self

    def get_session_items(self) -> List[Locator]:
        """获取所有会话项"""
        return self.page.locator(self.SESSION_ITEM).all()

    def get_session_count(self) -> int:
        """获取会话数量"""
        return len(self.get_session_items())

    def switch_to_session(self, index: int = 0) -> "ChatPage":
        """
        切换到指定会话

        Args:
            index: 会话索引

        Returns:
            self
        """
        sessions = self.get_session_items()
        if sessions and index < len(sessions):
            sessions[index].click()
            self.wait(1000)
            logger.info(f"Switched to session at index {index}")
        return self

    def rename_session(self, index: int, new_name: str) -> "ChatPage":
        """
        重命名会话（hover 后点击编辑按钮，输入新名称后按 Enter）

        Args:
            index: 会话索引
            new_name: 新名称

        Returns:
            self
        """
        logger.info(f"Renaming session {index} to: {new_name}")

        sessions = self.get_session_items()
        if not sessions or index >= len(sessions):
            logger.warning(f"Session at index {index} not found")
            return self

        # hover 会话项以显示操作按钮
        sessions[index].hover()
        self.wait(500)

        # 点击编辑按钮
        edit_btn = sessions[index].locator(self.SESSION_EDIT_BTN)
        if edit_btn.count() == 0:
            logger.warning("Edit button not found")
            return self
        edit_btn.first.click()
        self.wait(500)

        # 在出现的 input 中输入新名称
        rename_input = sessions[index].locator("input.qwenpaw-input")
        rename_input.fill(new_name)
        rename_input.press("Enter")
        self.wait(1000)

        logger.info(f"Session renamed to: {new_name}")
        return self

    def pin_session(self, index: int) -> "ChatPage":
        """
        置顶会话（点击会话项内的置顶按钮）

        Args:
            index: 会话索引

        Returns:
            self
        """
        logger.info(f"Pinning session at index {index}")

        sessions = self.get_session_items()
        if not sessions or index >= len(sessions):
            logger.warning(f"Session at index {index} not found")
            return self

        # 直接点击会话项内的置顶按钮
        pin_btn = sessions[index].locator(self.SESSION_PIN_BTN)
        if pin_btn.count() > 0:
            pin_btn.first.click()
            self.wait(1000)
            logger.info("Session pinned")
        else:
            logger.warning("Pin button not found in session item")

        return self

    def delete_session(self, index: int) -> "ChatPage":
        """
        删除会话（hover 后点击删除按钮，直接删除无确认弹窗）

        Args:
            index: 会话索引

        Returns:
            self
        """
        logger.info(f"Deleting session at index {index}")

        sessions_before = self.get_session_count()
        sessions = self.get_session_items()

        if not sessions or index >= len(sessions):
            logger.warning(f"Session at index {index} not found")
            return self

        # hover 会话项以显示操作按钮
        sessions[index].hover()
        self.wait(500)

        # 点击删除按钮（直接删除，无确认弹窗）
        del_btn = sessions[index].locator(self.SESSION_DELETE_BTN)
        if del_btn.count() == 0:
            logger.warning("Delete button not found")
            return self
        del_btn.first.click()
        self.wait(1000)

        logger.info(
            f"Session deleted (before: {sessions_before}, after: {self.get_session_count()})",
        )
        return self

    def verify_pinned_session(self) -> bool:
        """验证是否有置顶的会话（通过 data-pinned 属性判断）"""
        pinned_btn = self.page.locator(
            '[class*=pinButton][data-pinned="true"]',
        )
        return pinned_btn.count() > 0

    # ========== 模型和 Agent 切换 ==========

    def open_model_selector(self) -> "ChatPage":
        """打开模型选择器"""
        logger.info("Opening model selector")
        # 模型选择器在 header 右侧区域
        header = self.page.locator(
            ".qwenpaw-chat-anywhere-layout-right-header",
        )
        model_btn = header.locator(self.MODEL_SELECTOR).first
        model_btn.click()
        self.wait(500)
        return self

    def select_model(self, model_name: str) -> "ChatPage":
        """
        选择模型

        Args:
            model_name: 模型名称

        Returns:
            self
        """
        logger.info(f"Selecting model: {model_name}")

        # 查找并选择模型
        model_option = (
            self.page.locator(self.MODEL_OPTION)
            .filter(has_text=model_name)
            .first
        )
        if model_option.count() > 0:
            model_option.click()
            self.wait(1000)
            logger.info(f"Model selected: {model_name}")

        return self

    def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        options = self.page.locator(self.MODEL_OPTION).all()
        models = [opt.inner_text() for opt in options]
        return models

    def open_agent_selector(self) -> "ChatPage":
        """打开 Agent 选择器"""
        logger.info("Opening agent selector")
        agent_btn = self.page.locator(self.AGENT_SELECTOR).first
        if agent_btn.count() > 0:
            agent_btn.click()
            self.wait(500)
        return self

    # ========== 技能调用 ==========

    def invoke_skill(
        self,
        skill_name: str,
        input_text: str = "",
    ) -> "ChatPage":
        """
        调用技能

        Args:
            skill_name: 技能名称
            input_text: 输入参数

        Returns:
            self
        """
        command = f"/{skill_name}"
        if input_text:
            command += f" {input_text}"

        logger.info(f"Invoking skill: {command}")
        return self.send_message_and_wait(command)

    def get_skills_list(self) -> Optional[str]:
        """获取技能列表（通过 /skills 命令）"""
        self.send_message("/skills")
        response = self.wait_for_ai_response()
        if response:
            return self.get_message_text(response)
        return None

    # ========== 工具详情 ==========

    def expand_tool_details(self, message_index: int = -1) -> bool:
        """
        展开工具调用详情

        Args:
            message_index: 消息索引（-1 表示最后一条）

        Returns:
            是否展开成功
        """
        messages = self.get_ai_messages()
        if not messages:
            return False

        target_msg = messages[message_index]
        toggle_btn = target_msg.locator(self.TOOL_TOGGLE).first

        if toggle_btn.count() > 0:
            toggle_btn.click()
            self.wait(500)
            return self.assert_visible(self.TOOL_DETAILS, timeout=3000)

        return False

    # ========== 错误处理 ==========

    def has_error(self) -> bool:
        """检查是否有错误消息"""
        return self.assert_visible(self.ERROR_MESSAGE, timeout=2000)

    def get_error_message(self) -> Optional[str]:
        """获取错误消息文本"""
        error = self.find(self.ERROR_MESSAGE)
        if error.count() > 0:
            return error.inner_text()
        return None

    def dismiss_error(self) -> "ChatPage":
        """关闭错误消息"""
        error = self.find(self.ERROR_MESSAGE)
        if error.count() > 0:
            close_btn = error.locator(
                ".qwenpaw-message-close, .qwenpaw-notification-close",
            ).first
            if close_btn.count() > 0:
                close_btn.click()
                self.wait(500)
        return self

    # ========== 滚动和导航 ==========

    def scroll_to_top(self) -> "ChatPage":
        """滚动消息列表到顶部"""
        self.page.evaluate(
            """() => {
            const list = document.querySelector('.qwenpaw-bubble-list-scroll');
            if (list) list.scrollTop = 0;
        }""",
        )
        self.wait(500)
        return self

    def scroll_to_bottom(self) -> "ChatPage":
        """滚动消息列表到底部"""
        self.page.evaluate(
            """() => {
            const list = document.querySelector('.qwenpaw-bubble-list-scroll');
            if (list) list.scrollTop = list.scrollHeight;
        }""",
        )
        self.wait(500)
        return self

    def scroll_to_message(self, message_index: int) -> "ChatPage":
        """
        滚动到指定消息

        Args:
            message_index: 消息索引

        Returns:
            self
        """
        messages = self.get_all_messages()
        if messages and message_index < len(messages):
            messages[message_index].scroll_into_view_if_needed()
            self.wait(500)
        return self

    # ========== 组合操作 ==========

    def complete_chat_flow(self, messages: List[str]) -> "ChatPage":
        """
        完成完整的对话流程

        Args:
            messages: 要发送的消息列表

        Returns:
            self
        """
        logger.info(f"Starting chat flow with {len(messages)} messages")

        for msg in messages:
            self.send_message_and_wait(msg)

        logger.info("Chat flow completed")
        return self

    def create_chat_and_send(self, message: str) -> "ChatPage":
        """
        创建新对话并发送消息

        Args:
            message: 消息内容

        Returns:
            self
        """
        return self.create_new_chat().send_message_and_wait(message)

    # ========== 清理 ==========

    def delete_all_sessions(self, max_attempts: int = 50) -> "ChatPage":
        """
        删除所有会话，用于测试后清理数据

        Args:
            max_attempts: 最大删除次数，防止无限循环

        Returns:
            self
        """
        logger.info("Cleaning up: deleting all sessions")

        self.open_session_list()
        deleted_count = 0

        for _ in range(max_attempts):
            session_count = self.get_session_count()
            if session_count == 0:
                break

            try:
                self.delete_session(0)
                deleted_count += 1
            except Exception as error:
                logger.warning(f"Failed to delete session: {error}")
                break

        logger.info(f"Cleanup complete: deleted {deleted_count} sessions")
        return self
