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

''' JSON decoder and encoder.

:copyright:
    Stefan Mertl

:license:
    GNU General Public License, Version 3 
    http://www.gnu.org/licenses/gpl-3.0.html

'''

import json
from obspy.core import UTCDateTime


class ProjectFileEncoder(json.JSONEncoder):
    ''' A JSON encoder for the pSysmon project file.
    '''
    def __init__(self, **kwarg):
        json.JSONEncoder.__init__(self, **kwarg)
        self.indent = 4
        self.sort_keys = True

    def default(self, obj):
        ''' Convert pSysmon project objects to a dictionary.
        '''
        obj_class = obj.__class__.__name__
        base_class = [x.__name__ for x in obj.__class__.__bases__]
        #print 'Converting %s' % obj_class

        if obj_class == 'Project':
            d = self.convert_project(obj)
        elif obj_class == 'UTCDateTime':
            d = self.convert_utcdatetime(obj)
        elif obj_class == 'User':
            d = self.convert_user(obj)
        elif obj_class == 'Collection':
            d = self.convert_collection(obj)
        elif 'CollectionNode' in base_class:
            d = self.convert_collection_node(obj)
        elif obj_class == 'PreferencesManager':
            d = self.convert_preferencesmanager(obj)
        elif obj_class == 'CustomPrefItem':
            d = self.convert_custom_preferenceitem(obj)
        elif obj_class == 'type':
            d = {}
        elif 'PreferenceItem' in base_class:
            d = self.convert_preferenceitem(obj)
        elif 'WaveClient' in base_class:
            d = self.convert_waveclient(obj)
        elif 'ProcessingNode' in base_class:
            d = self.convert_processing_node(obj)
        else:
            d = {'ERROR': 'MISSING CONVERTER for obj_class %s with base_class %s' % (str(obj_class), str(base_class))}

        # Add the class and module information to the dictionary.
        tmp = {'__baseclass__': base_class,
               '__class__': obj.__class__.__name__,
               '__module__': obj.__module__}
        d.update(tmp)

        return d


    def convert_project(self, obj):
        attr = ['name', 'dbDriver', 'dbDialect', 'dbHost',
                'dbName', 'pkg_version', 'db_version', 'createTime',
                'defaultWaveclient', 'scnlDataSources', 'user', 'waveclient']
        d =  self.object_to_dict(obj, attr)
        #d['waveclient'] = [(x.name, x.mode, x.options) for x in obj.waveclient.itervalues()]
        return d


    def convert_utcdatetime(self, obj):
        return {'utcdatetime': obj.isoformat()}


    def convert_user(self, obj):
        attr = ['name', 'mode', 'author_name', 'author_uri', 
                'agency_name', 'agency_uri', 'collection']
        d = self.object_to_dict(obj, attr)
        if obj.activeCollection is None:
            d['activeCollection'] = obj.activeCollection
        else:
            d['activeCollection'] = obj.activeCollection.name

        return d


    def convert_collection(self, obj):
        attr = ['name', 'nodes']
        return self.object_to_dict(obj, attr)


    def convert_collection_node(self, obj):
        attr = ['enabled', 'requires', 'provides', 'pref_manager']
        d = self.object_to_dict(obj, attr)
        return d


    def convert_processing_node(self, obj):
        attr = ['pref_manager', 'enabled']
        d = self.object_to_dict(obj, attr)
        return d


    def convert_preferencesmanager(self, obj):
        attr = ['pages', ]
        d = self.object_to_dict(obj, attr)
        return d


    def convert_custom_preferenceitem(self, obj):
        import inspect

        attr = ['name', 'value', 'label', 'default',
                'group', 'limit']
        d = self.object_to_dict(obj, attr)

        # Find any additional arguments.
        base_arg = inspect.getargspec(obj.__class__.__bases__[0].__init__)
        arg = inspect.getargspec(obj.__init__)

        for cur_arg in arg.args:
            if cur_arg not in base_arg.args and cur_arg in attr:
                d[cur_arg] = getattr(obj, cur_arg)

        return d


    def convert_preferenceitem(self, obj):
        import inspect

        #attr = ['name', 'value', 'label', 'default', 
        #        'group', 'limit', 'guiclass', 'gui_element']
        attr = ['name', 'value', 'label', 'default',
                'group', 'limit']
        d = self.object_to_dict(obj, attr)

        # Find any additional arguments.
        base_arg = inspect.getargspec(obj.__class__.__bases__[0].__init__)
        arg = inspect.getargspec(obj.__init__)

        for cur_arg in arg.args:
            if cur_arg not in base_arg.args:
                d[cur_arg] = getattr(obj, cur_arg)

        return d


    def convert_waveclient(self, obj):
        ignore_attr = ['project', 'logger', 'stock', 'stock_lock', 'preload_threads', 'waveformDirList', 'client']
        attr = [x for x in obj.__dict__.keys() if x not in ignore_attr]
        d = self.object_to_dict(obj, attr)
        return d


    def object_to_dict(self, obj, attr):
        ''' Copy selceted attributes of object to a dictionary.
        '''
        def hint_tuples(item):
            if isinstance(item, tuple):
                return {'__tuple__': True, 'items': item}
            if isinstance(item, list):
                return [hint_tuples(e) for e in item]
            else:
                return item

        d = {}
        for cur_attr in attr:
            d[cur_attr] = hint_tuples(getattr(obj, cur_attr))

        return d



