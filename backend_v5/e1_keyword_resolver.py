# backend_v5/e1_keyword_resolver.py
import json
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def generate_keyword_set_via_llm(user_keyword: str) -> dict:
    prompt = f"""
    너는 입력받은 키워드만 분석하는 전문 분석기야.
    검색 키워드: '{user_keyword}'

    [절대 규칙]
    1. '{user_keyword}' 외에 다른 인물, 다른 팬덤, 다른 상품과 관련된 키워드는 절대 추가하지 마.
    2. 연관어(related)는 비워두거나, '{user_keyword}' 자체의 파생어(예: 왁뿌볼 재질, 왁뿌볼 가격)만 넣어.
    3. JSON 형식으로 출력하되, 검색어와 관련 없는 잡음은 0%로 만들어.
    
    출력 형식:
    {{
      "canonical": "정식명칭",
      "terms": [
        {{"term": "정식명칭", "term_type": "canonical", "term_weight": 1.0}},
        {{"term": "줄임말", "term_type": "alias", "term_weight": 0.9}},
        {{"term": "오타", "term_type": "typo", "term_weight": 0.5}},
        {{"term": "연관어", "term_type": "related", "term_weight": 0.3}}
      ]
    }}
    """

    # 💡 해결책: 어느 계정에서나 100% 작동하는 가장 범용적인 'gemini-2.5-flash' 모델 사용
    model = genai.GenerativeModel('gemini-2.5-flash')

    try:
        response = model.generate_content(prompt)
        result_text = response.text.strip()
        
        # 💡 안전장치: 모델이 혹시라도 ```json 텍스트 ``` 형태로 대답할 경우 껍데기를 벗겨냄
        if result_text.startswith("```json"):
            result_text = result_text[7:-3].strip()
        elif result_text.startswith("```"):
            result_text = result_text[3:-3].strip()
            
        parsed_data = json.loads(result_text)

        return {
            "keyword_set": parsed_data
        }
    except Exception as e:
        print(f"⚠️ Gemini API 에러 발생: {e}")
        return {
            "keyword_set": {
                "canonical": user_keyword,
                "terms": [{"term": user_keyword, "term_type": "canonical", "term_weight": 1.0}]
            }
        }