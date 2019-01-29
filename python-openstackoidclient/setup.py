# -*- coding: utf-8 -
#   ____                ______           __        _    __
#  / __ \___  ___ ___  / __/ /____ _____/ /_____  (_)__/ /
# / /_/ / _ \/ -_) _ \_\ \/ __/ _ `/ __/  '_/ _ \/ / _  /
# \____/ .__/\__/_//_/___/\__/\_,_/\__/_/\_\\___/_/\_,_/
#     /_/
# Make your OpenStacks Collaborative
from setuptools import setup

setup(
    name="python-openstackoidclient",
    version="0.0.1",
    description="Add the --os-scope global option to OpenStack Client",
    url='https://github.com/BeyondTheClouds/openstackoid',
    author='discovery',
    author_email='discovery-dev@inria.fr',
    license='GPL-3.0',
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: OpenStack",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6"
    ],
    packages=["openstackoidclient"],
    entry_points={
        "openstack.cli.base": ["openstackoid=openstackoidclient.client"]
    },
)
