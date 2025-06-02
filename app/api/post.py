from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.post import PostCreate, PostUpdate, PostOut
from app.crud.post import *

router = APIRouter(
    prefix="/posts",
    tags=["posts"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=list[PostOut])
def read_posts(db: Session = Depends(get_db)):
    return get_posts(db)

@router.get("{post_id}", response_model=PostOut)
def read_post(post_id: int, db: Session = Depends(get_db)):
    db_post = get_post(db, post_id)
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")
    return db_post

@router.post("/", response_model=PostOut)
def create_post_route(post: PostCreate, db: Session = Depends(get_db)):
    return create_post(db, post)

@router.put("/{post_id}", response_model=PostOut)
def update_post_route(post_id: int, post: PostUpdate, db: Session = Depends(get_db)):
    return update_post(db, post_id, post)

@router.delete("/{post_id}")
def delete_post_route(post_id: int, db: Session = Depends(get_db)):
    return delete_post(db, post_id)