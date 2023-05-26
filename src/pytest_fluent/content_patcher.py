"""Patch content according to settings."""
import argparse
import enum
import inspect
import os
import re
import typing


class _ContentType(enum.Enum):
    ENV = 0
    ARGS = 1


class ContentPatcher:
    """Patch the transmission content according to the user settings."""

    def __init__(
        self,
        user_settings: dict,
        args_settings: argparse.Namespace,
        stage_names: typing.List[str],
    ) -> None:
        """Initialize content patcher."""
        self._args_settings: argparse.Namespace = args_settings
        self._user_settings: dict = self._stage_settings(user_settings, stage_names)

    def _stage_settings(
        self, user_settings: dict, stage_names: typing.List[str]
    ) -> dict:
        """Prepare stage settings for faster online lookup.

        Args:
            user_settings (dict): User settings from JSON or YAML file.
            stage_names (typing.List[str]): Used stage names by Pytest-fluent plugin.

        Returns:
            dict: Returns patched user settings.
        """
        patched = {}
        all_settings = {}
        for key, value in user_settings.get("all", {}).items():
            if isinstance(value, dict):
                for subkey, subvalue in value.items():
                    value[subkey] = self._get_env_or_args(subvalue)
            else:
                value = self._get_env_or_args(value)
            all_settings.update({key: value})
        for stage_name in stage_names:
            patched.update({stage_name: all_settings.copy()})
            stage_info = user_settings.get(stage_name, {})
            for key, value in stage_info.items():
                if isinstance(value, dict):
                    for subkey, subvalue in value.items():
                        value[subkey] = self._get_env_or_args(subvalue)
                else:
                    value = self._get_env_or_args(value)
                patched[stage_name].update({key: value})
        return patched

    @property
    def user_settings(self) -> dict:
        """Retrieve processed user settings.

        Returns:
            dict: Dictionary of user settings.
        """
        return self._user_settings

    def get_tag_and_label(
        self, stage_name: typing.Optional[str] = None
    ) -> typing.Tuple[str, str]:
        """Return the tag for the corresponding stage.

        Args:
            stage_name (typing.Optional[str], optional): Current stage. Defaults to None.

        Returns:
            typing.Tuple[str, str]: Tag string, Label string.
        """
        if stage_name is None:
            stage_name = inspect.stack()[1][3]
        stage_info = self._user_settings.get(stage_name, {})
        return stage_info["tag"], stage_info["label"]

    def patch(self, content: dict, stage_name: typing.Optional[str] = None) -> dict:
        """Patch the content with the provided settings for each stage.

        Args:
            content (dict): Structured data for transmission.
            stage_name (typing.Optional[str], optional): Calling stage name.
                Defaults to None.

        Returns:
                str: Patch dictionary with the user provided stage settings.
        """
        if stage_name is None:
            stage_name = inspect.stack()[1][3]

        stage_info = self._user_settings.get(stage_name, {})
        if not stage_info:
            return content
        return self._patch_stage_content(content, stage_info)

    @staticmethod
    def _patch_stage_content(stage_content: dict, user_settings: dict) -> dict:
        stage_content_patched = stage_content.copy()
        stage_content_patched["tag"] = user_settings["tag"]
        stage_content_patched["label"] = user_settings["label"]
        if "replace" in user_settings:
            for key, value in user_settings["replace"].items():
                if key in stage_content_patched:
                    tmp = stage_content_patched[key]
                    stage_content_patched[value] = tmp
                    del stage_content_patched[key]
        to_add = user_settings.get("add", {})
        stage_content_patched.update(to_add)
        to_drop = user_settings.get("drop", [])
        for key in to_drop:
            del user_settings[key]
        return stage_content_patched

    def _get_env_or_args(self, value: str) -> str:
        reference = self._is_reference_string(value)
        if reference == _ContentType.ENV:
            return self._get_env_content(value)
        elif reference == _ContentType.ARGS:
            return self._get_args_content(value)
        else:
            return value

    @staticmethod
    def _is_reference_string(value: str) -> typing.Optional[_ContentType]:
        if re.match(r"(\$)?({)([\w_]+)(})", value):
            return _ContentType.ENV
        elif re.match(r"(<)([\w-]+)(>)", value):
            return _ContentType.ARGS
        return None

    @staticmethod
    def _get_env_content(value: str) -> str:
        """Check if string relates to ENV variable and return that value.

        Args:
            value (str): String providing ENV reference e.g. ${USE_ENV}

        Returns:
            str: String with ENV content or empty string.
        """
        env_match = re.findall(r"\$({)?([\w_]+)(})?", value)
        if not env_match:
            return ""
        env_value = os.getenv(env_match[0][1], "")
        return env_value

    def _get_args_content(self, value: str) -> str:
        """Check if string relates to CLI argument variable and return that value.

        Args:
            value (str): String providing argument reference e.g. <tag>

        Returns:
            str: String with argument content or empty string.
        """
        args_match = re.findall(r"^<([\w-]+)>$", value)
        if not args_match:
            return ""
        args_match = args_match[0].replace("-", "_")
        args_value = getattr(self._args_settings, args_match, "")
        return args_value
