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

import sys
import logging
import warnings
import time
import wx
import wx.lib.graphics
from wx.lib.stattext import GenStaticText as StaticText
from wx.lib.pubsub import setupkwargs
from wx.lib.pubsub import pub
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
import wx.lib.scrolledpanel as scrolled
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
import numpy as np
import wx.lib.platebtn as platebtn
try:
    from agw import floatspin as floatspin
except ImportError: # if it's not there locally, try the wxPython lib.
    import wx.lib.agw.floatspin as floatspin

from wx import DatePickerCtrl
from wx.lib.masked import TimeCtrl
from wx.lib.masked import TextCtrl as MaskedTextCtrl
from psysmon.core.util import _wxdate2pydate, _pydate2wxdate
from obspy.core import UTCDateTime
import matplotlib as mpl




class TdViewAnnotationPanel(wx.Panel):
    '''
    The view annotation area.

    This area can be used to plot anotations for the view. This might be 
    some statistic values (e.g. min, max), the axes limits or some 
    other custom info.
    '''
    def __init__(self, parent, size=(200,-1), color=None):
        wx.Panel.__init__(self, parent, size=size)
        self.SetBackgroundColour(color)
        self.SetMinSize((200, -1))


	# Create a test label.
        self.label = StaticText(self, wx.ID_ANY, "view annotation area", (20, 10))
        font = wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.NORMAL)
        self.label.SetFont(font)

	# Add the label to the sizer.
	sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.label, 1, wx.EXPAND|wx.ALL, border=0)
	self.SetSizer(sizer)

        #print label.GetAlignment()

    def setLabel(self, text):
        ''' Set the text of the annotation label.
        '''
        self.label.SetLabelText(text)
        self.label.Refresh()


class PlotPanel(wx.Panel):
    """
    The PlotPanel
    """
    def __init__( self, parent, color=None, dpi=None, **kwargs ):
        # initialize Panel
        if 'id' not in kwargs.keys():
            kwargs['id'] = wx.ID_ANY
        if 'style' not in kwargs.keys():
            kwargs['style'] = wx.NO_FULL_REPAINT_ON_RESIZE
        wx.Panel.__init__( self, parent, **kwargs )
        self.SetMinSize((100, 40))

        # initialize matplotlib stuff
        self.figure = Figure(None, dpi=dpi, facecolor='white')
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.canvas.SetMinSize((30, 10))
        self.SetBackgroundColour('white')

	# Add the canvas to the sizer.
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, wx.EXPAND)
        self.SetSizer(self.sizer)

        #self.canvas.mpl_connect('button_press_event', self.onClick)
        self.canvas.Bind(wx.EVT_SET_FOCUS, self.onSetFocus)
        self.Bind(wx.EVT_SET_FOCUS, self.onSetFocus2)
        self.canvas.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)
        self.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)
        self.canvas.Bind(wx.EVT_KEY_UP, self.onKeyUp)
        self.Bind(wx.EVT_KEY_UP, self.onKeyUp)
        self.Bind(wx.EVT_LEFT_DOWN, self.onLeftDown)
        self.canvas.Bind(wx.EVT_LEFT_DOWN, self.onLeftDown)


    def onClick(self, event):
        print "Clicked in View. event: %s" % event.guiEvent
        event.guiEvent.ResumePropagation(1)
        event.guiEvent.Skip()

    def onWxClick(self, event):
        print "Got the WX event."

    def onSetFocus(self, event):
        print "Canvas got Focus"
        event.Skip()

    def onSetFocus2(self, event):
        print "PlotPanel got Focus"

    def onKeyDown(self, event):
        print "Propagating keyDown in plotPanel"
        event.ResumePropagation(1)
        event.Skip()

    def onKeyUp(self, event):
        print "Propagating keyUp in plotPanel"
        event.ResumePropagation(1)
        event.Skip()

    def onLeftDown(self, event):
        print "PlotPanel LEFT DOWN"
        event.ResumePropagation(30)
        event.Skip()


    def SetColor( self, rgbtuple=None ):
        """Set figure and canvas colours to be the same."""
        if rgbtuple is None:
            rgbtuple = wx.SystemSettings.GetColour( wx.SYS_COLOUR_BTNFACE ).Get()
        clr = [c/255. for c in rgbtuple]
        self.figure.set_facecolor( clr )
        self.figure.set_edgecolor( clr )
        self.canvas.SetBackgroundColour( wx.Colour( *rgbtuple ) )
        self.canvas.Refresh()