class ProjectFileDecoder(json.JSONDecoder):

    def __init__(self, **kwarg):
        json.JSONDecoder.__init__(self, object_hook = self.convert_object)

    def convert_object(self, d):
        #print "Converting dict: %s." % str(d)

        if '__class__' in d:
            class_name = d.pop('__class__')
            module_name = d.pop('__module__')
            base_class = d.pop('__baseclass__')

            if class_name == 'Project':
                inst = self.convert_project(d)
            elif class_name == 'User':
                inst = self.convert_user(d)
            elif class_name == 'UTCDateTime':
                inst = self.convert_utcdatetime(d)
            elif class_name == 'Collection':
                inst = self.convert_collection(d)
            elif class_name == 'PreferencesManager':
                inst = self.convert_pref_manager(d)
            elif class_name == 'CustomPrefItem':
                inst = self.convert_custom_preferenceitem(d, class_name, module_name)
            elif class_name == 'type':
                inst = self.convert_class_object(d, class_name, module_name)
            elif 'CollectionNode' in base_class:
                inst = self.convert_collectionnode(d, class_name, module_name)
            elif 'PreferenceItem' in base_class:
                inst = self.convert_preferenceitem(d, class_name, module_name)
            elif 'WaveClient' in base_class:
                inst = self.convert_waveclient(d, class_name, module_name)
            elif 'ProcessingNode' in base_class:
                inst = self.convert_processing_node(d, class_name, module_name)
            else:
                inst = {'ERROR': 'MISSING CONVERTER'}

        else:
            inst = d

        return inst


    def decode_hinted_tuple(self, item):
        if isinstance(item, dict):
            if '__tuple__' in item:
                return tuple(item['items'])
        elif isinstance(item, list):
                return [self.decode_hinted_tuple(x) for x in item]
        else:
            return item


    def convert_project(self, d):
        import psysmon.core.project
        inst = psysmon.core.project.Project(psybase = None,
                                            name = d['name'],
                                            user = d['user'],
                                            dbHost = d['dbHost'],
                                            dbName = d['dbName'],
                                            pkg_version = d['pkg_version'],
                                            db_version = d['db_version'],
                                            dbDriver = d['dbDriver'],
                                            dbDialect = d['dbDialect'],
                                            createTime = d['createTime']
                                            )

        inst.defaultWaveclient = d['defaultWaveclient']
        inst.scnlDataSources = d['scnlDataSources']
        inst.waveclient = d['waveclient']

        return inst


    def convert_user(self, d):
        import psysmon.core.project
        inst = psysmon.core.project.User(user_name = d['name'],
                                         user_pwd = None,
                                         user_mode = d['mode'],
                                         author_name = d['author_name'],
                                         author_uri = d['author_uri'],
                                         agency_name = d['agency_name'],
                                         agency_uri = d['agency_uri']
                                         )
        inst.collection = d['collection']

        if d['activeCollection'] in inst.collection.keys():
            inst.activeCollection = inst.collection[d['activeCollection']]
        return inst


    def convert_utcdatetime(self, d):
        inst = UTCDateTime(d['utcdatetime'])
        return inst


    def convert_pref_manager(self, d):
        import psysmon.core.preferences_manager
        inst = psysmon.core.preferences_manager.PreferencesManager(pages = d['pages'])
        return inst

    def convert_collection(self, d):
        import psysmon.core.preferences_manager
        inst = psysmon.core.base.Collection(name = d['name'], nodes = d['nodes'])

        return inst


    def convert_class_object(self, d, class_name, module_name):
        import importlib
        module = importlib.import_module(module_name)
        class_ = getattr(module, class_name)
        return class_


    def convert_collectionnode(self, d, class_name, module_name):
        import importlib
        pref_manager = d.pop('pref_manager')
        module = importlib.import_module(module_name)
        class_ = getattr(module, class_name)
        args = dict( (key.encode('ascii'), self.decode_hinted_tuple(value)) for key, value in d.items())
        inst = class_(**args)
        inst.update_pref_manager(pref_manager)
        return inst


    def convert_processing_node(self, d, class_name, module_name):
        import importlib
        pref_manager = d.pop('pref_manager')
        module = importlib.import_module(module_name)
        class_ = getattr(module, class_name)
        args = dict( (key.encode('ascii'), self.decode_hinted_tuple(value)) for key, value in d.items())
        inst = class_(**args)
        inst.update_pref_manager(pref_manager)
        return inst


    def convert_custom_preferenceitem(self, d, class_name, module_name):
        import importlib
        module = importlib.import_module(module_name)
        class_ = getattr(module, class_name)
        args = dict( (key.encode('ascii'), self.decode_hinted_tuple(value)) for key, value in d.items())
        inst = class_(**args)
        return inst


    def convert_preferenceitem(self, d, class_name, module_name):
        import importlib
        module = importlib.import_module(module_name)
        class_ = getattr(module, class_name)
        args = dict( (key.encode('ascii'), self.decode_hinted_tuple(value)) for key, value in d.items())
        inst = class_(**args)
        return inst


    def convert_waveclient(self, d, class_name, module_name):
        import importlib
        module = importlib.import_module(module_name)
        class_ = getattr(module, class_name)
        args = dict( (key.encode('ascii'), self.decode_hinted_tuple(value)) for key, value in d.items())
        inst = class_(**args)
        return inst


