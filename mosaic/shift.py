import cv2
import numpy as np
from mosaic import log
from mosaic import util
from mosaic import fileio
import h5py
import os
import dxchange
import tomopy

import dxfile.dxtomo as dx



def shift_manual(args):

    log.info('Run manual shift')
    # read files grid and retrieve data sizes
    tile_dict, grid, data_shape, x_shift, y_shift = fileio.tile(args)

    log.info('image   size (x, y) in pixels: (%d, %d)' % (data_shape[2], data_shape[1]))
    log.info('mosaic shift (x, y) in pixels: (%d, %d)' % (x_shift, y_shift))
    log.warning('tile overlap (x, y) in pixels: (%d, %d)' % (data_shape[2]-x_shift, data_shape[1]-y_shift))

    print(tile_dict)
    binning = 3
    # create a stitched array with different shifts for each tile
    idslice = data_shape[1]//2
    data,flat,dark,theta = dxchange.read_aps_32id(grid[0,0],sino=(idslice,idslice+2**binning))    

    x_shift=2448

    rshifts = np.arange(0,grid.shape[1])*(data_shape[2]-x_shift)
    #rshifts[2] -= err_shift
    add = 20
    size = int(np.ceil((grid.shape[1]*data_shape[2]-rshifts[-1]+2*add)/2**(binning+1))*2**(binning+1))
    #size = (size0-data_shape[2]//2)*2
    data_all = np.ones([data_shape[0],2**binning,size],dtype=data.dtype)
    dark_all = np.zeros([1,2**binning,size],dtype=data.dtype)
    flat_all = np.ones([1,2**binning,size],dtype=data.dtype)
    center = data_shape[2]/2
    print(data_all.shape,center)
    for jtile in range(1,grid.shape[1]):
        for err_shift in range(-add,add,5):
            print(err_shift)
            rshifts = np.arange(0,grid.shape[1])*(data_shape[2]-x_shift)
            rshifts[jtile] += err_shift
            #rshifts[2] -= err_shift
            data_all*=0+1
            dark_all*=0
            flat_all*=0+1
            for itile in range(grid.shape[1]):
                print(itile)
                data,flat,dark,theta = dxchange.read_aps_32id(grid[0,itile],sino=(idslice,idslice+2**binning))       
                st = add+itile*data_shape[2]-rshifts[itile]
                end = st+data_shape[2]
                data_all[:,:,st:end] = data[:,:,::-1]
                dark_all[:,:,st:end] = np.mean(dark[:,:,::-1],axis=0)
                flat_all[:,:,st:end] = np.mean(flat[:,:,::-1],axis=0)
                
                file_name = '/data/tmp/t.h5'
                # create a temporarily DataExchange file
                dirPath = os.path.dirname(file_name)
                if not os.path.exists(dirPath):
                    os.makedirs(dirPath)
                f = dx.File(file_name, mode='w') 
                f.add_entry(dx.Entry.data(data={'value': data_all, 'units':'counts'}))
                f.add_entry(dx.Entry.data(data_white={'value': flat_all, 'units':'counts'}))
                f.add_entry(dx.Entry.data(data_dark={'value': dark_all, 'units':'counts'}))
                f.add_entry(dx.Entry.data(theta={'value': theta*180/np.pi, 'units':'degrees'}))
                f.close()
            os.system(f'tomopy recon --file-type double_fov --binning {binning} --reconstruction-type full --file-name {file_name} --center-search-width 50 --rotation-axis-auto manual --rotation-axis {center} --center-search-step 1')            
            os.system(f'mv /data/tmp_rec/t_rec/recon_00000.tiff /data/tmp_rec/t_rec/recon_shift_{jtile}_{add+rshifts[jtile]:04d}.tiff')
            
