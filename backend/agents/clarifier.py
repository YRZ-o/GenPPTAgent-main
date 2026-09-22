# 目录: ./backend/agents/clarifier.py
from langchain_core.messages import HumanMessage  # 新增导入
from core.state import AgentState
from core.llm import create_llm
from utils.progress import update_progress, log_step, push_event

llm = create_llm(temperature=0)


async def clarify_with_progress(state: AgentState) -> dict:
    progress_update = await update_progress(state, "CLARIFY", "正在分析用户需求...")
    log_step("CLARIFY", "开始需求分析")

    last_msg = state["messages"][-1]
    user_input = last_msg.content if hasattr(last_msg, 'content') else str(last_msg.get("content", ""))

    # 将 prompt 定义为纯文本
    prompt_text = f"""你是一个 PPT 需求分析师。用户输入："{user_input}"。
先输出简要分析，每项一行（没有的信息写"未提供"）：
主题：...
目标受众：...
期望页数：...
风格倾向：...
素材情况：...
最后一行给出结论：
- 如果信息严重不足，该行必须包含"需要更多信息"或"请问"，并列出追问；
- 如果信息足够，该行必须是"信息充足，可以开始规划大纲"。"""

    # 核心修复：使用 [HumanMessage(content=...)] 包装字符串
    response = await llm.ainvoke([HumanMessage(content=prompt_text)])

    # 把分析结论推给前端展示
    await push_event(state, "analysis", {
        "title": "需求分析",
        "content": response.content,
        "user_input": user_input,
    })

    new_stage = "OUTLINE" if "信息充足" in response.content else "CLARIFY"

    return {
        "messages": [{"role": "assistant", "content": response.content}],
        "stage": new_stage,
        **progress_update
    }
