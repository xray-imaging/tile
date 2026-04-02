=====
Usage
=====

Overview
========

**tile** is a command-line tool for stitching tomographic mosaic datasets — sets of overlapping
scans that together cover a field of view larger than a single detector frame.

The full pipeline from raw HDF5 files to a reconstructed 3D volume has the following steps.
Not all steps are required for every dataset; the table below shows which are optional.

.. list-table::
   :widths: 5 20 10 65
   :header-rows: 1

   * - #
     - Command
     - Required?
     - What it does
   * - 1
     - ``tile show``
     - Yes
     - Verify the dataset — print tile grid, image size, nominal overlap
   * - 2
     - ``tile bin``
     - Optional
     - Spatially bin raw files to reduce data volume before processing
   * - 3
     - ``tile dump-flats``
     - Optional
     - Collect a flat field basis for per-projection NNLS flat correction
   * - 4
     - ``tile panoramic``
     - Optional
     - Quick visual check — save one stitched projection to a tiff
   * - 5
     - ``tile center``
     - Yes
     - Find the rotation axis location (trial reconstruction stack)
   * - 6
     - ``tile shift``
     - Yes
     - Fine-tune horizontal tile positions
   * - 7
     - ``tile stitch``
     - Yes
     - Horizontally stitch all tiles in each y-row → ``tile.h5``
   * - 8
     - ``tile vstitch``
     - Multi-row only
     - Vertically stitch the per-row ``tile.h5`` files → ``vstitch.h5``
   * - 9
     - ``tile double-fov``
     - 360° scans only
     - Convert 360° dataset to 180° by stitching paired projections
   * - 10
     - ``tomocupy recon``
     - Yes
     - Final 3D reconstruction


HDF5 metadata requirements
===========================

tile reads the following metadata from each HDF5 file to sort tiles by position and compute the
nominal overlap:

#. Sample X position (mm): ``/measurement/instrument/sample_motor_stack/setup/x``
#. Sample Y position (mm): ``/measurement/instrument/sample_motor_stack/setup/y``
#. Image resolution (µm/px): ``/measurement/instrument/detection_system/objective/resolution``
#. Original file name: ``/measurement/sample/file/full_name``

These paths follow the `dxfile <https://dxfile.readthedocs.io/en/latest/source/demo/doc.areadetector.html#xml>`_
convention used at `2-BM <https://docs2bm.readthedocs.io/en/latest/>`_,
`7-BM <https://docs7bm.readthedocs.io/en/latest/>`_, and
`32-ID <https://docs32id.readthedocs.io/en/latest/>`_.

If your metadata is stored elsewhere, override the paths at runtime::

    tile show --sample-x '/your/path/to/x' --sample-y '/your/path/to/y'

.. note::

   At 2-BM, flat fields are collected at the **end** of each scan with the sample moved to
   ``SampleOutX``.  Because the HDF attribute is written ``OnFileClose``, the motor RBV at
   that moment reflects the flat-field position rather than the scan position.  The correct
   tile X positions are stored in ``/process/acquisition/flat_fields/sample/in_x`` and are
   read automatically by tile.  If you collected data before this fix was in place, pass the
   correct path explicitly::

       tile show --sample-x /process/acquisition/flat_fields/sample/in_x


----

Step 1 — Verify the dataset (``tile show``)
===========================================

Read the HDF metadata from every tile file, sort them by motor position, and print the tile
grid layout, image size, and nominal overlap::

    (tile) tomo@tomo4 $ tile show --folder-name /data/2021-12/Duchkov/mosaic/
    2022-02-16 11:33:38,485 - Started tile
    2022-02-16 11:33:38,485 - Saving log at /home/beams/TOMO/logs/tile_2022-02-16_11_33_38.log
    2022-02-16 11:33:38,485 - checking tile files ...
    2022-02-16 11:33:38,485 - Checking directory: /data/2021-12/Duchkov/mosaic for a tile scan
    2022-02-16 11:33:38,780 - tile file sorted
    2022-02-16 11:33:38,780 - x0y0: x = -0.0001; y = 28.0, file name = .../mosaic_2073.h5
    2022-02-16 11:33:38,780 - x1y0: x =  0.8499; y = 28.0, file name = .../mosaic_2074.h5
    ...
    2022-02-16 11:33:38,918 - image   size (x, y) in pixels: (2448, 2048)
    2022-02-16 11:33:38,918 - tile shift (x, y) in pixels: (2428, 0)
    2022-02-16 11:33:38,918 - tile overlap (x, y) in pixels: (20, 2048)
    2022-02-16 11:33:38,918 - tile file name grid:
                                              y_0
    x_0  /data/2021-12/Duchkov/mosaic/mosaic_2073.h5
    x_1  /data/2021-12/Duchkov/mosaic/mosaic_2074.h5
    ...

