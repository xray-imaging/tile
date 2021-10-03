import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import NoNorm

from mosaic import log
from mosaic import util
import dxchange

def register_shift_sift(datap1, datap2, threshold):
    """Find shifts via SIFT detecting features"""

    mmin,mmax = util.find_min_max(datap1)
    #print('min *************', mmin)
    #print('max *************', mmax)
    # sift = cv2.xfeatures2d.SIFT_create()
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
        # cv2.imwrite('original_image_right_keypoints.png',cv2.drawKeypoints(tmp1,kp1,None))
        # cv2.imwrite('original_image_left_keypoints.png',cv2.drawKeypoints(tmp2,kp2,None))
        match = cv2.BFMatcher()
        matches = match.knnMatch(des1,des2,k=2)
        good = []
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
        # tmp3 = cv2.drawMatches(tmp1,kp1,tmp2,kp2,good,None,**draw_params)
        # cv2.imwrite("original_image_drawMatches.jpg", tmp3)
        src_pts = np.float32([ kp1[m.queryIdx].pt for m in good ]).reshape(-1,1,2)
        dst_pts = np.float32([ kp2[m.trainIdx].pt for m in good ]).reshape(-1,1,2)
        shift = (src_pts-dst_pts)[:,0,:]
        shifts[id] = np.median(shift,axis=0)[::-1]        
        
        # cv2.imwrite("test1.jpg",np.roll(np.roll(tmp1,int(-shifts[id][1]),axis=1),int(-shifts[id][0]),axis=0))
        # cv2.imwrite("test2.jpg",tmp2)
        # exit()
    return shifts
