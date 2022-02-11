from setuptools import setup, find_packages


setup(
    name='tile',
    version=open('VERSION').read().strip(),
    author='Viktor Nikitin, Francesco De Carlo',
    author_email='vnikitin@anl.gov',
    url='https://github.com/xray-imaging/tile',
    packages=find_packages(),
    include_package_data = True,
    scripts=['bin/tile'],
    description='cli for stitching tomographic data',
    zip_safe=False,
)