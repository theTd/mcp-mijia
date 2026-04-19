# test_mijia.py - Test script for Mijia MCP server functions
"""
Test runner for mijia.py functions.
Run with: python test_mijia.py

Note: Requires authentication with Mi Home app on first run.
Set MIJIA_AUTH_PATH environment variable to use a custom auth file path.
"""

import sys
import logging
import inspect

# Fix UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stderr.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('TestMijia')

# Import mijia functions
from mijia import (
    list_homes,
    list_devices,
    list_device_capabilities,
    get_device_property,
    get_device_properties,
    set_device_property,
    run_device_action,
    control_device,
    list_scenes,
    run_scene,
)


def print_result(name: str, result: dict):
    """Pretty print test result."""
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}")
    if result.get("success"):
        print(f"✓ SUCCESS")
        for key, value in result.items():
            if key != "success":
                print(f"  {key}: {value}")
    else:
        print(f"✗ FAILED: {result.get('error', 'Unknown error')}")
    print()


def run_signature_compatibility_checks():
    """Verify legacy dev_name calls and newer DID-based calls still bind correctly."""
    print("\n" + "="*60)
    print("RUNNING SIGNATURE COMPATIBILITY CHECKS")
    print("="*60)

    checks = [
        ("list_device_capabilities(dev_name)", list_device_capabilities, ("demo-device",), {}),
        ("list_device_capabilities(did=..., json_safe=True)", list_device_capabilities, (), {"did": "123456789", "json_safe": True}),
        ("get_device_properties(dev_name)", get_device_properties, ("demo-device",), {}),
        ("get_device_properties(did=...)", get_device_properties, (), {"did": "123456789"}),
        ("get_device_property(dev_name, prop_name)", get_device_property, ("demo-device", "on"), {}),
        ("get_device_property(prop_name=..., did=...)", get_device_property, (), {"prop_name": "on", "did": "123456789"}),
        ("set_device_property(dev_name, prop_name, value)", set_device_property, ("demo-device", "on", "false"), {}),
        ("set_device_property(prop_name=..., value=..., did=...)", set_device_property, (), {"prop_name": "on", "value": "false", "did": "123456789"}),
        ("run_device_action(dev_name, action_name)", run_device_action, ("demo-device", "toggle"), {}),
        ("run_device_action(action_name=..., did=...)", run_device_action, (), {"action_name": "toggle", "did": "123456789"}),
        ("control_device(dev_name, command)", control_device, ("demo-device", "on"), {}),
        ("control_device(command=..., did=...)", control_device, (), {"command": "on", "did": "123456789"}),
    ]

    for label, fn, args, kwargs in checks:
        inspect.signature(fn).bind(*args, **kwargs)
        print(f"  ✓ {label}")
    print()


def test_list_homes():
    """Test listing all homes."""
    result = list_homes()
    print_result("list_homes()", result)
    return result


def test_list_devices(home_id: str = None):
    """Test listing all devices."""
    result = list_devices(home_id)
    print_result(f"list_devices(home_id={home_id})", result)
    return result


def test_list_scenes():
    """Test listing all scenes."""
    result = list_scenes()
    print_result("list_scenes()", result)
    return result


def test_device_capabilities(dev_name: str = None, did: str = None):
    """Test getting device capabilities."""
    result = list_device_capabilities(dev_name=dev_name, did=did)
    print_result(f"list_device_capabilities(dev_name={dev_name!r}, did={did!r})", result)
    return result


def test_get_device_properties(dev_name: str = None, did: str = None):
    """Test getting all device properties."""
    result = get_device_properties(dev_name=dev_name, did=did)
    print_result(f"get_device_properties(dev_name={dev_name!r}, did={did!r})", result)
    return result


def test_get_device_property(prop_name: str, dev_name: str = None, did: str = None):
    """Test getting a specific device property."""
    result = get_device_property(dev_name=dev_name, prop_name=prop_name, did=did)
    print_result(f"get_device_property(dev_name={dev_name!r}, prop_name={prop_name!r}, did={did!r})", result)
    return result


def test_set_device_property(prop_name: str, value: str, dev_name: str = None, did: str = None):
    """Test setting a device property."""
    result = set_device_property(dev_name=dev_name, prop_name=prop_name, value=value, did=did)
    print_result(f"set_device_property(dev_name={dev_name!r}, prop_name={prop_name!r}, value={value!r}, did={did!r})", result)
    return result


def test_control_device(command: str, dev_name: str = None, did: str = None):
    """Test high-level device control."""
    result = control_device(dev_name=dev_name, command=command, did=did)
    print_result(f"control_device(dev_name={dev_name!r}, command={command!r}, did={did!r})", result)
    return result


