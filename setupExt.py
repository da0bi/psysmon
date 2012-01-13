#!/usr/bin/env python

# License
#     This file is part of Seismon.
#
#     If you use Seismon in any program or publication, please inform and
#     acknowledge its author Stefan Mertl (info@stefanmertl.com). 
# 
#     Seismon is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
# 
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
# 
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
Some setup helper functions.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3 
    (http://www.gnu.org/licenses/gpl-3.0.html)
'''

import os
import sys
from textwrap import fill

if sys.version_info[0] < 3:
    import ConfigParser as configparser
else:
    import configparser


# pSysmon build options. These can be altered using setup.cfg
options = {'displayStatus': True,
           'verbose': False}

# Get the setup.cfg file name.
setupCfg = os.environ.get('PSY_SETUPCFG', 'setup.cfg')
# Based on the contents of setup.cfg, determine the build options.
if os.path.exists(setupCfg):
    config = configparser.SafeConfigParser()
    config.read(setupCfg)

    try: options['displayStatus'] = not config.getboolean("status", "suppress")
    except: pass

    try: options['verbose'] = config.getboolean("status", "verbose")
    except: pass


if options['displayStatus']:
    def printLine(char='='):
        print(char * 76)

    def printStatus(package, status):
        initial_indent = "%22s: " % package
        indent = ' ' * 24
        print(fill(str(status), width=76,
                   initial_indent=initial_indent,
                   subsequent_indent=indent))

    def printMessage(message):
        indent = ' ' * 24 + "* "
        print(fill(str(message), width=76,
                   initial_indent=indent,
                   subsequent_indent=indent))

    def printRaw(section):
        print(section)
else:
    def printLine(*args, **kwargs):
        pass
    printStatus = printMessage = printRaw = printLine




def checkForNumpy():
    try:
        from numpy import __version__
    except ImportError:
        printStatus("numpy", "missing")
        printMessage("You must install numpy 1.1 or later to build pSysmon.")
        return False
    nn = __version__.split('.')
    if not (int(nn[0]) >= 1 and int(nn[1]) >= 1):
        if not (int(nn[0]) >= 2):
            printMessage(
               'numpy 1.1 or later is required; you have %s' %__version__)
            return False
    #module = Extension('test', [])
    #add_numpy_flags(module)
    #add_base_flags(module)

    printStatus("numpy", __version__+" (1.1 required)")
    #if not find_include_file(module.include_dirs, os.path.join("numpy", "arrayobject.h")):
        #printMessage("Could not find the headers for numpy.  You may need to install the development package.")
        #return False
    return True


def checkForMatplotlib(requiredVersion):
    rV = requiredVersion.split('.')
    for k,x in enumerate(rV):
        rV[k] = int(x)

    try:
        from matplotlib import __version__ 
    except ImportError:
        printStatus("matplotlib", "missing")
        printMessage("You must install matplotlib "+requiredVersion+" or later to build pSysmon.")
        return False

    nn = __version__.split('.')
    for k,x in enumerate(nn):
        nn[k] = int(x)

    if not (nn[0] >= rV[0] and nn[1] >= rV[1]):
        if not (nn[0] >= rV[0]+1):
            printMessage(
               'matplotlib %s or later is required; you have %s' %
               (requiredVersion, __version__))
            return False

    printStatus("matplotlib", "%s (%s required)" % (__version__, requiredVersion))
    return True



def checkForBasemap(requiredVersion):
    rV = requiredVersion.split('.')
    for k,x in enumerate(rV):
        rV[k] = int(x)

    try:
        from mpl_toolkits.basemap import __version__ 
    except ImportError:
        printStatus("mpl_toolkits.basemap", "missing")
        printMessage("You must install mpl_toolkits.basemap "+requiredVersion+" or later to build pSysmon.")
        return False

    nn = __version__.split('.')
    for k,x in enumerate(nn):
        nn[k] = int(x)

    if not (nn[0] >= rV[0] and nn[1] >= rV[1] and nn[2] >= rV[2]):
        if not (nn[0] >= rV[0]+1 or nn[0] >= rV[1]+1):
            printMessage(
               'mpl_toolkits.basemap %s or later is required; you have %s' %
               (requiredVersion, __version__))
            return False

    printStatus("basemap", "%s (%s required)" % (__version__, requiredVersion))
    return True
