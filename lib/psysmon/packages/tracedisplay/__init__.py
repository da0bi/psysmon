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

name = "tracedisplay"
version = "0.0.1"
author = "Stefan Mertl"
minPsysmonVersion = "0.0.1"
description = "The tracedisplay package."
website = "http://www.stefanmertl.com"

# Specify the module(s) where to search for plugin classes.
plugin_modules = ['plugins_componentselectors',
                  'plugins_processingstack',
                  'plugins_sonification',
                  'plugins_views',
                  'plugins_zoom',
                  'plugins_measure',
                  'plugins_export',
                  'plugins_publish']

# Specify the module(s) where to search for collection node classes.
collection_node_modules = ['tracedisplay', ]

# Specify the module(s) where to search for processing node classes.
processing_node_modules = ['processingNodes', ]

