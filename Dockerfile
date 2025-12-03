# HKEX Agent - Chainlit Web 界面
# 港股智能分析系统 Docker 镜像

FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv (快速 Python 包管理器)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# 复制依赖文件
COPY pyproject.toml uv.lock ./

# 安装 Python 依赖
RUN uv sync --frozen --no-dev

# 复制项目文件
COPY libs/ ./libs/
COPY src/ ./src/
COPY chainlit/ ./chainlit/
COPY mcp_config.json ./

# 创建数据目录
RUN mkdir -p /app/chainlit_data /app/pdf_cache /app/md

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Chainlit 配置
ENV CHAINLIT_HOST=0.0.0.0
ENV CHAINLIT_PORT=8000

# 暴露端口
EXPOSE 8000

# 设置健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# 启动命令
WORKDIR /app/chainlit
CMD ["uv", "run", "chainlit", "run", "app.py", "--host", "0.0.0.0", "--port", "8000", "--headless"]

