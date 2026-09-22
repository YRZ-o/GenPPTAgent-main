<!-- 目录: ./frontend/src/components/PreviewPanel.vue -->
<template>
  <div class="flex flex-col h-full w-full bg-gray-50">
    <div class="flex-shrink-0 p-4 bg-white border-b flex justify-between items-center">
      <h2 class="text-lg font-semibold text-gray-700">📊 PPT 预览</h2>
      <el-button type="success" :icon="Download" @click="downloadPpt" :disabled="!isPptReady">
        下载 .pptx 源文件
      </el-button>
    </div>

    <div class="flex-1 overflow-y-auto p-6 flex flex-col items-center space-y-4" v-if="isPptReady">
      <div v-if="isLoadingPdf" class="text-gray-500 mt-10">
        <el-icon class="animate-spin mr-2"><Loading /></el-icon> 正在生成预览...
      </div>
      <canvas v-for="page in pdfPages" :key="page" :id="`pdf-canvas-${page}`"
              class="shadow-lg bg-white max-w-full"></canvas>
    </div>

    <div v-else class="flex-1 flex flex-col items-center justify-center text-gray-400">
      <el-icon :size="64" class="mb-4"><Document /></el-icon>
      <p>完成对话后，这里将展示 PPT 预览</p>
    </div>
  </div>
</template>

<script setup>
import { ref, inject, watch, nextTick } from 'vue'
import { Download, Loading, Document } from '@element-plus/icons-vue'
import * as pdfjsLib from 'pdfjs-dist'
import axios from 'axios'

pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js'

const sessionId = inject('sessionId')
const isPptReady = inject('isPptReady')
const isLoadingPdf = ref(false)
const pdfPages = ref([])

watch(isPptReady, async (ready) => {
  if (ready) await loadPdfPreview()
  else pdfPages.value = []
})

const loadPdfPreview = async () => {
  isLoadingPdf.value = true
  try {
    const response = await axios.get(`/preview/${sessionId.value}`, { responseType: 'arraybuffer' })
    const pdf = await pdfjsLib.getDocument({ data: response.data }).promise
    pdfPages.value = Array.from({ length: pdf.numPages }, (_, i) => i + 1)
    for (let i = 1; i <= pdf.numPages; i++) await renderPage(pdf, i)
  } catch (e) { console.error('PDF 预览加载失败:', e) } finally { isLoadingPdf.value = false }
}

const renderPage = async (pdf, pageNum) => {
  await nextTick()
  const canvas = document.getElementById(`pdf-canvas-${pageNum}`)
  if (!canvas) return
  const page = await pdf.getPage(pageNum)
  const viewport = page.getViewport({ scale: 1.5 })
  const ctx = canvas.getContext('2d')
  canvas.height = viewport.height
  canvas.width = viewport.width
  await page.render({ canvasContext: ctx, viewport }).promise
}

const downloadPpt = () => window.open(`/download/${sessionId.value}`, '_blank')
</script>