<!-- 目录: ./frontend/src/components/ChatPanel.vue -->
<template>
  <div class="flex flex-col h-full w-full bg-white">
    <!-- 进度条区域 -->
    <div class="flex-shrink-0 p-4 border-b border-gray-100">
      <ProgressBar :progress="currentProgress" :is-visible="isGenerating" />
    </div>

    <!-- 消息列表区域 -->
    <div ref="chatBox" class="flex-1 overflow-y-auto p-6 space-y-4">
      <div v-for="(msg, index) in messages" :key="index"
           :class="['flex', msg.role === 'user' ? 'justify-end' : 'justify-start']">
        <div :class="[
          'px-4 py-2 rounded-lg shadow-sm text-sm',
          msg.kind ? 'max-w-[92%] min-w-[260px]' : 'max-w-[80%] whitespace-pre-wrap',
          msg.role === 'user' ? 'bg-blue-600 text-white rounded-tr-none' : 'bg-gray-100 text-gray-800 rounded-tl-none'
        ]">
          <div v-if="msg.files && msg.files.length" class="mb-2 flex flex-wrap gap-1">
            <el-tag v-for="f in msg.files" :key="f" size="small" type="info"
                    class="!bg-white/20 !text-white !border-white/30">
              📎 {{ f.name }}
            </el-tag>
          </div>

          <!-- 普通文本消息 -->
          <template v-if="!msg.kind">{{ msg.content }}</template>

          <!-- 🔍 需求分析结果 -->
          <div v-else-if="msg.kind === 'analysis'" class="whitespace-pre-wrap">
            <div class="font-semibold mb-1 flex items-center gap-1">
              <el-icon class="text-blue-500"><Search /></el-icon> {{ msg.title || '需求分析' }}
            </div>
            <div class="text-gray-700 leading-relaxed">{{ msg.content }}</div>
          </div>

          <!-- 📋 大纲 -->
          <div v-else-if="msg.kind === 'outline'">
            <div class="font-semibold mb-1 flex items-center justify-between">
              <span class="flex items-center gap-1">
                <el-icon class="text-blue-500"><List /></el-icon> 大纲预览（{{ msg.slides.length }} 页）
              </span>
              <el-tag size="small" type="danger" effect="plain">{{ msg.theme }}</el-tag>
            </div>
            <div class="border-t border-gray-200 pt-1">
              <div v-for="s in msg.slides" :key="s.page_number" class="flex gap-2 text-sm py-0.5">
                <span class="text-blue-600 font-mono w-5 shrink-0 text-right">{{ s.page_number }}</span>
                <span class="text-gray-700">{{ s.title }}</span>
              </div>
            </div>
          </div>

          <!-- ✍️ 每页将写入的内容 -->
          <div v-else-if="msg.kind === 'draft'">
            <div class="font-semibold mb-1 flex items-center gap-1">
              <el-icon class="text-emerald-600"><EditPen /></el-icon>
              第 {{ msg.page_number }} 页｜{{ msg.title }}
            </div>
            <ul class="list-disc pl-4 space-y-0.5 text-gray-700">
              <li v-for="(b, i) in msg.bullets" :key="i">{{ b }}</li>
            </ul>
            <div v-if="msg.chart && msg.chart.labels" class="mt-1.5 text-xs text-indigo-600">
              📊 图表 {{ msg.chart.type }}｜{{ (msg.chart.labels || []).join('、') }}
              ｜{{ (msg.chart.data || []).join(' / ') }}
            </div>
            <div v-if="msg.notes" class="mt-2 text-xs text-gray-500 bg-white/70 rounded p-2 border border-gray-200">
              🎤 演讲备注：{{ msg.notes }}
            </div>
          </div>

          <!-- 🎨 版式分配 -->
          <div v-else-if="msg.kind === 'layout'">
            <div class="font-semibold mb-1 flex items-center gap-1">
              <el-icon class="text-orange-500"><Grid /></el-icon> 版式分配
            </div>
            <div v-for="row in msg.rows" :key="row.page_number"
                 class="flex gap-2 text-sm py-0.5 border-b border-gray-200/70 last:border-0">
              <span class="w-8 shrink-0 text-gray-400 font-mono">P{{ row.page_number }}</span>
              <span class="flex-1 text-gray-700 truncate">{{ row.title }}</span>
              <span class="shrink-0 text-blue-600">{{ row.layout_name }}</span>
            </div>
          </div>

          <!-- 🧩 模板套用信息 -->
          <div v-else-if="msg.kind === 'template'" class="flex items-center gap-2 flex-wrap">
            <el-icon class="text-pink-500"><Files /></el-icon>
            <span>已套用模板 <b>{{ msg.template }}</b></span>
            <el-tag v-for="r in msg.reused" :key="r" size="small" type="success" effect="plain">{{ r }}</el-tag>
            <span class="text-xs text-gray-500">
              正文 {{ msg.content_pages }} 页 · 共 {{ msg.total_pages }} 页
            </span>
          </div>
        </div>
      </div>

      <!-- 加载状态 -->
      <div v-if="isThinking" class="flex justify-start">
        <div class="bg-gray-100 px-4 py-2 rounded-lg text-sm text-gray-500 flex items-center">
          <el-icon class="animate-spin mr-2"><Loading /></el-icon> {{ statusMsg }}
        </div>
      </div>
    </div>

    <!-- 底部输入区域 -->
    <div class="flex-shrink-0 p-4 border-t border-gray-200 bg-gray-50">
      <div v-if="selectedFiles.length" class="mb-2 flex flex-wrap gap-2">
        <el-tag v-for="(file, idx) in selectedFiles" :key="idx" closable @close="removeFile(idx)">
          📎 {{ file.name }}
        </el-tag>
      </div>
      <div class="flex gap-2">
        <el-upload :auto-upload="false" :show-file-list="false" :on-change="handleFileChange" multiple
                   accept=".pdf,.docx,.xlsx,.txt,.png,.jpg">
          <el-button :icon="Paperclip" circle />
        </el-upload>
        <el-input v-model="inputText" placeholder="描述你的 PPT 需求..."
                  @keyup.enter="sendMessage" :disabled="isThinking">
          <template #prefix>
            <el-icon v-if="isThinking"><Loading /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" @click="sendMessage" :loading="isThinking" :icon="Promotion">
          发送
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, inject, nextTick, onMounted, onUnmounted } from 'vue'
import { Loading, Paperclip, Promotion, Search, List, EditPen, Grid, Files } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import ProgressBar from './ProgressBar.vue'

