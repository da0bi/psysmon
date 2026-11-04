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

        # Accelerators for shortcuts not bound to a menu item.
        handler = ft.partial(self.on_time_advance, step = 100)
        self.shortcuts['advance_100'] = {'accelerator_string': 'Right',
                                         'handler': handler}

        handler = ft.partial(self.on_time_advance, step = 25)
        self.shortcuts['advance_25'] = {'accelerator_string': 'SHIFT+Right',
                                        'handler': handler}

        handler = ft.partial(self.on_time_advance, step = 10)
        self.shortcuts['advance_10'] = {'accelerator_string': 'CTRL+Right',
                                        'handler': handler}

        handler = ft.partial(self.on_time_advance, step = 1)
        self.shortcuts['advance_1'] = {'accelerator_string': 'ALT+Right',
                                       'handler': handler}

        handler = ft.partial(self.on_time_regress, step = 100)
        self.shortcuts['regress_100'] = {'accelerator_string': 'Left',
                                         'handler': handler}

        handler = ft.partial(self.on_time_regress, step = 25)
        self.shortcuts['regress_25'] = {'accelerator_string': 'SHIFT+Left',
                                        'handler': handler}

        handler = ft.partial(self.on_time_regress, step = 10)
        self.shortcuts['regress_10'] = {'accelerator_string': 'CTRL+Left',
                                        'handler': handler}

        handler = ft.partial(self.on_time_regress, step = 1)
        self.shortcuts['regress_1'] = {'accelerator_string': 'ALT+Left',
                                       'handler': handler}

        # Zoom in shortcuts (Up arrow)
        handler = ft.partial(self.on_zoom_in, ratio = 20)
        self.shortcuts['zoom_in_20'] = {'accelerator_string': 'Up',
                                        'handler': handler}

        handler = ft.partial(self.on_zoom_in, ratio = 25)
        self.shortcuts['zoom_in_25'] = {'accelerator_string': 'SHIFT+Up',
                                        'handler': handler}

        handler = ft.partial(self.on_zoom_in, ratio = 10)
        self.shortcuts['zoom_in_10'] = {'accelerator_string': 'CTRL+Up',
                                        'handler': handler}

        handler = ft.partial(self.on_zoom_in, ratio = 1)
        self.shortcuts['zoom_in_1'] = {'accelerator_string': 'ALT+Up',
                                       'handler': handler}

        # Zoom out shortcuts (Down arrow)
        handler = ft.partial(self.on_zoom_out, ratio = 20)
        self.shortcuts['zoom_out_20'] = {'accelerator_string': 'Down',
                                         'handler': handler}

        handler = ft.partial(self.on_zoom_out, ratio = 25)
        self.shortcuts['zoom_out_25'] = {'accelerator_string': 'SHIFT+Down',
                                         'handler': handler}

        handler = ft.partial(self.on_zoom_out, ratio = 10)
        self.shortcuts['zoom_out_10'] = {'accelerator_string': 'CTRL+Down',
                                         'handler': handler}

        handler = ft.partial(self.on_zoom_out, ratio = 1)
        self.shortcuts['zoom_out_1'] = {'accelerator_string': 'ALT+Down',
                                        'handler': handler}

        # Add the plugin preferences.
        pref_page = self.pref_manager.add_page('Preferences')
        resp_group = pref_page.add_group('response')

        item = preferences_manager.IntegerSpinPrefItem(name = 'zoom ratio',
                                                       value = 20,
                                                       limit = (1, 99))
        resp_group.add_item(item)


    def getHooks(self):
        hooks = {}

        #hooks['button_press_event'] = self.onButtonPress
        #hooks['button_release_event'] = self.onButtonRelease

        return hooks


    def on_time_advance(self, evt, step):
        ''' Advance displayed time.
        '''
        self.parent.advanceTimePercentage(step = step)


    def on_time_regress(self, evt, step):
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

        # Up arrow shortcuts (zoom in)
        self.parent.shortcut_manager.add_shortcut(origin_rid = self.rid,
                                                  key_combination = ('WXK_UP',),
                                                  action = self.on_zoom_in)
        self.parent.shortcut_manager.add_shortcut(origin_rid = self.rid,
                                                  key_combination = ('WXK_SHIFT', 'WXK_UP'),
                                                  action = self.parent.shrinkTimePeriod,
                                                  action_kwargs = {'ratio': 25})
        self.parent.shortcut_manager.add_shortcut(origin_rid = self.rid,
                                                  key_combination = ('WXK_COMMAND', 'WXK_UP'),
                                                  action = self.parent.shrinkTimePeriod,
                                                  action_kwargs = {'ratio': 10})
        self.parent.shortcut_manager.add_shortcut(origin_rid = self.rid,
                                                  key_combination = ('WXK_ALT', 'WXK_UP'),
                                                  action = self.parent.shrinkTimePeriod,
                                                  action_kwargs = {'ratio': 1})

        # Down arrow shortcuts (zoom out)
        self.parent.shortcut_manager.add_shortcut(origin_rid = self.rid,
                                                  key_combination = ('WXK_DOWN',),
                                                  action = self.on_zoom_out)
        self.parent.shortcut_manager.add_shortcut(origin_rid = self.rid,
                                                  key_combination = ('WXK_SHIFT', 'WXK_DOWN'),
                                                  action = self.parent.growTimePeriod,
                                                  action_kwargs = {'ratio': 25})
        self.parent.shortcut_manager.add_shortcut(origin_rid = self.rid,
                                                  key_combination = ('WXK_COMMAND', 'WXK_DOWN'),
                                                  action = self.parent.growTimePeriod,
                                                  action_kwargs = {'ratio': 10})
        self.parent.shortcut_manager.add_shortcut(origin_rid = self.rid,
                                                  key_combination = ('WXK_ALT', 'WXK_DOWN'),
                                                  action = self.parent.growTimePeriod,
                                                  action_kwargs = {'ratio': 1})

        # Right arrow shortcuts (advance time)
        self.parent.shortcut_manager.add_shortcut(origin_rid = self.rid,
                                                  key_combination = ('WXK_RIGHT',),
                                                  action = self.parent.advanceTime)
        self.parent.shortcut_manager.add_shortcut(origin_rid = self.rid,
                                                  key_combination = ('WXK_SHIFT', 'WXK_RIGHT'),
                                                  action = self.parent.advanceTimePercentage,
                                                  action_kwargs = {'step': 25})
        self.parent.shortcut_manager.add_shortcut(origin_rid = self.rid,
                                                  key_combination = ('WXK_COMMAND', 'WXK_RIGHT'),
                                                  action = self.parent.advanceTimePercentage,
                                                  action_kwargs = {'step': 10})
        self.parent.shortcut_manager.add_shortcut(origin_rid = self.rid,
                                                  key_combination = ('WXK_ALT', 'WXK_RIGHT'),
                                                  action = self.parent.advanceTimePercentage,
                                                  action_kwargs = {'step': 1})

        # Left arrow shortcuts (regress time)
        self.parent.shortcut_manager.add_shortcut(origin_rid = self.rid,
                                                  key_combination = ('WXK_LEFT',),
                                                  action = self.parent.decreaseTime)
        self.parent.shortcut_manager.add_shortcut(origin_rid = self.rid,
                                                  key_combination = ('WXK_SHIFT', 'WXK_LEFT'),
                                                  action = self.parent.decreaseTimePercentage,
                                                  action_kwargs = {'step': 25})
        self.parent.shortcut_manager.add_shortcut(origin_rid = self.rid,
                                                  key_combination = ('WXK_COMMAND', 'WXK_LEFT'),
                                                  action = self.parent.decreaseTimePercentage,
                                                  action_kwargs = {'step': 10})
        self.parent.shortcut_manager.add_shortcut(origin_rid = self.rid,
                                                  key_combination = ('WXK_ALT', 'WXK_LEFT'),
                                                  action = self.parent.decreaseTimePercentage,
                                                  action_kwargs = {'step': 1})


    def deactivate(self):
        ''' Deactivate the plugin.
        '''
        InteractivePlugin.deactivate(self)


