#!/usr/bin/env python3
"""Standalone web tools. Keys stay in the environment, not the kernel."""

from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

DEFAULT_SUMMARIZER_MODEL = "Hermes-4-70B"
DEFAULT_MIN_LENGTH_FOR_SUMMARIZATION = 5000
DEBUG_MODE = os.getenv("WEB_TOOLS_DEBUG", "false").lower() == "true"
DEBUG_SESSION_ID = str(uuid.uuid4())
DEBUG_LOG_PATH = Path("./logs")
DEBUG_DATA: Optional[Dict[str, Any]] = (
    {
        "session_id": DEBUG_SESSION_ID,
        "start_time": datetime.now().isoformat(),
        "debug_enabled": True,
        "tool_calls": [],
    }
    if DEBUG_MODE
    else None
)

if DEBUG_MODE:
    DEBUG_LOG_PATH.mkdir(exist_ok=True)


def check_firecrawl_api_key() -> bool:
    return bool(os.getenv("FIRECRAWL_API_KEY"))


def check_nous_api_key() -> bool:
    return bool(os.getenv("NOUS_API_KEY"))


def _missing_key(name: str) -> str:
    return json.dumps({"error": f"{name} is not set; keys stay out of the kernel"})


def _firecrawl():
    if not check_firecrawl_api_key():
        return None
    from firecrawl import Firecrawl

    return Firecrawl(api_key=os.getenv("FIRECRAWL_API_KEY"))


def _nous():
    if not check_nous_api_key():
        return None
    from openai import AsyncOpenAI

    return AsyncOpenAI(
        api_key=os.getenv("NOUS_API_KEY"),
        base_url="https://inference-api.nousresearch.com/v1",
    )


def _log_debug_call(tool_name: str, call_data: Dict[str, Any]) -> None:
    if not DEBUG_MODE or not DEBUG_DATA:
        return
    DEBUG_DATA["tool_calls"].append(
        {
            "timestamp": datetime.now().isoformat(),
            "tool_name": tool_name,
            **call_data,
        }
    )


def _save_debug_log() -> None:
    if not DEBUG_MODE or not DEBUG_DATA:
        return
    DEBUG_DATA["end_time"] = datetime.now().isoformat()
    DEBUG_DATA["total_calls"] = len(DEBUG_DATA["tool_calls"])
    path = DEBUG_LOG_PATH / f"web_tools_debug_{DEBUG_SESSION_ID}.json"
    path.write_text(json.dumps(DEBUG_DATA, indent=2, ensure_ascii=False), encoding="utf-8")


def clean_base64_images(text: str) -> str:
    cleaned = re.sub(
        r"\(data:image/[^;]+;base64,[A-Za-z0-9+/=]+\)",
        "[BASE64_IMAGE_REMOVED]",
        text,
    )
    return re.sub(
        r"data:image/[^;]+;base64,[A-Za-z0-9+/=]+",
        "[BASE64_IMAGE_REMOVED]",
        cleaned,
    )


def _as_dict(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        dumped = value.model_dump()
        return dumped if isinstance(dumped, dict) else {}
    if hasattr(value, "__dict__"):
        return dict(value.__dict__)
    return {}


async def process_content_with_llm(
    content: str,
    url: str = "",
    title: str = "",
    model: str = DEFAULT_SUMMARIZER_MODEL,
    min_length: int = DEFAULT_MIN_LENGTH_FOR_SUMMARIZATION,
) -> Optional[str]:
    if len(content) < min_length:
        return None
    client = _nous()
    if client is None:
        return None
    context = []
    if title:
        context.append(f"Title: {title}")
    if url:
        context.append(f"Source: {url}")
    context_str = "\n".join(context) + "\n\n" if context else ""
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "Create a comprehensive markdown summary that preserves "
                    "important facts, quotes, and code while reducing bulk."
                ),
            },
            {
                "role": "user",
                "content": f"{context_str}CONTENT TO PROCESS:\n{content}",
            },
        ],
        temperature=0.1,
        max_tokens=4000,
    )
    processed = response.choices[0].message.content
    return processed.strip() if processed else None


