# mijia.py - MCP server for Xiaomi Mi Home (Mijia) smart home control
from fastmcp import FastMCP
import sys
import logging
import os
from typing import Annotated, Optional

from pydantic import Field

logger = logging.getLogger('Mijia')

DeviceNameArg = Annotated[
    Optional[str],
    Field(description="Device name. Optional when did is provided."),
]
DeviceDidArg = Annotated[
    Optional[str],
    Field(description="Device DID. Preferred for exact targeting, especially when device names are duplicated."),
]
CommandArg = Annotated[
    str,
    Field(description="Control command to run on the selected device, such as 'on', 'off', 'toggle', or 'brightness=50'."),
]
PropertyNameArg = Annotated[
    str,
    Field(description="Property name to get or set on the selected device."),
]
PropertyValueArg = Annotated[
    str,
    Field(description="Property value to set. The server will auto-convert bool, int, and float strings when possible."),
]
ActionNameArg = Annotated[
    str,
    Field(description="Action name to run on the selected device."),
]
JsonSafeArg = Annotated[
    bool,
    Field(description="When true, return JSON-safe property and action name lists instead of raw capability objects."),
]

# Fix UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stderr.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')

from mijiaAPI import (
    mijiaAPI, mijiaDevice,
    LoginError, DeviceNotFoundError, MultipleDevicesFoundError,
    DeviceGetError, DeviceSetError, DeviceActionError, APIError
)

# Create an MCP server
mcp = FastMCP("Mijia")

# Global API instance
_api = None

def get_api() -> mijiaAPI:
    """Get or create the mijiaAPI instance."""
    global _api
    if _api is None:
        auth_path = os.environ.get('MIJIA_AUTH_PATH', None)
        _api = mijiaAPI(auth_path) if auth_path else mijiaAPI()
        _api.login()
        logger.info("Successfully logged in to Mijia API")
    return _api


def resolve_device(dev_name: Optional[str] = None, did: Optional[str] = None) -> mijiaDevice:
    """Resolve a device by DID first, falling back to device name for compatibility."""
    if did:
        return mijiaDevice(get_api(), did=did)
    if dev_name:
        return mijiaDevice(get_api(), dev_name=dev_name)
    raise ValueError("Either did or dev_name must be provided")


def build_device_result(device: mijiaDevice, **extra) -> dict:
    """Build a consistent response payload for device-level operations."""
    result = {
        "success": True,
        "device": device.name,
        "did": device.did,
        "model": device.model,
    }
    result.update(extra)
    return result


def build_not_found_error(dev_name: Optional[str] = None, did: Optional[str] = None) -> dict:
    """Build a precise not-found response for the device selector that was used."""
    if did:
        return {"success": False, "error": f"Device with did '{did}' not found"}
    return {"success": False, "error": f"Device '{dev_name}' not found"}


def build_multiple_devices_error(dev_name: Optional[str] = None, did: Optional[str] = None) -> dict:
    """Build a precise duplicate-device response for the device selector that was used."""
    if did:
        return {"success": False, "error": f"Multiple devices found with did '{did}', please verify the device list"}
    return {"success": False, "error": f"Multiple devices found with name '{dev_name}', please use did to select the exact device"}


def serialize_capability_names(capabilities) -> list[str]:
    """Return capability names as plain strings for JSON-safe tool responses."""
    if isinstance(capabilities, dict):
        return sorted(capabilities.keys())
    if isinstance(capabilities, (list, tuple, set)):
        names = []
        for item in capabilities:
            if isinstance(item, str):
                names.append(item)
            else:
                names.append(getattr(item, "name", str(item)))
        return sorted(set(names))
    return []


def convert_value(value: str):
    """Auto-convert a string value to bool, int, float, or keep as string."""
    if value.lower() == 'true':
        return True
    if value.lower() == 'false':
        return False
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value


