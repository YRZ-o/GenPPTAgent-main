# 目录: ./tests/render_local.py | 模块: 渲染单测 | 职责: 不走 LLM，直接调用渲染器，验证模板复用与页序是否正确
import asyncio
import glob
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))
os.chdir(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

from tools.ppt_renderer import render_with_progress  # noqa: E402


def page(n, title, bullets, notes="备注内容", layout="标题和内容"):
    return {
        "page_number": n,
        "title": title,
        "content_bullets": bullets,
        "chart_data": None,
        "notes": notes,
        "layout_name": layout,
    }


outline = [
    page(1, "新能源汽车行业分析", ["封面", "公司logo", "报告标题：新能源汽车行业分析"], layout="标题幻灯片"),
    page(2, "行业背景", ["定义：纯电动、插电混动", "发展历程", "政策环境"]),
    page(3, "市场规模", ["全球销量超1000万辆", "中国销量超600万辆", "渗透率快速提升"]),
    page(4, "竞争格局", ["特斯拉、比亚迪领先", "国内外激烈竞争", "集中度提升"]),
    page(5, "技术趋势", ["电池能量密度提升", "成本下降", "智能化加速"]),
    page(6, "投资机会与风险", ["产业链上下游机会", "政策与技术风险", "建议分散投资"]),
    page(7, "产业链分析", ["上游矿产资源", "中游电池制造", "下游整车销售"]),
    page(8, "消费者洞察", ["购车决策因素", "续航与充电焦虑", "品牌认知变化"]),
    page(9, "未来展望", ["渗透率将持续提升", "出口成为新增长点", "能源生态融合发展"]),
    page(10, "致谢", ["感谢聆听", "欢迎交流"]),
]

state = {
    "ppt_structure": {"theme": "商务", "slides": outline, "total_pages": len(outline)},
    "session_id": "localtest",
    "ws": None,
}

result = asyncio.run(render_with_progress(state))
print("output:", result["output_path"])