class View(wx.Panel):
    '''
    The tracedisplay view container.
    '''
    def __init__(self, parent=None, id=wx.ID_ANY, parentViewport=None, name=None):
        wx.Panel.__init__(self, parent)

        self.SetBackgroundColour('cyan3')

        self.plotCanvas = PlotPanel(self, color='violet')
        self.annotationArea = TdViewAnnotationPanel(self, color='gray80')

        self.SetMinSize(self.plotCanvas.GetMinSize())

        sizer = wx.GridBagSizer(0,0)
        sizer.Add(self.plotCanvas, pos=(0,0), flag=wx.ALL|wx.EXPAND, border=0)
        sizer.Add(self.annotationArea, pos=(0,1), flag=wx.ALL|wx.EXPAND, border=1)
	sizer.AddGrowableRow(0)
	sizer.AddGrowableCol(0)
	self.SetSizer(sizer)

        self.name = name

        self.parentViewport = parentViewport

        # Create the view data axes.
        #self.dataAxes = self.plotCanvas.figure.add_axes([0.1,0.1,0.8,0.8])
        self.dataAxes = self.plotCanvas.figure.add_axes([0,0,1,1])

        # A dictionary of graphic handles to annotation artists.
        self.annotation_artists = []

        # A list of matplotlib event connection ids.
        self.cids = []

        self.Bind(wx.EVT_ENTER_WINDOW, self.onEnterWindow)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.onLeaveWindow)
        self.Bind(wx.EVT_SET_FOCUS, self.onSetFocus)
        self.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)
        self.Bind(wx.EVT_KEY_UP, self.onKeyUp)
        self.Bind(wx.EVT_LEFT_DOWN, self.onLeftDown)

    def __del__(self):
        print "Deleting the view."


    def draw(self):
        ''' Draw the canvas to make the changes visible.
        '''
        self.plotCanvas.canvas.draw()


    def onEnterWindow(self, event):
        print "Entered view."
        #self.plotCanvas.SetColor((0,255,255))
        self.SetBackgroundColour('blue')
        self.SetFocus()
        self.Refresh()

    def onLeaveWindow(self, event):
        print "Entered view."
        self.SetBackgroundColour('green')
        self.Refresh()

    def onSetFocus(self, event):
        print "view got focus."

    def onKeyDown(self, event):
        event.ResumePropagation(1)
        event.Skip()

    def onKeyUp(self, event):
        event.ResumePropagation(1)
        event.Skip()

    def _onSize(self, event):
        event.Skip()
        #print "view resize"
        #print "view size: " + str(self.GetSize())
        #print "view parent: " + str(self.GetParent())
        #print "view parent size: " + str(self.GetParent().GetSize())
        #self.annotationArea.Resize()
        self.plotCanvas.Resize()

    def onRelease(self, event):
        print "RELEASING BUTTON"

    def onPress(self, event):
        print "PRESS BUTTON"

    def onLeftDown(self, event):
        print "view LEFT DOWN"
        event.Skip()


    def setEventCallbacks(self, hooks, dataManager, displayManager):

        for curKey, curCallback in hooks.iteritems():
            cur_cid = self.plotCanvas.canvas.mpl_connect(curKey, lambda evt, dataManager=dataManager, displayManager=displayManager, callback=curCallback: callback(evt, dataManager, displayManager))
            self.cids.append(cur_cid)


    def clearEventCallbacks(self, cid_list = None):
        if cid_list is None:
            cid_list = self.cids

        for cur_cid in cid_list:
            self.plotCanvas.canvas.mpl_disconnect(cur_cid)


    def setAnnotation(self, text):
        ''' Set the text in the annotation area of the view.
        '''
        self.annotationArea.setLabel(text)



    def plot_annotation_vline(self, x, parent_rid, key, **kwargs):
        ''' Plot a vertical line in the data axes.
        '''
        pass


    def plot_annotation_vspan(self, x_start, x_end, parent_rid, key, **kwargs):
        ''' Plot a vertical span in the data axes.
        '''
        pass



    def clear_annotation_artist(self, mode = None, parent_rid = None, key = None):
        ''' Delete annotation artits from the view.
        '''
        artists_to_remove = self.get_annotation_artist(mode = mode,
                                                       parent_rid = parent_rid,
                                                       key = key)
        for cur_artist in artists_to_remove:
            for cur_line_artist in cur_artist.line_artist:
                self.dataAxes.lines.remove(cur_line_artist)

            for cur_patch_artist in cur_artist.patch_artist:
                self.dataAxes.patches.remove(cur_patch_artist)

            for cur_text_artist in cur_artist.text_artist:
                self.dataAxes.texts.remove(cur_text_artist)

            self.annotation_artists.remove(cur_artist)




    def get_annotation_artist(self, **kwargs):
        ''' Get the annotation artist.
        '''
        ret_artist = self.annotation_artists

        valid_keys = ['mode', 'parent_rid', 'key']

        for cur_key, cur_value in kwargs.iteritems():
            if cur_key in valid_keys:
                ret_artist = [x for x in ret_artist if getattr(x, cur_key) == cur_value or cur_value is None]
            else:
                warnings.warn('Search attribute %s is not existing.' % cur_key, RuntimeWarning)

        return ret_artist



