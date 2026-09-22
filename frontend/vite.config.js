// 目录: ./frontend/vite.config.js | 模块: 构建配置 | 职责: 配置 Vite 代理，解决前后端跨域问题
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      },
      // 后端路由本身就是 /ws/{session_id}，不能再 strip 掉 /ws 前缀
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true
      }
    }
  }
})