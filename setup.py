#!/usr/bin/env python
from setuptools import setup

setup(
    name="tap-wrike",
    version="0.1.0",
    description="Singer.io tap for extracting Wrike data",
    author="Potloc",
    url="https://potloc.com",
    classifiers=["Programming Language :: Python :: 3 :: Only"],
    py_modules=["tap_wrike"],
    install_requires=[
        # NB: Pin these to a more specific version for tap reliability
        "singer-python",
        "requests",
    ],
    entry_points="""
    [console_scripts]
    tap-wrike=tap_wrike:main
    """,
    packages=["tap_wrike"],
    package_data = {
        "schemas": ["tap_wrike/schemas/*.json"]
    },
    include_package_data=True,
)
