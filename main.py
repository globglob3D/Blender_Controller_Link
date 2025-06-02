import bpy
import sdl2

def get_reader():
    return bpy.data.objects.get("BCL_reader")

def create_reader():
    bcl_reader = get_reader()
    if bcl_reader is None:
        bcl_reader = bpy.data.objects.new("BCL_reader", None)
        bcl_reader.use_fake_user = True
    return bcl_reader

def keyframe_inputs(scene):
    reader = get_reader()
    if not reader:
        return

    frame = scene.frame_current
    for prop_name, prop_value in reader.items():
        if prop_name.startswith("controller_"):
            try:
                reader.keyframe_insert(data_path='["{}"]'.format(prop_name), frame=frame)
            except Exception as e:
                print(f"Failed to keyframe {prop_name}: {e}") 

class SDL2_Controller_Handler:
    def __init__(self):
        self.controller = None
        self.joystick = None
        self.controller_name = ""
        self.is_gamecontroller = False

        sdl2.SDL_Init(sdl2.SDL_INIT_GAMECONTROLLER | sdl2.SDL_INIT_JOYSTICK)

        for i in range(sdl2.SDL_NumJoysticks()):
            if sdl2.SDL_IsGameController(i):
                self.controller = sdl2.SDL_GameControllerOpen(i)
                if self.controller:
                    name_ptr = sdl2.SDL_GameControllerName(self.controller)
                    self.controller_name = name_ptr.decode("utf-8") if name_ptr else "Unknown"
                    self.is_gamecontroller = True
                break

        if not self.controller:
            # Fallback to raw joystick if no recognized gamecontroller found
            if sdl2.SDL_NumJoysticks() > 0:
                self.joystick = sdl2.SDL_JoystickOpen(0)
                if self.joystick:
                    name_ptr = sdl2.SDL_JoystickName(self.joystick)
                    self.controller_name = name_ptr.decode("utf-8") if name_ptr else "Unknown"
                else:
                    print("No joystick found.")
            else:
                print("No game controller or joystick found.")

    def poll(self):
        sdl2.SDL_PumpEvents()
        bcl_reader = get_reader()
        if not bcl_reader:
            return

        if self.is_gamecontroller and self.controller:
            # Poll GameController axes and buttons (standardized)
            for axis in range(sdl2.SDL_CONTROLLER_AXIS_MAX):
                if sdl2.SDL_GameControllerHasAxis(self.controller, axis):
                    name = sdl2.SDL_GameControllerGetStringForAxis(axis).decode("utf-8")
                    prop_id = f"controller_axis_{name}"
                    raw = sdl2.SDL_GameControllerGetAxis(self.controller, axis)
                    value = max(-1.0, min(1.0, raw / 32767.0))
                    bcl_reader[prop_id] = value

            for button in range(sdl2.SDL_CONTROLLER_BUTTON_MAX):
                if sdl2.SDL_GameControllerHasButton(self.controller, button):
                    name = sdl2.SDL_GameControllerGetStringForButton(button).decode("utf-8")
                    prop_id = f"controller_button_{name}"
                    pressed = bool(sdl2.SDL_GameControllerGetButton(self.controller, button))
                    bcl_reader[prop_id] = pressed

        elif self.joystick:
            # Poll raw joystick axes and buttons (fallback)
            num_axes = sdl2.SDL_JoystickNumAxes(self.joystick)
            for axis in range(num_axes):
                raw = sdl2.SDL_JoystickGetAxis(self.joystick, axis)
                value = max(-1.0, min(1.0, raw / 32767.0))
                prop_id = f"controller_axis_{axis}"
                bcl_reader[prop_id] = value

            num_buttons = sdl2.SDL_JoystickNumButtons(self.joystick)
            for button in range(num_buttons):
                pressed = bool(sdl2.SDL_JoystickGetButton(self.joystick, button))
                prop_id = f"controller_button_{button}"
                bcl_reader[prop_id] = pressed

        else:
            # No controller or joystick
            return

        # Trigger update on the empty to force driver updates
        bcl_reader.location = bcl_reader.location

class BCL_OT_LiveControllerInputs(bpy.types.Operator):
    """Get Controller Inputs (Live, ie without animation playback)"""
    bl_idname = "bcl.live_controller_inputs"
    bl_label = "Get Controller Inputs"

    _timer = None

    def modal(self, context, event):
        if event.type == 'TIMER':
            BCL_OT_LiveControllerInputs.sdl2_controller_handler.poll()
        if not context.scene.bcl_live_modal_running or event.type in {'ESC'}:
            self.cancel(context)
            return {'CANCELLED'}
        return {'PASS_THROUGH'}

    def execute(self, context):
        
        create_reader()

        if context.scene.bcl_record_modal_running:
            context.scene.bcl_record_modal_running = False

        if context.scene.bcl_live_modal_running:
            context.scene.bcl_live_modal_running = False
            return {'CANCELLED'}

        BCL_OT_LiveControllerInputs.sdl2_controller_handler = SDL2_Controller_Handler()

        wm = context.window_manager
        self._timer = wm.event_timer_add(time_step=1/60, window=context.window)
        wm.modal_handler_add(self)

        # Set flag
        context.scene.bcl_live_modal_running = True

        bpy.ops.bcl.create_nodegroup()

        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        if self._timer:
            wm.event_timer_remove(self._timer)

        context.scene.bcl_live_modal_running = False

        self.report({'INFO'}, "Stopped live inputs.")

