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

name = "localize"                                 # The package name.
version = "0.0.1"                               # The package version.
author = "Stefan Mertl"                         # The package author.
minPsysmonVersion = "0.0.1"                     # The minimum pSysmon version required.
description = "The events core package"            # The package description.
website = "http://www.stefanmertl.com"          # The package website.

# Specify the module(s) where to search for collection node classes.
collection_node_modules = ['graphic_localization',]

# Specify the module(s) where to search for plugin classes.
plugin_modules = ['plugins_graphic_localize',
                  'plugins_event_selector',
                  'plugins_localize_circle',
                  'plugins_localize_tdoa',
                  'plugins_view_map',
                  'plugins_export_result',
                  'plugin_pick_selector']

# Specify the module(s) where to search for processing node classes.
processing_node_modules = []

