# 大肥鱼桌宠

> 一只叫「大肥鱼」的鲸鱼娘，住进你的桌面，陪你摸鱼。

[![GitHub Release](https://img.shields.io/github/v/release/Yumiko-rin/dafeiyu-pet)](https://github.com/Yumiko-rin/dafeiyu-pet/releases)
[![GitHub](https://img.shields.io/github/license/Yumiko-rin/dafeiyu-pet)](https://github.com/Yumiko-rin/dafeiyu-pet)

**大肥鱼桌宠**是一款 Windows 桌面宠物应用。她会浮在屏幕上自由游荡，你可以拖拽她、戳她，她也会在空闲时主动戳戳你、碎碎念几句，给你一点陪伴感。

---

## 特性

- **三视图桌宠** — 正面、侧面、背面三套多尺寸精灵图，行走/拖拽时自动切换，朝向跟随拖动方向
- **拖拽交互** — 左键按住拖拽，她会侧身朝向拖动方向，松手后继续漫步
- **单击蹦跳** — 单击桌宠，她会蹦跳一下并冒出一句回嘴台词（带轻响音效）
- **空闲陪伴** — 桌宠空闲时会随机戳一戳你，或定时自发碎碎念，增强陪伴感
- **可视化设置** — 右键打开设置面板，可调整大小、置顶、穿透点击、音效开关等，无需重启
- **音效反馈** — 单击蹦跳一声「啵」，可在设置中关闭
- **托盘菜单** — 系统托盘常驻，随时唤出所有功能

---

## 截图

| 状态 | 示意 |
|------|------|
| 散步 | 大肥鱼在桌面上自由游荡，三视图轮换 |
| 拖拽 | 按住左键拖拽，侧身朝向拖动方向 |
| 设置 | 右键菜单 → 设置，调整所有参数 |

---

## 快速开始

### 直接下载（推荐）

从 [Releases](https://github.com/Yumiko-rin/dafeiyu-pet/releases) 下载最新版 `大肥鱼桌宠.exe`，双击运行即可，无需安装 Python。

### 源码运行

```bash
# 克隆仓库
git clone https://github.com/Yumiko-rin/dafeiyu-pet.git
cd dafeiyu-pet

# 安装依赖
pip install -r requirements.txt

# 启动桌宠
python 桌宠.py
```

或直接双击 `启动桌宠.bat`（无终端窗口）。

### 打包为 exe

```bash
pyinstaller --noconfirm --clean 桌宠.spec
```

输出位置：`dist/大肥鱼桌宠.exe`

---

## 使用指南

### 基本操作

| 操作 | 效果 |
|------|------|
| 左键按住 + 拖动 | 拖拽桌宠，侧身朝向拖动方向 |
| 单击左键 | 桌宠蹦跳 + 回嘴台词 |
| 双击左键 | 打开桌面时钟面板 |
| 右键单击 | 弹出功能菜单 |

---

## 项目结构

```
大肥鱼桌宠/
├── 桌宠.py              # 程序入口
├── 桌宠.spec            # PyInstaller 打包配置
├── 启动桌宠.bat         # Windows 无终端启动脚本
├── requirements.txt     # Python 依赖
├── pet/                 # 核心代码
│   ├── pet_window.py    # 主窗口：三视图精灵 + 动画 + 交互 + 托盘
│   ├── panels/          # 功能面板集合
│   │   ├── base.py      # 面板基类
│   │   ├── clock_calendar.py  # 桌面时钟/日历
│   │   ├── countdown.py       # 倒计时提醒
│   │   ├── system_monitor.py  # 系统监控
│   │   ├── sticky_notes.py    # 便签备忘录
│   │   ├── pomodoro.py        # 番茄钟
│   │   ├── clipboard_history.py # 剪贴板历史
│   │   ├── quick_launcher.py  # 快捷启动器
│   │   ├── weather.py         # 天气显示
│   │   ├── guess_number.py    # 猜数字游戏
│   │   └── fish_time.py       # 摸鱼计时器
│   ├── settings.py      # 可视化设置面板
│   ├── config.py        # 配置管理
│   ├── sound.py         # 音效管理
│   ├── effects.py       # 粒子特效系统
│   ├── logger.py        # 日志系统
│   ├── notifications.py # 通知系统
│   ├── hotkeys.py       # 快捷键管理
│   ├── lines.py         # 鲸鱼娘台词库
│   ├── styles.py        # 公共样式常量
│   └── __init__.py
├── sprites/             # 精灵图（正面/侧面/背面 × 多尺寸）
├── sounds/              # 音效文件
└── tools/               # 辅助工具
```

---

## 技术栈

- **Python 3** — 开发语言
- **PySide6** (Qt for Python) — GUI 框架，透明窗口、三视图渲染、动画循环
- **psutil** — 系统监控（CPU/内存/磁盘/网络）
- **requests** — 网络请求（天气查询）
- **PyInstaller** — 打包为单文件 exe，用户免装 Python 直接运行

---

## License

[MIT](LICENSE)

---

## 链接

- GitHub 仓库：[Yumiko-rin/dafeiyu-pet](https://github.com/Yumiko-rin/dafeiyu-pet)
- 问题反馈：[Issues](https://github.com/Yumiko-rin/dafeiyu-pet/issues)
- 下载：[Releases](https://github.com/Yumiko-rin/dafeiyu-pet/releases)