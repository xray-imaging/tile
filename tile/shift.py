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
import dxchange
import dxfile.dxtomo as dx
import numpy as np

from tile import log
from tile import fileio

__all__ = ['shift_manual']


def center(args):
    """Find rotation axis location"""

    log.info('Run find rotation axis location')
    # read files grid and retrieve data sizes
    meta_dict, grid, data_shape, data_type, x_shift, y_shift = fileio.tile(args)

    log.info('image   size (x, y) in pixels: (%d, %d)' % (data_shape[2], data_shape[1]))
    log.info('stitch shift (x, y) in pixels: (%d, %d)' % (x_shift, y_shift))
    log.warning('tile overlap (x, y) in pixels: (%d, %d)' % (data_shape[2]-x_shift, data_shape[1]-y_shift))

    # check if flip is needed for having tile[0,0] as the left one and at sample_x=0
    sample_x = args.sample_x
    x0 = meta_dict[grid[0,0]][sample_x][0]
    x1 = meta_dict[grid[0,-1]][sample_x][0]
    if(x0+x1>0):
        step = -1
    else:
        step = 1
    if args.rotation_axis==-1:
        args.rotation_axis = data_shape[2]//2
        
    # ids for slice and projection for shifts testing
    idslice = int((data_shape[1]-1)*args.nsino)
    idproj = int((data_shape[0]-1)*args.nprojection)

    # data size after stitching
    size = int(np.ceil((data_shape[2]+(grid.shape[1]-1)*x_shift)/2**(args.binning+4))*2**(args.binning+4))
    data_all = np.ones([data_shape[0],2**args.binning,size],dtype=data_type)
    dark_all = np.zeros([1,2**args.binning,size],dtype=data_type)
    flat_all = np.ones([1,2**args.binning,size],dtype=data_type)

    tmp_file_name = f'{args.folder_name}{args.tmp_file_name}'
    dirPath = os.path.dirname(tmp_file_name)
    if not os.path.exists(dirPath):
        os.makedirs(dirPath)

    # Center search with using the first tile
    for itile in range(grid.shape[1]):
        data,flat,dark,theta = dxchange.read_aps_tomoscan_hdf5(grid[0,::-step][itile],sino=(idslice,idslice+2**args.binning))       
        st = itile*x_shift
        end = st+data_shape[2]
        data_all[:,:,st:end] = data[:,:,::step]
        dark_all[:,:,st:end] = np.mean(dark[:,:,::step],axis=0)
        flat_all[:,:,st:end] = np.mean(flat[:,:,::step],axis=0)
        f = dx.File(tmp_file_name, mode='w') 
        f.add_entry(dx.Entry.data(data={'value': data_all, 'units':'counts'}))
        f.add_entry(dx.Entry.data(data_white={'value': flat_all, 'units':'counts'}))
        f.add_entry(dx.Entry.data(data_dark={'value': dark_all, 'units':'counts'}))
        f.add_entry(dx.Entry.data(theta={'value': theta*180/np.pi, 'units':'degrees'}))
        f.close()
    log.info(f'Created a temporary hdf file: {tmp_file_name}')
    log.warning(f'Running: {args.recon_engine} recon --file-type double_fov --binning {args.binning} --reconstruction-type try --file-name {tmp_file_name} --center-search-width {args.center_search_width} --rotation-axis-auto manual --rotation-axis {args.rotation_axis} --center-search-step {args.center_search_step}')
    os.system(f'{args.recon_engine} recon --file-type double_fov --binning {args.binning} --reconstruction-type try --file-name {tmp_file_name} --remove-stripe-method fw \
            --center-search-width {args.center_search_width} --rotation-axis-auto manual --rotation-axis {args.rotation_axis} \
            --center-search-step {args.center_search_step} --remove-stripe-method fw')            
    
    try_path = f"{os.path.dirname(tmp_file_name)}_rec/try_center/tmp/recon*"
    log.info(f'Please open the stack of images from {try_path} and select the rotation center')


