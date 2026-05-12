# -*- coding: utf-8 -*-
"""GPT Image 2 Tool Plugin Entry Point."""

import importlib.util
import logging
import os

from qwenpaw.plugins.api import PluginApi

logger = logging.getLogger(__name__)


class GPTImage2ToolPlugin:
    """GPT Image 2 Tool Plugin.

    Registers the generate_image_gpt tool into the Agent's toolkit.
    This is a pure backend plugin - no frontend code required.
    """

    def register(self, api: PluginApi):
        """Register the GPT Image 2 tool.

        Args:
            api: PluginApi instance
        """
        logger.info("Registering GPT Image 2 tool...")

        # Register startup hook to add tool to toolkit
        api.register_startup_hook(
            hook_name="register_gpt_image2_tool",
            callback=self._register_tool,
            priority=50,
        )

        logger.info("✓ GPT Image 2 tool plugin registered")

    def _register_tool(self):
        """Register GPT Image 2 tools to Agent toolkit.

        This is called during application startup.
        Registers both generate_image_gpt and edit_image_gpt tools.
        """
        try:
            # Load tool module
            plugin_dir = os.path.dirname(os.path.abspath(__file__))
            tool_path = os.path.join(plugin_dir, "tool.py")

            spec = importlib.util.spec_from_file_location(
                "gpt_image2_tool",
                tool_path,
            )
            tool_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(tool_module)

            generate_image_gpt = tool_module.generate_image_gpt
            edit_image_gpt = tool_module.edit_image_gpt

            # Register tool functions globally
            import qwenpaw.agents.tools as tools_module

            setattr(tools_module, "generate_image_gpt", generate_image_gpt)
            if "generate_image_gpt" not in tools_module.__all__:
                tools_module.__all__.append("generate_image_gpt")

            setattr(tools_module, "edit_image_gpt", edit_image_gpt)
            if "edit_image_gpt" not in tools_module.__all__:
                tools_module.__all__.append("edit_image_gpt")

            logger.info(
                "✓ Registered tool functions: "
                "generate_image_gpt, edit_image_gpt",
            )

            # Add tools to current agent's config
            from qwenpaw.config.config import (
                BuiltinToolConfig,
                load_agent_config,
                save_agent_config,
            )
            from qwenpaw.app.agent_context import get_current_agent_id

            tools_to_register = [
                {
                    "name": "generate_image_gpt",
                    "description": (
                        "Generate images using OpenAI GPT Image 2"
                    ),
                    "icon": "🎨",
                },
                {
                    "name": "edit_image_gpt",
                    "description": (
                        "Edit or generate images using reference images "
                        "with OpenAI GPT Image 2"
                    ),
                    "icon": "🖼️",
                },
            ]

            try:
                # Get current agent ID
                agent_id = get_current_agent_id()
                if not agent_id:
                    logger.warning(
                        "No current agent ID found, "
                        "tools will be registered later",
                    )
                    return

                # Load agent config
                agent_config = load_agent_config(agent_id)

                # Ensure tools config exists
                if not agent_config.tools:
                    from qwenpaw.config.config import ToolsConfig

                    agent_config.tools = ToolsConfig()

                # Add each tool if not exists
                for tool_info in tools_to_register:
                    tool_name = tool_info["name"]
                    if tool_name not in agent_config.tools.builtin_tools:
                        agent_config.tools.builtin_tools[
                            tool_name
                        ] = BuiltinToolConfig(
                            name=tool_name,
                            enabled=False,  # Default disabled
                            description=tool_info["description"],
                            display_to_user=True,
                            async_execution=False,
                            icon=tool_info["icon"],
                        )
                        logger.info(
                            f"✓ Added {tool_name} to agent {agent_id} "
                            f"(disabled)",
                        )
                    else:
                        logger.info(
                            f"Tool {tool_name} already exists in agent "
                            f"{agent_id}",
                        )

                save_agent_config(agent_id, agent_config)

            except Exception as ex:
                logger.warning(
                    f"Failed to add tools to current agent: {ex}. "
                    f"Tools will be available after restart.",
                )

        except Exception as e:
            logger.error(
                f"Failed to register GPT Image 2 tools: {e}",
                exc_info=True,
            )


# Export plugin instance
plugin = GPTImage2ToolPlugin()
