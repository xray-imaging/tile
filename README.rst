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
        tile         Show the file names in thier mosaic tile location
        shift        Calculate the tile horizonal and vertical overlap
        stitch       Create a single hdf file containing the mosaic datasets


Typical Workflow
----------------

::

    $ mosaic tile    --folder-name 2021-09/Pasha/13_center/
    $ mosaic shift   --folder-name 2021-09/Pasha/13_center/
    $ mosaic stitch  --folder-name 2021-09/Pasha/13_center/
    $ tomopy recon   --file-name 2021-09/Pasha/13_center/mosaic/mosaic.h5  --binning 2 --rotation-axis-auto manual --center-search-width 10 --rotation-axis 5653 --nsino-per-chunk 32 --reconstruction-type try --remove-stripe-method vo-all --fix-nan-and-inf True
    $ tomopy recon   --file-name 2021-09/Pasha/13_center/mosaic/mosaic.h5  --binning 2 --rotation-axis-auto manual --center-search-width 10 --rotation-axis 5653 --nsino-per-chunk 32 --reconstruction-type full --remove-stripe-method vo-all --fix-nan-and-inf True


Example
-------

Using a `Foam dataset <https://tomobank.readthedocs.io/en/latest/source/data/docs.data.tomosaic.html#foam>`_  
from `tomobank <https://tomobank.readthedocs.io/en/latest/index.html>`_:

::

    $ mosaic tile --folder-name mosaic_data_folder/

Return a numpy array containing the tile filename::

    2021-10-20 13:24:31,468 - Started mosaic
    2021-10-20 13:24:31,468 - Saving log at /home/beams/TOMO/logs/mosaic_2021-10-20_13_24_31.log
    2021-10-20 13:24:31,468 - General
    2021-10-20 13:24:31,468 -   config           /home/beams/TOMO/mosaic.conf
    2021-10-20 13:24:31,468 -   verbose          True
    2021-10-20 13:24:31,468 - File IO
    2021-10-20 13:24:31,468 -   binning          0
    2021-10-20 13:24:31,468 -   nsino            0.5
    2021-10-20 13:24:31,468 -   threshold        0.5
    2021-10-20 13:24:31,468 - checking mosaic files ...
    2021-10-20 13:24:31,468 - Checking directory: /data/2021-06/Kaoumi/7_top for a mosaic scan
    2021-10-20 13:24:32,421 - mosaic file sorted
    2021-10-20 13:24:32,421 - x0y0: x = -7.600000; y = 17.300000, file name = 2021-09/Pasha/mosaic_test_036.h5, original file name = 2021-09/Pasha/mosaic_test_036.h5
    2021-10-20 13:24:32,421 - x1y0: x = -3.800000; y = 17.300000, file name = 2021-09/Pasha/mosaic_test_037.h5, original file name = 2021-09/Pasha/mosaic_test_037.h5
    2021-10-20 13:24:32,421 - x2y0: x = -0.000000; y = 17.300000, file name = 2021-09/Pasha/mosaic_test_038.h5, original file name = 2021-09/Pasha/mosaic_test_038.h5
    2021-10-20 13:24:32,421 - x3y0: x = 3.800000; y = 17.300000, file name = 2021-09/Pasha/mosaic_test_039.h5, original file name = 2021-09/Pasha/mosaic_test_039.h5
    2021-10-20 13:24:32,421 - x4y0: x = 7.600000; y = 17.300000, file name = 2021-09/Pasha/mosaic_test_040.h5, original file name = 2021-09/Pasha/mosaic_test_040.h5
    2021-10-20 13:24:32,421 - x0y1: x = -7.600000; y = 18.700000, file name = 2021-09/Pasha/mosaic_test_041.h5, original file name = 2021-09/Pasha/mosaic_test_041.h5
    2021-10-20 13:24:32,421 - x1y1: x = -3.800000; y = 18.700000, file name = 2021-09/Pasha/mosaic_test_042.h5, original file name = 2021-09/Pasha/mosaic_test_042.h5
    2021-10-20 13:24:32,421 - x2y1: x = -0.000000; y = 18.700000, file name = 2021-09/Pasha/mosaic_test_043.h5, original file name = 2021-09/Pasha/mosaic_test_043.h5
    2021-10-20 13:24:32,421 - x3y1: x = 3.800000; y = 18.700000, file name = 2021-09/Pasha/mosaic_test_044.h5, original file name = 2021-09/Pasha/mosaic_test_044.h5
    2021-10-20 13:24:32,421 - x4y1: x = 7.600000; y = 18.700000, file name = 2021-09/Pasha/mosaic_test_045.h5, original file name = 2021-09/Pasha/mosaic_test_045.h5
    2021-10-20 13:24:32,421 - x0y2: x = -7.600000; y = 20.100000, file name = 2021-09/Pasha/mosaic_test_046.h5, original file name = 2021-09/Pasha/mosaic_test_046.h5
    2021-10-20 13:24:32,421 - x1y2: x = -3.800000; y = 20.100000, file name = 2021-09/Pasha/mosaic_test_047.h5, original file name = 2021-09/Pasha/mosaic_test_047.h5
    2021-10-20 13:24:32,421 - x2y2: x = -0.000000; y = 20.100000, file name = 2021-09/Pasha/mosaic_test_048.h5, original file name = 2021-09/Pasha/mosaic_test_048.h5
    2021-10-20 13:24:32,421 - x3y2: x = 3.800000; y = 20.100000, file name = 2021-09/Pasha/mosaic_test_049.h5, original file name = 2021-09/Pasha/mosaic_test_049.h5
    2021-10-20 13:24:32,421 - x4y2: x = 7.600000; y = 20.100000, file name = 2021-09/Pasha/mosaic_test_050.h5, original file name = 2021-09/Pasha/mosaic_test_050.h5
    2021-10-20 13:24:32,615 - image   size (x, y) in pixels: (2448, 900)
    2021-10-20 13:24:32,615 - mosaic shift (x, y) in pixels: (2235, 823)
    2021-10-20 13:24:32,615 - tile overlap (x, y) in pixels: (213, 77)
    2021-10-20 13:24:32,651 - mosaic file name grid:
                 y_0                                      y_1                               y_2                               y_3                            y_4
    x_0  2021-09/Pasha/mosaic_test_036.h5  2021-09/Pasha/mosaic_test_037.h5  2021-09/Pasha/mosaic_test_038.h5  2021-09/Pasha/mosaic_test_039.h5  2021-09/Pasha/mosaic_test_040.h5
    x_1  2021-09/Pasha/mosaic_test_041.h5  2021-09/Pasha/mosaic_test_042.h5  2021-09/Pasha/mosaic_test_043.h5  2021-09/Pasha/mosaic_test_044.h5  2021-09/Pasha/mosaic_test_045.h5
    x_2  2021-09/Pasha/mosaic_test_046.h5  2021-09/Pasha/mosaic_test_047.h5  2021-09/Pasha/mosaic_test_048.h5  2021-09/Pasha/mosaic_test_049.h5  2021-09/Pasha/mosaic_test_050.h5




