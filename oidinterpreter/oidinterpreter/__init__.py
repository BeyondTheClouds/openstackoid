# -*- coding: utf-8 -
#   ____                ______           __        _    __
#  / __ \___  ___ ___  / __/ /____ _____/ /_____  (_)__/ /
# / /_/ / _ \/ -_) _ \_\ \/ __/ _ `/ __/  '_/ _ \/ / _  /
# \____/ .__/\__/_//_/___/\__/\_,_/\__/_/\_\\___/_/\_,_/
#     /_/
# Make your OpenStacks Collaborative
"""
OidInterpreter: Interprets the Scope in a Request
"""
import logging


# Expose OidInterpreter
from .oidinterpreter import (Service, OidInterpreter, get_oidinterpreter,
                             oss2services, SCOPE_DELIM)


__version__ = '0.0.1'
version = __version__


# Add a Null logging handler to prevent logging output when un-configured
logging.getLogger('oidinterpreter').addHandler(logging.NullHandler())
