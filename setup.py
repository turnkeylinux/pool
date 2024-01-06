#!/usr/bin/python3

from distutils.core import setup

setup(
    name="pool",
    version="1.1.x",
    author="Jeremy Davis",
    author_email="jeremy@turnkeylinux.org",
    url="https://github.com/turnkeylinux/pool",
    packages=["pool_lib"],
    scripts=["pool"]
)