Check that:

- All expected tiles are present and in the correct row/column positions.
- The nominal overlap (``tile overlap``) is a reasonable fraction of the tile width
  (typically 5–20%).

.. warning::

   ``--reverse-grid True`` (the default at 2-BM) reverses the tile order within each row,
   so that tile x0 is placed at the left of the stitched image.  This matches the 2-BM
   detector geometry where positive motor X moves the sample to the **left** in the image.
   Pass ``--reverse-grid False`` if positive X moves the sample to the **right**.


----

Step 2 — Bin raw files (``tile bin``) — *optional*
===================================================

For large datasets (e.g. 6000 projections × 4852 × 6464 px per tile) it is practical to work
on a spatially-binned copy during the alignment steps (center search, shift tuning).  Once the
parameters are confirmed on the binned data the final stitch can be done at full resolution.

``tile bin`` copies all ``.h5`` files from ``--folder-name``, applies ``2**binning × 2**binning``
spatial binning to the exchange datasets, and optionally subsamples every ``--bin-step``\th
projection.  Output files are written to ``<folder-name>/bin<N>x<N>/`` by default::

    (tile) tomo@tomo4 $ tile bin --folder-name /data/raw/ --binning 1 --bin-step 2
    # → outputs to /data/raw/bin2x2/  (2×2 spatial bin, every 2nd projection)

    (tile) tomo@tomo4 $ tile bin --folder-name /data/raw/ --binning 2 --bin-step 1
    # → outputs to /data/raw/bin4x4/  (4×4 spatial bin, all projections)

For a multi-row mosaic where each row lives in a separate subfolder, run ``tile bin`` once per
row folder::

    for ydir in y0 y1 y2 y3; do
        tile bin --folder-name /data/raw/$ydir/ --binning 1 --bin-step 2
    done

Key parameters:

.. list-table::
   :widths: 30 70
   :header-rows: 0

   * - ``--binning N``
     - Spatial bin factor = 2\ :sup:`N` (0=none, 1=2×2, 2=4×4, …)
   * - ``--bin-step N``
     - Keep every Nth projection (1 = keep all)
   * - ``--bin-output-dir PATH``
     - Override the default output directory


----

Step 3 — Collect flat field basis (``tile dump-flats``) — *optional*
=====================================================================

``tile dump-flats`` collects flat fields from all tile HDF5 files and saves them as a basis
file for per-projection NNLS flat correction.  For each input file it writes two averaged
frames: the mean of the first half and the mean of the second half of the flat field frames.
This basis is then passed to subsequent commands via ``--flats-file``.

Use this when:

- Flat field illumination varies significantly across the scan (beam intensity drift, ring
  artifacts from a specific flat, etc.).
- You want per-projection flat correction rather than a simple averaged flat.

For a single-folder dataset::

    (tile) tomo@tomo4 $ tile dump-flats --folder-name /data/raw/bin2x2/ \
                                        --dump-flats-output flats.h5
    # → writes /data/raw/bin2x2/flats.h5

For a multi-row dataset where each row lives in a subfolder::

    (tile) tomo@tomo4 $ tile dump-flats --folder-name /data/raw/bin2x2/ \
                                        --y-folders y0,y1,y2,y3 \
                                        --dump-flats-output flats.h5
    # → collects flats from y0/, y1/, y2/, y3/  and writes /data/raw/bin2x2/flats.h5

The resulting ``flats.h5`` is passed to ``tile center``, ``tile shift``, and ``tile stitch``
via the ``--flats-file`` option.

Key parameters:

