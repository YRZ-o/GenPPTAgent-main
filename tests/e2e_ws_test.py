# 目录: ./tests/e2e_ws_test.py | 模块: 端到端测试 | 职责: 模拟前端 WebSocket 走完整 Agent 链路并校验产物
import asyncio
import json
import sys
import urllib.request
import uuid

import websockets

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
WS_BASE = BASE.replace("http://", "ws://").replace("https://", "wss://")
PROMPT = (
    sys.argv[2]
    if len(sys.argv) > 2
    else "帮我做一份《新能源汽车行业分析》PPT，共6页，面向投资人，商务简约风格，"
    "包含市场规模数据。信息充足，不需要追问，直接开始规划大纲。"
)


async def run() -> int:
    sid = uuid.uuid4().hex
    url = f"{WS_BASE}/ws/{sid}"
    print(f"[TEST] session={sid}")
    print(f"[TEST] connecting {url}")

    last_result = None
    progress_seen = 0
    events = {}
    async with websockets.connect(url, max_size=None, open_timeout=30) as ws:
        await ws.send(json.dumps({"content": PROMPT, "file_ids": []}, ensure_ascii=False))
        print("[TEST] prompt sent, waiting for events...")

        while True:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=300)
            except asyncio.TimeoutError:
                print("[TEST][ERROR] 300s 内未收到消息")
                return 2
            msg = json.loads(raw)
            if msg.get("type") == "progress":
                progress_seen += 1
                d = msg["data"]
                print(f"  [progress {progress_seen:02d}] {d['percentage']:>3}% {d['current_step']} | {d['message']}")
            elif msg.get("type") in ("analysis", "outline", "draft", "layout", "template"):
                t = msg["type"]
                events[t] = events.get(t, 0) + 1
                d = msg["data"]
                if t == "analysis":
                    print(f"  [analysis] {str(d.get('content'))[:160]}")
                elif t == "outline":
                    print(f"  [outline] theme={d.get('theme')} pages={d.get('total_pages')}")
                elif t == "draft":
                    print(f"  [draft] P{d.get('page_number')} {d.get('title')} | bullets={len(d.get('bullets') or [])} notes={'Y' if d.get('notes') else '-'}")
                elif t == "layout":
                    print(f"  [layout] P{d.get('page_number')} -> {d.get('layout_name')}")
                elif t == "template":
                    print(f"  [template] {d.get('template')} reused={d.get('reused')} content={d.get('content_pages')} total={d.get('total_pages')}")
            elif msg.get("type") == "result":
                last_result = msg
                print(f"  [result] stage={msg.get('stage')} file_ready={msg.get('file_ready')}")
                print(f"  [result] text={str(msg.get('text'))[:300]}")
                break
            else:
                print(f"  [unknown] {msg}")

    if not last_result:
        print("[TEST][FAIL] 未收到 result")
        return 1
    if not last_result.get("file_ready"):
        print("[TEST][FAIL] file_ready=False，PPT 未生成")
        return 1
    if progress_seen == 0:
        print("[TEST][FAIL] 没有收到任何 progress 事件")
        return 1

    # 校验阶段性展示事件齐全
    expected = {"analysis": 1, "outline": 1, "layout": None, "template": 1, "draft": None}
    missing = [k for k, v in expected.items() if k not in events or (v and events[k] < v)]
    print(f"[TEST] 事件统计: progress={progress_seen} {events}")
    if missing:
        print(f"[TEST][FAIL] 缺少展示事件: {missing}")
        return 1

    # 校验下载接口
    dl = f"{BASE}/download/{sid}"
    try:
        with urllib.request.urlopen(dl, timeout=60) as r:
            body = r.read()
            ctype = r.headers.get("Content-Type", "")
        print(f"[TEST] download OK: {len(body)} bytes, type={ctype}")
        if not body.startswith(b"PK"):
            print("[TEST][FAIL] 下载内容不是 zip/pptx 格式")
            return 1
        with open("tests/last_output.pptx", "wb") as f:
            f.write(body)
        # 记录 session，供后续脚本检查生成的 PPT 结构
        with open("tests/last_session.txt", "w", encoding="utf-8") as f:
            f.write(sid)
    except Exception as e:
        print(f"[TEST][FAIL] download 失败: {e}")
        return 1

    # 校验预览接口（LibreOffice 转 PDF）
    pv = f"{BASE}/preview/{sid}"
    try:
        with urllib.request.urlopen(pv, timeout=180) as r:
            pdf = r.read()
        print(f"[TEST] preview OK: {len(pdf)} bytes, starts_with=%PDF={pdf[:4] == b'%PDF'}")
    except Exception as e:
        detail = ""
        if hasattr(e, "read"):
            try:
                detail = e.read().decode("utf-8", "replace")
            except Exception:
                pass
        print(f"[TEST][WARN] preview 失败（不影响 .pptx 下载）: {e} {detail}")

    print("[TEST][PASS] 全链路通过")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
