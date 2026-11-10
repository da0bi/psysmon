import unittest
from unittest.mock import MagicMock
import numpy as np
from matplotlib.figure import Figure
from obspy.core.trace import Trace
from obspy.core.stream import Stream

import psysmon
import psysmon.packages.tracedisplay.tracedisplay as tracedisplay
from psysmon.packages.tracedisplay.plugins_views import SpectrogramPlotter, SpectrogramView


class SpectrogramViewTestCase(unittest.TestCase):
    def setUp(self):
        # Create SpectrogramPlotter plugin
        self.plotter = SpectrogramPlotter()

        # Create dummy parent with mock displayManager and dataManager
        self.parent = MagicMock()
        self.data_manager = MagicMock()
        self.display_manager = MagicMock()

        self.parent.dataManager = self.data_manager
        self.parent.displayManager = self.display_manager
        self.plotter.parent = self.parent

        # Setup sample stream with 100 Hz sampling rate (Nyquist = 50 Hz)
        data = np.sin(np.linspace(0, 100, 1000, dtype=np.float32))
        tr = Trace(data=data, header={'sampling_rate': 100.0, 'station': 'STA', 'channel': 'HHZ', 'network': 'XX'})
        self.stream = Stream(traces=[tr])
        self.data_manager.procStream = self.stream
        self.data_manager.origStream = self.stream

    def test_preferences_initialization(self):
        ''' Verify fmin and fmax preferences exist with correct defaults and limits.
        '''
        self.assertIsNotNone(self.plotter.pref_manager.get_item('fmin'))
        self.assertIsNotNone(self.plotter.pref_manager.get_item('fmax'))

        fmin_item = self.plotter.pref_manager.get_item('fmin')[0]
        fmax_item = self.plotter.pref_manager.get_item('fmax')[0]
        process_item = self.plotter.pref_manager.get_item('process')[0]

        self.assertEqual(fmin_item.label, 'fmin [Hz]')
        self.assertEqual(fmax_item.label, 'fmax [Hz]')
        self.assertEqual(process_item.label, 'process')
        self.assertEqual(fmin_item.value, 0.0)
        self.assertEqual(fmax_item.value, 0.0)
        self.assertEqual(fmin_item.limit, (0.0, None))
        self.assertEqual(fmax_item.limit, (0.0, None))
        self.assertIn('on_value_change', fmin_item.hooks)
        self.assertIn('on_value_change', fmax_item.hooks)
        self.assertEqual(fmin_item.hooks['on_value_change'], self.plotter.on_pref_input_changed)
        self.assertEqual(fmax_item.hooks['on_value_change'], self.plotter.on_pref_input_changed)

        self.assertIsNotNone(self.plotter.pref_manager.get_item('y_refinement'))
        refine_item = self.plotter.pref_manager.get_item('y_refinement')[0]
        self.assertEqual(refine_item.label, 'y-axis refinement')
        self.assertEqual(refine_item.value, '1x (standard)')
        self.assertEqual(refine_item.limit, ('1x (standard)', '2x', '4x', '8x'))

    def test_get_nyquist_frequency(self):
        ''' Verify Nyquist calculation from stream or parent dataManager.
        '''
        # From stream directly
        self.assertEqual(self.plotter.get_nyquist_frequency(self.stream), 50.0)

        # From parent dataManager
        self.assertEqual(self.plotter.get_nyquist_frequency(), 50.0)

        # Multiple streams with different sampling rates -> takes max
        tr2 = Trace(data=np.zeros(100), header={'sampling_rate': 250.0})
        multi_stream = Stream(traces=[self.stream[0], tr2])
        self.assertEqual(self.plotter.get_nyquist_frequency(multi_stream), 125.0)

        # Empty stream
        self.assertIsNone(self.plotter.get_nyquist_frequency(Stream()))

    def test_update_nyquist_fmax_on_plot(self):
        ''' Verify fmax automatically populates with Nyquist frequency when data is available.
        '''
        self.assertEqual(self.plotter.pref_manager.get_value('fmax'), 0.0)
        self.assertFalse(self.plotter._user_fmax_set)

        self.plotter.update_nyquist_fmax(self.stream)
        self.assertEqual(self.plotter.pref_manager.get_value('fmax'), 50.0)
        self.assertFalse(self.plotter._user_fmax_set)

    def test_auto_reset_to_nyquist_when_zero_or_empty(self):
        ''' Verify that setting fmax to 0.0 or None automatically resets to Nyquist frequency.
        '''
        # First set a custom fmax
        self.plotter.pref_manager.set_value('fmax', 20.0)
        self.plotter.on_pref_input_changed()
        self.assertEqual(self.plotter.pref_manager.get_value('fmax'), 20.0)
        self.assertTrue(self.plotter._user_fmax_set)

        # Reset fmax to 0.0
        self.plotter.pref_manager.set_value('fmax', 0.0)
        self.plotter.on_pref_input_changed()
        self.assertEqual(self.plotter.pref_manager.get_value('fmax'), 50.0)
        self.assertFalse(self.plotter._user_fmax_set)

        # Setting None should also reset to Nyquist
        self.plotter.pref_manager.set_value('fmax', None)
        self.plotter.on_pref_input_changed()
        self.assertEqual(self.plotter.pref_manager.get_value('fmax'), 50.0)
        self.assertFalse(self.plotter._user_fmax_set)

    def test_auto_clamping_fmax_above_nyquist(self):
        ''' Verify setting fmax > Nyquist clamps fmax to Nyquist.
        '''
        self.plotter.pref_manager.set_value('fmax', 80.0)
        self.plotter.on_pref_input_changed()
        self.assertEqual(self.plotter.pref_manager.get_value('fmax'), 50.0)
        self.assertFalse(self.plotter._user_fmax_set)

    def test_auto_clamping_negative_fmin(self):
        ''' Verify setting negative fmin clamps fmin to 0.0.
        '''
        self.plotter.pref_manager.set_value('fmin', -10.0)
        self.plotter.on_pref_input_changed()
        self.assertEqual(self.plotter.pref_manager.get_value('fmin'), 0.0)

    def test_on_pref_input_changed_does_not_trigger_redraw(self):
        ''' Verify on_pref_input_changed performs validation without calling update_display or plot.
        '''
        self.parent.update_display.reset_mock()
        self.plotter.plot = MagicMock()
        self.plotter.pref_manager.set_value('fmin', 5.0)
        self.plotter.on_pref_input_changed()
        self.parent.update_display.assert_not_called()
        self.plotter.plot.assert_not_called()

    def test_on_process_fast_path(self):
        ''' Verify on_process re-plots directly via self.plot(dm, data_mgr) when procStream exists.
        '''
        self.parent.update_display.reset_mock()
        self.plotter.plot = MagicMock()
        self.plotter.pref_manager.set_value('fmin', 5.0)
        self.plotter.on_process()
        self.plotter.plot.assert_called_once_with(self.display_manager, self.data_manager)
        self.parent.update_display.assert_not_called()

    def test_on_process_fallback_when_no_procstream(self):
        ''' Verify on_process falls back to parent.update_display() when procStream is not loaded.
        '''
        self.data_manager.procStream = None
        self.parent.update_display.reset_mock()
        self.plotter.plot = MagicMock()
        self.plotter.on_process()
        self.parent.update_display.assert_called_once()
        self.plotter.plot.assert_not_called()

    def _create_test_view(self):
        ''' Helper to construct a headless SpectrogramView with a matplotlib figure and axes.
        '''
        view = SpectrogramView.__new__(SpectrogramView)
        view.logger = psysmon.get_logger(view)
        view.plot_panel = MagicMock()
        fig = Figure()
        view.plot_panel.axes = fig.add_subplot(111)
        return view

    def test_spectrogram_full_range_rendering(self):
        ''' Test full frequency range rendering when fmin=0.0 and fmax=0.0.
        '''
        view = self._create_test_view()
        data = np.sin(np.linspace(0, 100, 1000, dtype=np.float32))

        view.spectrogram(data, samp_rate=100.0, wlen=1.0, fmin=0.0, fmax=0.0)

        # Lowest non-DC frequency bin
        self.assertAlmostEqual(view.freq[0], 0.78125, places=3)
        # Nyquist frequency bin
        self.assertAlmostEqual(view.freq[-1], 50.0, places=3)

        ylim = view.axes.get_ylim()
        self.assertLess(ylim[0], 1.0)
        self.assertGreaterEqual(ylim[1], 50.0)

    def test_spectrogram_band_slicing_and_y_zoom(self):
        ''' Test slicing frequency bins and zooming y-axis to [fmin, fmax].
        '''
        view = self._create_test_view()
        data = np.sin(np.linspace(0, 100, 1000, dtype=np.float32))

        view.spectrogram(data, samp_rate=100.0, wlen=1.0, fmin=5.0, fmax=20.0)

        # Frequencies are sliced
        self.assertGreaterEqual(view.freq[0], 4.5)
        self.assertLessEqual(view.freq[0], 5.5)
        self.assertGreaterEqual(view.freq[-1], 19.5)
        self.assertLessEqual(view.freq[-1], 20.5)

        # Axes y-limits are zoomed exactly to [5.0, 20.0]
        ylim = view.axes.get_ylim()
        self.assertAlmostEqual(ylim[0], 5.0, places=4)
        self.assertAlmostEqual(ylim[1], 20.0, places=4)

    def test_spectrogram_fmin_only(self):
        ''' Test lower frequency limit only.
        '''
        view = self._create_test_view()
        data = np.sin(np.linspace(0, 100, 1000, dtype=np.float32))

        view.spectrogram(data, samp_rate=100.0, wlen=1.0, fmin=10.0, fmax=0.0)

        ylim = view.axes.get_ylim()
        self.assertAlmostEqual(ylim[0], 10.0, places=4)
        self.assertGreaterEqual(ylim[1], 50.0)

    def test_spectrogram_fmax_only(self):
        ''' Test upper frequency limit only.
        '''
        view = self._create_test_view()
        data = np.sin(np.linspace(0, 100, 1000, dtype=np.float32))

        view.spectrogram(data, samp_rate=100.0, wlen=1.0, fmin=0.0, fmax=15.0)

        ylim = view.axes.get_ylim()
        self.assertLess(ylim[0], 1.0)
        self.assertAlmostEqual(ylim[1], 15.0, places=4)

    def test_spectrogram_invalid_band_fallback(self):
        ''' Test fallback to full band when fmin >= fmax.
        '''
        view = self._create_test_view()
        data = np.sin(np.linspace(0, 100, 1000, dtype=np.float32))

        # fmin > fmax
        view.spectrogram(data, samp_rate=100.0, wlen=1.0, fmin=30.0, fmax=10.0)

        # Safe fallback to full range up to 50 Hz
        self.assertAlmostEqual(view.freq[-1], 50.0, places=3)
        ylim = view.axes.get_ylim()
        self.assertGreaterEqual(ylim[1], 50.0)

    def test_measure_in_sliced_band(self):
        ''' Test that measure snaps accurately within the sliced frequency band.
        '''
        view = self._create_test_view()
        data = np.sin(np.linspace(0, 100, 1000, dtype=np.float32))

        view.spectrogram(data, samp_rate=100.0, wlen=1.0, fmin=10.0, fmax=25.0)

        event = MagicMock()
        event.inaxes = view.axes
        event.xdata = view.time[len(view.time) // 2]
        event.ydata = 18.0

        measurement = view.measure(event)
        self.assertIsNotNone(measurement)
        self.assertEqual(measurement['label'], 'frequency')
        self.assertEqual(measurement['units'], 'Hz')

        # Snapped frequency must be in the [10.0, 25.0] range
        snap_f = measurement['xy'][1]
        self.assertGreaterEqual(snap_f, 10.0 - 0.5)
        self.assertLessEqual(snap_f, 25.0 + 0.5)
        self.assertAlmostEqual(snap_f, 18.0, delta=1.0)

    def test_spectrogram_y_refinement_pad_factor(self):
        ''' Verify that pad_factor refines the vertical frequency resolution (4x bins).
        '''
        data = np.sin(np.linspace(0, 100, 1000, dtype=np.float32))

        # Standard 1x view
        view1 = self._create_test_view()
        view1.spectrogram(data, samp_rate=100.0, wlen=1.0, fmin=5.0, fmax=20.0, pad_factor=1)

        # Refined 4x view
        view4 = self._create_test_view()
        view4.spectrogram(data, samp_rate=100.0, wlen=1.0, fmin=5.0, fmax=20.0, pad_factor=4)

        # With wlen=1.0 s and fs=100 Hz, NFFT=128:
        # 1x df is 100 / 128 = 0.78125 Hz
        # 4x df is 100 / 512 = 0.1953125 Hz
        df1 = view1.freq[1] - view1.freq[0]
        df4 = view4.freq[1] - view4.freq[0]
        self.assertAlmostEqual(df1, 0.78125, places=5)
        self.assertAlmostEqual(df4, 0.1953125, places=5)
        self.assertAlmostEqual(df4, df1 / 4.0, places=5)

        # Frequency bin count across [5.0, 20.0] Hz is ~4x larger in view4
        self.assertGreaterEqual(len(view4.freq), len(view1.freq) * 3)

        # Axes y-limits remain zoomed to [5.0, 20.0]
        ylim4 = view4.axes.get_ylim()
        self.assertAlmostEqual(ylim4[0], 5.0, places=4)
        self.assertAlmostEqual(ylim4[1], 20.0, places=4)

        # Measurement snaps accurately on refined grid
        event = MagicMock()
        event.inaxes = view4.axes
        event.xdata = view4.time[len(view4.time) // 2]
        event.ydata = 12.345
        m4 = view4.measure(event)
        self.assertIsNotNone(m4)
        self.assertAlmostEqual(m4['xy'][1], 12.345, delta=df4)

    def test_plotChannel_passes_pad_factor(self):
        ''' Verify plotChannel correctly translates y_refinement choice into pad_factor.
        '''
        mock_channel = MagicMock()
        mock_channel.name = 'HHZ'
        mock_channel.parent.name = 'STA'
        mock_channel.parent.network = 'XX'
        mock_channel.parent.location = ''
        mock_channel.parent.obspy_location = ''

        mock_view = MagicMock()
        self.display_manager.getViewContainer.return_value = [mock_view]
        self.display_manager.startTime.timestamp = 0.0
        self.display_manager.endTime.timestamp = 10.0

        # Test '4x'
        self.plotter.pref_manager.set_value('y_refinement', '4x')
        self.plotter.plotChannel(self.display_manager, self.data_manager, [mock_channel])

        mock_view.plot.assert_called_once()
        _, kwargs = mock_view.plot.call_args
        self.assertEqual(kwargs.get('pad_factor'), 4)

        # Test default '1x (standard)'
        mock_view.plot.reset_mock()
        self.plotter.pref_manager.set_value('y_refinement', '1x (standard)')
        self.plotter.plotChannel(self.display_manager, self.data_manager, [mock_channel])

        mock_view.plot.assert_called_once()
        _, kwargs = mock_view.plot.call_args
        self.assertEqual(kwargs.get('pad_factor'), 1)

    def test_spectrogram_short_input_padding(self):
        ''' Verify that signals shorter than window length (len(data) < nfft) are zero-padded without error.
        '''
        view = self._create_test_view()
        short_data = np.ones(50, dtype=np.float32)  # shorter than nfft=128

        view.spectrogram(short_data, samp_rate=100.0, wlen=1.0)
        self.assertGreaterEqual(len(view.freq), 1)
        self.assertEqual(len(view.time), 1)
        self.assertEqual(len(view.axes.images), 1)

    def test_spectrogram_display_decimation_preserves_resolution_and_peaks(self):
        ''' Verify that large spectrograms (> 3000 cols) are decimated for display while self.time remains full resolution.
        '''
        view = self._create_test_view()
        # 100 Hz, 4000 steps requires 4000 * 64 = 256,000 samples
        npts = 260000
        data = np.zeros(npts, dtype=np.float32)
        # Inject an amplitude spike at sample 100,000
        data[100000] = 50.0

        view.spectrogram(data, samp_rate=100.0, wlen=1.0, overlap=0.5, amp_mode='square')

        # Full resolution self.time has > 3500 points
        self.assertGreater(len(view.time), 3500)

        # Displayed image array has <= 3000 columns
        img_arr = view.axes.images[0].get_array()
        self.assertLessEqual(img_arr.shape[1], 3000)

        # Peak preservation: maximum of displayed image captures the spike
        self.assertGreater(img_arr.max(), 0.1)

        # Measurement tool continues snapping with full-resolution time array
        event = MagicMock()
        event.inaxes = view.axes
        event.xdata = view.time[1000]
        event.ydata = view.freq[10]
        measurement = view.measure(event)
        self.assertIsNotNone(measurement)
        self.assertAlmostEqual(measurement['xy'][0], view.time[1000], places=4)
        self.assertAlmostEqual(measurement['xy'][1], view.freq[10], places=4)


if __name__ == '__main__':
    unittest.main()