class AnnotationArtist(object):

    def __init__(self, mode, parent_rid, key):
        self.mode = mode

        self.parent_rid = parent_rid

        self.key = key

        self.line_artist = []

        self.text_artist = []

        self.patch_artist = []

        self.image_artist = []


    def add_artist(self, artist_list):
        ''' Add an artist.
        '''
        for cur_artist in artist_list:
            if isinstance(cur_artist, mpl.lines.Line2D):
                self.line_artist.append(cur_artist)
            elif isinstance(cur_artist, mpl.patches.Patch):
                self.patch_artist.append(cur_artist)
            elif isinstance(cur_artist, mpl.text.Text):
                self.text_artist.append(cur_artist)
            else:
                raise RuntimeError('Unknown artist type.')



class ChannelAnnotationArea(wx.Panel):

    def __init__(self, parent=None, id=wx.ID_ANY, label="channel name", bgColor="white", color="indianred", penColor="black"):
        wx.Panel.__init__(self, parent=parent, id=id, style=wx.FULL_REPAINT_ON_RESIZE)
        self.SetMinSize((40, -1))

        self.bgColor = bgColor
        self.label = label
        self.color = color
        self.penColor = penColor

	self.SetBackgroundColour(self.bgColor)
	self.SetBackgroundColour('white')

        self.Bind(wx.EVT_PAINT, self.OnPaint)


    def OnPaint(self, event):
        #print "OnPaint"
        event.Skip()
        dc = wx.PaintDC(self)
        gc = self.makeGC(dc)
        self.draw(gc)

    def makeGC(self, dc):
        try:
            gc = wx.GraphicsContext.Create(dc)
        except NotImplementedError:
            dc.DrawText("This build of wxPython does not support the wx.GraphicsContext "
                        "family of classes.",
                        25, 25)
            return None
        return gc

    def draw(self, gc):
        #print "drawing"
        winSize = self.GetClientSize()
        width = winSize[0]
        height = winSize[1]

        # Define the drawing  pen.
        penSize = 2;
        pen = wx.Pen(self.penColor, penSize)
        pen.SetJoin(wx.JOIN_ROUND)

        # Define the filling brush.
        brush = wx.Brush(self.color)

        # Define the font styles.
        font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        #font.SetWeight(wx.BOLD)
        gc.SetFont(font)

        path = gc.CreatePath()
        path.MoveToPoint(width, penSize/2.0)
        path.AddLineToPoint(3/4.0*width, penSize/2.0)
        path.MoveToPoint(3/4.0*width, penSize/2.0)
        path.AddLineToPoint(3/4.0*width, height-penSize/2.0)
        path.MoveToPoint(3/4.0*width, height-penSize/2.0)
        path.AddLineToPoint(width, height-penSize/2.0)
        path.CloseSubpath()

        path1 = gc.CreatePath()
        path1.AddRectangle(3/4.0*width, penSize/2.0, width/4.0, height-penSize/2.0)

        gc.SetPen(pen)
        gc.SetBrush(brush)
        gc.FillPath(path1)
        gc.DrawPath(path)

        newPos =  height/2

        #print winSize
        #print newPos
        gc.PushState()
        gc.Translate(width/4.0, newPos)
        gc.Rotate(np.radians(-90))
        w, h = gc.GetTextExtent(self.label)
        #print w
        gc.DrawText(self.label, -w/2.0, -h/2.0)
        #gc.DrawPath(path1)
        gc.PopState()


