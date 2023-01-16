import os

from setuptools import setup


def __read__(file_name):
    return open(os.path.join(os.path.dirname(__file__), file_name)).read()


setup(
    name="frinx-python-sdk",
    package_dir={"": "src"},
    version="0.0.1",
    description="Python SDK for Frinx Machine Workflow Manager",
    author="FRINXio",
    author_email="",
    url="https://github.com/FRINXio/fm-base-workers",
    keywords=["frinx-machine", "conductor"],
    include_package_data=True,
    license="Apache 2.0",
    install_requires=[],
    long_description=__read__("README.md"),
    long_description_content_type="text/markdown",
)
