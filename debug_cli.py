import json
import time
from typing import Any, Dict, List, Optional

from set_level import ThetaEngine, level30, BETA_TABLE, TARGET_P


def map_level_to_diff(level_value: str) -> str:
    if level_value is None:
        return "medium"
    normalized = str(level_value).strip().lower()
    if normalized in {"easy", "medium", "hard"}:
        return normalized
    # Graceful fallback for non-standard values like "normal" or empty
    if normalized in {"", "normal", "norm", "average"}:
        return "medium"
    return "medium"


def load_quiz_pool(json_path: str) -> List[Dict[str, Any]]:
    with open(json_path, "r", encoding="utf-8") as f:
        raw_items = json.load(f)

    pool: List[Dict[str, Any]] = []
    for item in raw_items:
        quiz_id_raw = item.get("quiz_id", ""); quiz_id = str(quiz_id_raw).strip()
        cat = item.get("category")
        diff = map_level_to_diff(item.get("level"))

        # Skip items that can't be mapped to our beta table
        if (cat, diff) not in BETA_TABLE:
            continue

        # Two-choice items are required for 1/2 input
        option1 = item.get("option1")
        option2 = item.get("option2")
        correct_index = int(item.get("correctIndex", 0))
        if option1 is None or option2 is None or correct_index not in (1, 2):
            continue

        pool.append({
            "quiz_id": quiz_id,
            "cat": cat,
            "diff": diff,
            "question": item.get("question", ""),
            "option1": option1,
            "option2": option2,
            "correctIndex": correct_index,
        })

    return pool


def prompt_for_answer() -> str:
    while True:
        answer = input("정답 (1/2), 종료(q): ").strip().lower()
        if answer in {"1", "2", "q"}:
            return answer
        print("입력이 올바르지 않습니다. 1, 2 또는 q를 입력하세요.")


def run_cli(
    json_path: str = "/Users/hobongs/Desktop/HoBongs_Project/ICCAS/question_temp/quiz_data.json",
    child_id: str = "child_cli",
    max_questions: Optional[int] = None,
) -> None:
    engine = ThetaEngine()
    pool = load_quiz_pool(json_path)

    if not pool:
        print("퀴즈 풀이 목록을 불러오지 못했습니다. quiz_data.json을 확인하세요.")
        return

    used_ids = set()
    asked_count = 0

    print("실행 방법: 1 또는 2로 답변, q로 종료합니다.")
    print(f"목표 정답확률 TARGET_P = {TARGET_P:.2f}\n")

    while True:
        available = [q for q in pool if q["quiz_id"] not in used_ids]
        if not available:
            print("더 이상 남은 문항이 없습니다. 종료합니다.")
            break

        selected = engine.pick(child_id, available)

        current_theta = engine.theta[child_id]
        current_level_int = level30(current_theta)
        # 디버깅용 연속 레벨 표시를 위해 내부 함수를 직접 호출하지 않고 update 결과를 사용

        header = (
            f"[레벨 {current_level_int:2d} | θ={current_theta:+.3f} | 목표 p={TARGET_P:.2f}] "
            f"문항ID={selected['quiz_id']} | 카테고리={selected['cat']} | 난이도={selected['diff']}"
        )
        print("-" * len(header))
        print(header)
        print("-" * len(header))

        print(selected["question"])
        print(f"1) {selected['option1']}")
        print(f"2) {selected['option2']}")

        t0 = time.perf_counter()
        ans = prompt_for_answer()
        elapsed = time.perf_counter() - t0

        if ans == "q":
            print("종료합니다.")
            break

        is_correct = 1 if int(ans) == selected["correctIndex"] else 0

        # Update theta using elapsed time as solving time
        res = engine.update(
            child_id,
            {"cat": selected["cat"], "diff": selected["diff"]},
            correct=is_correct,
            t=elapsed,
        )

        used_ids.add(selected["quiz_id"])
        asked_count += 1

        print(
            f"정답: {'O' if is_correct else 'X'} | 풀이시간: {elapsed:.2f}s | "
            f"p̂={res['pred_prob']:.2f} | grad={res['grad']:+.3f} | "
            f"θ={res['theta']:+.3f} → 레벨 {res['level_int']} (연속 {res['level_float']:.3f})\n"
        )

        if max_questions is not None and asked_count >= max_questions:
            print("요청한 문항 수에 도달했습니다. 종료합니다.")
            break


if __name__ == "__main__":
    run_cli()

