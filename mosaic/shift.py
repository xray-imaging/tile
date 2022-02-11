from mosaic import log
from mosaic import fileio
import numpy as np
import os
import dxchange
import dxfile.dxtomo as dx
import h5py

def shift_manual(args):

    log.info('Run manual shift')
    # read files grid and retrieve data sizes
    meta_dict, grid, data_shape, x_shift, y_shift = fileio.tile(args)

    log.info('image   size (x, y) in pixels: (%d, %d)' % (data_shape[2], data_shape[1]))
    log.info('mosaic shift (x, y) in pixels: (%d, %d)' % (x_shift, y_shift))
    log.warning('tile overlap (x, y) in pixels: (%d, %d)' % (data_shape[2]-x_shift, data_shape[1]-y_shift))

    # check if flip is needed for having tile[0,0] as the left one and at sample_x=0
    sample_x = 'measurement_instrument_sample_motor_stack_setup_sample_x'
    x0 = meta_dict[grid[0,0]][sample_x][0]
    x1 = meta_dict[grid[0,-1]][sample_x][0]
    if(x0+x1>0):
        step = -1
    else:
        step = 1
    idslice = int((data_shape[1]-1)*args.nsino)
    idproj = int((data_shape[0]-1)*args.nproj)
    data,flat,dark,theta = dxchange.read_aps_32id(grid[0,0],sino=(idslice,idslice+2**args.binning))    
    size = int(np.ceil((data_shape[2]+(grid.shape[1]-1)*x_shift)/2**(args.binning+1))*2**(args.binning+1))
    data_all = np.ones([data_shape[0],2**args.binning,size],dtype=data.dtype)
    dark_all = np.zeros([1,2**args.binning,size],dtype=data.dtype)
    flat_all = np.ones([1,2**args.binning,size],dtype=data.dtype)

    tmp_file_name = f'{args.folder_name}/mosaic/tmp.h5'
    # Center search with using the first tile
    for itile in range(grid.shape[1]):
        data,flat,dark,theta = dxchange.read_aps_32id(grid[0,::-step][itile],sino=(idslice,idslice+2**args.binning))       
        st = itile*x_shift
        end = st+data_shape[2]
        data_all[:,:,st:end] = data[:,:,::step]
        dark_all[:,:,st:end] = np.mean(dark[:,:,::step],axis=0)
        flat_all[:,:,st:end] = np.mean(flat[:,:,::step],axis=0)
        dirPath = os.path.dirname(tmp_file_name)
        if not os.path.exists(dirPath):
            os.makedirs(dirPath)
        f = dx.File(tmp_file_name, mode='w') 
        f.add_entry(dx.Entry.data(data={'value': data_all, 'units':'counts'}))
        f.add_entry(dx.Entry.data(data_white={'value': flat_all, 'units':'counts'}))
        f.add_entry(dx.Entry.data(data_dark={'value': dark_all, 'units':'counts'}))
        f.add_entry(dx.Entry.data(theta={'value': theta*180/np.pi, 'units':'degrees'}))
        f.close()
        
    os.system(f'tomocupy recon --file-type double_fov --binning {args.binning} --reconstruction-type try --file-name {tmp_file_name} \
            --center-search-width {args.center_search_width} --rotation-axis-auto manual --rotation-axis {args.rotation_axis} \
            --center-search-step {args.center_search_step}')            
    
    center = input("Please enter rotation center: ")
    
    # find shift error
    arr_err = range(-args.shift_search_width,args.shift_search_width,args.shift_search_step)
    data_all = np.ones([data_shape[0],2**args.binning*len(arr_err),size],dtype=data.dtype)
    dark_all = np.zeros([1,2**args.binning*len(arr_err),size],dtype=data.dtype)
    flat_all = np.ones([1,2**args.binning*len(arr_err),size],dtype=data.dtype)    
    
    pdata_all = np.ones([len(arr_err),data_shape[1],size],dtype='float32')
    
    x_shifts_res = np.zeros(grid.shape[1],'int')
    x_shifts_res[1:] = x_shift
    for jtile in range(1,grid.shape[1]):        
        data_all[:] = 1
        flat_all[:] = 1
        dark_all[:] = 0
        pdata_all[:] = 1
        
        for ishift,err_shift in enumerate(arr_err):
            x_shifts = x_shifts_res.copy()
            x_shifts[jtile] += err_shift
            for itile in range(grid.shape[1]):
                data,flat,dark,theta = dxchange.read_aps_32id(grid[0,::-step][itile],sino=(idslice,idslice+2**args.binning))       
                st = np.sum(x_shifts[:itile+1])
                end = min(st+data_shape[2],size)
                sts = ishift*2**args.binning
                ends = sts+2**args.binning
                data_all[:,sts:ends,st:end] = data[:,:,::step][:,:,:end-st]
                dark_all[:,sts:ends,st:end] = np.mean(dark[:,:,::step],axis=0)[:,:end-st]
                flat_all[:,sts:ends,st:end] = np.mean(flat[:,:,::step],axis=0)[:,:end-st]
                data,flat,dark,theta = dxchange.read_aps_32id(grid[0,::-step][itile],proj=(idproj,idproj+1))       
                data = (data-np.mean(dark,axis=0))/np.maximum(1e-3,(np.mean(flat,axis=0)-np.mean(dark,axis=0)))
                pdata_all[ishift,:,st:end] = data[:,:,::step][:,:,:end-st]
        # create a temporarily DataExchange file
        dir = os.path.dirname(tmp_file_name)
        basename = os.path.basename(tmp_file_name)
        if not os.path.exists(dirPath):
            os.makedirs(dirPath)
        dxchange.write_tiff_stack(pdata_all,f'{dir}_recgpu/{basename[:-3]}_proj/p',overwrite=True)        
        f = dx.File(tmp_file_name, mode='w') 
        f.add_entry(dx.Entry.data(data={'value': data_all, 'units':'counts'}))
        f.add_entry(dx.Entry.data(data_white={'value': flat_all, 'units':'counts'}))
        f.add_entry(dx.Entry.data(data_dark={'value': dark_all, 'units':'counts'}))
        f.add_entry(dx.Entry.data(theta={'value': theta*180/np.pi, 'units':'degrees'}))
        f.close()        

        os.system(f'tomocupy recon --file-type double_fov --binning {args.binning} --reconstruction-type full \
            --file-name {tmp_file_name} --rotation-axis-auto manual --rotation-axis {center} --nsino-per-chunk {args.nsino_per_chunk}')            
        

        print(x_shifts_res)
        sh = int(input(f"Please enter id for tile {jtile}: "))
        x_shifts_res[jtile]+=arr_err[sh]




    log.info(f'Center {center}')
    log.info(f'Relative shifts {x_shifts_res.tolist()}')
        
            