# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import bpy
from . import main
from . import ui

classes = (
    main.BCL_OT_ControllerInput,
    main.BCL_OT_Record,
    ui.BCL_PT_Main,
)

def start_controller_poll():
    try:
        bpy.ops.bcl.controller_input()
    except RuntimeError as e:
        print("Could not start controller input:", e)
    return None  # Only run once

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.bcl_record_modal_running = bpy.props.BoolProperty(default=False)

    # Delay to ensure context is fully ready
    bpy.app.timers.register(start_controller_poll, first_interval=0.1)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
