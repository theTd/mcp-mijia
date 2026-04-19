# MCP Mijia | 米家智能家居 MCP 服务

An MCP server for controlling Xiaomi Mi Home (Mijia) smart home devices, designed for use with Xiaozhi AI assistant.

用于控制小米米家智能家居设备的 MCP 服务器，专为小智 AI 助手设计。

## Overview | 概述

This project provides an MCP (Model Context Protocol) server that enables AI assistants like Xiaozhi to control Xiaomi Mi Home smart devices through natural language commands. It supports listing devices, getting/setting properties, running actions, and executing scenes.

本项目提供一个 MCP 服务器，使小智等 AI 助手能够通过自然语言命令控制小米米家智能设备。支持列出设备、获取/设置属性、运行动作和执行场景。

## Features | 特性

- 🏠 List and manage multiple homes | 列出和管理多个家庭
- 📱 Discover and control all Mi Home devices | 发现和控制所有米家设备
- 💡 High-level device control (on/off/toggle) | 高级设备控制（开/关/切换）
- ⚙️ Get and set device properties | 获取和设置设备属性
- 🎬 Run device actions and scenes | 运行设备动作和场景
- 🔍 Query device capabilities | 查询设备能力

## Device Identification | 设备标识 (DID)

All device-related tools support both `dev_name` (device name) and `did` (Device ID). **It is highly recommended to use `did` for operations**, as device names may not be unique or may change. You can find the `did` for each device using the `list_devices` tool.

所有设备相关的工具都支持 `dev_name`（设备名称）和 `did`（设备 ID）。**强烈建议使用 `did` 进行操作**，因为设备名称可能不唯一或可能发生更改。您可以使用 `list_devices` 工具找到每个设备的 `did`。

## Available Tools | 可用工具

| Tool | Description | Recommended Param |
|------|-------------|-------------------|
| `list_homes` | List all homes in the Mi Home account | - |
| `list_devices` | List all devices (optionally filter by home) | - |
| `list_device_capabilities` | List available properties and actions for a device | `did` |
| `get_device_properties` | Get all property values for a device | `did` |
| `get_device_property` | Get a specific property value | `did` |
| `set_device_property` | Set a property value on a device | `did` |
| `run_device_action` | Run an action on a device | `did` |
| `control_device` | High-level control: 'on', 'off', 'toggle', or 'property=value' | `did` |
| `list_scenes` | List all scenes/automations | - |
| `run_scene` | Run a scene by its ID | - |

## Quick Start | 快速开始

1. Install dependencies | 安装依赖:
```bash
pip install -r requirements.txt
```

2. First run authentication | 首次运行认证:
```bash
python test_mijia.py
```
*Follow the prompts to log in with your Mi Home account by QR code on the first run.*

*首次运行时按照提示用二维码登录您的米家账号。*

3. Run with Xiaozhi | 配合小智运行:
```bash
export MCP_ENDPOINT=wss://api.xiaozhi.me/mcp/?token=xxx
python mcp_pipe.py mijia.py
```
Or run all configured servers | 或运行所有配置的服务:
```bash
export MCP_ENDPOINT=wss://api.xiaozhi.me/mcp/?token=xxx
python mcp_pipe.py
```

4. Interactive mode for testing (optional) | 交互模式测试(可选):
```bash
python test_mijia.py -i
```
Enter commands interactively to test device control. | 交互式输入命令测试设备控制。

Commands:
  1. List device capabilities
  2. Get device properties
  3. Get specific property
  4. Set property
  5. Control device (on/off/toggle)
  6. Run device action
  7. List scenes
  8. Run scene

## Configuration | 配置

### Environment Variables | 环境变量

| Variable | Description |
|----------|-------------|
| `MIJIA_AUTH_PATH` | Custom path for authentication file (optional) |
| `MCP_ENDPOINT` | WebSocket endpoint for Xiaozhi connection, such as wss://api.xiaozhi.me/mcp/?token=\<YourToken\> |

### MCP Config | MCP 配置

The `mcp_config.json` defines the server configuration:

```json
{
  "mcpServers": {
    "local-stdio-mijia": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "mijia"]
    }
  }
}
```

## Project Structure | 项目结构

| File | Description |
|------|-------------|
| `mijia.py` | MCP server with all smart home control tools |
| `mcp_pipe.py` | WebSocket communication pipe for Xiaozhi |
| `mcp_config.json` | Server configuration |
| `test_mijia.py` | Test script for verifying functionality |

## Usage Examples | 使用示例

Once connected to Xiaozhi, you can use natural language commands like:

连接小智后，您可以使用自然语言命令，例如：

- "Turn on the living room light" | "打开客厅灯"
- "Set bedroom light brightness to 50%" | "把卧室灯亮度设为50%"
- "What's the temperature of the air conditioner?" | "空调温度是多少？"
- "Run the 'Good Night' scene" | "执行'晚安'场景"
- "List all my devices" | "列出所有设备"

## Requirements | 环境要求

- Python 3.10+
- python-dotenv>=1.2.1
- websockets>=15.0.1
- mcp>=1.20.0
- pydantic>=2.12.3
- mcp-proxy>=0.10.0
- fastmcp>=2.13.0
- mijiaAPI>=3.0.0

## Contributing | 贡献指南

Contributions are welcome! Please feel free to submit a Pull Request.

欢迎贡献代码！请随时提交 Pull Request。

## License | 许可证

This project is licensed under the MIT License - see the LICENSE file for details.

本项目采用 MIT 许可证 - 详情请查看 LICENSE 文件。

## Acknowledgments | 致谢

- [mijiaAPI](https://github.com/nickel110/mijiaAPI) - Xiaomi Mi Home API library
- [Xiaozhi](https://github.com/78/xiaozhi-esp32) - AI assistant platform
