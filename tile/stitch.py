from tile import log
from tile import fileio
import numpy as np
import h5py
import dxchange
import os


def stitching(args):
    """Stitching projection tiles in horizontal direction"""

    log.info('Run stitching')
    # read files grid and retrieve data sizes
    meta_dict, grid, data_shape, data_type, _, _ = fileio.tile(args)
    # check if flip is needed for having tile[0,0] as the left one and at sample_x=0
    sample_x = 'measurement_instrument_sample_motor_stack_setup_sample_x'
    x0 = meta_dict[grid[0, 0]][sample_x][0]
    x1 = meta_dict[grid[0, -1]][sample_x][0]
    if(x0+x1 > 0):
        step = -1
    else:
        step = 1

    x_shifts = np.fromstring(args.x_shifts[1:-1], sep=',', dtype='int')
    log.info(f'Relative shifts {x_shifts}')
    if args.end_proj == -1:
        args.end_proj = data_shape[0]

    # total size in x direction, multiple of 4 for faster ffts in reconstruction
    size = int(np.ceil(
        (data_shape[2]+np.sum(np.sum(x_shifts)))/4)*4)

    tile_path = os.path.join(args.folder_name, 'tile')
    if not os.path.exists(tile_path):
        os.makedirs(tile_path)
    tile_fname = os.path.join(tile_path, 'tile.h5')
    with h5py.File(grid[0, 0], 'r') as fid:
        theta = fid['/exchange/theta'][:]

    with h5py.File(tile_fname, 'w') as fid:
        # init output arrays
        data_all = fid.create_dataset('/exchange/data', (args.end_proj-args.start_proj,
                                      data_shape[1], size), dtype=data_type, chunks=(1, data_shape[1], size))
        flat_all = fid.create_dataset(
            '/exchange/data_white', (1, data_shape[1], size), dtype=data_type, chunks=(1, data_shape[1], size))
        dark_all = fid.create_dataset(
            '/exchange/data_dark', (1, data_shape[1], size), dtype=data_type, chunks=(1, data_shape[1], size))
        theta = fid.create_dataset(
            '/exchange/theta', data=theta[args.start_proj:args.end_proj])

        for ichunk in range(int(np.ceil((args.end_proj-args.start_proj)/args.nproj_per_chunk))):
            # processing by chunks in angles
            st_chunk = args.start_proj+ichunk*args.nproj_per_chunk
            end_chunk = min(st_chunk+args.nproj_per_chunk, args.end_proj)

            log.info(f'Stitching projections {st_chunk} - {end_chunk}')
            for itile in range(grid.shape[1]):
                data, flat, dark, _ = dxchange.read_aps_32id(
                    grid[0, ::-step][itile], proj=(st_chunk, end_chunk))
                st = np.sum(x_shifts[:itile+1])
                end = min(st+data_shape[2], size)
                data_all[st_chunk-args.start_proj:end_chunk -
                         args.start_proj, :, st:end] = data[:, :, ::step]
                dark_all[st_chunk-args.start_proj:end_chunk-args.start_proj,
                         :, st:end] = np.mean(dark[:, :, ::step], axis=0)
                flat_all[st_chunk-args.start_proj:end_chunk-args.start_proj,
                         :, st:end] = np.mean(flat[:, :, ::step], axis=0)

    log.info(f'Output file {args.stitch_fname}')
