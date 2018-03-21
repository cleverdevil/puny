# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

setup(
    name='puny',
    version='0.1.0',
    description='Micropub server and CMS for creating IndieWeb websites.',
    author='Jonathan LaCour',
    author_email='jonathan@cleverdevil.org',
    install_requires=[
        "pecan",
        "jsl",
        "tinydb",
        "jsonschema",
        "requests",
        "hashfs",
        "maya",
        "awesome-slugify",
    ],
    test_suite='puny',
    zip_safe=False,
    include_package_data=True,
    packages=find_packages(exclude=['ez_setup']),
)