def register_shift_sift(datap1, datap2, threshold):
    """Find shifts via SIFT detecting features"""

    mmin1,mmax1 = util.find_min_max(datap1)
    mmin2,mmax2 = util.find_min_max(datap2)
    #print('min *************', mmin)
    #print('max *************', mmax)
    # sift = cv2.xfeatures2d.SIFT_create()
    sift = cv2.SIFT_create()
    shifts = np.zeros([datap1.shape[0],2],dtype='float32')
    for id in range(datap1.shape[0]):       
        tmp1 = ((datap1[id]-mmin1[id]) / (mmax1[id]-mmin1[id])*255.)
        tmp1[tmp1 > 255] = 255
        tmp1[tmp1 < 0] = 0
        tmp2 = ((datap2[id]-mmin2[id]) /
                (mmax2[id]-mmin2[id])*255)
        tmp2[tmp2 > 255] = 255
        tmp2[tmp2 < 0] = 0
        # find key points
        tmp1 = tmp1.astype('uint8')
        tmp2 = tmp2.astype('uint8')
        kp1, des1 = sift.detectAndCompute(tmp1,None)
        kp2, des2 = sift.detectAndCompute(tmp2,None)
        
        cv2.imwrite('original_image_right_keypoints.png',cv2.drawKeypoints(tmp1,kp1,None))
        cv2.imwrite('original_image_left_keypoints.png',cv2.drawKeypoints(tmp2,kp2,None))
        if(len(kp1)==0 or len(kp2)==0):
            shifts[id] = np.nan  
            continue
        match = cv2.BFMatcher()
        matches = match.knnMatch(des1,des2,k=2)
        good = []
        #VN: temporarily solution, knnMatch returns strange shape sometimes
        if(len(matches)==0):
            shifts[id] = np.nan  
            continue
        if(len(matches[0])!=2):
            shifts[id] = np.nan  
            continue
        for m,n in matches:
            if m.distance < threshold*n.distance:
                good.append(m)
        log.info('Number of matched features %d',len(good))
        draw_params = dict(matchColor=(0,255,0),
                            singlePointColor=None,
                            flags=2)
        if(len(good)==0):
            log.warning("No features found for projection %d, set shifts to nan", id)
            shifts[id] = np.nan   
            continue
        tmp3 = cv2.drawMatches(tmp1,kp1,tmp2,kp2,good,None,**draw_params)
        cv2.imwrite("original_image_drawMatches.jpg", tmp3)
        src_pts = np.float32([ kp1[m.queryIdx].pt for m in good ]).reshape(-1,1,2)
        dst_pts = np.float32([ kp2[m.trainIdx].pt for m in good ]).reshape(-1,1,2)
        shift = (src_pts-dst_pts)[:,0,:]
        shifts[id] = np.median(shift,axis=0)[::-1]        
        
        # cv2.imwrite("test1.jpg",np.roll(np.roll(tmp1,int(-shifts[id][1]),axis=1),int(-shifts[id][0]),axis=0))
        # cv2.imwrite("test2.jpg",tmp2)
        # exit()
    return shifts


