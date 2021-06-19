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
         2021-06-18 18:16:47,621 - Started mosaic
         2021-06-18 18:16:47,621 - Saving log at /home/beams/FAST/logs/mosaic_2021-06-18_18_16_47.log
         2021-06-18 18:16:47,621 - General
         2021-06-18 18:16:47,621 -   config           /home/beams/FAST/mosaic.conf
         2021-06-18 18:16:47,621 -   verbose          True
         2021-06-18 18:16:47,621 - File reading
         2021-06-18 18:16:47,621 -   binning          0
         2021-06-18 18:16:47,621 -   nsino            0.5
         2021-06-18 18:16:47,621 - reconstruction start
         021-06-18 18:16:47,621 - Checking directory: /local/data/mosaic for a mosaic scan
         2021-06-18 18:16:48,071 - {
        "000_camera_objective": ["2x", null],
        "000_full_file_name": ["/local/data/2021-06/Kaoumi/4_top_001.h5", null],
        "000_resolution": [1.7,"microns"],
        "000_sample_name": ["sample 4 top weld", null],
        "000_sample_x": [-7.600000000001529, "mm"],
        "000_sample_y": [17.599999999999994, "mm"],
        "001_camera_objective": ["2x", null],
        "001_full_file_name": ["/local/data/2021-06/Kaoumi/4_top_002.h5", null],
        "001_resolution": [1.7, "microns"],
        "001_sample_name": ["sample 4 top weld", null],
        "001_sample_x": [-3.800000000001546, "mm"],
        "001_sample_y": [17.599999999999994, "mm"]
        }
