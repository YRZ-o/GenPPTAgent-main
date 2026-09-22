// 目录: ./frontend/src/main.js | 模块: 应用入口 | 职责: 初始化 Vue 应用，注册 Element Plus 和全局样式
import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import './style.css'

const app = createApp(App)
app.use(ElementPlus)
app.mount('#app')