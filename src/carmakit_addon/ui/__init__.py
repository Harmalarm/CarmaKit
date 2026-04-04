"""
UI package exports for CarmaKit.
"""

from .main_panel import CARMAKIT_PT_main_panel
from .tools_panel import CARMAKIT_PT_tools_panel
from .tools_vertex_index import CARMAKIT_PT_tool_vertex_index
from .tools_groove_setup import (
    CARMAKIT_OT_add_groove_item,
    CARMAKIT_OT_remove_groove_item,
    CARMAKIT_PT_tool_groove_setup,
    CARMAKIT_UL_groove_list,
    register_handlers as _register_groove_handlers,
    register_properties as _register_groove_properties,
    unregister_handlers as _unregister_groove_handlers,
    unregister_properties as _unregister_groove_properties,
)
from .tools_track_preprocess import (
    CARMAKIT_PT_tool_track_preprocess,
    register_properties as _register_track_properties,
    unregister_properties as _unregister_track_properties,
)
from .tools_track_setup import CARMAKIT_PT_tool_track_setup
from .tools_car_setup import CARMAKIT_PT_tool_car_setup
from ..props.groove_props import GrooveItem
from .preferences_operator import CARMAKIT_OT_open_preferences

__all__ = [
    "CARMAKIT_PT_main_panel",
    "CARMAKIT_PT_tools_panel",
    "CARMAKIT_PT_tool_vertex_index",
    "CARMAKIT_PT_tool_groove_setup",
    "CARMAKIT_PT_tool_track_setup",
    "CARMAKIT_PT_tool_car_setup",
    "CARMAKIT_PT_tool_track_preprocess",
    "CARMAKIT_UL_groove_list",
    "CARMAKIT_OT_add_groove_item",
    "CARMAKIT_OT_remove_groove_item",
    "GrooveItem",
    "register_handlers",
    "register_properties",
    "unregister_handlers",
    "unregister_properties",
    "CARMAKIT_OT_open_preferences",
]


def register_handlers() -> None:
    """
    Register UI handlers.
    """
    _register_groove_handlers()


def unregister_handlers() -> None:
    """
    Unregister UI handlers.
    """
    _unregister_groove_handlers()


def register_properties() -> None:
    """
    Register UI properties.
    """
    _register_groove_properties()
    _register_track_properties()


def unregister_properties() -> None:
    """
    Unregister UI properties.
    """
    _unregister_track_properties()
    _unregister_groove_properties()
