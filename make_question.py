
### make\_new\_quizzes.py (수정된 버전)
import os
import json
import random
import time
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# 1. 원본 퀴즈 데이터에서 20개를 무작위로 가져오는 함수
def get_random_quizzes(file_path: str, num_quizzes: int = 20):
    """지정된 경로의 JSON 파일에서 퀴즈를 무작위로 추출합니다."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # 데이터가 20개 미만일 경우를 대비해 min() 사용
        return random.sample(data, min(num_quizzes, len(data)))
    except FileNotFoundError:
        print(f"오류: '{file_path}' 파일을 찾을 수 없습니다. 스크립트와 동일한 위치에 파일이 있는지 확인하세요.")
        exit()
    except json.JSONDecodeError:
        print(f"오류: '{file_path}' 파일이 올바른 JSON 형식이 아닙니다.")
        exit()


# 2. Gemini API에 전달할 프롬프트 템플릿 (영어로 번역)
PROMPT_TEMPLATE = """
### Role
You are an expert in creating quiz data for the treatment of dyscalculia.

### Input (20 JSON questions)
```json
quizzes
````

### Instructions

Use the 20 questions above as "idea material" to create 9 new quizzes.
The new questions should be distributed as evenly as possible across the following three categories:

  - **lexical_dyscalculia**: Matching number symbols to words (e.g., 6 ↔ six).
  - **practical_dyscalculia**: Comparing magnitudes, number order, and understanding real-world quantities and meanings.
  - **arithmetic_dyscalculia**: Basic arithmetic calculation problems (+, −, ×, ÷).

The output must be a JSON array, and each object must include the following keys:
`question`, `category`, `level`, `option1`, `option2`, `correctIndex`, `question_en_US`, `question_en_UK`, `question_de_DE`, `quiz_id`

Do not simply copy the existing questions; use new scenarios and expressions.
CorrectIndex should be 1 if the answer is option 1, and 2 if it is option 2.
Question should be in Korean,
Your output must contain only the JSON array, with no additional explanations or surrounding text.
"""

# 3\. Gemini API를 호출하는 함수

def call_gemini(prompt: str, model_name: str = "gemini-1.5-flash-latest") -> str:
    print("Gemini 호출 시작")
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        raise EnvironmentError("GEMINI_API_KEY environment variable is not set.")

    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel(model_name)

    time.sleep(4)


    response = model.generate_content(prompt)
    return response.text


# 4\. 메인 실행 로직

def main():
    """스크립트의 메인 흐름을 실행합니다."""
    original_file = "quiz_data.json"
    new_file = "new_quiz_data.json"
    num_to_generate = 10

    # (1) 원본 데이터에서 퀴즈 num개 추출
    quizzes = get_random_quizzes(original_file, num_to_generate)
    if not quizzes:
        return

    # (2) 프롬프트 생성 (f-string 사용)
    prompt = PROMPT_TEMPLATE.format(quizzes=json.dumps(quizzes, ensure_ascii=False, indent=2))

    print("Gemini API를 호출하여 새 퀴즈를 생성합니다. 잠시 기다려 주세요...")
    # (3) Gemini를 호출하여 새 퀴즈 데이터(문자열) 받아오기
    raw_output = call_gemini(prompt)

    # (4) 응답 문자열을 파싱하여 JSON 파일로 저장
    try:
        # LLM이 응답에 Markdown 코드 블록(```json ... ```)을 포함하는 경우 대비
        if raw_output.strip().startswith("```json"):
            clean_json_str = raw_output.strip()[7:-4]
        elif raw_output.strip().startswith("["):
            clean_json_str = raw_output.strip()
        else:
            # 예상치 못한 형식일 경우, 대괄호로 시작하고 끝나는 부분을 탐색
            start = raw_output.find("[")
            end = raw_output.rfind("]") + 1
            if start != -1 and end != 0:
                clean_json_str = raw_output[start:end]
            else:
                raise json.JSONDecodeError("Valid JSON array not found in the response.", raw_output, 0)
        
        new_quizzes = json.loads(clean_json_str)

        with open(new_file, "w", encoding="utf-8") as f:
            json.dump(new_quizzes, f, ensure_ascii=False, indent=4)

        print(f"✅ 새 퀴즈 {len(new_quizzes)}개를 '{new_file}' 파일에 성공적으로 저장했습니다.")

    except json.JSONDecodeError as e:
        print("\n--- JSON 파싱 오류 ---")
        print(f"오류 메시지: {e}")
        print("\n--- Gemini API 원본 응답 ---")
        print(raw_output)
        print("\n--------------------------")
        print(f"오류: Gemini API의 응답을 파싱하는 데 실패했습니다. 원본 응답을 터미널에 출력했습니다.")

if __name__ == "__main__":
    main()

    