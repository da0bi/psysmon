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

import logging
import wx
from obspy.core.utcdatetime import UTCDateTime
import wx.lib.mixins.listctrl as listmix
from wx.lib.stattext import GenStaticText as StaticText

import psysmon
from psysmon.core.plugins import OptionPlugin
from psysmon.core.guiBricks import PrefEditPanel
from psysmon.artwork.icons import iconsBlack16 as icons
import psysmon.core.preferences_manager as psy_pm
import psysmon.packages.event.core as ev_core


class SelectEvents(OptionPlugin):
    '''

    '''
    nodeClass = 'GraphicLocalizationNode'

    def __init__(self):
        ''' Initialize the instance.

        '''
        OptionPlugin.__init__(self,
                              name = 'select event',
                              category = 'select',
                              tags = ['event', 'select']
                             )

        # Create the logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.icons['active'] = icons.flag_icon_16

        # The events library.
        self.library = ev_core.Library(name = self.rid)

        # The currently selected event.
        self.selected_event = {}

        # The plot colors used by the plugin.
        self.colors = {}

        # Setup the pages of the preference manager.
        self.pref_manager.add_page('Select')

        item = psy_pm.DateTimeEditPrefItem(name = 'start_time',
                                           label = 'start time',
                                           group = 'detection time span',
                                           value = UTCDateTime('2015-01-01T00:00:00'),
                                           tool_tip = 'The start time of the detection time span (UTCDateTime string format YYYY-MM-DDTHH:MM:SS).')
        self.pref_manager.add_item(pagename = 'Select',
                                   item = item)


        item = psy_pm.FloatSpinPrefItem(name = 'window_length',
                                        label = 'window length [s]',
                                        group = 'detection time span',
                                        value = 3600,
                                        limit = (0, 86400),
                                        digits = 1,
                                        tool_tip = 'The length of the time window for which events should be loaded.')
        self.pref_manager.add_item(pagename = 'Select',
                                   item = item)

        item = psy_pm.SingleChoicePrefItem(name = 'event_catalog',
                                          label = 'event catalog',
                                          group = 'event selection',
                                          value = '',
                                          limit = [],
                                          tool_tip = 'Select an event catalog for which to load the events.')
        self.pref_manager.add_item(pagename = 'Select',
                                   item = item)


        column_labels = ['db_id', 'start_time', 'length', 'public_id',
                         'description', 'agency_uri', 'author_uri',
                         'comment']
        item = psy_pm.ListCtrlEditPrefItem(name = 'events',
                                           label = 'events',
                                           group = 'event selection',
                                           value = [],
                                           column_labels = column_labels,
                                           limit = [],
                                           hooks = {'on_value_change': self.on_event_selected},
                                           tool_tip = 'The available events.')
        self.pref_manager.add_item(pagename = 'Select',
                                   item = item)


        item = psy_pm.ActionItem(name = 'load_events',
                                 label = 'load events',
                                 group = 'detection time span',
                                 mode = 'button',
                                 action = self.on_load_events)
        self.pref_manager.add_item(pagename = 'Select',
                                   item = item)


    def buildFoldPanel(self, panelBar):
        ''' Create the foldpanel GUI.
        '''
        # Set the limits of the event_catalog field.
        catalog_names = self.library.get_catalogs_in_db(self.parent.project)
        self.pref_manager.set_limit('event_catalog', catalog_names)
        if catalog_names:
            self.pref_manager.set_value('event_catalog', catalog_names[0])

        fold_panel = PrefEditPanel(pref = self.pref_manager,
                                  parent = panelBar)

        return fold_panel


    def activate(self):
        ''' Extend the plugin deactivate method.
        '''
        OptionPlugin.activate(self)
        if self.selected_event:
            self.parent.add_shared_info(origin_rid = self.rid,
                                        name = 'selected_event',
                                        value = self.selected_event)


    def deactivate(self):
        ''' Extend the plugin deactivate method.
        '''
        OptionPlugin.deactivate(self)
        self.clear_annotation()
        self.parent.plugins_information_bag.remove_info(origin_rid = self.rid)


    def getHooks(self):
        ''' The callback hooks.
        '''
        hooks = {}
        return hooks


    def on_load_events(self, event):
        '''
        '''
        self.update_events_list()


    def update_events_list(self):
        ''' Update the events list control.
        '''
        event_library = self.library
        catalog_name = self.pref_manager.get_value('event_catalog')
        start_time = self.pref_manager.get_value('start_time')
        duration = self.pref_manager.get_value('window_length')

        if catalog_name not in event_library.catalogs.keys():
            event_library.load_catalog_from_db(project = self.parent.project,
                                               name = catalog_name)

        cur_catalog = event_library.catalogs[catalog_name]
        cur_catalog.clear_events()
        cur_catalog.load_events(project = self.parent.project,
                                start_time = start_time,
                                end_time = start_time + duration)

        event_list = self.convert_events_to_list(cur_catalog.events)
        self.pref_manager.set_limit('events', event_list)


    def convert_events_to_list(self, events):
        ''' Convert a list of event objects to a list suitable for the GUI element.
        '''
        list_fields = []
        list_fields.append(('db_id', 'id', int))
        list_fields.append(('start_time_string', 'start time', str))
        list_fields.append(('length', 'length', float))
        list_fields.append(('public_id', 'public id', str))
        list_fields.append(('description', 'description', str))
        list_fields.append(('agency_uri', 'agency', str))
        list_fields.append(('author_uri', 'author', str))
        list_fields.append(('comment', 'comment', str))

        event_list = []
        for cur_event in events:
            cur_row = []
            for cur_field in list_fields:
                cur_name = cur_field[0]
                cur_row.append(str(getattr(cur_event, cur_name)))
            event_list.append(cur_row)

        return event_list


    def on_event_selected(self):
        '''
        '''
        selected_event = self.pref_manager.get_value('events')

        if selected_event:
            selected_event = selected_event[0]
            event_id = float(selected_event[0])
            start_time = UTCDateTime(selected_event[1])
            end_time = start_time + float(selected_event[2])
            self.selected_event = {'start_time':start_time,
                                   'end_time':end_time,
                                   'id':event_id,
                                   'catalog_name': self.pref_manager.get_value('event_catalog')}
            self.parent.add_shared_info(origin_rid = self.rid,
                                        name = 'selected_event',
                                        value = self.selected_event)

            #self.clear_annotation()
            #self.parent.updateDisplay()


    def clear_annotation(self):
        ''' Clear the annotation elements in the tracedisplay views.
        '''
        pass



