<!-- 目录: ./frontend/src/components/ProgressBar.vue | 模块: 进度条组件 | 职责: 显示实时生成进度 -->
<template>
  <div class="progress-container" v-if="isVisible">
    <!-- 步骤指示器 -->
    <div class="steps-indicator">
      <div
        v-for="(step, index) in steps"
        :key="index"
        :class="['step-item', getStepClass(index)]"
      >
        <div class="step-icon">
          <el-icon v-if="isStepCompleted(index)"><Check /></el-icon>
          <el-icon v-else-if="isStepActive(index)"><Loading /></el-icon>
          <span v-else>{{ index + 1 }}</span>
        </div>
        <div class="step-label">{{ step.name }}</div>
        <div class="step-line" v-if="index < steps.length - 1"></div>
      </div>
    </div>

    <!-- 进度条 -->
    <div class="progress-bar-wrapper">
      <el-progress
        :percentage="progressData.percentage"
        :stroke-width="8"
        :show-text="false"
        :color="progressColor"
      />
    </div>

    <!-- 进度消息 -->
    <div class="progress-message">
      <el-icon class="animate-pulse" v-if="!isCompleted"><Loading /></el-icon>
      <!-- 核心修复：使用 CircleCheck 替代不存在的 Success -->
      <el-icon v-else><CircleCheck /></el-icon>
      <span>{{ progressData.message || '准备中...' }}</span>
    </div>

    <!-- 详细进度（子进度） -->
    <div v-if="progressData.sub_progress !== null && !isCompleted" class="sub-progress">
      <span class="text-xs text-gray-500">
        当前步骤进度: {{ progressData.sub_progress }}%
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
// 核心修复：导入 CircleCheck
import { Check, Loading, CircleCheck } from '@element-plus/icons-vue'

const props = defineProps({
  progress: {
    type: Object,
    default: () => ({
      current_step: '',
      step_index: 0,
      total_steps: 0,
      percentage: 0,
      message: '',
      sub_progress: null
    })
  },
  isVisible: {
    type: Boolean,
    default: true
  }
})

const steps = [
  { name: '初始化', key: 'INIT' },
  { name: '需求分析', key: 'CLARIFY' },
  { name: '生成大纲', key: 'OUTLINE' },
  { name: '撰写内容', key: 'DRAFT' },
  { name: '渲染PPT', key: 'RENDER' },
  { name: '完成', key: 'DONE' }
]

const progressData = computed(() => props.progress || {})
const isCompleted = computed(() => props.progress?.percentage === 100)

const progressColor = computed(() => {
  if (isCompleted.value) return '#67c23a'
  if (props.progress?.percentage < 30) return '#409eff'
  if (props.progress?.percentage < 70) return '#e6a23c'
  return '#f56c6c'
})

const getStepClass = (index) => {
  if (index < props.progress?.step_index) return 'completed'
  if (index === props.progress?.step_index) return 'active'
  return 'pending'
}

const isStepCompleted = (index) => index < props.progress?.step_index
const isStepActive = (index) => index === props.progress?.step_index
</script>

<style scoped>
.progress-container {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  margin-bottom: 20px;
}
.steps-indicator {
  display: flex;
  justify-content: space-between;
  margin-bottom: 24px;
  position: relative;
}
.step-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  position: relative;
  z-index: 1;
}
.step-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  margin-bottom: 8px;
  transition: all 0.3s;
}
.step-item.completed .step-icon { background: #67c23a; color: white; }
.step-item.active .step-icon { background: #409eff; color: white; animation: pulse 1.5s infinite; }
.step-item.pending .step-icon { background: #f5f7fa; color: #909399; border: 2px solid #e4e7ed; }
.step-label { font-size: 12px; color: #606266; text-align: center; }
.step-item.active .step-label { color: #409eff; font-weight: 600; }
.step-item.completed .step-label { color: #67c23a; }
.step-line {
  position: absolute;
  top: 18px;
  left: 50%;
  width: 100%;
  height: 2px;
  background: #e4e7ed;
  z-index: -1;
}
.step-item.completed .step-line { background: #67c23a; }
.progress-bar-wrapper { margin: 20px 0; }
.progress-message {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #606266;
  font-size: 14px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
}
.sub-progress { text-align: center; margin-top: 8px; }

@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.1); opacity: 0.8; }
}
</style>