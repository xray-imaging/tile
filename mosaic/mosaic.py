import os
import sys
import argparse
import datetime

import pandas as pd

from pathlib import Path
from mosaic import log
from mosaic import config


KNOWN_FORMATS = ['dx', 'aps2bm', 'aps7bm', 'aps32id']


def sort(args):

    log.warning('reconstruction start')
    file_path = Path(args.file_name)

    if str(args.file_format) in KNOWN_FORMATS:

        if file_path.is_file():
            log.error("single file: %s" % args.file_name)
            config.update_config(args)
        elif file_path.is_dir():
            log.info("Checking directory: %s for a mosaic scan" % args.file_name)
            # Add a trailing slash if missing
            top = os.path.join(args.file_name, '')
            h5_file_list = list(filter(lambda x: x.endswith(('.h5', '.hdf', 'hdf5')), os.listdir(top)))
            if (h5_file_list):
                h5_file_list.sort()
                log.info("found: %s" % h5_file_list) 
                index=0
                for fname in h5_file_list:
                    args.file_name = top + fname
                    log.warning("  *** file %d/%d;  %s" % (index, len(h5_file_list), fname))
                    index += 1
                    # recon.rec(args)
                    config.update_config(args)
                log.warning('reconstruction end')
            else:
                log.error("directory %s does not contain any file" % args.file_name)

    else:
        log.error("  *** %s is not a supported file format" % args.file_format)
        log.error("supported data formats are: %s, %s, %s, %s" % tuple(KNOWN_FORMATS))