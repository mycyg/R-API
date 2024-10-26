# R-API

一个基于Python Flask和Docker的R代码执行服务。用户可以通过HTTP端点提交R代码，服务器将在独立的Docker容器中执行代码，并返回执行结果及生成的文件URL。

## 功能

- 接收用户提交的R代码并执行。
- 在独立的Docker容器中执行代码，确保环境隔离和安全性。
- 返回代码执行的输出结果。
- 提供生成的文件以URL形式下载。
- 快速使用Docker部署。

## 项目结构

```
r-api/
├── app.py
├── requirements.txt
├── Dockerfile
├── Dockerfile.rexecutor
├── output_files/
├── README.md
└── .gitignore
```

## 安装和使用

### 前提条件

- [Docker](https://www.docker.com/get-started) 已安装并运行。
- [Python 3.9](https://www.python.org/downloads/) 及以上版本。
- [Git](https://git-scm.com/downloads) 已安装。

### 克隆仓库

```bash
git clone https://github.com/mycyg1994/r-api.git
cd r-api
```

### 构建R执行器镜像

```bash
docker build -t my-r-executor:latest -f Dockerfile.rexecutor .
```

### 构建Flask应用镜像

```bash
docker build -t python-r-flask-app .
```

### 运行Flask应用容器

**注意**：此操作需要将主机的Docker socket挂载到容器内，存在安全风险。请确保在受信任的环境中使用。

```bash
docker run -d -p 8000:8000 \
    --name python-r-flask-app \
    -v /var/run/docker.sock:/var/run/docker.sock \
    python-r-flask-app
```

### 测试API

使用 `curl` 提交R代码：

```bash
curl -X POST \
     -H "Content-Type: text/plain" \
     --data 'png(filename="plot.png"); plot(cars); dev.off(); print("绘图完成")' \
     http://localhost:8000/execute
```

**预期响应**：

```json
{
  "output": "[1] \"绘图完成\"\n",
  "files": ["http://localhost:8000/files/<exec_id>/plot.png"]
}
```

然后，访问返回的文件URL即可下载生成的图片。

## 安全注意事项

- **代码执行风险**：执行用户提交的任意代码存在潜在风险。建议在受控和隔离的环境中运行，并仅允许可信用户访问。
- **Docker Socket暴露风险**：将主机的Docker socket挂载到容器内允许容器内的应用完全控制主机的Docker daemon。这是一种高风险操作。请确保在受信任的环境中使用，或考虑使用更安全的隔离方法（如Docker-in-Docker）。
- **资源限制**：合理设置Docker容器的资源限制，防止滥用。
- **网络隔离**：通过禁用容器内的网络访问，进一步限制潜在的恶意活动。
- **代码安全检查**：加强代码的安全检查，防止执行危险函数或操作。

## 贡献

欢迎贡献！请提交Pull Request或创建Issue以讨论改进建议。

## 许可证

本项目采用MIT许可证。详情请参见 [LICENSE](LICENSE) 文件。

```

