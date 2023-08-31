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
from threading import Thread
__all__ = ['stitching']

def read_proj_chunk(out, inp, st, st_proj, end_proj):    
        """Read a chunk of projections """                        
        out[st_proj:end_proj] = inp[st+st_proj:st+end_proj]
        
def read_data_parallel(inp,st=0,end=-1,nthreads=8):
        """Reading data in parallel"""
        # parallel read of projections
        if end==-1:
            end=inp.shape[0]
        data = np.empty([end-st,*inp.shape[1:]], dtype='float32')
        lchunk = int(np.ceil((end-st)/nthreads))
        procs = []
        for k in range(nthreads):
            st_proj = k*lchunk
            end_proj = min((k+1)*lchunk,end-st)
            if st_proj>=end_proj:
                continue
            read_thread = Thread(
                target=read_proj_chunk, args=(data, inp, st,st_proj, end_proj))
            procs.append(read_thread)
            read_thread.start()
        for proc in procs:
            proc.join()
        return data
    

def stitching(args):
    """Stitching projection tiles in horizontal direction"""

    log.info('Run stitching')
    # read files grid and retrieve data sizes
    meta_dict, grid, data_shape, data_type, _, _ = fileio.tile(args)
    if args.reverse_step=='True':#reverse compared to shift (to do)
        step = -1
    else:
        step = 1

    

    x_shifts = np.fromstring(args.x_shifts[1:-1], sep=',', dtype='int')
    print(x_shifts)
    size = int(np.ceil(
        (data_shape[2]+np.sum(np.sum(x_shifts)))/16)*16)
    x_shifts=data_shape[-1]-x_shifts
    x_shifts[0]=0
    
    log.info(f'Relative shifts {x_shifts}')
    cx_shifts = np.cumsum(x_shifts)
    log.info(f'Cumulative shifts {cx_shifts}')
    if args.end_proj == -1:
        args.end_proj = data_shape[0]

    # total size in x direction, multiple of 4 for faster ffts in reconstruction
    
    tile_path = os.path.join(args.folder_name, 'tile')
    if not os.path.exists(tile_path):
        os.makedirs(tile_path)
    tile_file_name = os.path.join(tile_path, args.tile_file_name)
    theta = np.linspace(0,360,-args.start_proj+args.end_proj).astype('float32')
    os.system(f'rm -rf {tile_file_name}')
    
    dark0 = np.empty([grid.shape[1],1,*data_shape[1:]],dtype='float32') 
    flat0 = np.empty([grid.shape[1],1,*data_shape[1:]],dtype='float32') 
    
    
    log.info(f'reading flat and dark')
    
    for itile in range(grid.shape[1]):
        log.info(f'{itile=}')
        if args.reverse_grid=='True':# filling from another side
            iitile=grid.shape[1]-itile-1
        else: 
            iitile=itile
        with h5py.File(grid[0, ::-step][iitile],'r') as fidin:#filling from another side
            flat_pre = read_data_parallel(fidin['/exchange/data_white_pre'],0,-1)
            flat_post = read_data_parallel(fidin['/exchange/data_white_post'],0,-1)
            dark = read_data_parallel(fidin['/exchange/data_dark'],0,-1)
            flat = (flat_pre.astype('float32')+flat_post.astype('float32'))*0.5
            dark0[itile] = np.mean(dark[:, :, ::step], axis=0)
            flat0[itile] = np.mean(flat[:, :, ::step], axis=0)
    flatmdark0=(1e-3+flat0-dark0)              
    
    
    log.info(f'stitiching projections')
    with h5py.File(tile_file_name, 'w') as fid:
        # init output arrays
        data_all = fid.create_dataset('/exchange/data', (args.end_proj-args.start_proj,
                                      data_shape[1], size), dtype='float32', chunks=(1, data_shape[1], size))
        flat_all = fid.create_dataset(
            '/exchange/data_white', (1, data_shape[1], size), dtype='float32', chunks=(1, data_shape[1], size))
        dark_all = fid.create_dataset(
            '/exchange/data_dark', (1, data_shape[1], size), dtype='float32', chunks=(1, data_shape[1], size))
        flat_all[:]=1
        dark_all[:]=0
        theta = fid.create_dataset(
            '/exchange/theta', data=theta[args.start_proj:args.end_proj])

        for ichunk in range(int(np.ceil((args.end_proj-args.start_proj)/args.nproj_per_chunk))):
            # processing by chunks in angles
            st_chunk = args.start_proj+ichunk*args.nproj_per_chunk
            end_chunk = min(st_chunk+args.nproj_per_chunk, args.end_proj)

            log.info(f'Stitching projections {st_chunk} - {end_chunk}')
            for itile in range(grid.shape[1]):
                log.info(f'{itile=}')
                if args.reverse_grid=='True':# filling from another side
                    iitile=grid.shape[1]-itile-1
                else: 
                    iitile=itile
                    log.warning(f'{step=}')
                with h5py.File(grid[0, ::step][iitile],'r') as fidin:#filling from another side
                    data = read_data_parallel(fidin['/exchange/data'],st_chunk,end_chunk)
                    
                    # st = np.sum(x_shifts[:itile+1])
                    # end = min(st+data_shape[2], size)
                    data0 = data[:, :, ::step]
                    data0 = (data0-dark0[itile])/flatmdark0[itile]
                    
                    # define index in x for proj (filling from the left side)
                    st_x0 = int(np.round((iitile)*data_shape[2]-cx_shifts[iitile]))
                    end_x0 = st_x0+data_shape[2]            
                    
                    # crop to the data_all size 
                    st_x = max(st_x0,0)
                    end_x = min(end_x0,data_all.shape[2])
                                        
                    # define index in x for data
                    st_x0 = st_x-st_x0
                    end_x0 = data.shape[2]+end_x-end_x0
                    
                    vx = np.ones([end_x0-st_x0],dtype='float32')
                                        
                    v = np.linspace(0, 1, int(x_shifts[iitile]), endpoint=False)
                    
                    # if ix>0:
                    vxleft = v**5*(126-420*v+540*v**2-315*v**3+70*v**4)
                    vx[:len(vxleft)] = vxleft
                    # print(vx)
                    if iitile+1<grid.shape[1]:
                        v = np.linspace(1, 0, int(x_shifts[iitile+1]), endpoint=False)
                        vxright = v**5*(126-420*v+540*v**2-315*v**3+70*v**4)                    
                        vx[-len(vxright):] = vxright                                        
                    v = np.tile(vx,(data_all.shape[1],1))
                    
                    # fill array part
                    tmp = data0[:,:,st_x0:end_x0]*v
                    log.info(f"{st_x=},{st_x0=},{end_x=},{end_x0=}")                                        
                    data_all[st_chunk:end_chunk,:,st_x:end_x] += tmp
            
            if args.test=='True':
                exit()
                    
                    
                    
                    

    log.info(f'Output file {tile_file_name}')
    log.info(f'Reconstruct {tile_file_name} with tomocupy:')
    log.info(f'tomocupy recon --file-name {tile_file_name} --rotation-axis <found rotation axis> --reconstruction-type full --remove-stripe-method vo-all --binning <select binning> --nsino-per-chunk 2 ')
