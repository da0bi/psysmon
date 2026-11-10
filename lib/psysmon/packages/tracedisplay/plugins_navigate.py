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

import functools as ft
import logging

import wx

import psysmon
from psysmon.core.plugins import InteractivePlugin
from psysmon.artwork.icons import iconsBlack16 as icons
import psysmon.core.preferences_manager as preferences_manager


class Navigate(InteractivePlugin):
    '''

    '''
    nodeClass = 'TraceDisplay'

    def __init__(self):
        ''' The constructor.

        '''
        InteractivePlugin.__init__(self,
                                   name = 'navigate',
                                   category = 'tools',
                                   tags = None)
        # Create the logging logger instance.
        self.logger = psysmon.get_logger(self)

        self.icons['active'] = icons.star_icon_16
        self.cursor = wx.CURSOR_HAND

        # Set the shortcut string.
        self.accelerator_string = 'N'

        # Add the plugin preferences.
        pref_page = self.pref_manager.add_page('Preferences')
        resp_group = pref_page.add_group('response')

        item = preferences_manager.IntegerSpinPrefItem(name = 'zoom ratio',
                                                       value = 20,
                                                       limit = (1, 99))
        resp_group.add_item(item)

        item = preferences_manager.IntegerSpinPrefItem(name = 'zoom_history_steps',
                                                       value = 3,
                                                       limit = (1, 10))
        resp_group.add_item(item)


    def getHooks(self):
        hooks = {}
        return hooks


    def on_time_advance(self, evt = None, step = 100):
        ''' Advance displayed time.
        '''
        self.parent.advanceTimePercentage(step = step)


    def on_time_regress(self, evt = None, step = 100):
        ''' Regress displayed time.
        '''
        self.parent.decreaseTimePercentage(step = step)


    def on_zoom_in(self, evt = None, ratio = None):
        ''' Zoom in along the time axis.
        '''
        if ratio is None:
            ratio = self.pref_manager.get_value('zoom ratio')
        self.parent.shrinkTimePeriod(ratio = ratio)


    def on_zoom_out(self, evt = None, ratio = None):
        ''' Zoom out along the time axis.
        '''
        if ratio is None:
            ratio = self.pref_manager.get_value('zoom ratio')
        self.parent.growTimePeriod(ratio = ratio)


    def activate(self):
        ''' Activate the plugin.
        '''
        InteractivePlugin.activate(self)

        # Primary shortcuts registered for status bar tips
        self.parent.shortcut_manager.add_shortcut(origin_rid = self.rid,
                                                  key_combination = ('WXK_UP',),
                                                  action = self.on_zoom_in)
        self.parent.shortcut_manager.add_shortcut(origin_rid = self.rid,
                                                  key_combination = ('WXK_DOWN',),
                                                  action = self.on_zoom_out)
        self.parent.shortcut_manager.add_shortcut(origin_rid = self.rid,
                                                  key_combination = ('WXK_LEFT',),
                                                  action = self.parent.decreaseTime)
        self.parent.shortcut_manager.add_shortcut(origin_rid = self.rid,
                                                  key_combination = ('WXK_RIGHT',),
                                                  action = self.parent.advanceTime)
        self.parent.shortcut_manager.add_shortcut(origin_rid = self.rid,
                                                  key_combination = ('"z"',),
                                                  action = lambda: None)
        self.parent.shortcut_manager.add_shortcut(origin_rid = self.rid,
                                                  key_combination = ('Ctrl+Z',),
                                                  action = getattr(self.parent, 'undo_zoom', lambda: None))


    def deactivate(self):
        ''' Deactivate the plugin.
        '''
        InteractivePlugin.deactivate(self)


