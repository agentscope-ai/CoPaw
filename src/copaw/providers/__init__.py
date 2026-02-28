# -*- coding: utf-8 -*-
"""Provider management — models, registry + persistent store."""

from .models import (
    ActiveModelsInfo,
    CustomProviderData,
    ModelInfo,
    ModelSlotConfig,
    ModelTier,
    ProviderDefinition,
    ProviderInfo,
    ProviderSettings,
    ProvidersData,
    ResolvedModelConfig,
    RoutingConfig,
)
from .registry import (
    PROVIDERS,
    get_chat_model_class,
    get_provider,
    get_provider_chat_model,
    is_builtin,
    list_providers,
    sync_local_models,
)
from .store import (
    add_model,
    create_custom_provider,
    delete_custom_provider,
    get_active_llm_config,
    get_model_slot,
    load_providers_json,
    mask_api_key,
    remove_model,
    save_providers_json,
    set_active_llm,
<<<<<<< HEAD
    test_model_connection,
    test_provider_connection,
=======
    set_model_slot,
>>>>>>> fb7ebea (feat(routing): add intelligent task routing with tier-based model selection)
    update_provider_settings,
)

__all__ = [
    "ActiveModelsInfo",
    "CustomProviderData",
    "ModelInfo",
    "ModelSlotConfig",
    "ModelTier",
    "ProviderDefinition",
    "ProviderInfo",
    "ProviderSettings",
    "ProvidersData",
    "ResolvedModelConfig",
    "RoutingConfig",
    "PROVIDERS",
    "get_chat_model_class",
    "get_provider",
    "get_provider_chat_model",
    "is_builtin",
    "list_providers",
    "sync_local_models",
    "add_model",
    "create_custom_provider",
    "delete_custom_provider",
    "get_active_llm_config",
    "get_model_slot",
    "load_providers_json",
    "mask_api_key",
    "remove_model",
    "save_providers_json",
    "set_active_llm",
<<<<<<< HEAD
    "test_model_connection",
    "test_provider_connection",
=======
    "set_model_slot",
>>>>>>> fb7ebea (feat(routing): add intelligent task routing with tier-based model selection)
    "update_provider_settings",
]
