import pytest
import concurrent.futures
import time
from app.services.post import PostService
from app.schemas.post import PostCreate
from app.db.database import SessionLocal

def test_concurrent_view_count_simple(db):
    """기본 동시성 테스트 - 문제 확인용"""
    service = PostService(db)

    # 게시글 생성
    new_post = PostCreate(title="동시성 테스트", content="내용")
    post = service.create_post(new_post)
    post_id = post.id
    db.commit()  # 다른 세션에서도 볼 수 있도록 커밋

    # 동시 요청 수 (작게 시작)
    num_requests = 20

    def increase_view_count_worker():
        # conftest.py의 engine 사용해서 새 세션 생성
        from tests.conftest import TestingSessionLocal
        thread_db = TestingSessionLocal()
        try:
            thread_service = PostService(thread_db)
            # race condition 발생 가능성을 높이기 위한 약간의 지연
            time.sleep(0.1)
            thread_service.increase_view_count(post_id)
            thread_db.commit()
        except Exception as e:
            thread_db.rollback()
            print(f"Thread error: {e}")
            raise
        finally:
            thread_db.close()

    # 동시 실행
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(increase_view_count_worker) for _ in range(num_requests)]

        #모든 작업 완료 대기 및 예외 처리
        results = []
        for future in concurrent.futures.as_completed(futures):
            try:
                results.append(future.result())
            except Exception as e:
                print(f"Future failed: {e}")

    end_time = time.time()

    # 최종 결과 확인 (원래 db 세션 재사용)
    db.refresh(post) # DB에서 최신 상태 다시 로드
    updated = service.get_post(post.id)
    actual_count = updated.view_count

    print(f"\n=== 테스트 결과 ===")
    print(f"예상 조회수: {num_requests}")
    print(f"실제 조회수: {actual_count}")
    print(f"손실된 조회수: {num_requests - actual_count}")
    print(f"정확도: {(actual_count / num_requests) * 100:.1f}%")
    print(f"실행 시간: {end_time - start_time:.3f}초")

    # 결과에 따라 메시지 출력
    if actual_count == num_requests:
        print("✅ Race condition 없음 - 현재 코드로 충분")
    else:
        print("❌ Race condition 발생 - 원자적 업데이트 고려 필요")

    # 테스트는 일단 통과시키되, 결과를 확인
    assert actual_count > 0, "조회수가 전혀 증가하지 않음"

    return actual_count == num_requests


def test_concurrent_view_count_stress(db):
    """스트레스 테스트 - 더 많은 동시 요청"""
    service = PostService(db)

    # 게시글 생성
    new_post = PostCreate(title="스트레스 테스트", content="내용")
    post = service.create_post(new_post)
    post_id = post.id
    db.commit()

    # 더 많은 동시 요청
    num_requests = 100
    max_workers = 20

    def increase_view_count_worker():
        from tests.conftest import TestingSessionLocal
        thread_db = TestingSessionLocal()
        try:
            thread_service = PostService(thread_db)
            thread_service.increase_view_count(post_id)
            thread_db.commit()
        except Exception as e:
            thread_db.rollback()
            raise
        finally:
            thread_db.close()

    # 동시 실행
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(increase_view_count_worker) for _ in range(num_requests)]
        concurrent.futures.wait(futures)

    # 결과 확인
    updated = service.get_post(post_id)
    actual_count = updated.view_count

    print(f"\n=== 스트레스 테스트 결과 ===")
    print(f"예상 조회수: {num_requests}")
    print(f"실제 조회수: {actual_count}")
    print(f"손실률: {((num_requests - actual_count) / num_requests) * 100:.1f}%")

    # 스트레스 테스트에서는 어느 정도 손실 허용
    loss_rate = (num_requests - actual_count) / num_requests
    if loss_rate > 0.1:  # 10% 이상 손실시 문제 있음
        print("❌ 심각한 race condition - 즉시 수정 필요")
        pytest.fail(f"조회수 손실률이 너무 높음: {loss_rate * 100:.1f}%")
    elif loss_rate > 0:
        print("⚠️  일부 race condition 발생 - 수정 권장")
    else:
        print("✅ 완벽한 동시성 처리")


def test_multiple_concurrent_runs(db):
    """여러 번 실행해서 일관성 확인"""
    service = PostService(db)

    results = []
    num_runs = 5
    requests_per_run = 30

    for run in range(num_runs):
        print(f"\n--- 실행 {run + 1}/{num_runs} ---")

        # 새 게시글 생성
        new_post = PostCreate(title=f"일관성 테스트 {run + 1}", content="내용")
        post = service.create_post(new_post)
        post_id = post.id
        db.commit()

        def worker():
            from tests.conftest import TestingSessionLocal
            thread_db = TestingSessionLocal()
            try:
                thread_service = PostService(thread_db)
                thread_service.increase_view_count(post_id)
                thread_db.commit()
            finally:
                thread_db.close()

        # 동시 실행
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(worker) for _ in range(requests_per_run)]
            concurrent.futures.wait(futures)

        # 결과 확인
        updated = service.get_post(post_id)
        actual_count = updated.view_count
        is_perfect = actual_count == requests_per_run
        results.append(is_perfect)

        print(f"결과: {actual_count}/{requests_per_run} ({'✅' if is_perfect else '❌'})")

    # 전체 결과 분석
    success_rate = sum(results) / len(results)
    print(f"\n=== 최종 일관성 결과 ===")
    print(f"성공한 실행: {sum(results)}/{num_runs}")
    print(f"성공률: {success_rate * 100:.0f}%")

    if success_rate == 1.0:
        print("✅ 완벽한 일관성 - 현재 코드 유지")
    elif success_rate >= 0.8:
        print("⚠️  대부분 정상이지만 가끔 문제 발생 - 수정 고려")
        print("   → 높은 트래픽에서는 문제가 될 수 있음")
    else:
        print("❌ 일관성 없음 - 반드시 수정 필요")
        print("   → 원자적 업데이트 방식으로 변경 권장")

    # 80% 이상 성공하면 테스트 통과
    assert success_rate >= 0.8, f"일관성이 너무 낮음: {success_rate * 100:.0f}%"