.. list-table::
   :widths: 30 70
   :header-rows: 0

   * - ``--y-folders``
     - Comma-separated subfolder names (e.g. ``y0,y1,y2,y3``).  Leave empty to use
       ``--folder-name`` directly.
   * - ``--dump-flats-output``
     - Output filename inside ``--folder-name`` (default: ``flats.h5``)
   * - ``--reverse-step``
     - Flip the X direction when reading flats (``True``/``False``, default ``False``)


----

Step 4 — Quick panoramic inspection (``tile panoramic``) — *optional*
======================================================================

Before running the time-consuming center search, use ``tile panoramic`` to visually confirm
the tile layout.  It reads a single projection (at the angle set by ``--nprojection``, default
0.5 = midpoint) from each tile, normalises it, and saves a wide stitched image to
``tile/panoramic.tif`` in the dataset folder::

    (tile) tomo@tomo4 $ tile panoramic --flat-linear True

Open the result in `Fiji ImageJ <https://imagej.net/software/fiji/>`_ to confirm:

- All tiles are present and in the correct left-to-right order.
- The nominal overlap looks approximately correct (seam regions may not be perfect yet).
- The sample fills the expected field of view.

Once you have the correct shifts from ``tile shift``, you can regenerate the panoramic with
the corrected positions to verify the alignment::

    (tile) tomo@tomo4 $ tile panoramic --flat-linear True --x-shifts "[0, 5430, 5419]"

Pass ``--show`` to display the image interactively in a matplotlib window (requires a display).


----

Step 5 — Find the rotation center (``tile center``)
====================================================

``tile center`` stitches all horizontal tiles in the **top row** of the mosaic using the
nominal overlap from the HDF file, then reconstructs a stack of trial slices, each with a
slightly different rotation axis position.  You inspect the stack and pick the sharpest image.

The sinogram row used is controlled by ``--nsino`` (0 = top, 1 = bottom, default 0.5 =
vertical centre of the detector).  With ``--binning N``, ``2**N`` consecutive rows are
averaged to improve signal.

.. warning::

   Only the **centre of the reconstructed image** is reliable at this stage.  The outer
   regions may look blurry because the nominal tile overlap is only approximate.  Ignore
   those regions and focus on the centre when selecting the rotation axis.

.. warning::

   ``--file-type double_fov`` (the default) tells tomocupy to treat the input as a 360°
   scan and mirror the sinogram.  This is the standard mode at 2-BM for 360° acquisitions.
   Pass ``--file-type standard`` for ordinary 180° scans.

**Recommended workflow — two passes:**

*Pass 1 — coarse search* (wide step, large range)::

    (tile) tomo@tomo4 $ tile center --recon-engine tomocupy \
        --rotation-axis 400 --center-search-width 200 --center-search-step 10 \
        --file-type double_fov --binning 2 --nsino-per-chunk 2 --flat-linear True

Open the try-center stack from::

    /path/to/data/tile_rec/try_center/tmp/recon*

in Fiji (File → Import → Image Sequence).  Zoom into the **centre** of the image and move the
slider until the reconstruction looks sharp and ring-free.  Note the rotation axis value shown
in the top-left corner of the best image.

*Pass 2 — fine search* (small step, narrow range)::

    (tile) tomo@tomo4 $ tile center --recon-engine tomocupy \
        --rotation-axis 656 --center-search-width 10 --center-search-step 1 \
        --file-type double_fov --binning 2 --nsino-per-chunk 2 --flat-linear True

Record the final rotation axis value (e.g. 650) for the next step.

Key parameters:

.. list-table::
   :widths: 30 70
   :header-rows: 0

   * - ``--rotation-axis``
     - Starting guess for the rotation axis (pixels).  Use -1 to default to image centre.
   * - ``--center-search-width``
     - Half-width of the search range (pixels).
   * - ``--center-search-step``
     - Step size between trials (pixels).
   * - ``--nsino``
     - Relative vertical position of the sinogram row (0–1).
   * - ``--binning``
     - Spatial binning (0=none, 1=2×, 2=4×).
   * - ``--nsino-per-chunk``
     - Number of sinogram rows averaged per chunk (increase for better SNR).
   * - ``--flat-linear True``
     - Enable linear interpolation of flat fields across the scan.
   * - ``--flats-file PATH``
     - Use per-projection NNLS flat correction from a ``dump-flats`` basis file.
   * - ``--file-type``
     - ``double_fov`` (default, 360° scans) or ``standard`` (180° scans).
   * - ``--recon-engine``
     - ``tomocupy`` (default) or ``tomopy``.


