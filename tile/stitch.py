# #########################################################################
# Copyright (c) 2022, UChicago Argonne, LLC. All rights reserved.         #
#                                                                         #
# Copyright 2022. UChicago Argonne, LLC. This software was produced       #
# under U.S. Government contract DE-AC02-06CH11357 for Argonne National   #
# Laboratory (ANL), which is operated by UChicago Argonne, LLC for the    #
# U.S. Department of Energy. The U.S. Government has rights to use,       #
# reproduce, and distribute this software.  NEITHER THE GOVERNMENT NOR    #
# UChicago Argonne, LLC MAKES ANY WARRANTY, EXPRESS OR IMPLIED, OR        #
# ASSUMES ANY LIABILITY FOR THE USE OF THIS SOFTWARE.  If software is     #
# modified to produce derivative works, such modified software should     #
# be clearly marked, so as not to confuse it with the version available   #
# from ANL.                                                               #
#                                                                         #
# Additionally, redistribution and use in source and binary forms, with   #
# or without modification, are permitted provided that the following      #
# conditions are met:                                                     #
#                                                                         #
#     * Redistributions of source code must retain the above copyright    #
#       notice, this list of conditions and the following disclaimer.     #
#                                                                         #
#     * Redistributions in binary form must reproduce the above copyright #
#       notice, this list of conditions and the following disclaimer in   #
#       the documentation and/or other materials provided with the        #
#       distribution.                                                     #
#                                                                         #
#     * Neither the name of UChicago Argonne, LLC, Argonne National       #
#       Laboratory, ANL, the U.S. Government, nor the names of its        #
#       contributors may be used to endorse or promote products derived   #
#       from this software without specific prior written permission.     #
#                                                                         #
# THIS SOFTWARE IS PROVIDED BY UChicago Argonne, LLC AND CONTRIBUTORS     #
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT       #
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS       #
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL UChicago     #
# Argonne, LLC OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,        #
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,    #
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;        #
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER        #
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT      #
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN       #
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE         #
# POSSIBILITY OF SUCH DAMAGE.                                             #
# #########################################################################

import os
import h5py
import dxchange
import numpy as np

from tile import log
from tile import fileio

__all__ = ['stitching']

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
    tile_file_name = os.path.join(tile_path, args.tile_file_name)
    with h5py.File(grid[0, 0], 'r') as fid:
        theta = fid['/exchange/theta'][:]

    with h5py.File(tile_file_name, 'w') as fid:
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

    log.info(f'Output file {tile_file_name}')
    log.info(f'Reconstruct {tile_file_name} with tomocupy:')
    log.info(f'tomocupy recon --file-name /data/2021-12/Duchkov/mosaic/tile/tile.h5 --rotation-axis 1246 --reconstruction-type full --file-type double_fov --remove-stripe-method fw --binning 0 --nsino-per-chunk 8 --rotation-axis-auto manual')
    log.info(f'Reconstruct {tile_file_name} with tomopy:')
    log.info(f'tomopy recon --file-name /data/2021-12/Duchkov/mosaic/tile/tile.h5 --rotation-axis 1246 --reconstruction-type full --file-type double_fov --remove-stripe-method fw --binning 0 --nsino-per-chunk 8 --rotation-axis-auto manual')
