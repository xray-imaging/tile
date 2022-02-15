=====
Usage
=====

1. Verify the dataset is valid
==============================
::
    (tile)$ tile info --folder-name /local/data/mosaic/mosaic/
    2022-02-15 17:13:17,505 - Started tile
    2022-02-15 17:13:17,505 - Saving log at /home/beams/FAST/logs/tile_2022-02-15_17_13_17.log
    2022-02-15 17:13:17,505 - General
    2022-02-15 17:13:17,505 -   config           /home/beams/FAST/tile.conf
    2022-02-15 17:13:17,505 -   verbose          False
    2022-02-15 17:13:17,505 - checking tile files ...
    2022-02-15 17:13:17,505 - Checking directory: /local/data/mosaic/mosaic for a tile scan
    2022-02-15 17:13:18,773 - tile file sorted
    2022-02-15 17:13:18,774 - x0y0: x = -3.800300; y = 15.000000, file name = /local/data/mosaic/mosaic/    mosaic_test_001.h5, original file name = /local/data/2021-09/Pasha/mosaic_test_001.h5
    2022-02-15 17:13:18,774 - x1y0: x = -0.000300; y = 15.000000, file name = /local/data/mosaic/mosaic/    mosaic_test_002.h5, original file name = /local/data/2021-09/Pasha/mosaic_test_002.h5
    2022-02-15 17:13:18,774 - x2y0: x = 3.799700; y = 15.000000, file name = /local/data/mosaic/mosaic/    mosaic_test_003.h5, original file name = /local/data/2021-09/Pasha/mosaic_test_003.h5
    2022-02-15 17:13:18,774 - x0y1: x = -3.800300; y = 16.400000, file name = /local/data/mosaic/mosaic/    mosaic_test_004.h5, original file name = /local/data/2021-09/Pasha/mosaic_test_004.h5
    2022-02-15 17:13:18,774 - x1y1: x = -0.000300; y = 16.400000, file name = /local/data/mosaic/mosaic/    mosaic_test_005.h5, original file name = /local/data/2021-09/Pasha/mosaic_test_005.h5
    2022-02-15 17:13:18,774 - x2y1: x = 3.799700; y = 16.400000, file name = /local/data/mosaic/mosaic/    mosaic_test_006.h5, original file name = /local/data/2021-09/Pasha/mosaic_test_006.h5
    2022-02-15 17:13:18,774 - x0y2: x = -3.800300; y = 17.800000, file name = /local/data/mosaic/mosaic/    mosaic_test_007.h5, original file name = /local/data/2021-09/Pasha/mosaic_test_007.h5
    2022-02-15 17:13:18,774 - x1y2: x = -0.000300; y = 17.800000, file name = /local/data/mosaic/mosaic/    mosaic_test_008.h5, original file name = /local/data/2021-09/Pasha/mosaic_test_008.h5
    2022-02-15 17:13:18,774 - x2y2: x = 3.799700; y = 17.800000, file name = /local/data/mosaic/mosaic/    mosaic_test_009.h5, original file name = /local/data/2021-09/Pasha/mosaic_test_009.h5
    2022-02-15 17:13:18,985 - image   size (x, y) in pixels: (2448, 900)
    2022-02-15 17:13:18,985 - tile shift (x, y) in pixels: (2202, 811)
    2022-02-15 17:13:18,986 - tile overlap (x, y) in pixels: (246, 89)
    2022-02-15 17:13:18,992 - tile file name grid:
                                                  y_0                                               y_1                                           y_2
    x_0  /local/data/mosaic/mosaic/mosaic_test_001.h5  /local/data/mosaic/mosaic/mosaic_test_002.h5  /local/    data/mosaic/mosaic/mosaic_test_003.h5
    x_1  /local/data/mosaic/mosaic/mosaic_test_004.h5  /local/data/mosaic/mosaic/mosaic_test_005.h5  /local/    data/mosaic/mosaic/mosaic_test_006.h5
    x_2  /local/data/mosaic/mosaic/mosaic_test_007.h5  /local/data/mosaic/mosaic/mosaic_test_008.h5  /local/    data/mosaic/mosaic/mosaic_test_009.h5

2. Find rotation center and shifts
==================================
::

    (tile)$ tile shift --folder-path /data/2021-12/Duchkov/mosaic --nsino-per-chunk 2 --binning 2 --center-search-width 10 --shift-search-width 30 --shift-search-step 2 --recon-engine tomocupy
  

3. Stitch data
==============
::

    (tile)$ tile stitch --folder-name /data/2021-12/Duchkov/mosaic --nproj-per-chunk 128 --x-shifts "[0, 2452, 2448, 2446, 2448]" 

Fro more options:
::

    (tile)$ tile -h
    (tile)$ tile stitch -h
    (tile)$ tile shift -h 

4. Reconstruct
==============

Once the stitching is completed the tomographic reconstruction can be done with `tomocupy <https://tomocupy.readthedocs.io/en/latest/>`_ or `tomopy <https://tomopy.readthedocs.io/en/latest/>`_/`tomopycli <https://tomopycli.readthedocs.io/en/latest/>`_:

with **tomocupy**
::
 
    (tile)$ tomocupy recon --file-name /data/2021-11/Banerjee/ROM_R_3474_072.h5 --rotation-axis 339 --reconstruction-type full --file-type double_fov --remove-stripe-method fw --binning 0 --nsino-per-chunk 8 --rotation-axis-auto manual

with **tomopy**
::
 
    (tile)$ tomopy recon --file-name /data/2021-11/Banerjee/ROM_R_3474_072.h5 --rotation-axis 339 --reconstruction-type full --file-type double_fov --remove-stripe-method fw --binning 0 --nsino-per-chunk 8 --rotation-axis-auto manual


For more options:

::

    (tile)$ tomocupy -h
    (tile)$ tomopy -h
