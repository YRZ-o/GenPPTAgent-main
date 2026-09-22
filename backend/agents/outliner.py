# 目录: ./backend/agents/outliner.py
import json, re
from langchain_core.messages import HumanMessage  # 新增导入
from core.state import AgentState
from core.llm import create_llm
from utils.progress import update_progress, log_step, push_event

llm = create_llm(temperature=0.3)


def extract_json(text: str) -> dict:
    text = re.sub(r'^```json\s*', '', text, flags=re.MULTILINE).strip()
    text = re.sub(r'\s*```$', '', text, flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except:
        last = text.rfind('}')
        return json.loads(text[:last + 1]) if last != -1 else {}


def msg_role(msg) -> str:
    """兼容 LangChain 消息对象和原始 dict 两种形态（LangGraph 会把 dict 转成消息对象）。"""
    if isinstance(msg, dict):
        return msg.get("role", "")
    return {"human": "user", "ai": "assistant"}.get(getattr(msg, "type", ""), getattr(msg, "type", ""))


def msg_text(msg) -> str:
    if isinstance(msg, dict):
        return str(msg.get("content", ""))
    return str(getattr(msg, "content", ""))


async def outline_with_progress(state: AgentState) -> dict:
    await update_progress(state, "OUTLINE", "正在分析需求并规划大纲结构...")

    # 取全部用户消息（含后续修改意见），避免多轮对话时大纲丢失最新要求
    user_inputs = [msg_text(m) for m in state["messages"] if msg_role(m) == "user"]
    user_req = "\n".join(user_inputs) or ""

    prompt_text = f"""作为 PPT 策划专家，为以下需求生成大纲。
    需求：{user_req}
    要求：1.第一页封面，最后一页致谢。2.严格输出纯 JSON，无 Markdown 标记。
    3.第一页和最后一页的 content_bullets 写 1~2 句副标题文案（如"2026年度总结""欢迎交流指正"），
    不要写"封面""logo""目录"这类设计说明。其他页每条 bullet 是具体要点。
    格式：{{"theme": "风格", "slides": [{{"page_number": 1, "title": "...", "content_bullets": ["..."]}}]}}"""

    # 核心修复：使用 [HumanMessage(content=...)] 包装字符串
    response = await llm.ainvoke([HumanMessage(content=prompt_text)])

    outline_data = extract_json(response.content)

    ppt_structure = {
        "theme": outline_data.get("theme", "商务简约"),
        "slides": outline_data.get("slides", []),
        "total_pages": len(outline_data.get("slides", []))
    }

    md_outline = "\n".join([f"- 第{s['page_number']}页: {s['title']}" for s in ppt_structure["slides"]])
    reply = f"为您规划了 {ppt_structure['total_pages']} 页 PPT：\n{md_outline}\n\n回复'确认'开始生成详细内容，或提出修改意见。"

    # 把大纲推给前端展示
    await push_event(state, "outline", {
        "theme": ppt_structure["theme"],
        "total_pages": ppt_structure["total_pages"],
        "slides": [
            {"page_number": s.get("page_number", i + 1), "title": s.get("title", "")}
            for i, s in enumerate(ppt_structure["slides"])
        ],
    })

    progress_update = await update_progress(state, "OUTLINE", "大纲生成完毕，等待用户确认", sub_progress=100)

    return {
        "messages": [{"role": "assistant", "content": reply}],
        "ppt_structure": ppt_structure,
        "stage": "OUTLINE",
        **progress_update
    }
