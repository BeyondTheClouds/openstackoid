# -*- coding: utf-8 -
#   ____                ______           __        _    __
#  / __ \___  ___ ___  / __/ /____ _____/ /_____  (_)__/ /
# / /_/ / _ \/ -_) _ \_\ \/ __/ _ `/ __/  '_/ _ \/ / _  /
# \____/ .__/\__/_//_/___/\__/\_,_/\__/_/\_\\___/_/\_,_/
#     /_/
# Make your OpenStacks Collaborative


from os import environ
from typing import Any, Callable, Dict, Optional, Tuple, Type

import functools
import inspect
import logging


logger = logging.getLogger(__name__)


def _get_os_scope_service_env(service_name: str) -> Optional[str]:
    env_name = f"OS_SCOPE_{service_name.upper()}"
    value = environ.get(env_name)
    if not value:
        value = environ.get("OS_REGION_NAME")

    return value


def get_default_scope() -> Dict[str, str]:
    return {
        "compute": _get_os_scope_service_env("compute"),
        "identity": _get_os_scope_service_env("identity"),
        "image": _get_os_scope_service_env("image"),
        "network": _get_os_scope_service_env("network"),
        "placement": _get_os_scope_service_env("placement")
    }


def update_tuple(old: Any, new: Any, arguments: Tuple) -> Tuple:
    """Update a value of a tuple with an new value.

    Replace with a new value an element positioned at the same indexed position
    of an old value. This is an immutable method returning an new object.

    """

    idx = arguments.index(old)
    return arguments[:idx] + (new,) + arguments[idx + 1:]


def get_from_tuple(argument_type: Type, arguments: Tuple) -> Any:
    """Get first element of a given 'type' from a tuple.

    """

    return next(a for a in arguments if isinstance(a, argument_type))


def _retrieve_name(variable: Any) -> str:
    """Retrieve the name of a variable.

    """

    local_variables = inspect.currentframe().f_back.f_back.f_locals.items()
    return [_name for _name, _value in local_variables if _value is variable]


def print_func_signature(func: Callable):
    """Print the signature of a method including its parameters.

    """

    @functools.wraps(func)
    def wrapper(*arguments, **keywords):
        # inspect.signature() or inspect.getfullargspec()
        logger.debug(f"Executing function: "
                     f"{func.__module__}.{func.__qualname__}")
        parameters = inspect.signature(func).parameters.keys()
        signature = zip(parameters, arguments)
        logger.debug(f"Function signature: {list(signature)}")
        # if arguments:
        #     print("... with arguments")
        #     for argument in arguments:
        #         argument_name = _retrieve_name(argument)
        #         if hasattr(argument, "__dict__"):
        #             for name, value in vars(argument).items():
        #                 argument_type = type(value).__name__
        #                 print(f"    aggregated argument '{argument_name}'")
        #                 print(f"    ... {name}: {value} [{argument_type}]")
        #         else:
        #             argument_type = type(argument).__name__
        #             print(f"    {argument_name}: {argument} [{argument_type}]")
        #
        # if keywords:
        #     print("... with keywords")
        #     for name, value in keywords.items():
        #         keyword_type = type(value).__name__
        #         print(f"    {name}: {value} [{keyword_type}] ")

        return func(*arguments, **keywords)
    return wrapper

    # # _args = None
    # # if func.__name__ == "send":
    # #     request = _get_by_type(args, PreparedRequest)
    # #     service = self.interpreter.get_service_scope(request)
    # for argument in arguments:
    #     if hasattr(argument, "__dict__"):
    #         print(f"\t\t{argument}({type(argument)}): {vars(argument)}")
    #     else:
    #         print(f"\t\t{argument}")
    #
    #         print(f"\twith keywords {kwargs}")
    #         print("- - - - - - - - - - - - - - - - - - - - - - - - ")
