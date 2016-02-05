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
'''

'''

import unittest
import nose.plugins.attrib as nose_attrib
import psysmon
import logging
import os

from obspy.core.utcdatetime import UTCDateTime

from psysmon.core.test_util import create_psybase
from psysmon.core.test_util import create_empty_project
from psysmon.core.test_util import drop_project_database_tables
from psysmon.core.test_util import clear_project_database_tables
from psysmon.core.test_util import remove_project_filestructure

from psysmon.packages.geometry.db_inventory import DbInventory
from psysmon.packages.geometry.db_inventory import DbNetwork
from psysmon.packages.geometry.db_inventory import DbStation
from psysmon.packages.geometry.db_inventory import DbChannel
from psysmon.packages.geometry.db_inventory import DbRecorder
from psysmon.packages.geometry.db_inventory import DbRecorderStream
from psysmon.packages.geometry.db_inventory import DbSensor
from psysmon.packages.geometry.db_inventory import DbSensorComponent
from psysmon.packages.geometry.db_inventory import DbSensorComponentParameter

from psysmon.packages.geometry.inventory import Network
from psysmon.packages.geometry.inventory import Station
from psysmon.packages.geometry.inventory import Channel
from psysmon.packages.geometry.inventory import Recorder
from psysmon.packages.geometry.inventory import RecorderStream
from psysmon.packages.geometry.inventory import RecorderStreamParameter
from psysmon.packages.geometry.inventory import Sensor
from psysmon.packages.geometry.inventory import SensorComponent
from psysmon.packages.geometry.inventory import SensorComponentParameter
from psysmon.packages.geometry.inventory import TimeBox

from psysmon.packages.geometry.inventory_parser import InventoryXmlParser

