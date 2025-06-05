import pytest
import concurrent.futures
import time
from app.services.post import PostService
from app.schemas.post import PostCreate

def test_atomic_update_concurrency(db):
    """원자적 업데이트 방식의 동시성 테스트"""
    service = PostService(db)

    # 게시글 생성
    new_post = PostCreate(title="원자적 업데이트 테스트", content="내용")
    post = service.create_post(new_post)
    post_id = post.id
    db.commit()

    # 동시 요청 수
    num_requests = 500

    def increase_view_count_worker():
        from tests.conftest import TestingSessionLocal
        thread_db = TestingSessionLocal()
        try:
            thread_service = PostService(thread_db)
            result = thread_service.atomic_increase_view_count(post_id)
            # 원자적 업데이트는 이미 내부에서 commit하므로 추가 commit 불필요
            return result is not None
        except Exception as e:
            thread_db.rollback()
            print(f"Thread error: {e}")
            return False
        finally:
            thread_db.close()

    # 동시 실행
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(increase_view_count_worker) for _ in range(num_requests)]

        # 결과 수집
        successful_updates = 0
        for future in concurrent.futures.as_completed(futures):
            try:
                if future.result():
                    successful_updates += 1
            except Exception as e:
                print(f"Future failed: {e}")

    end_time = time.time()

    # 최종 결과 확인
    updated = service.get_post(post_id)
    actual_count = updated.view_count

    print(f"\n=== 원자적 업데이트 테스트 결과 ===")
    print(f"예상 조회수: {num_requests}")
    print(f"실제 조회수: {actual_count}")
    print(f"성공한 업데이트: {successful_updates}")
    print(f"정확도: {(actual_count / num_requests) * 100:.1f}%")
    print(f"실행 시간: {end_time - start_time:.3f}초")

    # 원자적 업데이트는 100% 정확해야 함
    assert actual_count == num_requests, f"예상 {num_requests}, 실제 {actual_count}"
    assert successful_updates == num_requests, f"일부 업데이트 실패: {successful_updates}/{num_requests}"

    print("✅ 원자적 업데이트 완벽 동작!")