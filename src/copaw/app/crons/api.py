# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from agentscope.model import OpenAIChatModel

from ...providers import get_active_llm_config
from .manager import CronManager
from .models import CronJobSpec, CronJobView, CronParseRequest, CronParseResponse
from .parser import parse_with_rules, validate_cron, cron_to_human

router = APIRouter(prefix="/cron", tags=["cron"])


def get_cron_manager(request: Request) -> CronManager:
    mgr = getattr(request.app.state, "cron_manager", None)
    if mgr is None:
        raise HTTPException(
            status_code=503,
            detail="cron manager not initialized",
        )
    return mgr


@router.get("/jobs", response_model=list[CronJobSpec])
async def list_jobs(mgr: CronManager = Depends(get_cron_manager)):
    return await mgr.list_jobs()


@router.get("/jobs/{job_id}", response_model=CronJobView)
async def get_job(job_id: str, mgr: CronManager = Depends(get_cron_manager)):
    job = await mgr.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return CronJobView(spec=job, state=mgr.get_state(job_id))


@router.post("/jobs", response_model=CronJobSpec)
async def create_job(
    spec: CronJobSpec,
    mgr: CronManager = Depends(get_cron_manager),
):
    # server generates id; ignore client-provided spec.id
    job_id = str(uuid.uuid4())
    created = spec.model_copy(update={"id": job_id})
    await mgr.create_or_replace_job(created)
    return created


@router.put("/jobs/{job_id}", response_model=CronJobSpec)
async def replace_job(
    job_id: str,
    spec: CronJobSpec,
    mgr: CronManager = Depends(get_cron_manager),
):
    if spec.id != job_id:
        raise HTTPException(status_code=400, detail="job_id mismatch")
    await mgr.create_or_replace_job(spec)
    return spec


@router.delete("/jobs/{job_id}")
async def delete_job(
    job_id: str,
    mgr: CronManager = Depends(get_cron_manager),
):
    ok = await mgr.delete_job(job_id)
    if not ok:
        raise HTTPException(status_code=404, detail="job not found")
    return {"deleted": True}


@router.post("/jobs/{job_id}/pause")
async def pause_job(job_id: str, mgr: CronManager = Depends(get_cron_manager)):
    try:
        await mgr.pause_job(job_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"paused": True}


@router.post("/jobs/{job_id}/resume")
async def resume_job(
    job_id: str,
    mgr: CronManager = Depends(get_cron_manager),
):
    try:
        await mgr.resume_job(job_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"resumed": True}


@router.post("/jobs/{job_id}/run")
async def run_job(job_id: str, mgr: CronManager = Depends(get_cron_manager)):
    try:
        await mgr.run_job(job_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail="job not found") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"started": True}


@router.get("/jobs/{job_id}/state")
async def get_job_state(
    job_id: str,
    mgr: CronManager = Depends(get_cron_manager),
):
    job = await mgr.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return mgr.get_state(job_id).model_dump(mode="json")


@router.post("/parse-cron", response_model=CronParseResponse)
async def parse_cron_expression(request: CronParseRequest):
    """
    Parse natural language to cron expression.

    - First tries local rule-based parsing (fast)
    - Falls back to LLM if rules don't match (smart)
    - Supports both Chinese and English
    """
    text = request.text.strip()

    # Auto-detect language if not provided
    lang = request.lang
    if not lang:
        # Simple heuristic: if contains Chinese characters, use zh, else en
        lang = "zh" if any('\u4e00' <= c <= '\u9fff' for c in text) else "en"

    # 1. Try local rule-based parsing (fast)
    local_result = parse_with_rules(text)
    if local_result:
        return CronParseResponse(
            cron=local_result,
            source="rules",
            description=cron_to_human(local_result, lang=lang),
        )

    # 2. Try LLM parsing (smart fallback)
    try:
        llm_result = await _parse_with_llm(text, lang=lang)
        return CronParseResponse(
            cron=llm_result,
            source="llm",
            description=cron_to_human(llm_result, lang=lang),
        )
    except Exception as e:
        error_msg = (
            f"无法解析表达式: {text}. 请使用标准 cron 格式或更清晰的自然语言描述。错误: {str(e)}"
            if lang == "zh"
            else f"Failed to parse: {text}. Please use standard cron format or clearer natural language. Error: {str(e)}"
        )
        raise HTTPException(
            status_code=400,
            detail=error_msg,
        ) from e


async def _parse_with_llm(text: str, lang: str = "zh") -> str:
    """Use LLM to parse complex/ambiguous natural language."""
    if lang == "en":
        prompt = f"""Convert natural language to standard cron expression (5 fields).

Rules:
- Output only the cron expression, nothing else
- Format: minute hour day month day_of_week
- If ambiguous, choose the most reasonable interpretation

Examples:
"every day at 2pm" → 0 14 * * *
"every Monday at 9am" → 0 9 * * 1
"every hour" → 0 * * * *
"every 30 minutes" → */30 * * * *
"weekdays at 9am" → 0 9 * * 1-5

Input: {text}
Output (cron expression only):"""
    else:
        prompt = f"""将自然语言转换为标准 cron 表达式（5个字段）。

规则：
- 只输出 cron 表达式，不要其他内容
- 格式：分钟 小时 日 月 星期
- 如果有歧义，选择最合理的解释

示例：
"每天下午2点" → 0 14 * * *
"每周一上午9点" → 0 9 * * 1
"每小时" → 0 * * * *
"每30分钟" → */30 * * * *
"工作日早上9点" → 0 9 * * 1-5

输入：{text}
输出（只输出cron表达式）："""

    # Create a non-streaming model for this specific use case
    llm_cfg = get_active_llm_config()

    if llm_cfg and llm_cfg.api_key:
        model_name = llm_cfg.model or "qwen3-max"
        api_key = llm_cfg.api_key
        base_url = llm_cfg.base_url
    else:
        model_name = "qwen3-max"
        api_key = os.getenv("DASHSCOPE_API_KEY", "")
        base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # Create non-streaming model
    model = OpenAIChatModel(
        model_name,
        api_key=api_key,
        stream=False,  # Disable streaming for simpler response handling
        client_kwargs={"base_url": base_url},
    )

    response = await model([{"role": "user", "content": prompt}])

    # Extract cron from response - ChatResponse has content field with blocks
    try:
        # ChatResponse.content is a list of content blocks (TextBlock, etc.)
        if hasattr(response, 'content'):
            content = response.content
            if isinstance(content, list):
                # Extract text from all TextBlock items
                text_parts = []
                for block in content:
                    if hasattr(block, 'text'):
                        text_parts.append(block.text)
                    elif isinstance(block, str):
                        text_parts.append(block)
                    elif isinstance(block, dict) and 'text' in block:
                        text_parts.append(block['text'])
                cron = ''.join(text_parts).strip()
            elif isinstance(content, str):
                cron = content.strip()
            else:
                cron = str(content).strip()
        elif isinstance(response, str):
            cron = response.strip()
        else:
            raise ValueError(f"Unexpected response structure: {type(response)}")
    except Exception as e:
        raise ValueError(f"Failed to extract text from response (type: {type(response).__name__}): {str(e)}")

    # Clean up potential extra text
    lines = cron.split("\n")
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith("//"):
            parts = line.split()
            if len(parts) == 5:
                cron = line
                break

    # Validate
    validate_cron(cron)
    return cron
