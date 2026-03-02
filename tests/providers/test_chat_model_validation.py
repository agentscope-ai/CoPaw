import copaw.providers.registry as registry
from copaw.providers.models import ProviderSettings, ProvidersData
from copaw.providers.registry import get_provider_chat_model, normalize_chat_model_name


def test_normalize_chat_model_name_logs_and_fallback(monkeypatch) -> None:
    called = {}

    def fake_warning(msg, *args):
        called["msg"] = msg
        called["args"] = args

    monkeypatch.setattr(registry.logger, "warning", fake_warning)

    normalized = normalize_chat_model_name("UnknownModel", "dashscope")

    assert normalized == "OpenAIChatModel"
    assert called["args"][0] == "UnknownModel"
    assert called["args"][1] == "dashscope"


def test_get_provider_chat_model_applies_normalization() -> None:
    providers_data = ProvidersData(
        providers={
            "dashscope": ProviderSettings(chat_model="BadValue"),
        },
    )

    chat_model = get_provider_chat_model("dashscope", providers_data)

    assert chat_model == "OpenAIChatModel"
