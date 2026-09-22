# 目录: ./backend/agents/planner.py
from core.state import AgentState
from utils.progress import update_progress, log_step, push_event


async def plan_with_progress(state: AgentState) -> dict:
    await update_progress(state, "RENDER", "正在为每一页智能分配排版布局...")
    slides = state["ppt_structure"]["slides"]
    total = len(slides)

    new_slides = slides.copy()
    for idx, slide in enumerate(new_slides):
        page_num = slide["page_number"]
        bullets = slide.get("content_bullets", [])
        has_chart = slide.get("chart_data") is not None

        # 版式名必须与 templates/master.pptx 中的实际版式名一致（中文），
        # 否则 python-pptx 匹配不到会全部 fallback 到第 0 个版式（标题幻灯片）
        if page_num == 1:
            layout = "标题幻灯片"
        elif page_num == total:
            layout = "仅标题"
        elif has_chart:
            layout = "标题和内容"
        elif len(bullets) > 5:
            layout = "两栏内容"
        elif len(bullets) <= 2 and all(len(b) < 20 for b in bullets):
            layout = "仅标题"
        else:
            layout = "标题和内容"

        slide["layout_name"] = layout
        sub_progress = int(((idx + 1) / total) * 30)
        await update_progress(state, "RENDER", f"第 {page_num} 页分配版式: {layout}", sub_progress=sub_progress)

        # 版式分配结果推给前端展示
        await push_event(state, "layout", {
            "page_number": page_num,
            "title": slide.get("title", ""),
            "layout_name": layout,
            "has_chart": has_chart,
            "bullet_count": len(bullets),
        })

    new_ppt_structure = {**state["ppt_structure"], "slides": new_slides}
    return {
        "ppt_structure": new_ppt_structure,
        "stage": "RENDER"
    }