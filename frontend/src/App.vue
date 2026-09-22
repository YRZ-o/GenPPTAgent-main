<!-- 目录: ./frontend/src/App.vue -->
<template>
  <div class="h-screen flex flex-col bg-gray-50 font-sans overflow-hidden">
    <header class="bg-white shadow-sm px-6 py-4 flex justify-between items-center border-b flex-shrink-0">
      <h1 class="text-xl font-bold text-gray-800 flex items-center">
        <el-icon class="mr-2 text-blue-500"><Monitor /></el-icon> PPT Agent 智能助手
      </h1>
      <div class="text-sm text-gray-500">
        Session: <span class="font-mono text-blue-600">{{ sessionId.slice(0, 8) }}</span>
      </div>
    </header>

    <main class="flex-1 flex overflow-hidden">
      <!-- 左侧：严格限制宽度 50% -->
      <div class="w-1/2 h-full border-r border-gray-200 bg-white flex flex-col overflow-hidden">
        <ChatPanel />
      </div>

      <!-- 右侧：严格限制宽度 50% -->
      <div class="w-1/2 h-full bg-gray-50 flex flex-col overflow-hidden">
        <PreviewPanel />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, provide } from 'vue'
import { Monitor } from '@element-plus/icons-vue'
import ChatPanel from './components/ChatPanel.vue'
import PreviewPanel from './components/PreviewPanel.vue'

// crypto.randomUUID 仅在安全上下文（localhost/https）可用，用 IP 访问时需要兜底
const genId = () =>
  (typeof crypto !== 'undefined' && crypto.randomUUID)
    ? crypto.randomUUID()
    : 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
        const r = (Math.random() * 16) | 0
        return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16)
      })

const sessionId = ref(genId())
provide('sessionId', sessionId)

const isPptReady = ref(false)
provide('isPptReady', isPptReady)
</script>