----

Step 6 — Fine-tune tile shifts (``tile shift``)
================================================

``tile center`` used the nominal overlap stored in the HDF file.  ``tile shift`` refines each
horizontal tile position one boundary at a time, keeping all previously fixed tiles fixed and
sliding only the next tile.

For each boundary between adjacent tiles, it reconstructs a stack of slices by shifting the
overlap by ``--shift-search-width`` pixels in steps of ``--shift-search-step`` on either side
of the nominal position.  A colour-coded index map is printed:

- **green** = negative offset (tiles closer than nominal)
- **red** = 0 offset (perfect motor positioning = nominal overlap)
- **yellow** = positive offset (tiles farther than nominal)

::

    (tile) tomo@tomo4 $ tile shift --rotation-axis 650 --flat-linear True \
        --shift-search-width 60 --shift-search-step 1
    ...
    Please enter rotation center (656.2): 650
    ...
    Please enter id for tile 1 shift [nominal: 60] ...: 74
    2026-03-25 15:47:02,348 - Selected offset for tile 1: +14 px (index 74)
    2026-03-25 15:47:02,349 - Current shifts: [0 5430 5416]
    ...
    Please enter id for tile 2 shift [nominal: 60] ...: 63
    2026-03-25 16:02:20,813 - Selected offset for tile 2: +3 px (index 63)
    2026-03-25 16:02:20,813 - Current shifts: [0 5430 5419]
    2026-03-25 16:02:20,814 - Center 650
    2026-03-25 16:02:20,815 - Relative shifts [0, 5430, 5419]

Inspect the try-recon stack or the stitched projection stack in Fiji.  Zoom into the **boundary
region** between the two tiles and move the slider until the seam is sharp and artifact-free.
The file name in Fiji's title bar gives the index to enter (pressing Enter accepts the nominal).

Record the final shift list (e.g. ``[0, 5430, 5419]``) for the next step.

Key parameters:

.. list-table::
   :widths: 30 70
   :header-rows: 0

   * - ``--rotation-axis``
     - Rotation axis found in Step 5.
   * - ``--shift-search-width``
     - Half-width of the shift search in pixels (default 20).
   * - ``--shift-search-step``
     - Step size between shift trials in pixels (default 1).
   * - ``--flat-linear True``
     - As in Step 5.
   * - ``--x-shifts``
     - Provide pre-computed shifts to skip the interactive search (e.g. from a previous run).


----

Step 7 — Horizontal stitch (``tile stitch``)
=============================================

``tile stitch`` merges all tiles for each y-row into a single HDF5 file (``tile.h5``) using
the confirmed x-shifts.  The output file has flat/dark correction already applied
(``data_white=1``, ``data_dark=0``) so that subsequent steps (vstitch, double-fov,
reconstruction) do not need to repeat it.

For a **single-row** mosaic::

    (tile) tomo@tomo4 $ tile stitch --folder-name /data/mosaic/ \
        --x-shifts "[0, 2450, 2450, 2452, 2454]" \
        --rotation-axis 1246 --flat-linear True

For a **multi-row** mosaic, run ``tile stitch`` once per y-row::

    for k in 0 1 2 3; do
        tile stitch --folder-name /data/bin2x2/y$k/ \
            --x-shifts "[0, 2752, 2752]" \
            --rotation-axis 324 --flat-linear True \
            --flats-file /data/bin2x2/flats.h5 --zinger-level 0.08
    done

Each run writes ``<folder-name>/tile/tile.h5``.

Key parameters:

.. list-table::
   :widths: 30 70
   :header-rows: 0

   * - ``--x-shifts``
     - Cumulative pixel shifts from Step 6, e.g. ``"[0, 5430, 5419]"``.  Required.
   * - ``--rotation-axis``
     - Rotation axis from Step 5 (used when ``--recon True``).
   * - ``--flat-linear True``
     - Linear flat-field interpolation per projection.
   * - ``--flats-file PATH``
     - Per-projection NNLS flat correction (from ``tile dump-flats``).
   * - ``--zinger-level``
     - Zinger removal threshold as fraction above local temporal median (0 = disabled,
       0.08 = 8%).  A value of 0 disables zinger removal.
   * - ``--nproj-per-chunk``
     - Projections processed per chunk (increase for faster I/O, at the cost of memory).
   * - ``--max-workers``
     - Number of parallel threads for chunk processing.
   * - ``--start-proj / --end-proj``
     - Process only a subset of projections (useful for splitting a large job).
   * - ``--recon True/False``
     - Whether to also run a quick reconstruction after stitching (default True).


