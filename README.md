# AI 商品改色工作台

基于 FastAPI、静态前端和 ComfyUI/云端图片 API 的商品批量改色工具。用户在浏览器中上传商品图片文件夹和颜色定义 TXT 文件，系统会为每张图片和每个目标颜色生成改色结果，并提供任务进度、看板统计、取消、恢复、删除和 ZIP 下载能力。

## 项目能力

- 上传一个商品图片文件夹，批量处理多张商品图。
- 上传颜色定义 TXT，按颜色列表批量生成。
- 支持本地 ComfyUI 工作流引擎。
- 支持云端 API 引擎：`gpt-image-2-client`、`gpt-image-2`、`gemini-3.1-flash-image-preview`。
- 自动记录任务状态，服务重启后恢复任务列表。
- 支持任务取消、失败/暂停任务恢复、单个删除、批量删除。
- 支持下载单个任务的全部输出结果 ZIP。
- 提供看板页面，展示任务状态、引擎分布、最近 7 天提交量和任务明细。
- 支持两台固定服务器的前端负载选择：`192.168.0.186:8000` 与 `192.168.0.34:8000`。

## 目录结构

```text
.
├── app.py                         # FastAPI 启动入口
├── backend/
│   ├── main.py                    # 路由、静态页面、任务 API、统计 API
│   ├── tasks.py                   # 任务队列、ComfyUI/API 调用、输出保存、恢复逻辑
│   ├── jobs.py                    # 内存任务表和任务数据结构
│   ├── persistence.py             # 任务 JSON 持久化
│   ├── workflow.py                # 工作流加载、品类判断、提示词生成
│   ├── comfy_client.py            # ComfyUI HTTP 客户端
│   ├── api_client.py              # 云端图片 API 客户端
│   ├── api_keys.py                # API Key 解析和轮换
│   └── config.py                  # 路径、默认参数、环境变量配置
├── frontend/
│   ├── index.html                 # 工作台页面
│   ├── dashboard.html             # 看板页面
│   ├── app.js                     # 工作台交互逻辑
│   ├── dashboard.js               # 看板图表和表格逻辑
│   └── style.css                  # 页面样式
├── docs/
│   └── DESIGNER_USER_GUIDE.md     # 面向设计人员的完整使用手册
├── image_flux2_working.json       # ComfyUI 工作流 JSON
├── batch_comfyui_flux2_recolor.py # 独立批处理脚本
├── nginx/nginx.conf               # 双服务器负载均衡示例
├── tests/                         # 单元测试
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## 快速开始

### 1. 安装依赖

建议使用 Python 3.11。

```bash
pip install -r requirements.txt
```

### 2. 启动 ComfyUI

如果使用本地 ComfyUI 引擎，需要先启动 ComfyUI，并确保它可以通过下面地址访问：

```text
http://127.0.0.1:8188
```

可以用环境变量修改 ComfyUI 地址：

```bash
COMFY_URL=http://127.0.0.1:8188 python app.py
```

Windows PowerShell 示例：

```powershell
$env:COMFY_URL="http://127.0.0.1:8188"
python app.py
```

### 3. 启动网站

```bash
python app.py
```

等价命令：

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

部署到公司网络后，设计人员连接公司网络即可访问：

```text
http://192.168.0.186/
```

本机开发或服务器本机调试时，可以访问：

```text
http://localhost:8000/
```

本机看板页面：

```text
http://localhost:8000/dashboard
```

## Docker 运行

项目提供了 `Dockerfile` 和 `docker-compose.yml`。

```bash
docker compose up --build
```

Docker Compose 默认把容器内的 `COMFY_URL` 设置为：

```text
http://host.docker.internal:8188
```

并把运行数据保存到 Docker volume：

```text
storage_data:/app/storage
```

## 环境变量

| 变量名 | 默认值 | 说明 |
| --- | --- | --- |
| `COMFY_URL` | `http://127.0.0.1:8188` | ComfyUI 服务地址 |
| `TARGET_WIDTH` | `1601` | 默认输出目标宽度 |
| `TARGET_HEIGHT` | `2086` | 默认输出目标高度 |
| `GUIDANCE` | `3.5` | 默认 guidance |
| `STEPS` | `20` | 默认生成步数 |
| `STEPS_8` | `8` | 默认 8-step 步数 |
| `SERVER_ID` | 当前主机名 | 服务标识 |
| `SERVER_NAME` | `Server` | 服务显示名 |
| `API_BASE_URL` | `https://147ai.com` | 云端 API 基础地址 |
| `API_CONCURRENCY` | `3` | 云端 API 并发数 |

