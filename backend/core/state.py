# 目录: ./backend/core/state.py
from typing import TypedDict, List, Dict, Any, Optional, Annotated
from langgraph.graph.message import add_messages

class SlideState(TypedDict):
    page_number: int
    layout_name: str
    title: str
    content_bullets: List[str]
    chart_data: Optional[Dict[str, Any]]
    notes: str

class PPTStructure(TypedDict):
    theme: str
    total_pages: int
    slides: List[SlideState]

class ProgressInfo(TypedDict):
    current_step: str
    step_index: int
    total_steps: int
    percentage: int
    message: str
    sub_progress: Optional[int]

class AgentState(TypedDict):
    # 使用 list 和 add_messages，让 LangChain 自动管理消息对象
    messages: Annotated[list, add_messages]
    ppt_structure: PPTStructure
    stage: str
    output_path: str
    uploaded_files: List[str]
    progress: ProgressInfo
    ws: Any
    session_id: str
