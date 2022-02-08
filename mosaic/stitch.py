import cv2
import numpy as np
from mosaic import log
from mosaic import util
from mosaic import fileio
import h5py
import os
import dxchange
import tomopy

def stitch(args):
    
    shifts_h_fname, shifts_v_fname, multipliers_fname = fileio.service_fnames(args.mosaic_fname)

    # read shifts
    shifts_h    = fileio.read_array(shifts_h_fname)
    shifts_v    = fileio.read_array(shifts_v_fname)
    
    #FDC: here we need to handle the case of h/v scan only (no tiles)
    # compute cumulative shifts
    cshifts_h = shifts_h[:,:,1]
    cshifts_v = shifts_v[:,:,0]
    cshifts_h[:,0] = np.cumsum(shifts_h[:,0,1]+shifts_v[:,0,1])
    cshifts_v[0,:] = np.cumsum(shifts_h[0,:,0]+shifts_v[0,:,0])
    cshifts_h = np.cumsum(cshifts_h,axis=1)
    cshifts_v = np.cumsum(cshifts_v,axis=0)
    
    # retrieve sizes (could be optimized)
    _, grid, data_shape, _, _ = fileio.tile(args)
    [ntiles_v,ntiles_h] = grid.shape
    proj0, flat0, dark0, theta0, _ = dxchange.read_dx(grid[0,0], proj=(0, 1))


    proj_size = (ntiles_v*data_shape[1]-int(cshifts_v[-1].max()), 
        (ntiles_h*data_shape[2]-int(cshifts_h[-1].max()))//4*4)#make the width divisible by 4 to work with binning 2 at least
    
    if(args.test=='True'):
        # number of projections to test stitching
        nproj_to_stitch = 1
        # normalized array to be filled
        norm = np.zeros([nproj_to_stitch,*proj_size],dtype='float32')        
    else:
        nproj_to_stitch = data_shape[0]

    with h5py.File(args.mosaic_fname,'w') as fid:
        # init output arrays
        #VN: add metadata with dxwriter
        proj = fid.create_dataset('/exchange/data', (nproj_to_stitch,*proj_size),dtype=proj0.dtype, chunks = (1,*proj_size))
        flat = fid.create_dataset('/exchange/data_white', (1,*proj_size),dtype=flat0.dtype, chunks = (1,*proj_size))
        dark = fid.create_dataset('/exchange/data_dark', (1,*proj_size),dtype=dark0.dtype, chunks = (1,*proj_size))
        theta = fid.create_dataset('/exchange/theta', data = theta0/np.pi*180)
        
        # stitch projections by chunks
        for ichunk in range(int(np.ceil(nproj_to_stitch/args.chunk_size))):
            st_chunk = ichunk*args.chunk_size
            end_chunk = min((ichunk+1)*args.chunk_size,nproj_to_stitch)
            if(args.test=='True'):
                st_chunk = args.proj
                end_chunk = args.proj+1
            
            log.info('Processing projections: %d - %d' % (st_chunk, end_chunk))
            for iy in range(ntiles_v):    
                for ix in range(ntiles_h):
                    # VN: no need to read flat and dark fields for each chunk, should we use h5py[].. instead?
                    proj0, flat0, dark0, _, _ = dxchange.read_dx(grid[iy,ix], proj=(st_chunk,end_chunk))
                    
                    # define index in x for proj (filling from the right side)
                    st_x0 = int(np.round(proj.shape[2]-(ix+1)*data_shape[2]+cshifts_h[iy,ix]))
                    end_x0 = st_x0+data_shape[2]            
                    
                    # define index in y for proj (filling from the top side)
                    st_y0 = int(np.round(iy*data_shape[1]-cshifts_v[iy,ix]))
                    end_y0 = st_y0+data_shape[1]            
                    
                    # crop to the proj size 
                    st_y = max(st_y0,0)
                    st_x = max(st_x0,0)
                    end_y = min(end_y0,proj.shape[1])
                    end_x = min(end_x0,proj.shape[2])
                                        
                    # define index in x for proj0
                    st_x0 = st_x-st_x0
                    end_x0 = proj0.shape[2]+end_x-end_x0
                    
                    # define index in x for proj0
                    st_y0 = st_y-st_y0                    
                    end_y0 = proj0.shape[1]+end_y-end_y0
                    
                    # fill array part
                    proj[st_chunk:end_chunk,st_y:end_y,st_x:end_x] = proj0[:,st_y0:end_y0,st_x0:end_x0]
                    log.info('grid[iy,ix] = %s, ix=%d, iy=%d dark0.shape[%d, %d, %d]' % (grid[iy,ix], ix, iy, dark0.shape[0], dark0.shape[1], dark0.shape[2]))
                    if(ichunk==0): # flat and dark field can be filled once (VN: maybe we can move this code out of the loop)
                        flat[:,st_y:end_y,st_x:end_x] = np.mean(flat0[:,st_y0:end_y0,st_x0:end_x0],axis=0)
                        dark[:,st_y:end_y,st_x:end_x] = np.mean(dark0[:,st_y0:end_y0,st_x0:end_x0],axis=0)
                    
                    if(args.test=='True'):                
                        # fill the normalized array part
                        norm[0,st_y:end_y,st_x:end_x] = tomopy.normalize(proj0[0,st_y0:end_y0,st_x0:end_x0], 
                            flat0[:,st_y0:end_y0,st_x0:end_x0], dark0[:,st_y0:end_y0,st_x0:end_x0])                
                        # plot lines arround borders (not necessary in future)
                        norm[0,min(max(st_y-16,0),proj.shape[1]-1),st_x:end_x]=0
                        norm[0,min(max(st_y+16,0),proj.shape[1]-1),st_x:end_x]=0
                        norm[0,min(max(end_y-16,0),proj.shape[1]-1),st_x:end_x]=0
                        norm[0,min(max(end_y+16,0),proj.shape[1]-1),st_x:end_x]=0
                        
                        norm[0,st_y:end_y,min(max(st_x-16,0),proj.shape[2]-1)]=0
                        norm[0,st_y:end_y,min(max(st_x+16,0),proj.shape[2]-1)]=0
                        norm[0,st_y:end_y,min(max(end_x-16,0),proj.shape[2]-1)]=0
                        norm[0,st_y:end_y,min(max(end_x+16,0),proj.shape[2]-1)]=0

    log.info('Stitched h5 file is saved as %s' % args.mosaic_fname)
    if(args.test=='True'): 
        mosaic_folder = os.path.dirname(args.mosaic_fname)
        mosaic_test_fname = os.path.join(mosaic_folder, 'projection')
        dxchange.write_tiff_stack(norm, mosaic_test_fname+str(args.proj),overwrite=True)
        log.info('Test results are saved to %s' % mosaic_test_fname)

