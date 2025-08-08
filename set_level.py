# file: rasch_theta_only.py
import math, random
from collections import defaultdict

# ---- 고정 9β̃ 테이블 ----
BETA_TABLE = {
    ("lexical_dyscalculia",  "easy"):   -1.5,
    ("lexical_dyscalculia",  "medium"): -1.0,
    ("lexical_dyscalculia",  "hard"):   -0.5,
    ("practical_dyscalculia","easy"):    0.0,
    ("practical_dyscalculia","medium"):  0.5,
    ("practical_dyscalculia","hard"):    1.0,
    ("arithmetic_dyscalculia","easy"):   1.5,
    ("arithmetic_dyscalculia","medium"): 2.0,
    ("arithmetic_dyscalculia","hard"):   2.5,
}

# ---- 하이퍼파라미터 ----
K_THETA = 0.4   # 적응 속도 상향
ALPHA   = 0.85   # 정답 가중치 상향(느린 정답에서도 감소 방지)
TAU     = 10.0    # 시간 패널티 완화
TARGET_P = 0.70

# ---- 유틸 ----
sigmoid = lambda x: 1/(1+math.exp(-x))
def level30(theta):
    return max(1, min(30, math.ceil(15*(math.tanh(theta/2)+1))))

def level30_continuous(theta: float) -> float:
    """연속 레벨 값 (ceil/clamp 전) — 디버깅용 표시.
    범위는 대략 [0, 30]이며, 실사용 int 레벨은 level30에서 1..30로 clamp됩니다.
    """
    return 15 * (math.tanh(theta/2) + 1)

def r_prime(correct:int, t:float):
    return ALPHA*correct - (1-ALPHA)*math.tanh(t/TAU)

# ---- 엔진 ----
class ThetaEngine:
    def __init__(self):
        self.theta = defaultdict(float)   # child -> θ

    # 문항 풀에서 θ에 맞춰 p≈TARGET_P인 퀴즈 선택
    def pick(self, cid, pool):
        th = self.theta[cid]
        def gap(q):
            beta = BETA_TABLE[(q["cat"], q["diff"])]
            return abs(sigmoid(th-beta) - TARGET_P)
        return min(pool, key=gap)

    def update(self, cid, quiz, correct:int, t:float):
        th   = self.theta[cid]
        beta = BETA_TABLE[(quiz["cat"], quiz["diff"])]

        p_hat = sigmoid(th - beta)
        r     = r_prime(correct, t)
        grad  = r - p_hat

        # θ 업데이트 및 안정화를 위한 클리핑
        self.theta[cid] += K_THETA * grad
     #    if self.theta[cid] > 4.0:
     #        self.theta[cid] = 4.0
     #    elif self.theta[cid] < -4.0:
     #        self.theta[cid] = -4.0

        return {
            "theta": round(self.theta[cid], 3),
            "pred_prob": round(p_hat, 3),
            "grad": round(grad, 3),
            "level_int": level30(self.theta[cid]),
            "level_float": round(level30_continuous(self.theta[cid]), 3),
        }

# ---- 데모 ----
if __name__ == "__main__":
    # 데모 실행을 위한 선택적 numpy 임포트 (없어도 데모가 돌아가도록 대체 구현 제공)
    try:
        import numpy as np  # type: ignore
        rand_uniform = lambda a, b: float(np.random.uniform(a, b))
        rand_bern = lambda p: int(np.random.rand() < p)
    except Exception:  # numpy 미설치 시 파이썬 random으로 대체
        rand_uniform = lambda a, b: random.uniform(a, b)
        rand_bern = lambda p: int(random.random() < p)

    eng = ThetaEngine()

    # 9개 카테고리·난이도 퀴즈 풀
    pool = [{"quiz_id": f"{c[:3]}_{d[0]}_{i}",
             "cat": c, "diff": d}
            for c in ["lexical_dyscalculia",
                       "practical_dyscalculia",
                       "arithmetic_dyscalculia"]
            for d in ["easy","medium","hard"]
            for i in range(10)]

    cid="child_A"
    print("step | correct | θ -> lvl | p̂ | grad")
    for step in range(30):
        q = eng.pick(cid, pool)
        p = sigmoid(eng.theta[cid] - BETA_TABLE[(q["cat"], q["diff"])])
        correct = rand_bern(p)
        res = eng.update(cid, q, correct, t=rand_uniform(1, 6))
        print(f"{step:2d} |   {correct}    | "
              f"{res['theta']:+} -> {res['next_level']:2d} | "
              f"{res['pred_prob']:.2f} | {res['grad']:+.3f}")
