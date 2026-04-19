# MCP Mijia | 米家智能家居 MCP 服务

An MCP server for controlling Xiaomi Mi Home (Mijia) smart home devices, designed for use with Xiaozhi AI assistant.

用于控制小米米家智能家居设备的 MCP 服务器，专为小智 AI 助手设计。

## Overview | 概述

This project provides an MCP (Model Context Protocol) server that enables AI assistants like Xiaozhi to control Xiaomi Mi Home smart devices through natural language commands. It supports listing devices, getting/setting properties, running actions, and executing scenes.

本项目提供一个 MCP 服务器，使小智等 AI 助手能够通过自然语言命令控制小米米家智能设备。支持列出设备、获取/设置属性、运行动作和执行场景。

## Features | 特性

- 🏠 List and manage multiple homes | 列出和管理多个家庭
- 📱 Discover and control all Mi Home devices | 发现和控制所有米家设备
- 🆔 Prefer DID-based targeting for exact device control | 优先使用 DID 精确定位设备
- 💡 High-level device control (on/off/toggle) | 高级设备控制（开/关/切换）
- ⚙️ Get and set device properties | 获取和设置设备属性
- 🎬 Run device actions and scenes | 运行设备动作和场景
- 🔍 Query device capabilities | 查询设备能力

## Available Tools | 可用工具

| Tool | Description |
|------|-------------|
| `list_homes` | List all homes in the Mi Home account |
| `list_devices` | List all devices (optionally filter by home) |
| `list_device_capabilities` | List available properties and actions for a device (`did` preferred, `dev_name` compatible) |
| `get_device_properties` | Get all property values for a device (`did` preferred, `dev_name` compatible) |
| `get_device_property` | Get a specific property value (`did` preferred, `dev_name` compatible) |
| `set_device_property` | Set a property value on a device (`did` preferred, `dev_name` compatible) |
| `run_device_action` | Run an action on a device (`did` preferred, `dev_name` compatible) |
| `control_device` | High-level control: 'on', 'off', 'toggle', or 'property=value' (`did` preferred, `dev_name` compatible) |
| `list_scenes` | List all scenes/automations |
| `run_scene` | Run a scene by its ID |

## Server Guidance | 服务器提示

This server now exposes MCP-level `instructions` for clients that read server guidance automatically.

该服务现在提供 MCP 级别的 `instructions`，供会自动读取服务器提示的客户端直接使用。

The server guidance is opinionated on purpose:

这层服务器提示是有意做得比较强约束的：

- Resolve home first, then devices inside that home. | 先定位家庭，再定位该家庭内的设备。
- Lock onto `did` once discovered. | 一旦拿到 `did`，后续就固定使用它。
- For simple on/off control, prefer direct control over unnecessary capability inspection. | 对简单开关动作，优先直接控制，不要默认先查 capability。
- After writes, verify final state by reading back a key property. | 写操作后必须回读关键属性确认最终状态。
- On failure, restate the actual tool error before guessing causes. | 失败时先复述真实工具错误，再讨论原因。

The server also exposes a prompt named `safe_control_playbook`.

服务还额外暴露了一个名为 `safe_control_playbook` 的 prompt。

Use it when your MCP client supports prompt discovery and you want an explicit control playbook before executing device actions.

如果你的 MCP 客户端支持 prompt discovery，并且你希望在执行设备控制前先拿到一份明确的操作剧本，就使用它。

## Device Targeting | 设备定位

Device-level tools now support both `did` and `dev_name`.

设备级工具现在同时支持 `did` 和 `dev_name`。

- Prefer `did` for exact targeting, especially when multiple devices share the same name. | 优先使用 `did` 精确定位，尤其适用于重名设备。
- Existing `dev_name` calls remain compatible for older clients and scripts. | 旧的 `dev_name` 调用仍然兼容，适用于已有客户端和脚本。
- If both `did` and `dev_name` are provided, `did` takes priority. | 如果同时提供 `did` 和 `dev_name`，优先使用 `did`。
- `list_device_capabilities` supports `json_safe=true` to return plain property/action name lists. | `list_device_capabilities` 支持传入 `json_safe=true`，返回纯字符串的属性/动作名称列表。

## Prompting Guide | 提示词指南

For agents and low-parameter models, the most reliable execution order is:

对于 Agent 和低参数模型，最可靠的执行顺序是：

1. Call `list_homes` first when the user mentions a specific home/family. | 当用户提到具体家庭时，先调用 `list_homes`。
2. Match the target home by name, then call `list_devices(home_id=...)`. | 按名称匹配目标家庭，再调用 `list_devices(home_id=...)`。
3. Find the exact target device inside that home and record its `did`. | 在该家庭内找到目标设备，并记录它的 `did`。
4. Use `did` for all later reads and writes. Avoid switching back to `dev_name`. | 后续所有读写都使用 `did`，不要再切回 `dev_name`。
5. After any write, call `get_device_property` to verify the final state. | 任何写操作后都要调用 `get_device_property` 校验最终状态。
6. For lights, use `prop_name='on'` to confirm power state. | 对灯具，使用 `prop_name='on'` 确认电源状态。
7. If `control_device` reports success but the state looks stale, wait briefly and read again. If needed, fall back to `set_device_property`. | 如果 `control_device` 返回成功但状态看起来还没收敛，先短暂等待后重读，必要时回退到 `set_device_property`。

Avoid these mistakes:

避免这些错误：

- Do not control a device by name before narrowing to the correct home. | 在缩小到正确家庭前，不要仅按设备名控制。
- Do not assume the write result alone proves final state. | 不要把写操作返回值直接当成最终状态证明。
- Do not issue the write and verification read in parallel. | 不要把写操作和校验读取并发执行。
- Do not dump SDK capability objects directly to JSON. Use the tool output as returned. | 不要把 SDK 能力对象直接转成 JSON，应直接使用工具已经返回的结果。

Reusable prompt template:

可复用提示词模板：

```text
Use the local Mi Home credentials to fulfill the request safely.
If the user mentions a home/family, call list_homes first and match the home by name.
Then call list_devices with the matched home_id and identify the target device inside that home.
Record the device did and use did for all later reads and writes.
When controlling a light, prefer confirming the final state with get_device_property(prop_name="on").
Do not run the write and the verification read in parallel.
If a high-level control call succeeds but the readback still looks stale, wait briefly and read again before escalating to set_device_property.
Never expose any credential or token values in the response.
```

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

The interactive tester now shows each device DID and lets you choose DID-first targeting. | 交互测试现在会显示每个设备的 DID，并优先支持按 DID 选择设备。

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

For direct tool calls, prefer `did`, for example:

直接调用工具时，推荐优先传 `did`，例如：

```json
{
  "did": "123456789",
  "command": "on"
}
```

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