## 颜色文件格式

颜色文件使用 UTF-8 编码的 TXT。

```text
GARMENT: 长款背心系列-圆领无袖背心收褶皱
COLORS:
Black: #141414
White: #f2f2f2
Pink: #e271a5
```

规则：

- `GARMENT:` 后是商品名称。
- `COLORS:` 后逐行填写颜色。
- 颜色格式为 `颜色名: #六位HEX`。
- 支持中文冒号 `：`。
- HEX 会被转为小写保存。
- 无效长度的 HEX 会被忽略。
- 如果没有识别到任何颜色，会抛出 `No colors found`。

## Web 使用流程

1. 打开 `/` 工作台。
2. 选择目标服务器，默认“自动”会选择负载较低的服务器。
3. 选择商品图文件夹。
4. 选择颜色定义 TXT 文件。
5. 选择改色引擎：ComfyUI 或 Cloud API。
6. 可选填写商品名称、手动颜色、提示词模板和生成参数。
7. 点击“开始改色”。
8. 在任务列表中查看进度。
9. 完成后点击“下载结果”获取 ZIP。

完整设计人员操作说明见 [docs/DESIGNER_USER_GUIDE.md](docs/DESIGNER_USER_GUIDE.md)。

## 任务状态

| 状态 | 含义 |
| --- | --- |
| `queued` | 已提交，等待处理 |
| `running` | 正在处理 |
| `completed` | 全部组合已完成 |
| `failed` | 任务失败 |
| `cancelled` | 用户取消 |
| `cancelling` | 正在取消 |
| `paused` | 服务重启前处于运行状态，重启后标记为暂停 |

任务组合按 `图片数量 × 颜色数量` 计算。每完成一个图片与颜色组合，就会记录到 `completed_combos`，恢复任务时会跳过已完成组合。

## 输出与持久化

运行数据位于 `storage/`：

```text
storage/
├── uploads/   # 用户上传的图片
├── outputs/   # 生成结果
├── jobs/      # 任务 JSON 记录
└── temp/      # 临时颜色文件
```

输出文件保存到：

```text
storage/outputs/<商品编号或任务ID>/
```

文件名格式大致为：

```text
<原图文件名>_<颜色名>_<HEX色号>_<序号>.png
```

任务记录持久化为 JSON，服务启动时会自动读取。若服务关闭时有 `running` 任务，重启后会标记为 `paused`，可以在前端尝试恢复。

## ComfyUI 工作流

默认工作流文件：

```text
image_flux2_working.json
```

后端会在提交到 ComfyUI 前修改关键节点：

| 节点 | 用途 |
| --- | --- |
| `46` | 输入图片 |
| `68:6` | 改色提示词 |
| `68:26` | guidance |
| `68:90` | 8-step steps |
| `68:91` | steps |
| `68:92` | LoRA 开关 |
| `68:93` | 8-step LoRA 开关 |
| `68:94` | 8-step LoRA 值 |
| `45` | 图片缩放 megapixels |
| `68:47` | 目标宽高 |
| `68:72` | 缩放后的图片尺寸来源 |
| `68:48` | 后续节点宽高 |
| `9` | 输出文件名前缀 |

如果替换工作流 JSON，需要确认这些节点 ID 仍然存在，否则任务会失败。

## 提示词与品类判断

`backend/workflow.py` 会根据商品名称推断品类：

- `top`：上衣、T恤、POLO、背心、吊带、文胸、衬衫、卫衣、夹克、外套等。
- `bottom`：裤、短裤、长裤、牛仔裤、半身裙、裙等。
- `dress`：命中 `dress` 时识别为连衣裙类。
- 未命中时默认 `top`。

