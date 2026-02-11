"""
Preference access operator for CarmaKit.
"""

from typing import Set

import bpy
from bpy.types import Context, Operator


class CARMAKIT_OT_open_preferences(Operator):
    """
    Operator to open the CarmaKit addon preferences.
    """

    bl_idname = "carmakit.open_preferences"
    bl_label = "Open CarmaKit Preferences"
    bl_description = "Open the CarmaKit addon preferences panel"

    def execute(self, context: Context) -> Set[str]:
        """
        Execute the operator to open preferences.

        """
        # Open preferences window.
        bpy.ops.screen.userpref_show('INVOKE_DEFAULT')

        # Switch to Add-ons section and search for CarmaKit.
        context.preferences.active_section = 'ADDONS'

        # Set the search filter to find our addon.
        bpy.context.window_manager.addon_search = "CarmaKit"

        return {'FINISHED'}
