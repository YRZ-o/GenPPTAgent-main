import os
from urllib.parse import urlsplit, urlunsplit

from langchain_openai import ChatOpenAI


def normalize_openai_base_url(value: str | None) -> str:
    """OpenAI SDK 需要以 /v1 结尾的 API 根路径。"""
    value = (value or "https://api.openai.com/v1").strip().rstrip("/")
    if not value:
        return "https://api.openai.com/v1"

    parts = urlsplit(value)
    if parts.path and not parts.path.startswith("/"):
        raise ValueError(f"OPENAI_BASE_URL 格式不正确: {value}")

    # 常见兼容网关只配置了域名；未写路径时按 OpenAI 标准补 /v1。
    if not parts.path:
        parts = parts._replace(path="/v1")
    return urlunsplit(parts)


def create_llm(temperature: float = 0) -> ChatOpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("未配置 OPENAI_API_KEY，请检查 .env 或容器环境变量")

    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        temperature=temperature,
        api_key=api_key,
        base_url=normalize_openai_base_url(os.getenv("OPENAI_BASE_URL")),
        timeout=120,
        max_retries=2,
    )