----

Step 8 — Vertical stitch (``tile vstitch``) — *multi-row only*
===============================================================

For a mosaic with multiple y-rows, ``tile vstitch`` stacks the per-row ``tile.h5`` files
vertically into a single ``vstitch.h5``.  It uses quintic blending in the overlap region and
applies per-projection intensity scale calibration between adjacent rows to smooth brightness
differences.

Determine the y-shifts between rows (in pixels) by inspecting a single projection from each
row's ``tile.h5`` and measuring the vertical overlap::

    (tile) tomo@tomo4 $ tile vstitch \
        --folder-name /data/bin2x2/ \
        --y-folders y0,y1,y2,y3 \
        --y-shifts "[0, 450, 450, 450]" \
        --vstitch-output vstitch.h5

Alternatively, pass an explicit glob pattern::

    (tile) tomo@tomo4 $ tile vstitch \
        --folder-name /data/bin2x2/ \
        --vstitch-pattern "/data/bin2x2/y*/tile/tile.h5" \
        --y-shifts "[0, 450, 450, 450]"

Output: ``<folder-name>/vstitch.h5`` (or as set by ``--vstitch-output``).

Key parameters:

.. list-table::
   :widths: 30 70
   :header-rows: 0

   * - ``--y-shifts``
     - Cumulative y-shifts between rows in pixels, e.g. ``"[0, 450, 450, 450]"``.  Required.
   * - ``--y-folders``
     - Comma-separated subfolder names (e.g. ``y0,y1,y2,y3``).
   * - ``--vstitch-pattern``
     - Explicit glob pattern overriding ``--y-folders`` (e.g. ``y*/tile/tile.h5``).
   * - ``--vstitch-output``
     - Output filename relative to ``--folder-name`` (default ``vstitch.h5``).
   * - ``--nproj-per-chunk``
     - Projections processed per chunk.
   * - ``--max-workers``
     - Number of parallel threads.


----

Step 9 — 360° to 180° conversion (``tile double-fov``) — *360° scans only*
===========================================================================

For 360° acquisitions, ``tile double-fov`` converts the dataset to an effective 180° scan
by stitching projection ``i`` with ``fliplr(projection[i + N/2])``.  The rotation axis position
controls the amount of overlap/shift between the two halves.

The output is a half-sized projection stack (N/2 projections × full stitched width) ready
for standard 180° reconstruction::

    (tile) tomo@tomo4 $ tile double-fov \
        --folder-name /data/bin2x2/ \
        --double-fov-input vstitch.h5 \
        --double-fov-output double_fov.h5 \
        --rotation-axis 1627

Key parameters:

.. list-table::
   :widths: 30 70
   :header-rows: 0

   * - ``--rotation-axis``
     - Rotation axis position in the input file (pixels from left edge).  Required.
   * - ``--double-fov-input``
     - Input HDF5 file (relative to ``--folder-name`` or absolute, default ``vstitch.h5``).
   * - ``--double-fov-output``
     - Output HDF5 file (default ``double_fov.h5``).
   * - ``--nproj-per-chunk``
     - Projections processed per chunk.
   * - ``--max-workers``
     - Number of parallel threads.


----

Step 10 — Reconstruction
=========================

Once the final stitched file is ready, reconstruct with
`tomocupy <https://tomocupy.readthedocs.io/en/latest/>`_ or
`tomopy <https://tomopy.readthedocs.io/en/latest/>`_/`tomopycli <https://tomopycli.readthedocs.io/en/latest/>`_.

**Single-row mosaic** (``tile/tile.h5``, 180° scan)::

    (tomocupy) tomo@tomo4 $ tomocupy recon \
        --file-name /data/mosaic/tile/tile.h5 \
        --rotation-axis 1246 \
        --reconstruction-type full \
        --file-type standard \
        --binning 0 --nsino-per-chunk 8 \
        --rotation-axis-auto manual

