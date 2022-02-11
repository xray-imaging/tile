====
Tile
====

`tile <https://tile.readthedocs.io/en/latest/>`_ is a command-line interface for stitching projections in the horizontal direction. Stitching is done manually by selecting the shift for each tile. The selection of correct set of shifts is made by looking at reconstructed slices and/or projections.

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

To install tomopy `tomopy <https://tomopy.readthedocs.io/en/latest/>`_/`tomopy cli <https://tomopycli.readthedocs.io/en/latest/>`_ follow the ` tomopy install <https://tomopy.readthedocs.io/en/latest/install.html>`_/`tomopycli install <https://tomopycli.readthedocs.io/en/latest/source/install.html>`_ instructions.

=====
Usage
=====

1. Find rotation center and shifts
==================================
::

  tile shift --folder-path /data/2021-12/Duchkov/mosaic --nsino-per-chunk 2 --binning 2 --center-search-width 10 --shift-search-width 30 --shift-search-step 2 --recon-engine tomocupy
  

2. Stitch data
==============
::

  tile stitch --folder-name /data/2021-12/Duchkov/mosaic --nproj-per-chunk 128 --x-shifts "[0, 2452, 2448, 2446, 2448]" 

Fro more options:
::

  tile -h
  tile stitch -h
  tile shift -h 

5. Reconstruct
==============

Once the stitching is completed the tomographic reconstruction can be done with `tomocupy <https://tomocupy.readthedocs.io/en/latest/>`_ or `tomopy <https://tomopy.readthedocs.io/en/latest/>`_/`tomopy cli <https://tomopycli.readthedocs.io/en/latest/>`_ 

With **tomocupy**
::
 
  tomocupy recon --file-name /data/2021-11/Banerjee/ROM_R_3474_072.h5 --rotation-axis 339 --reconstruction-type full --file-type double_fov --remove-stripe-method fw --binning 0 --nsino-per-chunk 8 --rotation-axis-auto manual

with **tomopy**
::
 
  tomopy recon --file-name /data/2021-11/Banerjee/ROM_R_3474_072.h5 --rotation-axis 339 --reconstruction-type full --file-type double_fov --remove-stripe-method fw --binning 0 --nsino-per-chunk 8 --rotation-axis-auto manual


For more options see:

::

  tomocupy -h
  tomopy -h