def shift_manual(args):
    """Find shifts between horizontal tiles"""

    log.info('Run manual shift')
    # read files grid and retrieve data sizes
    meta_dict, grid, data_shape, data_type, x_shift, y_shift = fileio.tile(args)

    log.info('image   size (x, y) in pixels: (%d, %d)' % (data_shape[2], data_shape[1]))
    log.info('stitch shift (x, y) in pixels: (%d, %d)' % (x_shift, y_shift))
    log.warning('tile overlap (x, y) in pixels: (%d, %d)' % (data_shape[2]-x_shift, data_shape[1]-y_shift))

    # check if flip is needed for having tile[0,0] as the left one and at sample_x=0
    sample_x = args.sample_x
    x0 = meta_dict[grid[0,0]][sample_x][0]
    x1 = meta_dict[grid[0,-1]][sample_x][0]
    if(x0+x1>0):
        step = -1
    else:
        step = 1
    
    # if args.rotation_axis==-1:
    #     args.rotation_axis = data_shape[2]//2
    
    
    # ids for slice and projection for shifts testing
    idslice = int((data_shape[1]-1)*args.nsino)
    idproj = int((data_shape[0]-1)*args.nprojection)
    print(args.binning)

    # data size after stitching
    size = int(np.ceil((data_shape[2]+(grid.shape[1]-1)*x_shift)/2**(args.binning+1))*2**(args.binning+1))
    data_all = np.ones([data_shape[0],2**args.binning,size],dtype=data_type)
    dark_all = np.zeros([1,2**args.binning,size],dtype=data_type)
    flat_all = np.ones([1,2**args.binning,size],dtype=data_type)

    tmp_file_name = f'{args.folder_name}/tile/tmp.h5'
    dirPath = os.path.dirname(tmp_file_name)
    if not os.path.exists(dirPath):
        os.makedirs(dirPath)
    center = input(f"Please enter rotation center ({args.rotation_axis}): ")
    if center is not None:        
        args.rotation_axis = center
    # find shift error
    arr_err = range(-args.shift_search_width,args.shift_search_width,args.shift_search_step)
    data_all = np.ones([data_shape[0],2**args.binning*len(arr_err),size],dtype=data_type)
    dark_all = np.zeros([1,2**args.binning*len(arr_err),size],dtype=data_type)
    flat_all = np.ones([1,2**args.binning*len(arr_err),size],dtype=data_type)    
    
    pdata_all = np.ones([len(arr_err),data_shape[1],size],dtype='float32')
    print(data_all.shape)
    x_shifts_res = np.zeros(grid.shape[1],'int')
    x_shifts_res[1:] = x_shift
    for jtile in range(1,grid.shape[1]):      
        print(jtile)  
        data_all[:]  = 1
        flat_all[:]  = 1
        dark_all[:]  = 0
        pdata_all[:] = 1
        
        for ishift,err_shift in enumerate(arr_err):
            print(ishift)                
            x_shifts = x_shifts_res.copy()
            x_shifts[jtile] += err_shift
            for itile in range(grid.shape[1]):
                data,flat,dark,theta = dxchange.read_aps_tomoscan_hdf5(grid[0,::-step][itile],sino=(idslice,idslice+2**args.binning))       
                st = np.sum(x_shifts[:itile+1])
                end = min(st+data_shape[2],size)
                sts = ishift*2**args.binning
                ends = sts+2**args.binning
                data_all[:,sts:ends,st:end] = data[:,:,::step][:,:,:end-st]
                dark_all[:,sts:ends,st:end] = np.mean(dark[:,:,::step],axis=0)[:,:end-st]
                flat_all[:,sts:ends,st:end] = np.mean(flat[:,:,::step],axis=0)[:,:end-st]
                data,flat,dark,theta = dxchange.read_aps_tomoscan_hdf5(grid[0,::-step][itile],proj=(idproj,idproj+1))       
                data = (data-np.mean(dark,axis=0))/np.maximum(1e-3,(np.mean(flat,axis=0)-np.mean(dark,axis=0)))
                pdata_all[ishift,:,st:end] = data[:,:,::step][:,:,:end-st]
        # create a temporarily DataExchange file
        dir = os.path.dirname(tmp_file_name)
        basename = os.path.basename(tmp_file_name)
        if not os.path.exists(dirPath):
            os.makedirs(dirPath)
        dxchange.write_tiff_stack(pdata_all,f'{dir}_rec/{basename[:-3]}_proj/p',overwrite=True)        
        f = dx.File(tmp_file_name, mode='w') 
        f.add_entry(dx.Entry.data(data={'value': data_all, 'units':'counts'}))
        f.add_entry(dx.Entry.data(data_white={'value': flat_all, 'units':'counts'}))
        f.add_entry(dx.Entry.data(data_dark={'value': dark_all, 'units':'counts'}))
        f.add_entry(dx.Entry.data(theta={'value': theta*180/np.pi, 'units':'degrees'}))
        f.close()        

        os.system(f'{args.recon_engine} recon --file-type double_fov --binning {args.binning} --reconstruction-type full \
            --file-name {tmp_file_name} --rotation-axis-auto manual --rotation-axis {args.rotation_axis} --nsino-per-chunk {args.nsino_per_chunk}')            
        
        try_path = f"{os.path.dirname(tmp_file_name)}_rec/tmp_rec/recon*"
        tryproj_path = f"{dir}_rec/{basename[:-3]}_proj/p*"
        print(f'Please open the stack of images from reconstructions {try_path} or stitched projections {tryproj_path}, and select the file id to shift tile {jtile}')
        sh = int(input(f"Please enter id for tile {jtile}: "))
        
        x_shifts_res[jtile]+=arr_err[sh]
        log.info(f'Current shifts: {x_shifts_res}')
        

    log.info(f'Center {args.rotation_axis}')
    log.info(f'Relative shifts {x_shifts_res.tolist()}')
        
            