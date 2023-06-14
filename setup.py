#!/usr/bin/env python
from setuptools import setup

setup(
    name="tap-wrike",
    version="0.3.0",
    description="Singer.io tap for extracting Wrike data",
    author="Potloc",
    url="https://potloc.com",
    classifiers=["Programming Language :: Python :: 3 :: Only"],
    py_modules=["tap_wrike"],
    install_requires=[
        "backoff==2.2.1",
        "requests==2.31.0",
        "singer-python==5.9.0",
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
