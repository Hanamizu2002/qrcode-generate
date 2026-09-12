# 二维码生成 API

本服务完全在本机生成二维码，不访问用户提交的 URL，也不会将链接上传到第三方服务。返回的 SVG 或 PNG
使用透明背景，中央二维码模块会被实际删除，并显示解析后内联的 `logo.svg`。

## 启动服务

```bash
.venv/bin/python api_server.py
```

默认监听 `http://127.0.0.1:8000`。可以修改地址和端口：

```bash
.venv/bin/python api_server.py --host 0.0.0.0 --port 8080
```

> `0.0.0.0` 会允许其他设备访问。当前服务没有身份验证，暴露到公网前应由反向代理添加 HTTPS、鉴权、限流和请求大小限制。

### Docker 部署

构建镜像：

```bash
docker build -t qrcode-api .
```

Dockerfile 中 Debian 软件包和 Python 依赖分别使用清华 APT 与 PyPI 镜像下载。`python:3.12-slim-bookworm` 基础镜像仍由 Docker 引擎拉取；如果 Docker Hub 访问较慢，需要在部署主机上单独配置镜像加速器。

启动容器：

```bash
docker run -d --name qrcode-api -p 8000:8000 --restart unless-stopped qrcode-api
```

验证健康状态：

```bash
curl http://127.0.0.1:8000/health
```

### Docker Compose 部署

构建并启动：

```bash
docker compose up -d --build
```

默认对外端口为 `8000`。可以通过环境变量修改：

```bash
QR_PORT=8080 docker compose up -d --build
```

查看运行和健康状态：

```bash
docker compose ps
docker compose logs -f qrcode-api
```

停止服务：

```bash
docker compose down
```

## 通用约定

- 请求与错误响应编码：UTF-8。
- JSON 请求必须使用 `Content-Type: application/json`。
- 单个请求体最大为 16 KiB。
- 二维码使用 H 级纠错，最低版本为 4。
- SVG 和 PNG 均为透明背景，适合放在白色或浅色背景上。
- 服务会将结果栅格化并进行解码验证；无法验证时返回错误，不输出文件。
- 当前不返回 CORS 响应头。浏览器跨域调用时应通过同源反向代理转发。

## `GET /health`

检查服务是否正在运行。

### 请求示例

```bash
curl http://127.0.0.1:8000/health
```

### 成功响应

状态码：`200 OK`

```json
{
  "status": "ok"
}
```

## `POST /generate`

生成 SVG 或 PNG 二维码。成功响应直接返回文件内容，不返回 JSON。

### 请求字段

| 字段           | 类型    | 必填 | 默认值     | 限制与说明                                                           |
|----------------|---------|------|------------|----------------------------------------------------------------------|
| `url`          | string  | 是   | 无         | 完整的 `http://` 或 `https://` URL；不能为空，不能包含空白或控制字符 |
| `format`       | string  | 否   | `svg`      | 可选值为 `svg`、`png`                                                |
| `size`         | integer | 否   | `1024`     | 输出宽度和高度，范围 `256`～`16384` 像素                             |
| `border`       | integer | 否   | `4`        | 二维码静区宽度，范围 `4`～`32` 个模块                                |
| `center_ratio` | number  | 否   | `0.333333` | 中央框占二维码主体宽度的比例；可为 `0`，或 `0.12`～`0.36`            |
| `color`        | string  | 否   | `#000000`  | 二维码、中央边框及 Logo 颜色；必须为六位 `#RRGGBB` 格式              |

当 `center_ratio` 为 `0` 时，不删除中央模块，也不显示中央边框和 Logo。为保证解码，服务可能自动缩小中央比例，实际值见响应头
`X-Center-Ratio`。

过浅的颜色可能无法通过白色背景下的解码验证，服务会返回 `400`。即使自动验证通过，发布或印刷前仍应使用实际手机和最终载体复核。

### 生成 SVG

```bash
curl -X POST http://127.0.0.1:8000/generate \
  -H 'Content-Type: application/json' \
  -d '{
    "url": "https://www.voxisle.art",
    "format": "svg",
    "size": 1024,
    "border": 4,
    "center_ratio": 0.333,
    "color": "#004C97"
  }' \
  --output qrcode.svg
```

### 生成 PNG

```bash
curl -X POST http://127.0.0.1:8000/generate \
  -H 'Content-Type: application/json' \
  -d '{
    "url": "https://www.voxisle.art",
    "format": "png",
    "size": 1024,
    "border": 4,
    "center_ratio": 0.333,
    "color": "#1D1F2A"
  }' \
  --output qrcode.png
```

### 成功响应

状态码：`200 OK`

| 响应头                  | SVG 示例                            | PNG 示例                            | 说明               |
|-------------------------|-------------------------------------|-------------------------------------|--------------------|
| `Content-Type`          | `image/svg+xml; charset=utf-8`      | `image/png`                         | 文件媒体类型       |
| `Content-Disposition`   | `attachment; filename="qrcode.svg"` | `attachment; filename="qrcode.png"` | 建议下载文件名     |
| `Content-Length`        | 具体字节数                          | 具体字节数                          | 响应体长度         |
| `X-QR-Version`          | `4`                                 | `4`                                 | 实际二维码版本     |
| `X-QR-Error-Correction` | `H`                                 | `H`                                 | 纠错等级           |
| `X-Center-Ratio`        | `0.333`                             | `0.333`                             | 实际采用的中央比例 |
| `X-QR-Color`            | `#004C97`                           | `#1D1F2A`                           | 实际二维码颜色     |

响应体是对应的 SVG 文本或 PNG 二进制数据。

## 错误响应

所有错误均返回 JSON：

```json
{
  "error": "具体错误信息"
}
```

| 状态码                       | 场景                                                                                   |
|------------------------------|----------------------------------------------------------------------------------------|
| `400 Bad Request`            | JSON 无效、请求体不是对象、字段类型或范围错误、URL/颜色/格式无效、二维码未通过解码验证 |
| `404 Not Found`              | 请求的接口不存在                                                                       |
| `405 Method Not Allowed`     | 对已知接口使用错误的 HTTP 方法，`Allow` 响应头会列出支持的方法                         |
| `415 Unsupported Media Type` | `/generate` 请求未使用 `application/json`                                              |
| `500 Internal Server Error`  | Python 依赖、Cairo、Logo 文件或本地文件读取异常                                        |

### 参数错误示例

请求：

```bash
curl -X POST http://127.0.0.1:8000/generate \
  -H 'Content-Type: application/json' \
  -d '{"url":"not-a-url"}'
```

响应：

```json
{
  "error": "请输入完整的 http:// 或 https:// 链接。"
}
```

## `OPTIONS`

任意路径的 `OPTIONS` 请求返回 `204 No Content`，并包含：

```http
Allow: GET, POST, OPTIONS
```

此响应用于声明支持的方法，不代表已启用跨域访问。

## 未定义路径

访问未定义路径会返回：

状态码：`404 Not Found`

```json
{
  "error": "接口不存在。"
}
```
