# mijia.py - MCP server for Xiaomi Mi Home (Mijia) smart home control
from fastmcp import FastMCP
import sys
import logging
import os

logger = logging.getLogger('Mijia')

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


@mcp.tool()
def get_device_properties(dev_name: str) -> dict:
    """Get all available properties and their current values for a device by its name."""
    try:
        api = get_api()
        device = mijiaDevice(api, dev_name=dev_name)
        props = {}
        for prop_name in device.prop_list:
            try:
                props[prop_name] = device.get(prop_name)
            except (DeviceGetError, ValueError):
                props[prop_name] = None
        logger.info(f"Got properties for device '{dev_name}': {props}")
        return {"success": True, "device": dev_name, "properties": props}
    except DeviceNotFoundError as e:
        logger.error(f"Device not found: {e}")
        return {"success": False, "error": f"Device '{dev_name}' not found"}
    except MultipleDevicesFoundError as e:
        logger.error(f"Multiple devices found: {e}")
        return {"success": False, "error": f"Multiple devices found with name '{dev_name}', please be more specific"}
    except (LoginError, APIError) as e:
        logger.error(f"API error: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_device_property(dev_name: str, prop_name: str) -> dict:
    """Get a specific property value from a device. Use list_device_capabilities to see available properties."""
    try:
        api = get_api()
        device = mijiaDevice(api, dev_name=dev_name)
        value = device.get(prop_name)
        logger.info(f"Got property '{prop_name}' from device '{dev_name}': {value}")
        return {"success": True, "device": dev_name, "property": prop_name, "value": value}
    except DeviceNotFoundError:
        return {"success": False, "error": f"Device '{dev_name}' not found"}
    except MultipleDevicesFoundError:
        return {"success": False, "error": f"Multiple devices found with name '{dev_name}', please be more specific"}
    except DeviceGetError as e:
        logger.error(f"Failed to get property: {e}")
        return {"success": False, "error": f"Failed to get property '{prop_name}': {e}"}
    except (LoginError, APIError) as e:
        logger.error(f"API error: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
def set_device_property(dev_name: str, prop_name: str, value: str) -> dict:
    """Set a property value on a device. The value will be automatically converted to the appropriate type (bool, int, float, or string)."""
    try:
        api = get_api()
        device = mijiaDevice(api, dev_name=dev_name)

        # Auto-convert value to appropriate type
        converted_value = value
        if value.lower() == 'true':
            converted_value = True
        elif value.lower() == 'false':
            converted_value = False
        else:
            try:
                converted_value = int(value)
            except ValueError:
                try:
                    converted_value = float(value)
                except ValueError:
                    pass  # Keep as string

        device.set(prop_name, converted_value)
        logger.info(f"Set property '{prop_name}' on device '{dev_name}' to {converted_value}")
        return {"success": True, "device": dev_name, "property": prop_name, "value": converted_value}
    except DeviceNotFoundError:
        return {"success": False, "error": f"Device '{dev_name}' not found"}
    except MultipleDevicesFoundError:
        return {"success": False, "error": f"Multiple devices found with name '{dev_name}', please be more specific"}
    except DeviceSetError as e:
        logger.error(f"Failed to set property: {e}")
        return {"success": False, "error": f"Failed to set property '{prop_name}': {e}"}
    except (LoginError, APIError) as e:
        logger.error(f"API error: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
def run_device_action(dev_name: str, action_name: str) -> dict:
    """Run an action on a device (e.g., 'toggle', 'start-sweep'). Use list_device_capabilities to see available actions."""
    try:
        api = get_api()
        device = mijiaDevice(api, dev_name=dev_name)
        device.run_action(action_name)
        logger.info(f"Ran action '{action_name}' on device '{dev_name}'")
        return {"success": True, "device": dev_name, "action": action_name}
    except DeviceNotFoundError:
        return {"success": False, "error": f"Device '{dev_name}' not found"}
    except MultipleDevicesFoundError:
        return {"success": False, "error": f"Multiple devices found with name '{dev_name}', please be more specific"}
    except DeviceActionError as e:
        logger.error(f"Failed to run action: {e}")
        return {"success": False, "error": f"Failed to run action '{action_name}': {e}"}
    except (LoginError, APIError) as e:
        logger.error(f"API error: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
def list_device_capabilities(dev_name: str) -> dict:
    """List all available properties and actions for a device."""
    try:
        api = get_api()
        device = mijiaDevice(api, dev_name=dev_name)
        logger.info(f"Got capabilities for device '{dev_name}'")
        return {
            "success": True,
            "device": dev_name,
            "properties": device.prop_list,
            "actions": device.action_list
        }
    except DeviceNotFoundError:
        return {"success": False, "error": f"Device '{dev_name}' not found"}
    except MultipleDevicesFoundError:
        return {"success": False, "error": f"Multiple devices found with name '{dev_name}', please be more specific"}
    except (LoginError, APIError) as e:
        logger.error(f"API error: {e}")
        return {"success": False, "error": str(e)}


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


@mcp.tool()
def control_device(dev_name: str, command: str) -> dict:
    """
    High-level device control with common commands.
    Supported commands: 'on', 'off', 'toggle', or property assignments like 'brightness=50', 'color_temperature=4000'.
    For lights: 'on', 'off', 'toggle', 'brightness=<0-100>', 'color_temperature=<value>'
    For switches/plugs: 'on', 'off', 'toggle'
    """
    try:
        api = get_api()
        device = mijiaDevice(api, dev_name=dev_name)

        command = command.strip().lower()

        if command == 'on':
            if 'on' in device.prop_list:
                device.set('on', True)
            else:
                device.run_action('turn-on')  # Try action if 'on' property doesn't exist
            logger.info(f"Turned on device '{dev_name}'")
            return {"success": True, "device": dev_name, "action": "turned on"}

        elif command == 'off':
            if 'on' in device.prop_list:
                device.set('on', False)
            else:
                device.run_action('turn-off')  # Try action if 'on' property doesn't exist
            logger.info(f"Turned off device '{dev_name}'")
            return {"success": True, "device": dev_name, "action": "turned off"}

        elif command == 'toggle':
            device.run_action('toggle')
            logger.info(f"Toggled device '{dev_name}'")
            return {"success": True, "device": dev_name, "action": "toggled"}

        elif '=' in command:
            prop, value = command.split('=', 1)
            prop = prop.strip()
            value = value.strip()

            # Convert value
            if value.lower() == 'true':
                converted = True
            elif value.lower() == 'false':
                converted = False
            else:
                try:
                    converted = int(value)
                except ValueError:
                    try:
                        converted = float(value)
                    except ValueError:
                        converted = value

            device.set(prop, converted)
            logger.info(f"Set '{prop}' to {converted} on device '{dev_name}'")
            return {"success": True, "device": dev_name, "property": prop, "value": converted}

        else:
            return {"success": False, "error": f"Unknown command '{command}'. Use 'on', 'off', 'toggle', or 'property=value'"}

    except DeviceNotFoundError:
        return {"success": False, "error": f"Device '{dev_name}' not found"}
    except MultipleDevicesFoundError:
        return {"success": False, "error": f"Multiple devices found with name '{dev_name}', please be more specific"}
    except (DeviceSetError, DeviceActionError) as e:
        logger.error(f"Failed to control device: {e}")
        return {"success": False, "error": str(e)}
    except (LoginError, APIError) as e:
        logger.error(f"API error: {e}")
        return {"success": False, "error": str(e)}


# Start the server
if __name__ == "__main__":
    mcp.run(transport="stdio")