注意：当前关键词顺序中，中文“裙”会先命中 `bottom`，因此“连衣裙”可能被判断为 `bottom`。如需更精确，可调整 `CATEGORY_KEYWORDS` 的顺序和关键词。

提示词模板支持变量：

```text
{GARMENT}
{GARMENT_CATEGORY}
{RGB_VALUE}
{HEX_VALUE}
```

后端同时兼容小写变量：

```text
{garment}
{category}
{rgb_value}
{hex_value}
```

## 云端 API 配置

Cloud API 模式会读取项目根目录下的 `api.txt`。该文件不应提交到 Git。

格式示例：

```text
gpt-image-2-client
sk-xxxxx
sk-yyyyy

gpt-image-2
sk-zzzzz

gemini-3.1-flash-image-preview
sk-aaaaa
```

规则：

- 模型名独占一行。
- 紧随其后的 `sk-` 开头行会归到该模型。
- 同一模型可以配置多个 key，系统会轮换使用。
- 遇到 429 会临时标记该 key 限流。

## API 概览

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/` | 工作台页面 |
| `GET` | `/dashboard` | 看板页面 |
| `GET` | `/api/defaults` | 默认参数和默认提示词 |
| `POST` | `/api/parse-colors` | 解析颜色 TXT |
| `POST` | `/api/jobs` | 创建改色任务 |
| `GET` | `/api/jobs` | 获取任务列表 |
| `GET` | `/api/jobs/{job_id}` | 获取单个任务 |
| `POST` | `/api/jobs/{job_id}/cancel` | 取消任务 |
| `POST` | `/api/jobs/{job_id}/resume` | 恢复任务 |
| `DELETE` | `/api/jobs/{job_id}` | 删除任务 |
| `POST` | `/api/jobs/batch-delete` | 批量删除任务 |
| `GET` | `/api/jobs/{job_id}/download` | 下载任务结果 ZIP |
| `GET` | `/api/models` | 获取云端模型列表 |
| `GET` | `/api/stats` | 获取看板统计 |
| `GET` | `/api/health` | 健康检查 |
| `GET` | `/api/server-info` | 服务信息 |

## 测试

```bash
pytest
```

测试覆盖内容包括：

- 颜色解析。
- HEX 转 RGB。
- 提示词构建。
- 工作流加载。
- JobStore 基础行为。
- 部分 FastAPI 接口。

## Nginx 负载均衡

`nginx/nginx.conf` 提供了一个双服务器 least connection 配置示例：

```text
server 192.168.0.186:8000;
server 192.168.0.34:8000;
```

前端也内置了这两台服务器的选项，并在“自动”模式下查询 `/api/health`，选择运行中任务数加排队任务数更少的服务器提交。

如需更换服务器地址，需要同步修改：

- `frontend/app.js`
- `frontend/dashboard.js`
- `frontend/index.html`
- `frontend/dashboard.html`
- `nginx/nginx.conf`

## 已知注意事项

- 前端 HTML 文件中的部分中文文案当前存在编码异常迹象，`app.js` 和 `dashboard.js` 中的动态文案是正常中文。若浏览器页面出现乱码，应重新保存 HTML 为 UTF-8 正常中文文本。
- `CLAUDE.md` 也存在编码异常迹象，可作为历史说明参考，但不建议作为正式文档。
- `backend/config.py` 中 `DEFAULT_COLORS_TXT` 指向 `FS03899/FS03899.txt`，当前仓库示例目录是 `FS03920/`，此默认值在 Web 上传流程里通常不会用到。
- 当前任务队列是单进程内存队列。任务记录会落盘，但队列本身不适合多进程共享。
- 云端 API Key 文件 `api.txt` 包含敏感信息，应加入忽略列表并妥善保管。
- 如果修改 ComfyUI 工作流，请同步检查后端写入的节点 ID。

## 维护建议

- 将 `storage/` 视为运行数据目录，定期备份或清理。
- 生产环境建议通过进程管理工具或容器保持服务常驻。
- 大批量任务建议分批提交，避免图片数和颜色数相乘后任务过大。
- 替换模型、工作流或提示词后，先用少量图片和颜色做回归测试。
- 修改前端服务器列表时，确保工作台和看板保持一致。
