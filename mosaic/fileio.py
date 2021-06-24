import os
import dxchange.reader as dxreader

from datetime import datetime

from mosaic import log
from mosaic import config

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
    # d = {index : meta}
    # print(d)
    # # print(d.items())
    # # print(sorted(d.items()))
    # exit()
    sub_dict = {fname : meta}
    # print (sub_dict[0]['sample_x'])
    # exit()
    # sub_dict = {(('%3.3d' % index) +'_' + k):v for k, v in meta.items() if k in list_to_extract}
    return sub_dict
