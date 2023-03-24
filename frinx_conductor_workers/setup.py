import os

from setuptools import setup


def __read__(file_name):
    return open(os.path.join(os.path.dirname(__file__), file_name)).read()


setup(
    name="frinx_conductor_workers",
    packages=["frinx_conductor_workers", "frinx_conductor_workflows"],
    version="1.1.7",
    description="Conductor python client workers",
    author="Frinx",
    author_email="info@frinx.io",
    url="https://github.com/FRINXio/fm-base-workers",
    keywords=["conductor"],
    license="Apache 2.0",
    include_package_data=True,
    install_requires=[],
    long_description=__read__("README.md"),
    long_description_content_type="text/markdown",
)
