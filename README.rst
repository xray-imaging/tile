======
mosaic
======

A command-line-interface for mosaic tomography data processing

Installation
------------

First, you must have `Conda <https://docs.conda.io/en/latest/miniconda.html>`_
installed.

Next install `tomopy  <https://tomopy.readthedocs.io/en/latest/install.html#installing-from-conda>`_

and::

    $ conda activate tomopy

then install the mosaic::

    $ git clone https://github.com/xray-imaging/mosaic.git
    $ cd mosaic
    $ python setup.py install


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
    extract      Extract all meta data needed to compose a mosaic dataset

::

    $ mosaic init
        Creates a mosaic.conf default file

    $ mosaic status 
        Show the last used mosaic parameters

    $ mosaic extract -h

Example
-------

Extract all meta data needed to compose a mosaic tomography dataset::

    $ mosaic extract --file-name /local/data/mosaic/
    2021-06-25 18:57:24,077 - Started mosaic
    2021-06-25 18:57:24,078 - Saving log at /home/beams/FAST/logs/mosaic_2021-06-25_18_57_24.log
    2021-06-25 18:57:24,078 - General
    2021-06-25 18:57:24,078 -   config           /home/beams/FAST/mosaic.conf
    2021-06-25 18:57:24,078 -   verbose          True
    2021-06-25 18:57:24,078 - File reading
    2021-06-25 18:57:24,078 -   binning          0
    2021-06-25 18:57:24,078 -   nsino            0.5
    2021-06-25 18:57:24,078 - checking mosaic files ...
    2021-06-25 18:57:24,078 - Checking directory: /local/data/mosaic for a mosaic scan
    2021-06-25 18:57:26,010 - /local/data/mosaic/tomosaic_tile_a.h5, [-3.800000000001546, 'mm'], [17.599999999999994, 'mm']. Original file name: /local/data/2021-06/Kaoumi/4_top_002.h5
    2021-06-25 18:57:26,011 - /local/data/mosaic/tomosaic_tile_d.h5, [-7.600000000001529, 'mm'], [18.999999999999996, 'mm']. Original file name: /local/data/2021-06/Kaoumi/4_top_006.h5
    2021-06-25 18:57:26,011 - /local/data/mosaic/tomosaic_tile_f.h5, [7.5999999999984595, 'mm'], [17.599999999999994, 'mm']. Original file name: /local/data/2021-06/Kaoumi/4_top_005.h5
    2021-06-25 18:57:26,011 - /local/data/mosaic/tomosaic_tile_g.h5, [3.7999999999984766, 'mm'], [20.399999999999995, 'mm']. Original file name: /local/data/2021-06/Kaoumi/4_top_014.h5
    2021-06-25 18:57:26,011 - /local/data/mosaic/tomosaic_tile_h.h5, [7.5999999999984595, 'mm'], [18.999999999999996, 'mm']. Original file name: /local/data/2021-06/Kaoumi/4_top_010.h5
    2021-06-25 18:57:26,011 - /local/data/mosaic/tomosaic_tile_j.h5, [-1.5347723092418164e-12, 'mm'], [18.999999999999996, 'mm']. Original file name: /local/data/2021-06/Kaoumi/4_top_008.h5
    2021-06-25 18:57:26,011 - /local/data/mosaic/tomosaic_tile_k.h5, [7.5999999999984595, 'mm'], [20.399999999999995, 'mm']. Original file name: /local/data/2021-06/Kaoumi/4_top_015.h5
    2021-06-25 18:57:26,011 - /local/data/mosaic/tomosaic_tile_m.h5, [3.7999999999984766, 'mm'], [18.999999999999996, 'mm']. Original file name: /local/data/2021-06/Kaoumi/4_top_009.h5
    2021-06-25 18:57:26,011 - /local/data/mosaic/tomosaic_tile_n.h5, [-7.600000000001529, 'mm'], [20.399999999999995, 'mm']. Original file name: /local/data/2021-06/Kaoumi/4_top_011.h5
    2021-06-25 18:57:26,011 - /local/data/mosaic/tomosaic_tile_o.h5, [-3.800000000001546, 'mm'], [20.399999999999995, 'mm']. Original file name: /local/data/2021-06/Kaoumi/4_top_012.h5
    2021-06-25 18:57:26,011 - /local/data/mosaic/tomosaic_tile_p.h5, [3.7999999999984766, 'mm'], [17.599999999999994, 'mm']. Original file name: /local/data/2021-06/Kaoumi/4_top_004.h5
    2021-06-25 18:57:26,011 - /local/data/mosaic/tomosaic_tile_r.h5, [-1.5347723092418164e-12, 'mm'], [17.599999999999994, 'mm']. Original file name: /local/data/2021-06/Kaoumi/4_top_003.h5
    2021-06-25 18:57:26,011 - /local/data/mosaic/tomosaic_tile_w.h5, [-1.5347723092418164e-12, 'mm'], [20.399999999999995, 'mm']. Original file name: /local/data/2021-06/Kaoumi/4_top_013.h5
    2021-06-25 18:57:26,012 - /local/data/mosaic/tomosaic_tile_x.h5, [-7.600000000001529, 'mm'], [17.599999999999994, 'mm']. Original file name: /local/data/2021-06/Kaoumi/4_top_001.h5
    2021-06-25 18:57:26,012 - /local/data/mosaic/tomosaic_tile_z.h5, [-3.800000000001546, 'mm'], [18.999999999999996, 'mm']. Original file name: /local/data/2021-06/Kaoumi/4_top_007.h5


