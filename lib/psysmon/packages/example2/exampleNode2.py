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

from psysmon.core.packageNodes import CollectionNode
from psysmon.core.gui import PSysmonApp
import wx

class ExampleNode2(CollectionNode):
    '''
    An example node.

    This node demonstrates the usage of pSysmon collection nodes.
    The node inherints from the class :class:`~psysmon.core.base.CollectionNode`.

    The creator of the node has to define the edit and the execute method.

    The inherited log method can be used to display messages in the pSysmon 
    log area.

    In the execute method, accessing output of the previous node in the collection 
    is demonstrated. The output has been set by the example node.
    '''

    name = 'example node 2'
    mode = 'editable'
    category = 'Example'
    tags = ['stable', 'example']

    def __init__(self, **args):
        CollectionNode.__init__(self, **args)
        self.options = {}

    def edit(self):
        msg = "Editing the node %s." % self.name


    def execute(self, prevModuleOutput={}):
        self.logger.debug("Executing the node %s." % self.name)

        requiredData = self.requireData(origin = 'example node')

        app = PSysmonApp()

        dlg = wx.MessageDialog(None, str(requiredData),
                               'Echo Echo',
                               wx.OK | wx.ICON_INFORMATION
                               #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                               )
        dlg.ShowModal()
        dlg.Destroy()
        app.MainLoop()

        #self.logger.debug('requiredData: %s', requiredData)
        #print "Unpickled Data: %s" % requiredData['test_data']


