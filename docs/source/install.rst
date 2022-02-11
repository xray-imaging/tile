============
Installation
============

First, you must have `Conda <https://docs.conda.io/en/latest/miniconda.html>`_
installed and create a dedicated conda environment::

     conda create -n tile

and::

    $ conda activate tile

then install tile
::

  git clone https://github.com/xray-imaging/tile.git
  cd tile
  python setup.py install

============
Requirements
============

Besides the listed `requirements <https://github.com/xray-imaging/mosaic/blob/main/requirements.txt>`_, **tile** uses `tomopy <https://tomopy.readthedocs.io/en/latest/>`_ or, if you have a GPU available in your system, `tomocupy <https://tomocupy.readthedocs.io/en/latest/>`_ to perform the tomographic reconstruction after the stitching step. 

Install tomocupy
================

1. Install the pytorch pywavelets package for ring removal
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
::

  git clone https://github.com/fbcotter/pytorch_wavelets
  cd pytorch_wavelets
  pip install .
  cd -

2. Set path to the nvcc profiler (e.g. /local/cuda-11.4/bin/nvcc)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
::

  export CUDACXX=/local/cuda-11.4/bin/nvcc 


3. Install tomocupy
~~~~~~~~~~~~~~~~~~~
::

  git clone https://github.com/nikitinvv/tomocupy-cli
  cd tomocupy-cli
  python setup.py install 


Install tomopy
==============

To install tomopy `tomopy <https://tomopy.readthedocs.io/en/latest/>`_/`tomopy cli <https://tomopycli.readthedocs.io/en/latest/>`_ follow the `tomopy install <https://tomopy.readthedocs.io/en/latest/install.html>`_/`tomopycli install <https://tomopycli.readthedocs.io/en/latest/source/install.html>`_ instructions.
