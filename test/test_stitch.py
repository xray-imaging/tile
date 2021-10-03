import dxchange
import cv2
import numpy as np
import matplotlib.pyplot as plt

def find_min_max(data):
    """Find min and max values according to histogram"""
    
    mmin = np.zeros(data.shape[0],dtype='float32')
    mmax = np.zeros(data.shape[0],dtype='float32')
    
    for k in range(data.shape[0]):
        h, e = np.histogram(data[k][:],1000)
        stend = np.where(h>np.max(h)*0.005)
        st = stend[0][0]
        end = stend[0][-1]        
        mmin[k] = e[st]
        mmax[k] = e[end+1]
     
    return mmin, mmax

def split(data,ny,nx,sy,sx,wy,wx):
    """split data into tiles and shift them"""

    grid = np.zeros([ny,nx,1,wy,wx],dtype='float32')
    for iy in range(ny):
        for ix in range(nx):
            grid[iy,nx-ix-1] = data[:,iy*(wy-sy)+4*ix:iy*(wy-sy)+wy+4*ix,ix*(wx-sx)+4*iy:ix*(wx-sx)+wx+4*iy]
    return grid        

def register_shift_sift(datap1, datap2):
    """Find shifts via SIFT detecting features"""

    mmin,mmax = find_min_max(datap1)
    sift = cv2.SIFT_create()
    shifts = np.zeros([datap1.shape[0],2],dtype='float32')
    for id in range(datap1.shape[0]):       
        tmp1 = ((datap1[id]-mmin[id]) / (mmax[id]-mmin[id])*255.)
        tmp1[tmp1 > 255] = 255
        tmp1[tmp1 < 0] = 0
        tmp2 = ((datap2[id]-mmin[id]) /
                (mmax[id]-mmin[id])*255)
        tmp2[tmp2 > 255] = 255
        tmp2[tmp2 < 0] = 0
        # find key points
        tmp1 = tmp1.astype('uint8')
        tmp2 = tmp2.astype('uint8')
        kp1, des1 = sift.detectAndCompute(tmp1,None)
        kp2, des2 = sift.detectAndCompute(tmp2,None)
        cv2.imwrite('/local/data/tmp/original_image_right_keypoints.png',cv2.drawKeypoints(tmp1,kp1,None))
        cv2.imwrite('/local/data/tmp/original_image_left_keypoints.png',cv2.drawKeypoints(tmp2,kp2,None))
        match = cv2.BFMatcher()
        matches = match.knnMatch(des1,des2,k=2)
        good = []
        for m,n in matches:
            if m.distance < 0.4*n.distance:
                good.append(m)
        draw_params = dict(matchColor=(0,255,0),
                            singlePointColor=None,
                            flags=2)
        tmp3 = cv2.drawMatches(tmp1,kp1,tmp2,kp2,good,None,**draw_params)
        cv2.imwrite("/local/data/tmp/original_image_drawMatches.jpg", tmp3)
        src_pts = np.float32([ kp1[m.queryIdx].pt for m in good ]).reshape(-1,1,2)
        dst_pts = np.float32([ kp2[m.trainIdx].pt for m in good ]).reshape(-1,1,2)
        shift = (src_pts-dst_pts)[:,0,:]
        shifts[id] = np.median(shift,axis=0)[::-1]
    return shifts


ntiles_v = 4
ntiles_h = 4
shift_y = 50
shift_x = 120
width_y = 150
width_x = 512

data = dxchange.read_tiff('/local/data/tmp/test_proj.tiff')
grid = split(data,ntiles_v,ntiles_h,shift_y,shift_x,width_y,width_x)

shifts_h = np.zeros([ntiles_v,ntiles_h,2], dtype=np.float32)    
for iy in range(ntiles_v):    
        for ix in range(ntiles_h-1):
            wx = shift_x
            norm0 = grid[iy,ix]
            norm1 = grid[iy,ix+1]
            shift = register_shift_sift(norm1[:,:,-wx:], norm0[:,:,:wx])
            shift = shift[~np.isnan(shift[:,0])]
            shifts_h[iy,ix+1] = [np.median(shift[:,0]),np.median(wx-shift[:,1])] 

shifts_v = np.zeros([ntiles_v,ntiles_h,2], dtype=np.float32)    
for ix in range(ntiles_h):
    for iy in range(ntiles_v-1):            
        wy = shift_y
        norm0 = grid[iy,ix]
        norm1 = grid[iy+1,ix]
        shift = register_shift_sift(norm0[:,-wy:,:], norm1[:,:wy,:])
        shift = shift[~np.isnan(shift[:,0])]
        shifts_v[iy+1,ix] = [np.median(wy-shift[:,0]),np.median(shift[:,1])]

cshifts_h=shifts_h[:,:,1]
cshifts_v=shifts_v[:,:,0]
cshifts_h[:,0] = np.cumsum(shifts_h[:,0,1]+shifts_v[:,0,1])
cshifts_v[0,:] = np.cumsum(shifts_h[0,:,0]+shifts_v[0,:,0])
cshifts_h = np.cumsum(cshifts_h,axis=1)
cshifts_v = np.cumsum(cshifts_v,axis=0)

proj = np.zeros([1,ntiles_v*width_y-int(cshifts_v[-1].max()),
    ntiles_h*width_x-int(cshifts_h[-1].max())],dtype='float32')

# stitch several projections
for iy in range(ntiles_v):    
    for ix in range(ntiles_h):
        print(iy,ix,cshifts_h[iy,ix],cshifts_v[iy,ix])
        st_x = int(np.round(proj.shape[2]-(ix+1)*width_x+cshifts_h[iy,ix]))
        end_x = st_x+width_x            
        r_x = np.arange(st_x,end_x)%proj.shape[2]
        st_y = int(np.round(iy*width_y-cshifts_v[iy,ix]))
        end_y = st_y+width_y            
        r_y = np.arange(st_y,end_y)%proj.shape[1]
        norm0 = grid[iy,ix]
        proj[:,r_y[:,None],r_x] = norm0

        proj[:,min(max(st_y-16,0),proj.shape[1]-1),r_x]=0
        proj[:,min(max(st_y+16,0),proj.shape[1]-1),r_x]=0
        proj[:,min(max(end_y-16,0),proj.shape[1]-1),r_x]=0
        proj[:,min(max(end_y+16,0),proj.shape[1]-1),r_x]=0
        
        proj[:,r_y[:,None],min(max(st_x-16,0),proj.shape[2]-1)]=0
        proj[:,r_y[:,None],min(max(st_x+16,0),proj.shape[2]-1)]=0
        proj[:,r_y[:,None],min(max(end_x-16,0),proj.shape[2]-1)]=0
        proj[:,r_y[:,None],min(max(end_x+16,0),proj.shape[2]-1)]=0

dxchange.write_tiff(proj[0],'/local/data/tmp/res_test_proj',overwrite=True)