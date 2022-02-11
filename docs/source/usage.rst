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