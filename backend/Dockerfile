FROM python:3.12-slim

WORKDIR /app

# 配置pip使用国内镜像源（加速下载）
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip config set install.trusted-host pypi.tuna.tsinghua.edu.cn

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    dos2unix \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖（使用缓存加速）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 转换启动脚本格式并添加执行权限
RUN dos2unix start.sh && chmod +x start.sh

# 暴露端口
EXPOSE 8000

# 默认启动命令
CMD ["./start.sh"]
