# -*- coding: utf-8 -*-
import json

from copaw.app.channels.feishu_post import parse_feishu_post_content


def test_parse_feishu_post_content_extracts_text_and_image() -> None:
    content = json.dumps(
        {
            "zh_cn": {
                "title": "",
                "content": [
                    [
                        {"tag": "text", "text": "hello "},
                        {"tag": "a", "text": "world"},
                    ],
                    [
                        {"tag": "img", "image_key": "img_v2_123"},
                    ],
                ],
            },
        },
        ensure_ascii=False,
    )

    texts, image_keys = parse_feishu_post_content(content)

    assert texts == ["hello world"]
    assert image_keys == ["img_v2_123"]


def test_parse_feishu_post_content_extracts_image_only_post() -> None:
    content = json.dumps(
        {
            "zh_cn": {
                "title": "",
                "content": [
                    [
                        {"tag": "img", "image_key": "img_v2_only"},
                    ],
                ],
            },
        },
        ensure_ascii=False,
    )

    texts, image_keys = parse_feishu_post_content(content)

    assert texts == []
    assert image_keys == ["img_v2_only"]
