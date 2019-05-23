# -*- coding: utf-8 -
#   ____                ______           __        _    __
#  / __ \___  ___ ___  / __/ /____ _____/ /_____  (_)__/ /
# / /_/ / _ \/ -_) _ \_\ \/ __/ _ `/ __/  '_/ _ \/ / _  /
# \____/ .__/\__/_//_/___/\__/\_,_/\__/_/\_\\___/_/\_,_/
#     /_/
# Make your OpenStacks Collaborative


from typing import Any, Optional

import copy
import threading


# Name of the execution (atomic) scope
EXECUTION_SCOPE = "atomic_scope"


# Path on the devstack host of the openstackoid services catalog.
SERVICES_CATALOG_PATH = "file:///etc/openstackoid/catalog.json"


# Local storage stack
__local_context = threading.local()


def _get_from_context(name: str) -> Optional[Any]:
    return getattr(__local_context, name, None)


def _push_to_context(name: str, value: Any) -> None:
    setattr(__local_context, name, value)


def get_shell_scope() -> dict:
    shell_scope = _get_from_context("shell_scope")

    # undefined shell scope at this point is not an option
    assert shell_scope, "Shell scope is undefined."

    # Make shell scope immutable
    return copy.copy(shell_scope)


def push_shell_scope(value: dict) -> None:

    # set shell scope only once during all (context) execution
    shell_scope = _get_from_context("shell_scope")
    if not shell_scope:
        if not isinstance(value, dict):
            raise TypeError("Shell scope must be a dictionary.")
        _push_to_context("shell_scope", value)


def get_execution_scope() -> Optional[tuple]:
    """Get latest execution scope from the stack without pop it out.

    """

    stack = _get_from_context(EXECUTION_SCOPE)
    return stack[-1] if stack else None


def push_execution_scope(value: tuple) -> None:
    """Add an execution scope on the stack.

    """

    if not isinstance(value, tuple):
        raise TypeError("Atomic scope must be a tuple.")

    if any(operator in value[1] for operator in "|&^"):
        raise ValueError("Atomic scope must not include operators.")

    # `execution_scope` is an stack data type
    stack = _get_from_context(EXECUTION_SCOPE)
    if stack:
        stack.append(value)
    else:
        stack = [value]

    _push_to_context(EXECUTION_SCOPE, stack)


def pop_execution_scope() -> Optional[tuple]:
    """Remove latest execution scope from the stack and return it.

    """

    stack = _get_from_context(EXECUTION_SCOPE)
    return stack.pop() if stack else None
