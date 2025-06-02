from fastapi import FastAPI
from app.api import post
from app.models import post as post_model
from app.db.database import engine, Base

app = FastAPI(
    title="FastAPI Board Project",
    description="A FastAPI Board Project",
    version="0.0.1",
)

# 모델 기반 테이블 생성
Base.metadata.create_all(bind=engine)

# 라우터 등록
app.include_router(post.router)
