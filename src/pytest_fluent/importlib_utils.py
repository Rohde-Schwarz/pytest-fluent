"""Utility for pathlib operations."""

import importlib.util
import logging
import pathlib
import types
import typing
from importlib.machinery import ModuleSpec
from os import PathLike

LOGGER = logging.getLogger(__name__)


def extract_function_from_module_string(
    class_name: str,
    module: typing.Optional[str] = None,
    file_path: typing.Optional[str] = None,
) -> typing.Type[logging.Formatter]:
    """Extract record formatter from module.

    Args:
        class_name (str): The name of the record formatter class.
        module (typing.Optional[str], optional): Module name string or more descriptive
            dictionary. Defaults to None.
        file_path (typing.Optional[str], optional): File path to the module.
            Defaults to None.

    Returns:
        typing.Type[logging.Formatter]: The extract record formatter class.
    """
    # Use importlib to import the specified module dynamically
    if module:
        imported_module = importlib.import_module(module)
    elif file_path:
        imported_module = load_module_from_path(file_path)
    else:
        raise ValueError("Neither module nor file_path was set.")

    # Retrieve the specified function from the dynamically imported module
    if hasattr(imported_module, class_name):
        record_formatter = getattr(imported_module, class_name)
        if not issubclass(record_formatter, logging.Formatter):
            raise ValueError(
                "Provided record formatter is not derived from logging.Formatter"
            )
        return record_formatter
    raise ImportError(f"Could not find {class_name} in {imported_module.__name__}")


def load_module_from_path(path: typing.Union[str, PathLike]) -> types.ModuleType:
    """Load module from absolute path.

    Args:
        path: typing.Union[str, PathLike]: Path to module file

    Raises:
        ModuleNotFoundError: If the file path was not found.

    Returns:
        types.ModuleType: Loaded module type.
    """
    path_name = pathlib.Path(path)
    module_name = path_name.name.replace(".py", "")
    spec = importlib.util.spec_from_file_location(module_name, path_name.absolute())
    if spec is None:
        raise ModuleNotFoundError(f"Could not load module {path_name}")
    module = importlib.util.module_from_spec(spec)
    typing.cast(ModuleSpec, spec).loader.exec_module(module)  # type: ignore
    return module