class EventListField(wx.Panel, listmix.ColumnSorterMixin):

    def __init__(self, name, pref_item, size, parent = None):
        '''
        '''
        wx.Panel.__init__(self, parent = parent, size = size, id = wx.ID_ANY)

        self.name = name

        self.pref_item = pref_item

        self.size = size

        self.label = name + ":"

        self.labelElement = None

        self.controlElement = None

        self.sizer = wx.GridBagSizer(5,5)

        # Create the field label.
        self.labelElement = StaticText(parent=self,
                                       ID=wx.ID_ANY,
                                       label=self.label,
                                       style=wx.ALIGN_LEFT)

        self.sizer.Add(self.labelElement, pos = (0,0), flag = wx.EXPAND|wx.ALL, border = 0)

        self.controlElement = EventListCtrl(parent = self, size = (200, 300),
                                            style = wx.LC_REPORT
                                            | wx.BORDER_NONE
                                            | wx.LC_SINGLE_SEL
                                            | wx.LC_SORT_ASCENDING)

        # The columns to show as a list to keep it in the correct order.
        self.columns = ['db_id', 'start_time', 'length', 'public_id',
                        'description', 'agency_uri', 'author_uri',
                        'comment']

        # The labels of the columns.
        self.column_labels = {'db_id': 'id',
                       'start_time': 'start time',
                       'length': 'length',
                       'public_id': 'public id',
                       'description': 'description',
                       'agency_uri': 'agency',
                       'author_uri': 'author',
                       'comment': 'comment'}

        # Methods for derived values.
        self.get_method = {'length': self.get_length}

        # Methods for values which should not be converted using the default
        # str function.
        self.convert_method = {'start_time': self.convert_to_isoformat}

        for k, name in enumerate(self.columns):
            self.controlElement.InsertColumn(k, self.column_labels[name])

        self.sizer.Add(self.controlElement, pos = (1,0), flag = wx.EXPAND|wx.ALL, border = 0)
        self.sizer.AddGrowableCol(0)
        self.sizer.AddGrowableRow(1)

        self.SetSizer(self.sizer)

    def __del__(self):
        self.pref_item.remove_gui_element(self)


    def set_events(self, events):
        '''
        '''
        self.controlElement.DeleteAllItems()
        for k, cur_event in enumerate(events):
            for n_col, cur_name in enumerate(self.columns):
                if cur_name in self.get_method.keys():
                    val = self.get_method[cur_name](cur_event)
                elif cur_name in self.convert_method.keys():
                    val = self.convert_method[cur_name](getattr(cur_event, cur_name))
                else:
                    val = str(getattr(cur_event, cur_name))

                if n_col == 0:
                    self.controlElement.InsertStringItem(k, val)
                else:
                    self.controlElement.SetStringItem(k, n_col, val)


    def convert_to_isoformat(self, val):
        return UTCDateTime(val).isoformat()

    def get_length(self, event):
        return str(event.end_time - event.start_time)






class EventListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    '''
    '''
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        ''' Initialize the instance.
        '''
        wx.ListCtrl.__init__(self, parent, id, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)

        # Create the icons for column sorting.
        self.il = wx.ImageList(16, 16)
        self.sm_up = self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_GO_UP, wx.ART_OTHER, (16,16)))
        self.sm_dn = self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_GO_DOWN, wx.ART_OTHER, (16,16)))
        self.SetImageList(self.il, wx.IMAGE_LIST_SMALL)

