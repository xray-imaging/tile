import os
import sys
import json
import argparse
import datetime

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