const sessionId = inject('sessionId')
const isPptReady = inject('isPptReady')

const messages = ref([{ role: 'assistant', content: '你好！请告诉我你想做什么 PPT，或直接上传素材。' }])
const inputText = ref('')
const selectedFiles = ref([])
const uploadedFileIds = ref([])
const isThinking = ref(false)
const isGenerating = ref(false)
const statusMsg = ref('')
const currentProgress = ref({ percentage: 0, message: '', step_index: 0, total_steps: 6, current_step: '', sub_progress: null })
const chatBox = ref(null)
let ws = null

const handleFileChange = async (uploadFile) => {
  selectedFiles.value.push(uploadFile.raw)
  const formData = new FormData()
  formData.append('file', uploadFile.raw)
  try {
    const res = await axios.post('/api/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
    uploadedFileIds.value.push(res.data.file_id)
  } catch (e) {
    ElMessage.error('文件上传失败')
    removeFile(selectedFiles.value.length - 1)
  }
}

const removeFile = (index) => {
  selectedFiles.value.splice(index, 1)
  uploadedFileIds.value.splice(index, 1)
}

const sendMessage = () => {
  if (!inputText.value.trim() && selectedFiles.value.length === 0) return
  if (!ws || ws.readyState !== WebSocket.OPEN) return

  messages.value.push({ role: 'user', content: inputText.value, files: selectedFiles.value.map(f => ({ name: f.name })) })
  ws.send(JSON.stringify({ content: inputText.value, file_ids: uploadedFileIds.value }))

  inputText.value = ''
  selectedFiles.value = []
  uploadedFileIds.value = []
  isThinking.value = true
  isGenerating.value = true
  currentProgress.value.percentage = 10
  currentProgress.value.message = 'Agent 正在分析您的需求...'
  currentProgress.value.step_index = 1
  scrollToBottom()
}

const initWebSocket = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.host}/ws/${sessionId.value}`
  ws = new WebSocket(wsUrl)

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    if (data.type === 'progress') {
      currentProgress.value = data.data
      scheduleScroll()
    } else if (data.type === 'result') {
      messages.value.push({ role: 'assistant', content: data.text })
      isThinking.value = false
      isGenerating.value = false
      isPptReady.value = data.file_ready
      if (data.file_ready) {
        currentProgress.value.percentage = 100
        currentProgress.value.current_step = '完成'
      }
      scheduleScroll()
    } else if (data.type === 'analysis') {
      messages.value.push({
        role: 'assistant', kind: 'analysis',
        title: data.data.title, content: data.data.content
      })
      scheduleScroll()
    } else if (data.type === 'outline') {
      messages.value.push({
        role: 'assistant', kind: 'outline',
        theme: data.data.theme, slides: data.data.slides
      })
      scheduleScroll()
    } else if (data.type === 'draft') {
      messages.value.push({
        role: 'assistant', kind: 'draft',
        page_number: data.data.page_number, title: data.data.title,
        bullets: data.data.bullets, notes: data.data.notes, chart: data.data.chart
      })
      scheduleScroll()
    } else if (data.type === 'layout') {
      // 版式分配逐页推送，聚合成一张卡片
      const row = data.data
      const last = messages.value[messages.value.length - 1]
      if (last && last.kind === 'layout') last.rows.push(row)
      else messages.value.push({ role: 'assistant', kind: 'layout', rows: [row] })
      scheduleScroll()
    } else if (data.type === 'template') {
      messages.value.push({
        role: 'assistant', kind: 'template',
        template: data.data.template, reused: data.data.reused,
        content_pages: data.data.content_pages, total_pages: data.data.total_pages
      })
      scheduleScroll()
    }
  }
  ws.onclose = () => ElMessage.warning('连接断开，请刷新页面')
}

const scrollToBottom = () => {
  nextTick(() => { if (chatBox.value) chatBox.value.scrollTop = chatBox.value.scrollHeight })
}

// 防抖：进度/内容事件高频到达时避免每条都触发一次 DOM 滚动计算
let scrollTimer = null
const scheduleScroll = () => {
  if (scrollTimer) return
  scrollTimer = setTimeout(() => { scrollTimer = null; scrollToBottom() }, 150)
}

onMounted(initWebSocket)
onUnmounted(() => ws?.close())
</script>