class ChannelContainer(wx.Panel):
    '''
    The channel panel.

    The channel panel may hold 1 to more Views.
    '''

    def __init__(self, parent=None, id=wx.ID_ANY, parentViewPort=None, name='channel name', color='black'):
        wx.Panel.__init__(self, parent=parent, id=id)

        # The viewPort containing the channel.
        self.parentViewPort = parentViewPort

        # The channel's name.
        self.name = name

        # The channel's color.
        self.color = color

        # A dictionary containing the views of the channel.
        self.views = {}

        self.SetBackgroundColour('yellow3')

        self.annotationArea = ChannelAnnotationArea(self, id=wx.ID_ANY, label=self.name, color=color)

        self.sizer = wx.GridBagSizer(0,0)
        self.viewSizer = wx.BoxSizer(wx.VERTICAL)

	self.sizer.Add(self.annotationArea, pos=(0,0), span=(1,1), flag=wx.ALL|wx.EXPAND, border=0)
        self.sizer.Add(self.viewSizer, pos=(0,1), flag=wx.ALL|wx.EXPAND, border=0)
        self.sizer.AddGrowableRow(0)
        self.sizer.AddGrowableCol(1)
        self.SetSizer(self.sizer)


    @property
    def scnl(self):
        parent = self.GetParent()
        return (parent.name, self.name, parent.network, parent.location)

    def addView(self, view):
        view.Reparent(self)
        self.views[view.name] = view

        if self.views:
            self.viewSizer.Add(view, 1, flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=1)

            #channelSize = self.views.itervalues().next().GetMinSize()
            #channelSize[1] = channelSize[1] * len(self.views) 
            #self.SetMinSize(channelSize)

        self.sizer.Layout()
        #self.rearrangeViews()



    def getView(self, name):
        ''' Check if the channel already contains the view.

        Parameters
        ----------
        name : String
            The name of the view to search.
        '''
        if name is None:
            return self.views.values()
        else:
            view = self.views.get(name, None)
            if view:
                view = [view, ]
            return view




    def removeView(self, name):
        ''' Remove a specified view from the channel container.

        Parameters
        ----------
        name : String
            The name of the view to remove
        '''
        view2Remove = self.views.pop(name)

        if view2Remove:
            self.sizer.Remove(view2Remove)
            view2Remove.Destroy()

        self.rearrangeViews()
        self.sizer.Layout()



    def rearrangeViews(self):

        if not self.views:
            return

        for curView in self.views.values():
            self.viewSizer.Hide(curView)
            self.viewSizer.Detach(curView)

        viewSize = self.views.itervalues().next().GetMinSize()
        viewSize[1] = viewSize[1] * len(self.views)
        self.SetMinSize(viewSize)

        for k, curView in enumerate(self.views.values()):
            self.viewSizer.Add(curView, 1, flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=1)
            curView.Show()


    def draw(self):
        ''' Draw the views of the channel.
        '''
        for cur_view in self.views.itervalues():
            cur_view.draw()


    def plot_annotation_vline(self, x, parent_rid, key, **kwargs):
        ''' Plot a vertical line in all views of the channel.
        '''
        for cur_view in self.views.itervalues():
            cur_view.plot_annotation_vline(x = x, parent_rid = parent_rid,
                                           key = key, **kwargs)

    def plot_annotation_vspan(self, x_start, x_end, parent_rid, key, **kwargs):
        ''' Plot a vertical vspan in the views of the channel.
        '''
        for cur_view in self.views.itervalues():
            cur_view.plot_annotation_vspan(x_start = x_start,
                                           x_end = x_end,
                                           parent_rid = parent_rid,
                                           key = key,
                                           **kwargs)



    def clear_annotation_artist(self, **kwargs):
        ''' Delete annotation artits all views of the channel.
        '''
        for cur_view in self.views.itervalues():
            cur_view.clear_annotation_artist(**kwargs)




