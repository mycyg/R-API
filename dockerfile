# 使用官方Python 3.9精简版镜像
FROM python:3.9-slim

# 安装Docker客户端和系统依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 设置工作目录
WORKDIR /app

# 复制应用代码
COPY app.py /app/app.py

# 创建输出文件目录
RUN mkdir /app/output_files

# 暴露端口
EXPOSE 8000

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 启动Flask应用
CMD ["python", "app.py"]
