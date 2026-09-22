# 目录: ./backend/core/orchestrator.py
from langgraph.graph import StateGraph, END
from core.state import AgentState
from utils.progress import log_step

from agents.clarifier import clarify_with_progress as clarify_node
from agents.outliner import outline_with_progress as outline_node
from agents.writer import write_with_progress as write_node
from agents.planner import plan_with_progress as plan_node
from tools.ppt_renderer import render_with_progress as render_node

def get_msg_content(msg) -> str:
    """辅助函数：安全获取消息内容"""
    return msg.content if hasattr(msg, 'content') else msg.get("content", "")

def route_after_clarify(state: AgentState) -> str:
    messages = state.get("messages", [])
    if not messages: return "continue"
    content = get_msg_content(messages[-1])
    if "需要更多信息" in content or "请问" in content:
        return "wait_for_user"
    return "continue"

def route_after_outline(state: AgentState) -> str:
    messages = state.get("messages", [])
    if not messages: return "revise_outline"
    content = get_msg_content(messages[-1])
    if "确认" in content or "没问题" in content or "可以" in content or "开始" in content:
        return "generate_content"
    return "revise_outline"

def build_agent_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("clarify", clarify_node)
    workflow.add_node("outline", outline_node)
    workflow.add_node("write_content", write_node)
    workflow.add_node("plan_layout", plan_node)
    workflow.add_node("render_ppt", render_node)

    workflow.set_entry_point("clarify")
    workflow.add_conditional_edges("clarify", route_after_clarify, {"wait_for_user": END, "continue": "outline"})
    workflow.add_conditional_edges("outline", route_after_outline, {"revise_outline": "outline", "generate_content": "write_content"})
    workflow.add_edge("write_content", "plan_layout")
    workflow.add_edge("plan_layout", "render_ppt")
    workflow.add_edge("render_ppt", END)

    log_step("INIT", "LangGraph 状态图构建完成")
    return workflow.compile()