class StationContainer(wx.Panel):
    '''
    The station panel.

    The station panel may hold 1 to more ChannelContainers.
    '''

    def __init__(self, parent=None, id=wx.ID_ANY, parentViewPort=None, name=None, network=None, location=None, color='black'):
        wx.Panel.__init__(self, parent=parent, id=id)

        # The viewPort containing the channel.
        self.parentViewPort = parentViewPort

        # The name of the station.
        self.name = name

        # The network of the station.
        self.network = network

        # The location of the station.
        self.location = location

        # The channel's color.
        self.color = color

        # A dictionary containing the views of the channel.
        self.channels = {}

        self.SetBackgroundColour('white')

        self.annotationArea = StationAnnotationArea(self, id=wx.ID_ANY, label=self.name, color=color)

        self.channelSizer = wx.BoxSizer(wx.VERTICAL)

        self.sizer = wx.GridBagSizer(0,0)
	self.sizer.Add(self.annotationArea, pos=(0,0), span=(1,1), flag=wx.ALL|wx.EXPAND, border=0)
        self.sizer.Add(self.channelSizer, pos = (0,1), flag=wx.ALL|wx.EXPAND, border = 0)
        self.sizer.AddGrowableCol(1)
        self.sizer.AddGrowableRow(0)
        self.SetSizer(self.sizer)

    @property
    def snl(self):
        return (self.name, self.network, self.location)


    def addChannel(self, channel):
        channel.Reparent(self)
        self.channels[channel.name] = channel
	if self.channels:
            self.channelSizer.Add(channel, 1, flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=1)

        self.sizer.Layout()

        curSize = self.GetSize()

        height = self.channelSizer.GetSize()[1]
        if height > curSize[1]:
            self.SetMinSize(self.channelSizer.GetSize())
            self.channelSizer.Layout()



    def getChannel(self, name):
        ''' Check if the station already contains a channel.

        Parameters
        ----------
        name : String
            The name of the channel to search.
        '''
        if name is None:
            return self.channels.values()
        else:
            channel = self.channels.get(name, [])
            if channel:
                channel = [channel, ]
            return channel



    def removeChannel(self, channelName):

        chan2Remove = self.channels.pop(channelName, None)

        if chan2Remove:
            self.channelSizer.Remove(chan2Remove)
            chan2Remove.Destroy()

        self.rearrangeChannels()

        self.channelSizer.Layout()


    def rearrangeChannels(self):

        if not self.channels:
            return

        for curChannel in self.channels.values():
            self.channelSizer.Hide(curChannel)
            self.channelSizer.Detach(curChannel)

        stationSize = self.channels.itervalues().next().GetMinSize()
        stationSize[1] = stationSize[1] * len(self.channels)
        self.SetMinSize(stationSize)

        for curChannel in self.channels.values():
            self.channelSizer.Add(curChannel, 1, flag=wx.TOP|wx.BOTTOM|wx.EXPAND, border=1)
            curChannel.Show()



    def getViewContainer(self, channelName, viewName):
        channels = self.getChannel(name = channelName)
        if not channels:
            return None

        ret_channel = []
        for curChannel in channels:
            ret_channel.extend(curChannel.getView(name = viewName))

        return ret_channel


    def draw(self):
        ''' Draw all channels of the station.
        '''
        for cur_channel in self.channels.itervalues():
            cur_channel.draw()


    def plot_annotation_vline(self, x, parent_rid, key, **kwargs):
        ''' Plot a vertical line in all channels of the station.
        '''
        for cur_channel in self.channels.itervalues():
            cur_channel.plot_annotation_vline(x = x, parent_rid = parent_rid,
                                              key = key, **kwargs)

    def clear_annotation_artist(self, **kwargs):
        ''' Delete annotation artits all views of the channel.
        '''
        for cur_channel in self.channels.itervalues():
            cur_channel.clear_annotation_artist(**kwargs)




