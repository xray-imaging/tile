"""Various utility functions."""
import os
import glob
import math
import argparse
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