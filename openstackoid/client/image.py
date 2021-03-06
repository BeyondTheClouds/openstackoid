# -*- coding: utf-8 -
#   ____                ______           __        _    __
#  / __ \___  ___ ___  / __/ /____ _____/ /_____  (_)__/ /
# / /_/ / _ \/ -_) _ \_\ \/ __/ _ `/ __/  '_/ _ \/ / _  /
# \____/ .__/\__/_//_/___/\__/\_,_/\__/_/\_\\___/_/\_,_/
#     /_/
# Make your OpenStacks Collaborative


from typing import Optional, Tuple

import functools
import itertools
import logging

from ..dispatcher import OidDispatcher, scope
from ..interpreter import OidInterpreter


SERVICE_TYPE = "image"

logger = logging.getLogger(__name__)


def image_list_extr_scp_func(interpreter: OidInterpreter,
                             *arguments, **keywords) -> Optional[Tuple]:
    """Extract the execution scope of a 'image' service from arguments.

    In terms of the OS client the scope is collected from the command line
    options passed to an `openstackclient.image.v2.image.ListImage` instance
    initialized in the scoped method during the execution of the `take_action`
    method.

    """

    context = arguments[0]
    shell_scope = context.app.options.oid_scope
    service_scope = shell_scope[SERVICE_TYPE]
    logger.info(f"Service scope: '{service_scope}'")
    return SERVICE_TYPE, service_scope


def image_list_conj_res_func(
        this: OidDispatcher, other: OidDispatcher) -> OidDispatcher:
    """Aggregate results of the 'and' operator for the 'image list' command.

    Apply the aggregation after execution of the command with a compound, and
    conjunctive scope by merging the list of each endpoint.

    In terms of the OS client (thought the cliff library) this is a wrapper for
    a `osc_lib.command.Lister` instance.

    """

    if this.result and other.result:
        aggregated_labels = other.result[0]
        this_generator = this.result[1]
        other_generator = other.result[1]
        aggregated_results = itertools.chain(this_generator, other_generator)
        other.result = (aggregated_labels, aggregated_results)

    return other


# Partial function of the scope decorator for the 'image list' operation.
image_list_scope = functools.partial(scope,
                                     extr_scp_func=image_list_extr_scp_func,
                                     conj_res_func=image_list_conj_res_func)
