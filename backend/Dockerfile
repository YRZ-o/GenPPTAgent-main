# 目录: ./backend/Dockerfile | 模块: 后端容器 | 职责: 构建包含 Python + LibreOffice 的后端镜像
FROM python:3.11-slim-bookworm

# ===== 系统依赖 (已优化：使用阿里云镜像源解决网络超时，精简字体包避免冲突) =====
RUN echo "deb http://mirrors.aliyun.com/debian/ bookworm main contrib non-free non-free-firmware" > /etc/apt/sources.list && \
    echo "deb http://mirrors.aliyun.com/debian/ bookworm-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
    echo "deb http://mirrors.aliyun.com/debian-security bookworm-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
    apt-get update && apt-get install -y --no-install-recommends \
    libreoffice-impress \
    libreoffice-common \
    fonts-noto-cjk \
    fonts-wqy-microhei \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ===== 工作目录 =====
WORKDIR /app

# ===== Python 依赖 =====
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# ===== 应用代码 =====
COPY . .

# ===== 创建运行时目录 =====
RUN mkdir -p /app/output /app/uploads /app/templates

# ===== 暴露端口 =====
EXPOSE 8000

# ===== 启动命令 =====
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]