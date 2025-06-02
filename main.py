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


class SDL2_Controller_Handler:
    def __init__(self):
        self.controller = None
        self.controller_name = ""

        sdl2.SDL_Init(sdl2.SDL_INIT_GAMECONTROLLER)

        for i in range(sdl2.SDL_NumJoysticks()):
            if sdl2.SDL_IsGameController(i):
                self.controller = sdl2.SDL_GameControllerOpen(i)
                if self.controller:
                    name_ptr = sdl2.SDL_GameControllerName(self.controller)
                    self.controller_name = name_ptr.decode("utf-8") if name_ptr else "Unknown"
                break

        if not self.controller:
            print("No game controller found.")

    def poll(self):
        if not self.controller:
            return

        sdl2.SDL_PumpEvents()
        bcl_reader = get_reader()
        if not bcl_reader:
            return

        # Poll axes and set as float properties on the empty
        for axis in range(sdl2.SDL_CONTROLLER_AXIS_MAX):
            if sdl2.SDL_GameControllerHasAxis(self.controller, axis):
                name = sdl2.SDL_GameControllerGetStringForAxis(axis).decode("utf-8")
                prop_id = f"controller_axis_{name}"
                raw = sdl2.SDL_GameControllerGetAxis(self.controller, axis)
                value = max(-1.0, min(1.0, raw / 32767.0))
                bcl_reader[prop_id] = value

        # Poll buttons and set as bool properties on the empty
        for button in range(sdl2.SDL_CONTROLLER_BUTTON_MAX):
            if sdl2.SDL_GameControllerHasButton(self.controller, button):
                name = sdl2.SDL_GameControllerGetStringForButton(button).decode("utf-8")
                prop_id = f"controller_button_{name}"
                pressed = bool(sdl2.SDL_GameControllerGetButton(self.controller, button))
                bcl_reader[prop_id] = pressed

        # Trigger update on the empty to force driver updates
        bcl_reader.location = bcl_reader.location


class BCL_OT_ControllerInput(bpy.types.Operator):
    """Get Controller Inputs"""
    bl_idname = "bcl.controller_input"
    bl_label = "Get Controller Inputs"

    _timer = None

    def modal(self, context, event):
        if event.type == 'TIMER':
            if hasattr(BCL_OT_ControllerInput, "sdl2_controller_handler"):
                BCL_OT_ControllerInput.sdl2_controller_handler.poll()
        return {'PASS_THROUGH'}

    def execute(self, context):
        # Create or get the empty object
        create_reader()
        # Create the SDL2 controller handler once
        BCL_OT_ControllerInput.sdl2_controller_handler = SDL2_Controller_Handler()

        wm = context.window_manager
        self._timer = wm.event_timer_add(time_step=1/60, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        if self._timer:
            wm.event_timer_remove(self._timer)


def record_inputs(scene):
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

class BCL_OT_Record(bpy.types.Operator):
    """Start/Stop recording controller inputs as keyframes"""
    bl_idname = "bcl.record"
    bl_label = "Record Controller Inputs"

    _timer = None

    def modal(self, context, event):
        if not context.scene.bcl_record_modal_running or event.type in {'ESC'}:
            self.cancel(context)
            return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def execute(self, context):
        # Toggle: stop if already recording
        if context.scene.bcl_record_modal_running:
            context.scene.bcl_record_modal_running = False
            return {'CANCELLED'}

        # Ensure reader exists
        if "BCL_reader" not in bpy.data.objects:
            self.report({'ERROR'}, "No reader object named 'BCL_Reader' found.")
            return {'CANCELLED'}

        # Add frame change handler if not already present
        if record_inputs not in bpy.app.handlers.frame_change_pre:
            bpy.app.handlers.frame_change_pre.append(record_inputs)

        # Add modal + timer
        self._timer = context.window_manager.event_timer_add(0.01, window=context.window)
        context.window_manager.modal_handler_add(self)

        # Play timeline
        bpy.ops.screen.animation_play()

        # Set flag
        context.scene.bcl_record_modal_running = True

        return {'RUNNING_MODAL'}

    def cancel(self, context):
        # Remove timer
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)

        # Stop timeline if it is playing
        if bpy.context.screen.is_animation_playing:
            bpy.ops.screen.animation_play()  # This stops playback

        # Remove handler
        if record_inputs in bpy.app.handlers.frame_change_pre:
            bpy.app.handlers.frame_change_pre.remove(record_inputs)

        context.scene.bcl_record_modal_running = False
        self.report({'INFO'}, "Stopped recording inputs.")