class BCL_OT_RecordControllerInputs(bpy.types.Operator):
    """Get Controller Inputs (Record, ie with animation playback and keyframing)"""
    bl_idname = "bcl.record_controller_inputs"
    bl_label = "Record Controller Inputs"

    _timer = None

    def modal(self, context, event):
        if event.type == 'TIMER':
            BCL_OT_LiveControllerInputs.sdl2_controller_handler.poll()
        if not context.scene.bcl_record_modal_running or event.type in {'ESC'}:
            self.cancel(context)
            return {'CANCELLED'}
        return {'PASS_THROUGH'}

    def execute(self, context):

        create_reader()

        if context.scene.bcl_live_modal_running:
            context.scene.bcl_live_modal_running = False
    
        if context.scene.bcl_record_modal_running:
            context.scene.bcl_record_modal_running = False
            return {'CANCELLED'}
        
        BCL_OT_RecordControllerInputs.sdl2_controller_handler = SDL2_Controller_Handler()

        if keyframe_inputs not in bpy.app.handlers.frame_change_pre:
            bpy.app.handlers.frame_change_pre.append(keyframe_inputs)

        wm = context.window_manager
        self._timer = wm.event_timer_add(time_step=1/60, window=context.window)
        wm.modal_handler_add(self)

        # Play timeline
        bpy.ops.screen.animation_play()

        # Set flag
        context.scene.bcl_record_modal_running = True

        bpy.ops.bcl.create_nodegroup()

        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        if self._timer:
            wm.event_timer_remove(self._timer)

        # Stop timeline if it is playing
        if bpy.context.screen.is_animation_playing:
            bpy.ops.screen.animation_play()

        # Remove handler
        if keyframe_inputs in bpy.app.handlers.frame_change_pre:
            bpy.app.handlers.frame_change_pre.remove(keyframe_inputs)

        context.scene.bcl_record_modal_running = False

        self.report({'INFO'}, "Stopped recording inputs.")


class BCL_OT_CreateNodegroup(bpy.types.Operator):
    """Create a Node Group for Controller Inputs"""
    bl_idname = "bcl.create_nodegroup"
    bl_label = "Create Controller Nodegroup"

    def execute(self, context):
        reader = get_reader()
        group_name = "BCL_ControllerInputs"
        nodegroup = bpy.data.node_groups.get(group_name)

        # Collect desired outputs
        desired_outputs = {
            prop_name for prop_name, value in reader.items()
            if prop_name.startswith("controller_") and isinstance(value, (float, int, bool))
        }

        # Rebuild nodegroup if output list is out of sync
        if nodegroup:
            current_outputs = {
                socket.name for socket in nodegroup.interface.items_tree
                if socket.in_out == 'OUTPUT'
            }
            if current_outputs != desired_outputs:
                bpy.data.node_groups.remove(nodegroup)
                nodegroup = None

        if nodegroup is None:
            nodegroup = bpy.data.node_groups.new(group_name, 'GeometryNodeTree')

        # Find or create group output node
        output_node = next((n for n in nodegroup.nodes if n.type == 'GROUP_OUTPUT'), None)
        if not output_node:
            output_node = nodegroup.nodes.new('NodeGroupOutput')
            output_node.location = (0, 0)

        for prop_name in desired_outputs:
            # Create output interface socket if needed
            if not nodegroup.interface.items_tree.get(prop_name):
                nodegroup.interface.new_socket(prop_name, in_out="OUTPUT", socket_type="NodeSocketFloat")

            # Connect socket to output node
            if prop_name not in output_node.inputs:
                continue  # Something's wrong, skip

            output_socket = output_node.inputs[prop_name]

            # Set up or reuse driver
            try:
                fcurve = output_socket.driver_add('default_value')
            except RuntimeError:
                fcurve = output_socket.animation_data and next(
                    (fc for fc in output_socket.animation_data.drivers if fc.data_path == 'default_value'),
                    None
                )

            if not fcurve:
                continue

            fcurve.driver.type = 'SCRIPTED'
            driver = fcurve.driver

            # Avoid adding duplicate variables
            existing_var = next((v for v in driver.variables if v.name == 'var'), None)
            if not existing_var:
                var = driver.variables.new()
                var.name = 'var'
                var.type = 'SINGLE_PROP'
                var.targets[0].id_type = 'OBJECT'
                var.targets[0].id = reader
                var.targets[0].data_path = f'["{prop_name}"]'
            else:
                var = existing_var
                # Make sure the target is correct
                tgt = var.targets[0]
                tgt.id_type = 'OBJECT'
                tgt.id = reader
                tgt.data_path = f'["{prop_name}"]'

            driver.expression = 'var'

        self.report({'INFO'}, f"Node group '{group_name}' ready with controller outputs.")
        return {'FINISHED'}

