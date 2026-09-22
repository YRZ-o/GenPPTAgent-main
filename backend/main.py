# 目录: ./backend/main.py | 模块: 后端服务层 | 职责: WebSocket 入口，正确初始化 LangGraph 状态
import os
import logging

# 本地运行时从项目根目录的 .env 加载配置（agents 模块在 import 时就会读取 OPENAI_* 环境变量，
# 因此 dotenv 必须在 import 业务模块之前执行；Docker 部署时环境变量已由 compose 注入，此步无副作用）
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
except ImportError:
    logging.getLogger(__name__).warning("未安装 python-dotenv，跳过 .env 加载")

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from routers.files import router as files_router
from core.orchestrator import build_agent_graph

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def message_role(message) -> str:
    if hasattr(message, "type"):
        return {"ai": "assistant", "human": "user"}.get(message.type, message.type)
    return message.get("role", "")


def message_content(message) -> str:
    if hasattr(message, "text"):
        return message.text()
    if hasattr(message, "content"):
        return str(message.content)
    return str(message.get("content", ""))


app = FastAPI(title="PPT Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(files_router)

# 内存会话存储
session_store = {}


@app.get("/")
async def root():
    return {"status": "ok", "message": "PPT Agent Backend is running"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()

    # ================= 核心修改区域开始 =================
    if session_id not in session_store:
        # 严格按照新的 AgentState 定义初始化字典
        initial_state = {
            "messages": [],  # 初始为空列表，LangGraph 的 add_messages 会自动处理后续追加
            "ppt_structure": {"theme": "default", "slides": [], "total_pages": 0},
            "stage": "INIT",
            "output_path": "",
            "uploaded_files": [],
            "progress": {
                "current_step": "初始化",
                "step_index": 0,
                "total_steps": 6,
                "percentage": 0,
                "message": "等待用户输入...",
                "sub_progress": None
            },
            # WebSocket 是运行时连接对象，由 AgentState 中的 ws 字段透传给节点
            "ws": websocket,
            "session_id": session_id
        }

        session_store[session_id] = {
            "state": initial_state,
            "graph": build_agent_graph()
        }
    # ================= 核心修改区域结束 =================

    session_data = session_store[session_id]
    session_data["state"]["ws"] = websocket
    session_data["state"]["session_id"] = session_id

    try:
        while True:
            # 接收前端消息
            data = await websocket.receive_json()
            user_text = data.get("content", "")
            file_ids = data.get("file_ids", [])

            current_state = session_data["state"]

            # 1. 处理用户文本输入
            if user_text:
                # 直接 append 到列表中，LangGraph 的 add_messages reducer 会安全地合并它
                current_state["messages"].append({"role": "user", "content": user_text})

            # 2. 处理上传的文件
            if file_ids:
                for fid in file_ids:
                    fpath = f"./uploads/{fid}"
                    if os.path.exists(fpath) and fpath not in current_state["uploaded_files"]:
                        current_state["uploaded_files"].append(fpath)
                await websocket.send_json({
                    "type": "progress",
                    "data": {
                        "current_step": "初始化", "step_index": 0, "total_steps": 6,
                        "percentage": 5, "message": f"已接收 {len(file_ids)} 个素材文件，正在解析...",
                        "sub_progress": None
                    }
                })

            # 3. 推送初始思考状态
            await websocket.send_json({
                "type": "progress",
                "data": {
                    "current_step": "需求分析", "step_index": 1, "total_steps": 6,
                    "percentage": 10, "message": "Agent 正在分析您的需求...", "sub_progress": None
                }
            })

            # 4. 运行 LangGraph
            # 注意：传入 current_state，Graph 中的每个 Node 都会返回一个“部分更新字典”，LangGraph 会自动安全合并
            final_state = await session_data["graph"].ainvoke(current_state)

            # 5. 更新 store 中的状态为最新状态
            session_data["state"] = final_state

            # 6. 提取 AI 最终回复并发送给前端
            ai_messages = [m for m in final_state["messages"] if message_role(m) == "assistant"]
            reply_text = message_content(ai_messages[-1]) if ai_messages else "处理完成。"

            # 全链路跑完时，最后一条 assistant 消息还停留在大纲文本，改为直接汇报生成结果
            if final_state.get("output_path") and final_state.get("stage") == "DONE":
                total = len((final_state.get("ppt_structure") or {}).get("slides", []))
                reply_text = f"✅ PPT 已生成完成，共 {total} 页。右侧可预览，也可点击「下载 .pptx 源文件」。"

            await websocket.send_json({
                "type": "result",
                "text": reply_text,
                "stage": final_state["stage"],
                "file_ready": bool(final_state.get("output_path"))
            })

    except WebSocketDisconnect:
        logger.info(f"Session {session_id} disconnected normally.")
    except Exception as e:
        logger.error(f"Session {session_id} error: {e}", exc_info=True)
        try:
            await websocket.close()
        except:
            pass
