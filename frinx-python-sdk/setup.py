from setuptools import setup
import os

def __read__(file_name):
    return open(os.path.join(os.path.dirname(__file__), file_name)).read()
    
setup(
    name='fm-base-workers',
    package_dir = {"": "src"},
    version='2.1.0',
    description='Conductor python client wrapper and common utils for LMSTACK workers',
    author='FRINXio',
    author_email='',
    url='https://github.com/FRINXio/fm-base-workers',
    keywords=['frinx-machine','conductor'],
    include_package_data=True,
    license='Apache 2.0',
    install_requires = [
    ],
    long_description=__read__('README.md'),
    long_description_content_type="text/markdown"
)
