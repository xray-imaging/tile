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

__all__ = ['shift_manual',
           'center',
          ]



def _next_smooth(n):
    """Return the smallest integer >= n whose prime factors are all in {2, 3, 5}."""
    candidate = n
    while True:
        m = candidate
        for p in (2, 3, 5):
            while m % p == 0:
                m //= p
        if m == 1:
            return candidate
        candidate += 1


def center(args):
    """Find rotation axis location"""

    log.info('Run find rotation axis location')
    # read files grid and retrieve data sizes
    meta_dict, grid, data_shape, data_type, x_shift, y_shift = fileio.tile(args)

    # force float32 for stitching
    data_type = 'float32'
    log.info('image   size (x, y) in pixels: (%d, %d)' % (data_shape[2], data_shape[1]))
    log.info('stitch shift (x, y) in pixels: (%d, %d)' % (x_shift, y_shift))
    log.info('tile overlap (x, y) in pixels: (%d, %d)' % (data_shape[2]-x_shift, data_shape[1]-y_shift))

    # check if flip is needed for having tile[0,0] as the left one and at sample_x=0
    sample_x = args.sample_x
    x0 = meta_dict[grid[0,0]][sample_x][0]
    x1 = meta_dict[grid[0,-1]][sample_x][0]
    if args.reverse_step=='True':
        step=-1
    else:
        step=1    
    if args.rotation_axis==-1:
        args.rotation_axis = data_shape[2]//2
        log.warning('Rotation in pixel: (%d)' % (args.rotation_axis))
    # ids for slice and projection for shifts testing
    idslice = int((data_shape[1]-1)*args.nsino)
    idproj = int((data_shape[0]-1)*args.nprojection)

    # resolve x_shifts: use provided list or fall back to uniform nominal x_shift
    if args.x_shifts != 'None':
        x_shifts = np.fromstring(args.x_shifts[1:-1], sep=',', dtype='int')
        log.info(f'Using provided x-shifts: {x_shifts}')
    else:
        x_shifts = np.zeros(grid.shape[1], dtype='int')
        x_shifts[1:] = x_shift
        log.info(f'Using nominal x-shifts: {x_shifts}')

    # data size after stitching, rounded up to a cuFFT-friendly number
    raw_size = data_shape[2] + int(np.sum(x_shifts))
    size = _next_smooth(raw_size)
    # load external flat field basis if provided
    use_flats_basis = bool(args.flats_file)
    if use_flats_basis:
        import h5py
        with h5py.File(args.flats_file, 'r') as fb:
            basis_flats = fb['/exchange/data_white'][:, idslice:idslice+2**args.binning, ::step].astype('float32')
        log.info(f'Loaded flat basis: {basis_flats.shape[0]} frames from {args.flats_file}')
        basis_profs = np.mean(basis_flats, axis=2).T.astype('float64')  # (binning, n_basis)

    # pre-compute per-tile flat/dark correction arrays
    tile_dark = []
    tile_flat_p0 = []
    tile_flat_p1 = []
    for itile in range(grid.shape[1]):
        if args.reverse_grid=='True':
            iitile=grid.shape[1]-itile-1
        else:
            iitile=itile
        _,flat,dark,_ = dxchange.read_aps_tomoscan_hdf5(grid[0,::-step][iitile],sino=(idslice,idslice+2**args.binning))
        n = flat.shape[0]
        tile_dark.append(np.mean(dark[:,:,::step], axis=0))
        tile_flat_p0.append(np.mean(flat[:n//2,:,::step], axis=0))
        tile_flat_p1.append(np.mean(flat[n//2:,:,::step], axis=0))

    data_all = np.ones([data_shape[0],2**args.binning,size],dtype=data_type)
    print(data_all.shape)
    flat_all = np.ones([1,2**args.binning,size],dtype=data_type)
    dark_all = np.zeros([1,2**args.binning,size],dtype=data_type)

    tmp_file_name = f'{args.folder_name}{args.tmp_file_name}'
    dirPath = os.path.dirname(tmp_file_name)
    if not os.path.exists(dirPath):
        os.makedirs(dirPath)

    for itile in range(grid.shape[1]):
        print(itile)
        if args.reverse_grid=='True':
            iitile=grid.shape[1]-itile-1
        else:
            iitile=itile
        data,_,_,theta = dxchange.read_aps_tomoscan_hdf5(grid[0,::-step][iitile],sino=(idslice,idslice+2**args.binning))
        st = int(np.sum(x_shifts[:itile+1]))
        end = st+data_shape[2]
        vv = np.ones(data_shape[2])
        if itile<grid.shape[1]-1:
            overlap_r = data_shape[2]-x_shifts[itile+1]
            v = np.linspace(1, 0, overlap_r, endpoint=False)
            v = v**5*(126-420*v+540*v**2-315*v**3+70*v**4)
            vv[x_shifts[itile+1]:]=v
        if itile>0:
            overlap_l = data_shape[2]-x_shifts[itile]
            v = np.linspace(1, 0, overlap_l, endpoint=False)
            v = v**5*(126-420*v+540*v**2-315*v**3+70*v**4)
            vv[:overlap_l]=1-v
        dark_mean = tile_dark[itile]
        data_f = data[:,:,::step].copy()
        if use_flats_basis:
            from scipy.optimize import nnls
            for i in range(data_f.shape[0]):
                proj_prof = np.mean(data_f[i], axis=1).astype('float64')
                w, _ = nnls(basis_profs, proj_prof)
                flat_i = np.einsum('k,khw->hw', w, basis_flats)
                data_f[i] = (data_f[i] - dark_mean) / np.maximum(flat_i - dark_mean, 1e-3)
        elif args.flat_linear == 'True':
            for i in range(data_f.shape[0]):
                t = i / max(data_shape[0]-1, 1)
                flat_i = (1-t)*tile_flat_p0[itile] + t*tile_flat_p1[itile]
                data_f[i] = (data_f[i] - dark_mean) / np.maximum(flat_i - dark_mean, 1e-3)
        else:
            flat_mean = (tile_flat_p0[itile] + tile_flat_p1[itile]) / 2
            data_f = (data_f - dark_mean) / np.maximum(flat_mean - dark_mean, 1e-3)
        np.nan_to_num(data_f, nan=1.0, posinf=1.0, neginf=1.0, copy=False)
        data_all[:data_f.shape[0],:,st:end] += data_f*vv
        data_all[data_f.shape[0]:,:,st:end] += data_f[-1]*vv
        f = dx.File(tmp_file_name, mode='w')
        f.add_entry(dx.Entry.data(data={'value': data_all, 'units':'counts'}))
        f.add_entry(dx.Entry.data(data_white={'value': flat_all, 'units':'counts'}))
        f.add_entry(dx.Entry.data(data_dark={'value': dark_all, 'units':'counts'}))
        f.add_entry(dx.Entry.data(theta={'value': theta*180/np.pi, 'units':'degrees'}))
        f.close()
    log.info(f'Created a temporary hdf file: {tmp_file_name}')
    cmd = f'{args.recon_engine} recon --file-type {args.file_type} --binning {args.binning} --reconstruction-type try --file-name {tmp_file_name} \
            --center-search-width {args.center_search_width} --rotation-axis-auto manual --rotation-axis {args.rotation_axis} \
            --center-search-step {args.center_search_step} --end-column {args.end_column} --nsino-per-chunk {args.nsino_per_chunk}'
    log.warning(cmd)
    os.system(cmd)      
    
    try_path = f"{os.path.dirname(tmp_file_name)}_rec/try_center/tmp/recon*"
    log.action(f'Please open the stack of images from {try_path} and select the rotation center')


def panoramic(args):
    """Stitch a single projection from all tiles and save as a tiff for quick inspection.
    Uses nominal overlap from hdf metadata by default, or --x-shifts if provided."""

    import tifffile

    log.info('Run panoramic stitching')
    meta_dict, grid, data_shape, data_type, x_shift, y_shift = fileio.tile(args)
    log.info('image   size (x, y) in pixels: (%d, %d)' % (data_shape[2], data_shape[1]))
    log.info('stitch shift (x, y) in pixels: (%d, %d)' % (x_shift, y_shift))
    log.info('tile overlap (x, y) in pixels: (%d, %d)' % (data_shape[2]-x_shift, data_shape[1]-y_shift))

    if args.reverse_step == 'True':
        step = -1
    else:
        step = 1

    # build x_shifts array: use provided --x-shifts or nominal overlap
    if args.x_shifts != 'None':
        x_shifts = np.fromstring(args.x_shifts[1:-1], sep=',', dtype='int')
        log.info(f'Using provided x-shifts: {x_shifts}')
    else:
        x_shifts = np.zeros(grid.shape[1], dtype='int')
        x_shifts[1:] = x_shift
        log.info(f'Using nominal x-shifts: {x_shifts}')

    size = int(data_shape[2] + np.sum(x_shifts))
    idproj = int((data_shape[0]-1)*args.nprojection)
    log.info(f'Stitching projection {idproj} of {data_shape[0]}')

    use_flats_basis = bool(args.flats_file)
    if use_flats_basis:
        import h5py
        with h5py.File(args.flats_file, 'r') as fb:
            basis_flats = fb['/exchange/data_white'][:, :, ::step].astype('float32')
        log.info(f'Loaded flat basis: {basis_flats.shape[0]} frames from {args.flats_file}')
        basis_profs = np.mean(basis_flats, axis=2).T.astype('float64')

    pano = np.zeros([data_shape[1], size], dtype='float32')

    for itile in range(grid.shape[1]):
        if args.reverse_grid == 'True':
            iitile = grid.shape[1]-itile-1
        else:
            iitile = itile

        data, flat, dark, _ = dxchange.read_aps_tomoscan_hdf5(
            grid[0, ::-step][iitile], proj=(idproj, idproj+1))
        dark_mean = np.mean(dark, axis=0)
        n = flat.shape[0]
        p0 = np.mean(flat[:n//2, :, ::step], axis=0)
        p1 = np.mean(flat[n//2:, :, ::step], axis=0)
        if use_flats_basis:
            from scipy.optimize import nnls
            data_f = data[0, :, ::step]
            proj_prof = np.mean(data_f, axis=1).astype('float64')
            w, _ = nnls(basis_profs, proj_prof)
            flat_i = np.einsum('k,khw->hw', w, basis_flats)
            proj = (data_f - dark_mean) / np.maximum(flat_i - dark_mean, 1e-3)
        elif args.flat_linear == 'True':
            t = idproj / max(data_shape[0]-1, 1)
            flat_i = (1-t)*p0 + t*p1
            proj = (data[0, :, ::step] - dark_mean) / np.maximum(flat_i - dark_mean, 1e-3)
        else:
            flat_mean = (p0 + p1) / 2
            proj = (data[0, :, ::step] - dark_mean) / np.maximum(flat_mean - dark_mean, 1e-3)

        v = np.linspace(1, 0, data_shape[2]-x_shift, endpoint=False)
        v = v**5*(126-420*v+540*v**2-315*v**3+70*v**4)
        vv = np.ones(data_shape[2])
        if itile < grid.shape[1]-1:
            vv[x_shift:] = v
        if itile > 0:
            vv[:data_shape[2]-x_shift] = 1-v

        st = int(np.sum(x_shifts[:itile+1]))
        end = min(st+data_shape[2], size)
        pano[:, st:end] += proj[:, :end-st]*vv[:end-st]

    out_dir = os.path.join(args.folder_name, 'tile')
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    out_path = os.path.join(out_dir, 'panoramic.tif')
    tifffile.imwrite(out_path, pano)
    log.info(f'Saved panoramic projection to {out_path}')

    if args.show:
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(16, 4))
        p_low, p_high = np.percentile(pano, [1, 99])
        ax.imshow(pano, cmap='gray', vmin=p_low, vmax=p_high, aspect='auto')
        ax.set_title('Panoramic projection (nominal overlap)')
        ax.axis('off')
        plt.tight_layout()
        plt.show()


def shift_manual(args):
    """Find shifts between horizontal tiles"""

    log.info('Run manual shift')
    # read files grid and retrieve data sizes
    meta_dict, grid, data_shape, data_type, x_shift, y_shift = fileio.tile(args)
    data_type='float32'
    log.info('image   size (x, y) in pixels: (%d, %d)' % (data_shape[2], data_shape[1]))
    log.info('stitch shift (x, y) in pixels: (%d, %d)' % (x_shift, y_shift))
    log.warning('tile overlap (x, y) in pixels: (%d, %d)' % (data_shape[2]-x_shift, data_shape[1]-y_shift))

    # check if flip is needed for having tile[0,0] as the left one and at sample_x=0
    sample_x = args.sample_x
    x0 = meta_dict[grid[0,0]][sample_x][0]
    x1 = meta_dict[grid[0,-1]][sample_x][0]
    if args.reverse_step=='True':
        step = -1
    else:
        step = 1
    
    # ids for slice and projection for shifts testing
    idslice = int((data_shape[1]-1)*args.nsino)
    idproj = int((data_shape[0]-1)*args.nprojection)
    
    # data size after stitching
    size = int(np.ceil((data_shape[2]+(grid.shape[1]-1)*x_shift)/2**(args.binning+1))*2**(args.binning+1))
    data_all = np.ones([data_shape[0],2**args.binning,size],dtype=data_type)
    dark_all = np.zeros([1,2**args.binning,size],dtype=data_type)
    flat_all = np.ones([1,2**args.binning,size],dtype=data_type)

    # load external flat field basis if provided
    use_flats_basis = bool(args.flats_file)
    if use_flats_basis:
        import h5py
        with h5py.File(args.flats_file, 'r') as fb:
            basis_flats = fb['/exchange/data_white'][:, :, ::step].astype('float32')
        log.info(f'Loaded flat basis: {basis_flats.shape[0]} frames from {args.flats_file}')
        basis_profs = np.mean(basis_flats, axis=2).T.astype('float64')
        basis_flats_sino = basis_flats[:, idslice:idslice+2**args.binning, :]
        basis_profs_sino = np.mean(basis_flats_sino, axis=2).T.astype('float64')

    # pre-compute per-tile flat/dark correction arrays
    tile_dark = []
    tile_flat_p0 = []
    tile_flat_p1 = []
    for itile in range(grid.shape[1]):
        if args.reverse_grid=='True':
            iitile=grid.shape[1]-itile-1
        else:
            iitile=itile
        _,flat,dark,_ = dxchange.read_aps_tomoscan_hdf5(grid[0,::-step][iitile],sino=(idslice,idslice+2**args.binning))
        n = flat.shape[0]
        tile_dark.append(np.mean(dark[:,:,::step], axis=0))
        tile_flat_p0.append(np.mean(flat[:n//2,:,::step], axis=0))
        tile_flat_p1.append(np.mean(flat[n//2:,:,::step], axis=0))

    tmp_file_name = f'{args.folder_name}/tile/tmp.h5'
    dirPath = os.path.dirname(tmp_file_name)
    if not os.path.exists(dirPath):
        os.makedirs(dirPath)
    center = input(f"Please enter rotation center ({args.rotation_axis}): ")
    if center.strip():
        args.rotation_axis = center.strip()
    # find shift error
    arr_err = range(-args.shift_search_width, args.shift_search_width, args.shift_search_step)
    data_all = np.ones([data_shape[0],2**args.binning*len(arr_err),size],dtype=data_type)
    dark_all = np.zeros([1,2**args.binning*len(arr_err),size],dtype=data_type)
    flat_all = np.ones([1,2**args.binning*len(arr_err),size],dtype=data_type)    
    pdata_all = np.ones([len(arr_err),data_shape[1],size],dtype='float32')
    if args.x_shifts != 'None':
        x_shifts_res = np.fromstring(args.x_shifts[1:-1], sep=',', dtype='int')
        log.info(f'Using provided x-shifts: {x_shifts_res}')
    else:
        x_shifts_res = np.zeros(grid.shape[1],'int')
        x_shifts_res[1:] = x_shift
        log.info(f'Using nominal x-shifts: {x_shifts_res}')


    for jtile in range(1,grid.shape[1]):

        log.info(f'Processing tile boundary {jtile} of {grid.shape[1]-1}')
        data_all[:]  = 1
        flat_all[:]  = 1
        dark_all[:]  = 0
        pdata_all[:] = 1

        n_shifts = len(arr_err)
        for ishift,err_shift in enumerate(arr_err):
            pct = (ishift + 1) / n_shifts
            filled = int(40 * pct)
            bar = '\u2588' * filled + '\u2591' * (40 - filled)
            print(f'\r  [{bar}] {ishift+1}/{n_shifts} ({err_shift:+d} px)', end='', flush=True)

            x_shifts = x_shifts_res.copy()
            x_shifts[jtile] += err_shift
            for itile in range(grid.shape[1]):
                if args.reverse_grid=='True':
                    iitile=grid.shape[1]-itile-1
                else: 
                    iitile=itile
                if args.recon=='True':
                    data,flat,dark,theta = dxchange.read_aps_tomoscan_hdf5(grid[0,::-step][iitile],sino=(idslice,idslice+2**args.binning))       
                st = np.sum(x_shifts[:itile+1])
                end = min(st+data_shape[2],size)

                v = np.linspace(1, 0, data_shape[2]-x_shift, endpoint=False)
                v = v**5*(126-420*v+540*v**2-315*v**3+70*v**4)
                vv = np.ones(data_shape[2])
                if itile<grid.shape[1]-1:
                    vv[x_shift:]=v
                if itile>0:
                    vv[:data_shape[2]-x_shift]=1-v

                if args.recon=='True':
                    sts = ishift*2**args.binning
                    ends = sts+2**args.binning
                    dark_mean = tile_dark[itile]
                    data_f = data[:,:,::step].copy()
                    if use_flats_basis:
                        from scipy.optimize import nnls
                        for i in range(data_f.shape[0]):
                            proj_prof = np.mean(data_f[i], axis=1).astype('float64')
                            w, _ = nnls(basis_profs_sino, proj_prof)
                            flat_i = np.einsum('k,khw->hw', w, basis_flats_sino)
                            data_f[i] = (data_f[i] - dark_mean) / np.maximum(flat_i - dark_mean, 1e-3)
                    elif args.flat_linear == 'True':
                        for i in range(data_f.shape[0]):
                            t = i / max(data_shape[0]-1, 1)
                            flat_i = (1-t)*tile_flat_p0[itile] + t*tile_flat_p1[itile]
                            data_f[i] = (data_f[i] - dark_mean) / np.maximum(flat_i - dark_mean, 1e-3)
                    else:
                        flat_mean = (tile_flat_p0[itile] + tile_flat_p1[itile]) / 2
                        data_f = (data_f - dark_mean) / np.maximum(flat_mean - dark_mean, 1e-3)
                    np.nan_to_num(data_f, nan=1.0, posinf=1.0, neginf=1.0, copy=False)
                    data_all[:data_f.shape[0],sts:ends,st:end] += data_f[:,:,:end-st]*vv[:end-st]
                    data_all[data_f.shape[0]:,sts:ends,st:end] += data_f[-1,:,:end-st]*vv[:end-st]
                data,flat,dark,theta = dxchange.read_aps_tomoscan_hdf5(grid[0,::-step][iitile],proj=(idproj,idproj+1))
                dark_mean = np.mean(dark,axis=0)
                n = flat.shape[0]
                p0 = np.mean(flat[:n//2,:,::step], axis=0)
                p1 = np.mean(flat[n//2:,:,::step], axis=0)
                if use_flats_basis:
                    from scipy.optimize import nnls
                    data_f = data[0,:,::step]
                    proj_prof = np.mean(data_f, axis=1).astype('float64')
                    w, _ = nnls(basis_profs, proj_prof)
                    flat_i = np.einsum('k,khw->hw', w, basis_flats)
                    data = (data_f - dark_mean) / np.maximum(flat_i - dark_mean, 1e-3)
                elif args.flat_linear == 'True':
                    t = idproj / max(data_shape[0]-1, 1)
                    flat_i = (1-t)*p0 + t*p1
                    data = (data[0,:,::step]-dark_mean)/np.maximum(1e-3,(flat_i-dark_mean))
                else:
                    flat_mean = (p0 + p1) / 2
                    data = (data[0,:,::step]-dark_mean)/np.maximum(1e-3,(flat_mean-dark_mean))
                pdata_all[ishift,:,st:end] = data[:,:end-st]#*vv[:end-st]
                if itile==grid.shape[1]-1:
                    if args.recon=='True':
                        data_all[:,sts:ends,end:]=data_all[:,sts:ends,end-1:end]
                    pdata_all[ishift,:,end:]=pdata_all[ishift,:,end-1:end]
        print()  # end progress bar line
        # create a temporarily DataExchange file
        dir = os.path.dirname(tmp_file_name)
        basename = os.path.basename(tmp_file_name)
        if not os.path.exists(dirPath):
            os.makedirs(dirPath)
        dxchange.write_tiff_stack(pdata_all,f'{dir}_rec/{basename[:-3]}_proj/p',overwrite=True)


        #if args.recon==True:
        f = dx.File(tmp_file_name, mode='w')
        f.add_entry(dx.Entry.data(data={'value': data_all, 'units':'counts'}))
        f.add_entry(dx.Entry.data(data_white={'value': flat_all, 'units':'counts'}))
        f.add_entry(dx.Entry.data(data_dark={'value': dark_all, 'units':'counts'}))
        f.add_entry(dx.Entry.data(theta={'value': theta*180/np.pi, 'units':'degrees'}))
        f.close()

        cmd = f'{args.recon_engine} recon --file-type {args.file_type} --binning {args.binning} --reconstruction-type full \
        --file-name {tmp_file_name} --rotation-axis-auto manual --rotation-axis {args.rotation_axis} --nsino-per-chunk {args.nsino_per_chunk} --end-column {args.end_column}'
        log.warning(cmd)
        os.system(cmd)


        try_path = f"{os.path.dirname(tmp_file_name)}_rec/tmp_rec/recon*"
        tryproj_path = f"{dir}_rec/{basename[:-3]}_proj/p*"
        _G = "\033[92m"; _R = "\033[91m"; _Y = "\033[33m"; _E = "\033[0m"
        parts = [f'{(_G if e<0 else _R if e==0 else _Y)}{i}={e:+d}px{_E}' for i, e in enumerate(arr_err)]
        print(f'Index-to-pixel-offset map for tile {jtile}: ' + ', '.join(parts))
        log.action(f'Please open the stack of images from reconstructions {try_path} or stitched projections {tryproj_path}, and select the file id to shift tile {jtile}')
        nominal_idx = list(arr_err).index(0)
        nominal_overlap = data_shape[2] - x_shift
        sh_str = input(
            f"Please enter id for tile {jtile} shift "
            f"[nominal: {nominal_idx}] corresponding to 0 pixel shift "
            f"from the nominal overlap of {nominal_overlap} px stored in the raw data files: "
        )
        sh = int(sh_str.strip()) if sh_str.strip() else nominal_idx

        x_shifts_res[jtile]+=arr_err[sh]
        log.info(f'Selected offset for tile {jtile}: {arr_err[sh]:+d} px from nominal (index {sh})')
        log.info(f'Current shifts: {x_shifts_res}')
        

    log.info(f'Center {args.rotation_axis}')
    log.info(f'Relative shifts {x_shifts_res.tolist()}')
        
            