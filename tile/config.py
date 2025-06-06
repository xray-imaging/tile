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
import sys
import pathlib
import argparse
import configparser
from collections import OrderedDict
from pathlib import Path

from tile import log
from tile import util

LOGS_HOME = Path.home()/'logs'
CONFIG_FILE_NAME = os.path.join(str(pathlib.Path.home()), 'tile.conf')

SECTIONS = OrderedDict()

SECTIONS['general'] = {
    'config': {
        'default': CONFIG_FILE_NAME,
        'type': str,
        'help': "File name of configuration",
        'metavar': 'FILE'},
    'logs-home': {
        'default': LOGS_HOME,
        'type': str,
        'help': "Log file directory",
        'metavar': 'FILE'},
    'verbose': {
        'default': False,
        'help': 'Verbose output',
        'action': 'store_true'},
        }

SECTIONS['file-io'] = {
    'folder-name': {
        'default': '.',
        'type': Path,
        'help': "Name of the last used directory containing multiple hdf files",
        'metavar': 'PATH'},
    'tmp-file-name': {
        'default': '/tile/tmp.h5',
        'type': str,
        'help': "Default output file name",
        'metavar': 'FILE'},
    'tile-file-name': {
        'default': 'tile.h5',
        'type': str,
        'help': "Default stitched file name",
        'metavar': 'FILE'},
    'file-format': {
        'default': 'dx',
        'type': str,
        'help': "see from https://dxchange.readthedocs.io/en/latest/source/demo.html",
        'choices': ['dx', 'aps2bm', 'aps7bm', 'aps32id']},
    'binning': {
        'type': util.positive_int,
        'default': 0,
        'help': "Reconstruction binning factor as power(2, choice)",
        'choices': [0, 1, 2, 3]},
    'sample-x': {     
        'type': str,
        'default': '/measurement/instrument/sample_motor_stack/setup/x',
        'help': "Location in the hdf tomography layout where to find the tile x position (mm)"},    
    'sample-y': {     
        'type': str,
        'default': '/measurement/instrument/sample_motor_stack/setup/y',
        'help': "Location in the hdf tomography layout where to find the tile y position (mm)"},    
    'resolution': {     
        'type': str,
        'default': '/measurement/instrument/detection_system/objective/resolution',
        'help': "Location in the hdf tomography layout where to find the image resolution (um)"},    
    'full_file_name': {     
        'type': str,
        'default': '/measurement/sample/file/full_name',
        'help': "Location in the hdf tomography layout where to find the full file name"},
    'step-x': {
        'default': 0,
        'type': float,
        'help': 'When greater than 0, it is used to manually overide the sample x step size stored in the hdf file'},  
    'recon': {
        'default': 'True',
        'type': str,
        'help': 'Reconstruct slice for manual stitching or not'},  
        }

SECTIONS['stitch'] = {
    'x-shifts': {
        'default': 'None',
        'type': str,
        'help': "Projection pairs to find rotation axis. Each second projection in a pair will be flipped and used to find shifts from the first element in a pair. The shifts are used to calculate the center.  Example [0,1499] for a 180 deg scan, or [0,1499,749,2249] for 360, etc.",},            
    'start-proj': {
        'default': 0,
        'type': int,
        'help': "Start projection"},
    'end-proj': {
        'default': -1,
        'type': int,
        'help': "End projection"},   
    'nproj-per-chunk': {     
        'default': 64,
        'type': int,        
        'help': "Number of of projections for simultaneous processing",},    
    }    

SECTIONS['center'] = {
    'nsino': {
        'default': 0.5,
        'type': float,
        'help': 'Location of the sinogram used for slice reconstruction and find axis (0 top, 1 bottom)'},
    'nprojection': {
        'default': 0.5,
        'type': float,
        'help': 'Location of the projection used for testing shifts between tiles (0 top, 1 bottom)'},    
    'center-search-width': {
        'type': float,
        'default': 10.0,
        'help': "+/- center search width (pixel). "},
    'center-search-step': {
        'type': float,
        'default': 0.5,
        'help': "+/- center search step (pixel). "},
    'rotation-axis': {
        'default': -1.0,
        'type': float,
        'help': "Location of rotation axis, using -1 automatically calculated the center of the horizontally sticked projections"},
    'recon-engine': {     
        'type': str,
        'default': 'tomopy',
        'help': "Reconstruction engine (tomopy or tomocupy). ",},    
    'reverse-grid': {
        'type': str,
        'default': 'False',
        'help': 'Reverse grid datasets order',},
    'reverse-step': {
        'type': str,
        'default': 'False',
        'help': 'Reverse step in x',},
    'end-column': {
        'type': int,
        'default': -1,
        'help': 'End column in x',
    }
}


