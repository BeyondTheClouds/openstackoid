# -*- coding: utf-8 -
#   ____                ______           __        _    __
#  / __ \___  ___ ___  / __/ /____ _____/ /_____  (_)__/ /
# / /_/ / _ \/ -_) _ \_\ \/ __/ _ `/ __/  '_/ _ \/ / _  /
# \____/ .__/\__/_//_/___/\__/\_,_/\__/_/\_\\___/_/\_,_/
#     /_/
# Make your OpenStacks Collaborative


import logging

from requests import Response


logger = logging.getLogger(__name__)


def print_request_info(response: Response, *arguments, **keywords):
    """Print hook of a `Response` instance.

    Log the target address, headers and execution status of a request.
    This method works as a hook when the request is dispatched.

    """

    logger.debug(f"Request url: {response.request.url}")
    logger.debug(f"Request headers: {response.request.headers}")
    logger.debug(f"Response status: {response.status_code}")
