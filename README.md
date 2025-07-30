# fastapi-template

> 基于FastAPI的封装模板，支持流式与非流式响应，适配多环境配置，适合构建高性能 AI 推理服务。

---

## 🚀 项目特性

- 🌐 基于 FastAPI，支持异步高并发请求
- ⚡ 依赖管理使用 [uv](https://github.com/astral-sh/uv)，安装快、体积小
- 🐳 支持 Docker 构建部署，可选开启 BuildKit 提高构建效率
- 🔐 提供简单的 Bearer Token 鉴权机制，可扩展后端代理实现权限控制
- ⚙️ 支持多环境配置（dev/prod），方便开发/部署环境切换
- 🔁 内置 流式（SSE） 与 非流式 接口示例，适配大模型对话需求
- 📦 支持标准 `pyproject.toml`，构建统一规范

---

## 📂 项目目录结构

```ini
.
├── config/                 # 配置文件目录
│   ├── loader.py
│   ├── config.dev.yml
│   └── config.prod.yml
│
├── controller/             # 路由控制器
│   └── app_controller.py
│
├── service/                # 核心业务逻辑
│   └── app_service.py
│
├── utils/                  # 通用工具
│   ├── exception.py
│   ├── log.py
│   ├── logging.py
│   ├── request.py
│   └── response.py
│
├── server.py               # FastAPI 应用入口
├── deploy.sh               # Docker构建运行脚本
├── Dockerfile              # Docker构建配置
├── pyproject.toml          # 项目依赖定义
└── README.md
```

---

## ⚙️ 配置文件说明

配置文件位于 `config/` 目录，格式为 YAML，根据环境变量 `ENV=dev|prod` 自动加载对应配置。

示例字段说明：

```yaml
app:
  host: 0.0.0.0
  port: 18000
  workers: 1
  reload: true

llm:
  base_url: <上游模型API地址>
  model: <默认模型名称>
  api_key: <API密钥>
  timeout_seconds: 60

auth:
  enabled: true
  keys:
    - <允许访问的API密钥>

logging:
  level: INFO
  console: true
  file: true
  file_path: logs/app.log
```

---

## 🧪 本地启动方式

```bash
# 安装 uv
$ pipx install uv

# 同步依赖
$ uv sync

# 启动服务
$ uv run uvicorn server:app --host 0.0.0.0 --port 18000 --workers 1
```

---

## 🐳 Docker部署方式

使用 `deploy.sh` 一键构建并运行容器：

```bash
$ bash deploy.sh
```

你可以在脚本中修改以下变量：

- `ENV_NAME`：环境名，匹配配置文件 `config/config.${ENV_NAME}.yml`
- `IMAGE` / `TAG` / `CONTAINER`：镜像名、标签与容器名
- `HOST_PORT` / `APP_PORT`：宿主机与容器端口映射
- `USE_BUILDKIT`：是否启用 BuildKit 加速构建

**注：BuildKit 构建加速（推荐开启）**

BuildKit 能显著加速镜像构建，特别适合 CI/CD 场景。

启用方式：

```bash
$ export DOCKER_BUILDKIT=1
```

若系统未安装 BuildKit，可参考以下步骤：

1. 下载插件：

| 系统             | 下载地址 |
| ---------------- | -------- |
| macOS (M1/ARM64) | https://github.com/docker/buildx/releases/download/v0.14.0/buildx-v0.14.0.darwin-arm64 |
| Linux (x86_64)   | https://github.com/docker/buildx/releases/download/v0.14.0/buildx-v0.14.0.linux-amd64 |

2. 安装至 CLI 插件目录：

```bash
$ chmod +x docker-buildx
$ sudo mkdir -p /usr/local/lib/docker/cli-plugins
$ sudo mv docker-buildx /usr/local/lib/docker/cli-plugins/
$ docker buildx version
```

---

## 🔌 接口示例

**流式响应**

```bash
$ curl -X POST http://127.0.0.1:18000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-11111111111111111111111111111111" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "你好"
      }
    ],
    "stream": true,
    "temperature": 0.7
  }'
```

**非流式响应**

```bash
$ curl -X POST http://127.0.0.1:18000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-11111111111111111111111111111111" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "你好"
      }
    ],
    "stream": false,
    "temperature": 0.7
  }'
```
