from sentence_transformers import SentenceTransformer, util

# 모델 로드
model = SentenceTransformer('all-MiniLM-L6-v2')

# 문장 벡터화
emb1 = model.encode("2 + 7 = ?", convert_to_tensor=True)
emb2 = model.encode("7 + 3 = ?", convert_to_tensor=True)

# 코사인 유사도
similarity = util.cos_sim(emb1, emb2)
print("유사도:", similarity.item())
