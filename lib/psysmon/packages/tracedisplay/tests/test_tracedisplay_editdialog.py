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
from psysmon.core.test_util import create_psybase
from psysmon.core.test_util import create_full_project
from psysmon.core.test_util import drop_project_database_tables
from psysmon.core.test_util import remove_project_filestructure
from psysmon.core.test_util import clean_unittest_database
import psysmon.core.gui as psygui


class TracedisplayEditDialogTestCase(unittest.TestCase):
    """
    Test suite for psysmon.packages.geometry.editGeometry.EditGeometryDlg
    """
    @classmethod
    def setUpClass(cls):
        # Configure the logger.
        logger = logging.getLogger('psysmon')
        logger.setLevel('DEBUG')
        logger.addHandler(psysmon.getLoggerHandler())

        clean_unittest_database()

        cls.psybase = create_psybase()
        create_full_project(cls.psybase)
        cls.project = cls.psybase.project
        cls.project.dbEngine.echo = True


    @classmethod
    def tearDownClass(cls):
        drop_project_database_tables(cls.project)
        remove_project_filestructure(cls.project)
        os.removedirs(cls.project.base_dir)


    def setUp(self):
        self.app =psygui.PSysmonApp()

        nodeTemplate = self.psybase.packageMgr.getCollectionNodeTemplate('tracedisplay')
        self.node = nodeTemplate()
        self.node.project = self.project

        # Create a logger for the node.
        loggerName = __name__+ "." + self.node.__class__.__name__
        self.node.logger = logging.getLogger(loggerName)


    def tearDown(self):
        print "\n\nEs war sehr schoen - auf Wiederseh'n.\n"

    def testDlg(self):
        self.node.edit()
        self.app.MainLoop()
        pass


def suite():
    # return unittest.TestSuite(map(EditGeometryDlgTestCase, tests))
    return unittest.makeSuite(TracedisplayEditDialogTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

