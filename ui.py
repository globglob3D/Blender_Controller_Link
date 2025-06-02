import bpy
from . import main

class BCL_PT_Main(bpy.types.Panel):
    bl_label = "Controller Inputs"
    bl_idname = "BCL_PT_Main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BCL"

    def draw(self, context):
        layout = self.layout
        scene = context.scene


        # RECORD BUTTON
        row = layout.row()
        row.scale_y = 1.5
        if scene.bcl_record_modal_running:
            row.operator("bcl.record", text="Stop Recording", icon='PAUSE')
        else:
            row.operator("bcl.record", text="Start Recording", icon='REC')

        layout.separator()

        handler = getattr(main.BCL_OT_ControllerInput, "sdl2_controller_handler")

        if handler and handler.controller:
            layout.label(text=f"Controller: {handler.controller_name}")
        else:
            layout.label(text="No controller detected.")

        bcl_reader = main.get_reader()
        if not bcl_reader:
            layout.label(text="No reader object found.")
            return

        # Show all axis values
        layout.label(text="Axes:")
        axis_keys = sorted(k for k in bcl_reader.keys() if k.startswith("controller_axis_"))
        for prop_name in axis_keys:
            row = layout.row()
            row.prop(bcl_reader, f'["{prop_name}"]', text=prop_name.replace("controller_axis_", "").capitalize())

        layout.separator()

        # Show all button values
        layout.label(text="Buttons:")
        button_keys = sorted(k for k in bcl_reader.keys() if k.startswith("controller_button_"))
        for prop_name in button_keys:
            row = layout.row()
            row.prop(bcl_reader, f'["{prop_name}"]', text=prop_name.replace("controller_button_", "").capitalize())
