# -*- coding: utf-8 -*-
"""Definition of Provider."""

from abc import ABC, abstractmethod
from typing import Dict, List, Type
from pydantic import BaseModel, Field

from agentscope.model import ChatModelBase


class ModelInfo(BaseModel):
    id: str = Field(..., description="Model identifier used in API calls")
    name: str = Field(..., description="Human-readable model name")


class Provider(BaseModel, ABC):
    """Represents a provider instance with its configuration."""

    id: str = Field(..., description="Provider identifier")
    name: str = Field(..., description="Human-readable provider name")
    base_url: str = Field(default="", description="API base URL")
    api_key: str = Field(default="", description="API key for authentication")
    chat_model: str = Field(
        default="OpenAIChatModel",
        description="Chat model class name (e.g., 'OpenAIChatModel')",
    )
    models: List[ModelInfo] = Field(
        default_factory=list,
        description="List of available models",
    )
    api_key_prefix: str = Field(
        default="",
        description="Expected prefix for the API key (e.g., 'sk-')",
    )
    base_url_env_var: str = Field(
        default="",
        description=(
            "Environment variable name to override base URL "
            "(e.g., 'OLLAMA_HOST')"
        ),
    )
    is_local: bool = Field(
        default=False,
        description="Whether this provider is for a local hosting platform",
    )
    is_custom: bool = Field(
        default=False,
        description=("Whether this provider is user-created (not built-in)."),
    )

    @abstractmethod
    async def check_connection(self, timeout: float = 5) -> bool:
        """Check if the provider is reachable with the current config."""

    @abstractmethod
    async def fetch_models(self, timeout: float = 5) -> List[ModelInfo]:
        """Fetch the list of available models from the provider."""

    @abstractmethod
    async def check_model_connection(
        self,
        model_id: str,
        timeout: float = 5,
    ) -> bool:
        """Check if a specific model is reachable/usable."""

    @abstractmethod
    async def update_config(self, config: Dict) -> None:
        """Update provider configuration with the given dictionary."""

    async def add_model(
        self,
        model_info: ModelInfo,
        timeout: float = 10,
    ) -> None:
        """Add a model to the provider's model list."""
        raise NotImplementedError(
            "This provider does not support adding models.",
        )

    async def delete_model(self, model_id: str, timeout: float = 10) -> None:
        """Delete a model from the provider's model list."""
        raise NotImplementedError(
            "This provider does not support deleting models.",
        )

    def get_chat_model_cls(self) -> Type[ChatModelBase]:
        """Return the chat model class associated with this provider."""
        import agentscope.model

        chat_model_cls = getattr(
            agentscope.model,
            self.chat_model,
            None,
        )
        if chat_model_cls is None:
            raise ValueError(
                f"Chat model class '{self.chat_model}' not found"
                f" for provider '{self.name}'.",
            )
        return chat_model_cls


class DefaultProvider(Provider):
    """Default provider implementation with no-op methods."""

    async def check_connection(self, timeout: float = 5) -> bool:
        return len(self.models) > 0

    async def fetch_models(self, timeout: float = 5) -> List[ModelInfo]:
        return self.models

    async def check_model_connection(
        self,
        model_id: str,
        timeout: float = 5,
    ) -> bool:
        return model_id in {model.id for model in self.models}

    async def update_config(self, config: Dict) -> None:
        pass
