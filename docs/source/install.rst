=======
Install
=======

This section covers the basics of how to download and install
`Mosaic <https://github.com/xray-imaging/mosaic>`_.

First, you must have `Conda <https://docs.conda.io/en/latest/miniconda.html>`_
installed and create a dedicated conda environment::

     conda create -n mosaic

and::

    $ conda activate mosaic

then install the mosaic::

    $ git clone https://github.com/xray-imaging/mosaic.git
    $ cd mosaic
    $ python setup.py install

Dependencies
------------

- `dxchange <https://github.com/xray-imaging/mosaic>`_ version > 0.1.6 
- pandas => ``conda install pandas``
- tabulate
- numpy
- pandas
- h5py
- scipy
- tomopy
- libopencv
- opencv
- py-opencv
- tifffile  => ``pip install tifffile``