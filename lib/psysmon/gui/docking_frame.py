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

import operator as op

import wx
import wx.lib.agw.ribbon as ribbon

import psysmon
import psysmon.core
import psysmon.gui.view as psy_view
import psysmon.gui.view.viewport
import psysmon.gui.shortcut as psy_shortcut


class DockingFrame(wx.Frame):
    ''' A base class for a frame holding AUI docks.
    '''

    def __init__(self, parent = None, id = wx.ID_ANY,
                 title = 'docking frame', size = (1000, 600)):
        ''' Initialize the instance.
        '''
        wx.Frame.__init__(self,
                          parent = parent,
                          id = id,
                          title = title,
                          pos = wx.DefaultPosition,
                          style = wx.DEFAULT_FRAME_STYLE)
        self.SetMinSize(size)

        # The docking manager.
        self.mgr = wx.aui.AuiManager(self)

        # Create the tool ribbon bar instance.
        # The ribbon bar itself is filled using the init_ribbon_bar method
        # by the instance inheriting the PsysmonDockingFrame.
        self.ribbon = ribbon.RibbonBar(self, wx.ID_ANY)

        # Initialize the viewport.
        self.init_viewport()

        # Initialize the ribbon bar aui manager pane.
        self.init_ribbon_pane()

        #TODO: Add a status bar.
        self.statusbar = DockingFrameStatusBar(self)
        self.statusbar.set_error_log_msg("Last error message.")
        self.SetStatusBar(self.statusbar)


        # Create the shortcut manager.
        self.shortcut_manager = psy_shortcut.ShortcutManager()

        # Create the plugins shared information bag, which holds all the
        # information, that's shared by the tracedisplay plugins.
        self.plugins_information_bag = psysmon.core.plugins.SharedInformationBag()

        # Create the hook manager and fill it with the allowed hooks.
        self.hook_manager = psysmon.core.util.HookManager(self)

        self.hook_manager.add_hook(name = 'plugin_activated',
                                   description = 'Called after a plugin was activated.',
                                   passed_args = {'plugin_rid': 'The resource id of the plugin.',})
        self.hook_manager.add_hook(name = 'plugin_deactivated',
                                   description = 'Called after a plugin was deactivated.',
                                   passed_args = {'plugin_rid': 'The resource id of the plugin.',})
        self.hook_manager.add_hook(name = 'shared_information_added',
                                   description = 'Called after a shared information was added by a plugin.',
                                   passed_args = {'origin_rid': 'The resource id of the source of the shared information.',
                                                  'name': 'The name of the shared information.'})
        self.hook_manager.add_hook(name = 'shared_information_updated',
                                   description = 'Called after a shared information was added by a plugin.',
                                   passed_args = {'updated_info': 'The shared information instance which was updated.'})
        self.hook_manager.add_view_hook(name = 'button_press_event',
                                        description = 'The matplotlib button_press_event in the view axes.')
        self.hook_manager.add_view_hook(name = 'button_release_event',
                                        description = 'The matplotlib button_release_event in the view axes.')
        self.hook_manager.add_view_hook(name = 'motion_notify_event',
                                        description = 'The matplotlib motion_notify_event in the view axes.')


    def init_viewport(self):
        ''' Initialize the viewport.
        '''
        self.center_panel = wx.Panel(parent = self, id = wx.ID_ANY)
        self.viewport_sizer = wx.GridBagSizer()
        self.viewport = psy_view.viewport.Viewport(parent = self.center_panel)
        self.viewport_sizer.Add(self.viewport,
                                pos = (0, 0),
                                flag = wx.EXPAND|wx.ALL,
                                border = 0)
        self.viewport_sizer.AddGrowableRow(0)
        self.viewport_sizer.AddGrowableCol(0)
        self.center_panel.SetSizer(self.viewport_sizer)

        self.mgr.AddPane(self.center_panel,
                         wx.aui.AuiPaneInfo().Name('viewport').CenterPane())


    def init_menu_bar(self):
        ''' Initialize the menu bar.
        '''
        self.menubar = wx.MenuBar()
        category_list = list(set([x.category for x in self.plugins]))
        category_list = sorted(category_list)

        for cur_category in category_list:
            pass
           
        
        
    def init_ribbon_pane(self):
        ''' Initialize the aui manager pane for the ribbon bar.
        '''
        self.mgr.AddPane(self.ribbon,
                         wx.aui.AuiPaneInfo().Top().
                         Name('palette').
                         Caption('palette').
                         Layer(1).
                         Row(0).
                         Position(0).
                         BestSize(wx.Size(-1, 50)).
                         MinSize(wx.Size(-1, 80)).
                         CloseButton(False))



    def init_ribbon_bar(self):
        ''' Initialize the ribbon bar with the plugins.
        '''
        # Build the ribbon bar based on the plugins.
        # First create all the pages according to the category.
        self.ribbonPages = {}
        self.ribbonPanels = {}
        self.ribbonToolbars = {}
        self.foldPanels = {}
        for curGroup, curCategory in sorted([(x.group, x.category) for x in self.plugins], key = op.itemgetter(0, 1)):
            if curGroup not in iter(self.ribbonPages.keys()):
                self.logger.debug('Creating page %s', curGroup)
                self.ribbonPages[curGroup] = ribbon.RibbonPage(self.ribbon, wx.ID_ANY, curGroup)

            if curCategory not in iter(self.ribbonPanels.keys()):
                self.ribbonPanels[curCategory] = ribbon.RibbonPanel(self.ribbonPages[curGroup],
                                                                    wx.ID_ANY,
                                                                    curCategory,
                                                                    wx.NullBitmap,
                                                                    wx.DefaultPosition,
                                                                    wx.DefaultSize,
                                                                    agwStyle=ribbon.RIBBON_PANEL_NO_AUTO_MINIMISE)
                # TODO: Find out what I wanted to do with these lines!?!
                if curCategory == 'interactive':
                    self.ribbonToolbars[curCategory] = ribbon.RibbonToolBar(self.ribbonPanels[curCategory], 1)
                else:
                    self.ribbonToolbars[curCategory] = ribbon.RibbonToolBar(self.ribbonPanels[curCategory], 1)


        # Fill the ribbon bar with the plugin buttons.
        option_plugins = [x for x in self.plugins if x.mode == 'option']
        command_plugins = [x for x in self.plugins if x.mode == 'command']
        interactive_plugins = [x for x in self.plugins if x.mode == 'interactive']
        view_plugins = [x for x in self.plugins if x.mode == 'view']
        id_counter = 0

        for curPlugin in sorted(option_plugins, key = op.attrgetter('position_pref', 'name')):
                # Create a tool.
                curTool = self.ribbonToolbars[curPlugin.category].AddTool(tool_id = id_counter, 
                                                                          bitmap = curPlugin.icons['active'].GetBitmap(), 
                                                                          help_string = curPlugin.name,
                                                                          kind = ribbon.RIBBON_BUTTON_TOGGLE)
                self.ribbonToolbars[curPlugin.category].Bind(ribbon.EVT_RIBBONTOOLBAR_CLICKED, 
                                                             lambda evt, curPlugin=curPlugin : self.on_option_tool_clicked(evt, curPlugin), id=curTool.id)
                id_counter += 1

        for curPlugin in sorted(command_plugins, key = op.attrgetter('position_pref', 'name')):
                # Create a HybridTool or a normal tool if no preference items
                # are available. The dropdown menu allows to open
                # the tool parameters in a foldpanel.
                if len(curPlugin.pref_manager) == 0:
                    curTool = self.ribbonToolbars[curPlugin.category].AddTool(tool_id = id_counter,
                                                                              bitmap = curPlugin.icons['active'].GetBitmap(),
                                                                              help_string = curPlugin.name)
                else:
                    curTool = self.ribbonToolbars[curPlugin.category].AddHybridTool(tool_id = id_counter,
                                                                                    bitmap = curPlugin.icons['active'].GetBitmap(),
                                                                                    help_string = curPlugin.name)
                    self.ribbonToolbars[curPlugin.category].Bind(ribbon.EVT_RIBBONTOOLBAR_DROPDOWN_CLICKED,
                                                                 lambda evt, curPlugin=curPlugin: self.on_command_tool_dropdown_clicked(evt, curPlugin),
                                                                 id=curTool.id)
                self.ribbonToolbars[curPlugin.category].Bind(ribbon.EVT_RIBBONTOOLBAR_CLICKED,
                                                             lambda evt, curPlugin=curPlugin : self.on_command_tool_clicked(evt, curPlugin),
                                                             id=curTool.id)
                id_counter += 1


        for curPlugin in sorted(interactive_plugins, key = op.attrgetter('position_pref', 'name')):
                # Create a HybridTool. The dropdown menu allows to open
                # the tool parameters in a foldpanel.
                if len(curPlugin.pref_manager) == 0:
                    curTool = self.ribbonToolbars[curPlugin.category].AddTool(tool_id = id_counter,
                                                                              bitmap = curPlugin.icons['active'].GetBitmap(),
                                                                              help_string = curPlugin.name)
                else:
                    curTool = self.ribbonToolbars[curPlugin.category].AddHybridTool(tool_id = id_counter,
                                                                                    bitmap = curPlugin.icons['active'].GetBitmap(),
                                                                                    help_string = curPlugin.name)
                    self.ribbonToolbars[curPlugin.category].Bind(ribbon.EVT_RIBBONTOOLBAR_DROPDOWN_CLICKED,
                                                                 lambda evt, curPlugin=curPlugin: self.on_interactive_tool_dropdown_clicked(evt, curPlugin),
                                                                 id=curTool.id)
                self.ribbonToolbars[curPlugin.category].Bind(ribbon.EVT_RIBBONTOOLBAR_CLICKED,
                                                             lambda evt, curPlugin=curPlugin : self.on_interactive_tool_clicked(evt, curPlugin),
                                                             id=curTool.id)
                id_counter += 1

        for curPlugin in sorted(view_plugins, key = op.attrgetter('position_pref', 'name')):
                # Create a HybridTool or a normal tool if no preference items
                # are available. The dropdown menu allows to open
                # the tool parameters in a foldpanel.
                if len(curPlugin.pref_manager) == 0:
                    curTool = self.ribbonToolbars[curPlugin.category].AddTool(tool_id = id_counter,
                                                                              bitmap = curPlugin.icons['active'].GetBitmap(),
                                                                              help_string = curPlugin.name)

                else:
                    curTool = self.ribbonToolbars[curPlugin.category].AddHybridTool(tool_id = id_counter,
                                                                                    bitmap = curPlugin.icons['active'].GetBitmap(),
                                                                                    help_string = curPlugin.name)
                    self.ribbonToolbars[curPlugin.category].Bind(ribbon.EVT_RIBBONTOOLBAR_DROPDOWN_CLICKED,
                                                                 lambda evt, curPlugin=curPlugin: self.on_view_tool_dropdown_clicked(evt, curPlugin),
                                                                 id=curTool.id)
                self.ribbonToolbars[curPlugin.category].Bind(ribbon.EVT_RIBBONTOOLBAR_CLICKED,
                                                             lambda evt, curPlugin=curPlugin : self.on_view_tool_clicked(evt, curPlugin),
                                                             id=curTool.id)
                id_counter += 1


        self.ribbon.Realize()



    def on_option_tool_clicked(self, event, plugin):
        ''' Handle the click of an option plugin toolbar button.

        Show or hide the foldpanel of the plugin.
        '''
        self.logger.debug('Clicked the option tool: %s', plugin.name)

        cur_toolbar = event.GetEventObject()
        if cur_toolbar.GetToolState(event.GetId()) != ribbon.RIBBON_TOOLBAR_TOOL_TOGGLED:
            if plugin.name not in iter(self.foldPanels.keys()):
                # The panel of the option tool does't exist. Create it and add
                # it to the panel manager.
                curPanel = plugin.buildFoldPanel(self)
                self.mgr.AddPane(curPanel,
                                 wx.aui.AuiPaneInfo().Right().
                                 Name(plugin.name).
                                 Caption(plugin.name).
                                 Layer(2).
                                 Row(0).
                                 Position(0).
                                 BestSize(wx.Size(300, -1)).
                                 MinSize(wx.Size(200, 100)).
                                 MinimizeButton(True).
                                 MaximizeButton(True).
                                 CloseButton(False))
                # TODO: Add a onOptionToolPanelClose method to handle clicks of
                # the CloseButton in the AUI pane of the option tools. If the
                # pane is closed, the toggle state of the ribbonbar button has
                # be changed. The according event is aui.EVT_AUI_PANE_CLOSE.
                self.mgr.Update()
                self.foldPanels[plugin.name] = curPanel
            else:
                if not self.foldPanels[plugin.name].IsShown():
                    curPanel = self.foldPanels[plugin.name]
                    self.mgr.GetPane(curPanel).Show()
                    self.mgr.Update()
            plugin.activate()
            self.call_hook('plugin_activated', plugin_rid = plugin.rid)
        else:
            if self.foldPanels[plugin.name].IsShown():
                curPanel = self.foldPanels[plugin.name]
                self.mgr.GetPane(curPanel).Hide()
                self.mgr.Update()

            plugin.deactivate()
            self.call_hook('plugin_deactivated', plugin_rid = plugin.rid)




    def on_command_tool_clicked(self, event, plugin):
        ''' Handle the click of a command plugin toolbar button.

        Activate the tool.
        '''
        self.logger.debug('Clicked the command tool: %s', plugin.name)
        plugin.run()


    def on_command_tool_dropdown_clicked(self, event, plugin):
        ''' Handle the click on the dropdown button of an command plugin toolbar button.

        '''
        menu = wx.Menu()
        item = menu.Append(wx.ID_ANY, "edit preferences")
        self.Bind(wx.EVT_MENU, lambda evt, plugin=plugin: self.on_edit_tool_preferences(evt, plugin), item)
        event.PopupMenu(menu)



    def on_interactive_tool_clicked(self, event, plugin):
        ''' Handle the click of an interactive plugin toolbar button.

        Activate the tool.
        '''
        active_plugin = [x for x in self.plugins if x.active is True and x.mode == 'interactive']
        if len(active_plugin) > 1:
            raise RuntimeError('Only one interactive tool can be active.')
        elif len(active_plugin) == 1:
            active_plugin = active_plugin[0]
            self.deactivate_interactive_plugin(active_plugin)
        self.activate_interactive_plugin(plugin)


    def on_interactive_tool_dropdown_clicked(self, event, plugin):
        ''' Handle the click on the dropdown button of an interactive plugin toolbar button.

        '''
        menu = wx.Menu()
        item = menu.Append(wx.ID_ANY, "edit preferences")
        self.Bind(wx.EVT_MENU, lambda evt, plugin=plugin: self.on_edit_tool_preferences(evt, plugin), item)
        event.PopupMenu(menu)


    def activate_interactive_plugin(self, plugin):
        ''' Activate an interactive plugin.
        '''
        plugin.activate()
        if plugin.active:
            if plugin.cursor is not None:
                if isinstance(plugin.cursor, wx.lib.embeddedimage.PyEmbeddedImage):
                    image = plugin.cursor.GetImage()
                    # since this image didn't come from a .cur file, tell it where the hotspot is
                    img_size = image.GetSize()
                    image.SetOptionInt(wx.IMAGE_OPTION_CUR_HOTSPOT_X, img_size[0] * plugin.cursor_hotspot[0])
                    image.SetOptionInt(wx.IMAGE_OPTION_CUR_HOTSPOT_Y, img_size[1] * plugin.cursor_hotspot[1])

                    # make the image into a cursor
                    self.viewport.SetCursor(wx.CursorFromImage(image))
                else:
                    try:
                        self.viewport.SetCursor(wx.StockCursor(plugin.cursor))
                    except Exception:
                        pass

            self.logger.debug('Clicked the interactive tool: %s', plugin.name)

            # Get the hooks and register the matplotlib hooks in the viewport.
            hooks = plugin.getHooks()
            allowed_matplotlib_hooks = iter(self.hook_manager.view_hooks.keys())

            for cur_key in [x for x in hooks.keys() if x not in allowed_matplotlib_hooks]:
                del hooks[cur_key]

            # Set the callbacks of the views.
            self.viewport.clear_mpl_event_callbacks()
            self.viewport.register_mpl_event_callbacks(hooks)
            self.call_hook('plugin_activated', plugin_rid = plugin.rid)
            self.statusbar.set_interactive_tool_msg(plugin.name)
            shortcuts = self.shortcut_manager.get_shortcut(origin_rid = plugin.rid)
            status_msg = ','.join(['+'.join(x.key_combination) for x in shortcuts])
            status_msg = 'tool shortcuts: ' + status_msg
            self.statusbar.set_shortcut_tips_msg(status_msg)


    def deactivate_interactive_plugin(self, plugin):
        ''' Deactivate an interactive plugin.
        '''
        if plugin.mode != 'interactive':
            return
        self.viewport.clear_mpl_event_callbacks()
        self.viewport.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
        plugin.deactivate()
        self.shortcut_manager.remove_shortcut(origin_rid = plugin.rid)
        self.call_hook('plugin_deactivated', plugin_rid = plugin.rid)
        self.statusbar.set_interactive_tool_msg("no tool active")
        self.statusbar.set_shortcut_tips_msg('')


    def on_edit_tool_preferences(self, event, plugin):
        ''' Handle the edit preferences dropdown click.

        '''
        self.logger.debug('Dropdown clicked -> editing preferences.')

        if plugin.name not in iter(self.foldPanels.keys()):
            #curPanel = plugin.buildFoldPanel(self.foldPanelBar)
            #foldPanel = self.foldPanelBar.addPanel(curPanel, plugin.icons['active'])

            curPanel = plugin.buildFoldPanel(self)
            self.mgr.AddPane(curPanel,
                             wx.aui.AuiPaneInfo().Right().
                                                  Name(plugin.name).
                                                  Caption(plugin.name).
                                                  Layer(2).
                                                  Row(0).
                                                  Position(0).
                                                  BestSize(wx.Size(300, -1)).
                                                  MinSize(wx.Size(200, 100)).
                                                  MinimizeButton(True).
                                                  MaximizeButton(True))
            self.mgr.Update()
            self.foldPanels[plugin.name] = curPanel
        else:
            if not self.foldPanels[plugin.name].IsShown():
                curPanel = self.foldPanels[plugin.name]
                self.mgr.GetPane(curPanel).Show()
                self.mgr.Update()


    def on_view_tool_clicked(self, event, plugin):
        ''' Handle the click of an view plugin toolbar button.

        Activate the tool.
        '''
        self.logger.debug('Clicked the view tool: %s', plugin.name)

        if plugin.active == True:
            plugin.deactivate()
            self.call_hook('plugin_deactivated', plugin_rid = plugin.rid)
            self.unregister_view_plugin(plugin)
        else:
            plugin.activate()
            self.call_hook('plugin_activated', plugin_rid = plugin.rid)
            self.register_view_plugin(plugin)

        self.viewport.Refresh()
        self.viewport.Update()

        self.update_display()


    def on_view_tool_dropdown_clicked(self, event, plugin):
        ''' Handle the click on the dropdown button of an view plugin toolbar button.

        '''
        self.logger.debug('Clicked the view tool dropdown button: %s', plugin.name)
        menu = wx.Menu()
        item = menu.Append(wx.ID_ANY, "edit preferences")
        self.Bind(wx.EVT_MENU, lambda evt, plugin=plugin: self.on_edit_tool_preferences(evt, plugin), item)
        event.PopupMenu(menu)


    def call_hook(self, hook_name, **kwargs):
        ''' Call the hook of the plugins.
        '''
        # TODO: Think about calling the hooks of all plugins, even if they are
        # not activated. This would keep track of changes within deactivated
        # plugins. It might cause some troubles with plugins, for which the
        # fold panel was not yet created, check this.
        active_plugins = [x for x in self.plugins if x.active or x.mode == 'command']
        self.hook_manager.call_hook(receivers = active_plugins,
                                    hook_name = hook_name,
                                    **kwargs)


    def add_shared_info(self, origin_rid, name, value):
        ''' Add a shared information.

        Parameters
        ----------
        origin_rid : String
            The resource ID of the origin of the information.

        name : String
            The name of the shared information

        value : Dictionary
            The value of the shared information
        '''
        self.plugins_information_bag.add_info(origin_rid = origin_rid,
                                              name = name,
                                              value = value)
        self.call_hook('shared_information_added',
                       origin_rid = origin_rid,
                       name = name)


    def notify_shared_info_change(self, updated_info):
        ''' Notify tracedisplay, that a shared informtion was changed.
        '''
        self.call_hook('shared_information_updated',
                       updated_info = updated_info)


    def get_shared_info(self, **kwargs):
        ''' Get a shared information.

        Parameters
        ----------
        origin_rid : String
            The resource ID of the origin of the information.

        name : String
            The name of the shared information
        '''
        return self.plugins_information_bag.get_info(**kwargs)


    def register_view_plugin(self, plugin):
        ''' Method to handle plugin requests.

        Overwrite this method to react to special requirements needed by the plugin.
        E.g. create virtual channels in the tracedisplay.
        '''
        self.viewport.register_view_plugin(plugin)


    def unregister_view_plugin(self, plugin):
        ''' Method to handle plugin requests.

        Overwrite this method to react to special requirements needed by the plugin.
        E.g. create virtual channels in the tracedisplay.
        '''
        self.viewport.remove_node(name = plugin.rid, recursive = True)



class DockingFrameStatusBar(wx.StatusBar):

    def __init__(self, parent):
        wx.StatusBar.__init__(self, parent, -1)


        # This status bar has three fields
        self.SetFieldsCount(3)
        # Sets the three fields to be relative widths to each other.
        self.SetStatusWidths([-3, -3, -1])
        # Create sunken fields.
        wx.SB_SUNKEN = 3
        self.SetStatusStyles([wx.SB_SUNKEN, wx.SB_SUNKEN, wx.SB_SUNKEN])

        self.error_log_pos = 0
        self.shortcut_tips_pos = 1
        self.interactive_tool_pos = 2


    def set_error_log_msg(self, msg):
        ''' Set the message of the error log tool area.
        '''
        self.SetStatusText(msg, self.error_log_pos)


    def set_shortcut_tips_msg(self, msg):
        ''' Set the message of the shortcut tips area.
        '''
        self.SetStatusText(msg, self.shortcut_tips_pos)


    def set_interactive_tool_msg(self, msg):
        ''' Set the message of the interactive tool area.
        '''
        self.SetStatusText(msg, self.interactive_tool_pos)
