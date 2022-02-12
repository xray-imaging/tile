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
import dxchange.reader as dxreader
import dxchange

from collections import deque
from pathlib import Path

from tile import log

PIPE = "│"
ELBOW = "└──"
TEE = "├──"
PIPE_PREFIX = "│   "
SPACE_PREFIX = "    "

KNOWN_FORMATS = ['dx', 'aps2bm', 'aps7bm', 'aps32id']
SHIFTS_FILE_HEADER = '# Array shape: '

__all__ = ['read_hdf_meta']

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
        ##FDC shall we return an arrays with zeros? to handle vertial/horizontal scans?
    return new_data

def extract_meta(fname):

    if os.path.isdir(fname):
        # Add a trailing slash if missing
        top = os.path.join(fname, '')
        h5_file_list = list(filter(lambda x: x.endswith(('.h5', '.hdf')), os.listdir(top)))
        h5_file_list.sort()
        meta_dict = {}
        for fname in h5_file_list:
            h5fname = top + fname
            sub_dict = extract_dict(h5fname)
            meta_dict.update(sub_dict)
    else:
        log.error('No valid HDF5 file(s) fund')
        return None

    return meta_dict

def extract_dict(fname):

    tree, meta = read_hdf_meta(fname)
    sub_dict = {fname : meta}

    return sub_dict

def extract(args):

    log.warning('checking tile files ...')
    file_path = Path(args.folder_name)

    if str(args.file_format) in KNOWN_FORMATS:

        if file_path.is_file(): #or len(next(os.walk(file_path))[2]) == 1:
            log.error("A tile dataset requires more than 1 file")
            log.error("%s contains only 1 file" % args.folder_name)
        elif file_path.is_dir():
            log.info("Checking directory: %s for a tile scan" % args.folder_name)
            # Add a trailing slash if missing
            top = os.path.join(args.folder_name, '')
            meta_dict = extract_meta(args.folder_name)

            return meta_dict
        else:
            log.error("directory %s does not contain any file" % args.folder_name)
    else:
        log.error("  *** %s is not a supported file format" % args.file_format)
        log.error("supported data formats are: %s, %s, %s, %s" % tuple(KNOWN_FORMATS))


def tile(args):
    meta_dict = extract(args)

    sample_x       = 'measurement_instrument_sample_motor_stack_setup_sample_x'
    sample_y       = 'measurement_instrument_sample_motor_stack_setup_sample_y'
    resolution     = 'measurement_instrument_detection_system_objective_resolution'
    full_file_name = 'measurement_sample_full_file_name'

    log.warning('tile file sorted')
    x_sorted = {k: v for k, v in sorted(meta_dict.items(), key=lambda item: item[1][sample_x])}
    y_sorted = {k: v for k, v in sorted(x_sorted.items(), key=lambda item: item[1][sample_y])}
    
    first_key = list(y_sorted.keys())[0]
    second_key = list(y_sorted.keys())[1]
    # print(y_sorted)
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
            # key = [str(tile_index_x),s tr(tile_index_y)]
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

    proj0, flat0, dark0, theta0, _ = dxchange.read_dx(grid[0,0], proj=(0, 1))
    data_shape = [len(theta0),*proj0.shape[1:]]

    return meta_dict, grid, data_shape, proj0.dtype, x_shift, y_shift



# #####################################################################################
def read_hdf_meta(fname, add_shape=True):
    """
    Get the tree view of a hdf/nxs file.

    Parameters
    ----------
    file_path : str
        Path to the file.
    add_shape : bool
        Including the shape of a dataset to the tree if True.

    Returns
    -------
    meta : dict
        A dictionary containing all hdf file meta data
    tree : list
        A list of string containing the hdf file tree structure
    """

    tree = deque()
    meta = {}

    with h5py.File(fname, 'r') as hdf_object:
        _extract_hdf(tree, meta, hdf_object, add_shape=add_shape)
    # for entry in tree:
    #     print(entry)
    return tree, meta

def _get_subgroups(hdf_object, key=None):
    """
    Supplementary method for building the tree view of a hdf5 file.
    Return the name of subgroups :cite:`Vo:21`.
    """
    list_group = []
    if key is None:
        for group in hdf_object.keys():
            list_group.append(group)
        if len(list_group) == 1:
            key = list_group[0]
        else:
            key = ""
    else:
        if key in hdf_object:
            try:
                obj = hdf_object[key]
                if isinstance(obj, h5py.Group):
                    for group in hdf_object[key].keys():
                        list_group.append(group)
            except KeyError:
                pass
    if len(list_group) > 0:
        list_group = sorted(list_group)
    return list_group, key

def _add_branches(tree, meta, hdf_object, key, key1, index, last_index, prefix,
                  connector, level, add_shape):
    """
    Supplementary method for building the tree view of a hdf5 file.
    Add branches to the tree :cite:`Vo:21`.
    """
    shape = None
    key_comb = key + "/" + key1
    if add_shape is True:
        if key_comb in hdf_object:
            try:
                obj = hdf_object[key_comb]
                if isinstance(obj, h5py.Dataset):
                    shape = str(obj.shape)
                    if obj.shape[0]==1:
                        s = obj.name.split('/')
                        name = "_".join(s)[1:]
                        # print(s)
                        # print(name)
                        value = obj[()][0]
                        attr = obj.attrs.get('units')
                        if attr != None:
                            attr = attr.decode('UTF-8')
                            # log.info(">>>>>> %s: %s %s" % (obj.name, value, attr))
                        if  (value.dtype.kind == 'S'):
                            value = value.decode(encoding="utf-8")
                            # log.info(">>>>>> %s: %s" % (obj.name, value))
                        meta.update( {name : [value, attr] } )
            except KeyError:
                shape = str("-> ???External-link???")
    if shape is not None:
        tree.append(f"{prefix}{connector} {key1} {shape}")
    else:
        tree.append(f"{prefix}{connector} {key1}")
    if index != last_index:
        prefix += PIPE_PREFIX
    else:
        prefix += SPACE_PREFIX
    _extract_hdf(tree, meta, hdf_object, prefix=prefix, key=key_comb,
                    level=level, add_shape=add_shape)

def _extract_hdf(tree, meta, hdf_object, prefix="", key=None, level=0,
                    add_shape=True):
    """
    Supplementary method for building the tree view of a hdf5 file.
    Create the tree body :cite:`Vo:21`..
    """
    entries, key = _get_subgroups(hdf_object, key)
    num_ent = len(entries)
    last_index = num_ent - 1
    level = level + 1
    if num_ent > 0:
        if last_index == 0:
            key = "" if level == 1 else key
            if num_ent > 1:
                connector = PIPE
            else:
                connector = ELBOW if level > 1 else ""
            _add_branches(tree, meta, hdf_object, key, entries[0], 0, 0, prefix,
                          connector, level, add_shape)
        else:
            for index, key1 in enumerate(entries):
                connector = ELBOW if index == last_index else TEE
                if index == 0:
                    tree.append(prefix + PIPE)
                _add_branches(tree, meta, hdf_object, key, key1, index, last_index,
                              prefix, connector, level, add_shape)