**Multi-row 360° mosaic** (``double_fov.h5``, already converted to 180°)::

    (tomocupy) tomo@tomo4 $ tomocupy recon \
        --file-name /data/bin2x2/double_fov.h5 \
        --rotation-axis 1627 \
        --reconstruction-type full \
        --file-type standard \
        --binning 0 --nsino-per-chunk 8 \
        --rotation-axis-auto manual

.. note::

   After ``tile double-fov`` the file is already a 180° dataset, so pass
   ``--file-type standard``.  Use ``--file-type double_fov`` only if you are passing the
   raw stitched ``tile.h5`` directly to tomocupy without the explicit double-fov conversion.

For all options::

    (tile) tomo@tomo4 $ tile -h
    (tile) tomo@tomo4 $ tile stitch -h
    (tile) tomo@tomo4 $ tile vstitch -h
    (tile) tomo@tomo4 $ tile double-fov -h


----

Complete workflow example — 4×3 mosaic, 360° scan
==================================================

This example follows the processing of a 4-row × 3-column coffee bean mosaic collected at
2-BM in March 2026.  Each row lives in a separate subfolder ``y0``–``y3`` under the data
directory and the scan is a 360° acquisition.

::

    DATA=/data/raw                  # raw files in DATA/y0/, DATA/y1/, DATA/y2/, DATA/y3/
    BIN=/data/bin2x2                # working directory (2×2 binned, every 2nd projection)

    # 1. Verify the dataset (use any y-row)
    tile show --folder-name $DATA/y0/

    # 2. Bin all rows
    for k in 0 1 2 3; do
        tile bin --folder-name $DATA/y$k/ --binning 1 --bin-step 2
    done

    # 3. Collect flat field basis
    tile dump-flats --folder-name $BIN --y-folders y0,y1,y2,y3 \
        --dump-flats-output flats.h5

    # 4. Quick panoramic (top row only)
    tile panoramic --folder-name $BIN/y0/ --flat-linear True

    # 5. Find rotation center (coarse)
    tile center --folder-name $BIN/y0/ --recon-engine tomocupy \
        --rotation-axis 400 --center-search-width 200 --center-search-step 10 \
        --file-type double_fov --binning 0 --nsino-per-chunk 2 --flat-linear True
    # → open $BIN/y0/tile_rec/try_center/tmp/recon* in Fiji, pick best frame → e.g. 324

    # 5b. Fine search
    tile center --folder-name $BIN/y0/ --recon-engine tomocupy \
        --rotation-axis 324 --center-search-width 10 --center-search-step 1 \
        --file-type double_fov --binning 0 --nsino-per-chunk 2 --flat-linear True
    # → confirmed rotation axis = 324

    # 6. Find tile shifts
    tile shift --folder-name $BIN/y0/ --rotation-axis 324 --flat-linear True \
        --shift-search-width 60 --shift-search-step 1
    # → confirmed x-shifts = [0, 2752, 2752]

    # 7. Stitch all rows
    for k in 0 1 2 3; do
        tile stitch --folder-name $BIN/y$k/ \
            --x-shifts "[0, 2752, 2752]" \
            --rotation-axis 324 --flat-linear True \
            --flats-file $BIN/flats.h5 --zinger-level 0.08
    done
    # → $BIN/y*/tile/tile.h5

    # 8. Vertical stitch
    tile vstitch --folder-name $BIN \
        --y-folders y0,y1,y2,y3 \
        --y-shifts "[0, 450, 450, 450]" \
        --vstitch-output vstitch.h5
    # → $BIN/vstitch.h5

    # 9. 360° → 180° conversion
    tile double-fov --folder-name $BIN \
        --double-fov-input vstitch.h5 \
        --double-fov-output double_fov.h5 \
        --rotation-axis 1627
    # → $BIN/double_fov.h5

    # 10. Reconstruct
    tomocupy recon \
        --file-name $BIN/double_fov.h5 \
        --rotation-axis 1627 \
        --reconstruction-type full \
        --file-type standard \
        --binning 0 --nsino-per-chunk 8 \
        --rotation-axis-auto manual
