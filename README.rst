======
mosaic
======

A command-line-interface for mosaic tomography data processing

Installation
------------

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

- `dxchange <https://github.com/data-exchange/dxchange>`_ version > 0.1.6 
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

Usage
-----

::

    $ mosaic -h

    optional arguments:
      -h, --help     show this help message and exit
      --config FILE  File name of configuration

    Commands:
  
        init         Create configuration file
        status       Show the mosaic-cli status
        extract      Extract the mosaic tomography files
        sort         Sort the mosaic tomography files according to their tile location
        tile         Return the mosaic tiles
        shift        testing shift


::

    $ mosaic init
        Creates a mosaic.conf default file

    $ mosaic status 
        Show the last used mosaic parameters

    $ mosaic tile -h

Example
-------

Using a `Foam dataset <https://tomobank.readthedocs.io/en/latest/source/data/docs.data.tomosaic.html#foam>`_  
from `tomobank <https://tomobank.readthedocs.io/en/latest/index.html>`_:

::

    $ mosaic tile --folder-name /local/data/2021-09/mosaic_data_folder/

Return a numpy array containing the tile filename::

    2021-09-28 19:43:41,178 - Started mosaic
    2021-09-28 19:43:41,178 - Saving log at /home/beams/FAST/logs/mosaic_2021-09-28_19_43_41.log
    2021-09-28 19:43:41,178 - General
    2021-09-28 19:43:41,178 -   config           /home/beams/FAST/mosaic.conf
    2021-09-28 19:43:41,178 -   verbose          True
    2021-09-28 19:43:41,178 - File reading
    2021-09-28 19:43:41,179 -   binning          0
    2021-09-28 19:43:41,179 -   nsino            0.5
    2021-09-28 19:43:41,179 - checking mosaic files ...
    2021-09-28 19:43:41,179 - Checking directory: /local/data/2021-09/Pasha for a mosaic scan
    2021-09-28 19:43:42,261 - mosaic file sorted
    2021-09-28 19:43:42,262 - x0y0: x = -3.800300; y = 15.000000, file name = /local/data/2021-09/Pasha/mosaic_test_001.h5, original file name = /local/data/2021-09/Pasha/mosaic_test_001.h5
    2021-09-28 19:43:42,262 - x1y0: x = -0.000300; y = 15.000000, file name = /local/data/2021-09/Pasha/mosaic_test_002.h5, original file name = /local/data/2021-09/Pasha/mosaic_test_002.h5
    2021-09-28 19:43:42,263 - x2y0: x = 3.799700; y = 15.000000, file name = /local/data/2021-09/Pasha/mosaic_test_003.h5, original file name = /local/data/2021-09/Pasha/mosaic_test_003.h5
    2021-09-28 19:43:42,263 - x0y1: x = -3.800300; y = 16.400000, file name = /local/data/2021-09/Pasha/mosaic_test_004.h5, original file name = /local/data/2021-09/Pasha/mosaic_test_004.h5
    2021-09-28 19:43:42,263 - x1y1: x = -0.000300; y = 16.400000, file name = /local/data/2021-09/Pasha/mosaic_test_005.h5, original file name = /local/data/2021-09/Pasha/mosaic_test_005.h5
    2021-09-28 19:43:42,263 - x2y1: x = 3.799700; y = 16.400000, file name = /local/data/2021-09/Pasha/mosaic_test_006.h5, original file name = /local/data/2021-09/Pasha/mosaic_test_006.h5
    2021-09-28 19:43:42,263 - x0y2: x = -3.800300; y = 17.800000, file name = /local/data/2021-09/Pasha/mosaic_test_007.h5, original file name = /local/data/2021-09/Pasha/mosaic_test_007.h5
    2021-09-28 19:43:42,263 - x1y2: x = -0.000300; y = 17.800000, file name = /local/data/2021-09/Pasha/mosaic_test_008.h5, original file name = /local/data/2021-09/Pasha/mosaic_test_008.h5
    2021-09-28 19:43:42,263 - x2y2: x = 3.799700; y = 17.800000, file name = /local/data/2021-09/Pasha/mosaic_test_009.h5, original file name = /local/data/2021-09/Pasha/mosaic_test_009.h5
    2021-09-28 19:43:42,264 - mosaic shift (x, y) in pixels: (2202, 811)
    2021-09-28 19:43:42,958 - image   size (x, y) in pixels: (2448, 900)
    2021-09-28 19:43:42,967 - mosaic file name grid:
                                                  x_0                                           x_1                                           x_2
    y_0  /local/data/2021-09/Pasha/mosaic_test_001.h5  /local/data/2021-09/Pasha/mosaic_test_002.h5  /local/data/2021-09/Pasha/mosaic_test_003.h5
    y_1  /local/data/2021-09/Pasha/mosaic_test_004.h5  /local/data/2021-09/Pasha/mosaic_test_005.h5  /local/data/2021-09/Pasha/mosaic_test_006.h5
    y_2  /local/data/2021-09/Pasha/mosaic_test_007.h5  /local/data/2021-09/Pasha/mosaic_test_008.h5  /local/data/2021-09/Pasha/mosaic_test_009.h5



To find the actual shifs using features in the image::

    $ mosaic shift --folder-name /local/data/2021-09/mosaic_data_folder/

To create a single sinogram to perform a test reconstruction run::

    $ mosaic stitch --folder-name /local/data/2021-09/mosaic_data_folder/ --test

to generate:

.. image:: docs/source/img/tomo_00094.png
    :width: 50%
    :align: center

and 

.. image:: docs/source/img/tomo_00094_rec.png
    :width: 50%
    :align: center

Typical Workflow
----------------

::

        $ mosaic tile   --folder-name /local/data/2021-06/Kaoumi/10_bottom/
	$ mosaic shift  --folder-name /local/data/2021-06/Kaoumi/10_bottom/
	$ mosaic stitch --folder-name /local/data/2021-06/Kaoumi/10_bottom/ --test
	$ mosaic stitch --folder-name /local/data/2021-06/Kaoumi/10_bottom/
	$ tomopy recon  --folder-name /local/data/2021-06/Kaoumi/10_bottom/tmp/mosaic.h5 --binning 2 --rotation-axis-auto manual --center-search-width 50 --rotation-axis 5653 --nsino-per-chunk 32 --reconstruction-type full --remove-stripe-method vo-all --fix-nan-and-inf True

