# FastAPI API 工作台

这是一个单文件 FastAPI 项目，提供：

- 本地 ComfyUI 工作流生图接口
- Comfly 在线生图 / 聊天接口
- 对话、画布、历史记录的本地文件存储
- `static/` 下的前端页面与 `workflows/` 下的工作流文件

## 项目结构

- `main.py`：启动入口，保持 `python main.py` 启动方式
- `app/`：本次整理出的配置、模型、服务模块
- `static/`：前端静态页面
- `workflows/`：ComfyUI 工作流 JSON
- `packages/`：离线安装依赖包
- `API/.env`：本地环境变量文件（需自行创建或复制示例）

## 运行前准备

1. 注册 Comfly 并创建 API Key
2. 复制 `.env.example` 到 `API/.env`
3. 按需填写：

```env
COMFLY_API_KEY=sk-xxxxx
COMFYUI_INSTANCES=127.0.0.1:8188,127.0.0.1:4090
```

如果你要调用本地 ComfyUI，请确保 `workflows/` 里的工作流可以在本地正常运行。

## 安装依赖

优先使用离线安装：

```bat
安装依赖.bat
```

脚本会优先从 `packages/` 安装，失败后再尝试在线安装。

## 启动

直接运行：

```bat
启动服务.bat
```

或手动执行：

```bash
python main.py
```

默认访问地址：<http://127.0.0.1:3000/>

## 运行时文件

程序启动后会按需创建：

- `output/`：输出图片
- `data/conversations/`：对话记录
- `data/canvases/`：画布记录
- `history.json`：历史记录
- `global_config.json`：旧版兼容配置

这些文件默认已加入 `.gitignore`。