SECTIONS['shift'] = {
    'shift-search-width': {
        'type': int,
        'default': 20,
        'help': "+/- center search width (pixel). "},
    'shift-search-step': {
        'type': int,
        'default': 1,
        'help': "+/- center search step (pixel). "},
    'nsino-per-chunk': {     
        'type': int,
        'default': 8,
        'help': "Number of sinograms per chunk. Use larger numbers with computers with larger memory. ",},    
    }

INFO_PARAMS   = ('file-io',)
CENTER_PARAMS = ('file-io', 'center')
SHIFT_PARAMS  = ('file-io', 'center', 'shift')
STITCH_PARAMS = ('file-io', 'center', 'stitch')
ALL_PARAMS    = ('file-io', 'center', 'shift', 'stitch')

NICE_NAMES = ('General', 'File IO', 'Center', 'Shift', 'Stitch')

def get_config_name():
    """Get the command line --config option."""
    name = CONFIG_FILE_NAME
    for i, arg in enumerate(sys.argv):
        if arg.startswith('--config'):
            if arg == '--config':
                return sys.argv[i + 1]
            else:
                name = sys.argv[i].split('--config')[1]
                if name[0] == '=':
                    name = name[1:]
                return name

    return name

def parse_known_args(parser, subparser=False):
    """
    Parse arguments from file and then override by the ones specified on the
    command line. Use *parser* for parsing and is *subparser* is True take into
    account that there is a value on the command line specifying the subparser.
    """
    if len(sys.argv) > 1:
        subparser_value = [sys.argv[1]] if subparser else []
        config_values = config_to_list(config_name=get_config_name())
        values = subparser_value + config_values + sys.argv[1:]
        #print(subparser_value, config_values, values)
    else:
        values = ""

    return parser.parse_known_args(values)[0]
    

def config_to_list(config_name=CONFIG_FILE_NAME):
    """
    Read arguments from config file and convert them to a list of keys and
    values as sys.argv does when they are specified on the command line.
    *config_name* is the file name of the config file.
    """
    result = []
    config = configparser.ConfigParser()

    if not config.read([config_name]):
        return []

    for section in SECTIONS:
        for name, opts in ((n, o) for n, o in SECTIONS[section].items() if config.has_option(section, n)):
            value = config.get(section, name)

            if value != '' and value != 'None':
                action = opts.get('action', None)

                if action == 'store_true' and value == 'True':
                    # Only the key is on the command line for this action
                    result.append('--{}'.format(name))

                if not action == 'store_true':
                    if opts.get('nargs', None) == '+':
                        result.append('--{}'.format(name))
                        result.extend((v.strip() for v in value.split(',')))
                    else:
                        result.append('--{}={}'.format(name, value))

    return result


class Params(object):
    def __init__(self, sections=()):
        self.sections = sections + ('general', )

    def add_parser_args(self, parser):
        for section in self.sections:
            for name in sorted(SECTIONS[section]):
                opts = SECTIONS[section][name]
                parser.add_argument('--{}'.format(name), **opts)

    def add_arguments(self, parser):
        self.add_parser_args(parser)
        return parser

    def get_defaults(self):
        parser = argparse.ArgumentParser()
        self.add_arguments(parser)

        return parser.parse_args('')


def write(config_file, args=None, sections=None):
    """
    Write *config_file* with values from *args* if they are specified,
    otherwise use the defaults. If *sections* are specified, write values from
    *args* only to those sections, use the defaults on the remaining ones.
    """
    config = configparser.ConfigParser()

    for section in SECTIONS:
        config.add_section(section)
        for name, opts in SECTIONS[section].items():
            if args and sections and section in sections and hasattr(args, name.replace('-', '_')):
                value = getattr(args, name.replace('-', '_'))
                if isinstance(value, list):
                    # print(type(value), value)
                    value = ', '.join(value)
            else:
                value = opts['default'] if opts['default'] is not None else ''

            prefix = '# ' if value == '' else ''

            if name != 'config':
                config.set(section, prefix + name, str(value))
    with open(config_file, 'w') as f:
        config.write(f)


def show_config(args):
    """Log all values set in the args namespace.

    Arguments are grouped according to their section and logged alphabetically
    using the DEBUG log level thus --verbose is required.
    """
    args = args.__dict__

    log.warning('tile status start')
    for section, name in zip(SECTIONS, NICE_NAMES):
        entries = sorted((k for k in args.keys() if k.replace('_', '-') in SECTIONS[section]))        
        if entries:
            log.info(name)
            for entry in entries:
                value = args[entry] if args[entry] != None else "-"
                log.info("  {:<16} {}".format(entry, value))

    log.warning('tile status end')
 
