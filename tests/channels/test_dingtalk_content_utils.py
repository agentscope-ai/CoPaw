# -*- coding: utf-8 -*-
from copaw.app.channels.dingtalk.content_utils import (
    sender_from_chatbot_message,
)


class Dummy:
    pass


def test_sender_skip_when_missing_id_and_nickname():
    m = Dummy()
    m.sender_nick = ""
    m.sender_id = ""
    sender, skip = sender_from_chatbot_message(m)
    assert sender == "unknown#????"
    assert skip is True


def test_sender_not_skip_when_has_nickname_only():
    m = Dummy()
    m.sender_nick = "alice"
    m.sender_id = ""
    sender, skip = sender_from_chatbot_message(m)
    assert sender.startswith("alice#")
    assert skip is False


def test_sender_suffix_last4_when_has_id():
    m = Dummy()
    m.sender_nick = ""
    m.sender_id = "abcdef123456"
    sender, skip = sender_from_chatbot_message(m)
    assert sender.endswith("#3456")
    assert skip is False
