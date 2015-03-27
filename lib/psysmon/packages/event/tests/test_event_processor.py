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

import unittest
import psysmon
import logging
import os
import copy
from psysmon.core.test_util import create_psybase
from psysmon.core.test_util import create_full_project
from psysmon.core.test_util import drop_project_database_tables
from psysmon.core.test_util import remove_project_filestructure
from psysmon.core.test_util import drop_database_tables
import psysmon.core.gui as psygui
from obspy.core.utcdatetime import UTCDateTime


class EventProcessorTestCase(unittest.TestCase):
    """
    Test suite for psysmon.packages.geometry.editGeometry.EditGeometryDlg
    """
    @classmethod
    def setUpClass(cls):
        # Configure the logger.
        logger = logging.getLogger('psysmon')
        logger.setLevel('DEBUG')
        logger.addHandler(psysmon.getLoggerHandler())

        drop_database_tables(db_dialect = 'mysql',
                              db_driver = None,
                              db_host = 'localhost',
                              db_name = 'psysmon_unit_test',
                              db_user = 'unit_test',
                              db_pwd = 'test',
                              project_name = 'unit_test')


        cls.psybase = create_psybase()
        create_full_project(cls.psybase)
        cls.project = cls.psybase.project
        cls.project.dbEngine.echo = True


    @classmethod
    def tearDownClass(cls):
        cls.psybase.stop_project_server()
        print "dropping database tables...\n"
        drop_project_database_tables(cls.project)
        print "removing temporary file structure....\n"
        remove_project_filestructure(cls.project)
        print "removing temporary base directory....\n"
        os.removedirs(cls.project.base_dir)
        print "....finished cleaning up.\n"


    def setUp(self):
        self.app =psygui.PSysmonApp()

        nodeTemplate = self.psybase.packageMgr.getCollectionNodeTemplate('event processor')
        self.node = nodeTemplate()
        self.node.project = self.project

        # Initialize the available processing nodes.
        processing_nodes = self.project.getProcessingNodes(('common', ))

        node_template = [x for x in processing_nodes if x.name == 'compute amplitude features'][0]
        node = copy.deepcopy(node_template)
        self.node.pref_manager.set_value('processing_stack', [node, ])

        # Initialize the preference items.
        self.node.pref_manager.set_value('start_time', UTCDateTime('2010-08-31T00:00:00'))
        self.node.pref_manager.set_value('end_time', UTCDateTime('2010-09-01T00:00:00'))
        self.node.pref_manager.set_value('event_catalog', 'test')
        self.node.pref_manager.set_value('stations', ['GUWA', 'SITA'])
        self.node.pref_manager.set_value('channels', ['HHE', 'HHN', 'HHZ'])

        # Create a logger for the node.
        loggerName = __name__+ "." + self.node.__class__.__name__
        self.node.logger = logging.getLogger(loggerName)


    def tearDown(self):
        self.psybase.project_server.unregister_data()
        print "\n\nEs war sehr schoen - auf Wiederseh'n.\n"

    def testDlg(self):
        self.node.execute()
        self.app.MainLoop()


def suite():
    # return unittest.TestSuite(map(EditGeometryDlgTestCase, tests))
    return unittest.makeSuite(EventProcessorTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

