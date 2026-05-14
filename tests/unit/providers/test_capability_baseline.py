# -*- coding: utf-8 -*-
# pylint: disable=protected-access
from __future__ import annotations

from qwenpaw.providers import capability_baseline


def _cap(
    expected_image: bool | None,
    expected_video: bool | None,
) -> capability_baseline.ExpectedCapability:
    return capability_baseline.ExpectedCapability(
        provider_id="provider",
        model_id="model",
        expected_image=expected_image,
        expected_video=expected_video,
    )


def test_registry_loads_known_baseline_entries() -> None:
    registry = capability_baseline.ExpectedCapabilityRegistry()

    openai = registry.get_expected("openai", "gpt-5")
    dashscope = registry.get_expected("dashscope", "qwen3-max")

    assert openai is not None
    assert openai.expected_image is True
    assert openai.expected_video is True
    assert openai.doc_url == "https://platform.openai.com/docs/models"

    assert dashscope is not None
    assert dashscope.expected_image is False
    assert dashscope.expected_video is False
    assert registry.get_expected("missing", "model") is None


def test_registry_filters_models_by_provider() -> None:
    registry = capability_baseline.ExpectedCapabilityRegistry()

    kimi_models = registry.get_all_for_provider("kimi-cn")
    model_ids = {cap.model_id for cap in kimi_models}

    assert "kimi-k2.5" in model_ids
    assert "kimi-k2-thinking" in model_ids
    assert all(cap.provider_id == "kimi-cn" for cap in kimi_models)
    assert registry.get_all_for_provider("missing") == []


def test_register_overwrites_existing_model_entry() -> None:
    registry = capability_baseline.ExpectedCapabilityRegistry()
    custom = capability_baseline.ExpectedCapability(
        provider_id="custom",
        model_id="model-a",
        expected_image=None,
        expected_video=True,
        doc_url="https://example.test",
        note="custom note",
    )

    registry._register(custom)

    assert registry.get_expected("custom", "model-a") == custom


def test_compare_probe_result_reports_false_negative_and_positive() -> None:
    logs = capability_baseline.compare_probe_result(
        _cap(expected_image=True, expected_video=False),
        actual_image=False,
        actual_video=True,
    )

    assert logs == [
        capability_baseline.DiscrepancyLog(
            provider_id="provider",
            model_id="model",
            field="image",
            expected=True,
            actual=False,
            discrepancy_type="false_negative",
        ),
        capability_baseline.DiscrepancyLog(
            provider_id="provider",
            model_id="model",
            field="video",
            expected=False,
            actual=True,
            discrepancy_type="false_positive",
        ),
    ]


def test_compare_probe_result_skips_unknown_and_matching_fields() -> None:
    assert not capability_baseline.compare_probe_result(
        _cap(expected_image=None, expected_video=True),
        actual_image=True,
        actual_video=True,
    )


def test_generate_summary_counts_statuses_and_discrepancy_details() -> None:
    ok_cap = _cap(expected_image=True, expected_video=True)
    discrepancy_cap = _cap(expected_image=True, expected_video=False)
    failure_cap = _cap(expected_image=False, expected_video=False)

    summary = capability_baseline.generate_summary(
        [
            (ok_cap, True, True, "ok"),
            (discrepancy_cap, False, True, "discrepancy"),
            (failure_cap, False, False, "failure"),
        ],
    )

    assert summary.total_models == 3
    assert summary.passed == 1
    assert summary.discrepancies == 1
    assert summary.failures == 1
    assert [detail.field for detail in summary.details] == ["image", "video"]
