from setuptools import setup, find_packages
from setuptools.command.install import install
import os


setup(
    name='mosaic',
    version=open('VERSION').read().strip(),
    #version=__version__,
    author='Francesco De Carlo',
    author_email='decarlof@gmail.com',
    url='https://github.com/decarlof/mosaic',
    packages=find_packages(),
    include_package_data = True,
    scripts=['bin/mosaic'],
    description='cli to process mosaic tomography data',
    zip_safe=False,
)