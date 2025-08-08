import json
from sentence_transformers import SentenceTransformer, util
import numpy as np
import pprint

# 모델 로드
model = SentenceTransformer('all-MiniLM-L6-v2')

# 기존 퀴즈 로드
with open("quiz_data.json", "r", encoding="utf-8") as f:
    old_quizzes = json.load(f)

# 새 퀴즈 로드
with open("new_quiz_data.json", "r", encoding="utf-8") as f:
    new_quizzes = json.load(f)

# 기존 퀴즈를 category, level 별로 묶기
quiz_dict = {}
for quiz in old_quizzes:
    key = (quiz["category"], quiz["level"])
    quiz_dict.setdefault(key, []).append(quiz["question_en_US"])


# pprint.pprint(quiz_dict)
# print("--" * 50)
# 새 퀴즈와 기존 퀴즈 유사도 계산

results = []

# new_quiz_dict = {}
# for quiz in new_quizzes:
#     key = (quiz["category"], quiz["level"])
#     new_quiz_dict.setdefault(key, []).append(quiz["question_en_US"])
# pprint.pprint(new_quiz_dict)


for new_quiz in new_quizzes:
    key = (new_quiz["category"], new_quiz["level"])
    if key[0] == "arithmetic_dyscalculia":
        results.append(new_quiz)
        continue
    if key in quiz_dict:
        existing_questions = quiz_dict[key]

        # 임베딩 계산
        new_emb = model.encode(new_quiz["question_en_US"], convert_to_tensor=True)
        old_embs = model.encode(existing_questions, convert_to_tensor=True)

        # 모든 개별 유사도 계산
        sims = util.cos_sim(new_emb, old_embs).cpu().numpy()[0]
        avg_sim = float(np.mean(sims))

        # 개별 유사도 리스트 구성
        similarity_list = [
            {"existing_question": existing_questions[i], "similarity": float(sims[i])}
            for i in range(len(existing_questions))
        ]
        print(f"\n🔹 {new_quiz['question_en_US']} (평균 유사도: {avg_sim:.2f})")
        for item in similarity_list:
            print(f"  - {item['existing_question']} → {item['similarity']:.2f}")

        
        if avg_sim > 0.8:  # 유사도가 0.8 이상인 경우만 저장
            results.append(new_quiz)

# 결과 저장
with open("quiz_similarity_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("유사도 결과가 quiz_similarity_results.json에 저장되었습니다.")
