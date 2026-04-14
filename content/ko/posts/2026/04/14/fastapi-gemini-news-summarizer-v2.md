---
image: "/images/posts/2026/04/14/fastapi-gemini-news-summarizer-v2.jpg"
title: "실용 가이드: FastAPI와 Gemini API를 활용한 실시간 뉴스 요약 서버 구축"
date: "2026-04-14T10:47:52+09:00"
description: "FastAPI와 Google Gemini API를 사용하여 고성능 비동기 뉴스 요약 마이크로서비스의 아키텍처 및 구현을 상세히 다루는 포괄적이고 고급 기술 가이드입니다."
type: "posts"
clusters: ["guides"]
categories: ["tutorials"]
tags: ["기술", "가이드", "fastapi", "gemini", "ai"]
difficulty: "고급"
image_prompt_core: "High-end 3D render of a futuristic, interconnected data processing core. The centerpiece is a glowing, crystalline representation of a large language model (LLM) interface (Gemini API), housed within a sleek, metallic server rack structure. Fiber optic cables and data streams flow into and out of the core. Use deep blues, electric cyan, and gold accents. Focus on geometric precision, volumetric lighting, and abstract data representation. No human figures."
---

## 개요

본 가이드는 원본 뉴스 기사 콘텐츠를 수집하여 Gemini API를 사용하여 맥락적으로 정확하게 고도로 압축된 요약을 반환하도록 설계된 강력한 비동기 마이크로서비스 구축 과정을 상세히 설명합니다. FastAPI는 높은 성능과 비동기 작업에 대한 네이티브 지원을 제공하여, 실시간 환경에서 여러 개의 동시 요약 요청을 처리하는 데 이상적입니다.

**아키텍처 흐름:**
1. 클라이언트가 원본 뉴스 기사 텍스트를 FastAPI 엔드포인트로 전송합니다 (POST 요청을 통해).
2. FastAPI가 입력값을 검증하고 Gemini SDK로 비동기 호출을 시작합니다.
3. Gemini가 프롬프트를 처리합니다 (예: "이 기사를 전문적인 어조를 유지하며 세 개의 글머리 기호로 요약하십시오.") 그리고 요약을 생성합니다.
4. FastAPI가 요약을 수신하고 적절한 상태 코드와 함께 클라이언트에 반환합니다.

## 단계 1. 환경 설정

개발을 시작하기 전에 필요한 종속성 및 환경 변수를 설정해야 합니다.

### 1. 프로젝트 설정

가상 환경을 초기화하고 필요한 패키지를 설치합니다.

```bash
# 가상 환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate

# 핵심 종속성 설치
pip install fastapi uvicorn google-genai pydantic
```

### 2. 환경 변수

API 키를 안전하게 저장합니다. Gemini SDK는 `GEMINI_API_KEY` 환경 변수를 자동으로 감지하도록 설계되었습니다.

```bash
export GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
```

### 3. 데이터 스키마 정의 (Pydantic)

FastAPI 내에서 강력한 데이터 유효성 검사를 위해 Pydantic을 사용하여 예상되는 입력 구조를 정의합니다.

*파일: `app/schemas.py`*

```python
from pydantic import BaseModel, Field

class NewsArticle(BaseModel):
    """원본 뉴스 기사 콘텐츠를 수신하기 위한 스키마입니다."""
    article_id: str = Field(..., description="기사의 고유 식별자입니다.")
    raw_text: str = Field(..., description="뉴스 기사의 전체, 미처리 텍스트입니다.")
    target_summary_length: str = Field(3, description="원하는 길이 제약 조건입니다 (예: '3개의 글머리 기호', '1개 단락').")

class SummaryResponse(BaseModel):
    """구조화된 요약 응답을 위한 스키마입니다."""
    article_id: str
    summary: str
    model_used: str
    status: str
```

## 단계 2. 핵심 구현

이 단계에서는 핵심 로직, 즉 비동기 API 상호 작용 및 FastAPI 엔드포인트 정의를 구현합니다.

### 1. Gemini 상호 작용 서비스

Gemini API 호출을 서비스 함수 내에 캡슐화합니다. `async`와 `await`를 사용하면, 잠재적으로 느릴 수 있는 외부 API 호출을 기다리는 동안 FastAPI 서버가 응답성을 유지하도록 보장합니다.

*파일: `app/gemini_service.py`*

```python
from google import genai
from google.genai.errors import APIError
from typing import Optional

# 클라이언트 초기화 (환경 변수에서 API 키를 읽어옴)
client = genai.Client()
MODEL_NAME = "gemini-2.5-flash"

async def generate_summary(article_text: str, length_constraint: str) -> Optional[str]:
    """
    제공된 텍스트를 요약하기 위해 Gemini API를 비동기적으로 호출합니다.
    """
    # 상세한 시스템 프롬프트를 작성하면 출력의 품질과 일관성이 향상됩니다.
    prompt = f"""
    당신은 선임 뉴스 편집자입니다. 당신의 임무는 다음 기사 텍스트를 요약하는 것입니다.
    요약은 전문적이어야 하며, 고도로 압축되어야 하고, 다음 제약 조건: '{length_constraint}'을 엄격히 준수해야 합니다.
    
    기사 텍스트:
    ---
    {article_text}
    ---
    """
    
    try:
        # 스트리밍 또는 비스트리밍 generate_content 메서드를 사용합니다.
        # 간단한 요약의 경우, 비스트리밍이 일반적으로 충분합니다.
        response = await client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )
        return response.text
    except APIError as e:
        print(f"Gemini API 오류가 발생했습니다: {e}")
        return None
    except Exception as e:
        print(f"예기치 않은 오류가 발생했습니다: {e}")
        return None

```

### 2. FastAPI 라우터 설정

입력 스키마를 비동기 서비스 함수에 연결하는 메인 API 엔드포인트를 정의합니다.

*파일: `main.py`*

```python
from fastapi import FastAPI, HTTPException
from app.schemas import NewsArticle, SummaryResponse
from app.gemini_service import *
import asyncio # 비동기 처리를 위해 임포트

# FastAPI 앱 초기화 (실제 코드에서는 FastAPI()를 사용)
app = FastAPI() 

@app.post("/process_article")
async def process_article(article: ArticleModel):
    """
    기사 텍스트를 받아 요약 및 처리하는 엔드포인트.
    """
    try:
        # 비동기 함수 호출
        summary = await process_article_summary(article.text, article.source)
        return {"status": "success", "summary": summary}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 참고: 위 코드는 설명을 위한 구조이며, 실제 구현 시 적절한 비동기 함수 호출이 필요합니다.
```

*(참고: 위의 코드는 구조 설명용이며, 실제 사용 시에는 `FastAPI()` 객체 생성 및 적절한 비동기 함수 호출이 필요합니다.)*

## 요약 및 실행 방법 (Conceptual Summary)

이 코드는 **비동기(Asynchronous)** 방식으로 작동하도록 설계되어, 여러 요청을 동시에 효율적으로 처리할 수 있습니다.

1.  **`app.post("/process_article")`**: 클라이언트로부터 기사 데이터를 받아 요청을 처리합니다.
2.  **`await process_article_summary(...)`**: 핵심 비즈니스 로직을 담고 있으며, 느린 외부 API 호출(여기서는 LLM 호출을 가정)을 `await` 키워드를 사용하여 비동기적으로 기다립니다.
3.  **효율성**: `async/await` 패턴을 사용함으로써, 한 요청이 응답을 기다리는 동안 다른 요청을 처리할 수 있어 서버의 처리량이 극대화됩니다.