class TdDatetimeInfo(wx.Panel):
    def __init__(self, parent=None, id=wx.ID_ANY, bgColor="ghostwhite", penColor="black"):
        wx.Panel.__init__(self, parent=parent, id=id, style=wx.FULL_REPAINT_ON_RESIZE)
        self.SetMinSize((-1, 30))
        self.SetMaxSize((-1, 30))

        # The logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.startTime = None
        self.endTime = None
        self.scale = None

        sizer = wx.GridBagSizer(0,0)

        self.dummy80 = wx.StaticText(self, wx.ID_ANY, '', size=(80, 10))
        self.dummy100 = wx.StaticText(self, wx.ID_ANY, '', size=(100, 10))
        #self.startTimeButton = platebtn.PlateButton(self, wx.ID_ANY, str(self.startTime), 
        #                                            style=platebtn.PB_STYLE_DEFAULT|platebtn.PB_STYLE_SQUARE
        #                                           )

        self.startDatePicker = DatePickerCtrl(self, id=wx.ID_ANY, style=wx.DP_DEFAULT|wx.DP_SHOWCENTURY)


        self.startTimePicker = MaskedTextCtrl( self, wx.ID_ANY, '',
                                                mask         = '##:##:##.######',
                                                excludeChars = '',
                                                formatcodes  = 'F!',
                                                includeChars = '')


        size = self.startTimePicker.GetSize()
        self.startTimeGoButton = wx.Button(self, id=wx.ID_ANY, label="go", size=(40, size[1]))


        self.durationFloatSpin = floatspin.FloatSpin(self, wx.ID_ANY, min_val=0, max_val=None,
                                              increment=1, value=60, agwStyle=floatspin.FS_RIGHT)
        self.durationFloatSpin.SetDigits(3)
        self.durationFloatSpin.SetFormat('%f')
        self.durationFloatSpin.SetRange(min_val=0.1, max_val=None)

        sizer.Add(self.dummy80, pos=(0,0), flag=wx.ALL, border=0)
        sizer.Add(self.startDatePicker, pos=(0,1), flag=wx.ALL|wx.ALIGN_BOTTOM, border=0)
        sizer.Add(self.startTimePicker, pos=(0,2), flag=wx.ALL|wx.ALIGN_BOTTOM, border=0)
        sizer.Add(self.startTimeGoButton, pos=(0,3), flag=wx.ALL|wx.ALIGN_BOTTOM, border=0)
        sizer.Add(self.durationFloatSpin, pos=(0,4), flag=wx.ALL|wx.ALIGN_BOTTOM, border=0)
        sizer.Add(self.dummy100, pos=(0,5), flag=wx.ALL, border=0)

        sizer.AddGrowableRow(0)
        sizer.AddGrowableCol(3)

        self.SetSizer(sizer)

        self.SetBackgroundColour(bgColor)

        self.Bind(floatspin.EVT_FLOATSPIN, self.onDurationFloatSpin, self.durationFloatSpin)
        #self.Bind(wx.EVT_TEXT, self.onStartTimePicker, self.startTimePicker)
        self.Bind(wx.EVT_BUTTON, self.onStartTimeGo, self.startTimeGoButton)
        #self.Bind(wx.EVT_PAINT, self.onPaint)

    def onStartTimePicker(self, event):
        self.logger.debug('onStartTimePicker')

    def onStartTimeGo(self, event):
        self.logger.debug('GO startTime GO')
        curDate = _wxdate2pydate(self.startDatePicker.GetValue())
        if self.startTimePicker.IsValid():
            curTime = self.startTimePicker.GetValue().replace('.', ':').split(':')
            curDateTime = UTCDateTime(curDate.year, curDate.month, curDate.day,
                                      int(curTime[0]), int(curTime[1]),
                                      int(curTime[2]), int(curTime[3]))
            self.logger.debug('startTime: %s', curDateTime)
            self.GetParent().GetParent().setStartTime(curDateTime)


    def onDurationFloatSpin(self, event):
        #dlg = wx.TextEntryDialog(
        #        self, 'Duration:',
        #        'Enter new duration')

        #dlg.SetValue(str(self.endTime - self.startTime))

        #if dlg.ShowModal() == wx.ID_OK:
        #    self.logger.debug('New duration: %f', float(dlg.GetValue()))
        #    self.logger.debug('Parent: %s', self.GetParent().GetParent())
        #    self.GetParent().GetParent().setDuration(float(dlg.GetValue()))
        floatSpin = event.GetEventObject()
        value = floatSpin.GetValue()
        self.logger.debug('New duration: %f', value)
        self.GetParent().GetParent().setDuration(value)



    def onPaint(self, event):
        #print "OnPaint"
        winSize = self.GetClientSize()
        width = winSize[0]
        height = winSize[1]
        btnSize = self.durationButton.GetSize()
        pos = (width - 100 - btnSize[1], height/2)
        self.durationButton.SetPosition(pos)
        event.Skip()
        #dc = wx.PaintDC(self)
        #gc = self.makeGC(dc)
        #self.draw(gc)


    def makeGC(self, dc):
        try:
            gc = wx.GraphicsContext.Create(dc)
        except NotImplementedError:
            dc.DrawText("This build of wxPython does not support the wx.GraphicsContext "
                        "family of classes.",
                        25, 25)
            return None
        return gc

    def draw(self, gc):
        self.logger.debug('Draw datetime')
        winSize = self.GetClientSize()
        width = winSize[0]
        height = winSize[1]


        font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        font.SetWeight(wx.BOLD)
        gc.SetFont(font)
        if self.startTime:
            gc.PushState()
            gc.Translate(80, height/2.0)

            spanText = str(self.endTime - self.startTime) + ' s'
            text = str(self.startTime) + '      length: ' + spanText
            gc.DrawText(text, 0, 0)

            #gc.PopState()
            #gc.PushState()
            #text = str(self.endTime - self.startTime) + ' s'
            #(textWidth, textHeight) = gc.GetTextExtent(text)
            #gc.Translate(width - 100 - textWidth, height/2.0)
            #gc.DrawText(text, 0, 0)

            #gc.PopState()

            #gc.Translate(width/2.0, height/2.0)
            #penSize = 2
            #pen = wx.Pen('black', penSize)
            #pen.SetJoin(wx.JOIN_ROUND)
            #path = gc.CreatePath()
            #scalebarLength = 10
            #path.MoveToPoint(0, 0)
            #path.AddLineToPoint(scalebarLength * self.scale, 0)
            #path.CloseSubpath()

            #gc.Translate(width/2.0, height/2.0)
            #gc.SetPen(pen)
            #gc.DrawPath(path)

            #gc.PopState()


    def setTime(self, startTime, endTime, scale):

        # TODO: Add a check for the correct data type.
        self.startTime = startTime
        self.endTime = endTime
        self.scale = scale

        # Set the datePicker value.
        self.startDatePicker.SetValue(_pydate2wxdate(self.startTime))
        self.startTimePicker.SetValue(self.startTime.strftime('%H%M%S%f'))

        #self.startTimeButton.SetLabel(str(self.startTime))
        #self.startTimeButton.SetSize(self.startTimeButton.DoGetBestSize())

        #self.durationButton.SetLabel(str(self.endTime - self.startTime) + ' s')
        #self.durationButton.SetSize(self.durationButton.DoGetBestSize())
        self.durationFloatSpin.SetValue(self.endTime - self.startTime)




