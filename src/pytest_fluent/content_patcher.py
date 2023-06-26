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
            value = self._patch_value(key, value)
            all_settings.update({key: value})
        for stage_name in stage_names:
            patched.update({stage_name: all_settings.copy()})
            stage_info = user_settings.get(stage_name, {})
            for key, value in stage_info.items():
                value = self._patch_value(key, value)
                if isinstance(value, dict):
                    value = self._merge_patched_dict_values(
                        patched[stage_name].get(key, {}), value
                    )
                if isinstance(value, list):
                    value = self._merge_patched_list_values(
                        patched[stage_name].get(key, []), value
                    )
                patched[stage_name].update({key: value})
        return patched

    def _patch_value(self, key: str, value: typing.Any) -> typing.Any:
        if key == "replace":
            value = {key: self._patch_value(key, v) for key, v in value.items()}
        else:
            if isinstance(value, dict):
                for subkey, subvalue in value.items():
                    if not isinstance(subvalue, str):
                        continue
                    value[subkey] = self._get_env_or_args(subvalue)
            elif isinstance(value, list):
                for idx, subvalue in enumerate(value):
                    if not isinstance(subvalue, str):
                        continue
                    value[idx] = self._get_env_or_args(subvalue)
            else:
                value = self._get_env_or_args(value)
        return value

    def _merge_patched_dict_values(self, old: dict, new: dict) -> dict:
        merged = old.copy()
        for key, value in new.items():
            merged[key] = value
        return merged

    def _merge_patched_list_values(self, old: list, new: list) -> list:
        merged = [*{*old, *new}]
        return merged

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
            stage_name (typing.Optional[str], optional): Current stage.
                Defaults to None.

        Returns:
            typing.Tuple[str, str]: Tag string, Label string.
        """
        if stage_name is None:
            stage_name = inspect.stack()[1][3]
        stage_info = self._user_settings.get(stage_name, {})
        return stage_info["tag"], stage_info["label"]

    def patch(
        self,
        content: dict,
        stage_name: typing.Optional[str] = None,
        ignore_entries: typing.List[str] = [],
    ) -> dict:
        """Patch the content with the provided settings for each stage.

        Args:
            content (dict): Structured data for transmission.
            stage_name (typing.Optional[str], optional): Calling stage name.
                Defaults to None.

        Returns:
                dict: Patched dictionary with the user provided stage settings.
        """  # noqa
        if stage_name is None:
            stage_name = inspect.stack()[1][3]

        stage_info = self._user_settings.get(stage_name, {})
        stage_info = {k: v for k, v in stage_info.items() if k not in ignore_entries}
        if not stage_info:
            return content
        return self._patch_stage_content(content, stage_info)

    @staticmethod
    def _patch_stage_content(stage_content: dict, user_settings: dict) -> dict:
        stage_content_patched = stage_content.copy()
        if "replace" in user_settings:
            replace_it = user_settings["replace"]
            if "keys" in replace_it:
                keys_settings = replace_it["keys"]
                for key, value in keys_settings.items():
                    if key in stage_content_patched:
                        tmp = stage_content_patched[key]
                        stage_content_patched[value] = tmp
                        del stage_content_patched[key]
            if "values" in replace_it:
                value_settings = replace_it["values"]
                new_value_keys = value_settings.keys()
                for key, value in stage_content_patched.items():
                    if not isinstance(value, dict) and value in new_value_keys:
                        stage_content_patched[key] = value_settings[value]
        to_add = user_settings.get("add", {})
        stage_content_patched.update(to_add)
        to_drop = user_settings.get("drop", [])
        for key in to_drop:
            if key in stage_content_patched:
                del stage_content_patched[key]
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
        if re.match(r"(<)([\w-]+)(>)", value):
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
        args_string = args_match[0].replace("-", "_")
        args_value = getattr(self._args_settings, args_string, "")
        return args_value
