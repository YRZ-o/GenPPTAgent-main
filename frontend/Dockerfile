# 目录: ./frontend/Dockerfile | 模块: 前端容器 | 职责: 多阶段构建——第一阶段用 Node 编译 Vue，第二阶段用 Nginx 部署静态文件并反向代理后端
# ==================== 阶段 1: 构建 ====================
FROM node:20-alpine AS builder

WORKDIR /app

# 安装依赖（利用 Docker 缓存）
COPY package.json package-lock.json* ./
RUN npm install

# 复制源码并构建
COPY . .

# 构建参数：注入 WebSocket 地址
ARG VITE_WS_URL=ws://localhost:8000
ENV VITE_WS_URL=${VITE_WS_URL}

RUN npm run build

# ==================== 阶段 2: 部署 ====================
FROM nginx:1.27-alpine

# 删除默认配置
RUN rm /etc/nginx/conf.d/default.conf

# 复制自定义 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 从构建阶段复制产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 暴露端口
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]