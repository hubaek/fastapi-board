"""
게시글 관련 비즈니스 로직을 처리하는 서비스 모듈
"""
import math
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.post import Post
from app.schemas.post import PostCreate, PostUpdate


class PostService:
    """
    게시글 CRUD 작업과 비즈니스 로직을 처리하는 서비스 클래스
    """
    def __init__(self, db: Session):
        self.db = db

    def get_posts(self, page: int = 1, page_size: int = 10, search: Optional[str] = None):
        """게시글 목록 조회 (페이징, 검색)"""
        query = self.db.query(Post)

        # 검색 기능
        if search:
            query = query.filter(
                or_(
                    Post.title.contains(search),
                    Post.content.contains(search)
                )
            )

        # 전체 개수
        total = query.count()

        # 페이징
        offset = (page - 1) * page_size
        posts = query.order_by(Post.created_at.desc()).offset(offset).limit(page_size).all()

        total_pages = math.ceil(total / page_size)

        return {
            "posts": posts,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    def get_post(self, post_id: int):
        """ID로 단일 게시글 조회"""
        return self.db.query(Post).filter(Post.id == post_id).first()

    def create_post(self, post: PostCreate):
        """새 게시글 생성"""
        db_post = Post(
            title=post.title,
            content=post.content
        )
        self.db.add(db_post)
        self.db.commit()
        self.db.refresh(db_post)
        return db_post

    def update_post(self, post_id: int, post: PostUpdate):
        """기존 게시글 업데이트"""
        db_post = self.get_post(post_id)
        if not db_post:
            return None

        update_data = post.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_post, field, value)

        self.db.commit()
        self.db.refresh(db_post)
        return db_post

    def delete_post(self, post_id: int):
        """게시글 삭제"""
        db_post = self.get_post(post_id)
        if not db_post:
            return False

        self.db.delete(db_post)
        self.db.commit()
        return True

    def increase_view_count(self, post_id: int):
        """게시글 조회수 증가"""
        db_post = self.get_post(post_id)
        if db_post:
            db_post.view_count += 1
            self.db.commit()
            self.db.refresh(db_post)
        return db_post

    def atomic_increase_view_count(self, post_id: int):
        updated_post = self.db.query(Post).filter(Post.id == post_id).update(
            {Post.view_count: Post.view_count + 1}
        )

        if updated_post:
            self.db.commit()
            return self.get_post(post_id)
        return None