# LICENSE
#
# This file is part of pSysmon.
#
# If you use pSysmon in any program or publication, please inform and
# acknowledge its author Stefan Mertl (stefan@mertl-research.at).
#
# pSysmon is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
The pSysmon main program.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3 
    (http://www.gnu.org/licenses/gpl-3.0.html)
'''

import matplotlib as mpl
mpl.rcParams['backend'] = 'WXAgg'

import psysmon
from psysmon.core.waveclient import PsysmonDbWaveClient, EarthwormWaveclient
import psysmon.core.base as psybase
import sys
import shelve
import wx
import logging
import os

class ExecutionFrame(wx.Frame):

    def __init__(self, collection):
        wx.Frame.__init__(self, None, wx.ID_ANY, 'Execution frame')
        #wx.CallAfter(collection.execute, 'halloooo')



if __name__ == "__main__":

    # The process name and the temp. file are passes as arguments. 
    filename = sys.argv[1]
    proc_name = sys.argv[2]

    # Get the execution parameters from the ced file.
    db = shelve.open(filename)
    package_directories = db['package_directories']
    sys.path.extend(package_directories)
    project = db['project']
    collection = db['collection']
    waveclients = db['waveclient']
    project_server = db['project_server']
    db.close()

    #logfileName = os.path.join(tempfile.gettempdir(), proc_name + '.log')
    logfileName = os.path.join(project.tmpDir, proc_name + '.log')

    logger = logging.getLogger('psysmon')
    logger.setLevel(psysmon.logConfig['level'])
    logger.addHandler(psysmon.getLoggerFileHandler(logfileName))
    #logger.addHandler(psysmon.getLoggerHandler())

    logger.info('Starting process %s', proc_name)
    logger.info('Loading data from file %s', filename)

    logger.info('Project: %s', project)
    logger.info('Collection: %s', collection)

    logger.info('Executing collection %s of project %s.', collection, project)

    psyBaseDir = os.path.abspath(psysmon.__file__)
    psyBaseDir = os.path.dirname(psyBaseDir)
    psyBase = psybase.Base(psyBaseDir, project_server = project_server)
    psyBase.project = project
    psyBase.process_meta['name'] = proc_name
    psyBase.process_meta['pid'] = os.getpid()


    # Reinitialize the project.
    project.connect2Db()
    project.loadDatabaseStructure(psyBase.packageMgr.packages)
    project.load_geometry_inventory()

    for curName, curMode, curAttributes in waveclients:
        if curMode == 'PsysmonDbWaveClient':
            waveclient = PsysmonDbWaveClient(curName, project)
        elif curMode == 'EarthwormWaveclient':
            waveclient = EarthwormWaveclient(curName, **curAttributes)
        else:
            waveclient = None

        if waveclient != None:
            project.addWaveClient(waveclient)

    collection.set_project(project)
    collection.createNodeLoggers()

    project.psybase = psyBase
    logger.debug('psyBase: %s', project.psybase)

    collection.setDataShelfFile(filename)
    try:
        collection.execute()
        logger.info('Finished the execution. Cleaning up....')
    except:
        logger.exception("Failed to execute the collection successfully.")
    finally:
        logger.info('Unregistering the exported data from the project server.')
        psyBase.project_server.unregister_data(uri = collection.rid, recursive = True)
        logger.info('Deleting data file %s.', filename)
        os.remove(filename)