def get_device_properties(dev_name: Optional[str] = None, did: Optional[str] = None) -> dict:
    """Get all available properties and their current values for a device."""
    try:
        device = resolve_device(dev_name=dev_name, did=did)
        props = {}
        for prop_name in device.prop_list:
            try:
                props[prop_name] = device.get(prop_name)
            except (DeviceGetError, ValueError):
                props[prop_name] = None
        logger.info(f"Got properties for device '{device.name}' ({device.did}): {props}")
        return build_device_result(device, properties=props)
    except ValueError as e:
        return {"success": False, "error": str(e)}
    except DeviceNotFoundError as e:
        logger.error(f"Device not found: {e}")
        return build_not_found_error(dev_name=dev_name, did=did)
    except MultipleDevicesFoundError as e:
        logger.error(f"Multiple devices found: {e}")
        return build_multiple_devices_error(dev_name=dev_name, did=did)
    except (LoginError, APIError) as e:
        logger.error(f"API error: {e}")
        return {"success": False, "error": str(e)}


def get_device_property(
    dev_name: Optional[str] = None,
    *args,
    prop_name: Optional[str] = None,
    did: Optional[str] = None,
) -> dict:
    """Get a specific property value from a device."""
    if args:
        if len(args) != 1:
            raise TypeError(f"get_device_property() takes at most 2 positional arguments but {len(args) + 1} were given")
        if prop_name is not None:
            raise TypeError("get_device_property() got multiple values for argument 'prop_name'")
        prop_name = args[0]
    if prop_name is None:
        raise TypeError("get_device_property() missing required argument: 'prop_name'")

    try:
        device = resolve_device(dev_name=dev_name, did=did)
        value = device.get(prop_name)
        logger.info(f"Got property '{prop_name}' from device '{device.name}' ({device.did}): {value}")
        return build_device_result(device, property=prop_name, value=value)
    except ValueError as e:
        return {"success": False, "error": str(e)}
    except DeviceNotFoundError:
        return build_not_found_error(dev_name=dev_name, did=did)
    except MultipleDevicesFoundError:
        return build_multiple_devices_error(dev_name=dev_name, did=did)
    except DeviceGetError as e:
        logger.error(f"Failed to get property: {e}")
        return {"success": False, "error": f"Failed to get property '{prop_name}': {e}"}
    except (LoginError, APIError) as e:
        logger.error(f"API error: {e}")
        return {"success": False, "error": str(e)}


def set_device_property(
    dev_name: Optional[str] = None,
    *args,
    prop_name: Optional[str] = None,
    value: Optional[str] = None,
    did: Optional[str] = None,
) -> dict:
    """Set a property value on a device."""
    if len(args) > 2:
        raise TypeError(f"set_device_property() takes at most 3 positional arguments but {len(args) + 1} were given")
    if len(args) >= 1:
        if prop_name is not None:
            raise TypeError("set_device_property() got multiple values for argument 'prop_name'")
        prop_name = args[0]
    if len(args) == 2:
        if value is not None:
            raise TypeError("set_device_property() got multiple values for argument 'value'")
        value = args[1]
    if prop_name is None:
        raise TypeError("set_device_property() missing required argument: 'prop_name'")
    if value is None:
        raise TypeError("set_device_property() missing required argument: 'value'")

    try:
        device = resolve_device(dev_name=dev_name, did=did)
        converted_value = convert_value(value)
        device.set(prop_name, converted_value)
        logger.info(f"Set property '{prop_name}' on device '{device.name}' ({device.did}) to {converted_value}")
        return build_device_result(device, property=prop_name, value=converted_value)
    except ValueError as e:
        return {"success": False, "error": str(e)}
    except DeviceNotFoundError:
        return build_not_found_error(dev_name=dev_name, did=did)
    except MultipleDevicesFoundError:
        return build_multiple_devices_error(dev_name=dev_name, did=did)
    except DeviceSetError as e:
        logger.error(f"Failed to set property: {e}")
        return {"success": False, "error": f"Failed to set property '{prop_name}': {e}"}
    except (LoginError, APIError) as e:
        logger.error(f"API error: {e}")
        return {"success": False, "error": str(e)}


