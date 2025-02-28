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
# along with this program.  If not, see <http://www.gnu.org/licenses/>
'''
The importWaveform module.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3
    http://www.gnu.org/licenses/gpl-3.0.html

'''
from __future__ import division
from builtins import str
from past.utils import old_div
import os

import psysmon.core.packageNodes
import psysmon.core.result as result
import psysmon.core.preferences_manager as psy_pm
import psysmon.gui.dialog.pref_listbook as psy_lb

from obspy.core.utcdatetime import UTCDateTime
import matplotlib.mlab as mlab


class ComputePsdNode(psysmon.core.packageNodes.LooperCollectionChildNode):
    '''
    '''
    name = 'compute PSD'
    mode = 'looper child'
    category = 'Frequency analysis'
    tags = ['development', 'power spectral density']

    def __init__(self, **args):
        psysmon.core.packageNodes.LooperCollectionChildNode.__init__(self, **args)

        self.create_parameters_prefs()

        # The computed psd data.
        self.psd_data = {}

        # Last day of the saved psd data.
        self.save_day = {}

        # The interval for which to create the results. This is ignored when
        # processing events. For events a result is created for each event.
        # TODO: Make the save interval user selectable.
        self.save_interval = 3600.


    def create_parameters_prefs(self):
        ''' Create the preference items of the parameters section.
        '''
        par_page = self.pref_manager.add_page('parameters')
        psd_group = par_page.add_group('fft')

        pref_item = psy_pm.IntegerSpinPrefItem(name = 'psd_nfft',
                                             label = 'nfft',
                                             value = 8192,
                                             limit = [0, 1000000],
                                             tool_tip = 'The length of the fft window [samples].'
                                             )
        psd_group.add_item(pref_item)

        pref_item = psy_pm.IntegerSpinPrefItem(name = 'psd_overlap',
                                             label = 'fft overlap [%]',
                                             value = 50,
                                             limit = [0, 99],
                                             tool_tip = 'The overlap of the fft windows [%].'
                                             )
        psd_group.add_item(pref_item)


    def edit(self):
        ''' Show the node edit dialog.
        '''
        dlg = psy_lb. ListbookPrefDialog(preferences = self.pref_manager)
        dlg.ShowModal()
        dlg.Destroy()


    def execute(self, stream, process_limits = None, origin_resource = None, **kwargs):
        '''
        '''
        psd_nfft = self.pref_manager.get_value('psd_nfft')
        psd_overlap = self.pref_manager.get_value('psd_overlap')

        start_time = process_limits[0]
        end_time = process_limits[1]

        if 'event' in iter(kwargs.keys()):
            cur_event = kwargs['event']
        else:
            cur_event = None

        for cur_trace in stream:
            self.logger.info('###Processing trace with id %s.', cur_trace.id)

            cur_scnl = (cur_trace.stats.station, cur_trace.stats.channel,
                        cur_trace.stats.network, cur_trace.stats.location)

            # Check if a result has to be created.
            if not cur_event:
                self.check_result_needed(cur_scnl, start_time)

            # Get the channel instance from the inventory.
            cur_channel = self.project.geometry_inventory.get_channel(station = cur_trace.stats.station,
                                                                      name = cur_trace.stats.channel,
                                                                      network = cur_trace.stats.network,
                                                                      location = cur_trace.stats.location)
            if len(cur_channel) == 0:
                self.logger.error("No channel found for trace %s", cur_trace.id)
                continue
            elif len(cur_channel) > 1:
                self.logger.error("Multiple channels found for trace %s; channels: %s", cur_trace.id, cur_channel)
            else:
                cur_channel = cur_channel[0]

            psd_data = {}

            if cur_trace:
                # Compute the PSD using matplotlib.mlab.psd
                m_psd_nfft = psd_nfft
                m_pad_to = None
                if len(cur_trace.data) < psd_nfft:
                    m_psd_nfft = old_div(len(cur_trace.data), 4)
                    m_pad_to = psd_nfft
                n_overlap = old_div(m_psd_nfft, 100 * psd_overlap)

                (P, frequ) = mlab.psd(cur_trace.data,
                                      Fs = cur_trace.stats.sampling_rate,
                                      NFFT = m_psd_nfft,
                                      noverlap = n_overlap,
                                      detrend = 'constant',
                                      scale_by_freq = True,
                                      pad_to = m_pad_to)

                if P.ndim == 2:
                    P = P.squeeze()

                # Get the units of the trace data.
                unit = cur_trace.stats.unit

                cur_psd = {}
                cur_psd['sps'] = cur_trace.stats.sampling_rate
                cur_psd['frequ'] = frequ
                cur_psd['P'] = P
                cur_psd['window_length'] = self.parent.pref_manager.get_value('window_length')
                cur_psd['window_overlap'] = self.parent.pref_manager.get_value('window_overlap')
                cur_psd['psd_nfft'] = psd_nfft
                cur_psd['psd_overlap'] = psd_overlap
                cur_psd['scnl'] = cur_scnl
                cur_psd['unit'] = unit
                cur_psd['start_time'] = start_time
                cur_psd['end_time'] = end_time
                psd_data[start_time.isoformat()] = cur_psd
            else:
                cur_psd = {}
                cur_psd['sps'] = None
                cur_psd['frequ'] = None
                cur_psd['P'] = None
                cur_psd['window_length'] = self.parent.pref_manager.get_value('window_length')
                cur_psd['window_overlap'] = self.parent.pref_manager.get_value('window_overlap')
                cur_psd['psd_nfft'] = psd_nfft
                cur_psd['psd_overlap'] = psd_overlap
                cur_psd['scnl'] = cur_scnl
                cur_psd['unit'] = 'undefined'
                cur_psd['start_time'] = start_time
                cur_psd['end_time'] = end_time

            if cur_event:
                cur_psd['event_id'] = cur_event.db_id

            # Store the psd data in the psd dictionary.
            self.save_psd_data(psd = cur_psd,
                               origin_resource = origin_resource)

        if cur_event:
            self.create_event_result(event = cur_event,
                                     origin_resource = origin_resource)


    def save_psd_data(self, psd,
                      origin_resource = None):
        ''' Save the psd data to a file.
        '''
        if not psd:
            return

        scnl = psd['scnl']
        start_time = psd['start_time']

        if scnl not in iter(self.psd_data.keys()):
            self.psd_data[scnl] = {}

        if scnl not in iter(self.save_day.keys()):
            self.save_day[scnl] = None

        if self.save_day[scnl] is None:
            self.save_day[scnl] = UTCDateTime(start_time.timestamp - start_time.timestamp % self.save_interval)

        if 'event_id' in iter(psd.keys()):
            self.psd_data[scnl][psd['event_id']] = psd
        else:
            self.psd_data[scnl][start_time.isoformat()] = psd



    def check_result_needed(self, scnl, start_time,
                            origin_resource = None):
        ''' Check if a result has to be created for the given SCNL.
        '''
        if scnl not in self.save_day.keys():
            return

        last_save_day = self.save_day[scnl]

        # Create a result if the current start time extends the save interval.
        # TODO: The naming of the result when saved by the time window looper
        # uses the wrong start- and end-times. Add a support to specify the
        # valid timespan of the result in the result instance.
        if start_time - last_save_day >= self.save_interval:
            self.create_result(scnl, origin_resource = origin_resource)
            self.save_day[scnl] = UTCDateTime(start_time.timestamp - start_time.timestamp % self.save_interval)



    def create_result(self, scnl, origin_resource = None):
        ''' Write the psd data for the given scnl to file.
        '''
        export_data = self.psd_data[scnl]

        first_time = UTCDateTime(sorted(export_data.keys())[0])
        last_time = UTCDateTime(sorted(export_data.keys())[-1])
        #last_key = sorted(export_data.iterkeys())[-1]
        #last_time = export_data[last_key]['end_time']
        #first_time = sorted([x['start_time'] for x in export_data.values()])[0]
        #last_time = sorted([x['end_time'] for x in export_data.values()])[-1]

        shelve_result = result.ShelveResult(name = 'psd',
                                            start_time = first_time,
                                            end_time = last_time,
                                            origin_name = self.name,
                                            origin_resource = origin_resource,
                                            sub_directory = (scnl[0],
                                                             scnl[1],
                                                             "{0:04d}_{1:03d}".format(first_time.year,
                                                                                      first_time.julday)),
                                            postfix = '_'.join(scnl),
                                            db = export_data)
        self.result_bag.add(shelve_result)
        self.logger.info("Published the result for scnl %s (%s to %s).", scnl,
                                                                         first_time.isoformat(),
                                                                         last_time.isoformat())

        self.psd_data[scnl] = {}


    def create_event_result(self, event, origin_resource = None):
        ''' Write the psd data for the given scnl to file.
        '''
        export_data = dict((str(':'.join(key)), value) for (key, value) in list(self.psd_data.items()))
        export_data['event_id'] = event.db_id

        shelve_result = result.ShelveResult(name = 'psd',
                                            start_time = event.start_time,
                                            end_time = event.end_time,
                                            origin_name = self.name,
                                            origin_resource = origin_resource,
                                            db = export_data)
        self.result_bag.add(shelve_result)
        self.logger.info("Published the result for event %d (%s to %s).",
                         event.db_id,
                         event.start_time.isoformat(),
                         event.end_time.isoformat())

        self.psd_data = {}
        for cur_scnl in export_data.keys():
            self.save_day[cur_scnl] = UTCDateTime(event.start_time.timestamp - event.start_time.timestamp % self.save_interval)

    def cleanup(self, origin_resource = None):
        ''' Publish all remaining psd data to results.
        '''
        for cur_scnl, cur_data in self.psd_data.items():
            if cur_data:
                self.create_result(cur_scnl, origin_resource = origin_resource)



