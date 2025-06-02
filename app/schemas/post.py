from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


# 데이터 검증 스키마
# Pydantic을 사용한 입력/출력 데이터 검증
# API 요청/응답 형식 정의

class PostBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="게시글 제목")
    content: str = Field(..., min_length=1, description="게시글 내용")

class PostCreate(PostBase):
    pass

class PostUpdate(PostBase):
    pass

class PostResponse(PostBase):
    id: int
    created_at: datetime
    updated_at: datetime
    view_count: int

    class Config:
        from_attributes = True

class PostListResponse(BaseModel):
    posts: list[PostResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

