# 目录: ./backend/routers/files.py | 模块: 文件服务层 | 职责: 素材上传、PPT 转 PDF 预览、PPT 下载，路径适配 Docker 容器内目录
import os
import shutil
import uuid
import subprocess
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

router = APIRouter()


def find_libreoffice() -> str | None:
    """跨平台查找 LibreOffice 可执行文件：Linux 用 libreoffice，Windows/macOS 常见为 soffice。"""
    candidates = ["libreoffice", "soffice"]
    for name in candidates:
        path = shutil.which(name)
        if path:
            return path
    for p in (
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    ):
        if os.path.exists(p):
            return p
    return None

# Docker 容器内路径（与 Dockerfile 中 mkdir 一致）
UPLOAD_DIR = "./uploads"
OUTPUT_DIR = "./output"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 从 main.py 导入 session_store（生产环境建议用依赖注入）
def get_session_store():
    from main import session_store
    return session_store

@router.post("/upload")
async def upload_material(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1]
    file_id = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, file_id)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    return {"file_id": file_id, "filename": file.filename, "path": file_path}

@router.get("/preview/{session_id}")
async def get_ppt_preview(session_id: str):
    store = get_session_store()
    if session_id not in store:
        raise HTTPException(404, "Session not found")
    pptx_path = store[session_id]["state"].get("output_path")
    if not pptx_path or not os.path.exists(pptx_path):
        raise HTTPException(404, "PPT not generated yet")

    pdf_filename = f"preview_{session_id}.pdf"
    pdf_path = os.path.join(OUTPUT_DIR, pdf_filename)

    if not os.path.exists(pdf_path) or os.path.getmtime(pptx_path) > os.path.getmtime(pdf_path):
        office_bin = find_libreoffice()
        if not office_bin:
            raise HTTPException(
                501,
                "未检测到 LibreOffice，无法生成 PDF 预览。可安装后重试，或直接下载 .pptx 文件。"
            )
        try:
            subprocess.run([
                office_bin, "--headless", "--convert-to", "pdf",
                "--outdir", OUTPUT_DIR, pptx_path
            ], check=True, capture_output=True, timeout=120)

            generated_pdf = os.path.join(
                OUTPUT_DIR, os.path.basename(pptx_path).replace('.pptx', '.pdf')
            )
            if os.path.exists(generated_pdf) and generated_pdf != pdf_path:
                os.rename(generated_pdf, pdf_path)
        except subprocess.TimeoutExpired:
            raise HTTPException(500, "PDF 转换超时")
        except Exception as e:
            raise HTTPException(500, f"PDF 转换失败: {str(e)}")

    return FileResponse(pdf_path, media_type='application/pdf', filename=pdf_filename)

@router.get("/download/{session_id}")
async def download_ppt(session_id: str):
    store = get_session_store()
    if session_id not in store:
        raise HTTPException(404, "Session not found")
    file_path = store[session_id]["state"].get("output_path")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(404, "File not ready")
    return FileResponse(
        path=file_path,
        filename=os.path.basename(file_path),
        media_type='application/vnd.openxmlformats-officedocument.presentationml.presentation'
    )