def run_device_action(
    dev_name: Optional[str] = None,
    *args,
    action_name: Optional[str] = None,
    did: Optional[str] = None,
) -> dict:
    """Run an action on a device."""
    if args:
        if len(args) != 1:
            raise TypeError(f"run_device_action() takes at most 2 positional arguments but {len(args) + 1} were given")
        if action_name is not None:
            raise TypeError("run_device_action() got multiple values for argument 'action_name'")
        action_name = args[0]
    if action_name is None:
        raise TypeError("run_device_action() missing required argument: 'action_name'")

    try:
        device = resolve_device(dev_name=dev_name, did=did)
        device.run_action(action_name)
        logger.info(f"Ran action '{action_name}' on device '{device.name}' ({device.did})")
        return build_device_result(device, action=action_name)
    except ValueError as e:
        return {"success": False, "error": str(e)}
    except DeviceNotFoundError:
        return build_not_found_error(dev_name=dev_name, did=did)
    except MultipleDevicesFoundError:
        return build_multiple_devices_error(dev_name=dev_name, did=did)
    except DeviceActionError as e:
        logger.error(f"Failed to run action: {e}")
        return {"success": False, "error": f"Failed to run action '{action_name}': {e}"}
    except (LoginError, APIError) as e:
        logger.error(f"API error: {e}")
        return {"success": False, "error": str(e)}


def list_device_capabilities(
    dev_name: Optional[str] = None,
    did: Optional[str] = None,
    json_safe: bool = False,
) -> dict:
    """List all available properties and actions for a device."""
    try:
        device = resolve_device(dev_name=dev_name, did=did)
        logger.info(f"Got capabilities for device '{device.name}' ({device.did})")
        properties = device.prop_list
        actions = device.action_list
        if json_safe:
            properties = serialize_capability_names(properties)
            actions = serialize_capability_names(actions)
        return build_device_result(
            device,
            properties=properties,
            actions=actions,
        )
    except ValueError as e:
        return {"success": False, "error": str(e)}
    except DeviceNotFoundError:
        return build_not_found_error(dev_name=dev_name, did=did)
    except MultipleDevicesFoundError:
        return build_multiple_devices_error(dev_name=dev_name, did=did)
    except (LoginError, APIError) as e:
        logger.error(f"API error: {e}")
        return {"success": False, "error": str(e)}


