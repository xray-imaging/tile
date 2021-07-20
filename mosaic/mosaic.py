import os
import re
import sys
import json
import argparse
import datetime
import numpy as np

from pathlib import Path
from mosaic import log
from mosaic import config
from mosaic import fileio


KNOWN_FORMATS = ['dx', 'aps2bm', 'aps7bm', 'aps32id']


def extract(args):

    log.warning('checking mosaic files ...')
    file_path = Path(args.file_name)

    if str(args.file_format) in KNOWN_FORMATS:

        if file_path.is_file(): #or len(next(os.walk(file_path))[2]) == 1:
            log.error("A mosaic dataset requires more than 1 file")
            log.error("%s contains only 1 file" % args.file_name)
        elif file_path.is_dir():
            log.info("Checking directory: %s for a mosaic scan" % args.file_name)
            # Add a trailing slash if missing
            top = os.path.join(args.file_name, '')
            meta_dict = fileio.extract_meta(args.file_name)

            return meta_dict

        else:
            log.error("directory %s does not contain any file" % args.file_name)
    else:
        log.error("  *** %s is not a supported file format" % args.file_format)
        log.error("supported data formats are: %s, %s, %s, %s" % tuple(KNOWN_FORMATS))


def sort(args):

    meta_dict = extract(args)

    log.warning('mosaic file sorted')
    x_sorted = {k: v for k, v in sorted(meta_dict.items(), key=lambda item: item[1]['sample_x'])}
    y_sorted = {k: v for k, v in sorted(x_sorted.items(), key=lambda item: item[1]['sample_y'])}

    return y_sorted

def keyshift(dictionary, key, diff):
    if key in dictionary:
        token = object()
        keys = [token]*(diff*-1) + sorted(dictionary) + [token]*diff
        newkey = keys[keys.index(key)+diff]
        if newkey is token:
            return None
            # print None
        else:
            return newkey
            print ({newkey: dictionary[newkey]})
    # else:
    #     print 'Key not found'

def tile(args):
    meta_dict = extract(args)

    log.warning('mosaic file sorted')
    x_sorted = {k: v for k, v in sorted(meta_dict.items(), key=lambda item: item[1]['sample_x'])}
    y_sorted = {k: v for k, v in sorted(x_sorted.items(), key=lambda item: item[1]['sample_y'])}
    
    first_key = list(y_sorted.keys())[0]
    second_key = list(y_sorted.keys())[1]
    # print(y_sorted)
    tile_index_x = 0
    tile_index_y = 0
    x_start = y_sorted[first_key]['sample_x'][0] - 1
    y_start = y_sorted[first_key]['sample_y'][0] - 1 

    x_shift = int((1000*(x_sorted[second_key]['sample_x'][0]- x_sorted[first_key]['sample_x'][0]))/y_sorted[first_key]['resolution'][0])

    tile_dict = {}

    for k, v in y_sorted.items():

        if meta_dict[k]['sample_x'][0] > x_start:
            key = 'x' + str(tile_index_x) + 'y' + str(tile_index_y)
            # key = [str(tile_index_x),s tr(tile_index_y)]
            log.info('%s: x = %f; y = %f, file name = %s, original file name = %s' % (key, meta_dict[k]['sample_x'][0], meta_dict[k]['sample_y'][0], k, meta_dict[k]['full_file_name'][0]))
            tile_index_x = tile_index_x + 1
            x_start = meta_dict[k]['sample_x'][0]
            first_y = meta_dict[k]['sample_y'][0]
        else:
            tile_index_x = 0
            tile_index_y = tile_index_y + 1
            key = 'x' + str(tile_index_x) + 'y' + str(tile_index_y)
            log.info('%s: x = %f; y = %f, file name = %s, original file name = %s' % (key, meta_dict[k]['sample_x'][0], meta_dict[k]['sample_y'][0], k, meta_dict[k]['full_file_name'][0]))
            tile_index_x = tile_index_x + 1
            x_start = y_sorted[first_key]['sample_x'][0] - 1
            y_shift = int((1000*(meta_dict[k]['sample_y'][0] - first_y)/y_sorted[first_key]['resolution'][0]))

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

    return tile_dict, grid, x_shift, y_shift
