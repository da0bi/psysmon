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


class CombinedNavZoomTestCase(unittest.TestCase):

    def test_zoom_cursor_and_accelerator(self):
        zoom = Zoom()
        self.assertEqual(zoom.cursor, wx.CURSOR_CROSS)
        self.assertEqual(zoom.accelerator_string, 'SHIFT+Z')
        self.assertFalse(zoom.in_drag)
        self.assertFalse(zoom.restore_on_release)

    def test_navigate_arrow_shortcuts(self):
        nav = Navigate()
        parent = DummyParent()
        nav.parent = parent

        # Test Up arrow (zoom in)
        self.assertIn('zoom_in_20', nav.shortcuts)
        self.assertEqual(nav.shortcuts['zoom_in_20']['accelerator_string'], 'Up')
        nav.on_zoom_in(ratio=20)
        self.assertEqual(parent.displayManager.shrink_ratio, 20)
        self.assertTrue(parent.update_called)

        # Test Down arrow (zoom out)
        self.assertIn('zoom_out_20', nav.shortcuts)
        self.assertEqual(nav.shortcuts['zoom_out_20']['accelerator_string'], 'Down')
        parent.update_called = False
        nav.on_zoom_out(ratio=20)
        self.assertEqual(parent.displayManager.grow_ratio, 20)
        self.assertTrue(parent.update_called)

        # Test Left and Right arrows
        self.assertIn('advance_100', nav.shortcuts)
        self.assertEqual(nav.shortcuts['advance_100']['accelerator_string'], 'Right')
        self.assertIn('regress_100', nav.shortcuts)
        self.assertEqual(nav.shortcuts['regress_100']['accelerator_string'], 'Left')

        # Test fine steps
        self.assertEqual(nav.shortcuts['zoom_in_25']['accelerator_string'], 'SHIFT+Up')
        self.assertEqual(nav.shortcuts['zoom_in_10']['accelerator_string'], 'CTRL+Up')
        self.assertEqual(nav.shortcuts['zoom_in_1']['accelerator_string'], 'ALT+Up')
        self.assertEqual(nav.shortcuts['zoom_out_25']['accelerator_string'], 'SHIFT+Down')
        self.assertEqual(nav.shortcuts['zoom_out_10']['accelerator_string'], 'CTRL+Down')
        self.assertEqual(nav.shortcuts['zoom_out_1']['accelerator_string'], 'ALT+Down')

    def test_navigate_preferences(self):
        nav = Navigate()
        item = nav.pref_manager.get_item(name='zoom ratio')
        self.assertIsNotNone(item)
        self.assertEqual(nav.pref_manager.get_value('zoom ratio'), 20)

    def test_swap_tool_and_restore_tool(self):
        parent = DummyParent()
        nav = Navigate()
        nav.parent = parent
        zoom = Zoom()
        zoom.parent = parent
        parent.plugins = [nav, zoom]

        # Initially navigate is active
        nav.active = True
        zoom.active = False

        # Swap to zoom
        TraceDisplayDlg.swap_tool(parent, 'zoom')
        self.assertEqual(parent.plugin_to_restore, nav)
        self.assertFalse(nav.active)
        self.assertTrue(zoom.active)

        # Calling swap_tool again while swapped should be a no-op
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
        class MockKeyEvent(object):
            def GetKeyCode(self):
                return ord('z')
            def Skip(self):
                pass

        # Key release while dragging sets restore_on_release flag
        TraceDisplayDlg.on_key_up(parent, MockKeyEvent())
        self.assertTrue(zoom.restore_on_release)
        # Still in zoom because mouse drag hasn't finished
        self.assertTrue(zoom.active)


if __name__ == '__main__':
    unittest.main()
