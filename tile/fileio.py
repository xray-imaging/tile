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
import re
import h5py
import numpy as np
import json

from collections import deque
from pathlib import Path

from tile import log

SHIFTS_FILE_HEADER = '# Array shape: '

def write_array(fname, arr):
      
    # Write the array to disk
    header = SHIFTS_FILE_HEADER
    with open(fname, 'w') as outfile:
        outfile.write(header + '{0}\n'.format(arr.shape))
        for data_slice in arr:
            np.savetxt(outfile, data_slice, fmt='%-7.2f')
            # Writing out a break to indicate different slices...
            outfile.write('# New slice\n')
    log.info('Shift information saved in %s' % fname)

def read_array(fname):

    new_data = None
    try:
        with open(fname) as f:
            firstline = f.readlines()[0].rstrip()

            header = SHIFTS_FILE_HEADER
            fshape = firstline[len(header):]
            fshape = fshape.replace('(','').replace(')','')  
            shape = tuple(map(int, fshape.split(', ')))

            # Read the array from disk
            new_data = np.loadtxt(fname)
            new_data = new_data.reshape(shape)
    except Exception as error: 
        log.error("%s not found" % fname)
        log.error("run -- $ tile shift -- first")        
    return new_data

def extract_meta(args,fname):
        
    if os.path.isdir(fname):
        meta_dict = {}
        dirs = os.listdir(fname)
        
        for subdir in dirs:
            if subdir=='damaged' or subdir=='tile' or subdir=='tile_rec':
               continue
            if args.substring in subdir:
                fulldir = os.path.join(fname,subdir)
                # read file of max size in folder
                max_size = 0
                for f in os.listdir(fulldir):
                    size = os.stat(os.path.join(fulldir, f)).st_size                
                    # updating maximum size
                    if size>max_size:
                        max_size = size
                        max_file = os.path.join( fulldir, f  )        
                
                #read corresponding json
                mjson = fulldir+'/'+subdir+'.json'
                sub_dict = extract_dict(args,max_file,mjson)            
                meta_dict.update(sub_dict)        
    else:
        log.error('No valid HDF5 file(s) found')
        return None

    return meta_dict

def extract_dict(args,fname,mjson):

    f = open(mjson)
    data = json.load(f)
    meta_dict={}
    meta_dict[args.sample_x]=[data['scientificMetadata']['scanParameters']['Sample In']['v'],data['scientificMetadata']['scanParameters']['Sample In']['u']]
    meta_dict[args.sample_y]=[data['scientificMetadata']['scanParameters']['Sample holder Y-position']['v'],data['scientificMetadata']['scanParameters']['Sample holder Y-position']['u']]
    meta_dict[args.resolution]=[data['scientificMetadata']['detectorParameters']['Actual pixel size']['v'],data['scientificMetadata']['detectorParameters']['Actual pixel size']['u']]
    meta_dict[args.full_file_name]=fname
    
    return {fname:meta_dict}

def extract(args):

    log.warning('checking tile files ...')
    file_path = Path(args.folder_name)


    if file_path.is_dir():
        log.info("Checking directory: %s for a tile scan" % args.folder_name)
        # Add a trailing slash if missing
        top = os.path.join(args.folder_name, '')
        meta_dict = extract_meta(args,args.folder_name)
        return meta_dict
    else:
        log.error("directory %s does not contain any file" % args.folder_name)
    

def tile(args):
    meta_dict = extract(args)
    sample_x       = args.sample_x
    sample_y       = args.sample_y
    resolution     = args.resolution
    full_file_name = args.full_file_name
    if args.step_x>0:
        log.error('--step-x is greater than zero: %d' % args.step_x) 
        log.error('%d will be used to manually overide the value stored in the hdf file' % args.step_x) 
        log.error('to use the value stored in the hdf file: --step-x 0') 
        for i,k in enumerate(meta_dict.keys()):
            log.info(f'{k}, sample_x = {i*args.step_x}')
            meta_dict[k][sample_x][0] = i*args.step_x
    log.warning('tile file sorted')
    x_sorted = {k: v for k, v in sorted(meta_dict.items(), key=lambda item: item[1][sample_x])}
    y_sorted = x_sorted#{k: v for k, v in sorted(x_sorted.items(), key=lambda item: item[1][sample_y])}
    
    # y_sorted = {k: v for k, v in sorted(x_sorted.items(), key=lambda item: item[1][sample_y])}
    
    first_key = list(y_sorted.keys())[0]
    second_key = list(y_sorted.keys())[1]
    tile_index_x = 0
    tile_index_y = 0
    x_start = y_sorted[first_key][sample_x][0] - 1
    y_start = y_sorted[first_key][sample_y][0] - 1 

    x_shift = int((1000*(x_sorted[second_key][sample_x][0]- x_sorted[first_key][sample_x][0]))/y_sorted[first_key][resolution][0])
    y_shift = 0
    
    tile_dict = {}
    
    for k, v in y_sorted.items():
        if meta_dict[k][sample_x][0] > x_start:
            key = 'x' + str(tile_index_x) + 'y' + str(tile_index_y)
            log.info('%s: x = %f; y = %f, file name = %s, original file name = %s' % (key, meta_dict[k][sample_x][0], meta_dict[k][sample_y][0], k, meta_dict[k][full_file_name][0]))
            tile_index_x = tile_index_x + 1
            x_start = meta_dict[k][sample_x][0]
            first_y = meta_dict[k][sample_y][0]
        else:
            tile_index_x = 0
            tile_index_y = tile_index_y + 1
            key = 'x' + str(tile_index_x) + 'y' + str(tile_index_y)
            log.info('%s: x = %f; y = %f, file name = %s, original file name = %s' % (key, meta_dict[k][sample_x][0], meta_dict[k][sample_y][0], k, meta_dict[k][full_file_name][0]))
            tile_index_x = tile_index_x + 1
            x_start = y_sorted[first_key][sample_x][0] - 1
            y_shift = int((1000*(meta_dict[k][sample_y][0] - first_y)/y_sorted[first_key][resolution][0]))

        tile_dict[key] = k 

    tile_index_x_max  = tile_index_x
    tile_index_y_max  = tile_index_y + 1

    index_list = []
    for k, v in tile_dict.items():
        index_list.append(k)

    regex = re.compile(r"x(\d+)y(\d+)")
    ind_buff = [m.group(1, 2) for l in index_list for m in [regex.search(l)] if m]
    ind_list = np.asarray(ind_buff).astype('int')

    grid = np.empty((tile_index_y_max, tile_index_x_max), dtype=object)

    k_file = 0
    for k, v in tile_dict.items():
        grid[ind_list[k_file, 1], ind_list[k_file, 0]] = v
        k_file = k_file + 1 

    with h5py.File(grid[0,0],'r') as fid:
        data_shape = fid['exchange/data'].shape
        data_type = fid['exchange/data'].dtype


    return meta_dict, grid, data_shape, data_type, x_shift, y_shift