def test_run_device_action(action_name: str, dev_name: str = None, did: str = None):
    """Test running a device action."""
    result = run_device_action(dev_name=dev_name, action_name=action_name, did=did)
    print_result(f"run_device_action(dev_name={dev_name!r}, action_name={action_name!r}, did={did!r})", result)
    return result


def test_run_scene(scene_id: str, home_id: str):
    """Test running a scene."""
    result = run_scene(scene_id, home_id)
    print_result(f"run_scene('{scene_id}', '{home_id}')", result)
    return result


def run_basic_tests():
    """Run basic discovery tests (safe, read-only operations)."""
    print("\n" + "="*60)
    print("RUNNING BASIC DISCOVERY TESTS")
    print("="*60)

    run_signature_compatibility_checks()

    # Test 1: List homes
    homes_result = test_list_homes()

    # Test 2: List devices
    devices_result = test_list_devices()

    # Test 3: List scenes
    test_list_scenes()

    # If we found devices, test capabilities on the first one
    if devices_result.get("success") and devices_result.get("devices"):
        first_device = devices_result["devices"][0]
        dev_name = first_device.get("name")
        did = first_device.get("did")
        if dev_name:
            print(f"\n--- Testing with first device: '{dev_name}' ({did}) ---")
            test_device_capabilities(dev_name=dev_name, did=did)
            test_get_device_properties(dev_name=dev_name, did=did)


def run_interactive_tests():
    """Interactive mode for testing specific devices."""
    print("\n" + "="*60)
    print("INTERACTIVE TEST MODE")
    print("="*60)

    # First list devices
    devices_result = test_list_devices()
    if not devices_result.get("success"):
        print("Failed to list devices. Exiting.")
        return

    devices = devices_result.get("devices", [])
    if not devices:
        print("No devices found. Exiting.")
        return

    print("\nAvailable devices:")
    for i, dev in enumerate(devices):
        print(f"  {i+1}. {dev.get('name')} ({dev.get('model')}) did={dev.get('did')}")

    def prompt_device_selector():
        selector = input("Device DID (recommended, press Enter to use name): ").strip()
        if selector:
            return {"did": selector, "dev_name": None}
        return {"did": None, "dev_name": input("Device name: ").strip()}

    while True:
        print("\n" + "-"*40)
        print("Commands:")
        print("  1. List device capabilities")
        print("  2. Get device properties")
        print("  3. Get specific property")
        print("  4. Set property")
        print("  5. Control device (on/off/toggle)")
        print("  6. Run device action")
        print("  7. List scenes")
        print("  8. Run scene")
        print("  q. Quit")
        print("-"*40)

        choice = input("Enter choice: ").strip().lower()

        if choice == 'q':
            break

        elif choice == '1':
            selector = prompt_device_selector()
            test_device_capabilities(**selector)

        elif choice == '2':
            selector = prompt_device_selector()
            test_get_device_properties(**selector)

        elif choice == '3':
            selector = prompt_device_selector()
            prop_name = input("Property name: ").strip()
            test_get_device_property(prop_name, **selector)

        elif choice == '4':
            selector = prompt_device_selector()
            prop_name = input("Property name: ").strip()
            value = input("Value: ").strip()
            test_set_device_property(prop_name, value, **selector)

        elif choice == '5':
            selector = prompt_device_selector()
            command = input("Command (on/off/toggle/brightness=50): ").strip()
            test_control_device(command, **selector)

        elif choice == '6':
            selector = prompt_device_selector()
            action_name = input("Action name: ").strip()
            test_run_device_action(action_name, **selector)

        elif choice == '7':
            test_list_scenes()

        elif choice == '8':
            scene_id = input("Scene ID: ").strip()
            home_id = input("Home ID: ").strip()
            test_run_scene(scene_id, home_id)

        else:
            print("Invalid choice.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test Mijia MCP server functions")
    parser.add_argument("--interactive", "-i", action="store_true",
                        help="Run in interactive mode")
    parser.add_argument("--device", "-d", type=str,
                        help="Device name for quick test")
    parser.add_argument("--did", type=str,
                        help="Device DID for exact quick test")
    parser.add_argument("--command", "-c", type=str,
                        help="Command to run on device (with --device or --did)")
    args = parser.parse_args()

    if (args.device or args.did) and args.command:
        # Quick device control
        test_control_device(args.command, dev_name=args.device, did=args.did)
    elif args.device or args.did:
        # Show device info
        test_device_capabilities(dev_name=args.device, did=args.did)
        test_get_device_properties(dev_name=args.device, did=args.did)
    elif args.interactive:
        run_interactive_tests()
    else:
        run_basic_tests()