To find the actual shifs using features in the image::

    $ mosaic shift --folder-name mosaic_data_folder/

    2021-10-20 10:11:14,117 - Shift information saved in 2021-09/Pasha/mosaic/shifts_h.txt
    2021-10-20 10:11:14,117 - Shift information saved in 2021-09/Pasha/mosaic/shifts_v.txt
    2021-10-20 10:11:14,118 - Shift information saved in 2021-09/Pasha/mosaic/multipliers.txt

After running **mosaic shift** check the **shift_h.txt** and **shift_v.txt** files located in the **10_bottom.mosaic** folder for possible error in the feature autodetection.

To create a single image to check the stitching run::

    $ mosaic stitch --folder-name mosaic_data_folder/ --test

to generate:

.. image:: docs/source/img/tomo_00094.png
    :width: 50%
    :align: center

and 

.. image:: docs/source/img/tomo_00094_rec.png
    :width: 50%
    :align: center

To create a single hdf file containing the mosaic datasets::

    $ mosaic stitch --folder-name mosaic_data_folder/
    2021-10-20 10:33:17,431 - Stitched h5 file is saved as 2021-09/Pasha/mosaic/mosaic.h5


ready to be reconstructed with `tomopy cli <https://tomopycli.readthedocs.io/en/latest/>`_

::

    $ tomopy recon  --file-name  mosaic_data_folder/mosaic/mosaic.h5  --binning 2 --rotation-axis-auto manual --center-search-width 5 --rotation-axis 5653 --nsino-per-chunk 32 --reconstruction-type full --remove-stripe-method vo-all --fix-nan-and-inf True



