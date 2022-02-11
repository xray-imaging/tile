import numpy as np
from mosaic import log
from mosaic import fileio
import h5py
import dxchange


def stitch(args):
    log.info('Run stitch')

    if args.end_proj == -1:
        args.end_proj = len(theta)
    x_shifts = np.fromstring(args.x_shifts[1:-1],sep=',',dtype='int')
    
    # read files grid and retrieve data sizes
    _, grid, data_shape, _, _ = fileio.tile(args)
    # check whether flip is needed
    with h5py.File(grid[0,0],'r') as fid1:
        with h5py.File(grid[0,-1],'r') as fid2:
            x0 = fid1['/measurement/instrument/sample_motor_stack/setup/sample_x'][0]
            x1 = fid2['/measurement/instrument/sample_motor_stack/setup/sample_x'][0]
            if(x0+x1>0):
                step = -1
            else:
                step = 1    
    # read one sino to determine parameters
    data,flat,dark,theta = dxchange.read_aps_32id(grid[0,0],sino=(0,1))    
    # total size in x direction
    size = int(np.ceil((data_shape[2]+np.sum(np.sum(x_shifts)))/2**(args.binning+1))*2**(args.binning+1))
    with h5py.File(args.mosaic_fname,'w') as fid:
        # init output arrays
        data_all = fid.create_dataset('/exchange/data', (args.end_proj-args.start_proj,data_shape[1],size),dtype=data.dtype, chunks = (1,data_shape[1],size))
        flat_all = fid.create_dataset('/exchange/data_white', (1,data_shape[1],size),dtype=flat.dtype, chunks = (1,data_shape[1],size))
        dark_all = fid.create_dataset('/exchange/data_dark', (1,data_shape[1],size),dtype=dark.dtype, chunks =(1,data_shape[1],size))
        theta = fid.create_dataset('/exchange/theta', data = theta[args.start_proj:args.end_proj])

        for ichunk in range(int(np.ceil((args.end_proj-args.start_proj)/args.chunk_size))):            
            st_chunk = args.start_proj+ichunk*args.chunk_size
            end_chunk = min(st_chunk+args.chunk_size,args.end_proj)
            log.info(f'Stitching projections {st_chunk} - {end_chunk}')
            for itile in range(grid.shape[1]):
                data,flat,dark,_ = dxchange.read_aps_32id(grid[0,::-step][itile], proj=(st_chunk,end_chunk))      
                st = np.sum(x_shifts[:itile+1])
                end = min(st+data_shape[2],size)
                data_all[st_chunk-args.start_proj:end_chunk-args.start_proj,:,st:end] = data[:,:,::step]
                dark_all[st_chunk-args.start_proj:end_chunk-args.start_proj,:,st:end] = np.mean(dark[:,:,::step],axis=0)
                flat_all[st_chunk-args.start_proj:end_chunk-args.start_proj,:,st:end] = np.mean(flat[:,:,::step],axis=0)
    log.info(f'Output file {args.mosaic_fname}')
