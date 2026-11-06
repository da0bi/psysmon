import unittest
import wx
import psysmon
import psysmon.packages.tracedisplay.tracedisplay as tracedisplay
from obspy.core.utcdatetime import UTCDateTime
from psysmon.packages.tracedisplay.plugins_navigate import Navigate
from psysmon.packages.tracedisplay.plugins_zoom import Zoom
from psysmon.packages.tracedisplay.tracedisplay import TraceDisplayDlg


class DummyDisplayManager(object):
    def __init__(self, startTime=1000.0, endTime=2000.0):
        self.startTime = startTime
        self.endTime = endTime
        self.shrink_ratio = None
        self.grow_ratio = None
        self.advance_step = None
        self.decrease_step = None
        self.parent = None

    def setTimeLimits(self, startTime, endTime):
        self.startTime = startTime
        self.endTime = endTime

    def shrinkTimePeriod(self, ratio=50):
        self.shrink_ratio = ratio

    def growTimePeriod(self, ratio=50):
        self.grow_ratio = ratio

    def advanceTimePercentage(self, step=100):
        self.advance_step = step

    def decreaseTimePercentage(self, step=100):
        self.decrease_step = step


class DummyParent(object):
    def __init__(self):
        self.displayManager = DummyDisplayManager()
        self.displayManager.parent = self
        from psysmon.gui.shortcut import ShortcutManager
        self.shortcut_manager = ShortcutManager()
        self.update_called = False
        self.plugins = []
        self.plugin_to_restore = None
        self.collection_node = type('DummyNode', (), {'rid': 'test/node'})()
        self.zoom_history = []
        self.max_zoom_history = 3
        self.logger = psysmon.get_logger(self)
        self.statusbar = type('DummyStatusbar', (), {'set_shortcut_tips_msg': lambda s, msg: None})()

    def update_display(self):
        self.update_called = True

    def shrinkTimePeriod(self, ratio=50):
        self.displayManager.shrinkTimePeriod(ratio)
        self.update_display()

    def growTimePeriod(self, ratio=50):
        self.displayManager.growTimePeriod(ratio)
        self.update_display()

    def advanceTimePercentage(self, step=100):
        self.displayManager.advanceTimePercentage(step)
        self.update_display()

    def decreaseTimePercentage(self, step=100):
        self.displayManager.decreaseTimePercentage(step)
        self.update_display()

    def advanceTime(self):
        self.displayManager.advanceTimePercentage(100)
        self.update_display()

    def decreaseTime(self):
        self.displayManager.decreaseTimePercentage(100)
        self.update_display()

    def check_menu_checkitem(self, plugin):
        pass

    def uncheck_menu_checkitem(self, plugin):
        pass

    def deactivate_interactive_plugin(self, plugin):
        plugin.active = False

    def activate_interactive_plugin(self, plugin):
        plugin.active = True

    def is_text_control_focused(self):
        return False

    def get_plugin(self, name):
        return TraceDisplayDlg.get_plugin(self, name)

    def get_active_interactive_plugin(self):
        return TraceDisplayDlg.get_active_interactive_plugin(self)

    def activate_interactive_tool(self, plugin):
        TraceDisplayDlg.activate_interactive_tool(self, plugin)

    def swap_tool(self, name='zoom'):
        TraceDisplayDlg.swap_tool(self, name)

    def restore_tool(self):
        TraceDisplayDlg.restore_tool(self)

    def push_zoom_history(self, start_time = None, end_time = None):
        return TraceDisplayDlg.push_zoom_history(self, start_time, end_time)

    def undo_zoom(self):
        return TraceDisplayDlg.undo_zoom(self)

    def has_zoom_history(self):
        return TraceDisplayDlg.has_zoom_history(self)

    def clear_zoom_history(self):
        return TraceDisplayDlg.clear_zoom_history(self)

    def on_key_up(self, event):
        return TraceDisplayDlg.on_key_up(self, event)

    def on_char_hook(self, event):
        return TraceDisplayDlg.on_char_hook(self, event)

    def on_activate(self, event):
        return TraceDisplayDlg.on_activate(self, event)


