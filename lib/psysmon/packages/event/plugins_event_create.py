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

import psysmon
from psysmon.core.plugins import InteractivePlugin
from psysmon.core.guiBricks import PrefEditPanel
from psysmon.artwork.icons import iconsBlack16 as icons
import psysmon.core.preferences_manager as psy_pm
from obspy.core.utcdatetime import UTCDateTime
import wx.lib.mixins.listctrl as listmix
from wx.lib.stattext import GenStaticText as StaticText
import psysmon.packages.event.core as event_core


class CreateEvent(InteractivePlugin):
    '''

    '''
    nodeClass = 'TraceDisplay'

    def __init__(self):
        ''' Initialize the instance.

        '''
        InteractivePlugin.__init__(self,
                              name = 'create event',
                              category = 'edit',
                              tags = ['create', 'event']
                             )

        # Create the logging logger instance.
        logger_prefix = psysmon.logConfig['package_prefix']
        loggerName = logger_prefix + "." + __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.icons['active'] = icons.event_new_16
        self.cursor = wx.CURSOR_CROSS

        # The event catalog library used to manage the catalogs.
        self.library = event_core.Library('event library')

        # The name of the selected catalog.
        self.selected_catalog_name = None


        self.begin_line = {}
        self.end_line = {}
        self.bg = {}
        self.motion_notify_cid = []
        self.startTime = None
        self.endTime = None


        # Add the pages to the preferences manager.
        self.pref_manager.add_page('tool options')

        # Add the plugin preferences.
        item = psy_pm.SingleChoicePrefItem(name = 'event_catalog',
                                          label = 'event catalog',
                                          group = 'catalog',
                                          value = '',
                                          limit = [],
                                          tool_tip = 'Select an event catalog to work on.',
                                          hooks = {'on_value_change': self.on_select_catalog})
        self.pref_manager.add_item(pagename = 'tool options',
                                   item = item)

        item = psy_pm.ActionItem(name = 'create_new_catalog',
                                 label = 'create new catalog',
                                 group = 'catalog',
                                 mode = 'button',
                                 action = self.on_create_new_catalog)
        self.pref_manager.add_item(pagename = 'tool options',
                                   item = item)



    def buildFoldPanel(self, panelBar):
        ''' Create the foldpanel GUI.
        '''
        # Set the limits of the event_catalog field.
        catalog_names = self.library.get_catalogs_in_db(project = self.parent.project)
        self.pref_manager.set_limit('event_catalog', catalog_names)
        if catalog_names:
            self.pref_manager.set_value('event_catalog', catalog_names[0])

        fold_panel = PrefEditPanel(pref = self.pref_manager,
                                  parent = panelBar)

        # Customize the catalog field.
        #pref_item = self.pref_manager.get_item('pick_catalog')[0]
        #field = pref_item.gui_element[0]
        #fold_panel.Bind(wx.EVT_CHOICE, self.on_catalog_selected, field.controlElement)

        return fold_panel


    def getHooks(self):
        hooks = {}

        hooks['button_press_event'] = self.on_button_press
        hooks['button_release_event'] = self.on_button_release

        return hooks


    def deactivate(self):
        ''' Deactivate the plugin.
        '''
        self.cleanup()
        self.active = False


    def on_select_catalog(self):
        ''' Handle the catalog selection.
        '''
        self.selected_catalog_name = self.pref_manager.get_value('event_catalog')
        # Load the catalog from the database.
        self.library.clear()
        self.library.load_catalog_from_db(project = self.parent.project,
                                          name = self.selected_catalog_name)

        # Load the picks.
        self.load_events()

        # Clear existing pick lines.
        #self.clear_pick_lines()

        # Update the pick lines.
        #self.add_pick_lines()


    def load_events(self):
        ''' Load the events for the current timespan of the tracedisplay.
        '''
        cur_catalog = self.library.catalogs[self.selected_catalog_name]
        cur_catalog.clear_events()
        cur_catalog.load_events(project = self.parent.project,
                                start_time = self.parent.displayManager.startTime,
                                end_time = self.parent.displayManager.endTime)


    def on_create_new_catalog(self, event):
        ''' Handle the create new catalog button click.
        '''
        dialog_fields = (("name:", "name", wx.TE_RIGHT, 'not_empty'),
                         ("description:", "description", wx.TE_RIGHT, None))

        dlg = EditDlg(parent = self.parent,
                      title = 'Create a new event catalog.',
                      dialog_fields = dialog_fields)
        val = dlg.ShowModal()
        if val == wx.ID_OK:
            self.create_catalog(**dlg.data)
        dlg.Destroy()


    def create_catalog(self, name, description):
        ''' Create a new catalog in the database.
        '''
        catalog = event_core.Catalog(name = name,
                                     description = description,
                                     agency_uri = self.parent.project.activeUser.agency_uri,
                                     author_uri = self.parent.project.activeUser.author_uri,
                                     creation_time = UTCDateTime().isoformat())
        catalog.write_to_database(self.parent.project)
        cur_limit = self.pref_manager.get_limit('event_catalog')
        cur_limit.append(catalog.name)
        self.pref_manager.set_limit('event_catalog', cur_limit)


    def on_button_press(self, event, dataManager=None, displayManager=None):
        if event.button == 2:
            # Skip the middle mouse button.
            return
        elif event.button == 3:
            return

        #self.logger.debug('dataManager: %s\ndisplayManager: %s', dataManager, displayManager)

        #print 'Clicked mouse:\nxdata=%f, ydata=%f' % (event.xdata, event.ydata)
        #print 'x=%f, y=%f' % (event.x, event.y)

        self.startTime = event.xdata
        self.endTime = event.xdata

        viewport = displayManager.parent.viewPort
        for curStation in viewport.stations:
            for curChannel in curStation.channels.values():
                for curView in curChannel.views.values():
                    #bg = curView.plotCanvas.canvas.copy_from_bbox(curView.dataAxes.bbox)
                    #curView.plotCanvas.canvas.restore_region(bg)

                    if curView in self.end_line.keys():
                        self.end_line[curView].set_visible(False)
                        curView.dataAxes.draw_artist(self.end_line[curView])


                    if curView in self.begin_line.keys():
                        self.begin_line[curView].set_xdata(event.xdata)
                    else:
                        self.begin_line[curView] = curView.dataAxes.axvline(x=event.xdata)

                    curView.plotCanvas.canvas.draw()

                    cid = curView.plotCanvas.canvas.mpl_connect('motion_notify_event', lambda evt, dataManager=dataManager, displayManager=displayManager, callback=self.on_mouse_motion : callback(evt, dataManager, displayManager))
                    self.motion_notify_cid.append((curView.plotCanvas.canvas, cid))


    def on_mouse_motion(self, event, dataManger=None, displayManager=None):
        if event.inaxes is not None:
            self.endTime = event.xdata

        viewport = displayManager.parent.viewPort
        for curStation in viewport.stations:
            for curChannel in curStation.channels.values():
                for curView in curChannel.views.values():
                    if event.inaxes is None:
                        inv = curView.dataAxes.transData.inverted()
                        tmp = inv.transform((event.x, event.y))
                        self.logger.debug('xTrans: %f', tmp[0])
                        event.xdata = tmp[0]
                    canvas = curView.plotCanvas.canvas
                    if curView not in self.bg.keys():
                        self.bg[curView] = canvas.copy_from_bbox(curView.dataAxes.bbox)
                    canvas.restore_region(self.bg[curView])

                    if curView not in self.end_line.keys():
                        self.end_line[curView] = curView.dataAxes.axvline(x=event.xdata, animated=True)
                    else:
                        self.end_line[curView].set_xdata(event.xdata)
                        self.end_line[curView].set_visible(True)

                    curView.dataAxes.draw_artist(self.end_line[curView])
                    canvas.blit()


    def on_button_release(self, event, dataManager=None, displayManager=None):
        self.logger.debug('onButtonRelease')

        self.cleanup()

        # Call the setTimeLimits of the displayManager.
        # The timebase of the plots is unixseconds.
        if self.startTime == self.endTime:
            return
        elif self.endTime < self.startTime:
            self.create_event(start_time = self.endTime, end_time = self.endTime)
        else:
            self.create_event(start_time = self.startTime, end_time = self.endTime)


    def create_event(self, start_time, end_time):
        ''' Create a new event in the database.
        '''
        cur_catalog = self.library.catalogs[self.selected_catalog_name]
        event = event_core.Event(start_time = UTCDateTime(start_time),
                                 end_time = UTCDateTime(end_time),
                                 agency_uri = self.parent.project.activeUser.agency_uri,
                                 author_uri = self.parent.project.activeUser.author_uri,
                                 creation_time = UTCDateTime().isoformat())
        cur_catalog.add_events([event, ])
        event.write_to_database(self.parent.project)




    def cleanup(self):
        ''' Remove all elements added to the views.
        '''
        # Clear the zoom lines.
        for curView in self.begin_line.keys():
            if curView in self.begin_line.keys():
                curView.dataAxes.lines.remove(self.begin_line[curView])
            if curView in self.end_line.keys():
                curView.dataAxes.lines.remove(self.end_line[curView])
            curView.draw()

        self.begin_line = {}
        self.end_line = {}


        # Clear the motion notify callbacks.
        for canvas, cid in self.motion_notify_cid:
            canvas.mpl_disconnect(cid)

        self.motion_notify_cid = []
        self.bg = {}



