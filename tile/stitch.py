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

def write_meta(file_name, fid):

        try:  # trying to copy meta
            import meta

            mp = meta.read_meta.Hdf5MetadataReader(file_name)
            meta_dict = mp.readMetadata()
            mp.close()
            with h5py.File(file_name, 'r') as f:
                print(f"  *** copy meta data from {file_name}")#
                for key, value in meta_dict.items():
                    print(key, value)
                    if key.find('exchange') != 1:
                        dset = fid.create_dataset(
                            key, data=value[0], dtype=f[key].dtype, shape=(1,))
                        if value[1] is not None:
                            s = value[1]
                            utf8_type = h5py.string_dtype('utf-8', len(s)+1)
                            dset.attrs['units'] = np.array(
                                s.encode("utf-8"), dtype=utf8_type)
        except:
            log.error('write_meta() error: Skip copying meta')
            pass

def stitching(args):
    """Stitching projection tiles in horizontal direction"""

    log.info('Run stitching')
    # read files grid and retrieve data sizes
    meta_dict, grid, data_shape, data_type, _, _ = fileio.tile(args)
    data_type='float32'
    # check if flip is needed for having tile[0,0] as the left one and at sample_x=0
    sample_x = args.sample_x
    if args.reverse_step=='True':
        step = -1
    else:
        step = 1

    x_shifts = np.fromstring(args.x_shifts[1:-1], sep=',', dtype='int')
    log.info(f'Relative shifts {x_shifts}')
    if args.end_proj == -1:
        args.end_proj = data_shape[0]

    # total size in x direction, multiple of 4 for faster ffts in reconstruction
    size = int(np.ceil(
        (data_shape[2]+np.sum(np.sum(x_shifts)))/16)*16)

    tile_path = os.path.join(args.folder_name, 'tile')
    if not os.path.exists(tile_path):
        os.makedirs(tile_path)
    tile_file_name = os.path.join(tile_path, args.tile_file_name)
    theta = np.zeros(1,dtype='float32')
    for itile in range(grid.shape[1]):
        with h5py.File(grid[0, itile], 'r') as fid:
            if(len(fid['/exchange/theta'][:])>len(theta)):
                theta = fid['/exchange/theta'][:]

    os.system(f'rm -rf {tile_file_name}')
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
        write_meta(grid[0, itile],fid)

        for itile in range(grid.shape[1]):
                
            if args.reverse_grid=='True':
                iitile=grid.shape[1]-itile-1
            else: 
                iitile=itile
            with h5py.File(grid[0, ::-step][iitile],'r') as fidin:
                flat = fidin['/exchange/data_white'][:]
                dark = fidin['/exchange/data_dark'][:]
                
                st = np.sum(x_shifts[:itile+1])
                end = min(st+data_shape[2], size)
                vv = np.ones(data_shape[2])
                if itile<grid.shape[1]-1:
                    v = np.linspace(1, 0, data_shape[2]-x_shifts[itile+1], endpoint=False)
                    v = v**5*(126-420*v+540*v**2-315*v**3+70*v**4)                    
                    vv[x_shifts[itile+1]:]=v
                if itile>0:
                    v = np.linspace(1, 0, data_shape[2]-x_shifts[itile], endpoint=False)
                    v = v**5*(126-420*v+540*v**2-315*v**3+70*v**4)                    
                    vv[:data_shape[2]-x_shifts[itile]]=1-v
                dark_all[0,:, st:end] += np.mean(dark[:, :, ::step],axis=0)*vv[:end-st]
                flat_all[0,:, st:end] += np.mean(flat[:, :, ::step],axis=0)*vv[:end-st]
            if itile==grid.shape[1]-1:
                dark_all[0,:,end:]=dark_all[0,:,end-1:end]
                flat_all[0,:,end:]=flat_all[0,:,end-1:end]

        for ichunk in range(int(np.ceil((args.end_proj-args.start_proj)/args.nproj_per_chunk))):
            # processing by chunks in angles
            st_chunk = args.start_proj+ichunk*args.nproj_per_chunk
            end_chunk = min(st_chunk+args.nproj_per_chunk, args.end_proj)

            log.info(f'Stitching projections {st_chunk} - {end_chunk}')
            for itile in range(grid.shape[1]):
                
                if args.reverse_grid=='True':
                    iitile=grid.shape[1]-itile-1
                else: 
                    iitile=itile
                with h5py.File(grid[0, ::-step][iitile],'r') as fidin:
                    uids = fidin['/defaults/NDArrayUniqueId'][:]
                    hdf_location = fidin['/defaults/HDF5FrameLocation']                        
                    proj_ids = uids[hdf_location[:] == b'/exchange/data']-1
                    proj_ids = proj_ids[(proj_ids>=st_chunk)*(proj_ids<end_chunk)]
                    if len(proj_ids)!=end_chunk-st_chunk:
                        log.warning('There are missing projection in the current tile, setting them to 0')
                    data = fidin['/exchange/data'][proj_ids]
                    
                    st = np.sum(x_shifts[:itile+1])
                    end = min(st+data_shape[2], size)
                    vv = np.ones(data_shape[2])
                    if itile<grid.shape[1]-1:
                        v = np.linspace(1, 0, data_shape[2]-x_shifts[itile+1], endpoint=False)
                        v = v**5*(126-420*v+540*v**2-315*v**3+70*v**4)                    
                        vv[x_shifts[itile+1]:]=v
                    if itile>0:
                        v = np.linspace(1, 0, data_shape[2]-x_shifts[itile], endpoint=False)
                        v = v**5*(126-420*v+540*v**2-315*v**3+70*v**4)                    
                        vv[:data_shape[2]-x_shifts[itile]]=1-v
                    data_all[proj_ids-args.start_proj, :, st:end] += data[:, :, ::step]*vv[:end-st]
                if itile==grid.shape[1]-1:
                    data_all[proj_ids-args.start_proj,:,end:]=np.tile(data_all[proj_ids-args.start_proj,:,end-1:end],(1,1,size-end))
            
    log.info(f'Output file {tile_file_name}')
    log.info(f'Reconstruct {tile_file_name} with tomocupy:')
    log.info(f'tomocupy recon --file-name {tile_file_name} --rotation-axis <found rotation axis> --reconstruction-type full --file-type double_fov --remove-stripe-method fw --binning <select binning> --nsino-per-chunk 2 ')
    log.info(f'Reconstruct {tile_file_name} with tomopy:')
    log.info(f'tomopy recon --file-name {tile_file_name} --rotation-axis <found rotation axis> --reconstruction-type full --file-type double_fov --remove-stripe-method fw --binning <select binning> --nsino-per-chunk 8 --rotation-axis-auto manual')
