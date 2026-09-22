# 目录: ./backend/utils/progress.py | 模块: 进度管理工具 | 职责: 计算进度并返回更新字典，同时推送给前端
import logging
from typing import Optional
from core.state import AgentState, ProgressInfo

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

STEPS = {
    "INIT": ("初始化", 0),
    "CLARIFY": ("需求分析", 10),
    "OUTLINE": ("生成大纲", 30),
    "DRAFT": ("撰写内容", 50),
    "RENDER": ("渲染PPT", 70),
    "DONE": ("完成", 100)
}


async def update_progress(
        state: AgentState,
        step: str,
        message: str,
        sub_progress: Optional[int] = None
) -> dict:
    """计算进度，推送到前端，并返回需要更新到 State 的字典"""
    step_name, base_percentage = STEPS.get(step, (step, 0))

    if sub_progress is not None:
        keys = list(STEPS.keys())
        next_step = keys[keys.index(step) + 1] if step != "DONE" else "DONE"
        next_percentage = STEPS.get(next_step, (step, 100))[1]
        step_range = next_percentage - base_percentage
        percentage = base_percentage + int((sub_progress / 100) * step_range)
    else:
        percentage = base_percentage

    progress: ProgressInfo = {
        "current_step": step_name,
        "step_index": list(STEPS.keys()).index(step) if step in STEPS else 0,
        "total_steps": len(STEPS),
        "percentage": min(percentage, 100),
        "message": message,
        "sub_progress": sub_progress
    }

    # 推送到前端 (使用 ws)
    ws = state.get("ws")
    if ws:
        try:
            await ws.send_json({"type": "progress", "data": progress})
            logger.info(f"📊 进度更新: {step_name} - {percentage}% - {message}")
        except Exception as e:
            logger.error(f"推送进度失败: {e}")

    # 返回更新字典，供 Node 函数 return
    return {"progress": progress}


def log_step(step: str, message: str, details: str = ""):
    step_name, _ = STEPS.get(step, (step, 0))
    emoji_map = {"INIT": "🚀", "CLARIFY": "🔍", "OUTLINE": "📋", "DRAFT": "✍️", "RENDER": "🎨", "DONE": "✅", "ERROR": "❌"}
    logger.info(f"{emoji_map.get(step, '📌')} [{step_name}] {message} {f'- {details}' if details else ''}")


# 前端展示用的结构化事件类型：analysis / outline / draft / layout / template
async def push_event(state: AgentState, event: str, data: dict):
    """把阶段性的分析结果、大纲、每页内容、版式分配等推送给前端展示"""
    ws = state.get("ws")
    if not ws:
        return
    try:
        await ws.send_json({"type": event, "data": data})
    except Exception as e:
        logger.error(f"推送 {event} 事件失败: {e}")