Sort all meta data needed to compose a mosaic tomography dataset::

    $ mosaic sort --file-name /local/data/mosaic/
    2021-06-25 18:58:29,993 - Started mosaic
    2021-06-25 18:58:29,994 - Saving log at /home/beams/FAST/logs/mosaic_2021-06-25_18_58_29.log
    2021-06-25 18:58:29,994 - General
    2021-06-25 18:58:29,994 -   config           /home/beams/FAST/mosaic.conf
    2021-06-25 18:58:29,994 -   verbose          True
    2021-06-25 18:58:29,994 - File reading
    2021-06-25 18:58:29,994 -   binning          0
    2021-06-25 18:58:29,994 -   nsino            0.5
    2021-06-25 18:58:29,994 - checking mosaic files ...
    2021-06-25 18:58:29,994 - Checking directory: /local/data/mosaic for a mosaic scan
    2021-06-25 18:58:31,973 - mosaic file sorted
    2021-06-25 18:58:31,973 - /local/data/mosaic/tomosaic_tile_x.h5, [-7.600000000001529, 'mm'], [17.599999999999994, 'mm']. Original file name: /local/data/2021-06/Kaoumi/4_top_001.h5
    2021-06-25 18:58:31,973 - /local/data/mosaic/tomosaic_tile_a.h5, [-3.800000000001546, 'mm'], [17.599999999999994, 'mm']. Original file name: /local/data/2021-06/Kaoumi/4_top_002.h5
    2021-06-25 18:58:31,973 - /local/data/mosaic/tomosaic_tile_r.h5, [-1.5347723092418164e-12, 'mm'], [17.599999999999994, 'mm']. Original file name: /local/data/2021-06/Kaoumi/4_top_003.h5
    2021-06-25 18:58:31,974 - /local/data/mosaic/tomosaic_tile_p.h5, [3.7999999999984766, 'mm'], [17.599999999999994, 'mm']. Original file name: /local/data/2021-06/Kaoumi/4_top_004.h5
    2021-06-25 18:58:31,974 - /local/data/mosaic/tomosaic_tile_f.h5, [7.5999999999984595, 'mm'], [17.599999999999994, 'mm']. Original file name: /local/data/2021-06/Kaoumi/4_top_005.h5
    2021-06-25 18:58:31,974 - /local/data/mosaic/tomosaic_tile_d.h5, [-7.600000000001529, 'mm'], [18.999999999999996, 'mm']. Original file name: /local/data/2021-06/Kaoumi/4_top_006.h5
    2021-06-25 18:58:31,974 - /local/data/mosaic/tomosaic_tile_z.h5, [-3.800000000001546, 'mm'], [18.999999999999996, 'mm']. Original file name: /local/data/2021-06/Kaoumi/4_top_007.h5
    2021-06-25 18:58:31,974 - /local/data/mosaic/tomosaic_tile_j.h5, [-1.5347723092418164e-12, 'mm'], [18.999999999999996, 'mm']. Original file name: /local/data/2021-06/Kaoumi/4_top_008.h5
    2021-06-25 18:58:31,974 - /local/data/mosaic/tomosaic_tile_m.h5, [3.7999999999984766, 'mm'], [18.999999999999996, 'mm']. Original file name: /local/data/2021-06/Kaoumi/4_top_009.h5
    2021-06-25 18:58:31,974 - /local/data/mosaic/tomosaic_tile_h.h5, [7.5999999999984595, 'mm'], [18.999999999999996, 'mm']. Original file name: /local/data/2021-06/Kaoumi/4_top_010.h5
    2021-06-25 18:58:31,974 - /local/data/mosaic/tomosaic_tile_n.h5, [-7.600000000001529, 'mm'], [20.399999999999995, 'mm']. Original file name: /local/data/2021-06/Kaoumi/4_top_011.h5
    2021-06-25 18:58:31,974 - /local/data/mosaic/tomosaic_tile_o.h5, [-3.800000000001546, 'mm'], [20.399999999999995, 'mm']. Original file name: /local/data/2021-06/Kaoumi/4_top_012.h5
    2021-06-25 18:58:31,974 - /local/data/mosaic/tomosaic_tile_w.h5, [-1.5347723092418164e-12, 'mm'], [20.399999999999995, 'mm']. Original file name: /local/data/2021-06/Kaoumi/4_top_013.h5
    2021-06-25 18:58:31,974 - /local/data/mosaic/tomosaic_tile_g.h5, [3.7999999999984766, 'mm'], [20.399999999999995, 'mm']. Original file name: /local/data/2021-06/Kaoumi/4_top_014.h5
    2021-06-25 18:58:31,975 - /local/data/mosaic/tomosaic_tile_k.h5, [7.5999999999984595, 'mm'], [20.399999999999995, 'mm']. Original file name: /local/data/2021-06/Kaoumi/4_top_015.h5