class EditDlg(wx.Dialog):

    def __init__(self, dialog_fields, title = None,
                 data = None, parent=None, size=(300, 200)):
        wx.Dialog.__init__(self, parent, wx.ID_ANY, title, size=size)


        # Use standard button IDs.
        ok_button = wx.Button(self, wx.ID_OK)
        ok_button.SetDefault()
        cancel_button = wx.Button(self, wx.ID_CANCEL)

        self.dialog_fields = dialog_fields

        if data is None:
            self.data = {}
        else:
            self.data = data

        # Layout using sizers.
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.label = {};
        self.edit = {};

        sizer.Add(self.create_dialog_fields(), 0, wx.EXPAND|wx.ALL, 5)

        btnSizer = wx.StdDialogButtonSizer()
        btnSizer.AddButton(ok_button)
        btnSizer.AddButton(cancel_button)
        btnSizer.Realize()
        sizer.Add(btnSizer, 0, wx.EXPAND|wx.ALL, 5)

        self.SetSizer(sizer)
        sizer.Fit(self)

        # Bind the events.
        self.Bind(wx.EVT_BUTTON, self.on_ok, ok_button)


    def on_ok(self, event):
        is_valid = self.Validate()

        if(is_valid):
            for _, cur_key, _, _ in self.dialog_fields:
                self.data[cur_key] = self.edit[cur_key].GetValue()

            self.EndModal(wx.ID_OK)


    def create_dialog_fields(self):
        fgSizer = wx.FlexGridSizer(len(self.dialog_fields), 2, 5, 5)

        for curLabel, curKey, curStyle, curValidator in self.dialog_fields:
            self.label[curKey] = wx.StaticText(self, wx.ID_ANY, curLabel)
            self.edit[curKey] = wx.TextCtrl(self, size=(200, -1),
                                            style=curStyle)

            if curKey in self.data.keys():
                self.edit[curKey].SetValue(str(self.data[curKey]))

            if curValidator == 'not_empty':
                self.edit[curKey].SetValidator(NotEmptyValidator())

            fgSizer.Add(self.label[curKey], 0, wx.ALIGN_RIGHT)
            fgSizer.Add(self.edit[curKey], 0, wx.EXPAND)

        fgSizer.AddGrowableCol(1)
        return fgSizer


class NotEmptyValidator(wx.PyValidator):
    ## The constructor
    #
    # @param self The object pointer.
    def __init__(self):
        wx.PyValidator.__init__(self)


    ## The default clone method.    
    def Clone(self):
        return NotEmptyValidator()


    ## The method run when validating the field.
    #
    # This method checks if the control has a value. If not, it returns False.
    # @param self The object pointer.
    def Validate(self, win):
        ctrl = self.GetWindow()
        value = ctrl.GetValue()

        if len(value) == 0:
            wx.MessageBox("This field must contain some text!", "Error")
            ctrl.SetBackgroundColour("pink")
            ctrl.SetFocus()
            ctrl.Refresh()
            return False
        else:
            ctrl.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
            ctrl.Refresh()
            return True

    ## The method called when entering the dialog.      
    def TransferToWindow(self):
        return True

    ## The method called when leaving the dialog.  
    def TransferFromWindow(self):
        return True
