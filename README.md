# 大肥鱼桌宠 🐟

一个可爱的桌面宠物 —— **大肥鱼**，会浮在屏幕上游来游去，陪你摸鱼！

- 左键按住拖拽（会侧身朝向拖动方向）
- 单击蹦跳 + 回嘴
- 双击 / 右键菜单打开「鲸语讯道」AI 对话面板
- 右键 / 托盘菜单：完整设置面板
- 空闲时随机戳一戳、自发碎碎念

## 仓库链接

GitHub: [https://github.com/Yumiko-rin/dafeiyu-pet](https://github.com/Yumiko-rin/dafeiyu-pet)

## 技术栈

- Python 3
- **PySide6** (Qt for Python) — GUI 框架
- **requests** — 余额查询网络请求
- **PyInstaller** — 打包为 Windows 可执行文件

## 快速开始

### 开发环境

```bash
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

打包完成后，exe 文件位于：

```
dist/大肥鱼桌宠.exe
```

## 发布到 GitHub Releases

将已打包好的 exe 上传到 GitHub Release，供用户直接下载使用：

### 方法一：在 GitHub 网页操作

1. 打开仓库 [Yumiko-rin/dafeiyu-pet](https://github.com/Yumiko-rin/dafeiyu-pet)
2. 点击右侧导航栏的 **Releases**
3. 点击 **Create a new release** (或 **Draft a new release**)
4. 填写 **Tag version**（例如 `v1.0.0`）
5. 填写 **Release title**（例如 `v1.0.0 - 初始版本`）
6. 在描述框中写明更新内容
7. 在 **Binaries** 区域点击 **Attach binaries by dropping them here or selecting them**
8. 选择 `dist/大肥鱼桌宠.exe` 文件上传
9. 点击 **Publish release**

### 方法二：使用 GitHub CLI (`gh`)

```bash
# 创建 tag
git tag v1.0.0
git push origin v1.0.0

# 创建 Release 并上传 exe
gh release create v1.0.0 dist/大肥鱼桌宠.exe --title "v1.0.0 - 初始版本" --notes "发行说明"
```

用户下载后即可直接双击运行 `大肥鱼桌宠.exe`，无需安装 Python 环境。

## 项目结构

```
大肥鱼桌宠/
├── 桌宠.py              # 程序入口
├── 桌宠.spec            # PyInstaller 打包配置
├── 启动桌宠.bat         # Windows 启动脚本
├── requirements.txt     # Python 依赖
├── pet/                 # 核心代码包
│   ├── pet_window.py    # 主窗口（三视图透明桌宠 + 动画 + 交互 + 托盘）
│   ├── config.py        # 配置管理
│   ├── services.py      # 服务（AI 对话、余额查询）
│   ├── panels.py        # 面板组件
│   ├── sound.py         # 音效
│   └── settings.py      # 设置
├── assets/              # 资源文件（图片、音效等）
└── dist/                # 打包输出目录
    └── 大肥鱼桌宠.exe
```

## License

MIT