def shift_auto(args):

    # read files grid and retrieve data sizes
    tile_dict, grid, data_shape, x_shift, y_shift = fileio.tile(args)

    log.info('image   size (x, y) in pixels: (%d, %d)' % (data_shape[2], data_shape[1]))
    log.info('mosaic shift (x, y) in pixels: (%d, %d)' % (x_shift, y_shift))
    log.warning('tile overlap (x, y) in pixels: (%d, %d)' % (data_shape[2]-x_shift, data_shape[1]-y_shift))

    columns = [f'x_{num}' for num in range(grid.shape[0])]
    index = [f'y_{num}' for num in range(grid.shape[0])]
    
    [ntiles_v,ntiles_h] = grid.shape

    multipliers = np.ones([ntiles_v,ntiles_h], dtype=np.float32)      
    # find shifts in horizontal direction
    shifts_h = np.zeros([ntiles_v,ntiles_h,2], dtype=np.float32)    
    if(args.test=='True'):
        iproj = (args.proj,args.proj+1)
    else:
        iproj = (0, data_shape[0], data_shape[0]//8)

    for iy in range(ntiles_v):    
        for ix in range(ntiles_h-1):
            if 'y1_x4' in grid[iy,ix] or 'y1_x4' in grid[iy,ix+1]:
                continue
            print(iproj,grid[iy,ix],grid[iy,ix+1])

            proj0, flat0, dark0, _, _ = dxchange.read_dx(grid[iy,ix], proj=iproj)
            proj1, flat1, dark1, _, _ = dxchange.read_dx(grid[iy,ix+1], proj=iproj)
            norm0 = tomopy.normalize(proj0, flat0, dark0)
            norm1 = tomopy.normalize(proj1, flat1, dark1)
            wx = int((norm0.shape[2] - x_shift)*1)
            dxchange.write_tiff(norm1[:,:,-wx:].astype('float32'),f'/data/NAISE_Spinal_Cord/h1{iy}_{ix}',overwrite=True)
            dxchange.write_tiff(norm0[:,:,:wx].astype('float32'),f'/data/NAISE_Spinal_Cord/h0{iy}_{ix}',overwrite=True)
            
            shift = mosaic.register_shift_sift(norm1[:,:,-wx:], norm0[:,:,:wx],args.threshold)

            shift = shift[~np.isnan(shift[:,0])]
            if (len(shift)==0):
                shift = np.array([[0,0]])
            print(f'{iy},{ix},{wx=}')
            shifts_h[iy,ix+1] = [np.median(shift[:,0]),np.median(wx-shift[:,1])]            
            log.info(shifts_h[iy,ix+1])
            #VN: tmp for Kaoumi dataset
            height = 256
            multipliers[iy,ix+1] = 1#/(np.linalg.norm(norm1[:,data_shape[1]//2-height:data_shape[1]//2+height,-wx:])/np.linalg.norm(norm0[:,data_shape[1]//2-height:data_shape[1]//2+height,:wx]))
            log.info('multipliers:')
            log.info(multipliers)
    # find shifts in vertical direction    
    shifts_v = np.zeros([ntiles_v,ntiles_h,2], dtype=np.float32)    
    for ix in range(ntiles_h):
        for iy in range(ntiles_v-1):            
            if 'y1_x4' in grid[iy,ix] or 'y1_x4' in grid[iy+1,ix]:
                continue
            proj0, flat0, dark0, _, _ = dxchange.read_dx(grid[iy,ix], proj=iproj)
            proj1, flat1, dark1, _, _ = dxchange.read_dx(grid[iy+1,ix], proj=iproj)
            norm0 = tomopy.normalize(proj0, flat0, dark0)
            norm1 = tomopy.normalize(proj1, flat1, dark1)
            wy = int((norm0.shape[1] - y_shift)*1)
            dxchange.write_tiff(norm1[:,-wy:].astype('float32'),f'/data/NAISE_Spinal_Cord/v1{iy}_{ix}',overwrite=True)
            dxchange.write_tiff(norm0[:,:wy].astype('float32'),f'/data/NAISE_Spinal_Cord/v0{iy}_{ix}',overwrite=True)
            shift = mosaic.register_shift_sift(norm0[:,-wy:,:], norm1[:,:wy,:],args.threshold)
            shift = shift[~np.isnan(shift[:,0])]
            if (len(shift)==0):
                shift = np.array([[0,0]])
            shifts_v[iy+1,ix] = [np.median(wy-shift[:,0]),np.median(shift[:,1])]
            multipliers[iy+1,ix] = np.linalg.norm(norm0[:,-wy:,:])/np.linalg.norm(norm1[:,:wy,:])
    log.info('Horizontal shifts')
    log.info(shifts_h)
    log.info('Vertical shifts')
    log.info(shifts_v)

    shifts_h_fname, shifts_v_fname, multipliers_fname = fileio.service_fnames(args.mosaic_fname)

    # save shifts
    # VN:we can try to save them as txt or csv instead to be able to change manually at any time
    # log.info('save shifts as npy')
    # np.save(shifts_h_fname, shifts_h)
    # np.save(shifts_v_fname, shifts_v)
    # np.save(multipliers_fname, multipliers)

    # reshaping the array from 3D matrice to 2D matrice.
    fileio.write_array(shifts_h_fname, shifts_h)
    fileio.write_array(shifts_v_fname, shifts_v)
    fileio.write_array(multipliers_fname, multipliers)

    return shifts_h, shifts_v
