'''
Created on May 17, 2011

@author: Stefan Mertl
'''

import unittest
import psysmon
import logging
import os
from psysmon.core.test_util import create_psybase
from psysmon.core.test_util import create_full_project
from psysmon.core.test_util import drop_project_database_tables
from psysmon.core.test_util import remove_project_filestructure
import psysmon.core.gui as psygui


class TracedisplayTestCase(unittest.TestCase):
    """
    Test suite for psysmon.packages.geometry.editGeometry.EditGeometryDlg
    """
    @classmethod
    def setUpClass(cls):
        cls.psybase = create_psybase()
        create_full_project(cls.psybase)
        cls.project = cls.psybase.project
        print "In setUpClass...\n"


    @classmethod
    def tearDownClass(cls):
        drop_project_database_tables(cls.project)
        remove_project_filestructure(cls.project)
        os.removedirs(cls.project.base_dir)
        print "....in tearDownClass.\n"


    def setUp(self):
        # Configure the logger.
        logger = logging.getLogger('psysmon')
        logger.setLevel('DEBUG')
        logger.addHandler(psysmon.getLoggerHandler())


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
        self.node.execute()
        self.app.MainLoop()



def suite():
    # return unittest.TestSuite(map(EditGeometryDlgTestCase, tests))
    return unittest.makeSuite(TracedisplayTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