def web_search_tool(query: str, limit: int = 5) -> str:
    debug = {"parameters": {"query": query, "limit": limit}, "error": None}
    client = _firecrawl()
    if client is None:
        debug["error"] = "FIRECRAWL_API_KEY missing"
        _log_debug_call("web_search_tool", debug)
        _save_debug_log()
        return _missing_key("FIRECRAWL_API_KEY")
    try:
        response = client.search(query=query, limit=limit)
        web_results: List[Dict[str, Any]] = []
        payload = _as_dict(response)
        raw_web = getattr(response, "web", None)
        if raw_web is None:
            raw_web = payload.get("web") or []
        for result in raw_web:
            web_results.append(_as_dict(result) or result if isinstance(result, dict) else _as_dict(result))
        body = json.dumps({"success": True, "data": {"web": web_results}}, indent=2)
        debug["results_count"] = len(web_results)
        debug["final_response_size"] = len(body)
        _log_debug_call("web_search_tool", debug)
        _save_debug_log()
        return body
    except Exception as exc:
        debug["error"] = str(exc)
        _log_debug_call("web_search_tool", debug)
        _save_debug_log()
        return json.dumps({"error": f"Error searching web: {exc}"})


async def web_extract_tool(
    urls: List[str],
    format: str = None,
    use_llm_processing: bool = True,
    model: str = DEFAULT_SUMMARIZER_MODEL,
    min_length: int = DEFAULT_MIN_LENGTH_FOR_SUMMARIZATION,
) -> str:
    client = _firecrawl()
    if client is None:
        return _missing_key("FIRECRAWL_API_KEY")
    formats = ["markdown"] if format == "markdown" else ["html"] if format == "html" else ["markdown", "html"]
    results: List[Dict[str, Any]] = []
    for url in urls:
        try:
            scrape_result = client.scrape(url=url, formats=formats)
            payload = _as_dict(scrape_result)
            metadata = _as_dict(payload.get("metadata") or getattr(scrape_result, "metadata", {}))
            markdown = payload.get("markdown") or getattr(scrape_result, "markdown", None)
            html = payload.get("html") or getattr(scrape_result, "html", None)
            chosen = markdown if (format == "markdown" or (format is None and markdown)) else html or markdown or ""
            title = metadata.get("title", "")
            if use_llm_processing and chosen:
                processed = await process_content_with_llm(chosen, url, title, model, min_length)
                content = processed or chosen
            else:
                content = chosen
            results.append({"title": title, "content": content, "error": None})
        except Exception as exc:
            results.append({"title": "", "content": "", "error": str(exc)})
    return clean_base64_images(json.dumps({"results": results}, indent=2))


async def web_crawl_tool(
    url: str,
    instructions: str = None,
    depth: str = "basic",
    use_llm_processing: bool = True,
    model: str = DEFAULT_SUMMARIZER_MODEL,
    min_length: int = DEFAULT_MIN_LENGTH_FOR_SUMMARIZATION,
) -> str:
    del instructions, depth
    client = _firecrawl()
    if client is None:
        return _missing_key("FIRECRAWL_API_KEY")
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    try:
        crawl_result = client.crawl(
            url=url,
            limit=20,
            scrape_options={"formats": ["markdown"]},
        )
        data_list = getattr(crawl_result, "data", None)
        if data_list is None:
            data_list = _as_dict(crawl_result).get("data") or []
        pages: List[Dict[str, Any]] = []
        for item in data_list:
            payload = _as_dict(item)
            metadata = _as_dict(payload.get("metadata"))
            content = payload.get("markdown") or payload.get("html") or ""
            title = metadata.get("title", "")
            page_url = metadata.get("sourceURL", metadata.get("url", url))
            if use_llm_processing and content:
                processed = await process_content_with_llm(
                    content, page_url, title, model, min_length
                )
                content = processed or content
            pages.append({"title": title, "content": content, "error": None})
        return clean_base64_images(json.dumps({"results": pages}, indent=2))
    except Exception as exc:
        return json.dumps({"error": f"Error crawling website: {exc}"})


def get_debug_session_info() -> Dict[str, Any]:
    if not DEBUG_MODE or not DEBUG_DATA:
        return {
            "enabled": False,
            "session_id": None,
            "log_path": None,
            "total_calls": 0,
        }
    return {
        "enabled": True,
        "session_id": DEBUG_SESSION_ID,
        "log_path": str(DEBUG_LOG_PATH / f"web_tools_debug_{DEBUG_SESSION_ID}.json"),
        "total_calls": len(DEBUG_DATA["tool_calls"]),
    }
