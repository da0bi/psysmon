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

name = "event"                                 # The package name.
version = "0.0.2"                               # The package version.
author = "Stefan Mertl"                         # The package author.
minPsysmonVersion = "0.0.1"                     # The minimum pSysmon version required.
description = "The events core package"            # The package description.
website = "http://www.stefanmertl.com"          # The package website.

# Specify the module(s) where to search for collection node classes.
collection_node_modules = ['import_bulletin',
                           'detect_sta_lta',
                           'edit_event_catalogs',
                           'lc_detect_sta_lta',
                           'edit_detection_catalogs',
                           'lc_detection_binder',
                           'lc_event_type_filter',
                           'cn_export_events',
                           'cn_export_event_picks']

# Specify the module(s) where to search for plugin classes.
plugin_modules = ['plugins_event_selector',
                  'plugins_event_create',
                  'plugins_event_change_limits',
                  'plugins_detect_sta_lta',
                  'plugins_detection_selector']

# Specify the module(s) where to search for processing node classes.
processing_node_modules = []

# The packages which this package requires.
depends_on = ['geometry']


'''
Database change history.
version 0.0.1 - 2018-03-15
Added the event_type database.
Added the foreign key relationship to the event database.

'''


def databaseFactory(base):
    from sqlalchemy import Column
    from sqlalchemy import Integer
    from sqlalchemy import String
    from sqlalchemy import Text
    from sqlalchemy import Float
    from sqlalchemy import ForeignKey
    from sqlalchemy import UniqueConstraint
    from sqlalchemy.orm import relationship
    from sqlalchemy.orm import backref

    tables = []


    ###########################################################################
    # EVENT_SET table mapper class
    class EventCatalogDb(base):
        __tablename__  = 'event_catalog'
        __table_args__ = (
                          UniqueConstraint('name'),
                          {'mysql_engine': 'InnoDB'}
                         )
        _version = '1.0.0'

        id = Column(Integer, primary_key = True, autoincrement = True)
        name = Column(String(191), nullable = False)
        description = Column(Text, nullable = True)
        agency_uri = Column(String(255), nullable = True)
        author_uri = Column(String(255), nullable = True)
        creation_time = Column(String(30), nullable = True)

        events = relationship('EventDb',
                               cascade = 'all',
                               backref = 'parent',
                               lazy = 'select')

        def __init__(self, name, description, agency_uri,
                     author_uri, creation_time):
            self.name = name
            self.description = description
            self.agency_uri = agency_uri
            self.author_uri = author_uri
            self.creation_time = creation_time

    tables.append(EventCatalogDb)


    ###########################################################################
    # EVENT_TYPE table mapper class
    class EventTypeDb(base):
        __tablename__  = 'event_type'
        __table_args__ = (
                          UniqueConstraint('name'),
                          {'mysql_engine': 'InnoDB'}
                         )
        _version = '1.0.0'

        id = Column(Integer, primary_key = True, autoincrement = True)
        parent_id = Column(Integer,
                           ForeignKey('event_type.id',
                                      onupdate = 'cascade',
                                      ondelete = 'cascade'),
                           nullable = True)
        name = Column(String(191), nullable = False)
        description = Column(Text, nullable = True)
        agency_uri = Column(String(255), nullable = True)
        author_uri = Column(String(255), nullable = True)
        creation_time = Column(String(30), nullable = True)

        children = relationship('EventTypeDb',
                                cascade = 'all',
                                backref = backref('parent', remote_side = [id]))


        def __init__(self, name, description, agency_uri,
                     author_uri, creation_time):
            self.name = name
            self.description = description
            self.agency_uri = agency_uri
            self.author_uri = author_uri
            self.creation_time = creation_time

    tables.append(EventTypeDb)



    ###########################################################################
    # EVENT table mapper class
    class EventDb(base):
        __tablename__  = 'event'
        __table_args__ = (
                          {'mysql_engine': 'InnoDB'}
                         )
        _version = '1.0.1'

        id = Column(Integer, primary_key = True, autoincrement = True)
        ev_catalog_id = Column(Integer,
                               ForeignKey('event_catalog.id',
                                          onupdate = 'cascade',
                                          ondelete = 'set null'),
                               nullable = True)
        start_time = Column(Float(53), nullable = False)
        end_time = Column(Float(53), nullable = False)
        public_id = Column(String(255), nullable = True)
        description = Column(Text, nullable = True)
        comment = Column(Text, nullable = True)
        tags = Column(String(255), nullable = True)
        ev_type_id = Column(Integer,
                            ForeignKey('event_type.id',
                                       onupdate = 'cascade',
                                       ondelete = 'set null'),
                            nullable = True)
        ev_type_certainty = Column(String(50), nullable = True)
        pref_origin_id = Column(Integer, nullable = True)
        pref_magnitude_id = Column(Integer, nullable = True)
        pref_focmec_id = Column(Integer, nullable = True)
        agency_uri = Column(String(255), nullable = True)
        author_uri = Column(String(255), nullable = True)
        creation_time = Column(String(30), nullable = True)

        detections = relationship('DetectionToEventDb')
        event_type = relationship('EventTypeDb')


        def __init__(self, ev_catalog_id, start_time, end_time,
                     agency_uri, author_uri, creation_time,
                     public_id = None, description = None, comment = None,
                     tags = None, ev_type_id = None, ev_type_certainty = None,
                     pref_origin_id = None, pref_magnitude_id = None, pref_focmec_id = None):
            self.ev_catalog_id = ev_catalog_id
            self.start_time = start_time
            self.end_time = end_time
            self.public_id = public_id
            self.description = description
            self.comment = comment
            self.tags = tags
            self.ev_type_id = ev_type_id
            self.ev_type_certainty = ev_type_certainty
            self.pref_origin_id = pref_origin_id
            self.pref_magnitude_id = pref_magnitude_id
            self.pref_focmec_id = pref_focmec_id
            self.agency_uri = agency_uri
            self.author_uri = author_uri
            self.creation_time = creation_time

    tables.append(EventDb)



    ###########################################################################
    # DETECTION_CATALOG table mapper class
    class DetectionCatalogDb(base):
        __tablename__  = 'detection_catalog'
        __table_args__ = (
                          UniqueConstraint('name'),
                          {'mysql_engine': 'InnoDB'}
                         )
        _version = '1.0.0'

        id = Column(Integer, primary_key = True, autoincrement = True)
        name = Column(String(191), nullable = False)
        description = Column(Text, nullable = True)
        agency_uri = Column(String(255), nullable = True)
        author_uri = Column(String(255), nullable = True)
        creation_time = Column(String(30), nullable = True)

        detections = relationship('DetectionDb',
                                  cascade = 'all',
                                  backref = 'parent',
                                  lazy = 'noload')

        def __init__(self, name, description, agency_uri,
                     author_uri, creation_time):
            self.name = name
            self.description = description
            self.agency_uri = agency_uri
            self.author_uri = author_uri
            self.creation_time = creation_time


    tables.append(DetectionCatalogDb)


    ###########################################################################
    # DETECTION table mapper class
    class DetectionDb(base):
        __tablename__  = 'detection'
        __table_args__ = {'mysql_engine': 'InnoDB'}
        _version = '1.0.0'

        id = Column(Integer, primary_key = True, autoincrement = True)
        catalog_id = Column(Integer,
                            ForeignKey('detection_catalog.id',
                                        onupdate = 'cascade',
                                        ondelete = 'set null'),
                            nullable = True)
        rec_stream_id = Column(Integer,
                               ForeignKey('geom_rec_stream.id',
                                      onupdate = 'cascade',
                                      ondelete = 'set null'),
                                      nullable = True)
        start_time = Column(Float(53), nullable = False)
        end_time = Column(Float(53), nullable = False)
        method = Column(String(255), nullable = True)
        agency_uri = Column(String(255), nullable = True)
        author_uri = Column(String(255), nullable = True)
        creation_time = Column(String(30), nullable = True)

        def __init__(self, catalog_id, rec_stream_id,
                     start_time, end_time, method,
                     agency_uri, author_uri, creation_time):
            self.catalog_id = catalog_id,
            self.rec_stream_id = rec_stream_id,
            self.start_time = start_time,
            self.end_time = end_time,
            self.method = method,
            self.agency_uri = agency_uri
            self.author_uri = author_uri
            self.creation_time = creation_time

    tables.append(DetectionDb)



    ###########################################################################
    # DETECTION_TO_EVENT table mapper class
    class DetectionToEventDb(base):
        ''' The traceheader database table mapper.

        History
        -------
        1.1.0 - 2018-03-29
        Cascade the deletes of events and detections.
        '''
        __tablename__  = 'detection_to_event'
        __table_args__ = (
                          {'mysql_engine': 'InnoDB'}
                         )
        _version = '1.1.0'

        ev_id = Column(Integer,
                       ForeignKey('event.id',
                                  onupdate = 'cascade',
                                  ondelete = 'cascade'),
                       primary_key = True,
                       nullable = False)
        det_id = Column(Integer,
                        ForeignKey('detection.id',
                                   onupdate = 'cascade',
                                   ondelete = 'cascade'),
                        primary_key = True,
                        nullable = False)
        
        detection = relationship('DetectionDb')

        def __init(self, ev_id, det_id):
            self.ev_id = ev_id
            self.det_id = det_id

    tables.append(DetectionToEventDb)

    return tables