class MockKeyEvent(object):
    def __init__(self, key_code, event_type=wx.wxEVT_KEY_UP, shift=False, ctrl=False, alt=False, cmd=False):
        self.key_code = key_code
        self.event_type = event_type
        self.shift = shift
        self.ctrl = ctrl
        self.alt = alt
        self.cmd = cmd
        self.skipped = False

    def GetKeyCode(self):
        return self.key_code

    def GetEventType(self):
        return self.event_type

    def ShiftDown(self):
        return self.shift

    def ControlDown(self):
        return self.ctrl

    def CmdDown(self):
        return self.cmd

    def AltDown(self):
        return self.alt

    def Skip(self):
        self.skipped = True


class CombinedNavZoomTestCase(unittest.TestCase):

    def test_zoom_cursor_and_accelerator(self):
        zoom = Zoom()
        self.assertEqual(zoom.cursor, wx.CURSOR_CROSS)
        self.assertEqual(zoom.accelerator_string, 'SHIFT+Z')
        self.assertFalse(zoom.in_drag)
        self.assertFalse(zoom.restore_on_release)

    def test_navigate_methods_and_shortcuts(self):
        nav = Navigate()
        parent = DummyParent()
        nav.parent = parent

        # Test zoom in method
        nav.on_zoom_in(ratio=20)
        self.assertEqual(parent.displayManager.shrink_ratio, 20)
        self.assertTrue(parent.update_called)

        # Test zoom out method
        parent.update_called = False
        nav.on_zoom_out(ratio=20)
        self.assertEqual(parent.displayManager.grow_ratio, 20)
        self.assertTrue(parent.update_called)

        # Test time advance/regress methods
        nav.on_time_advance(step=100)
        self.assertEqual(parent.displayManager.advance_step, 100)
        nav.on_time_regress(step=100)
        self.assertEqual(parent.displayManager.decrease_step, 100)

        # Test activate registers clean primary shortcuts
        nav.activate()
        registered = parent.shortcut_manager.get_shortcut(origin_rid=nav.rid)
        key_combos = [x.key_combination for x in registered]
        self.assertIn(('WXK_UP',), key_combos)
        self.assertIn(('WXK_DOWN',), key_combos)
        self.assertIn(('WXK_LEFT',), key_combos)
        self.assertIn(('WXK_RIGHT',), key_combos)
        self.assertIn(('"z"',), key_combos)
        self.assertIn(('Ctrl+Z',), key_combos)
        self.assertEqual(len(registered), 6)

    def test_navigate_preferences(self):
        nav = Navigate()
        item = nav.pref_manager.get_item(name='zoom ratio')
        self.assertIsNotNone(item)
        self.assertEqual(nav.pref_manager.get_value('zoom ratio'), 20)
        history_item = nav.pref_manager.get_item(name='zoom_history_steps')
        self.assertIsNotNone(history_item)
        self.assertEqual(nav.pref_manager.get_value('zoom_history_steps'), 3)

    def test_navigate_inactive_by_default_and_skipped(self):
        parent = DummyParent()
        nav = Navigate()
        nav.parent = parent
        zoom = Zoom()
        zoom.parent = parent
        parent.plugins = [nav, zoom]

        # By default no interactive plugin is active
        nav.active = False
        zoom.active = False
        self.assertIsNone(parent.get_active_interactive_plugin())

        # Up arrow when inactive must be skipped (not consumed)
        evt = MockKeyEvent(wx.WXK_UP)
        TraceDisplayDlg.on_char_hook(parent, evt)
        self.assertTrue(evt.skipped)
        self.assertIsNone(parent.displayManager.shrink_ratio)

        # Plain 'z' when inactive must be skipped (not swapped to zoom)
        evt = MockKeyEvent(ord('z'), shift=False)
        TraceDisplayDlg.on_char_hook(parent, evt)
        self.assertTrue(evt.skipped)
        self.assertFalse(zoom.active)
        self.assertIsNone(parent.plugin_to_restore)

    def test_swap_tool_and_restore_tool(self):
        parent = DummyParent()
        nav = Navigate()
        nav.parent = parent
        zoom = Zoom()
        zoom.parent = parent
        parent.plugins = [nav, zoom]

        # Navigate is active
        nav.active = True
        zoom.active = False

        # Swap to zoom
        TraceDisplayDlg.swap_tool(parent, 'zoom')
        self.assertEqual(parent.plugin_to_restore, nav)
        self.assertFalse(nav.active)
        self.assertTrue(zoom.active)

        # Calling swap_tool again while swapped should be a no-op (or self-heal)
        TraceDisplayDlg.swap_tool(parent, 'zoom')
        self.assertEqual(parent.plugin_to_restore, nav)

        # Restore tool
        TraceDisplayDlg.restore_tool(parent)
        self.assertIsNone(parent.plugin_to_restore)
        self.assertTrue(nav.active)
        self.assertFalse(zoom.active)

    def test_zoom_deferred_restore_on_release(self):
        parent = DummyParent()
        nav = Navigate()
        nav.parent = parent
        zoom = Zoom()
        zoom.parent = parent
        parent.plugins = [nav, zoom]

        nav.active = True
        TraceDisplayDlg.swap_tool(parent, 'zoom')
        self.assertTrue(zoom.active)

        # Simulate user in drag when 'z' is released
        zoom.in_drag = True
        # Key release while dragging sets restore_on_release flag
        TraceDisplayDlg.on_key_up(parent, MockKeyEvent(ord('z')))
        self.assertTrue(zoom.restore_on_release)
        # Still in zoom because mouse drag hasn't finished
        self.assertTrue(zoom.active)

    def test_on_char_hook_arrows_zoom_and_navigate(self):
        parent = DummyParent()
        nav = Navigate()
        nav.parent = parent
        zoom = Zoom()
        zoom.parent = parent
        parent.plugins = [nav, zoom]
        nav.active = True

        # Plain Up arrow -> zoom in with default ratio (20)
        evt = MockKeyEvent(wx.WXK_UP)
        TraceDisplayDlg.on_char_hook(parent, evt)
        self.assertFalse(evt.skipped)
        self.assertEqual(parent.displayManager.shrink_ratio, 20)

        # Shift+Up arrow -> zoom in with ratio 25
        evt = MockKeyEvent(wx.WXK_UP, shift=True)
        TraceDisplayDlg.on_char_hook(parent, evt)
        self.assertFalse(evt.skipped)
        self.assertEqual(parent.displayManager.shrink_ratio, 25)

        # Ctrl+Up arrow -> zoom in with ratio 10
        evt = MockKeyEvent(wx.WXK_UP, ctrl=True)
        TraceDisplayDlg.on_char_hook(parent, evt)
        self.assertFalse(evt.skipped)
        self.assertEqual(parent.displayManager.shrink_ratio, 10)

        # Alt+Up arrow -> zoom in with ratio 1
        evt = MockKeyEvent(wx.WXK_UP, alt=True)
        TraceDisplayDlg.on_char_hook(parent, evt)
        self.assertFalse(evt.skipped)
        self.assertEqual(parent.displayManager.shrink_ratio, 1)

        # Plain Down arrow -> zoom out with default ratio (20)
        evt = MockKeyEvent(wx.WXK_DOWN)
        TraceDisplayDlg.on_char_hook(parent, evt)
        self.assertFalse(evt.skipped)
        self.assertEqual(parent.displayManager.grow_ratio, 20)

        # Plain Left arrow -> regress time step 100
        evt = MockKeyEvent(wx.WXK_LEFT)
        TraceDisplayDlg.on_char_hook(parent, evt)
        self.assertFalse(evt.skipped)
        self.assertEqual(parent.displayManager.decrease_step, 100)

        # Plain Right arrow -> advance time step 100
        evt = MockKeyEvent(wx.WXK_RIGHT)
        TraceDisplayDlg.on_char_hook(parent, evt)
        self.assertFalse(evt.skipped)
        self.assertEqual(parent.displayManager.advance_step, 100)

    def test_on_char_hook_shift_z_permanent_selection(self):
        parent = DummyParent()
        nav = Navigate()
        nav.parent = parent
        zoom = Zoom()
        zoom.parent = parent
        parent.plugins = [nav, zoom]
        nav.active = True

        # Shift+Z should activate Zoom permanently
        evt = MockKeyEvent(ord('z'), shift=True)
        TraceDisplayDlg.on_char_hook(parent, evt)
        self.assertFalse(evt.skipped)
        self.assertTrue(zoom.active)
        self.assertFalse(nav.active)
        self.assertIsNone(parent.plugin_to_restore)

        # Releasing 'z' does NOT restore because it was permanent
        TraceDisplayDlg.on_key_up(parent, MockKeyEvent(ord('z')))
        self.assertTrue(zoom.active)
        self.assertFalse(nav.active)

    def test_consecutive_z_hold_swaps(self):
        parent = DummyParent()
        nav = Navigate()
        nav.parent = parent
        zoom = Zoom()
        zoom.parent = parent
        parent.plugins = [nav, zoom]
        nav.active = True

        # First press-and-hold Z
        TraceDisplayDlg.on_char_hook(parent, MockKeyEvent(ord('z'), shift=False))
        self.assertTrue(zoom.active)
        self.assertFalse(nav.active)
        self.assertEqual(parent.plugin_to_restore, nav)

        # Release Z
        TraceDisplayDlg.on_key_up(parent, MockKeyEvent(ord('z')))
        self.assertFalse(zoom.active)
        self.assertTrue(nav.active)
        self.assertIsNone(parent.plugin_to_restore)

        # Second press-and-hold Z (verifies issue 2 is fixed!)
        TraceDisplayDlg.on_char_hook(parent, MockKeyEvent(ord('z'), shift=False))
        self.assertTrue(zoom.active)
        self.assertFalse(nav.active)
        self.assertEqual(parent.plugin_to_restore, nav)

        # Release Z again
        TraceDisplayDlg.on_key_up(parent, MockKeyEvent(ord('z')))
        self.assertFalse(zoom.active)
        self.assertTrue(nav.active)
        self.assertIsNone(parent.plugin_to_restore)

    def test_swap_tool_recovers_from_stale_state(self):
        parent = DummyParent()
        nav = Navigate()
        nav.parent = parent
        zoom = Zoom()
        zoom.parent = parent
        parent.plugins = [nav, zoom]
        nav.active = True

        # Simulate stuck swap state where zoom is active and plugin_to_restore is set
        TraceDisplayDlg.swap_tool(parent, 'zoom')
        self.assertEqual(parent.plugin_to_restore, nav)

        # Calling swap_tool again detects the stale state, recovers, and re-swaps cleanly
        TraceDisplayDlg.swap_tool(parent, 'zoom')
        self.assertTrue(zoom.active)
        self.assertEqual(parent.plugin_to_restore, nav)

    def test_push_and_undo_zoom_history(self):
        parent = DummyParent()
        parent.displayManager.startTime = 1000.0
        parent.displayManager.endTime = 2000.0

        # Push state 1
        parent.push_zoom_history()
        self.assertTrue(parent.has_zoom_history())
        self.assertEqual(len(parent.zoom_history), 1)

        # Move to state 2 and push
        parent.displayManager.startTime = 1200.0
        parent.displayManager.endTime = 1800.0
        parent.push_zoom_history()
        self.assertEqual(len(parent.zoom_history), 2)

        # Move to state 3 (current view)
        parent.displayManager.startTime = 1400.0
        parent.displayManager.endTime = 1600.0

        # Undo 1: should restore state 2 (1200, 1800)
        parent.update_called = False
        res = parent.undo_zoom()
        self.assertTrue(res)
        self.assertEqual(parent.displayManager.startTime, UTCDateTime(1200.0))
        self.assertEqual(parent.displayManager.endTime, UTCDateTime(1800.0))
        self.assertTrue(parent.update_called)

        # Undo 2: should restore state 1 (1000, 2000)
        res = parent.undo_zoom()
        self.assertTrue(res)
        self.assertEqual(parent.displayManager.startTime, UTCDateTime(1000.0))
        self.assertEqual(parent.displayManager.endTime, UTCDateTime(2000.0))

        # Undo 3: history empty, should return False
        self.assertFalse(parent.has_zoom_history())
        res = parent.undo_zoom()
        self.assertFalse(res)

    def test_zoom_history_max_depth(self):
        parent = DummyParent()
        nav = Navigate()
        nav.parent = parent
        parent.plugins = [nav]

        # Push 4 states: (100, 200), (110, 190), (120, 180), (130, 170)
        states = [
            (100.0, 200.0),
            (110.0, 190.0),
            (120.0, 180.0),
            (130.0, 170.0)
        ]
        for start, end in states:
            parent.displayManager.startTime = start
            parent.displayManager.endTime = end
            parent.push_zoom_history()

        # Default max_history is 3, so only the last 3 states should be retained
        self.assertEqual(len(parent.zoom_history), 3)

        # First undo restores states[3] (130, 170)
        parent.undo_zoom()
        self.assertEqual(parent.displayManager.startTime, UTCDateTime(130.0))
        # Second undo restores states[2] (120, 180)
        parent.undo_zoom()
        self.assertEqual(parent.displayManager.startTime, UTCDateTime(120.0))
        # Third undo restores states[1] (110, 190)
        parent.undo_zoom()
        self.assertEqual(parent.displayManager.startTime, UTCDateTime(110.0))
        # Fourth undo: empty
        self.assertFalse(parent.undo_zoom())

    def test_on_char_hook_ctrl_z_undo(self):
        parent = DummyParent()
        parent.displayManager.startTime = 1000.0
        parent.displayManager.endTime = 2000.0
        parent.push_zoom_history()

        parent.displayManager.startTime = 1200.0
        parent.displayManager.endTime = 1800.0

        # Ctrl+Z should trigger undo_zoom
        evt = MockKeyEvent(ord('z'), ctrl=True)
        TraceDisplayDlg.on_char_hook(parent, evt)
        self.assertFalse(evt.skipped)
        self.assertEqual(parent.displayManager.startTime, UTCDateTime(1000.0))
        self.assertEqual(parent.displayManager.endTime, UTCDateTime(2000.0))

    def test_zoom_right_click_undo(self):
        parent = DummyParent()
        parent.displayManager.startTime = 1000.0
        parent.displayManager.endTime = 2000.0
        parent.push_zoom_history()

        parent.displayManager.startTime = 1200.0
        parent.displayManager.endTime = 1800.0

        zoom = Zoom()
        zoom.parent = parent

        # Mock mouse event button 3 (right-click)
        class MockMouseEvent(object):
            def __init__(self, button, xdata=1500.0):
                self.button = button
                self.xdata = xdata

        evt = MockMouseEvent(button=3, xdata=1500.0)
        # Press right mouse button: restores previous view
        zoom.onButtonPress(evt)
        self.assertEqual(parent.displayManager.startTime, UTCDateTime(1000.0))
        self.assertEqual(parent.displayManager.endTime, UTCDateTime(2000.0))
        self.assertFalse(parent.has_zoom_history())

        # Release right mouse button: must NOT trigger a zoom-in or overwrite the reset
        zoom.onButtonRelease(evt)
        self.assertEqual(parent.displayManager.startTime, UTCDateTime(1000.0))
        self.assertEqual(parent.displayManager.endTime, UTCDateTime(2000.0))
        self.assertFalse(parent.has_zoom_history())

    def test_hold_z_right_click_then_release_z(self):
        parent = DummyParent()
        nav = Navigate()
        nav.parent = parent
        zoom = Zoom()
        zoom.parent = parent
        parent.plugins = [nav, zoom]
        nav.active = True

        parent.displayManager.startTime = 1000.0
        parent.displayManager.endTime = 2000.0
        parent.push_zoom_history()

        parent.displayManager.startTime = 1200.0
        parent.displayManager.endTime = 1800.0

        # 1. User holds 'z': swaps to zoom
        TraceDisplayDlg.on_char_hook(parent, MockKeyEvent(ord('z'), shift=False))
        self.assertTrue(zoom.active)
        self.assertFalse(nav.active)
        self.assertEqual(parent.plugin_to_restore, nav)

        class MockMouseEvent(object):
            def __init__(self, button, xdata=1500.0):
                self.button = button
                self.xdata = xdata

        evt = MockMouseEvent(button=3, xdata=1500.0)

        # 2. User right clicks (press and release while holding 'z')
        zoom.onButtonPress(evt)
        self.assertEqual(parent.displayManager.startTime, UTCDateTime(1000.0))
        self.assertEqual(parent.displayManager.endTime, UTCDateTime(2000.0))

        zoom.onButtonRelease(evt)
        self.assertEqual(parent.displayManager.startTime, UTCDateTime(1000.0))
        self.assertEqual(parent.displayManager.endTime, UTCDateTime(2000.0))
        # Zoom tool is still active while 'z' is held
        self.assertTrue(zoom.active)

        # 3. User releases 'z': restores Navigate cleanly
        TraceDisplayDlg.on_key_up(parent, MockKeyEvent(ord('z')))
        self.assertFalse(zoom.active)
        self.assertTrue(nav.active)
        self.assertIsNone(parent.plugin_to_restore)
        # View remains at the undone zoom state
        self.assertEqual(parent.displayManager.startTime, UTCDateTime(1000.0))
        self.assertEqual(parent.displayManager.endTime, UTCDateTime(2000.0))

    def test_reset_view_clears_zoom_history(self):
        parent = DummyParent()
        parent.displayManager.startTime = 1000.0
        parent.displayManager.endTime = 2000.0
        parent.push_zoom_history()
        self.assertTrue(parent.has_zoom_history())

        parent.clear_zoom_history()
        self.assertFalse(parent.has_zoom_history())
        self.assertEqual(len(parent.zoom_history), 0)

    def test_zoom_on_button_release_pushes_history(self):
        parent = DummyParent()
        zoom = Zoom()
        zoom.parent = parent
        zoom.cleanup = lambda: None
        parent.displayManager.startTime = 1000.0
        parent.displayManager.endTime = 2000.0

        zoom.startTime = 1200.0
        zoom.endTime = 1600.0
        zoom.in_drag = True

        class MockButton1Event(object):
            def __init__(self):
                self.button = 1

        zoom.onButtonRelease(MockButton1Event())

        # Current view should be updated
        self.assertEqual(parent.displayManager.startTime, UTCDateTime(1200.0))
        self.assertEqual(parent.displayManager.endTime, UTCDateTime(1600.0))
        # History should contain the previous view (1000, 2000)
        self.assertTrue(parent.has_zoom_history())
        self.assertEqual(parent.zoom_history[0], (UTCDateTime(1000.0), UTCDateTime(2000.0)))

    def test_key_up_global_event_filter(self):
        from psysmon.packages.tracedisplay.tracedisplay import TraceDisplayKeyFilter
        parent = DummyParent()
        nav = Navigate()
        nav.parent = parent
        zoom = Zoom()
        zoom.parent = parent
        parent.plugins = [nav, zoom]
        nav.active = True

        TraceDisplayDlg.swap_tool(parent, 'zoom')
        self.assertTrue(zoom.active)
        self.assertEqual(parent.plugin_to_restore, nav)

        # Create the filter attached to parent
        key_filter = TraceDisplayKeyFilter(parent)

        # Non-matching event (key code ord('A'))
        evt_a = MockKeyEvent(ord('A'), event_type=wx.wxEVT_KEY_UP)
        result = key_filter.FilterEvent(evt_a)
        self.assertEqual(result, wx.EventFilter.Event_Skip)
        self.assertTrue(zoom.active)

        # Matching event (key code ord('z'))
        evt_z = MockKeyEvent(ord('z'), event_type=wx.wxEVT_KEY_UP)
        result = key_filter.FilterEvent(evt_z)
        self.assertEqual(result, wx.EventFilter.Event_Skip)
        # Verify tool was restored to navigate
        self.assertFalse(zoom.active)
        self.assertTrue(nav.active)
        self.assertIsNone(parent.plugin_to_restore)

    def test_stuck_drag_escape_recovery(self):
        parent = DummyParent()
        nav = Navigate()
        nav.parent = parent
        zoom = Zoom()
        zoom.parent = parent
        parent.plugins = [nav, zoom]
        nav.active = True

        TraceDisplayDlg.swap_tool(parent, 'zoom')
        self.assertTrue(zoom.active)
        zoom.in_drag = True

        # User presses Escape while in stuck drag
        evt_esc = MockKeyEvent(wx.WXK_ESCAPE)
        TraceDisplayDlg.on_char_hook(parent, evt_esc)

        self.assertFalse(zoom.in_drag)
        self.assertFalse(zoom.active)
        self.assertTrue(nav.active)
        self.assertIsNone(parent.plugin_to_restore)

    def test_on_button_release_exception_safety(self):
        parent = DummyParent()
        nav = Navigate()
        nav.parent = parent
        zoom = Zoom()
        zoom.parent = parent
        parent.plugins = [nav, zoom]
        nav.active = True

        TraceDisplayDlg.swap_tool(parent, 'zoom')
        zoom.in_drag = True
        zoom.startTime = 1000.0
        zoom.endTime = 1500.0

        # Simulate 'z' released during drag
        TraceDisplayDlg.on_key_up(parent, MockKeyEvent(ord('z')))
        self.assertTrue(zoom.restore_on_release)

        # Make displayManager.setTimeLimits throw an exception
        def failing_set_time_limits(start, end):
            raise RuntimeError("Unexpected plotting error")

        parent.displayManager.setTimeLimits = failing_set_time_limits

        class MockButton1Event(object):
            def __init__(self):
                self.button = 1

        with self.assertRaises(RuntimeError):
            zoom.onButtonRelease(MockButton1Event())

        # Cleanup and restoration must have completed despite exception
        self.assertFalse(zoom.in_drag)
        self.assertFalse(zoom.restore_on_release)
        self.assertFalse(zoom.active)
        self.assertTrue(nav.active)
        self.assertIsNone(parent.plugin_to_restore)

    def test_window_deactivation_restores_tool(self):
        parent = DummyParent()
        nav = Navigate()
        nav.parent = parent
        zoom = Zoom()
        zoom.parent = parent
        parent.plugins = [nav, zoom]
        nav.active = True

        TraceDisplayDlg.swap_tool(parent, 'zoom')
        self.assertTrue(zoom.active)
        zoom.in_drag = True

        class MockActivateEvent(object):
            def __init__(self, active=False):
                self.active = active
                self.skipped = False

            def GetActive(self):
                return self.active

            def Skip(self):
                self.skipped = True

        evt_deactivate = MockActivateEvent(active=False)
        TraceDisplayDlg.on_activate(parent, evt_deactivate)

        self.assertTrue(evt_deactivate.skipped)
        self.assertFalse(zoom.in_drag)
        self.assertFalse(zoom.active)
        self.assertTrue(nav.active)
        self.assertIsNone(parent.plugin_to_restore)

    def test_mouse_motion_lost_release_recovery(self):
        parent = DummyParent()
        nav = Navigate()
        nav.parent = parent
        zoom = Zoom()
        zoom.parent = parent
        parent.plugins = [nav, zoom]
        nav.active = True

        TraceDisplayDlg.swap_tool(parent, 'zoom')
        zoom.in_drag = True
        zoom.restore_on_release = True

        class MockMotionEvent(object):
            def __init__(self):
                self.x = 100
                self.y = 100
                self.inaxes = None
                self.xdata = None

        # In testing environment LeftIsDown is False, so onMouseMotion should detect lost release
        from unittest.mock import patch, MagicMock
        mock_mouse_state = MagicMock()
        mock_mouse_state.LeftIsDown.return_value = False
        with patch('wx.GetApp', return_value=object()), \
             patch('wx.GetMouseState', return_value=mock_mouse_state):
            zoom.onMouseMotion(MockMotionEvent())

        self.assertFalse(zoom.in_drag)
        self.assertFalse(zoom.restore_on_release)
        self.assertFalse(zoom.active)
        self.assertTrue(nav.active)
        self.assertIsNone(parent.plugin_to_restore)

    def test_on_button_press_ignores_none_xdata(self):
        parent = DummyParent()
        zoom = Zoom()
        zoom.parent = parent

        class MockButtonPressEvent(object):
            def __init__(self):
                self.button = 1
                self.xdata = None

        zoom.onButtonPress(MockButtonPressEvent())
        self.assertFalse(zoom.in_drag)


if __name__ == '__main__':
    unittest.main()
