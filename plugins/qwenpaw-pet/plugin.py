# -*- coding: utf-8 -*-
"""QwenPaw Pet backend plugin entry point."""

# pylint: disable=wrong-import-position,wrong-import-order

import logging
import sys
from pathlib import Path

# ``qwenpaw plugin install`` execs this file as a plain module (no
# package), so sibling modules are not reachable via relative imports
# unless the plugin directory is on sys.path before importing them.
_plugin_dir = str(Path(__file__).resolve().parent)
if _plugin_dir not in sys.path:
    sys.path.insert(0, _plugin_dir)

from qwenpaw.plugins.api import PluginApi  # noqa: E402

from emitter import emit_pet_event, ensure_desktop_available  # noqa: E402
from patch_approval import (  # noqa: E402
    patch_approval_service,
    restore_approval_service,
)
from patch_runner import (  # noqa: E402
    patch_agent_runner,
    restore_agent_runner,
)
from router import build_router  # noqa: E402

# Logger uses ``qwenpaw.*`` so messages appear in the project logger
# (``~/.qwenpaw/qwenpaw.log``).
logger = logging.getLogger("qwenpaw.pet_desktop")


class QwenPawPetPlugin:
    """Emit QwenPaw backend lifecycle events to the desktop pet."""

    def register(self, api: PluginApi):
        """Register startup/shutdown hooks and plugin HTTP routes."""
        logger.info("Registering QwenPaw Pet plugin")

        # Patch as early as possible (do not rely only on async startup hooks).
        try:
            patch_agent_runner()
            patch_approval_service()
        except Exception:
            logger.exception("QwenPaw Pet: failed to install runtime patches")

        api.register_startup_hook(
            hook_name="qwenpaw_pet_startup",
            callback=self._startup,
            priority=80,
        )
        api.register_shutdown_hook(
            hook_name="qwenpaw_pet_shutdown",
            callback=self._shutdown,
            priority=120,
        )
        api.register_http_router(
            build_router(),
            prefix="/qwenpaw-pet",
            tags=["qwenpaw-pet"],
        )

        logger.info("QwenPaw Pet plugin registered")

    def _startup(self):
        """Patch the runner and notify the desktop."""
        try:
            ensure_desktop_available()
            patch_agent_runner()
            patch_approval_service()
            emit_pet_event(
                "qwenpaw.startup",
                text="QwenPaw started",
                duration_ms=1500,
            )
            logger.info("QwenPaw Pet startup hook complete")
        except Exception:
            logger.exception("QwenPaw Pet startup hook failed")

    def _shutdown(self):
        """Notify the desktop and restore the runner patch."""
        try:
            emit_pet_event("qwenpaw.shutdown", text="", duration_ms=500)
            restore_approval_service()
            restore_agent_runner()
            logger.info("QwenPaw Pet shutdown hook complete")
        except Exception:
            logger.exception("QwenPaw Pet shutdown hook failed")


plugin = QwenPawPetPlugin()
