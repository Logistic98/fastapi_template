#!/usr/bin/env bash

set -Eeuo pipefail
IFS=$'\n\t'

### ===== 配置区（按需修改）=====
ENV_NAME="prod"                    # 对应 config/config.$ENV_NAME.yml
IMAGE="fastapi_template_image"     # 镜像名
TAG="latest"                       # 镜像标签
CONTAINER="fastapi_template"       # 容器名
HOST_PORT=18000                    # 宿主机外部端口
APP_PORT=18000                     # 容器内固定端口
RESTART_POLICY="always"            # 容器重启策略：no | on-failure | unless-stopped | always
USE_BUILDKIT=true                  # 是否启用 BuildKit 构建加速
### ============================

CONFIG_FILE="config/config.${ENV_NAME}.yml"
[[ -f "$CONFIG_FILE" ]] || { echo "错误：未找到 ${CONFIG_FILE}"; exit 2; }

FULL_IMAGE="${IMAGE}:${TAG}"

echo "环境: ${ENV_NAME}"
echo "配置: ${CONFIG_FILE}"
echo "镜像: ${FULL_IMAGE}"
echo "容器: ${CONTAINER}"
echo "端口映射: ${HOST_PORT}:${APP_PORT}"
echo "重启策略: ${RESTART_POLICY}"
echo "BuildKit 构建支持: ${USE_BUILDKIT}"

if [[ "${USE_BUILDKIT}" == "true" ]]; then
  if ! docker buildx version >/dev/null 2>&1; then
    echo "错误：你已启用 BuildKit 构建支持，但本机尚未安装 buildx 插件。"
    echo "请前往 https://github.com/docker/buildx/releases 下载并安装。"
    exit 2
  fi
  export DOCKER_BUILDKIT=1
fi

if CID="$(docker ps -aq -f name="^${CONTAINER}$")" && [[ -n "${CID}" ]]; then
  echo "移除旧容器: ${CONTAINER}"
  docker rm -f "${CONTAINER}" >/dev/null
fi

if IID="$(docker images -q "${FULL_IMAGE}")" && [[ -n "${IID}" ]]; then
  echo "移除旧镜像: ${FULL_IMAGE}"
  docker rmi -f "${FULL_IMAGE}" >/dev/null
fi

echo "构建镜像..."
docker build -t "${FULL_IMAGE}" .

echo "运行容器..."
docker run -d \
  --name "${CONTAINER}" \
  -e ENV="${ENV_NAME}" \
  -p "${HOST_PORT}:${APP_PORT}" \
  --restart "${RESTART_POLICY}" \
  "${FULL_IMAGE}"

echo "部署完成，正在查看日志："
docker logs -f "${CONTAINER}"
