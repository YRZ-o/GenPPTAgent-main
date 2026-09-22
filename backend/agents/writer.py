# 目录: ./backend/agents/writer.py
import json, re
from langchain_core.messages import HumanMessage  # 新增导入
from core.state import AgentState
from core.llm import create_llm
from utils.progress import update_progress, log_step, push_event

llm = create_llm(temperature=0.5)


def extract_json_array(text: str) -> list:
    text = re.sub(r'^```json\s*', '', text, flags=re.MULTILINE).strip()
    text = re.sub(r'\s*```$', '', text, flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except:
        start, end = text.find('['), text.rfind(']')
        return json.loads(text[start:end + 1]) if start != -1 and end != -1 else []


async def write_with_progress(state: AgentState) -> dict:
    await update_progress(state, "DRAFT", "开始撰写 PPT 内容...")
    slides = state["ppt_structure"]["slides"]

    prompt_text = f"""为以下大纲扩写详细内容。
    大纲：{json.dumps(slides, ensure_ascii=False)}
    要求：1.每页 3-5 条 bullet，每条<30字。2.生成 100 字左右的口语化 notes。3.若有数据，生成 chart_data (含 type, labels, data)，否则为 null。
    严格输出 JSON 数组，无 Markdown 标记。"""

    # 核心修复：使用 [HumanMessage(content=...)] 包装字符串
    response = await llm.ainvoke([HumanMessage(content=prompt_text)])

    detailed_slides = extract_json_array(response.content)

    new_slides = state["ppt_structure"]["slides"].copy()
    for i, slide in enumerate(new_slides):
        if i < len(detailed_slides):
            slide.update(detailed_slides[i])

        sub_progress = int(((i + 1) / len(new_slides)) * 100)
        await update_progress(state, "DRAFT", f"已完成第 {i + 1}/{len(new_slides)} 页：{slide.get('title')}",
                              sub_progress=sub_progress)

        # 把这一页将写入 PPT 的实际内容推给前端展示
        await push_event(state, "draft", {
            "page_number": slide.get("page_number", i + 1),
            "title": slide.get("title", ""),
            "bullets": slide.get("content_bullets", []) or [],
            "notes": slide.get("notes", "") or "",
            "chart": slide.get("chart_data"),
        })

    new_ppt_structure = {**state["ppt_structure"], "slides": new_slides}
    progress_update = await update_progress(state, "DRAFT", "内容撰写全部完成", sub_progress=100)

    return {
        "ppt_structure": new_ppt_structure,
        "stage": "DRAFT",
        **progress_update
    }