class DbInventoryTestCase(unittest.TestCase):
    """
    Test suite for psysmon.packages.geometry.editGeometry.EditGeometryDlg
    """
    @classmethod
    def setUpClass(cls):
        # Configure the logger.
        cls.logger = logging.getLogger('psysmon')
        cls.logger.setLevel('DEBUG')
        cls.logger.addHandler(psysmon.getLoggerHandler(log_level = 'INFO'))

        cls.data_path = os.path.dirname(os.path.abspath(__file__))
        cls.data_path = os.path.join(cls.data_path, 'data')

        cls.psybase = create_psybase()
        cls.project = create_empty_project(cls.psybase)
        cls.project.dbEngine.echo = False
        #cls.full_project = create_full_project(cls.psybase)
        print "In setUpClass...\n"


    @classmethod
    def tearDownClass(cls):
        cls.psybase.stop_project_server()
        print "dropping database tables...\n"
        drop_project_database_tables(cls.project)
        print "removing temporary file structure....\n"
        remove_project_filestructure(cls.project)
        print "removing temporary base directory....\n"
        os.removedirs(cls.project.base_dir)
        print "....finished cleaning up.\n"


    def setUp(self):
        #clear_project_database_tables(self.project)
        pass

    def tearDown(self):
        clear_project_database_tables(self.project)
        print "Es war sehr schoen - auf Wiederseh'n.\n"



    def test_network_setattr(self):
        db_inventory = DbInventory(self.project)

        try:
            # Add a network to the db_inventory.
            network1 = Network(name = 'XX', description = 'A test network.')
            added_network1 = db_inventory.add_network(network1)
            self.assertEqual(db_inventory.networks[0], added_network1)
            self.assertEqual(added_network1.name, 'XX')

            added_network1.name = 'YY'
            self.assertEqual(added_network1.name, 'YY')
            self.assertEqual(added_network1.orm.name, 'YY')

            # Add stations to the XX network.
            station1 = Station(name = 'station1_name',
                               location = '00',
                               x = 11,
                               y = 12,
                               z = 13,
                               coord_system = 'station1_coord_system')
            added_station1 = db_inventory.add_station('YY', station1)
            self.assertTrue(added_station1 in added_network1.stations)

            added_network1.name = 'ZZ'
            self.assertEqual(added_station1.network, 'ZZ')

        finally:
            db_inventory.close()



    def test_add_empty_network_to_inventory(self):
        db_inventory = DbInventory(self.project)

        try:
            # Add a network to the db_inventory.
            network1 = Network(name = 'XX', description = 'A test network.')
            added_network1 = db_inventory.add_network(network1)
            self.assertIsInstance(added_network1, DbNetwork)
            self.assertEqual(len(db_inventory.networks), 1)
            self.assertIs(db_inventory.networks[0], added_network1)

            db_inventory.commit()
        finally:
            db_inventory.close()


    def test_add_network_to_inventory(self):
        db_inventory = DbInventory(self.project)

        try:
            # Add networks to the db_inventory.
            network1 = Network(name = 'XX', description = 'A test network.')

            # Add stations to the XX network.
            station1 = Station(name = 'station1_name',
                               location = '00',
                               x = 11,
                               y = 12,
                               z = 13,
                               coord_system = 'station1_coord_system')

            station2 = Station(name = 'station2_name',
                               location = '00',
                               x = 21,
                               y = 22,
                               z = 23,
                               coord_system = 'station2_coord_system')


            channel1 = Channel(name = 'channel1_name',
                               description = 'channel1_description')
            channel2 = Channel(name = 'channel2_name',
                               description = 'channel2_description')

            station1.add_channel(channel1)
            station2.add_channel(channel2)

            network1.add_station(station1)
            network1.add_station(station2)

            added_network1 = db_inventory.add_network(network1)


            self.assertEqual(len(db_inventory.networks), 1)
            self.assertTrue(added_network1 in db_inventory.networks)
            self.assertEqual(len(added_network1.stations), 2)
            self.assertEqual(len(added_network1.orm.stations), 2)
            self.assertEqual(added_network1.stations[0].name, 'station1_name')
            self.assertEqual(added_network1.stations[1].name, 'station2_name')
            self.assertEqual(len(added_network1.stations[0].channels), 1)
            self.assertEqual(len(added_network1.stations[1].channels), 1)
            self.assertEqual(added_network1.stations[0].channels[0].name, 'channel1_name')
            self.assertEqual(added_network1.stations[1].channels[0].name, 'channel2_name')

            
            db_inventory.commit()
        finally:
            db_inventory.close()


    def test_add_station_to_inventory(self):
        db_inventory = DbInventory(self.project)

        try:
            # Add networks to the db_inventory.
            network1 = Network(name = 'XX', description = 'A test network.')
            added_network1 = db_inventory.add_network(network1)

            network2 = Network(name = 'YY', description = 'A test network.')
            added_network2 = db_inventory.add_network(network2)

            # Add stations to the XX network.
            station1 = Station(name = 'station1_name',
                               location = '00',
                               x = 11,
                               y = 12,
                               z = 13,
                               coord_system = 'station1_coord_system')

            station2 = Station(name = 'station2_name',
                               location = '00',
                               x = 21,
                               y = 22,
                               z = 23,
                               coord_system = 'station2_coord_system')

            station3 = Station(name = 'station3_name',
                               location = '00',
                               x = 31,
                               y = 32,
                               z = 33,
                               coord_system = 'station3_coord_system')


            channel1 = Channel(name = 'channel1_name',
                               description = 'channel1_description')
            channel2 = Channel(name = 'channel2_name',
                               description = 'channel2_description')
            channel3 = Channel(name = 'channel3_name',
                               description = 'channel3_description')

            station1.add_channel(channel1)
            station2.add_channel(channel2)
            station3.add_channel(channel3)

            added_station1 = db_inventory.add_station('XX', station1)
            added_station2 = db_inventory.add_station('YY', station2)
            added_station3 = db_inventory.add_station('ZZ', station3)

            self.assertEqual(len(db_inventory.networks), 2)
            self.assertTrue(added_network1 in db_inventory.networks)
            self.assertTrue(added_network2 in db_inventory.networks)
            self.assertEqual(len(added_network1.stations), 1)
            self.assertEqual(len(added_network1.orm.stations), 1)
            self.assertTrue(added_station1 in added_network1.stations)
            self.assertEqual(len(added_network2.stations), 1)
            self.assertEqual(len(added_network2.orm.stations), 1)
            self.assertTrue(added_station2 in added_network2.stations)
            self.assertIsNone(added_station3)

            self.assertEqual(len(added_station1.channels), 1)
            self.assertEqual(len(added_station2.channels), 1)

            self.assertIsInstance(added_station1.channels[0], DbChannel)
            self.assertIsInstance(added_station2.channels[0], DbChannel)

            db_inventory.commit()
        finally:
            db_inventory.close()




    def test_add_sensor_to_inventory(self):
        db_inventory = DbInventory(self.project)

        try:
            sensor1 = Sensor(serial = 'sensor1_name',
                             model = 'sensor1_model',
                             producer = 'sensor1_producer')

            sensor2 = Sensor(serial = 'sensor2_name',
                             model = 'sensor2_model',
                             producer = 'sensor2_producer')

            sensor3 = Sensor(serial = 'sensor3_name',
                             model = 'sensor3_model',
                             producer = 'sensor3_producer')

            component1 = SensorComponent(name = 'comp1_name',
                                     input_unit = 'm',
                                     output_unit = 'm/s',
                                     deliver_unit = 'V')
            component2 = SensorComponent(name = 'comp2_name',
                                     input_unit = 'm',
                                     output_unit = 'm/s',
                                     deliver_unit = 'V')
            component3 = SensorComponent(name = 'comp3_name',
                                     input_unit = 'm',
                                     output_unit = 'm/s',
                                     deliver_unit = 'V')

            cur_start_time = UTCDateTime('2014-01-01')
            cur_end_time = UTCDateTime('2014-02-01')
            parameter1 = SensorComponentParameter(sensitivity = 1,
                                              start_time = cur_start_time,
                                              end_time = cur_end_time,
                                              tf_poles = [complex('1+1j'), complex('1+2j')],
                                              tf_zeros = [complex('0+1j'), complex('0+2j')])

            component1.add_parameter(parameter1)

            sensor1.add_component(component1)
            sensor2.add_component(component2)
            sensor3.add_component(component3)

            added_sensor1 = db_inventory.add_sensor(sensor1)
            added_sensor2 = db_inventory.add_sensor(sensor2)
            added_sensor3 = db_inventory.add_sensor(sensor3)

            self.assertEqual(len(db_inventory.sensors), 3)
            self.assertTrue(added_sensor1 in db_inventory.sensors)
            self.assertTrue(added_sensor2 in db_inventory.sensors)
            self.assertTrue(added_sensor3 in db_inventory.sensors)

            self.assertEqual(len(db_inventory.sensors[0].components), 1)
            self.assertIsInstance(db_inventory.sensors[0].components[0], DbSensorComponent)
            self.assertEqual(len(db_inventory.sensors[0].components[0].parameters), 1)
            self.assertIsInstance(db_inventory.sensors[0].components[0].parameters[0], DbSensorComponentParameter)

            self.assertEqual(db_inventory.sensors[0].components[0].orm.input_unit, 'm')
            self.assertEqual(db_inventory.sensors[0].components[0].orm.output_unit, 'm/s')
            self.assertEqual(db_inventory.sensors[0].components[0].orm.deliver_unit, 'V')

            db_inventory.commit()
        finally:
            db_inventory.close()


    def test_add_recorder_to_inventory(self):
        db_inventory = DbInventory(self.project)

        try:
            recorder1 = Recorder(serial = 'recorder1_serial',
                                 model = 'recorder1_model',
                                 producer = 'recorder1_producer')

            recorder2 = Recorder(serial = 'recorder2_serial',
                                 model = 'recorder2_model',
                                 producer = 'recorder2_producer')

            stream1 = RecorderStream(name = 'stream1_name',
                                     label = 'stream1_label')


            cur_start_time = UTCDateTime('2014-01-01')
            cur_end_time = UTCDateTime('2014-02-01')
            parameter1 = RecorderStreamParameter(gain = 1,
                                                 bitweight = 0.1,
                                                 start_time = cur_start_time,
                                                 end_time = cur_end_time)

            stream1.add_parameter(parameter1)
            recorder1.add_stream(stream1)
            added_recorder1 = db_inventory.add_recorder(recorder1)
            added_recorder2 = db_inventory.add_recorder(recorder2)

            self.assertEqual(len(db_inventory.recorders), 2)
            self.assertEqual(db_inventory.recorders[0], added_recorder1)
            self.assertEqual(db_inventory.recorders[1], added_recorder2)
            self.assertEqual(db_inventory.recorders[0].streams[0].name, 'stream1_name')

            db_inventory.commit()
        finally:
            db_inventory.close()


    def test_add_stream_to_channel(self):
        ''' Test assigning a stream to a channel.
        '''
        db_inventory = DbInventory(self.project)

        try:
            # Create a recorder and a stream.
            recorder1 = Recorder(serial = 'recorder1_serial',
                                 model = 'recorder1_model',
                                 producer = 'recorder1_producer')

            stream1 = RecorderStream(name = 'stream1_name',
                                     label = 'stream1_label')

            recorder1.add_stream(stream1)

            # Create a network with stations and channels.
            network1 = Network(name = 'XX', description = 'A test network.')

            station1 = Station(name = 'station1_name',
                               location = '00',
                               x = 11,
                               y = 12,
                               z = 13,
                               coord_system = 'station1_coord_system')

            station2 = Station(name = 'station2_name',
                               location = '00',
                               x = 21,
                               y = 22,
                               z = 23,
                               coord_system = 'station2_coord_system')

            channel1 = Channel(name = 'channel1_name',
                               description = 'channel1_description')
            channel2 = Channel(name = 'channel2_name',
                               description = 'channel2_description')

            station1.add_channel(channel1)
            station2.add_channel(channel2)

            network1.add_station(station1)
            network1.add_station(station2)

            # Add the objects to the inventory.
            added_recorder1 = db_inventory.add_recorder(recorder1)
            added_network1 = db_inventory.add_network(network1)


            # Add the stream to a channel.
            cur_start_time = UTCDateTime('2014-01-01')
            cur_end_time = UTCDateTime('2014-02-01')
            cur_channel = added_network1.stations[0].channels[0]
            cur_channel.add_stream(serial = 'recorder1_serial',
                                   model = 'recorder1_model',
                                   producer = 'recorder1_producer',
                                   name = 'stream1_name',
                                   start_time = cur_start_time,
                                   end_time = cur_end_time)


            self.assertEqual(len(added_network1.stations), 2)
            self.assertEqual(len(added_network1.orm.stations), 2)
            self.assertEqual(len(added_network1.stations[0].channels[0].streams), 1)
            self.assertEqual(len(added_network1.stations[1].channels[0].streams), 0)
            self.assertEqual(added_network1.stations[0].channels[0].streams[0].item.name, 'stream1_name')

            db_inventory.commit()
        finally:
            db_inventory.close()


    def test_add_component_to_stream(self):
        db_inventory = DbInventory(self.project)

        try:
            recorder1 = Recorder(serial = 'recorder1_serial',
                                 model = 'recorder1_model',
                                 producer = 'recorder1_producer')


            stream1 = RecorderStream(name = 'stream1_name',
                                     label = 'stream1_label')


            sensor1 = Sensor(serial = 'sensor1_serial',
                             model = 'sensor1_model',
                             producer = 'sensor1_producer')
            component1 = SensorComponent(name = 'comp1_name')

            sensor1.add_component(component1)
            recorder1.add_stream(stream1)

            cur_start_time = UTCDateTime('2014-01-01')
            cur_end_time = UTCDateTime('2014-02-01')

            # Add the recorder and the sensor to the inventory before 
            # adding the stream.
            db_recorder1 = db_inventory.add_recorder(recorder1)
            db_sensor1 = db_inventory.add_sensor(sensor1)

            db_stream1 = db_recorder1.streams[0]
            db_stream1.add_component(serial = 'sensor1_serial',
                                     model = 'sensor1_model',
                                     producer = 'sensor1_producer',
                                     name = 'comp1_name',
                                     start_time = cur_start_time,
                                     end_time = cur_end_time)


            self.assertIsInstance(db_recorder1, DbRecorder)
            self.assertIs(db_inventory.recorders[0], db_recorder1)
            self.assertEqual(len(db_recorder1.streams), 1)
            self.assertEqual(len(db_recorder1.streams[0].components), 1)

            db_inventory.commit()
        finally:
            db_inventory.close()


    def test_remove_network(self):
        print "test_remove_network\n"
        db_inventory = DbInventory(self.project)

        try:
            # Add a network to the db_inventory.
            net_2_add = Network(name = 'XX', description = 'A test network.')
            added_network_1 = db_inventory.add_network(net_2_add)
            self.assertIsInstance(added_network_1, DbNetwork)
            self.assertEqual(len(db_inventory.networks), 1)

            net_2_add = Network(name = 'YY', description = 'A second test network.')
            added_network_2 = db_inventory.add_network(net_2_add)
            self.assertIsInstance(added_network_2, DbNetwork)
            self.assertEqual(len(db_inventory.networks), 2)


            removed_network = db_inventory.remove_network('XX')
            self.assertEqual(len(db_inventory.networks), 1)
            self.assertIsInstance(removed_network, DbNetwork)
            self.assertEqual(added_network_1, removed_network)
            self.assertEqual(added_network_2, db_inventory.networks[0])


            removed_network = db_inventory.remove_network('YY')
            self.assertEqual(len(db_inventory.networks), 0)
            self.assertIsInstance(removed_network, DbNetwork)
            self.assertEqual(added_network_2, removed_network)
            db_inventory.commit()
        finally:
            db_inventory.close()



    def test_remove_station(self):
        db_inventory = DbInventory(self.project)
        try:
            # Add a network to the db_inventory.
            net_2_add = Network(name = 'XX', description = 'A test network.')
            added_network_1 = db_inventory.add_network(net_2_add)

            net_2_add = Network(name = 'YY', description = 'A second test network.')
            added_network_2 = db_inventory.add_network(net_2_add)

            # Add a station to the XX network.
            stat_2_add = Station(name = 'AAA',
                                 location = '00',
                                 x = 0,
                                 y = 0,
                                 z = 0,
                                 coord_system = 'epsg:4316')
            added_station_1 = db_inventory.add_station(network_name = 'XX',
                                                       station_to_add = stat_2_add)

            # Add a station to the YY network.
            stat_2_add = Station(name = 'AAA',
                                 location = '00',
                                 x = 0,
                                 y = 0,
                                 z = 0,
                                 coord_system = 'epsg:4316')
            added_station_2 = added_network_2.add_station(stat_2_add)

            removed_station = db_inventory.remove_station(('AAA', 'XX', '00'))
            self.assertEqual(removed_station, added_station_1)
            self.assertEqual(len(added_network_1.stations), 0)
            self.assertEqual(len(added_network_1.orm.stations), 0)

            removed_station = db_inventory.remove_station(('AAA', 'YY', '00'))
            self.assertEqual(removed_station, added_station_2)
            self.assertEqual(len(added_network_2.stations), 0)
            self.assertEqual(len(added_network_2.orm.stations), 0)
            db_inventory.commit()
        finally:
            db_inventory.close()


    def test_move_station(self):
        db_inventory = DbInventory(self.project)
        try:
            # Add a network to the db_inventory.
            net_2_add = Network(name = 'XX', description = 'A test network.')
            added_network_1 = db_inventory.add_network(net_2_add)

            net_2_add = Network(name = 'YY', description = 'A second test network.')
            added_network_2 = db_inventory.add_network(net_2_add)

            # Add a station to the XX network.
            stat_2_add = Station(name = 'AAA',
                                 location = '00',
                                 x = 0,
                                 y = 0,
                                 z = 0,
                                 coord_system = 'epsg:4316')
            added_station_1 = added_network_1.add_station(stat_2_add)

            removed_station = added_network_1.remove_station(name = 'AAA', location = '00')
            added_network_2.add_station(removed_station)

            self.assertEqual(len(added_network_1.stations), 0)
            self.assertEqual(len(added_network_2.stations), 1)
            self.assertEqual(added_network_2.stations[0], added_station_1)
            self.assertEqual(len(added_network_1.orm.stations), 0)
            self.assertEqual(len(added_network_2.orm.stations), 1)

            # Commit the changes to the database.
            #db_inventory.commit()

            #removed_station = added_network_2.remove_station(name = 'AAA', location = '00')
            #added_network_1.add_station(removed_station)

            db_inventory.commit()
        finally:
            db_inventory.close()


    def test_load_sensor(self):
        db_inventory = DbInventory(self.project, name = 'write')

        try:
            sensor1 = Sensor(serial = 'sensor1_serial',
                             model = 'sensor1_model',
                             producer = 'sensor1_producer')

            sensor2 = Sensor(serial = 'sensor2_serial',
                             model = 'sensor2_model',
                             producer = 'sensor2_producer')

            sensor3 = Sensor(serial = 'sensor3_serial',
                             model = 'sensor3_model',
                             producer = 'sensor3_producer')

            component1 = SensorComponent(name = 'comp1_name')
            component2 = SensorComponent(name = 'comp2_name')
            component3 = SensorComponent(name = 'comp3_name')

            cur_start_time = UTCDateTime('2014-01-01')
            cur_end_time = UTCDateTime('2014-02-01')
            parameter1 = SensorComponentParameter(sensitivity = 1,
                                              start_time = cur_start_time,
                                              end_time = cur_end_time,
                                              tf_poles = [complex('1+1j'), complex('1+2j')],
                                              tf_zeros = [complex('0+1j'), complex('0+2j')])

            component1.add_parameter(parameter1)

            sensor1.add_component(component1)
            sensor2.add_component(component2)
            sensor3.add_component(component3)

            db_inventory.add_sensor(sensor1)
            db_inventory.add_sensor(sensor2)
            db_inventory.add_sensor(sensor3)

            db_inventory.commit()
        finally:
            db_inventory.close()

        try:
            # Load the networks from the database.
            db_inventory_load = DbInventory(self.project, name = 'load')
            db_inventory_load.load_sensors()
        finally:
            db_inventory_load.close()

        self.assertEqual(len(db_inventory_load.sensors), 3)
        cur_sensor = db_inventory_load.sensors[0]
        self.assertEqual(cur_sensor.serial, 'sensor1_serial')
        self.assertEqual(cur_sensor.model, 'sensor1_model')
        self.assertEqual(cur_sensor.producer, 'sensor1_producer')
        self.assertEqual(len(cur_sensor.components), 1)
        self.assertEqual(len(cur_sensor.orm.components), 1)

        cur_component = cur_sensor.components[0]
        self.assertEqual(cur_component.name, 'comp1_name')
        self.assertEqual(len(cur_component.parameters), 1)
        self.assertEqual(len(cur_component.orm.parameters), 1)

        cur_parameter = cur_component.parameters[0]
        self.assertEqual(len(cur_parameter.orm.tf_pz), 4)
        self.assertEqual(cur_parameter.sensitivity, 1)
        self.assertEqual(cur_parameter.start_time.isoformat(), cur_start_time.isoformat())
        self.assertEqual(cur_parameter.end_time.isoformat(), cur_end_time.isoformat())
        self.assertEqual(cur_parameter.tf_poles, [complex('1+1j'), complex('1+2j')])
        self.assertEqual(cur_parameter.tf_zeros, [complex('0+1j'), complex('0+2j')])



    def test_load_recorder(self):
        db_inventory = DbInventory(self.project)

        try:
            # Add recorders to the database.
            recorder1 = Recorder(serial = 'recorder1_serial',
                                 model = 'recorder1_model',
                                 producer = 'recorder1_producer')

            recorder2 = Recorder(serial = 'recorder2_serial',
                                 model = 'recorder2_model',
                                 producer = 'recorder2_producer')

            stream1 = RecorderStream(name = 'stream1_name',
                                     label = 'stream1_label')


            cur_start_time = UTCDateTime('2014-01-01')
            cur_end_time = UTCDateTime('2014-02-01')
            parameter1 = RecorderStreamParameter(gain = 1,
                                                 bitweight = 0.1,
                                                 start_time = cur_start_time,
                                                 end_time = cur_end_time)

            stream1.add_parameter(parameter1)
            recorder1.add_stream(stream1)
            db_inventory.add_recorder(recorder1)
            db_inventory.add_recorder(recorder2)

            # Commit the changes to the database.
            db_inventory.commit()
        finally:
            db_inventory.close()

        # Load the recorders from the database.
        db_inventory_load = DbInventory(self.project)
        try:
            db_inventory_load.load_recorders()
        finally:
            db_inventory_load.close()
        self.assertEqual(len(db_inventory_load.recorders), 2)
        cur_recorder = db_inventory_load.recorders[0]
        self.assertEqual(len(cur_recorder.streams), 1)
        self.assertEqual(len(cur_recorder.orm.streams), 1)
        self.assertEqual(cur_recorder.serial, 'recorder1_serial')
        self.assertEqual(cur_recorder.model, 'recorder1_model')
        self.assertEqual(cur_recorder.producer, 'recorder1_producer')
        self.assertIsNotNone(cur_recorder.id)

        cur_stream = cur_recorder.streams[0]
        self.assertEqual(cur_stream.name, 'stream1_name')
        self.assertEqual(cur_stream.label, 'stream1_label')
        self.assertEqual(cur_stream.parent_recorder, cur_recorder)

        self.assertEqual(len(cur_stream.parameters), 1)
        self.assertEqual(len(cur_stream.orm.parameters), 1)
        cur_parameter = cur_stream.parameters[0]
        self.assertEqual(cur_parameter.gain, 1)
        self.assertEqual(cur_parameter.bitweight, 0.1)
        self.assertEqual(cur_parameter.start_time.isoformat, cur_start_time.isoformat)
        self.assertEqual(cur_parameter.end_time.isoformat, cur_end_time.isoformat)


        cur_recorder = db_inventory_load.recorders[1]
        self.assertEqual(len(cur_recorder.streams), 0)





    def test_load_recorder_with_components(self):
        db_inventory = DbInventory(self.project)

        try:
            sensor1 = Sensor(serial = 'sensor1_serial',
                             model = 'sensor1_model',
                             producer = 'sensor1_producer')

            sensor2 = Sensor(serial = 'sensor2_serial',
                             model = 'sensor2_model',
                             producer = 'sensor2_producer')

            component1 = SensorComponent(name = 'comp1_name')
            component2 = SensorComponent(name = 'comp2_name')

            cur_start_time = UTCDateTime('2014-01-01')
            cur_end_time = UTCDateTime('2014-02-01')
            parameter1 = SensorComponentParameter(sensitivity = 1,
                                              start_time = cur_start_time,
                                              end_time = cur_end_time,
                                              tf_poles = [complex('1+1j'), complex('1+2j')],
                                              tf_zeros = [complex('0+1j'), complex('0+2j')])

            component1.add_parameter(parameter1)

            sensor1.add_component(component1)
            sensor2.add_component(component2)

            db_inventory.add_sensor(sensor1)
            db_inventory.add_sensor(sensor2)

            # Add recorders to the database.
            recorder1 = Recorder(serial = 'recorder1_serial',
                                 model = 'recorder1_model',
                                 producer = 'recorder1_producer')

            recorder2 = Recorder(serial = 'recorder2_serial',
                                 model = 'recorder2_model',
                                 producer = 'recorder2_producer')

            stream1 = RecorderStream(name = 'stream1_name',
                                     label = 'stream1_label')


            cur_start_time = UTCDateTime('2014-01-01')
            cur_end_time = UTCDateTime('2014-02-01')
            parameter1 = RecorderStreamParameter(gain = 1,
                                                 bitweight = 0.1,
                                                 start_time = cur_start_time,
                                                 end_time = cur_end_time)

            stream1.add_parameter(parameter1)
            recorder1.add_stream(stream1)

            db_inventory.add_recorder(recorder1)
            db_inventory.add_recorder(recorder2)

            cur_recorder = db_inventory.get_recorder(serial = 'recorder1_serial')
            cur_recorder = cur_recorder[0]
            cur_stream = cur_recorder.get_stream(name = 'stream1_name')
            cur_stream = cur_stream[0]
            cur_stream.add_component(serial = 'sensor1_serial',
                                     model = 'sensor1_model',
                                     producer = 'sensor1_producer',
                                     name = 'comp1_name',
                                     start_time = cur_start_time,
                                     end_time = cur_end_time)

            # Commit the changes to the database.
            db_inventory.commit()
        finally:
            db_inventory.close()

        try:
            # Load the networks from the database.
            db_inventory_load = DbInventory(self.project)
            # Load the sensors first, they are needed to add components to the
            # recorders.
            db_inventory_load.load_sensors()
            db_inventory_load.load_recorders()
        finally:
            db_inventory_load.close()

        self.assertEqual(len(db_inventory_load.recorders), 2)
        self.assertEqual(db_inventory_load.recorders[0].serial, 'recorder1_serial')
        self.assertEqual(db_inventory_load.recorders[1].serial, 'recorder2_serial')
        cur_rec = db_inventory_load.recorders[0]
        self.assertIsInstance(cur_rec, DbRecorder)
        self.assertEqual(len(cur_rec.streams), 1)
        cur_stream = cur_rec.streams[0]
        self.assertIsInstance(cur_stream, DbRecorderStream)
        self.assertEqual(len(cur_stream.components), 1)
        self.assertIsInstance(cur_stream.components[0], TimeBox)
        cur_component = cur_stream.components[0].item
        self.assertEqual(cur_component.serial, 'sensor1_serial')
        self.assertEqual(cur_component.name, 'comp1_name')
        self.assertEqual(cur_stream.components[0].start_time.isoformat, cur_start_time.isoformat)
        self.assertEqual(cur_stream.components[0].end_time.isoformat, cur_end_time.isoformat)



    def test_load_network(self):
        db_inventory = DbInventory(self.project)

        try:
            # Add networks to the db_inventory.
            network1 = Network(name = 'XX', description = 'network1_description')

            network2 = Network(name = 'YY', description = 'network2_description')

            # Add stations to the XX network.
            station1 = Station(name = 'station1_name',
                               location = '00',
                               x = 11,
                               y = 12,
                               z = 13,
                               coord_system = 'station1_coord_system')

            station2 = Station(name = 'station2_name',
                               location = '00',
                               x = 21,
                               y = 22,
                               z = 23,
                               coord_system = 'station2_coord_system')

            channel1 = Channel(name = 'channel1_name',
                               description = 'channel1_description')
            channel2 = Channel(name = 'channel2_name',
                               description = 'channel2_description')
            channel3 = Channel(name = 'channel3_name',
                               description = 'channel3_description')

            station1.add_channel(channel1)
            station1.add_channel(channel2)
            station2.add_channel(channel3)

            network1.add_station(station1)
            network2.add_station(station2)

            db_inventory.add_network(network1)
            db_inventory.add_network(network2)

            # Commit the changes to the database.
            db_inventory.commit()
        finally:
            db_inventory.close()

        # Load the networks from the database.
        try:
            db_inventory_load = DbInventory(self.project)
            db_inventory_load.load_networks()
        finally:
            db_inventory_load.close()

        self.assertEqual(len(db_inventory_load.networks), 2)

        self.assertEqual(db_inventory_load.networks[0].name, 'XX')
        self.assertEqual(db_inventory_load.networks[0].description, 'network1_description')
        self.assertEqual(db_inventory_load.networks[0].parent_inventory, db_inventory_load)

        self.assertEqual(db_inventory_load.networks[1].name, 'YY')
        self.assertEqual(db_inventory_load.networks[1].description, 'network2_description')
        self.assertEqual(db_inventory_load.networks[1].parent_inventory, db_inventory_load)

        cur_network = db_inventory_load.networks[0]
        self.assertEqual(len(cur_network.stations), 1)
        self.assertEqual(len(cur_network.orm.stations), 1)
        cur_station = cur_network.stations[0]
        self.assertEqual(cur_station.name, 'station1_name')
        self.assertEqual(cur_station.network, 'XX')
        self.assertEqual(cur_station.parent_network, cur_network)
        self.assertEqual(len(cur_station.channels), 2)
        self.assertEqual(len(cur_station.orm.channels), 2)
        cur_channel = cur_station.channels[0]
        self.assertEqual(cur_channel.name, 'channel1_name')
        cur_channel = cur_station.channels[1]
        self.assertEqual(cur_channel.name, 'channel2_name')

        cur_network = db_inventory_load.networks[1]
        self.assertEqual(len(cur_network.stations), 1)
        self.assertEqual(len(cur_network.orm.stations), 1)
        cur_station = cur_network.stations[0]
        self.assertEqual(cur_station.name, 'station2_name')
        self.assertEqual(cur_station.network, 'YY')
        self.assertEqual(cur_station.parent_network, cur_network)
        self.assertEqual(len(cur_station.channels), 1)
        self.assertEqual(len(cur_station.orm.channels), 1)
        cur_channel = cur_station.channels[0]
        self.assertEqual(cur_channel.name, 'channel3_name')



    def test_load_network_with_streams(self):
        db_inventory = DbInventory(self.project)

        try:
            # Add networks to the db_inventory.
            network1 = Network(name = 'XX', description = 'network1_description')

            network2 = Network(name = 'YY', description = 'network2_description')

            # Create a recorder and a stream.
            recorder1 = Recorder(serial = 'recorder1_serial',
                                 model = 'recorder1_model',
                                 producer = 'recorder1_producer')

            stream1 = RecorderStream(name = 'stream1_name',
                                     label = 'stream1_label')

            recorder1.add_stream(stream1)

            # Add stations to the XX network.
            station1 = Station(name = 'station1_name',
                               location = '00',
                               x = 11,
                               y = 12,
                               z = 13,
                               coord_system = 'station1_coord_system')

            station2 = Station(name = 'station2_name',
                               location = '00',
                               x = 21,
                               y = 22,
                               z = 23,
                               coord_system = 'station2_coord_system')

            channel1 = Channel(name = 'channel1_name',
                               description = 'channel1_description')
            channel2 = Channel(name = 'channel2_name',
                               description = 'channel2_description')
            channel3 = Channel(name = 'channel3_name',
                               description = 'channel3_description')

            station1.add_channel(channel1)
            station1.add_channel(channel2)
            station2.add_channel(channel3)

            network1.add_station(station1)
            network2.add_station(station2)

            # Add the elements to the inventory.
            db_inventory.add_network(network1)
            db_inventory.add_network(network2)
            db_inventory.add_recorder(recorder1)

            # Add the stream to a channel.
            cur_start_time = UTCDateTime('2014-01-01')
            cur_end_time = UTCDateTime('2014-02-01')
            cur_channel = db_inventory.get_channel(name = 'channel1_name')
            cur_channel = cur_channel[0]
            cur_channel.add_stream(serial = 'recorder1_serial',
                                   model = 'recorder1_model',
                                   producer = 'recorder1_producer',
                                   name = 'stream1_name',
                                   start_time = cur_start_time,
                                   end_time = cur_end_time)

            # Commit the changes to the database.
            db_inventory.commit()
        finally:
            db_inventory.close()


        # Load the networks from the database.
        try:
            db_inventory_load = DbInventory(self.project)
            db_inventory_load.load_recorders()
            db_inventory_load.load_networks()
        finally:
            db_inventory_load.close()


        self.assertEqual(len(db_inventory_load.networks), 2)
        self.assertEqual(db_inventory_load.networks[0].name, 'XX')
        self.assertEqual(db_inventory_load.networks[1].name, 'YY')

        cur_channel = db_inventory_load.get_channel(name = 'channel1_name')
        self.assertEqual(len(cur_channel), 1)
        cur_channel = cur_channel[0]
        self.assertEqual(len(cur_channel.streams), 1)


    def test_change_network(self):
        db_inventory = DbInventory(self.project)

        # Add a network to the db_inventory.
        net_2_add = Network(name = 'XX', description = 'A test network.')
        added_network = db_inventory.add_network(net_2_add)

        added_network.name = 'YY'
        added_network.description = 'changed description'
        added_network.type = 'changed type'

        self.assertEqual(added_network.name, 'YY')
        self.assertEqual(added_network.orm.name, 'YY')
        self.assertEqual(added_network.description, 'changed description')
        self.assertEqual(added_network.orm.description, 'changed description')
        self.assertEqual(added_network.type, 'changed type')
        self.assertEqual(added_network.orm.type, 'changed type')

        db_inventory.close()


    def test_change_station(self):
        db_inventory = DbInventory(self.project)

        # Add a network to the db_inventory.
        net_2_add = Network(name = 'XX', description = 'A test network.')
        added_network = db_inventory.add_network(net_2_add)

        # Add a station to the XX network.
        stat_2_add = Station(name = 'AAA',
                             location = '00',
                             x = 0,
                             y = 0,
                             z = 0,
                             coord_system = 'epsg:4316')
        added_station = added_network.add_station(stat_2_add)

        cur_station = added_station
        test_attr = [('name', 'BBB'), 
                     ('location', '01'), ('x', 999), ('y', 999), ('z', 999),
                     ('coord_system', 'epsg:0000')]
        for cur_attr, cur_value in test_attr:
            setattr(cur_station, cur_attr, cur_value)
            self.assertEqual(getattr(cur_station, cur_attr), cur_value)
            self.assertEqual(getattr(cur_station.orm, cur_attr), cur_value)


        db_inventory.close()


    def test_change_recorder(self):
        db_inventory = DbInventory(self.project)

        rec_2_add = Recorder(serial = 'AAAA',
                             model = 'recorder1_model',
                             producer = 'recorder1_producer',
                             description = 'test description')
        added_recorder = db_inventory.add_recorder(rec_2_add)

        added_recorder.serial = 'BBBB'
        added_recorder.model = 'changed model'
        added_recorder.producer = 'changed producer'
        added_recorder.description = 'changed description'

        self.assertEqual(added_recorder.serial, 'BBBB')
        self.assertEqual(added_recorder.orm.serial, 'BBBB')
        self.assertEqual(added_recorder.description, 'changed description')
        self.assertEqual(added_recorder.orm.description, 'changed description')
        self.assertEqual(added_recorder.model, 'changed model')
        self.assertEqual(added_recorder.orm.model, 'changed model')
        self.assertEqual(added_recorder.producer, 'changed producer')
        self.assertEqual(added_recorder.orm.producer, 'changed producer')

        db_inventory.close()


    def test_xml_to_db_inventory(self):
        xml_file = os.path.join(self.data_path, 'simple_inventory.xml')
        xml_parser = InventoryXmlParser()
        inventory = xml_parser.parse(xml_file)

        db_inventory = DbInventory.from_inventory_instance(name = 'test',
                                                           project = self.project,
                                                           inventory = inventory)

        self.assertEqual(len(db_inventory.sensors), len(inventory.sensors))
        self.assertEqual(len(db_inventory.recorders), len(inventory.recorders))
        self.assertEqual(len(db_inventory.networks), len(inventory.networks))

        # Test the sensor.
        self.assertEqual(len(db_inventory.sensors), 1)
        cur_sensor = db_inventory.sensors[0]
        self.assertEqual(cur_sensor.serial, '1417')
        self.assertEqual(cur_sensor.model, 'Seismonitor 1Hz')
        self.assertEqual(cur_sensor.producer, 'Geospace')
        self.assertEqual(cur_sensor.description, 'Sensor description.')

        # Test the sensor components.
        self.assertEqual(len(cur_sensor.components), 3)
        cur_component = cur_sensor.get_component(name = 'Z')
        self.assertEqual(len(cur_component), 1)
        cur_component = cur_component[0]
        self.assertEqual(cur_component.name, 'Z')
        self.assertEqual(cur_component.description, 'Sensor component Z description.')
        self.assertEqual(len(cur_component.parameters), 1)
        cur_parameter = cur_component.parameters[0]
        self.assertEqual(cur_parameter.start_time, UTCDateTime('2009-01-01T00:00:00.000000Z'))
        self.assertEqual(cur_parameter.end_time, UTCDateTime('2009-02-01T00:00:00.000000Z'))
        self.assertEqual(cur_parameter.sensitivity, 340.55)
        self.assertEqual(cur_parameter.tf_normalization_factor, 0.4)
        self.assertEqual(cur_parameter.tf_normalization_frequency, 1.0)
        self.assertEqual(len(cur_parameter.tf_poles), 3)
        self.assertTrue(complex('-4.44+4.44j') in cur_parameter.tf_poles)
        self.assertTrue(complex('-4.44-4.44j') in cur_parameter.tf_poles)
        self.assertTrue(complex('-1.083+0j') in cur_parameter.tf_poles)
        self.assertEqual(len(cur_parameter.tf_zeros), 3)
        self.assertEqual(cur_parameter.tf_zeros, [complex(0), complex(0), complex(0)])


        cur_component = cur_sensor.get_component(name = 'N')
        self.assertEqual(len(cur_component), 1)
        cur_component = cur_component[0]
        self.assertEqual(cur_component.name, 'N')
        self.assertEqual(cur_component.description, 'Sensor component N description.')
        self.assertEqual(len(cur_component.parameters), 1)
        cur_parameter = cur_component.parameters[0]
        self.assertEqual(cur_parameter.start_time, UTCDateTime('2009-01-01T00:00:00.000000Z'))
        self.assertEqual(cur_parameter.end_time, UTCDateTime('2009-03-01T00:00:00.000000Z'))
        self.assertEqual(cur_parameter.sensitivity, 340.55)
        self.assertEqual(cur_parameter.tf_normalization_factor, 0.4)
        self.assertEqual(cur_parameter.tf_normalization_frequency, 2.0)
        self.assertEqual(len(cur_parameter.tf_poles), 3)
        self.assertTrue(complex('-4.44+4.44j') in cur_parameter.tf_poles)
        self.assertTrue(complex('-4.44-4.44j') in cur_parameter.tf_poles)
        self.assertTrue(complex('-1.083+0j') in cur_parameter.tf_poles)
        self.assertEqual(len(cur_parameter.tf_zeros), 3)
        self.assertEqual(cur_parameter.tf_zeros, [complex(0), complex(0), complex(0)])

        cur_component = cur_sensor.get_component(name = 'E')
        self.assertEqual(len(cur_component), 1)
        cur_component = cur_component[0]
        self.assertEqual(cur_component.name, 'E')
        self.assertEqual(cur_component.description, 'Sensor component E description.')
        self.assertEqual(len(cur_component.parameters), 1)
        cur_parameter = cur_component.parameters[0]
        self.assertEqual(cur_parameter.start_time, UTCDateTime('2009-01-01T00:00:00.000000Z'))
        self.assertIsNone(cur_parameter.end_time)
        self.assertEqual(cur_parameter.sensitivity, 340.55)
        self.assertEqual(cur_parameter.tf_normalization_factor, 0.4)
        self.assertEqual(cur_parameter.tf_normalization_frequency, 3.0)
        self.assertEqual(len(cur_parameter.tf_poles), 3)
        self.assertTrue(complex('-4.44+4.44j') in cur_parameter.tf_poles)
        self.assertTrue(complex('-4.44-4.44j') in cur_parameter.tf_poles)
        self.assertTrue(complex('-1.083+0j') in cur_parameter.tf_poles)
        self.assertEqual(len(cur_parameter.tf_zeros), 3)
        self.assertEqual(cur_parameter.tf_zeros, [complex(0), complex(0), complex(0)])



        # Test the recorders.
        self.assertEqual(len(db_inventory.recorders), 1)
        cur_recorder = db_inventory.recorders[0]
        self.assertEqual(cur_recorder.serial, '9D6C')
        self.assertEqual(cur_recorder.model, '130-01')
        self.assertEqual(cur_recorder.producer, 'Reftek')
        self.assertEqual(cur_recorder.description, 'Recorder description.')
        self.assertEqual(len(cur_recorder.streams), 3)

        # Test the first stream.
        cur_stream = cur_recorder.streams[0]
        self.assertEqual(cur_stream.name, '101')
        self.assertEqual(cur_stream.label, 'Stream-101')
        self.assertEqual(len(cur_stream.parameters), 1)
        self.assertEqual(len(cur_stream.components), 1)

        cur_param = cur_stream.parameters[0]
        self.assertEqual(cur_param.start_time, UTCDateTime('2009-01-01T00:00:00.000000Z'))
        self.assertEqual(cur_param.end_time, UTCDateTime('2009-02-01T00:00:00.000000Z'))
        self.assertEqual(cur_param.gain, 32.)
        self.assertEqual(cur_param.bitweight, 1.5895e-6)

        cur_timebox = cur_stream.components[0]
        self.assertIsInstance(cur_timebox, TimeBox)
        self.assertEqual(cur_timebox.start_time, UTCDateTime('2009-01-01T00:00:00.000000Z'))
        self.assertEqual(cur_timebox.end_time, UTCDateTime('2009-02-01T00:00:00.000000Z'))
        cur_component = cur_timebox.item
        self.assertEqual(cur_component.serial, '1417')
        self.assertEqual(cur_component.name, 'Z')

        # Test the second stream.
        cur_stream = cur_recorder.streams[1]
        self.assertEqual(cur_stream.name, '102')
        self.assertEqual(cur_stream.label, 'Stream-102')
        self.assertEqual(len(cur_stream.parameters), 1)
        self.assertEqual(len(cur_stream.components), 1)

        cur_param = cur_stream.parameters[0]
        self.assertEqual(cur_param.start_time, UTCDateTime('2009-01-01T00:00:00.000000Z'))
        self.assertIsNone(cur_param.end_time)
        self.assertEqual(cur_param.gain, 32.)
        self.assertEqual(cur_param.bitweight, 1.5895e-6)

        cur_timebox = cur_stream.components[0]
        self.assertIsInstance(cur_timebox, TimeBox)
        self.assertEqual(cur_timebox.start_time, UTCDateTime('2009-01-01T00:00:00.000000Z'))
        self.assertIsNone(cur_timebox.end_time)
        cur_component = cur_timebox.item
        self.assertEqual(cur_component.serial, '1417')
        self.assertEqual(cur_component.name, 'N')

        # Test the third stream.
        cur_stream = cur_recorder.streams[2]
        self.assertEqual(cur_stream.name, '103')
        self.assertEqual(cur_stream.label, 'Stream-103')
        self.assertEqual(len(cur_stream.parameters), 1)
        self.assertEqual(len(cur_stream.components), 1)

        cur_param = cur_stream.parameters[0]
        self.assertEqual(cur_param.start_time, UTCDateTime('2009-01-01T00:00:00.000000Z'))
        self.assertIsNone(cur_param.end_time)
        self.assertEqual(cur_param.gain, 32.)
        self.assertEqual(cur_param.bitweight, 1.5895e-6)

        cur_timebox = cur_stream.components[0]
        self.assertIsInstance(cur_timebox, TimeBox)
        self.assertEqual(cur_timebox.start_time, UTCDateTime('2009-01-01T00:00:00.000000Z'))
        self.assertIsNone(cur_timebox.end_time)
        cur_component = cur_timebox.item
        self.assertEqual(cur_component.serial, '1417')
        self.assertEqual(cur_component.name, 'E')


        # Test the network.
        self.assertEqual(len(db_inventory.networks), 1)
        cur_network = db_inventory.networks[0]
        self.assertEqual(cur_network.name, 'XX')
        self.assertEqual(cur_network.type, 'network type')
        self.assertEqual(cur_network.description, 'Network description.')
        self.assertEqual(len(cur_network.stations), 1)

        # Test the station.
        cur_station = cur_network.stations[0]
        self.assertEqual(cur_station.name, 'GILA')
        self.assertEqual(cur_station.location, '00')
        self.assertEqual(cur_station.x, 15.887788)
        self.assertEqual(cur_station.y, 47.69577)
        self.assertEqual(cur_station.z, 643.0)
        self.assertEqual(cur_station.coord_system, 'epsg:4326')
        self.assertEqual(cur_station.description, 'Grillenberg')
        self.assertEqual(len(cur_station.channels), 3)

        # Test the first channel.
        cur_channel = cur_station.channels[0]
        self.assertEqual(cur_channel.name, 'HHZ')
        self.assertEqual(cur_channel.description, 'Description for channel HHZ.')
        self.assertEqual(len(cur_channel.streams), 1)
        cur_timebox = cur_channel.streams[0]
        self.assertIsInstance(cur_timebox, TimeBox)
        self.assertEqual(cur_timebox.start_time, UTCDateTime('2010-02-04T00:00:00.000000Z'))
        self.assertIsNone(cur_timebox.end_time)
        cur_stream = cur_timebox.item
        self.assertEqual(cur_stream.serial, '9D6C')
        self.assertEqual(cur_stream.name, '101')
        self.assertEqual(cur_stream.label, 'Stream-101')

        # Test the second channel.
        cur_channel = cur_station.channels[1]
        self.assertEqual(cur_channel.name, 'HHN')
        self.assertEqual(cur_channel.description, 'Description for channel HHN.')
        self.assertEqual(len(cur_channel.streams), 1)
        cur_timebox = cur_channel.streams[0]
        self.assertIsInstance(cur_timebox, TimeBox)
        self.assertEqual(cur_timebox.start_time, UTCDateTime('2010-02-04T00:00:00.000000Z'))
        self.assertIsNone(cur_timebox.end_time)
        cur_stream = cur_timebox.item
        self.assertEqual(cur_stream.serial, '9D6C')
        self.assertEqual(cur_stream.name, '102')
        self.assertEqual(cur_stream.label, 'Stream-102')


        # Test the third channel.
        cur_channel = cur_station.channels[2]
        self.assertEqual(cur_channel.name, 'HHE')
        self.assertEqual(cur_channel.description, 'Description for channel HHE.')
        self.assertEqual(len(cur_channel.streams), 1)
        cur_timebox = cur_channel.streams[0]
        self.assertIsInstance(cur_timebox, TimeBox)
        self.assertEqual(cur_timebox.start_time, UTCDateTime('2010-02-04T00:00:00.000000Z'))
        self.assertIsNone(cur_timebox.end_time)
        cur_stream = cur_timebox.item
        self.assertEqual(cur_stream.serial, '9D6C')
        self.assertEqual(cur_stream.name, '103')
        self.assertEqual(cur_stream.label, 'Stream-103')



def suite():
    #tests = ['test_load_recorder']
    #return unittest.TestSuite(map(DbInventoryTestCase, tests))
    return unittest.makeSuite(DbInventoryTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