class StationAnnotationArea(wx.Panel):

    def __init__(self, parent=None, id=wx.ID_ANY, label="station name", bgColor="white", color="indianred", penColor="black"):
        wx.Panel.__init__(self, parent=parent, id=id, style=wx.FULL_REPAINT_ON_RESIZE)
        self.SetMinSize((40, -1))

        self.bgColor = bgColor
        self.label = label
        self.color = color
        self.penColor = penColor

	self.SetBackgroundColour(self.bgColor)

        self.Bind(wx.EVT_PAINT, self.OnPaint)


    def OnPaint(self, event):
        #print "OnPaint"
        event.Skip()
        dc = wx.PaintDC(self)
        gc = self.makeGC(dc)
        self.draw(gc)

    def makeGC(self, dc):
        try:
            gc = wx.GraphicsContext.Create(dc)
        except NotImplementedError:
            dc.DrawText("This build of wxPython does not support the wx.GraphicsContext "
                        "family of classes.",
                        25, 25)
            return None
        return gc

    def draw(self, gc):
        #print "drawing"
        winSize = self.GetClientSize()
        width = winSize[0]
        height = winSize[1]

        # Define the drawing  pen.
        penSize = 2;
        pen = wx.Pen(self.penColor, penSize)
        pen.SetJoin(wx.JOIN_ROUND)

        # Define the filling brush.
        brush = wx.Brush(self.color)

        # Define the font styles.
        font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        font.SetWeight(wx.BOLD)
        gc.SetFont(font)

        path = gc.CreatePath()
        path.MoveToPoint(width, penSize/2.0)
        path.AddLineToPoint(3/4.0*width, penSize/2.0)
        path.MoveToPoint(3/4.0*width, penSize/2.0)
        path.AddLineToPoint(3/4.0*width, height-penSize/2.0)
        path.MoveToPoint(3/4.0*width, height-penSize/2.0)
        path.AddLineToPoint(width, height-penSize/2.0)
        path.CloseSubpath()

        path1 = gc.CreatePath()
        path1.AddRectangle(3/4.0*width, penSize/2.0, width/4.0, height-penSize/2.0)

        gc.SetPen(pen)
        gc.SetBrush(brush)
        gc.FillPath(path1)
        gc.DrawPath(path)

        newPos =  height/2

        #print winSize
        #print newPos
        gc.PushState()
        gc.Translate(width/4.0, newPos)
        gc.Rotate(np.radians(-90))
        w, h = gc.GetTextExtent(self.label)
        #print w
        gc.DrawText(self.label, -w/2.0, -h/2.0)
        #gc.DrawPath(path1)
        gc.PopState()