Add the tile coordinated (top-left is x0y0) to compose a mosaic tomography dataset::

    $ mosaic tile --file-name /local/data/mosaic/
    Warning: dxfile module not found
    Warning: netCDF4 module not found
    spefile module not found
    netCDF4 module not found
    EdfFile module not found
    2021-07-09 18:21:31,268 - Started mosaic
    2021-07-09 18:21:31,268 - Saving log at /home/beams/FAST/logs/mosaic_2021-07-09_18_21_31.log
    2021-07-09 18:21:31,268 - General
    2021-07-09 18:21:31,268 -   config           /home/beams/FAST/mosaic.conf
    2021-07-09 18:21:31,268 -   verbose          True
    2021-07-09 18:21:31,268 - File reading
    2021-07-09 18:21:31,268 -   binning          0
    2021-07-09 18:21:31,268 -   nsino            0.5
    2021-07-09 18:21:31,268 - checking mosaic files ...
    2021-07-09 18:21:31,269 - Checking directory: /local/data/mosaic for a mosaic scan
    2021-07-09 18:21:32,689 - mosaic file sorted
    2021-07-09 18:21:32,690 - x0y0: x = -7.600000; y = 17.600000, file name = /local/data/mosaic/tomosaic_tile_x.h5
    2021-07-09 18:21:32,690 - x1y0: x = -3.800000; y = 17.600000, file name = /local/data/mosaic/tomosaic_tile_a.h5
    2021-07-09 18:21:32,690 - x2y0: x = -0.000000; y = 17.600000, file name = /local/data/mosaic/tomosaic_tile_r.h5
    2021-07-09 18:21:32,690 - x3y0: x = 3.800000; y = 17.600000, file name = /local/data/mosaic/tomosaic_tile_p.h5
    2021-07-09 18:21:32,690 - x4y0: x = 7.600000; y = 17.600000, file name = /local/data/mosaic/tomosaic_tile_f.h5
    2021-07-09 18:21:32,690 - x0y1: x = -7.600000; y = 19.000000, file name = /local/data/mosaic/tomosaic_tile_d.h5
    2021-07-09 18:21:32,691 - x1y1: x = -3.800000; y = 19.000000, file name = /local/data/mosaic/tomosaic_tile_z.h5
    2021-07-09 18:21:32,691 - x2y1: x = -0.000000; y = 19.000000, file name = /local/data/mosaic/tomosaic_tile_j.h5
    2021-07-09 18:21:32,691 - x3y1: x = 3.800000; y = 19.000000, file name = /local/data/mosaic/tomosaic_tile_m.h5
    2021-07-09 18:21:32,691 - x4y1: x = 7.600000; y = 19.000000, file name = /local/data/mosaic/tomosaic_tile_h.h5
    2021-07-09 18:21:32,691 - x0y2: x = -7.600000; y = 20.400000, file name = /local/data/mosaic/tomosaic_tile_n.h5
    2021-07-09 18:21:32,691 - x1y2: x = -3.800000; y = 20.400000, file name = /local/data/mosaic/tomosaic_tile_o.h5
    2021-07-09 18:21:32,691 - x2y2: x = -0.000000; y = 20.400000, file name = /local/data/mosaic/tomosaic_tile_w.h5
    2021-07-09 18:21:32,691 - x3y2: x = 3.800000; y = 20.400000, file name = /local/data/mosaic/tomosaic_tile_g.h5
    2021-07-09 18:21:32,691 - x4y2: x = 7.600000; y = 20.400000, file name = /local/data/mosaic/tomosaic_tile_k.h5
