============
Installation
============

First, you must have `Conda <https://docs.conda.io/en/latest/miniconda.html>`_
installed and create a dedicated conda environment::

    (base)$ conda create -n tile

and::

    (base)$ conda activate tile
    (tile)$ 

then install all `requirements <https://github.com/xray-imaging/mosaic/blob/main/requirements.txt>`_ with::

    (tile)$ conda install  -c conda-forge dxchange dxfile

and install tile
::

    (tile)$ git clone https://github.com/xray-imaging/tile.git
    (tile)$ cd tile
    (tile)$ python setup.py install


Requirements
============

Besides the packases listed in `requirements <https://github.com/xray-imaging/mosaic/blob/main/requirements.txt>`_, **tile** uses `tomopy <https://tomopy.readthedocs.io/en/latest/>`_ or, if you have a GPU available in your system, `tomocupy <https://tomocupy.readthedocs.io/en/latest/>`_ to perform the tomographic reconstruction after the stitching step. 

Install tomocupy
~~~~~~~~~~~~~~~~

Follow the tomocupu `installation intruction <https://tomocupycli.readthedocs.io/en/latest/source/install.html>`_:

::

    (tile)$ conda install cupy scikit-build swig pywavelets numexpr astropy olefile opencv

1. Install the pytorch pywavelets package for ring removal

::

    (tile)$ git clone https://github.com/fbcotter/pytorch_wavelets
    (tile)$ cd pytorch_wavelets
    (tile)$ pip install .
    (tile)$ cd -

2. Set path to the nvcc profiler (e.g. /local/cuda-11.4/bin/nvcc)

::

  export CUDACXX=/local/cuda-11.4/bin/nvcc 


3. Install tomocupy

::

    (tile)$ git clone https://github.com/nikitinvv/tomocupy-cli
    (tile)$ cd tomocupy-cli
    (tile)$ python setup.py install 


Install tomopy
==============

To install tomopy `tomopy <https://tomopy.readthedocs.io/en/latest/>`_/`tomopy cli <https://tomopycli.readthedocs.io/en/latest/>`_ follow the `tomopy install <https://tomopy.readthedocs.io/en/latest/install.html>`_/`tomopycli install <https://tomopycli.readthedocs.io/en/latest/source/install.html>`_ instructions.

::

    (tile)$ conda install -c conda-forge tomopy