class TdViewPort(scrolled.ScrolledPanel):
    '''
    The tracedisplay viewport.

    This panel holds the :class:`~psysmon.packages.tracedisplay.StationContainer` objects.
    '''

    def __init__(self, parent=None, id=wx.ID_ANY):
        scrolled.ScrolledPanel.__init__(self, parent=parent, id=id, style=wx.FULL_REPAINT_ON_RESIZE)
        
        # The logging logger instance.
        loggerName = __name__ + "." + self.__class__.__name__
        self.logger = logging.getLogger(loggerName)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)

        self.SetBackgroundColour('white')

        self.SetupScrolling()

        # The list of stations controlled by the viewport.
        self.stations = [] 

        self.SetupScrolling()

        self.Bind(wx.EVT_LEFT_DOWN, self.onLeftDown)

        # Message subsiptions
        # pub.subscribe(self.onStationMsg, ('tracedisplay', 'display', 'station'))


    def onLeftDown(self, event):
        print "##### LEFT DOWN IN VIEWPORT #######"

    def onStationMsg(self, msg):
        if msg.topic == ('tracedisplay', 'display', 'station', 'hide'):
            self.removeStation(msg.data)
        elif msg.topic == ('tracedisplay', 'display', 'station', 'show'):
            self.sortStations(msg.data)




    def addStation(self, station, position=None):
        '''
        Add a StationContainer object to the viewport.

        :param self: The object pointer.
        :type self: :class:`~psysmon.packages.tracedisplay.TdViewPort`
        :param station: The station to be added to the viewport.
        :type station: :class:StationContainer
        :param position: The position where to add the station. If none, the station is added to the bottom.
        :type position: Integer
        '''
        station.Reparent(self)
        self.stations.append(station)

        #viewPortSize = self.stations[-1].GetMinSize()
        #viewPortSize[1] = viewPortSize[1] * len(self.stations) + 100 
        #self.SetMinSize(viewPortSize)



    def getStation(self, **kwargs):
        ''' Check if the viewport already contains a station.

        Parameters
        ----------
        '''
        ret_stations = self.stations

        valid_keys = ['name', 'network', 'location']

        for cur_key, cur_value in kwargs.iteritems():
            if cur_key in valid_keys:
                ret_stations = [x for x in ret_stations if getattr(x, cur_key) == cur_value or cur_value is None]
            else:
                warnings.warn('Search attribute %s is not existing.' % cur_key, RuntimeWarning)

        return ret_stations




    def sortStations(self, snl=[]):
        ''' Sort the stations according to the list given by snl.

            Parameters
            ----------
            snl : Tuple of Stringssnl=[]
                The order how to sort the stations. (station, network, location).
        '''
        #for curStation in self.stations:
        #    curStation.Hide()
        #    self.sizer.Detach(curStation)

        # Sort the stations list according to snl.
        tmp = []
        for curSnl in snl:
            statFound = [x for x in self.stations if x.name == curSnl[0]]

            # Add the station only if it's not already contained in the list.
            if statFound[0] not in tmp:
                tmp.append(statFound[0])

        self.stations = tmp

        # Rearrange the stations.
        self.rearrangeStations()
        #for curStation in self.stations:
        #    self.sizer.Add(curStation, 1, flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=5)
        #    curStation.Show()



    def removeStation(self, snl):
        ''' Remove a station from the viewport.

        This destroys the instance of the station.

        Parameters
        ----------
        station : :class:`StationContainer`
            The station object which should be removed.
        '''
        statFound = [x for x in self.stations if x.name == snl[0]]
        if statFound:
            self.logger.debug('Hiding the station.')
            statFound = statFound[0]
            self.stations.remove(statFound)
            self.sizer.Remove(statFound)
            statFound.Destroy()
            self.logger.debug('statFound: %s', statFound)
            self.rearrangeStations()

        self.sizer.Layout()


    def removeChannel(self, scnl):

        for curSCNL in scnl:
            statFound = [x for x in self.stations if x.name == curSCNL[0]]

            if statFound:
                statFound = statFound[0]
                statFound.removeChannel(curSCNL[1])




    def rearrangeStations(self):
        ''' Rearrange the stations in the viewport.

        '''

        for curStation in self.stations:
            #curStation.Hide()
            self.sizer.Hide(curStation)
            self.sizer.Detach(curStation)


        for curStation in self.stations:
            self.sizer.Add(curStation, 1, flag=wx.EXPAND|wx.TOP|wx.BOTTOM, border=1)
            curStation.Show()

        self.SetupScrolling()



    def getChannelContainer(self, station = None,
                            channel = None, network = None, location = None):
        ret_channels = []
        stations = self.getStation(name = station,
                                   network = network,
                                   location = location)
        if stations:
            for cur_station in stations:
                cur_channel = cur_station.getChannel(name = channel)
                if cur_channel is not None:
                    ret_channels.extend(cur_channel)

        return ret_channels



    def getViewContainer(self, station = None,
                         channel = None, network = None,
                         location = None, name = None):
        ''' Get the view container of a specified scnl code.

        '''
        stations = self.getStation(name = station,
                                   network = network,
                                   location = location)

        ret_views = []

        for cur_station in stations:
            views = cur_station.getViewContainer(channel, name)
            if views:
                ret_views.extend(views)

        return ret_views


    def registerEventCallbacks(self, hooks, dataManager, displayManager):
        ''' Set the specified event callbacks of the views.

        '''
        for curStation in self.stations:
            for curChannel in curStation.channels.values():
                for curView in curChannel.views.values():
                    curView.setEventCallbacks(hooks, dataManager, displayManager)


    def clearEventCallbacks(self):
        ''' Clear the callbacks of the views.
        '''
        for curStation in self.stations:
            for curChannel in curStation.channels.values():
                for curView in curChannel.views.values():
                    curView.clearEventCallbacks()






#viewTypeMap = {'seismogram' : SeismogramView}
