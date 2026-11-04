import unittest
import wx
import psysmon
import psysmon.packages.tracedisplay.tracedisplay as tracedisplay
from psysmon.packages.tracedisplay.plugins_navigate import Navigate
from psysmon.packages.tracedisplay.plugins_zoom import Zoom
from psysmon.packages.tracedisplay.tracedisplay import TraceDisplayDlg


class DummyDisplayManager(object):
    def __init__(self):
        self.shrink_ratio = None
        self.grow_ratio = None
        self.advance_step = None
        self.decrease_step = None

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
        from psysmon.gui.shortcut import ShortcutManager
        self.shortcut_manager = ShortcutManager()
        self.update_called = False
        self.plugins = []
        self.plugin_to_restore = None
        self.collection_node = type('DummyNode', (), {'rid': 'test/node'})()

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


class MockKeyEvent(object):
    def __init__(self, key_code, shift=False, ctrl=False, alt=False):
        self.key_code = key_code
        self.shift = shift
        self.ctrl = ctrl
        self.alt = alt
        self.skipped = False

    def GetKeyCode(self):
        return self.key_code

    def ShiftDown(self):
        return self.shift

    def ControlDown(self):
        return self.ctrl

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
        # Should only have 5 clean shortcuts, not a bloated list
        self.assertEqual(len(registered), 5)

    def test_navigate_preferences(self):
        nav = Navigate()
        item = nav.pref_manager.get_item(name='zoom ratio')
        self.assertIsNotNone(item)
        self.assertEqual(nav.pref_manager.get_value('zoom ratio'), 20)

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

        # In non-interactive test environment where Z is not physically held,
        # calling swap_tool again detects the stale state, recovers, and re-swaps cleanly
        TraceDisplayDlg.swap_tool(parent, 'zoom')
        self.assertTrue(zoom.active)
        self.assertEqual(parent.plugin_to_restore, nav)


if __name__ == '__main__':
    unittest.main()
