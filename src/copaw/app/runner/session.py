# -*- coding: utf-8 -*-
"""Safe JSON session with filename sanitization for cross-platform
compatibility.

Windows filenames cannot contain: \\ / : * ? " < > |
This module wraps agentscope's JSONSession so that session_id and user_id
are sanitized before being used as filenames.
"""
import os
import re
import json
import logging

from agentscope.session import JSONSession

logger = logging.getLogger(__name__)


# Characters forbidden in Windows filenames
_UNSAFE_FILENAME_RE = re.compile(r'[\\/:*?"<>|]')


def sanitize_filename(name: str) -> str:
    """Replace characters that are illegal in Windows filenames with ``--``.

    >>> sanitize_filename('discord:dm:12345')
    'discord--dm--12345'
    >>> sanitize_filename('normal-name')
    'normal-name'
    """
    return _UNSAFE_FILENAME_RE.sub("--", name)


class SafeJSONSession(JSONSession):
    """JSONSession subclass that sanitizes session_id / user_id before
    building file paths.

    All other behaviour (save / load / state management) is inherited
    unchanged from :class:`JSONSession`.
    """

    def _get_save_path(self, session_id: str, user_id: str) -> str:
        """Return a filesystem-safe save path.

        Overrides the parent implementation to ensure the generated
        filename is valid on Windows, macOS and Linux.
        """
        os.makedirs(self.save_dir, exist_ok=True)
        safe_sid = sanitize_filename(session_id)
        safe_uid = sanitize_filename(user_id) if user_id else ""
        if safe_uid:
            file_path = f"{safe_uid}_{safe_sid}.json"
        else:
            file_path = f"{safe_sid}.json"
        return os.path.join(self.save_dir, file_path)

    async def update_session_state(
        self,
        session_id: str,
        key: str,
        value,
        user_id: str = "",
        create_if_not_exist: bool = True,
    ) -> None:
        """Update a top-level key in the session JSON file."""
        session_save_path = self._get_save_path(session_id, user_id=user_id)

        if os.path.exists(session_save_path):
            with open(
                session_save_path,
                "r",
                encoding="utf-8",
                errors="surrogatepass",
            ) as file:
                states = json.load(file)
        else:
            if not create_if_not_exist:
                raise ValueError(
                    f"Session file {session_save_path} does not exist.",
                )
            states = {}

        states[key] = value

        with open(
            session_save_path,
            "w",
            encoding="utf-8",
            errors="surrogatepass",
        ) as file:
            json.dump(states, file, ensure_ascii=False)

        logger.info(
            "Updated session state key '%s' in %s successfully.",
            key,
            session_save_path,
        )
