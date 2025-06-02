from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.post import PostCreate, PostUpdate, PostResponse, PostListResponse
from app.services.post import PostService
from typing import Optional

router = APIRouter(
    prefix="/posts",
    tags=["posts"],
    responses={404: {"description": "Not found"}},
)

def get_post_service(db: Session = Depends(get_db)):
    return PostService(db)

@router.get("/", response_model=PostListResponse)
async def get_posts(
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(10, ge=1, le=100, description="페이지 크기"),
    search: Optional[str] = Query(None, description="검색어"),
    service: PostService = Depends(get_post_service),
):
    return service.get_posts(page=page, page_size=page_size, search=search)

@router.get("/{post_id}", response_model=PostResponse)
async def read_post(
    post_id: int,
    service: PostService = Depends(get_post_service)
):
    post = service.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다")
    return post

@router.post("/", response_model=PostResponse)
def create_post(
    post_data: PostCreate,
    service: PostService = Depends(get_post_service)
):
    return service.create_post(post_data)

@router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: int,
    post_data: PostUpdate,
    service: PostService = Depends(get_post_service)
):
    updated_post = service.update_post(post_id, post_data)
    if not updated_post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다")
    return updated_post

@router.delete("/{post_id}")
async def delete_post_route(
    post_id: int,
    service: PostService = Depends(get_post_service)
):
    success = service.delete_post(post_id)
    if not success:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다")
    return {"message": "게시글이 삭제되었습니다"}

@router.post("/{post_id}/view", response_model=PostResponse)
async def increase_view_count(
    post_id: int,
    service: PostService = Depends(get_post_service)
):
    post = service.increase_view_count(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다")
    return post