def control_device(
    dev_name: Optional[str] = None,
    *args,
    command: Optional[str] = None,
    did: Optional[str] = None,
) -> dict:
    """
    High-level device control with common commands.
    Supported commands: 'on', 'off', 'toggle', or property assignments like 'brightness=50', 'color_temperature=4000'.
    For lights: 'on', 'off', 'toggle', 'brightness=<0-100>', 'color_temperature=<value>'
    For switches/plugs: 'on', 'off', 'toggle'
    """
    if args:
        if len(args) != 1:
            raise TypeError(f"control_device() takes at most 2 positional arguments but {len(args) + 1} were given")
        if command is not None:
            raise TypeError("control_device() got multiple values for argument 'command'")
        command = args[0]
    if command is None:
        raise TypeError("control_device() missing required argument: 'command'")

    try:
        device = resolve_device(dev_name=dev_name, did=did)
        command = command.strip().lower()

        if command == 'on':
            if 'on' in device.prop_list:
                device.set('on', True)
            else:
                device.run_action('turn-on')
            logger.info(f"Turned on device '{device.name}' ({device.did})")
            return build_device_result(device, action="turned on")

        if command == 'off':
            if 'on' in device.prop_list:
                device.set('on', False)
            else:
                device.run_action('turn-off')
            logger.info(f"Turned off device '{device.name}' ({device.did})")
            return build_device_result(device, action="turned off")

        if command == 'toggle':
            device.run_action('toggle')
            logger.info(f"Toggled device '{device.name}' ({device.did})")
            return build_device_result(device, action="toggled")

        if '=' in command:
            prop, value = command.split('=', 1)
            prop = prop.strip()
            value = value.strip()
            converted = convert_value(value)
            device.set(prop, converted)
            logger.info(f"Set '{prop}' to {converted} on device '{device.name}' ({device.did})")
            return build_device_result(device, property=prop, value=converted)

        return {"success": False, "error": f"Unknown command '{command}'. Use 'on', 'off', 'toggle', or 'property=value'"}
    except ValueError as e:
        return {"success": False, "error": str(e)}
    except DeviceNotFoundError:
        return build_not_found_error(dev_name=dev_name, did=did)
    except MultipleDevicesFoundError:
        return build_multiple_devices_error(dev_name=dev_name, did=did)
    except (DeviceSetError, DeviceActionError) as e:
        logger.error(f"Failed to control device: {e}")
        return {"success": False, "error": str(e)}
    except (LoginError, APIError) as e:
        logger.error(f"API error: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
def list_homes() -> dict:
    """List all homes in the Mi Home account."""
    try:
        api = get_api()
        homes = api.get_homes_list()
        homes.sort(key=lambda x: x.get("id", ""))
        logger.info(f"Found {len(homes)} homes")
        return {"success": True, "homes": homes}
    except (LoginError, APIError) as e:
        logger.error(f"Failed to list homes: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
def list_devices(home_id: str = None) -> dict:
    """List all devices in the Mi Home account. Optionally filter by home_id."""
    try:
        api = get_api()
        devices = api.get_devices_list(home_id=home_id)
        result = [{"name": d.get("name"), "model": d.get("model"), "did": d.get("did")} for d in devices]
        result.sort(key=lambda x: x.get("did", ""))
        logger.info(f"Found {len(result)} devices")
        return {"success": True, "devices": result}
    except (LoginError, APIError) as e:
        logger.error(f"Failed to list devices: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool(name="get_device_properties")
def get_device_properties_tool(dev_name: DeviceNameArg = None, did: DeviceDidArg = None) -> dict:
    """Get all available properties and their current values for a device."""
    return get_device_properties(dev_name=dev_name, did=did)


@mcp.tool(name="get_device_property")
def get_device_property_tool(
    prop_name: PropertyNameArg,
    dev_name: DeviceNameArg = None,
    did: DeviceDidArg = None,
) -> dict:
    """Get a specific property value from a device. Use list_device_capabilities to see available properties."""
    return get_device_property(dev_name=dev_name, prop_name=prop_name, did=did)


@mcp.tool(name="set_device_property")
def set_device_property_tool(
    prop_name: PropertyNameArg,
    value: PropertyValueArg,
    dev_name: DeviceNameArg = None,
    did: DeviceDidArg = None,
) -> dict:
    """Set a property value on a device. The value will be automatically converted to the appropriate type (bool, int, float, or string)."""
    return set_device_property(dev_name=dev_name, prop_name=prop_name, value=value, did=did)


@mcp.tool(name="run_device_action")
def run_device_action_tool(
    action_name: ActionNameArg,
    dev_name: DeviceNameArg = None,
    did: DeviceDidArg = None,
) -> dict:
    """Run an action on a device (e.g., 'toggle', 'start-sweep'). Use list_device_capabilities to see available actions."""
    return run_device_action(dev_name=dev_name, action_name=action_name, did=did)


@mcp.tool(name="list_device_capabilities")
def list_device_capabilities_tool(
    dev_name: DeviceNameArg = None,
    did: DeviceDidArg = None,
    json_safe: JsonSafeArg = False,
) -> dict:
    """List all available properties and actions for a device."""
    return list_device_capabilities(dev_name=dev_name, did=did, json_safe=json_safe)


@mcp.tool()
def list_scenes() -> dict:
    """List all available scenes/automations in Mi Home."""
    try:
        api = get_api()
        scenes = api.get_scenes_list()
        scenes.sort(key=lambda x: x.get("scene_id", ""))
        logger.info(f"Found {len(scenes)} scenes")
        return {"success": True, "scenes": scenes}
    except (LoginError, APIError) as e:
        logger.error(f"Failed to list scenes: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
def run_scene(scene_id: str, home_id: str) -> dict:
    """Run a scene/automation by its ID. Use list_scenes to get available scene IDs."""
    try:
        api = get_api()
        api.run_scene(scene_id=scene_id, home_id=home_id)
        logger.info(f"Ran scene '{scene_id}'")
        return {"success": True, "scene_id": scene_id}
    except (LoginError, APIError) as e:
        logger.error(f"Failed to run scene: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool(name="control_device")
def control_device_tool(
    command: CommandArg,
    dev_name: DeviceNameArg = None,
    did: DeviceDidArg = None,
) -> dict:
    """
    High-level device control with common commands.
    Supported commands: 'on', 'off', 'toggle', or property assignments like 'brightness=50', 'color_temperature=4000'.
    For lights: 'on', 'off', 'toggle', 'brightness=<0-100>', 'color_temperature=<value>'
    For switches/plugs: 'on', 'off', 'toggle'
    """
    return control_device(dev_name=dev_name, command=command, did=did)


# Start the server
if __name__ == "__main__":
    mcp.run(transport="stdio")
