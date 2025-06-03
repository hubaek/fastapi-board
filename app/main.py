from fastapi import FastAPI
from app.controller import post
from app.db.database import engine, Base

app = FastAPI(
    title="FastAPI Board Project",
    description="FastAPI로 만든 간단한 게시판",
    version="1.0.0",
)

# 모델 기반 테이블 생성
Base.metadata.create_all(bind=engine)

# 라우터 등록
app.include_router(post.router)

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {"message": "게시판 API에 오신 것을 환영합니다!"}

@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    return {"status": "healthy"}
