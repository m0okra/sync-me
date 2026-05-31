# Sync-me

一个 Syncthing 的 Windows 托盘管理工具，提供便捷的进程管理、状态监控和文件迁移功能。

## 功能特性

### 核心功能

- **Syncthing 进程管理**：启动、停止、重启 Syncthing 进程，支持暂停/继续同步
- **系统托盘图标**：动态图标实时显示同步状态，通过颜色区分不同级别（蓝色=正常、橙色=警告、红色=错误）
- **状态监控**：实时解析 Syncthing 日志输出，显示同步状态文本
- **文件迁移**：支持将同步文件夹中的文件一键迁移到备份文件夹，或反向迁移
- **Web GUI 集成**：一键打开 Syncthing Web 管理界面
- **配置文件编辑**：快速打开 Syncthing 配置文件进行编辑
- **子进程管理**：额外启动受主进程管理的子进程，可用于运行内网穿透程序等用途

### 托盘菜单功能

- 显示/隐藏控制台窗口
- 迁入备份文件夹（将同步文件夹内容迁移至备份文件夹）
- 迁回同步文件夹（将备份文件夹内容迁移回同步文件夹）
- 打开 Web GUI
- 编辑配置文件
- 暂停/继续同步
- 重启软件
- 暂停/开启子进程（当 `SUBPROCESS_CONFIG["enable"]` 为 `True` 时显示）
- 重启子进程（当 `SUBPROCESS_CONFIG["enable"]` 为 `True` 时显示）
- 退出

### 其他功能

- **双击托盘图标**：快速打开 Syncthing Web GUI
- **子进程管理**：支持通过配置文件 `SUBPROCESS_CONFIG` 管理外部子进程的启动、停止、重启

## 项目结构

```
sync-me/
├── main.py                 # 主程序入口
├── run.py                  # 启动脚本（隐藏窗口启动）
├── config.py               # 配置文件
├── run.bat                 # Windows 批处理启动脚本
├── info.ico                # 应用图标
├── bin/
│   └── syncthing.exe       # Syncthing 可执行文件
├── logs/                   # 日志文件目录
└── modules/
    ├── syncthing.py        # Syncthing 进程管理模块
    ├── state_manager.py    # 状态管理和托盘图标模块
    ├── file_migrate.py     # 文件迁移模块
    ├── web_gui.py          # Web GUI 管理模块
    ├── config_editor.py    # 配置文件编辑模块
    ├── icon_draw.py        # 托盘图标绘制模块
    ├── logger.py           # 日志记录模块
    ├── timer.py            # 计时器模块
    └── win.py              # Windows 系统操作模块
```

## 安装与运行

### 从源码运行

- 安装Python与所需的依赖库
- 在[Syncthing下载界面](https://syncthing.net/downloads/)找到对应内核版本的压缩包，下载，将压缩包中的`syncthing.exe`放置于项目文件夹中的`bin/`目录下
- 按照下面三种方式中的任意一种运行

**方式一：双击批处理文件**
```
run.bat
```

**方式二：命令行运行**
```bash
python run.py
```

**方式三：直接运行主程序**
```bash
python main.py
```

### 从Release包运行

- 将Release包解压到合适的地方，然后双击`run.bat`运行

### 环境要求

- Windows 操作系统
- Python 3.x
- 依赖库：`pystray`, `Pillow`, `psutil`, `pywin32`

## 配置说明

用户配置通过根目录下的 `config.json` 文件进行。`config.py` 中定义了所有配置项的默认值，若 `config.json` 存在，其中的项会覆盖默认值；不存在的项则沿用 `config.py` 中的默认值。

### config.json 可配置项

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `CONSOLE_START_HIDE` | `bool` | `True` | 启动时是否隐藏控制台窗口 |
| `SYNCTHING_PATH` | `str` | `\bin\syncthing.exe` | Syncthing 可执行文件的相对路径 |
| `SYNCTHING_CONFIG_PATH` | `str` | `%LOCALAPPDATA%\Syncthing\config.xml` | Syncthing 配置文件路径 |
| `TEXT_EDITOR_PATH` | `str` | `notepad.exe` | 文本编辑器路径（用于编辑配置文件） |
| `LOG_PATH` | `str` | `\logs\` | 日志文件目录的相对路径 |
| `CMD_ENCODING` | `str` | `utf-8` | 命令行输出编码 |
| `CMD_STREAM_TIMEOUT` | `float` | `0.1` | 命令行流读取超时（秒） |
| `CMD_CHECK_TIMEOUT_INTERVAL` | `float` | `0.5` | 命令行检查超时间隔（秒） |
| `PROCESS_TERM_WAIT` | `float` | `2.0` | 进程终止等待时间（秒） |
| `SUBPROCESS_CONFIG` | `dict` | `{"enable": false, "command": "", "cwd": ""}` | 子进程配置，`enable` 控制是否额外启用子进程，`command` 为启动命令，`cwd` 为工作目录 |
| `FILE_MIGRATE_PATHS` | `dict` | `{}` | 文件迁移路径映射，键为同步文件夹路径，值为备份文件夹路径 |

### config.json 示例

```json
{
    "SUBPROCESS_CONFIG": {
        "enable": true,
        "command": "frpc_windows_amd64.exe -f ...",
        "cwd": "D:\\path\\to\\frpc"
    },
    "FILE_MIGRATE_PATHS": {
        "E:\\#Syncthing\\QQ图片": "E:\\#备份文件夹\\QQ图片",
        "E:\\#Syncthing\\Pixiv": "E:\\#备份文件夹\\Pixiv"
    }
}
```

### config.py 内部配置（一般不需要修改）

| 配置项 | 说明 |
|--------|------|
| `FILE_ENCODING` | 文件编码 |
| `ICON_*` | 托盘图标相关颜色和尺寸配置 |

## 托盘图标状态

| 颜色 | 状态 |
|------|------|
| 蓝色 | 正常运行 |
| 橙色 | 警告 |
| 红色 | 错误 |
| 闪烁 | 有新的同步活动 |

## 依赖库

- `pystray` - 系统托盘图标支持
- `Pillow` - 图像处理（图标绘制）
- `psutil` - 进程管理
- `pywin32` - Windows API 调用
