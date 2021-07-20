"""Various utility functions."""
import re
import os
import glob
import math
import argparse
import numpy as np

from collections import OrderedDict

from mosaic import log

def tupleize(num_items=None, conv=float, dtype=tuple):
    """Convert comma-separated string values to a *num-items*-tuple of values converted with
    *conv*.
    """
    def split_values(value):
        """Convert comma-separated string *value* to a tuple of numbers."""
        try:
            result = dtype([conv(x) for x in value.split(',')])
        except:
            raise argparse.ArgumentTypeError('Expect comma-separated tuple')

        if num_items and len(result) != num_items:
            raise argparse.ArgumentTypeError('Expected {} items'.format(num_items))

        return result

    return split_values

def positive_int(value):
    """Convert *value* to an integer and make sure it is positive."""
    result = int(value)
    if result < 0:
        raise argparse.ArgumentTypeError('Only positive integers are allowed')

    return result

def get_index(file_list):
    '''
    Get tile indices.
    :param file_list: list of files.
    :param pattern: pattern of naming. For files named with x_*_y_*, use
                    pattern=0. For files named with y_*_x_*, use pattern=1.
    :return: 
    '''
    regex = re.compile(r".+_x(\d+)_y(\d+).+")
    ind_buff = [m.group(1, 2) for l in file_list for m in [regex.search(l)] if m]

    return np.asarray(ind_buff).astype('int')