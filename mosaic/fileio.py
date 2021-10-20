import os
import re
import numpy as np
import dxchange.reader as dxreader
import dxchange

from pathlib import Path

from mosaic import log

KNOWN_FORMATS = ['dx', 'aps2bm', 'aps7bm', 'aps32id']
SHIFTS_FILE_HEADER = '# Array shape: '


def service_fnames(mosaic_fname):

    mosaic_folder = os.path.dirname(mosaic_fname)
    # shifts_h_fname = os.path.join(mosaic_folder, 'shifts_h.npy')
    # shifts_v_fname = os.path.join(mosaic_folder, 'shifts_v.npy')
    # multipliers_fname = os.path.join(mosaic_folder, 'multipliers.npy')
    shifts_h_fname = os.path.join(mosaic_folder, 'shifts_h.txt')
    shifts_v_fname = os.path.join(mosaic_folder, 'shifts_v.txt')
    multipliers_fname = os.path.join(mosaic_folder, 'multipliers.txt')

    return shifts_h_fname, shifts_v_fname, multipliers_fname

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
        log.error("run -- $ mosaic shift -- first")
        ##FDC shall we return an arrays with zeros? to handle vertial/horizontal scans?
    return new_data

def extract_meta(fname):

    # list_to_extract = ('sample_x', 'sample_y', 'experimenter_name', 'full_file_name',  'sample_in_x', 'sample_in_y', 'proposal', 'sample_name', 'sample_y', 'camera_objective', 'resolution', 'energy', 'camera_distance', 'exposure_time', 'num_angles', 'scintillator_type', 'model')
    list_to_extract = ('sample_x', 'sample_y', 'full_file_name', 'sample_name', 'resolution', 'camera_objective', 'num_angles', )

    if os.path.isdir(fname):
        # Add a trailing slash if missing
        top = os.path.join(fname, '')
        h5_file_list = list(filter(lambda x: x.endswith(('.h5', '.hdf')), os.listdir(top)))
        h5_file_list.sort()
        meta_dict = {}
        file_counter=0
        for fname in h5_file_list:
            h5fname = top + fname
            sub_dict = extract_dict(h5fname, list_to_extract, index=file_counter)
            meta_dict.update(sub_dict)
            file_counter+=1
    else:
        log.error('No valid HDF5 file(s) fund')
        return None

    return meta_dict

def extract_dict(fname, list_to_extract, index=0):

    meta = dxreader.read_dx_meta(fname, label1='/measurement/instrument/sample_motor_stack/setup/', label2='/measurement/') 
    sub_dict = {fname : meta}

    return sub_dict

def extract(args):

    log.warning('checking mosaic files ...')
    file_path = Path(args.folder_name)

    if str(args.file_format) in KNOWN_FORMATS:

        if file_path.is_file(): #or len(next(os.walk(file_path))[2]) == 1:
            log.error("A mosaic dataset requires more than 1 file")
            log.error("%s contains only 1 file" % args.folder_name)
        elif file_path.is_dir():
            log.info("Checking directory: %s for a mosaic scan" % args.folder_name)
            # Add a trailing slash if missing
            top = os.path.join(args.folder_name, '')
            meta_dict = extract_meta(args.folder_name)

            return meta_dict

        else:
            log.error("directory %s does not contain any file" % args.folder_name)
    else:
        log.error("  *** %s is not a supported file format" % args.file_format)
        log.error("supported data formats are: %s, %s, %s, %s" % tuple(KNOWN_FORMATS))


def sort(args):

    meta_dict = extract(args)

    log.warning('mosaic file sorted')
    x_sorted = {k: v for k, v in sorted(meta_dict.items(), key=lambda item: item[1]['sample_x'])}
    y_sorted = {k: v for k, v in sorted(x_sorted.items(), key=lambda item: item[1]['sample_y'])}

    return y_sorted

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
    y_shift = 0
    
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

    proj0, flat0, dark0, theta0, _ = dxchange.read_dx(grid[0,0], proj=(0, 1))
    data_shape = [len(theta0),*proj0.shape[1:]]

    # print(f'{x_shift=},{y_shift=}')
    return tile_dict, grid, data_shape, x_shift, y_shift
