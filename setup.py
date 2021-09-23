#!/usr/bin/python3

from distutils.core import setup

setup(
    name="pool",
    version="2.0rc1",
    author="Jeremy Davis",
    author_email="jeremy@turnkeylinux.org",
    url="https://github.com/turnkeylinux/pool",
    packages=["pool_lib"],
    scripts=["pool_bin"]
)

